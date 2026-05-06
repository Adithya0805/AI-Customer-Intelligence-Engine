import os
import asyncpraw
import logging
from datetime import datetime
from typing import List
from src.ingestion.connectors.base import BaseConnector, Review

logger = logging.getLogger(__name__)

class RedditConnector(BaseConnector):
    """
    Ingests reviews/comments from Reddit.
    Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.
    """
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = "AI-Intel-Engine/1.0"

    async def extract(self, query: str, limit: int = 50) -> List[Review]:
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials missing. Skipping Reddit extraction.")
            return []

        reviews = []
        try:
            reddit = asyncpraw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )

            # Search for mentions across all subreddits
            async for submission in reddit.subreddit("all").search(query, limit=limit, sort="new"):
                reviews.append(Review(
                    original_text=f"{submission.title}\n{submission.selftext[:500]}",
                    rating=None, # Reddit doesn't have 1-5 ratings
                    date=datetime.fromtimestamp(submission.created_utc),
                    source="reddit",
                    metadata={"url": f"https://reddit.com{submission.permalink}", "type": "submission"}
                ))

            await reddit.close()
            return reviews
        except Exception as e:
            logger.error(f"Reddit extraction failed: {e}")
            return []
