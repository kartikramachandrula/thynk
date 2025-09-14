# Rizzoids Smart Glasses Backend
# OCR and AI-powered text analysis for smart glasses

import os
import json
import time
import base64
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import modal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
fastapi_app = FastAPI(title="Rizzoids Backend", version="1.0.0")

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

@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rizzoids-backend"}

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

@fastapi_app.get("/context_status")
async def context_status():
    """Debug endpoint to check stored context"""
    try:
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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
