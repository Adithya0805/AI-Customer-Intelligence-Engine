import os
import json
import logging
import google.generativeai as genai
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class AspectAnalyzer:
    """
    Extracts key aspects (e.g., price, quality, service) and their sentiment
    using Gemini LLM for deep-dive intelligence.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini for Aspect Analysis: {e}")
                self.model = None
        else:
            self.model = None

    def analyze_aspects(self, reviews: List[Dict]) -> List[Dict]:
        """
        Analyzes a batch of reviews to extract aspect-level sentiment.
        Uses a single prompt for efficiency.
        """
        if not self.model or not reviews:
            return []

        # Sample reviews if too many to fit in prompt (limit to top 50 for cost/speed)
        sample_size = min(50, len(reviews))
        text_samples = "\n".join([f"- {r['clean_text'][:200]}" for r in reviews[:sample_size]])

        prompt = f"""
        Analyze the following customer reviews and extract the top 5 business aspects (e.g., Quality, Price, Support, Delivery, Ease of Use).
        For each aspect, provide:
        1. Aspect Name
        2. Sentiment Score (0.0 to 1.0, where 1.0 is very positive)
        3. A brief 1-sentence summary of what customers said about this aspect.

        REVIEWS:
        {text_samples}

        Return the results STRICTLY as a JSON array of objects with keys: "aspect", "score", "summary".
        """

        try:
            response = self.model.generate_content(prompt)
            # Clean response text (remove markdown code blocks if present)
            json_str = response.text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            aspects = json.loads(json_str)
            return aspects
        except Exception as e:
            logger.error(f"Aspect analysis failed: {e}")
            return []
