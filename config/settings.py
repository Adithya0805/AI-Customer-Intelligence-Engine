import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ALERTS_DIR = DATA_DIR / "alerts"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ALERTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Scraper Settings
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MAX_REVIEWS_PER_SCRAPE = int(os.getenv("MAX_REVIEWS_PER_SCRAPE", 500))
SCRAPE_TIMEOUT = float(os.getenv("SCRAPE_TIMEOUT", 15.0))

# NLP Settings
# Using RoBERTa for sentiment analysis (English)
SENTIMENT_MODEL_NAME = os.getenv("SENTIMENT_MODEL_NAME", "cardiffnlp/twitter-roberta-base-sentiment-latest")
MODEL_CACHE_DIR = BASE_DIR / ".model_cache"
MODEL_CACHE_DIR.mkdir(exist_ok=True)

# Gemini AI Settings
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

# Pressure Detector Settings
PRESSURE_RECENT_DAYS = int(os.getenv("PRESSURE_RECENT_DAYS", 7))
PRESSURE_BASELINE_DAYS = int(os.getenv("PRESSURE_BASELINE_DAYS", 30))
PRESSURE_ALERT_THRESHOLD = float(os.getenv("PRESSURE_ALERT_THRESHOLD", 2.0))
MIN_REVIEWS_FOR_PRESSURE = int(os.getenv("MIN_REVIEWS_FOR_PRESSURE", 5))

# Automation Settings
WATCHLIST_SYNC_HOURS = int(os.getenv("WATCHLIST_SYNC_HOURS", 6))
WATCHLIST_COOLDOWN_HOURS = int(os.getenv("WATCHLIST_COOLDOWN_HOURS", 4))

# Supabase Service Key
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "engine.log"
