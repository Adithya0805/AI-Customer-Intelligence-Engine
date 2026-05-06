import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.processing.pipeline import IntelligencePipeline
from src.ingestion.scraper import Review

@pytest.fixture
def mock_pipeline():
    with patch('src.intelligence.analyzer.SentimentAnalyzer') as mock_sent:
        with patch('src.intelligence.summarizer.LLMSummarizer') as mock_sum:
            with patch('src.database.client.get_service_client') as mock_db:
                pipeline = IntelligencePipeline()
                # Mock methods to avoid real AI calls
                pipeline.analyzer = MagicMock()
                pipeline.analyzer.analyze_batch.return_value = [{"label": "positive", "score": 0.9}]
                pipeline.summarizer.generate_executive_summary.return_value = "Mock summary"
                return pipeline

def test_pipeline_processing(mock_pipeline):
    raw_reviews = [
        Review(text="Great product", rating=5.0, date="2024-01-01", source="test", url="http://test.com")
    ]
    
    # Mock database save
    mock_pipeline._save_to_supabase = MagicMock()
    mock_pipeline._load_historical_data = MagicMock(return_value=pd.DataFrame())
    
    result = mock_pipeline._process_reviews(raw_reviews)
    
    assert result['status'] == 'success'
    assert result['processed_count'] == 1
    assert result['executive_summary'] == "Mock summary"
    mock_pipeline._save_to_supabase.assert_called()

def test_pipeline_empty_input(mock_pipeline):
    result = mock_pipeline._process_reviews([])
    assert result['status'] == 'error'
    assert "No reviews" in result['message']
