import base64
import io
from PIL import Image
from fastapi import HTTPException

<<<<<<< HEAD
from .base_ocr import BaseOCR, OCRResponse, TextPhrase
=======
from .base_ocr import BaseOCR, OCRResponse, SimpleOCRResponse, TextPhrase
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512

# Google Cloud Vision imports
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Google Cloud Vision not available. Install google-cloud-vision to use OCR.")

class GoogleVisionModel(BaseOCR):
    """Google Cloud Vision API implementation of the OCR interface"""
    
    def __init__(self):
        self._vision_client = None
    
    def is_available(self) -> bool:
        """Check if Google Cloud Vision is available"""
        return GOOGLE_VISION_AVAILABLE
    
    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        return "Google Cloud Vision"
    
    def _get_vision_client(self):
        """Get or initialize Google Vision client (lazy loading)"""
        if self._vision_client is None:
            if not self.is_available():
                raise HTTPException(
                    status_code=500, 
                    detail="Google Cloud Vision not available. Please install google-cloud-vision."
                )
            # Initialize the Vision API client
            self._vision_client = vision.ImageAnnotatorClient()
        return self._vision_client
    
<<<<<<< HEAD
    async def extract_text_from_image(self, image_base64: str) -> OCRResponse:
=======
    async def extract_text_from_image(self, image_base64: str) -> SimpleOCRResponse:
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
        """Extract text from base64 encoded image using Google Cloud Vision"""
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            
            # Get Vision client
            client = self._get_vision_client()
            
            # Create Vision API image object
            image = vision.Image(content=image_data)
            
            # Perform text detection
            response = client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise HTTPException(
                    status_code=500,
                    detail=f"Vision API error: {response.error.message}"
                )
            
            # Extract text with confidence filtering
            detected_texts = []
            confidences = []
            
            if texts:
                # First annotation contains the full detected text
                full_detected_text = texts[0].description
                
                # For individual word confidences, we'd need document_text_detection
                # For now, use a default high confidence for Vision API
                confidence = 0.95
                
                # Apply confidence threshold (similar to EasyOCR)
                if confidence > 0.8:
                    detected_texts.append(full_detected_text)
                    confidences.append(confidence)
            
            # Combine all detected text
            full_text = ' '.join(detected_texts) if detected_texts else ""
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Create phrases list
            phrases = [TextPhrase(text=full_detected_text, confidence=confidence)] if detected_texts else []
            
<<<<<<< HEAD
            return OCRResponse(
                phrases=phrases,
                full_text=full_text,
                average_confidence=avg_confidence,
=======
            return SimpleOCRResponse(
                full_text=full_text,
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
                success=True
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Google Vision processing failed: {str(e)}"
            )
