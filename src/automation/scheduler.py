import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from datetime import datetime

from src.automation.worker import run_worker
from config import settings

logger = logging.getLogger("Scheduler")

_scheduler = None

def start_scheduler():
    """Starts the background scheduler for watchlist syncing."""
    global _scheduler
    if _scheduler is not None:
        logger.warning("Scheduler is already running.")
        return

    logger.info(f"Initializing background scheduler (Interval: {settings.WATCHLIST_SYNC_HOURS}h)...")
    
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        func=run_worker,
        trigger=IntervalTrigger(hours=settings.WATCHLIST_SYNC_HOURS),
        id='watchlist_sync_job',
        name='Sync Watchlist URLs',
        replace_existing=True,
        next_run_time=datetime.now() # Run immediately on startup
    )
    
    _scheduler.start()
    logger.info("Background scheduler started.")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: _scheduler.shutdown())

def get_scheduler_status():
    """Returns the status of the scheduler for the dashboard."""
    global _scheduler
    if _scheduler is None or not _scheduler.running:
        return {"status": "inactive", "next_run": "N/A"}
    
    job = _scheduler.get_job('watchlist_sync_job')
    if job:
        return {
            "status": "active",
            "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "Running...",
            "last_run": job.prev_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.prev_run_time else "Never"
        }
    return {"status": "active (no job)", "next_run": "N/A"}
