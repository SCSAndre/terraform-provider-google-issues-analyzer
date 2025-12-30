"""Issue classification using TF-IDF and regex matching."""
import re
import logging
from typing import Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import TFIDF_WEIGHT, REGEX_WEIGHT, MIN_CONFIDENCE_THRESHOLD
from service_definitions import get_service_terms, get_critical_keywords

logger = logging.getLogger(__name__)


class IssueClassifier:
    """Classifies issues based on service relevance."""
                                              
    def __init__(self):
        self.service_terms = get_service_terms()
        self.critical_keywords = get_critical_keywords()

    def classify_issue(self, issue: Dict) -> Tuple[bool, Optional[str], float]:
        """
        Determines if issue is relevant to target services.

        Returns:
            Tuple of (is_relevant, service_category, confidence)
        """
        # Quick keyword check first
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
                    return True, category, 90.0

            # Check title (high confidence)
            for keyword in keywords:
                if keyword in title:
                    return True, category, 85.0

            # Check body (medium-high confidence)
            for keyword in keywords:
                if keyword in body:
                    return True, category, 75.0

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
        """Uses TF-IDF and cosine similarity for classification."""
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
            logger.error(f"Error in TF-IDF classification: {e}")
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

    def _log_scores(self, issue: Dict, scores: Dict[str, float]) -> None:
        """Logs classification scores for debugging."""
        logger.debug(f"Issue #{issue.get('number')}: {issue.get('title')}")
        for category, score in scores.items():
            logger.debug(f"  - {category}: {score:.2f}%")
