from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(title="Rizzoids Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Rizzoids Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rizzoids-backend"}

@app.get("/give-hint")
async def give_hint():
    """Outputs the text to the user"""
    text = "Hello, here's your hint!"
    return {"hint": text, "success": True}

if __name__ == "__main__":
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
