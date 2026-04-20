"""
Offline Text-to-Speech module using pyttsx3.
Generates and plays speech without requiring external APIs.
"""

import logging

logger = logging.getLogger(__name__)


class OfflineTTS:
    """Text-to-Speech using pyttsx3 (offline engine)."""
    
    def __init__(self, rate: int = 150, volume: float = 0.9):
        """
        Initialize TTS engine.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
        """
        self.rate = rate
        self.volume = volume
        self.engine = None
        self.initialized = False
        
        try:
            import pyttsx3
            self.pyttsx3 = pyttsx3
            self._initialize_engine()
        except ImportError:
            logger.error("pyttsx3 not installed. Install with: pip install pyttsx3")
            self.pyttsx3 = None
    
    def _initialize_engine(self):
        """Initialize pyttsx3 engine."""
        try:
            if self.pyttsx3 is None:
                logger.error("pyttsx3 module not available")
                return False
            
            logger.info("Initializing TTS engine...")
            self.engine = self.pyttsx3.init()
            
            # Configure engine
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Log available voices
            voices = self.engine.getProperty('voices')
            logger.info(f"Available voices: {len(voices)}")
            for voice in voices:
                logger.debug(f"  - {voice.name} (lang: {voice.languages})")
            
            self.initialized = True
            logger.info("TTS engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            return False
    
    def set_language(self, language: str = 'en'):
        """
        Set TTS language.
        
        Args:
            language: Language code ('ta' for Tamil, 'en' for English)
        """
        if not self.initialized or self.engine is None:
            logger.warning("TTS engine not initialized")
            return False
        
        try:
            voices = self.engine.getProperty('voices')
            
            # Map language codes to voice preferences
            lang_map = {
                'ta': 'tamil',
                'en': 'english'
            }
            
            target_lang = lang_map.get(language, 'english')
            
            # Try to find voice matching language
            for voice in voices:
                voice_lang = str(voice.languages).lower() if voice.languages else ''
                if target_lang in voice_lang.lower() or target_lang in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Set voice to {voice.name}")
                    return True
            
            # Fallback to first available voice
            if voices:
                self.engine.setProperty('voice', voices[0].id)
                logger.warning(f"Exact {language} voice not found, using {voices[0].name}")
                return True
            
            logger.warning("No voices available")
            return False
            
        except Exception as e:
            logger.error(f"Failed to set language: {e}")
            return False
    
    def speak(self, text: str, language: str = 'en', is_save: bool = False, 
              save_path: str = None) -> bool:
        """
        Speak text using TTS.
        
        Args:
            text: Text to speak
            language: Language code ('ta' for Tamil, 'en' for English)
            is_save: Whether to save audio to file
            save_path: Path to save audio file (if is_save=True)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized or self.engine is None:
            logger.warning("TTS engine not initialized, skipping speech")
            return False
        
        if not text or not text.strip():
            logger.debug("Empty text, skipping speech")
            return False
        
        try:
            # Set language
            self.set_language(language)
            
            # Set text
            self.engine.say(text)
            
            # Save to file if requested
            if is_save and save_path:
                self.engine.save_to_file(text, save_path)
                logger.info(f"Audio will be saved to: {save_path}")
            
            # Play speech
            logger.info("Playing speech...")
            self.engine.runAndWait()
            logger.debug("Speech playback completed")
            return True
            
        except Exception as e:
            logger.error(f"TTS playback failed: {e}")
            return False
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)."""
        if self.engine:
            self.engine.setProperty('rate', rate)
            self.rate = rate
            logger.debug(f"Speech rate set to {rate} wpm")
    
    def set_volume(self, volume: float):
        """Set volume level (0.0 to 1.0)."""
        if self.engine:
            self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            self.volume = volume
            logger.debug(f"Volume set to {volume}")
