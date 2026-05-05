import pytest
from src.intelligence.analyzer import SentimentAnalyzer

def test_sentiment_analyzer():
    # In a real CI environment, we might mock the model or use a tiny model
    # to prevent large downloads during testing.
    # Here we assume the model downloads/exists.
    analyzer = SentimentAnalyzer()
    
    pos_result = analyzer.analyze("I absolutely love this product!")
    assert pos_result['label'] == 'positive'
    assert pos_result['score'] > 0.5
    
    neg_result = analyzer.analyze("This is the worst service I have ever received.")
    assert neg_result['label'] == 'negative'
    assert neg_result['score'] > 0.5
    
    empty_result = analyzer.analyze("")
    assert empty_result['label'] == 'neutral'
