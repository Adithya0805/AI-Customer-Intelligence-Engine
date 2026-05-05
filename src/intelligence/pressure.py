import logging
import pandas as pd
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PressureDetector:
    """
    The Emerging Issue Detector.
    Identifies if specific negative keywords/complaints are growing in frequency
    (like water pressure building up) to alert before a crisis.
    """
    def __init__(self, recent_days: int = 7, baseline_days: int = 30, alert_threshold: float = 2.0, min_reviews: int = 5):
        self.recent_days = recent_days
        self.baseline_days = baseline_days
        self.alert_threshold = alert_threshold
        self.min_reviews = min_reviews
        # Tfidf to extract significant keywords (unigrams and bigrams)
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=100)

    def extract_keywords(self, texts: List[str]) -> Dict[str, float]:
        """Extracts top keywords and their average TF-IDF scores from a list of texts."""
        if not texts:
            return {}
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            feature_names = self.vectorizer.get_feature_names_out()
            avg_scores = tfidf_matrix.mean(axis=0).A1
            
            # Sort by score
            keywords = {feature_names[i]: float(avg_scores[i]) for i in avg_scores.argsort()[::-1]}
            return keywords
        except ValueError:
            # Handles empty vocabulary error if texts are empty or only stopwords
            return {}

    def detect(self, reviews_df: pd.DataFrame) -> List[dict]:
        """
        Analyzes a DataFrame of reviews (requires 'date', 'clean_text', 'sentiment' columns).
        Returns a list of alerts.
        """
        if reviews_df.empty or len(reviews_df) < self.min_reviews:
            logger.info("Not enough data to run pressure detection.")
            return []

        # Ensure datetime
        reviews_df['date'] = pd.to_datetime(reviews_df['date'])
        
        # Filter to only negative reviews
        negative_reviews = reviews_df[reviews_df['sentiment'] == 'negative']
        if negative_reviews.empty:
            return []

        now = datetime.now()
        recent_cutoff = now - timedelta(days=self.recent_days)
        baseline_cutoff = now - timedelta(days=self.baseline_days)

        recent_df = negative_reviews[negative_reviews['date'] >= recent_cutoff]
        baseline_df = negative_reviews[(negative_reviews['date'] >= baseline_cutoff) & (negative_reviews['date'] < recent_cutoff)]

        if recent_df.empty:
            return []

        recent_keywords = self.extract_keywords(recent_df['clean_text'].tolist())
        baseline_keywords = self.extract_keywords(baseline_df['clean_text'].tolist())

        alerts = []
        for kw, recent_score in recent_keywords.items():
            baseline_score = baseline_keywords.get(kw, 0.0001) # Small epsilon to avoid division by zero
            
            # Calculate Pressure Score (Ratio of recent importance to baseline importance)
            pressure_score = recent_score / baseline_score
            
            if pressure_score >= self.alert_threshold and recent_score > 0.05: # Also require some minimum absolute importance
                alerts.append({
                    "keyword": kw,
                    "pressure_score": round(pressure_score, 2),
                    "recent_importance": round(recent_score, 4),
                    "baseline_importance": round(baseline_score, 4),
                    "timestamp": now.isoformat(),
                    "status": "EMERGING_CRISIS" if pressure_score >= (self.alert_threshold * 1.5) else "WARNING"
                })

        # Sort alerts by pressure score
        alerts.sort(key=lambda x: x['pressure_score'], reverse=True)
        return alerts
