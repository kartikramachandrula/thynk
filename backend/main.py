# Created by Melody Yu
# Created on Sep 13, 2025
# Enhanced for Thynk: Always Ask Y

import os
import json
import time
import base64
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import modal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from PIL import Image
import numpy as np

# Import Thynk system components
from .thynk_functions import is_different, context_compression, get_context, give_hint
from .redis_client import redis_client

# EasyOCR imports
# try:
#     import easyocr
#     EASYOCR_AVAILABLE = True
# except ImportError:
#     EASYOCR_AVAILABLE = False
#     print("EasyOCR not available. Install easyocr to use OCR.")

EASYOCR_AVAILABLE = False

# Modal imports (only if Modal is available)
try:
    import modal
    MODAL_AVAILABLE = True
except ImportError:
    MODAL_AVAILABLE = False

load_dotenv()

# Create FastAPI app
fastapi_app = FastAPI(title="Rizzoids Backend", version="1.0.0")

# --- Modal Setup ---
app = modal.App("rizzoids-backend")
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "python-dotenv==1.0.0",
    "modal==0.64.0",
    "easyocr==1.7.0",
    "pillow==10.1.0",
    "pydantic==2.5.0",
    "anthropic==0.25.0",
    "redis==5.0.1",
    "upstash-redis==0.15.0",
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

# Thynk system models
class ThynkContextRequest(BaseModel):
    text: str

class HintRequest(BaseModel):
    learned: str
    question: Optional[str] = ""

class ContextStatusResponse(BaseModel):
    status: str
    total_entries: int
    context_preview: str

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
    """Analyze photo from Mentra glasses and extract text using OCR with Thynk integration"""
    # Perform OCR
    ocr_result = await extract_text_from_image(request.image_base64)
    
    # If OCR was successful, process with Thynk system
    if ocr_result.success and ocr_result.text.strip():
        try:
            # Check if content is different enough to process
            content_data = {"text": ocr_result.text}
            different_result = is_different(content_data)
            
            # If content is different, compress and store it
            if different_result.get("text"):
                await context_compression(different_result)
                print(f"Processed new learning content: {different_result['text'][:100]}...")
                
        except Exception as e:
            print(f"Error processing with Thynk system: {e}")
            # Continue with OCR result even if Thynk processing fails
    
    return ocr_result

@fastapi_app.get("/context_status")
async def context_status():
    """Debug endpoint to check stored context"""
    try:
        context_data = await get_context()
        return {
            "status": "success", 
            "total_entries": context_data["entries"], 
            "context_preview": context_data["context"][:500] + "..." if len(context_data["context"]) > 500 else context_data["context"]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Thynk System Endpoints

@fastapi_app.post("/give-hint")
async def give_hint_endpoint(request: HintRequest):
    """
    Generate a helpful hint based on learned context.
    This is the main endpoint for the frontend 'get hint' button.
    """
    try:
        hint_text = await give_hint(request.learned, request.question)
        return {"hint": hint_text, "status": "success"}
    except Exception as e:
        return {"hint": "💡 **Hint:** Keep working through the problem step by step!", "status": "error", "message": str(e)}

@fastapi_app.post("/context-compression")
async def context_compression_endpoint(request: ThynkContextRequest):
    """
    Manually trigger context compression (useful for testing)
    """
    try:
        content_data = {"text": request.text}
        await context_compression(content_data)
        return {"status": "success", "message": "Context processed and stored"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@fastapi_app.get("/get-context")
async def get_context_endpoint():
    """
    Retrieve current learning context
    """
    try:
        context_data = await get_context()
        return {
            "status": "success",
            "entries": context_data["entries"],
            "context": context_data["context"]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@fastapi_app.post("/is-different")
async def is_different_endpoint(request: ThynkContextRequest):
    """
    Check if content is different enough to process (useful for testing)
    """
    try:
        content_data = {"text": request.text}
        result = is_different(content_data)
        return {
            "status": "success",
            "is_different": bool(result.get("text")),
            "content": result.get("text", "")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@fastapi_app.delete("/clear-context")
async def clear_context_endpoint():
    """
    Clear all stored context (useful for testing)
    """
    try:
        success = await redis_client.clear_context()
        if success:
            return {"status": "success", "message": "Context cleared"}
        else:
            return {"status": "error", "message": "Failed to clear context"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Modal deployment setup (only if Modal is available)
if MODAL_AVAILABLE:
    # Create Modal app (use 'app' as the variable name for Modal CLI)
    app = modal.App("rizzoids-backend-personal")
    
    # Define the image with FastAPI and EasyOCR
    image = modal.Image.debian_slim(python_version="3.12").pip_install([
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-dotenv==1.0.0",
        "pydantic==2.11.9",
        "pillow==10.1.0",
        "numpy",
        "easyocr==1.7.0",
        "anthropic==0.25.0",
        "redis==5.0.1",
        "upstash-redis==0.15.0",
        "google-cloud-vision",
        "cerebras-cloud-sdk==1.50.1"
    ])
    
    # Modal deployment using the same FastAPI app
    @app.function(
        image=image,
        memory=1024,
        cpu=1.0
    )
    @modal.asgi_app(label="rizzoids-api")
    def modal_fastapi_app():
        return fastapi_app

# Local development server
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )