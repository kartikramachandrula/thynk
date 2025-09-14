from .base_ocr import BaseOCR
from .easyocr_model import EasyOCRModel
from .google_vision_model import GoogleVisionModel
from .claude_model import ClaudeModel
from .cerebras_model import CerebrasModel
from .jury_model import JuryModel

class OCRFactory:
    """Factory class to create OCR model instances"""
    
    @staticmethod
    def create_ocr_model(model_type: str = "claude") -> BaseOCR:
        """Create an OCR model instance based on the specified type"""
        
        if model_type.lower() == "easyocr":
            return EasyOCRModel()
        elif model_type.lower() == "google_vision":
            return GoogleVisionModel()
        elif model_type.lower() == "claude":
            return ClaudeModel()
        elif model_type.lower() == "cerebras":
            return CerebrasModel()
        elif model_type.lower() == "jury":
            return JuryModel()
        else:
            raise ValueError(f"Unsupported OCR model type: {model_type}")
    
    @staticmethod
    def get_available_models() -> list[str]:
        """Get list of available OCR models"""
        models = []
        
        # Check EasyOCR availability
        easyocr_model = EasyOCRModel()
        if easyocr_model.is_available():
            models.append("easyocr")
        
        # Check Google Vision availability
        google_vision_model = GoogleVisionModel()
        if google_vision_model.is_available():
            models.append("google_vision")
        
        # Check Claude availability
        claude_model = ClaudeModel()
        if claude_model.is_available():
            models.append("claude")
        
        # Check Cerebras availability
        cerebras_model = CerebrasModel()
        if cerebras_model.is_available():
            models.append("cerebras")
        
        # Check Jury availability
        jury_model = JuryModel()
        if jury_model.is_available():
            models.append("jury")
        
        return models
