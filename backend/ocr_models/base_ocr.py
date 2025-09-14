from abc import ABC, abstractmethod
from typing import Optional, List
from pydantic import BaseModel

# Pydantic models for OCR
class OCRRequest(BaseModel):
    image_base64: str

class TextPhrase(BaseModel):
    text: str
    confidence: float
    
class OCRResponse(BaseModel):
    phrases: List[TextPhrase]
    full_text: str
    average_confidence: float
    success: bool

class SimpleOCRResponse(BaseModel):
    """Simplified response exposed by API endpoints."""
    full_text: str
    success: bool

# Abstract base class for OCR models
class BaseOCR(ABC):
    """Abstract base class for OCR implementations"""
    
    @abstractmethod
    async def extract_text_from_image(self, image_base64: str) -> SimpleOCRResponse:
        """Extract text from base64 encoded image"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the OCR model is available"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        pass
