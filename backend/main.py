<<<<<<< HEAD
# Rizzoids Smart Glasses Backend
# OCR and AI-powered text analysis for smart glasses
=======
# Created by Melody Yu
# Created on Sep 13, 2025
# Enhanced for Thynk: Always Ask Y
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512

import os
import json
import time
import base64
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import modal
from fastapi import FastAPI, HTTPException, Request
<<<<<<< HEAD
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import numpy as np
from dotenv import load_dotenv

# Load environment variables
=======
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from PIL import Image
import numpy as np
from ocr_models.ocr_factory import OCRFactory
from ocr_models.base_ocr import SimpleOCRResponse
from redis_client import ThynkRedisClient


# Import Thynk system components
from .thynk_functions import (
    is_different, 
    context_compression, 
    get_context, 
    give_hint,
    lecture_context_compression
)
from .redis_client import redis_client
from .audio_transcription import audio_transcriber
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

>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
load_dotenv()

# Create FastAPI app
fastapi_app = FastAPI(title="Rizzoids Backend", version="1.0.0")
<<<<<<< HEAD

# Initialize FastAPI app
fastapi_app = FastAPI(
    title="Rizzoids Smart Glasses API",
    description="OCR and AI analysis for smart glasses",
    version="1.0.0"
)

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class OCRRequest(BaseModel):
    image_base64: str
    
class OCRResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    success: bool
    processing_time: Optional[float] = None

class AnalysisRequest(BaseModel):
    text: str
    context: Optional[str] = None

class AnalysisResponse(BaseModel):
    analysis: str
    suggestions: List[str]
    confidence: float
    success: bool

# Global OCR reader (lazy loading)
_ocr_reader = None

def get_ocr_reader():
    """Get or initialize EasyOCR reader"""
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr
            _ocr_reader = easyocr.Reader(['en'], gpu=False)
        except ImportError:
            raise HTTPException(
                status_code=500, 
                detail="EasyOCR not available. Please install easyocr."
            )
    return _ocr_reader

def get_redis_client():
    """Get Redis client for context storage"""
    from upstash_redis import Redis
    return Redis(url=os.environ["UPSTASH_REDIS_REST_URL"], token=os.environ["UPSTASH_REDIS_REST_TOKEN"])

def get_claude_client():
    """Get Claude API client"""
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=os.environ.get("CLAUDE_KEY"))
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Anthropic client not available"
        )

def call_claude_api(messages: List[Dict[str, str]], max_tokens: int = 1500) -> str:
    """Call Claude API with messages"""
    client = get_claude_client()
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=max_tokens,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return f"Sorry, I encountered an error: {e}"

def context_compression(input_json: Dict[str, Any]) -> None:
    """Process and store context from smart glasses input"""
    learned_text = input_json.get("text", "")
    if not learned_text:
        return
    
    prompt = f"""You are analyzing content from smart glasses. Extract ONLY relevant math problems, concepts, or work shown. IGNORE all other content. If no math content is found, respond with 'NO_RELEVANT_CONTENT'.

Content to analyze:
---
{learned_text}
---"""

    messages = [{"role": "user", "content": prompt}]
    extracted_content = call_claude_api(messages)
    
    if extracted_content.strip() != "NO_RELEVANT_CONTENT":
        redis_client = get_redis_client()
        timestamp = datetime.now(timezone.utc).isoformat()
        context_entry = {"content": extracted_content, "timestamp": timestamp, "unix_time": int(time.time())}
        key = f"math_context:{int(time.time() * 1000)}"
        redis_client.set(key, json.dumps(context_entry))
        redis_client.expire(key, 86400)

def get_context() -> Dict[str, Any]:
    """Retrieve stored context with time-based weighting"""
    redis_client = get_redis_client()
    context_keys = redis_client.keys("math_context:*")
    if not context_keys:
        return {"context": "No previous context available", "entries": []}
    
    context_entries = []
    current_time = int(time.time())
    for key in context_keys:
        try:
            entry_data = redis_client.get(key)
            if entry_data:
                entry = json.loads(entry_data)
                age_hours = (current_time - entry["unix_time"]) / 3600
                entry["weight"] = max(0.1, 1.0 / (1 + age_hours * 0.5))
                context_entries.append(entry)
        except (json.JSONDecodeError, KeyError):
            continue
    
    context_entries.sort(key=lambda x: x["weight"], reverse=True)
    top_entries = context_entries[:5]
    combined_context = "\n\n".join([f"Context (weight: {entry['weight']:.2f}): {entry['content']}" for entry in top_entries])
    return {"context": combined_context, "entries": len(context_entries), "top_entries": top_entries}

# API Endpoints
@fastapi_app.get("/")
async def root():
    return {
        "message": "Rizzoids Smart Glasses API", 
        "status": "running",
        "version": "1.0.0",
        "endpoints": ["/ocr", "/analyze", "/give_hint", "/context_compression", "/context_status", "/health"]
    }
=======
thynk_client = ThynkRedisClient()

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
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512

@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rizzoids-backend"}

