import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.intelligence.pressure import PressureDetector

def test_pressure_detector():
    detector = PressureDetector(recent_days=7, baseline_days=30, alert_threshold=1.5, min_reviews=2)
    
    now = datetime.now()
    
    # Create mock data where "delivery" becomes a big issue recently
    data = [
        # Baseline
        {"date": now - timedelta(days=20), "clean_text": "bad product", "sentiment": "negative"},
        {"date": now - timedelta(days=21), "clean_text": "terrible customer service", "sentiment": "negative"},
        {"date": now - timedelta(days=22), "clean_text": "delivery was slightly late", "sentiment": "negative"},
        # Recent
        {"date": now - timedelta(days=2), "clean_text": "worst delivery ever", "sentiment": "negative"},
        {"date": now - timedelta(days=3), "clean_text": "delivery delayed again", "sentiment": "negative"},
        {"date": now - timedelta(days=4), "clean_text": "delivery is awful", "sentiment": "negative"},
    ]
    df = pd.DataFrame(data)
    
    alerts = detector.detect(df)
    
    assert len(alerts) > 0
    # "delivery" should be the top keyword causing an alert
    assert any('delivery' in alert['keyword'] for alert in alerts)
