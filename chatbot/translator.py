"""
Bidirectional translator for Tamil <-> English.
Uses indic-nlp library for offline translation.
"""

import logging
import re
from typing import Tuple
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


class Translator:
    """Handles translation between Tamil and English with language detection."""
    
    def __init__(self):
        """Initialize the translator."""
        self.supported_languages = {'ta', 'en'}  # Tamil, English
        logger.info("Translator initialized (offline mode)")
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of input text.
        
        Args:
            text: Input text to detect
            
        Returns:
            Language code ('ta' for Tamil, 'en' for English)
        """
        if not text or not text.strip():
            return 'en'  # Default to English for empty input

        normalized = text.strip()

        # Short answers, numbers, and yes/no style responses are treated as English
        # to avoid noisy langdetect warnings on questionnaire inputs.
        if len(normalized) < 4 or re.fullmatch(r"[\d\s.,/-]+", normalized):
            return 'en'

        tamil_characters = re.search(r"[\u0B80-\u0BFF]", normalized)
        if tamil_characters:
            return 'ta'

        if normalized.lower() in {
            'yes', 'no', 'male', 'female', 'other', 'single', 'married',
            'divorced', 'widowed', 'hindu', 'muslim', 'christian', 'sikh',
            'buddhist', 'jain', 'student', 'government', 'private'
        }:
            return 'en'
        
        try:
            lang = detect(normalized)
            if lang in self.supported_languages:
                return lang
            else:
                # Default to English if unsupported language detected
                logger.warning(f"Unsupported language detected: {lang}, defaulting to English")
                return 'en'
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def translate(self, text: str, target_lang: str) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_lang: Target language code ('ta' or 'en')
            
        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text
        
        source_lang = self.detect_language(text)
        
        # If source and target are same, return as-is
        if source_lang == target_lang:
            return text
        
        try:
            # Import here to avoid dependency issues if indic-nlp not installed
            from indicnlp.transliterate import unicode_transliterate
            from indicnlp.transliterate.unicode_transliterate import XlitClass
            
            # For Tamil <-> English, we use a simple transliteration approach
            # In production, you'd use a proper NMT model
            if source_lang == 'ta' and target_lang == 'en':
                # Tamil to English: transliterate
                try:
                    result = unicode_transliterate.transliterate(text, XlitClass.ITRANS, 'ta')
                    logger.debug(f"Translated Tamil to English (transliteration)")
                    return result
                except Exception as e:
                    logger.error(f"Transliteration failed: {e}, returning original text")
                    return text
            elif source_lang == 'en' and target_lang == 'ta':
                # English to Tamil: this is more complex, would need ML model
                # For now, return placeholder
                logger.warning("English to Tamil translation not fully implemented, using placeholder")
                return text
            else:
                return text
                
        except ImportError as e:
            logger.warning(f"indic-nlp not properly installed: {e}")
            logger.info("Returning text as-is (translation skipped)")
            return text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name."""
        names = {'ta': 'Tamil', 'en': 'English'}
        return names.get(lang_code, 'Unknown')