<<<<<<< HEAD
@fastapi_app.post("/context_compression")
async def context_compression_endpoint(request: Request):
    """Process glasses input and store relevant math context"""
    try:
        data = await request.json()
        context_compression(data)
        return {"status": "success", "message": "Context processed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@fastapi_app.post("/give_hint")
async def give_hint(request: Request):
    """Generate tutoring hints based on stored context and current situation"""
    try:
        data = await request.json()
        current_learned = data.get("learned", "")
        stored_context = get_context()["context"]
        
        prompt = f"""You are a friendly math tutor. Based on the stored context and the student's current situation, provide a helpful hint for the next step in markdown format.

STORED CONTEXT:
{stored_context}

CURRENT SITUATION:
{current_learned}"""
        
        messages = [{"role": "user", "content": prompt}]
        hint_response = call_claude_api(messages)
        return Response(hint_response, media_type="text/markdown; charset=utf-8")
    except Exception as e:
        return Response(f"Error generating hint: {str(e)}", status_code=500)
=======
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

@fastapi_app.post("/process-audio", response_model=AudioResponse)
async def process_audio(request: AudioRequest):
    """
    Process audio input for lecture mode - transcribe and compress content
    """
    try:
        # Transcribe audio using Whisper
        transcription_result = audio_transcriber.transcribe_base64_audio(request.audio_base64)
        
        if not transcription_result["success"]:
            return {
                "success": False,
                "error": f"Transcription failed: {transcription_result.get('error', 'Unknown error')}",
                "transcript": "",
                "session_id": request.session_id
            }
        
        transcript = transcription_result["text"]
        
        # Skip processing if transcript is too short or empty
        if len(transcript.strip()) < 10:
            return {
                "success": True,
                "transcript": transcript,
                "compressed_content": "Audio too short to process",
                "session_id": request.session_id,
                "compression_stats": {
                    "original_length": len(transcript),
                    "compressed_length": 0
                }
            }
        
        # Use lecture-specific context compression with session ID
        session_id = request.session_id or "default"
        compression_result = await lecture_context_compression(transcript, session_id)
        
        if compression_result["success"]:
            return {
                "success": True,
                "transcript": transcript,
                "compressed_content": compression_result["compressed_content"],
                "session_id": session_id,
                "compression_stats": {
                    "original_length": compression_result["original_length"],
                    "compressed_length": compression_result["compressed_length"]
                }
            }
        else:
            return {
                "success": False,
                "error": compression_result.get("error", "Failed to compress lecture content"),
                "transcript": transcript,
                "session_id": session_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Audio processing failed: {str(e)}"
        }
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512

@fastapi_app.get("/context_status")
async def context_status():
    """Debug endpoint to check stored context"""
    try:
<<<<<<< HEAD
        context_data = get_context()
        return {"status": "success", "total_entries": context_data["entries"], "context_preview": context_data["context"][:500] + "..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@fastapi_app.post("/ocr", response_model=OCRResponse)
async def perform_ocr(request: OCRRequest):
    """Extract text from image using OCR"""
    start_time = time.time()
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64)
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
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
            if confidence > 0.3:  # Filter low confidence results
                detected_texts.append(text)
                confidences.append(confidence)
        
        # Combine all detected text
        full_text = ' '.join(detected_texts) if detected_texts else ""
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        processing_time = time.time() - start_time
        
        return OCRResponse(
            text=full_text,
            confidence=avg_confidence,
            success=True,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )

@fastapi_app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """Analyze extracted text using Claude AI"""
    try:
        client = get_claude_client()
        
        prompt = f"""You are an AI assistant for smart glasses. Analyze the following text and provide helpful insights.

Text to analyze: {request.text}
Context: {request.context or 'No additional context'}

Please provide:
1. A brief analysis of what this text contains
2. 3-5 actionable suggestions or insights
3. Your confidence level (0-1)

Format your response as JSON with 'analysis', 'suggestions' (array), and 'confidence' fields."""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse Claude's response
        try:
            result = json.loads(response.content[0].text)
            return AnalysisResponse(
                analysis=result.get("analysis", "Analysis completed"),
                suggestions=result.get("suggestions", []),
                confidence=result.get("confidence", 0.8),
                success=True
            )
        except json.JSONDecodeError:
            # Fallback if Claude doesn't return JSON
            return AnalysisResponse(
                analysis=response.content[0].text,
                suggestions=["Review the extracted text", "Consider the context"],
                confidence=0.7,
                success=True
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@fastapi_app.post("/process-glasses-image", response_model=Dict[str, Any])
async def process_glasses_image(request: OCRRequest):
    """Complete pipeline: OCR + Analysis for smart glasses"""
    try:
        # Step 1: Extract text
        ocr_result = await perform_ocr(request)
        
        if not ocr_result.success or not ocr_result.text.strip():
            return {
                "success": False,
                "message": "No text detected in image",
                "ocr_result": ocr_result.dict()
            }
        
        # Step 2: Store context if it's math-related
        context_compression({"text": ocr_result.text})
        
        # Step 3: Analyze text
        analysis_request = AnalysisRequest(
            text=ocr_result.text,
            context="Smart glasses capture"
        )
        analysis_result = await analyze_text(analysis_request)
        
        return {
            "success": True,
            "ocr_result": ocr_result.dict(),
            "analysis_result": analysis_result.dict(),
            "processing_pipeline": "OCR + Context Storage + AI Analysis completed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline processing failed: {str(e)}"
        )

# Modal deployment
app = modal.App("rizzoids-smart-glasses")

# Define container image with all dependencies
image = modal.Image.debian_slim(python_version="3.12").pip_install([
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "python-dotenv==1.0.0",
    "pydantic==2.5.0",
    "pillow==10.1.0",
    "numpy",
    "easyocr==1.7.0",
    "anthropic==0.25.0",
    "opencv-python-headless",
    "redis==5.0.1",
    "upstash-redis==0.15.0"
])

@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=300,
    memory=2048,
    cpu=2.0
)
@modal.asgi_app()
def modal_app():
    return fastapi_app

# Local development
if __name__ == "__main__":
    import uvicorn
    import uvicorn
=======
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
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
<<<<<<< HEAD
    )
=======
    )
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
