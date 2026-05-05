import os
from pathlib import Path

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

# Scraper Settings
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# NLP Settings
# Using RoBERTa for sentiment analysis (English)
SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
# If HF_API_KEY is present in env, we can use the Inference API instead of downloading

# Pressure Detector Settings
PRESSURE_RECENT_DAYS = 7
PRESSURE_BASELINE_DAYS = 30
PRESSURE_ALERT_THRESHOLD = 2.0  # 2.0x increase triggers an alert
MIN_REVIEWS_FOR_PRESSURE = 5    # Minimum reviews needed to calculate pressure

# Logging
LOG_FILE = LOGS_DIR / "engine.log"
