"""Issue classification using TF-IDF and regex matching."""
from .logging_config import get_logger
import re
from typing import Dict, Tuple, Optional, List, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import (
    TFIDF_WEIGHT,
    REGEX_WEIGHT,
    MIN_CONFIDENCE_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    ConfidenceLevel,
)
from .service_definitions import get_service_terms, get_critical_keywords
from .utils import extract_label_names, extract_label_names_lower

logger = get_logger(__name__)


def get_blocking_label_info(labels: List[str]) -> Dict[str, bool]:
    """Return blocking signal flags derived from GitHub label names.

    Args:
        labels: List of lowercase label name strings.

    Returns:
        Dict with keys:
            'is_exempt'   — True if forward/exempt is present
            'is_upstream' — True if upstream is present
            'is_blocked'  — True if either is present
    """
    lower = extract_label_names_lower(labels)
    is_exempt = "forward/exempt" in lower
    is_upstream = "upstream" in lower
    return {
        "is_exempt": is_exempt,
        "is_upstream": is_upstream,
        "is_blocked": is_exempt or is_upstream,
    }


def classify_labels(labels: List[str]) -> Dict[str, bool]:
    """Classify labels into semantic types.

    Args:
        labels: List of label names.

    Returns:
        Dictionary with label type flags.
    """
    labels_lower = extract_label_names_lower(labels)

    return {
        "bug": any("bug" in label for label in labels_lower),
        "enhancement": any(
            label in ["enhancement", "feature", "feature-request"] for label in labels_lower
        ),
        "documentation": any("doc" in label for label in labels_lower),
        "upstream": any("upstream" in label for label in labels_lower),
        "breaking_change": any("breaking" in label for label in labels_lower),
        "has_pr": any("pr" in label or "pull" in label for label in labels_lower),
        "waiting": any("waiting" in label or "blocked" in label for label in labels_lower),
        "good_first_issue": any("good first" in label or "beginner" in label for label in labels_lower),
        "actionable": any(
            "good first" in label or
            "beginner" in label or
            label == "small" or
            "size:small" in label
            for label in labels_lower
        ),
    }


