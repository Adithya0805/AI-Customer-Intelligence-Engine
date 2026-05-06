import os
import sys
import time
from pathlib import Path
import logging
from datetime import datetime

# Add root to sys.path to allow imports
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from src.processing.pipeline import IntelligencePipeline
from src.database.client import get_supabase_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WatchlistWorker")

def run_worker():
    logger.info("Starting automated Watchlist Worker...")
    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return

    # 1. Fetch URLs from Watchlist
    try:
        response = supabase.table('watchlist').select('*').execute()
        watchlist = response.data
    except Exception as e:
        logger.error(f"Failed to fetch watchlist: {e}")
        return

    if not watchlist:
        logger.info("Watchlist is empty. Nothing to do.")
        return

    logger.info(f"Found {len(watchlist)} URLs in watchlist.")
    
    pipeline = IntelligencePipeline()

    # 2. Iterate through URLs
    for item in watchlist:
        url = item['url']
        company = item.get('company_name', 'Unknown')
        logger.info(f"Processing URL for {company}: {url}")
        
        try:
            # Run the pipeline (this handles scraping, sentiment, clustering, LLM summary, and saving to DB)
            result = pipeline.run(url)
            
            if result['status'] == 'success':
                logger.info(f"Successfully processed {company}. Extracted {result['processed_count']} reviews.")
                # Update last_scraped_at timestamp
                supabase.table('watchlist').update({
                    'last_scraped_at': datetime.now().isoformat()
                }).eq('id', item['id']).execute()
            else:
                logger.error(f"Pipeline failed for {company}: {result.get('message')}")
        except Exception as e:
            logger.error(f"Unexpected error processing {company}: {e}")
            
        # Polite delay between sites
        time.sleep(2)

    logger.info("Watchlist Worker finished execution.")

if __name__ == "__main__":
    run_worker()
