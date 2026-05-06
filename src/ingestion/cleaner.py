import re
import logging
from langdetect import detect, DetectorFactory
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# Ensure consistent language detection
DetectorFactory.seed = 0
logger = logging.getLogger(__name__)

class ReviewCleaner:
    """
    Cleans raw review text. Handles noise removal, normalization, 
    and Tamil-English transliteration/translation handling.
    """
    def __init__(self):
        # Regex for cleaning but keeping emojis (optional)
        # Production ready cleaning regex
        pass

    def remove_html(self, text: str) -> str:
        """Removes HTML tags from text."""
        if not text: return ""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def remove_urls(self, text: str) -> str:
        """Removes URLs from text."""
        if not text: return ""
        return re.sub(r'http\S+|www\.\S+', '', text)

    def normalize_whitespace(self, text: str) -> str:
        """Removes extra whitespaces and newlines."""
        if not text: return ""
        return re.sub(r'\s+', ' ', text).strip()

    def handle_multilingual(self, text: str) -> str:
        """
        Detects if the text is Tamil and transliterates it.
        Hardened to handle errors and short text.
        """
        if not text or len(text) < 10:
            return text
            
        try:
            # langdetect can fail on short or weird text
            lang = detect(text)
            if lang == 'ta':
                transliterated = transliterate(text, sanscript.TAMIL, sanscript.ITRANS)
                logger.debug(f"Transliterated Tamil: {text[:20]}...")
                return transliterated
        except Exception as e:
            # Non-fatal, just log and return original
            logger.debug(f"Language detection skipped/failed: {e}")
            
        return text

    def normalize_rating(self, rating: float, max_rating: float = 5.0) -> float:
        """Normalizes rating to a 0.0 to 1.0 scale."""
        if rating is None or not isinstance(rating, (int, float)):
            return None
        return min(max(rating / max_rating, 0.0), 1.0)

    def clean(self, text: str) -> str:
        """Full cleaning pipeline for a single text string."""
        if not text or not isinstance(text, str):
            return ""
            
        # Guard against extremely long strings that might crash regex or memory
        if len(text) > 10000:
            text = text[:10000]
            
        text = self.remove_html(text)
        text = self.remove_urls(text)
        text = self.handle_multilingual(text)
        text = self.normalize_whitespace(text)
        
        return text
