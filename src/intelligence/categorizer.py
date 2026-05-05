import logging
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

logger = logging.getLogger(__name__)

class TopicCategorizer:
    """
    Auto-discovers topics/clusters from a batch of reviews using TF-IDF and KMeans.
    """
    def __init__(self, n_clusters: int = 4, max_features: int = 500):
        self.n_clusters = n_clusters
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            stop_words='english', 
            ngram_range=(1, 2), 
            max_features=self.max_features,
            min_df=2 # requires term to be in at least 2 docs
        )

    def categorize(self, texts: List[str]) -> Dict:
        """
        Clusters the given texts and returns a summary.
        If too few texts, groups all under 'General'.
        Returns:
            {
                "clusters": {
                    0: {"label": "Keyword1, Keyword2", "indices": [0, 5, 12, ...]},
                    ...
                },
                "labels": [0, 1, 0, 2, ...] # mapped to texts index
            }
        """
        if not texts or len(texts) < 5:
            # Not enough data to cluster meaningfully
            return {
                "clusters": {0: {"label": "General Feedback", "indices": list(range(len(texts))) }},
                "labels": [0] * len(texts)
            }
        
        # Adjust n_clusters if texts are fewer than n_clusters
        actual_clusters = min(self.n_clusters, len(texts) // 2)
        if actual_clusters < 2:
            return {
                "clusters": {0: {"label": "General Feedback", "indices": list(range(len(texts))) }},
                "labels": [0] * len(texts)
            }

        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Use KMeans with a fixed random state for reproducibility within the same batch
            kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init='auto')
            kmeans.fit(tfidf_matrix)
            
            cluster_labels = kmeans.labels_.tolist()
            feature_names = self.vectorizer.get_feature_names_out()
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            
            clusters_info = {}
            for i in range(actual_clusters):
                # Get indices of texts in this cluster
                indices = [idx for idx, label in enumerate(cluster_labels) if label == i]
                
                # If cluster is empty somehow, skip
                if not indices:
                    continue
                    
                # Generate a label based on top 2 keywords
                top_features = [feature_names[ind] for ind in order_centroids[i, :2]]
                label_str = " & ".join([f.title() for f in top_features])
                if not label_str:
                    label_str = "Miscellaneous"
                
                clusters_info[i] = {
                    "label": label_str,
                    "indices": indices
                }
                
            return {
                "clusters": clusters_info,
                "labels": cluster_labels
            }
            
        except Exception as e:
            logger.error(f"Error during topic categorization: {e}")
            # Fallback
            return {
                "clusters": {0: {"label": "General Feedback", "indices": list(range(len(texts))) }},
                "labels": [0] * len(texts)
            }
