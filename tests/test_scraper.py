import pytest
from unittest.mock import MagicMock, patch
from src.ingestion.cleaner import ReviewCleaner
from src.ingestion.scraper import GenericScraper

@pytest.fixture
def mock_scraper():
    return GenericScraper()

def test_cleaner_remove_html():
    cleaner = ReviewCleaner()
    html_text = "<p>This is a <b>great</b> product!</p>"
    assert cleaner.remove_html(html_text) == "This is a great product!"

def test_cleaner_handle_tamil():
    cleaner = ReviewCleaner()
    # "வணக்கம்" (Vanakkam) transliterates to something phonetic
    tamil_text = "வணக்கம்"
    result = cleaner.handle_multilingual(tamil_text)
    assert result != tamil_text # Transliteration should change the string

def test_parse_from_text(mock_scraper):
    text = "Great product!\nWorst service ever.\nIt was okay."
    reviews = mock_scraper.parse_from_text(text)
    assert len(reviews) == 3
    assert reviews[0].text == "Great product!"
    assert reviews[1].text == "Worst service ever."

def test_scrape_logic(mock_scraper):
    with patch('httpx.Client') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><div class='review'>Great!</div></body></html>"
        
        mock_client_instance = mock_client.return_value.__enter__.return_value
        mock_client_instance.get.return_value = mock_response
        
        # Test a generic scrape
        reviews = mock_scraper.scrape("https://example.com")
        # Since it's heuristic based, we just check it doesn't crash
        assert isinstance(reviews, list)

def test_scraper_generic_parsing():
    scraper = GenericScraper()
    mock_html = """
    <html><body>
        <div class="review">
            <p class="text">Amazing service!</p>
            <span class="rating">5 stars</span>
        </div>
        <div class="user-comment">
            <div class="text">Terrible experience.</div>
            <div class="rating">1.0 out of 5</div>
        </div>
    </body></html>
    """
    reviews = scraper.parse_reviews(mock_html, "http://test.com")
    assert len(reviews) == 2
    assert reviews[0].text == "Amazing service!"
    assert reviews[0].rating == 5.0
    assert reviews[1].text == "Terrible experience."
    assert reviews[1].rating == 1.0
