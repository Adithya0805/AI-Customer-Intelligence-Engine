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
        pass

    def remove_html(self, text: str) -> str:
        """Removes HTML tags from text."""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def remove_urls(self, text: str) -> str:
        """Removes URLs from text."""
        return re.sub(r'http\S+|www\.\S+', '', text)

    def normalize_whitespace(self, text: str) -> str:
        """Removes extra whitespaces and newlines."""
        return re.sub(r'\s+', ' ', text).strip()

    def handle_multilingual(self, text: str) -> str:
        """
        Detects if the text is Tamil. If so, transliterates it to English script.
        For a production system, an actual translation API (like Google Translate or local translation model) 
        would be better if the sentiment model strictly requires English. 
        Here we use transliteration as a lightweight proxy, assuming the sentiment model might 
        handle code-mixed "Tanglish" or transliterated Tamil reasonably well, or we just keep it clean.
        """
        try:
            lang = detect(text)
            if lang == 'ta':
                # Transliterate Tamil script to Latin (ITRANS format is close to English phonetics)
                # This is a simplified approach. 
                transliterated = transliterate(text, sanscript.TAMIL, sanscript.ITRANS)
                logger.debug(f"Transliterated Tamil: {text[:20]}... -> {transliterated[:20]}...")
                return transliterated
            return text
        except Exception as e:
            logger.debug(f"Language detection failed: {e}. Defaulting to original text.")
            return text

    def normalize_rating(self, rating: float, max_rating: float = 5.0) -> float:
        """Normalizes rating to a 0.0 to 1.0 scale."""
        if rating is None:
            return None
        return min(max(rating / max_rating, 0.0), 1.0)

    def clean(self, text: str) -> str:
        """Full cleaning pipeline for a single text string."""
        if not text:
            return ""
        text = self.remove_html(text)
        text = self.remove_urls(text)
        text = self.handle_multilingual(text)
        text = self.normalize_whitespace(text)
        return text
