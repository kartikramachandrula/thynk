from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Import OCR models directly
from ocr_models.base_ocr import OCRRequest, OCRResponse
from ocr_models.ocr_factory import OCRFactory

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
        preferred_order = ["claude", "easyocr", "google_vision"]
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
@fastapi_app.post("/ocr", response_model=OCRResponse)
async def perform_ocr(request: OCRRequest):
    """Extract text from image using OCR"""
    ocr_model = get_ocr_model()
    return await ocr_model.extract_text_from_image(request.image_base64)

@fastapi_app.post("/analyze-photo", response_model=OCRResponse)
async def analyze_photo(request: OCRRequest):
    """Analyze photo from Mentra glasses and extract text using OCR"""
    ocr_model = get_ocr_model()
    result = await ocr_model.extract_text_from_image(request.image_base64)
    print(result)
    return result

# Modal deployment setup (only if Modal is available)
if MODAL_AVAILABLE:
    # Create Modal app (use 'app' as the variable name for Modal CLI)
    app = modal.App("rizzoids-backend-personal")
    
    # Define the image with FastAPI and all runtime dependencies
    image = modal.Image.debian_slim(python_version="3.12").pip_install([
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-dotenv==1.0.0",
        "pydantic==2.11.9",
        "pillow==10.1.0",
        "numpy",
        "easyocr",
        "google-cloud-vision",
        "anthropic==0.34.0",
        "cerebras-cloud-sdk==1.50.1",
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
