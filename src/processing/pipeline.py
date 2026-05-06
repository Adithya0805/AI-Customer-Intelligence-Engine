import json
import logging
import pandas as pd
import time
import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from src.ingestion.scraper import GenericScraper, Review
from src.ingestion.cleaner import ReviewCleaner
from src.intelligence.analyzer import SentimentAnalyzer
from src.intelligence.aspect_analyzer import AspectAnalyzer
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
        self.aspect_analyzer = AspectAnalyzer()
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

    def _process_reviews(self, raw_reviews: List[Review], progress_callback=None, user_id=None) -> Dict:
        start_time = time.perf_counter()
        
        if not raw_reviews:
            logger.warning("No reviews to process.")
            return {"status": "error", "message": "No reviews found or failed to parse."}

        logger.info(f"Processing {len(raw_reviews)} reviews...")
        if progress_callback: progress_callback(f"Found {len(raw_reviews)} raw items. Cleaning text...")

        self._init_analyzer()
        
        clean_texts = []
        valid_reviews = []
        for rev in raw_reviews:
            try:
                clean_text = self.cleaner.clean(rev.text)
                if clean_text:
                    clean_texts.append(clean_text)
                    valid_reviews.append(rev)
            except Exception as e:
                logger.error(f"Error cleaning review: {e}")

        if not valid_reviews:
             return {"status": "error", "message": "No valid reviews after cleaning."}

        # 1. Sentiment Analysis
        if progress_callback: progress_callback(f"Analyzing sentiment for {len(clean_texts)} items...")
        sent_start = time.perf_counter()
        try:
            sentiment_results = self.analyzer.analyze_batch(clean_texts)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            sentiment_results = [{"label": "neutral", "score": 0.0}] * len(clean_texts)
        logger.info(f"Sentiment analysis took {time.perf_counter() - sent_start:.2f}s")

        # 2. Topic Clustering
        if progress_callback: progress_callback("Clustering topics...")
        cluster_start = time.perf_counter()
        categorizer = TopicCategorizer(n_clusters=4)
        cluster_results = categorizer.categorize(clean_texts)
        logger.info(f"Topic clustering took {time.perf_counter() - cluster_start:.2f}s")

        # 3. Aspect Analysis (Phase 3 Upgrade)
        aspects = []
        if progress_callback: progress_callback("Extracting key business aspects...")
        try:
            # We pass the processed data to aspect analyzer
            # Limitation: AspectAnalyzer currently expects raw review dicts with 'clean_text'
            review_dicts = [{"clean_text": txt} for txt in clean_texts]
            aspects = self.aspect_analyzer.analyze_aspects(review_dicts)
        except Exception as e:
            logger.error(f"Aspect analysis failed: {e}")

        processed_data = []
        # Get current user_id for multi-tenancy if not provided
        if not user_id and 'user' in st.session_state:
            user_id = st.session_state.user.get('id')
        
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

            row = {
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
            }
            if user_id:
                row["user_id"] = user_id
            processed_data.append(row)

        # 4. Database Persistence
        if progress_callback: progress_callback("Saving results to database...")
        db_start = time.perf_counter()
        self._save_to_supabase("reviews", processed_data, progress_callback)
        
        # Save aspects if any
        if aspects:
            aspect_records = []
            for a in aspects:
                rec = {
                    "aspect": a['aspect'],
                    "score": a['score'],
                    "summary": a['summary'],
                    "company_name": processed_data[0]['source'] if processed_data else "Unknown"
                }
                if user_id: rec["user_id"] = user_id
                aspect_records.append(rec)
            self._save_to_supabase("aspects", aspect_records, progress_callback)
            
        logger.info(f"Database save took {time.perf_counter() - db_start:.2f}s")

        # 5. Pressure Detection
        if progress_callback: progress_callback("Running Pressure Radar...")
        pressure_start = time.perf_counter()
        historical_df = self._load_historical_data()
        alerts = self.pressure_detector.detect(historical_df)
        if alerts:
            if user_id:
                for a in alerts: a["user_id"] = user_id
            self._save_to_supabase("alerts", alerts, progress_callback)
            
            # Phase 4: Dispatch notifications
            if user_id:
                from src.notifications.dispatcher import NotificationDispatcher
                import asyncio
                dispatcher = NotificationDispatcher()
                for alert in alerts:
                    # We run this in a background task if possible, or just async
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(dispatcher.dispatch(user_id, "alert", alert))
                        else:
                            asyncio.run(dispatcher.dispatch(user_id, "alert", alert))
                    except Exception as ne:
                        logger.error(f"Notification dispatch failed: {ne}")
        logger.info(f"Pressure detection took {time.perf_counter() - pressure_start:.2f}s")

        # 6. AI Summary
        if progress_callback: progress_callback("Generating AI Executive Summary...")
        summary_start = time.perf_counter()
        summary_content = self.summarizer.generate_executive_summary(processed_data, cluster_results['clusters'], alerts)
        
        # Persist summary
        summary_obj = {
            "content": summary_content,
            "source_context": "pipeline",
            "metadata": {"processed_count": len(processed_data), "aspects": aspects}
        }
        if user_id:
            summary_obj["user_id"] = user_id
        self._save_to_supabase("summaries", [summary_obj], progress_callback)
        logger.info(f"AI summarization took {time.perf_counter() - summary_start:.2f}s")

        total_duration = time.perf_counter() - start_time
        logger.info(f"Pipeline completed in {total_duration:.2f}s")

        return {
            "status": "success",
            "processed_count": len(processed_data),
            "alerts_generated": len(alerts),
            "alerts": alerts,
            "aspects": aspects,
            "processed_data": processed_data,
            "clusters": cluster_results['clusters'],
            "executive_summary": summary_content,
            "duration": total_duration
        }

    def run(self, url: str, progress_callback=None, user_id=None) -> Dict:
        """Runs the pipeline on a scraped URL."""
        logger.info(f"Pipeline triggered for URL: {url} (User: {user_id})")
        try:
            if progress_callback: progress_callback("Ingesting data: Scraping reviews from URL...")
            raw_reviews = self.scraper.scrape(url)
            return self._process_reviews(raw_reviews, progress_callback, user_id=user_id)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {"status": "error", "message": str(e)}

    def run_from_text(self, text: str, progress_callback=None, user_id=None) -> Dict:
        """Runs the pipeline on pasted text."""
        logger.info("Pipeline triggered for pasted text")
        try:
            if progress_callback: progress_callback("Parsing raw text into reviews...")
            raw_reviews = GenericScraper.parse_from_text(text)
            return self._process_reviews(raw_reviews, progress_callback, user_id=user_id)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {"status": "error", "message": str(e)}
        
    def run_from_dataframe(self, df: pd.DataFrame, text_col: str, progress_callback=None, user_id=None) -> Dict:
        """Runs the pipeline on a CSV DataFrame."""
        logger.info(f"Pipeline triggered for DataFrame column: {text_col}")
        try:
            if progress_callback: progress_callback("Parsing DataFrame into reviews...")
            raw_reviews = GenericScraper.parse_from_csv(df, text_col)
            return self._process_reviews(raw_reviews, progress_callback, user_id=user_id)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {"status": "error", "message": str(e)}

    def _save_to_supabase(self, table: str, data: List[dict], progress_callback=None):
        try:
            from src.database.client import get_service_client
            supabase = get_service_client()
            supabase.table(table).insert(data).execute()
        except Exception as e:
            logger.error(f"Error saving to Supabase table {table}: {e}")
            if progress_callback: progress_callback(f"Database sync warning: {e}")

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