class IssueClassifier:
    """Classifies issues based on service relevance using pre-fitted TF-IDF."""
    
    def __init__(self):
        self.service_terms = get_service_terms()
        self.critical_keywords = get_critical_keywords()
        self._categories = list(self.service_terms.keys())
        
        # Pre-fit TF-IDF vectorizer with service terms for better performance
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._category_vectors = None
        self._initialize_tfidf()

        # Experimental shadow vectorizer (tri-grams). Logging-only usage.
        self._shadow_vectorizer: Optional[TfidfVectorizer] = None
        self._shadow_category_vectors = None

    def _initialize_tfidf(self) -> None:
        """Pre-fits TF-IDF vectorizer with service category documents."""
        try:
            # Build category documents
            category_docs = []
            for category in self._categories:
                cat_text = " ".join(self.service_terms[category])
                category_docs.append(cat_text)
            
            # Initialize and fit vectorizer
            self._vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=5000,  # Limit features for performance
                min_df=1
            )
            
            # Fit on category documents and transform
            self._category_vectors = self._vectorizer.fit_transform(category_docs)
            logger.debug("TF-IDF vectorizer initialized with %d features", 
                        len(self._vectorizer.get_feature_names_out()))
        except Exception as e:
            logger.error("Error initializing TF-IDF vectorizer: %s", e)
            self._vectorizer = None
            self._category_vectors = None

    def _initialize_shadow_tfidf(self) -> None:
        """Pre-fits experimental tri-gram TF-IDF vectorizer for shadow comparisons."""
        try:
            category_docs = []
            for category in self._categories:
                cat_text = " ".join(self.service_terms[category])
                category_docs.append(cat_text)

            self._shadow_vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 3),
                max_features=8000,
                min_df=1,
            )
            self._shadow_category_vectors = self._shadow_vectorizer.fit_transform(category_docs)
            logger.debug(
                "Shadow TF-IDF vectorizer initialized with %d features",
                len(self._shadow_vectorizer.get_feature_names_out()),
            )
        except Exception as e:
            logger.warning("Error initializing shadow TF-IDF vectorizer: %s", e)
            self._shadow_vectorizer = None
            self._shadow_category_vectors = None

    def _ensure_shadow_initialized(self) -> None:
        """Lazy-init the shadow vectorizer on first use."""
        if self._shadow_vectorizer is None and self._shadow_category_vectors is None:
            self._initialize_shadow_tfidf()

    def classify_issue(self, issue: Dict) -> Tuple[bool, Optional[str], float, str]:
        """
        Determines if issue is relevant to target services.

        Args:
            issue: Dictionary containing issue data with 'title', 'body', 'labels'

        Returns:
            Tuple of (is_relevant, service_category, confidence, confidence_band)
        """
        # Quick keyword check first (most efficient)
        is_match, category, confidence, confidence_band = self._quick_keyword_check(issue)
        if self._is_excluded_by_negative_gate(issue):
            return False, None, 0.0, "EXCLUDED"
        if is_match:
            return True, category, confidence, confidence_band

        # Full analysis if quick check fails
        issue_text = self._build_issue_text(issue)
        tfidf_scores = self._classify_with_tfidf(issue_text)
        regex_scores = self._calculate_regex_scores(issue)
        final_scores = self._combine_scores(tfidf_scores, regex_scores)

        is_relevant, category, score, band, _ = self._evaluate_scores_with_related(final_scores)
        return is_relevant, category, score, band

    def _is_excluded_by_negative_gate(self, issue: Dict[str, Any]) -> bool:
        """Exclude known non-Cloud-Armor contexts before expensive scoring."""
        try:
            title = str(issue.get("title") or "")
            body = str(issue.get("body") or "")
            combined_text = f"{title}\n{body}"
            text_lower = combined_text.lower()

            issue_number = issue.get("number")
            cloud_armor_keywords = self.critical_keywords.get("Cloud Armor", [])
            has_cloud_armor_keyword = any(keyword in text_lower for keyword in cloud_armor_keywords)

            # Condition 1: first mentioned Terraform resource clearly belongs to other GCP services.
            first_resource_match = re.search(r"google_[a-z_]+", text_lower)
            if first_resource_match:
                first_resource = first_resource_match.group(0)
                non_cloud_armor_prefixes = (
                    "google_dns_",
                    "google_firebase_",
                    "google_bigquery_",
                    "google_storage_bucket",
                    "google_sql_",
                    "google_container_",
                    "google_pubsub_",
                    "google_cloud_run_",
                    "google_artifact_registry_",
                    "google_spanner_",
                    "google_dataflow_",
                )
                if first_resource.startswith(non_cloud_armor_prefixes) and not has_cloud_armor_keyword:
                    logger.debug(
                        "Negative gate excluded issue #%s by condition_1 (first_resource=%s)",
                        issue_number,
                        first_resource,
                    )
                    return True

            # Condition 2: Firebase context without Cloud Armor signals.
            if (
                "firebase" in text_lower
                and "cloud armor" not in text_lower
                and "compute_security_policy" not in text_lower
            ):
                logger.debug(
                    "Negative gate excluded issue #%s by condition_2 (firebase context)",
                    issue_number,
                )
                return True

            # Condition 3: DNSSEC/DNS context without Cloud Armor signals.
            if (
                ("dnssec" in text_lower or "google_dns_" in text_lower)
                and "cloud armor" not in text_lower
                and "compute_security_policy" not in text_lower
            ):
                logger.debug(
                    "Negative gate excluded issue #%s by condition_3 (dns context)",
                    issue_number,
                )
                return True

            return False
        except Exception as e:
            logger.debug(
                "Negative gate failed for issue #%s: %s",
                issue.get("number"),
                e,
            )
            return False

    def _quick_keyword_check(self, issue: Dict) -> Tuple[bool, Optional[str], float, str]:
        """Fast pre-filtering using critical keywords."""
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        labels = extract_label_names_lower(issue.get("labels", []))
        label_text = " ".join(labels)

        for category, keywords in self.critical_keywords.items():
            # Check labels (highest confidence)
            for keyword in keywords:
                if keyword in label_text:
                    score = ConfidenceLevel.LABEL_MATCH
                    return True, category, score, self._get_confidence_band(score)

            # Check title (high confidence)
            for keyword in keywords:
                if keyword in title:
                    score = ConfidenceLevel.TITLE_MATCH
                    return True, category, score, self._get_confidence_band(score)

            # Check body (medium-high confidence)
            for keyword in keywords:
                if keyword in body:
                    score = ConfidenceLevel.BODY_MATCH
                    return True, category, score, self._get_confidence_band(score)

        return False, None, 0, "EXCLUDED"


    def _build_issue_text(self, issue: Dict) -> str:
        """Combines issue fields into analyzable text."""
        title = issue.get("title") or ""
        body = issue.get("body") or ""
        labels = extract_label_names(issue.get("labels", []))
        return f"{title}\n{' '.join(labels)}\n{body}"

    def _classify_with_tfidf(self, issue_text: str) -> Dict[str, float]:
        """
        Uses pre-fitted TF-IDF vectorizer and cosine similarity for classification.
        
        This optimized version uses a pre-fitted vectorizer instead of fitting
        a new one for each issue, significantly improving performance.
        """
        # Check if vectorizer is initialized
        if self._vectorizer is None or self._category_vectors is None:
            logger.warning("TF-IDF vectorizer not initialized, falling back to per-issue fitting")
            return self._classify_with_tfidf_fallback(issue_text)
        
        try:
            # Transform issue text using pre-fitted vectorizer
            issue_vector = self._vectorizer.transform([issue_text])
            
            # Calculate similarities with pre-computed category vectors
            similarities = {}
            for i, category in enumerate(self._categories):
                cat_vector = self._category_vectors[i]
                sim = cosine_similarity(issue_vector, cat_vector)
                similarities[category] = float(sim[0][0]) * 100
            
            return similarities
        except Exception as e:
            logger.error("Error in optimized TF-IDF classification: %s", e)
            return self._classify_with_tfidf_fallback(issue_text)

    def _classify_with_tfidf_fallback(self, issue_text: str) -> Dict[str, float]:
        """Fallback TF-IDF classification when pre-fitted vectorizer is unavailable."""
        documents = [issue_text]
        categories = list(self.service_terms.keys())

        # Add category documents
        for category in categories:
            cat_text = " ".join(self.service_terms[category])
            documents.append(cat_text)

        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(documents)
            issue_vector = tfidf_matrix[0]

            similarities = {}
            for i, category in enumerate(categories):
                cat_vector = tfidf_matrix[i + 1]
                sim = cosine_similarity(issue_vector, cat_vector)
                similarities[category] = float(sim[0][0]) * 100

            return similarities
        except Exception as e:
            logger.error("Error in TF-IDF fallback classification: %s", e)
            return {}

    def _classify_with_tfidf_trigram_shadow(self, issue_text: str) -> Dict[str, float]:
        """Experimental tri-gram TF-IDF scoring used only for shadow comparisons."""
        self._ensure_shadow_initialized()
        if self._shadow_vectorizer is None or self._shadow_category_vectors is None:
            return {}

        try:
            issue_vector = self._shadow_vectorizer.transform([issue_text])
            similarities: Dict[str, float] = {}
            for i, category in enumerate(self._categories):
                cat_vector = self._shadow_category_vectors[i]
                sim = cosine_similarity(issue_vector, cat_vector)
                similarities[category] = float(sim[0][0]) * 100
            return similarities
        except Exception as e:
            logger.warning("Error in shadow TF-IDF classification: %s", e)
            return {}

    def _calculate_regex_scores(self, issue: Dict) -> Dict[str, float]:
        """Calculates regex-based matching scores."""
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        labels = extract_label_names_lower(issue.get("labels", []))

        regex_scores = {}
        for category, terms in self.service_terms.items():
            matches = 0
            important_matches = 0

            for term in terms:
                pattern = r"\b" + re.escape(term.lower()) + r"\b"

                # Title matches are most important
                if re.search(pattern, title):
                    important_matches += 3

                # Label matches are important
                for label in labels:
                    if re.search(pattern, label):
                        important_matches += 2

                # Body matches
                if re.search(pattern, body):
                    matches += 1

            term_count = len(terms) if terms else 1
            base_score = (matches / term_count) * 30
            important_score = min(70.0, (important_matches / term_count) * 70)

            regex_scores[category] = min(100.0, base_score + important_score)

        return regex_scores

    def _combine_scores(self, tfidf_scores: Dict[str, float],
                        regex_scores: Dict[str, float]) -> Dict[str, float]:
        """Combines TF-IDF and regex scores with weighting."""
        final_scores = {}
        all_categories = set(list(tfidf_scores.keys()) + list(regex_scores.keys()))

        for category in all_categories:
            tf_component = tfidf_scores.get(category, 0)
            regex_component = regex_scores.get(category, 0)
            final_scores[category] = (TFIDF_WEIGHT * tf_component) + (REGEX_WEIGHT * regex_component)

        return final_scores


    def _evaluate_scores_with_related(
        self, final_scores: Dict[str, float]
    ) -> Tuple[bool, Optional[str], float, str, List[str]]:
        """Evaluates final scores and returns classification with related categories.
        
        Returns:
            Tuple of (is_relevant, primary_category, confidence, confidence_band, related_categories)
        """
        if not final_scores:
            return False, None, 0, "EXCLUDED", []

        # Sort categories by score
        sorted_categories = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_categories:
            return False, None, 0, "EXCLUDED", []
        
        best_category, score = sorted_categories[0]
        confidence_band = self._get_confidence_band(score)
        
        if score < MIN_CONFIDENCE_THRESHOLD:
            return False, None, score, confidence_band, []
        
        # Find related categories (score >= 50% of best score and >= 50 absolute)
        related_threshold = max(score * 0.5, 50)
        related_categories = [
            cat for cat, cat_score in sorted_categories[1:]
            if cat_score >= related_threshold
        ]
        
        return True, best_category, score, confidence_band, related_categories

    def classify_issue_with_related(
        self, issue: Dict
    ) -> Tuple[bool, Optional[str], float, str, List[str]]:
        """
        Determines if issue is relevant and identifies related categories.
        
        This is an enhanced version of classify_issue that also returns
        categories that the issue might be related to (for cross-referencing).

        Args:
            issue: Dictionary containing issue data with 'title', 'body', 'labels'

        Returns:
            Tuple of (is_relevant, primary_category, confidence, confidence_band, related_categories)

        Note:
            related_categories is always empty when a quick keyword match
            is found, since the project currently supports a single service
            category.
        """
        # Quick keyword check first (most efficient)
        is_match, category, confidence, confidence_band = self._quick_keyword_check(issue)
        if self._is_excluded_by_negative_gate(issue):
            return False, None, 0.0, "EXCLUDED", []
        if is_match:
            return True, category, confidence, confidence_band, []

        # Full analysis if quick check fails
        issue_text = self._build_issue_text(issue)
        tfidf_scores = self._classify_with_tfidf(issue_text)
        regex_scores = self._calculate_regex_scores(issue)
        final_scores = self._combine_scores(tfidf_scores, regex_scores)
        
        return self._evaluate_scores_with_related(final_scores)

    def _get_confidence_band(self, score: float) -> str:
        """Get confidence band label for a numeric score.

        Args:
            score: Confidence score in range 0-100.

        Returns:
            Confidence band name: HIGH, REVIEW, or EXCLUDED.
        """
        if score >= HIGH_CONFIDENCE_THRESHOLD:
            return "HIGH"
        if score >= MEDIUM_CONFIDENCE_THRESHOLD:
            return "REVIEW"
        return "EXCLUDED"

    def get_shadow_score_comparison(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Return baseline vs experimental scoring details without changing decisions."""
        self._ensure_shadow_initialized()
        issue_text = self._build_issue_text(issue)
        regex_scores = self._calculate_regex_scores(issue)

        baseline_scores = self._combine_scores(
            self._classify_with_tfidf(issue_text),
            regex_scores,
        )
        shadow_scores = self._combine_scores(
            self._classify_with_tfidf_trigram_shadow(issue_text),
            regex_scores,
        )

        baseline_category = None
        baseline_score = 0.0
        if baseline_scores:
            baseline_category, baseline_score = max(baseline_scores.items(), key=lambda x: x[1])

        shadow_category = None
        shadow_score = 0.0
        if shadow_scores:
            shadow_category, shadow_score = max(shadow_scores.items(), key=lambda x: x[1])

        return {
            "baseline": {
                "category": baseline_category,
                "score": float(baseline_score),
                "is_relevant": bool(baseline_score >= MIN_CONFIDENCE_THRESHOLD),
                "band": self._get_confidence_band(float(baseline_score)),
            },
            "shadow": {
                "category": shadow_category,
                "score": float(shadow_score),
                "is_relevant": bool(shadow_score >= MIN_CONFIDENCE_THRESHOLD),
                "band": self._get_confidence_band(float(shadow_score)),
            },
            "score_delta": float(shadow_score - baseline_score),
        }

    def _log_scores(self, issue: Dict, scores: Dict[str, float]) -> None:
        """Logs classification scores for debugging."""
        logger.debug("Issue #%s: %s", issue.get('number'), issue.get('title'))
        for category, score in scores.items():
            logger.debug("  - %s: %.2f%%", category, score)
