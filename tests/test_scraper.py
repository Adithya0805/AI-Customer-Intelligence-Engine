import pytest
from src.ingestion.cleaner import ReviewCleaner
from src.ingestion.scraper import GenericScraper

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
