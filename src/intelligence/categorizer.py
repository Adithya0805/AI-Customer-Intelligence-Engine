import logging
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np

logger = logging.getLogger(__name__)

class TopicCategorizer:
    """
    Auto-discovers topics/clusters from a batch of reviews using TF-IDF and KMeans.
    Uses silhouette score to adaptively determine the optimal number of clusters.
    """
    def __init__(self, max_clusters: int = 8, max_features: int = 500):
        self.max_clusters = max_clusters
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            stop_words='english', 
            ngram_range=(1, 2), 
            max_features=self.max_features,
            min_df=2
        )

    def find_optimal_k(self, tfidf_matrix) -> int:
        """Finds the optimal number of clusters using silhouette score."""
        n_samples = tfidf_matrix.shape[0]
        if n_samples < 5:
            return 1
        
        # Candidate k values: from 2 up to min(max_clusters, n_samples-1)
        limit = min(self.max_clusters, n_samples - 1)
        if limit < 2:
            return 1

        best_k = 2
        best_score = -1
        
        for k in range(2, limit + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(tfidf_matrix)
            score = silhouette_score(tfidf_matrix, kmeans.labels_)
            if score > best_score:
                best_score = score
                best_k = k
        
        return best_k

    def categorize(self, texts: List[str]) -> Dict:
        """
        Clusters the given texts and returns a summary.
        Adaptive k-selection based on silhouette score.
        """
        if not texts or len(texts) < 5:
            return {
                "clusters": {0: {"label": "General Feedback", "indices": list(range(len(texts))) }},
                "labels": [0] * len(texts)
            }
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Use adaptive k-selection
            optimal_k = self.find_optimal_k(tfidf_matrix)
            
            if optimal_k == 1:
                return {
                    "clusters": {0: {"label": "General Feedback", "indices": list(range(len(texts))) }},
                    "labels": [0] * len(texts)
                }

            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto')
            kmeans.fit(tfidf_matrix)
            
            cluster_labels = kmeans.labels_.tolist()
            feature_names = self.vectorizer.get_feature_names_out()
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            
            clusters_info = {}
            for i in range(optimal_k):
                indices = [idx for idx, label in enumerate(cluster_labels) if label == i]
                if not indices:
                    continue
                    
                # Generate a richer label based on top 3 keywords
                top_features = [feature_names[ind] for ind in order_centroids[i, :3]]
                label_str = " & ".join([f.title() for f in top_features if f.strip()])
                if not label_str:
                    label_str = f"Topic Group {i+1}"
                
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
            return {
                "clusters": {0: {"label": "General Feedback", "indices": list(range(len(texts))) }},
                "labels": [0] * len(texts)
            }
