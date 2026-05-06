import pytest
from unittest.mock import MagicMock, patch
from src.intelligence.analyzer import SentimentAnalyzer

@pytest.fixture
def mock_analyzer():
    with patch('src.intelligence.analyzer.pipeline') as mock_pipeline:
        # Mock the pipeline return value
        mock_instance = MagicMock()
        mock_instance.return_value = [{'label': 'LABEL_2', 'score': 0.99}]
        mock_pipeline.return_value = mock_instance
        
        analyzer = SentimentAnalyzer()
        # Ensure lazy loading happens or mock it
        analyzer._nlp = mock_instance
        return analyzer

def test_analyze_positive(mock_analyzer):
    result = mock_analyzer.analyze("This is great!")
    assert result['label'] == 'positive'
    assert result['score'] > 0.5

def test_analyze_empty(mock_analyzer):
    result = mock_analyzer.analyze("")
    assert result['label'] == 'neutral'
    assert result['score'] == 0.0

def test_batch_analysis(mock_analyzer):
    texts = ["I love it", "I hate it"]
    # Mock batch return
    mock_analyzer._nlp.return_value = [
        {'label': 'LABEL_2', 'score': 0.9},
        {'label': 'LABEL_0', 'score': 0.8}
    ]
    results = mock_analyzer.analyze_batch(texts)
    assert len(results) == 2
    assert results[0]['label'] == 'positive'
    assert results[1]['label'] == 'negative'
