import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import json
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class Review:
    text: str
    rating: Optional[float]
    date: str
    source: str
    url: str

class GenericScraper:
    """
    A base scraper that attempts to find review-like elements on a generic URL.
    In a real-world scenario, you would subclass this for specific sites (Amazon, Trustpilot, etc.).
    """
    def __init__(self, headers: Optional[dict] = None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_html(self, url: str) -> str:
        """Fetches HTML content from the given URL."""
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.RequestError as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return ""

    def parse_reviews(self, html: str, url: str) -> List[Review]:
        """
        Attempts a generic heuristic-based extraction of reviews.
        Looks for elements with classes containing 'review', 'comment', 'rating'.
        """
        soup = BeautifulSoup(html, "html.parser")
        reviews = []
        
        # Generic heuristic: find divs or articles that might be reviews
        potential_reviews = soup.find_all(lambda tag: tag.name in ['div', 'article', 'li'] and 
                                          tag.get('class') and 
                                          any(isinstance(c, str) and 'review' in c.lower() for c in tag.get('class')))
        
        if not potential_reviews:
            # Fallback: look for generic paragraphs if no review containers found
            # This is a very naive fallback for demonstration
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20: # Arbitrary threshold for a "review"
                    reviews.append(Review(
                        text=text,
                        rating=None, # Cannot reliably guess rating generically
                        date=datetime.now().isoformat(),
                        source="generic",
                        url=url
                    ))
            return reviews

        for item in potential_reviews:
            # Try to find text
            text_elem = item.find(['p', 'span', 'div'], class_=lambda c: c and isinstance(c, str) and 'text' in c.lower())
            text = text_elem.get_text(strip=True) if text_elem else item.get_text(strip=True)
            
            # Try to find rating
            rating_elem = item.find(class_=lambda c: c and isinstance(c, str) and ('rating' in c.lower() or 'star' in c.lower()))
            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Attempt to extract a number
                import re
                match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if match:
                    rating = float(match.group(1))

            if len(text) > 10:
                reviews.append(Review(
                    text=text,
                    rating=rating,
                    date=datetime.now().isoformat(),
                    source="generic",
                    url=url
                ))
                
        return reviews

    def scrape(self, url: str) -> List[Review]:
        """Main method to execute scraping."""
        logger.info(f"Starting scrape for {url}")
        html = self.fetch_html(url)
        if not html:
            return []
        
        reviews = self.parse_reviews(html, url)
        logger.info(f"Found {len(reviews)} reviews.")
        return reviews

    @staticmethod
    def parse_from_text(raw_text: str) -> List[Review]:
        """Parses a multi-line string into Reviews."""
        reviews = []
        for line in raw_text.splitlines():
            line = line.strip()
            if len(line) > 5:
                reviews.append(Review(
                    text=line,
                    rating=None,
                    date=datetime.now().isoformat(),
                    source="text_paste",
                    url="N/A"
                ))
        return reviews

    @staticmethod
    def parse_from_csv(df: pd.DataFrame, text_col: str) -> List[Review]:
        """Parses a DataFrame into Reviews, expecting a specific text column."""
        reviews = []
        if text_col not in df.columns:
            return reviews
        
        for idx, row in df.iterrows():
            text = str(row[text_col]).strip()
            if text and text.lower() != 'nan' and len(text) > 5:
                # Optionally look for a date or rating column, but defaults are fine
                reviews.append(Review(
                    text=text,
                    rating=None,
                    date=datetime.now().isoformat(),
                    source="csv_upload",
                    url="N/A"
                ))
        return reviews

# To support JS-rendered pages, we could add a PlaywrightScraper class here.
