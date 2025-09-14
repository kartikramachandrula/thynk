"""
Audio transcription module using OpenAI Whisper for lecture mode processing
"""

import whisper
import tempfile
import base64
import io
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranscriber:
    """Handle audio transcription using Whisper"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe_base64_audio(self, audio_base64: str) -> Dict[str, Any]:
        """
        Transcribe base64 encoded audio
        
        Args:
            audio_base64: Base64 encoded audio data
            
        Returns:
            Dict containing transcription result
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Transcribe audio
            result = self.model.transcribe(temp_file_path)
            
            # Clean up temporary file
            import os
            os.unlink(temp_file_path)
            
            return {
                "success": True,
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "confidence": self._calculate_confidence(result),
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "language": "unknown",
                "confidence": 0.0
            }
    
    def _calculate_confidence(self, result: Dict) -> float:
        """
        Calculate average confidence from segments
        
        Args:
            result: Whisper transcription result
            
        Returns:
            Average confidence score
        """
        try:
            segments = result.get("segments", [])
            if not segments:
                return 0.8  # Default confidence if no segments
            
            # Calculate average confidence from segments
            total_confidence = sum(seg.get("avg_logprob", -1.0) for seg in segments)
            avg_confidence = total_confidence / len(segments)
            
            # Convert log probability to confidence (approximate)
            # Whisper returns negative log probabilities, convert to 0-1 scale
            confidence = max(0.0, min(1.0, (avg_confidence + 3.0) / 3.0))
            return confidence
            
        except Exception:
            return 0.5  # Default confidence on error

# Global transcriber instance
audio_transcriber = AudioTranscriber(model_size="base")
