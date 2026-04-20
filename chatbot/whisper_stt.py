"""
Speech-to-Text module using OpenAI Whisper.
Captures audio from microphone and transcribes using local Whisper model.
"""

import logging
import wave
import os
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class WhisperSTT:
    """Speech-to-Text using OpenAI Whisper (local model)."""
    
    def __init__(self, model_size: str = "base", language: Optional[str] = None):
        """
        Initialize Whisper STT.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            language: Language code ('ta' for Tamil, 'en' for English, None for auto-detect)
        """
        self.model_size = model_size
        self.language = language
        self.model = None
        self.initialized = False
        
        try:
            import whisper
            self.whisper = whisper
            self._load_model()
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            self.whisper = None
    
    def _load_model(self):
        """Load Whisper model."""
        try:
            if self.whisper is None:
                logger.error("Whisper module not available")
                return False
            
            logger.info(f"Loading Whisper model ({self.model_size})...")
            self.model = self.whisper.load_model(self.model_size)
            self.initialized = True
            logger.info("Whisper model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False
    
    def record_audio(self, duration: int = 10, sample_rate: int = 16000) -> Optional[str]:
        """
        Record audio from microphone.
        
        Args:
            duration: Recording duration in seconds
            sample_rate: Sample rate in Hz
            
        Returns:
            Path to saved WAV file or None if failed
        """
        try:
            import pyaudio
        except ImportError:
            logger.error("PyAudio not installed. Install with: pip install pyaudio")
            return None
        
        try:
            CHUNK = 1024
            FORMAT = 8  # pyaudio.paInt16
            CHANNELS = 1
            
            logger.info(f"Recording audio for {duration} seconds...")
            print(f"🎤 Listening... (speak for up to {duration} seconds)")
            
            p = pyaudio.PyAudio()
            
            try:
                stream = p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=CHUNK
                )
            except Exception as e:
                logger.error(f"Failed to open audio stream: {e}")
                logger.warning("Microphone not available")
                return None
            
            frames = []
            
            try:
                for _ in range(0, int(sample_rate / CHUNK * duration)):
                    data = stream.read(CHUNK)
                    frames.append(data)
            except KeyboardInterrupt:
                logger.info("Recording interrupted by user")
                print("\n⏹️  Recording stopped")
            except Exception as e:
                logger.error(f"Error during recording: {e}")
            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()
            
            # Save audio to file
            audio_file = "/tmp/recorded_audio.wav"
            try:
                wf = wave.open(audio_file, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                logger.info(f"Audio saved to {audio_file}")
                return audio_file
            except Exception as e:
                logger.error(f"Failed to save audio file: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return None
    
    def transcribe(self, audio_input: str) -> Tuple[str, str]:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_input: Path to audio file or URL
            
        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        if not self.initialized or self.model is None:
            logger.error("Whisper model not initialized")
            return "", "en"
        
        try:
            if not os.path.exists(audio_input):
                logger.error(f"Audio file not found: {audio_input}")
                return "", "en"
            
            logger.info(f"Transcribing audio: {audio_input}")
            
            # Transcribe
            result = self.model.transcribe(
                audio_input,
                language=self.language,
                verbose=False
            )
            
            text = result.get('text', '').strip()
            detected_lang = result.get('language', 'en')
            
            logger.info(f"Transcription complete. Language: {detected_lang}")
            logger.debug(f"Transcribed text: {text}")
            
            return text, detected_lang
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return "", "en"
    
    def transcribe_with_recording(self, duration: int = 10) -> Tuple[str, str]:
        """
        Record audio and transcribe in one call.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        audio_file = self.record_audio(duration=duration)
        
        if audio_file is None:
            logger.warning("Failed to record audio")
            return "", "en"
        
        text, lang = self.transcribe(audio_file)
        
        # Cleanup
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as e:
            logger.debug(f"Could not remove temp audio file: {e}")
        
        return text, lang
