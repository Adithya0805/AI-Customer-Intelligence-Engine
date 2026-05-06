import logging
from typing import List, Dict
from .base import BaseConnector
try:
    from google_play_scraper import reviews, Sort
except ImportError:
    reviews = None

logger = logging.getLogger(__name__)

class GooglePlayConnector(BaseConnector):
    """Connector for Google Play Store reviews using google-play-scraper."""
    
    async def scrape(self, url: str, max_reviews: int = 100) -> List[Dict]:
        logger.info(f"Scraping Google Play: {url}")
        
        if reviews is None:
            logger.error("google-play-scraper not installed.")
            return []

        # Extract app ID from URL (e.g., https://play.google.com/store/apps/details?id=com.whatsapp)
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        app_id = params.get('id', [None])[0]
        
        if not app_id:
            logger.error(f"Could not extract app ID from {url}")
            return []

        try:
            # Note: reviews() is a blocking call, but for simplicity we call it here. 
            # In a full async app, we would run_in_executor.
            result, _ = reviews(
                app_id,
                lang='en',
                country='us',
                sort=Sort.NEWEST,
                count=max_reviews
            )
            
            processed_reviews = []
            for r in result:
                processed_reviews.append({
                    "original_text": r['content'],
                    "rating": float(r['score']),
                    "date": r['at'].isoformat(),
                    "source": "google_play",
                    "url": url
                })
            return processed_reviews
        except Exception as e:
            logger.error(f"Google Play scrape failed: {e}")
            return []
