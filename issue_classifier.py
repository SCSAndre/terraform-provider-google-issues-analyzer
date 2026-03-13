"""Issue classification using TF-IDF and regex matching."""
import re
import logging
from typing import Dict, Tuple, Optional, List, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from config import TFIDF_WEIGHT, REGEX_WEIGHT, MIN_CONFIDENCE_THRESHOLD, ConfidenceLevel
from service_definitions import get_service_terms, get_critical_keywords

logger = logging.getLogger(__name__)


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
        self._initialize_shadow_tfidf()

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
            logger.error(f"Error initializing TF-IDF vectorizer: {e}")
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

    def classify_issue(self, issue: Dict) -> Tuple[bool, Optional[str], float]:
        """
        Determines if issue is relevant to target services.

        Args:
            issue: Dictionary containing issue data with 'title', 'body', 'labels'

        Returns:
            Tuple of (is_relevant, service_category, confidence)
        """
        # Quick keyword check first (most efficient)
        is_match, category, confidence = self._quick_keyword_check(issue)
        if is_match:
            return True, category, confidence

        # Full analysis if quick check fails
        return self._perform_full_analysis(issue)

    def _quick_keyword_check(self, issue: Dict) -> Tuple[bool, Optional[str], float]:
        """Fast pre-filtering using critical keywords."""
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        labels = [label["name"].lower() for label in issue.get("labels", [])]
        label_text = " ".join(labels)

        for category, keywords in self.critical_keywords.items():
            # Check labels (highest confidence)
            for keyword in keywords:
                if keyword in label_text:
                    return True, category, ConfidenceLevel.LABEL_MATCH

            # Check title (high confidence)
            for keyword in keywords:
                if keyword in title:
                    return True, category, ConfidenceLevel.TITLE_MATCH

            # Check body (medium-high confidence)
            for keyword in keywords:
                if keyword in body:
                    return True, category, ConfidenceLevel.BODY_MATCH

        return False, None, 0

    def _perform_full_analysis(self, issue: Dict) -> Tuple[bool, Optional[str], float]:
        """Comprehensive TF-IDF and regex analysis."""
        issue_text = self._build_issue_text(issue)

        # TF-IDF classification
        tfidf_scores = self._classify_with_tfidf(issue_text)

        # Regex-based scoring
        regex_scores = self._calculate_regex_scores(issue)

        # Combine scores
        final_scores = self._combine_scores(tfidf_scores, regex_scores)

        # Log for debugging
        if issue.get("number") and issue.get("number") % 100 == 0:
            self._log_scores(issue, final_scores)

        return self._evaluate_scores(final_scores)

    def _build_issue_text(self, issue: Dict) -> str:
        """Combines issue fields into analyzable text."""
        title = issue.get("title") or ""
        body = issue.get("body") or ""
        labels = [label["name"] for label in issue.get("labels", [])]
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
            logger.error(f"Error in optimized TF-IDF classification: {e}")
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
            logger.error(f"Error in TF-IDF fallback classification: {e}")
            return {}

    def _classify_with_tfidf_trigram_shadow(self, issue_text: str) -> Dict[str, float]:
        """Experimental tri-gram TF-IDF scoring used only for shadow comparisons."""
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
        labels = [label["name"].lower() for label in issue.get("labels", [])]

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

    def _evaluate_scores(self, final_scores: Dict[str, float]) -> Tuple[bool, Optional[str], float]:
        """Evaluates final scores and returns classification decision."""
        if not final_scores:
            return False, None, 0

        best_category, score = max(final_scores.items(), key=lambda x: x[1])

        if score >= MIN_CONFIDENCE_THRESHOLD:
            return True, best_category, score

        return False, None, 0

    def _evaluate_scores_with_related(
        self, final_scores: Dict[str, float]
    ) -> Tuple[bool, Optional[str], float, List[str]]:
        """Evaluates final scores and returns classification with related categories.
        
        Returns:
            Tuple of (is_relevant, primary_category, confidence, related_categories)
        """
        if not final_scores:
            return False, None, 0, []

        # Sort categories by score
        sorted_categories = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_categories:
            return False, None, 0, []
        
        best_category, score = sorted_categories[0]
        
        if score < MIN_CONFIDENCE_THRESHOLD:
            return False, None, 0, []
        
        # Find related categories (score >= 50% of best score and >= 50 absolute)
        related_threshold = max(score * 0.5, 50)
        related_categories = [
            cat for cat, cat_score in sorted_categories[1:]
            if cat_score >= related_threshold
        ]
        
        return True, best_category, score, related_categories

    def classify_issue_with_related(
        self, issue: Dict
    ) -> Tuple[bool, Optional[str], float, List[str]]:
        """
        Determines if issue is relevant and identifies related categories.
        
        This is an enhanced version of classify_issue that also returns
        categories that the issue might be related to (for cross-referencing).

        Args:
            issue: Dictionary containing issue data with 'title', 'body', 'labels'

        Returns:
            Tuple of (is_relevant, primary_category, confidence, related_categories)
        """
        # Quick keyword check first (most efficient)
        is_match, category, confidence = self._quick_keyword_check(issue)
        if is_match:
            # For quick matches, still check for related categories
            issue_text = self._build_issue_text(issue)
            tfidf_scores = self._classify_with_tfidf(issue_text)
            regex_scores = self._calculate_regex_scores(issue)
            final_scores = self._combine_scores(tfidf_scores, regex_scores)
            
            # Remove the matched category and find related ones
            related_threshold = max(confidence * 0.5, 50)
            related_categories = [
                cat for cat, cat_score in final_scores.items()
                if cat != category and cat_score >= related_threshold
            ]
            return True, category, confidence, related_categories

        # Full analysis if quick check fails
        issue_text = self._build_issue_text(issue)
        tfidf_scores = self._classify_with_tfidf(issue_text)
        regex_scores = self._calculate_regex_scores(issue)
        final_scores = self._combine_scores(tfidf_scores, regex_scores)
        
        return self._evaluate_scores_with_related(final_scores)

    def get_shadow_score_comparison(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Return baseline vs experimental scoring details without changing decisions."""
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
            },
            "shadow": {
                "category": shadow_category,
                "score": float(shadow_score),
                "is_relevant": bool(shadow_score >= MIN_CONFIDENCE_THRESHOLD),
            },
            "score_delta": float(shadow_score - baseline_score),
        }

    def _log_scores(self, issue: Dict, scores: Dict[str, float]) -> None:
        """Logs classification scores for debugging."""
        logger.debug(f"Issue #{issue.get('number')}: {issue.get('title')}")
        for category, score in scores.items():
            logger.debug(f"  - {category}: {score:.2f}%")
