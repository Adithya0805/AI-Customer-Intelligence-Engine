import httpx
import random
import time
import re
import logging
import asyncio
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
from config import settings

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
    Hardened with retries, UA rotation, and production-ready heuristics.
    """
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
    ]

    def __init__(self, headers: Optional[dict] = None):
        self.base_headers = headers or {}
        self.max_retries = 3
        self.timeout = settings.SCRAPE_TIMEOUT

    def _get_headers(self) -> Dict:
        headers = self.base_headers.copy()
        headers["User-Agent"] = random.choice(self.USER_AGENTS)
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        headers["Accept-Language"] = "en-US,en;q=0.5"
        return headers

    async def fetch_html_async(self, url: str) -> str:
        """Fetches HTML content with retries and backoff (async)."""
        async with httpx.AsyncClient(headers=self._get_headers(), follow_redirects=True, timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Attempt {attempt+1} failed for {url}: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        return ""

    def fetch_html(self, url: str) -> str:
        """Synchronous wrapper for fetch_html_async (for legacy support)."""
        try:
            return asyncio.run(self.fetch_html_async(url))
        except RuntimeError:
            # If loop already running (e.g. in Streamlit)
            with httpx.Client(headers=self._get_headers(), follow_redirects=True, timeout=self.timeout) as client:
                response = client.get(url)
                return response.text

    def parse_reviews(self, html: str, url: str) -> List[Review]:
        """Generic heuristic-based extraction of reviews."""
        soup = BeautifulSoup(html, "html.parser")
        reviews = []
        
        # 1. Look for common review containers
        containers = soup.find_all(lambda tag: tag.name in ['div', 'article', 'section', 'li'] and 
                                   tag.get('class') and 
                                   any(isinstance(c, str) and any(kw in c.lower() for kw in ['review', 'comment', 'feedback', 'testimonial']) for c in tag.get('class')))
        
        if not containers:
            # Fallback 2: Look for long paragraphs in blocks
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 40:
                    reviews.append(Review(
                        text=text,
                        rating=None,
                        date=datetime.now().isoformat(),
                        source="generic_p",
                        url=url
                    ))
            return reviews[:settings.MAX_REVIEWS_PER_SCRAPE]

        for item in containers:
            if len(reviews) >= settings.MAX_REVIEWS_PER_SCRAPE:
                break
                
            text = ""
            potential_text = item.find_all(['p', 'span', 'div'], recursive=True)
            if potential_text:
                texts = [t.get_text(strip=True) for t in potential_text if len(t.get_text(strip=True)) > 10]
                if texts:
                    text = max(texts, key=len)
            
            if not text:
                text = item.get_text(strip=True)

            rating = None
            rating_match = re.search(r'(\d+(\.\d+)?)', item.get_text())
            if rating_match:
                try:
                    val = float(rating_match.group(1))
                    if 1.0 <= val <= 5.0:
                        rating = val
                except ValueError:
                    pass

            if len(text) > 15:
                reviews.append(Review(
                    text=text,
                    rating=rating,
                    date=datetime.now().isoformat(),
                    source="generic_container",
                    url=url
                ))
                
        return reviews

    async def scrape_async(self, url: str, max_reviews: int = 100) -> List[Review]:
        """Scrapes reviews from a URL using specific connectors or generic heuristics."""
        from .connectors import detect_connector
        
        connector = detect_connector(url)
        if connector:
            logger.info(f"Using specialized connector for {url}")
            try:
                results = await connector.scrape(url, max_reviews)
                return [Review(
                    text=r['original_text'],
                    rating=r['rating'],
                    date=r['date'] or datetime.now().isoformat(),
                    source=r['source'],
                    url=r['url']
                ) for r in results]
            except Exception as e:
                logger.error(f"Specialized connector failed: {e}. Falling back to generic.")
            
        logger.info(f"Using generic scraper for {url}")
        html = await self.fetch_html_async(url)
        if not html:
            return []
        
        return self.parse_reviews(html, url)

    def scrape(self, url: str) -> List[Review]:
        """Synchronous wrapper for scrape_async."""
        try:
            return asyncio.run(self.scrape_async(url, settings.MAX_REVIEWS_PER_SCRAPE))
        except RuntimeError:
            # Fallback for when loop is already running
            html = self.fetch_html(url)
            return self.parse_reviews(html, url)

    @staticmethod
    def parse_from_text(raw_text: str) -> List[Review]:
        """Parses raw text into Review objects."""
        reviews = []
        for line in raw_text.splitlines():
            line = line.strip()
            if len(line) > 5:
                reviews.append(Review(
                    text=line,
                    rating=None,
                    date=datetime.now().isoformat(),
                    source="manual_paste",
                    url="N/A"
                ))
        return reviews[:settings.MAX_REVIEWS_PER_SCRAPE]

    @staticmethod
    def parse_from_csv(df: pd.DataFrame, text_col: str) -> List[Review]:
        """Parses a DataFrame into Review objects."""
        reviews = []
        if text_col not in df.columns:
            return reviews
        
        for _, row in df.iterrows():
            if len(reviews) >= settings.MAX_REVIEWS_PER_SCRAPE:
                break
            text = str(row[text_col]).strip()
            if text and text.lower() != 'nan' and len(text) > 5:
                reviews.append(Review(
                    text=text,
                    rating=None,
                    date=datetime.now().isoformat(),
                    source="csv_import",
                    url="N/A"
                ))
        return reviews
