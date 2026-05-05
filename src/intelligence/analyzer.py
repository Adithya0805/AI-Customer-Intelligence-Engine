import logging
import os
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyzes sentiment of text using HuggingFace Transformers.
    Defaults to RoBERTa. Falls back to CPU if GPU not available.
    """
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.model_name = model_name
        # Check if HF Inference API key is provided for cloud inference (not implemented in this local version)
        # We will use local transformers model for this setup.
        
        device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Loading sentiment model '{self.model_name}' on device {device}...")
        
        try:
            self.nlp = pipeline("sentiment-analysis", model=self.model_name, tokenizer=self.model_name, device=device)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.nlp = None

    def analyze(self, text: str) -> dict:
        """
        Analyzes a single piece of text.
        Returns: { 'label': 'positive'|'neutral'|'negative', 'score': float }
        """
        if not text or not self.nlp:
            return {"label": "neutral", "score": 0.0}
            
        try:
            # RoBERTa has a max sequence length (usually 512 tokens). Truncating string roughly.
            # A more robust approach uses the tokenizer to truncate, but this is a quick safety net.
            safe_text = text[:1500] 
            result = self.nlp(safe_text)[0]
            
            # Map model-specific labels to generic ones if necessary
            label_map = {
                "positive": "positive",
                "neutral": "neutral",
                "negative": "negative",
                "LABEL_2": "positive",
                "LABEL_1": "neutral",
                "LABEL_0": "negative"
            }
            
            normalized_label = label_map.get(result['label'].lower(), result['label'].lower())
            
            return {
                "label": normalized_label,
                "score": float(result['score'])
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed for text: '{text[:20]}...'. Error: {e}")
            return {"label": "neutral", "score": 0.0}
