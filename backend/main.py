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
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from PIL import Image
import numpy as np
from ocr_models.ocr_factory import OCRFactory
from ocr_models.base_ocr import SimpleOCRResponse
from redis_client import ThynkRedisClient

# Import Thynk system components (support running as package or as script)
# try:
from thynk_functions import is_different, context_compression, get_context, give_hint
from redis_client import redis_client
# except ImportError:
#     # Fallback for when running this file directly (e.g., `python backend/main.py`)
#     from thynk_functions import is_different, context_compression, get_context, give_hint
#     from redis_client import redis_client

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
thynk_client = ThynkRedisClient()

# CORS configuration to allow frontend to call backend (handles OPTIONS preflight)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # broad allow for dev
        "null",  # handle file:// or sandboxed contexts
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r".*",  # fallback match any origin
    allow_credentials=False,  # keep False when using '*'
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generic OPTIONS handler to ensure preflight never 400s even if headers are missing
@fastapi_app.options("/{rest_of_path:path}")
async def preflight_handler():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Max-Age": "86400",
    }
    return Response(status_code=200, headers=headers)

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

@fastapi_app.get("/ocr/models")
async def get_available_ocr_models():
    """Get list of available OCR models"""
    available_models = OCRFactory.get_available_models()
    return {"available_models": available_models}

# Initialize OCR model using factory
_ocr_model = None

def get_ocr_model():
    """Get or initialize OCR model (lazy loading)"""
    global _ocr_model
    if _ocr_model is None:
        # Get available models and use the first available one
        available_models = OCRFactory.get_available_models()
        if not available_models:
            raise HTTPException(
                status_code=500,
                detail="No OCR models are available. Please check your environment configuration."
            )
        
        # Prefer Claude, then EasyOCR, then Google Vision
        preferred_order = ["jury","claude", "easyocr", "google_vision"]
        selected_model = None
        
        for preferred in preferred_order:
            if preferred in available_models:
                selected_model = preferred
                break
        
        # Fallback to first available if none of the preferred models are available
        if selected_model is None:
            selected_model = available_models[0]
        
        print(f"Using OCR model: {selected_model}")
        _ocr_model = OCRFactory.create_ocr_model(selected_model)
    return _ocr_model

# OCR endpoints
@fastapi_app.post("/ocr", response_model=SimpleOCRResponse)
async def perform_ocr(request: OCRRequest):
    """Extract text from image using OCR"""
    try:
        ocr_model = get_ocr_model()
        return await ocr_model.extract_text_from_image(request.image_base64)
    except HTTPException as he:
        import traceback
        print("/ocr endpoint HTTPException:", he.detail)
        print(traceback.format_exc())
        raise he
    except Exception as e:
        import traceback
        print("/ocr endpoint error:", e)
        print(traceback.format_exc())
        # Re-raise as HTTPException to ensure proper JSON response
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/analyze-photo", response_model=SimpleOCRResponse)
async def analyze_photo(request: OCRRequest):
    """Analyze photo from Mentra glasses and extract text using OCR"""
    print("Analyzing photo...")
    try:
        ocr_model = get_ocr_model()
        result = await ocr_model.extract_text_from_image(request.image_base64)
        if result.success:
            text = result.full_text
            await thynk_client.store_context(text)
        return result
    except HTTPException as he:
        import traceback
        print("/analyze-photo endpoint HTTPException:", he.detail)
        print(traceback.format_exc())
        raise he
    except Exception as e:
        import traceback
        print("/analyze-photo endpoint error:", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

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
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )