from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

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

# Modal deployment setup (only if Modal is available)
if MODAL_AVAILABLE:
    # Create Modal app (use 'app' as the variable name for Modal CLI)
    app = modal.App("rizzoids-backend-personal")
    
    # Define the image with FastAPI
    image = modal.Image.debian_slim(python_version="3.12").pip_install([
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-dotenv==1.0.0"
    ])
    
    # Modal deployment using the same FastAPI app
    @app.function(
        image=image,
        timeout=3600,
        memory=1024,
        cpu=1.0
    )
    @modal.concurrent(max_inputs=50)
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
