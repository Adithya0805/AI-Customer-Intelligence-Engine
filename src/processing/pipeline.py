import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from src.ingestion.scraper import GenericScraper, Review
from src.ingestion.cleaner import ReviewCleaner
from src.intelligence.analyzer import SentimentAnalyzer
from src.intelligence.pressure import PressureDetector
from src.intelligence.categorizer import TopicCategorizer
from src.intelligence.summarizer import LLMSummarizer
from config import settings

logger = logging.getLogger(__name__)

class IntelligencePipeline:
    """
    Orchestrates the entire flow: Scrape/Load -> Clean -> Analyze Sentiment -> Cluster -> Detect Pressure -> Store
    """
    def __init__(self):
        self.scraper = GenericScraper()
        self.cleaner = ReviewCleaner()
        self.analyzer = None
        self.summarizer = LLMSummarizer()
        self.pressure_detector = PressureDetector(
            recent_days=settings.PRESSURE_RECENT_DAYS,
            baseline_days=settings.PRESSURE_BASELINE_DAYS,
            alert_threshold=settings.PRESSURE_ALERT_THRESHOLD,
            min_reviews=settings.MIN_REVIEWS_FOR_PRESSURE
        )

    def _init_analyzer(self):
        if self.analyzer is None:
            self.analyzer = SentimentAnalyzer(model_name=settings.SENTIMENT_MODEL_NAME)

    def _process_reviews(self, raw_reviews: List[Review], progress_callback=None) -> Dict:
        if not raw_reviews:
            logger.warning("No reviews to process.")
            return {"status": "error", "message": "No reviews found or failed to parse."}

        if progress_callback: progress_callback(f"Found {len(raw_reviews)} raw items. Cleaning text...")

        self._init_analyzer()
        
        clean_texts = []
        valid_reviews = []
        for rev in raw_reviews:
            clean_text = self.cleaner.clean(rev.text)
            if clean_text:
                clean_texts.append(clean_text)
                valid_reviews.append(rev)

        if not valid_reviews:
             return {"status": "error", "message": "No valid reviews after cleaning."}

        if progress_callback: progress_callback(f"Analyzing sentiment for {len(clean_texts)} items (batch mode)...")
        
        try:
            # Batch inference
            if self.analyzer.nlp:
                sentiment_results = self.analyzer.nlp(clean_texts, batch_size=16)
            else:
                sentiment_results = [self.analyzer.analyze(txt) for txt in clean_texts]
        except Exception as e:
            logger.error(f"Batch sentiment failed: {e}. Falling back to single.")
            sentiment_results = [self.analyzer.analyze(txt) for txt in clean_texts]

        # Topic Clustering
        if progress_callback: progress_callback("Clustering topics...")
        categorizer = TopicCategorizer(n_clusters=4)
        cluster_results = categorizer.categorize(clean_texts)

        processed_data = []
        for i, (rev, clean_txt, sent) in enumerate(zip(valid_reviews, clean_texts, sentiment_results)):
            
            label_map = {
                "positive": "positive", "neutral": "neutral", "negative": "negative",
                "LABEL_2": "positive", "LABEL_1": "neutral", "LABEL_0": "negative"
            }
            if isinstance(sent, dict) and 'label' in sent:
                label = label_map.get(sent['label'].lower(), sent['label'].lower())
                score = float(sent['score'])
            else:
                label = "neutral"
                score = 0.0

            topic = cluster_results['clusters'][cluster_results['labels'][i]]['label']

            processed_data.append({
                "original_text": rev.text,
                "clean_text": clean_txt,
                "rating": rev.rating,
                "normalized_rating": self.cleaner.normalize_rating(rev.rating),
                "date": rev.date,
                "source": rev.source,
                "url": rev.url,
                "sentiment": label,
                "sentiment_score": score,
                "topic_cluster": topic,
                "processed_at": datetime.now().isoformat()
            })

        if progress_callback: progress_callback("Saving processed data to Supabase...")
        self._save_to_supabase("reviews", processed_data, progress_callback)

        if progress_callback: progress_callback("Running Pressure Detector (Emerging Issues)...")
        historical_df = self._load_historical_data()
        alerts = self.pressure_detector.detect(historical_df)
        
        if alerts:
            self._save_to_supabase("alerts", alerts, progress_callback)

        if progress_callback: progress_callback("Generating AI Executive Summary...")
        summary = self.summarizer.generate_executive_summary(processed_data, cluster_results['clusters'], alerts)

        logger.info("Pipeline completed successfully.")
        return {
            "status": "success",
            "processed_count": len(processed_data),
            "alerts_generated": len(alerts),
            "alerts": alerts,
            "processed_data": processed_data,
            "clusters": cluster_results['clusters'],
            "executive_summary": summary
        }

    def run(self, url: str, progress_callback=None) -> Dict:
        """Runs the pipeline on a scraped URL."""
        logger.info(f"Starting pipeline for URL: {url}")
        if progress_callback: progress_callback("Ingesting data: Scraping reviews from URL...")
        raw_reviews = self.scraper.scrape(url)
        return self._process_reviews(raw_reviews, progress_callback)

    def run_from_text(self, text: str, progress_callback=None) -> Dict:
        """Runs the pipeline on pasted text."""
        logger.info("Starting pipeline for pasted text")
        if progress_callback: progress_callback("Parsing raw text into reviews...")
        raw_reviews = GenericScraper.parse_from_text(text)
        return self._process_reviews(raw_reviews, progress_callback)
        
    def run_from_dataframe(self, df: pd.DataFrame, text_col: str, progress_callback=None) -> Dict:
        """Runs the pipeline on a CSV DataFrame."""
        logger.info(f"Starting pipeline from DataFrame column: {text_col}")
        if progress_callback: progress_callback("Parsing DataFrame into reviews...")
        raw_reviews = GenericScraper.parse_from_csv(df, text_col)
        return self._process_reviews(raw_reviews, progress_callback)

    def _save_to_supabase(self, table: str, data: List[dict], progress_callback=None):
        try:
            from src.database.client import get_supabase_client
            supabase = get_supabase_client()
            
            # The Supabase Python client can insert lists of dicts
            response = supabase.table(table).insert(data).execute()
        except Exception as e:
            logger.error(f"Error saving to Supabase table {table}: {e}")
            if progress_callback: progress_callback(f"Failed to save to database: {e}")

    def _load_historical_data(self) -> pd.DataFrame:
        """Loads historical processed data from Supabase."""
        try:
            from src.database.client import get_supabase_client
            supabase = get_supabase_client()
            response = supabase.table('reviews').select('*').order('date', desc=True).limit(5000).execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
