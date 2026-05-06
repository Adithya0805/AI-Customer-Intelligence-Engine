import logging
import os
from typing import List, Optional
from transformers import pipeline, AutoTokenizer
import torch
from config import settings

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyzes sentiment of text using HuggingFace Transformers.
    Hardened for production with lazy loading, proper truncation, and error recovery.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.SENTIMENT_MODEL_NAME
        self.device = 0 if torch.cuda.is_available() else -1
        self._nlp = None
        self._tokenizer = None
        
        # Mapping labels
        self.label_map = {
            "positive": "positive",
            "neutral": "neutral",
            "negative": "negative",
            "LABEL_2": "positive",
            "LABEL_1": "neutral",
            "LABEL_0": "negative"
        }

    @property
    def nlp(self):
        """Lazy load the model pipeline."""
        if self._nlp is None:
            try:
                logger.info(f"Loading sentiment model '{self.model_name}' on device {self.device}...")
                self._nlp = pipeline(
                    "sentiment-analysis", 
                    model=self.model_name, 
                    tokenizer=self.model_name, 
                    device=self.device,
                    model_kwargs={"cache_dir": settings.MODEL_CACHE_DIR}
                )
                logger.info("Model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                return None
        return self._nlp

    def analyze(self, text: str) -> dict:
        """Analyzes a single piece of text with proper truncation."""
        if not text:
            return {"label": "neutral", "score": 0.0}
            
        model = self.nlp
        if not model:
            return {"label": "neutral", "score": 0.0}
            
        try:
            # The pipeline 'truncation' argument is the correct way to handle long text
            result = model(text, truncation=True, max_length=512)[0]
            normalized_label = self.label_map.get(result['label'].lower(), result['label'].lower())
            
            return {
                "label": normalized_label,
                "score": float(result['score'])
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"label": "neutral", "score": 0.0}

    def analyze_batch(self, texts: List[str], batch_size: int = 16) -> List[dict]:
        """Analyzes a batch of texts efficiently."""
        if not texts:
            return []
            
        model = self.nlp
        if not model:
            return [{"label": "neutral", "score": 0.0}] * len(texts)
            
        try:
            results = model(texts, truncation=True, max_length=512, batch_size=batch_size)
            processed_results = []
            for res in results:
                label = self.label_map.get(res['label'].lower(), res['label'].lower())
                processed_results.append({"label": label, "score": float(res['score'])})
            return processed_results
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}. Falling back to single mode.")
            return [self.analyze(t) for t in texts]
