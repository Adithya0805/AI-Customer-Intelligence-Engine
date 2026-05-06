import os
import sys
import time
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Add root to sys.path to allow imports
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from src.processing.pipeline import IntelligencePipeline
from src.database.client import get_supabase_client, get_service_client
from config import settings

# Initialize logging using settings if possible, otherwise basic
logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WatchlistWorker")

def run_worker():
    logger.info("Starting automated Watchlist Worker cycle...")
    try:
        # Use anon client for reads, service client for updates
        supabase = get_supabase_client()
        service_supabase = get_service_client()
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
    cooldown_limit = datetime.now() - timedelta(hours=settings.WATCHLIST_COOLDOWN_HOURS)

    # 2. Iterate through URLs
    for item in watchlist:
        url = item['url']
        company = item.get('company_name', 'Unknown')
        
        # Cooldown check
        last_scraped = item.get('last_scraped_at')
        if last_scraped:
            last_scraped_dt = datetime.fromisoformat(last_scraped.replace('Z', '+00:00'))
            # Remove timezone if necessary for comparison or ensure both are offset-aware
            if last_scraped_dt.replace(tzinfo=None) > cooldown_limit:
                logger.info(f"Skipping {company} (Cooldown active: last scraped at {last_scraped})")
                continue

        logger.info(f"Processing URL for {company}: {url}")
        
        try:
            # Run the pipeline with the owner's user_id
            result = pipeline.run(url, user_id=item.get('user_id'))
            
            if result['status'] == 'success':
                logger.info(f"Successfully processed {company}. Extracted {result['processed_count']} reviews.")
                # Update last_scraped_at timestamp using service client
                service_supabase.table('watchlist').update({
                    'last_scraped_at': datetime.now().isoformat()
                }).eq('id', item['id']).execute()
            else:
                logger.error(f"Pipeline failed for {company}: {result.get('message')}")
        except Exception as e:
            logger.error(f"Unexpected error processing {company}: {e}")
            
        # Polite delay between sites
        time.sleep(settings.SCRAPE_TIMEOUT / 3) # Use a fraction of the timeout as delay

    logger.info("Watchlist Worker cycle finished.")

if __name__ == "__main__":
    run_worker()
