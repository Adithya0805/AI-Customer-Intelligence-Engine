import argparse
import logging
from src.processing.pipeline import IntelligencePipeline
from config import settings

# Setup basic logging
logging.basicConfig(
    level=getattr(logging, "INFO"), # Ideally read from settings
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

def main():
    parser = argparse.ArgumentParser(description="AI Customer Intelligence Engine CLI")
    parser.add_argument("--url", type=str, required=True, help="Target URL to scrape reviews from")
    
    args = parser.parse_args()
    
    pipeline = IntelligencePipeline()
    result = pipeline.run(args.url)
    
    print("\n--- Pipeline Result ---")
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"Processed Reviews: {result.get('processed_count')}")
        print(f"New Alerts: {result.get('alerts_generated')}")
        for alert in result.get('alerts', []):
            print(f"  [{alert['status']}] Keyword: '{alert['keyword']}' | Pressure: {alert['pressure_score']}x")
    else:
         print(f"Message: {result.get('message')}")

if __name__ == "__main__":
    main()
