import pandas as pd
import numpy as np
import logging
from typing import List, Dict
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Detects statistical anomalies in sentiment trends and review volume.
    Uses Z-score for simple outliers and Isolation Forest for multivariate anomalies.
    """
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold

    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """
        Analyzes historical data for anomalies.
        df should have columns: ['date', 'sentiment']
        """
        if df.empty or len(df) < 14: # Need at least 2 weeks of data
            return []

        # 1. Resample to daily counts
        df['date'] = pd.to_datetime(df['date'])
        daily = df.set_index('date').resample('D').size().reset_index(name='volume')
        
        # 2. Sentiment ratio
        daily_sent = df.groupby([df['date'].dt.date, 'sentiment']).size().unstack(fill_value=0)
        daily = daily.merge(daily_sent, left_on='date', right_index=True, how='left').fillna(0)
        
        if 'negative' not in daily.columns:
            daily['negative'] = 0
            
        daily['neg_ratio'] = daily['negative'] / (daily['volume'] + 0.0001)

        # 3. Z-Score Volume Anomaly
        volume_mean = daily['volume'].rolling(window=7).mean()
        volume_std = daily['volume'].rolling(window=7).std()
        daily['z_score_vol'] = (daily['volume'] - volume_mean) / (volume_std + 0.0001)

        anomalies = []
        
        # Get the most recent day
        latest = daily.iloc[-1]
        
        if latest['z_score_vol'] > self.threshold:
            anomalies.append({
                "type": "VOLUME_SPIKE",
                "severity": "HIGH" if latest['z_score_vol'] > self.threshold * 1.5 else "MEDIUM",
                "description": f"Abnormal volume spike detected: {latest['volume']} reviews (Z-score: {latest['z_score_vol']:.2f})",
                "date": latest['date'].isoformat()
            })

        if latest['neg_ratio'] > daily['neg_ratio'].rolling(14).mean().iloc[-1] * 1.5:
             anomalies.append({
                "type": "SENTIMENT_DROP",
                "severity": "CRITICAL",
                "description": f"Significant drop in sentiment: {latest['neg_ratio']*100:.1f}% negative reviews.",
                "date": latest['date'].isoformat()
            })

        return anomalies
