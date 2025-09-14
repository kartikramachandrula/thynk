from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import base64
from pydantic import BaseModel
from typing import Optional
import io
from PIL import Image
import numpy as np


# EasyOCR imports
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available. Install easyocr to use OCR.")

# Modal imports (only if Modal is available)
try:
    import modal
    MODAL_AVAILABLE = True
except ImportError:
    MODAL_AVAILABLE = False

load_dotenv()

# Create FastAPI app
fastapi_app = FastAPI(title="Rizzoids Backend", version="1.0.0")

# CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fastapi_app.get("/")
async def root():
    return {"message": "Rizzoids Backend API", "status": "running"}

@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rizzoids-backend"}

# Pydantic models
class OCRRequest(BaseModel):
    image_base64: str
    
class OCRResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    success: bool

# Initialize EasyOCR reader (lazy loading)
_ocr_reader = None

def get_ocr_reader():
    """Get or initialize EasyOCR reader"""
    global _ocr_reader
    if _ocr_reader is None:
        if not EASYOCR_AVAILABLE:
            raise HTTPException(
                status_code=500, 
                detail="EasyOCR not available. Please install easyocr."
            )
        # Initialize with English and common languages
        _ocr_reader = easyocr.Reader(['en'])
    return _ocr_reader

# OCR Service using EasyOCR
async def extract_text_from_image(image_base64: str) -> OCRResponse:
    """Extract text from base64 encoded image using EasyOCR"""
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert PIL image to numpy array for EasyOCR
        image_array = np.array(pil_image)
        
        # Get OCR reader
        reader = get_ocr_reader()
        
        # Perform text detection
        results = reader.readtext(image_array)
        
        # Extract text and calculate average confidence
        detected_texts = []
        confidences = []
        
        for (bbox, text, confidence) in results:
            detected_texts.append(text)
            confidences.append(confidence)
        
        # Combine all detected text
        full_text = ' '.join(detected_texts) if detected_texts else ""
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return OCRResponse(
            text=full_text,
            confidence=avg_confidence,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )

@fastapi_app.post("/ocr", response_model=OCRResponse)
async def perform_ocr(request: OCRRequest):
    """Extract text from image using OCR"""
    return await extract_text_from_image(request.image_base64)

@fastapi_app.post("/analyze-photo", response_model=OCRResponse)
async def analyze_photo(request: OCRRequest):
    """Analyze photo from Mentra glasses and extract text using OCR"""
    return await extract_text_from_image(request.image_base64)

@fastapi_app.get("/give-hint")
async def give_hint():
    """Outputs the text to the user"""
    text = "Hello, here's your hint!"
    return {"hint": text, "success": True}

# Modal deployment setup (only if Modal is available)
if MODAL_AVAILABLE:
    # Create Modal app (use 'app' as the variable name for Modal CLI)
    app = modal.App("rizzoids-backend-personal")
    
    # Define the image with FastAPI and EasyOCR
    image = modal.Image.debian_slim(python_version="3.12").pip_install([
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-dotenv==1.0.0",
        "easyocr==1.7.0",
        "pillow==10.1.0",
        "numpy"
    ])
    
    # Modal deployment using the same FastAPI app
    @app.function(
        image=image,
        timeout=3600,
        memory=1024,
        cpu=1.0,
        max_containers=50
    )
    @modal.asgi_app(label="rizzoids-api")
    def modal_fastapi_app():
        return fastapi_app

# Local development server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
