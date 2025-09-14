import base64
import io
from PIL import Image
import numpy as np
from fastapi import HTTPException

from .base_ocr import BaseOCR, OCRResponse, TextPhrase

# EasyOCR imports
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available. Install easyocr to use OCR.")

class EasyOCRModel(BaseOCR):
    """EasyOCR implementation of the OCR interface"""
    
    def __init__(self):
        self._ocr_reader = None
    
    def is_available(self) -> bool:
        """Check if EasyOCR is available"""
        return EASYOCR_AVAILABLE
    
    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        return "EasyOCR"
    
    def _get_ocr_reader(self):
        """Get or initialize EasyOCR reader (lazy loading)"""
        if self._ocr_reader is None:
            if not self.is_available():
                raise HTTPException(
                    status_code=500, 
                    detail="EasyOCR not available. Please install easyocr."
                )
            # Initialize with English and common languages
            self._ocr_reader = easyocr.Reader(['en'])
        return self._ocr_reader
    
    async def extract_text_from_image(self, image_base64: str) -> OCRResponse:
        """Extract text from base64 encoded image using EasyOCR"""
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Convert PIL image to numpy array for EasyOCR
            image_array = np.array(pil_image)
            
            # Get OCR reader
            reader = self._get_ocr_reader()
            
            # Perform text detection
            results = reader.readtext(image_array)
            
            # Extract text and calculate average confidence
            detected_texts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.8:
                    detected_texts.append(text)
                    confidences.append(confidence)
            
            # Combine all detected text
            full_text = ' '.join(detected_texts) if detected_texts else ""
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Create phrases list
            phrases = [TextPhrase(text=text, confidence=confidence) for text, confidence in zip(detected_texts, confidences)]
            
            return OCRResponse(
                phrases=phrases,
                full_text=full_text,
                average_confidence=avg_confidence,
                success=True
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"EasyOCR processing failed: {str(e)}"
            )
