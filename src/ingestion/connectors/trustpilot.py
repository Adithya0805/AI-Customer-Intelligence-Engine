import logging
from typing import List, Dict
from bs4 import BeautifulSoup
from .base import BaseConnector
import urllib.parse

logger = logging.getLogger(__name__)

class TrustpilotConnector(BaseConnector):
    """Connector for Trustpilot reviews."""
    
    async def scrape(self, url: str, max_reviews: int = 100) -> List[Dict]:
        logger.info(f"Scraping Trustpilot: {url}")
        reviews = []
        page = 1
        
        while len(reviews) < max_reviews:
            # Construct page URL
            parsed_url = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(parsed_url.query)
            query['page'] = page
            current_url = parsed_url._replace(query=urllib.parse.urlencode(query, doseq=True)).geturl()
            
            try:
                html = await self.fetch_html(current_url)
                soup = BeautifulSoup(html, 'html.parser')
                
                # Trustpilot review containers
                containers = soup.select('section.styles_reviewContentwrapper__zH_9M')
                if not containers:
                    break
                
                for container in containers:
                    if len(reviews) >= max_reviews:
                        break
                        
                    # Extract data
                    title_el = container.select_one('h2[data-service-review-title-typography]')
                    text_el = container.select_one('p[data-service-review-text-typography]')
                    rating_el = container.parent.select_one('div.styles_reviewHeader__iU9Px img')
                    date_el = container.select_one('time')
                    
                    rating = 0
                    if rating_el and 'alt' in rating_el.attrs:
                        # "Rated 5 out of 5 stars"
                        rating = int(rating_el.attrs['alt'].split()[1])
                        
                    review = {
                        "original_text": f"{title_el.text if title_el else ''} {text_el.text if text_el else ''}".strip(),
                        "rating": float(rating),
                        "date": date_el['datetime'] if date_el else None,
                        "source": "trustpilot",
                        "url": url
                    }
                    reviews.append(review)
                
                page += 1
            except Exception as e:
                logger.error(f"Error scraping Trustpilot page {page}: {e}")
                break
                
        return reviews
