import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """Abstract base class for all source-specific connectors."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def fetch_html(self, url: str) -> str:
        """Fetches HTML content from the URL."""
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    @abstractmethod
    async def scrape(self, url: str, max_reviews: int = 100) -> List[Dict]:
        """Scrapes reviews from the given URL. Must be implemented by subclasses."""
        pass
