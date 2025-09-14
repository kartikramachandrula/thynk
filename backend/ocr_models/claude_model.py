import base64
import io
import os
from PIL import Image
import anthropic
import json
from typing import List, Dict, Any
from fastapi import HTTPException

from .base_ocr import BaseOCR, SimpleOCRResponse, TextPhrase

# Claude API imports
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("Anthropic not available. Install anthropic to use Claude OCR.")

class ClaudeModel(BaseOCR):
    """Claude 4 Sonnet implementation of the OCR interface"""
    
    def __init__(self):
        self._claude_client = None
    
    def is_available(self) -> bool:
        """Check if Claude is available"""
        return CLAUDE_AVAILABLE and os.getenv("CLAUDE_KEY") is not None
    
    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        return "Claude 4 Sonnet"
    
    def _get_claude_client(self):
        """Get or initialize Claude client (lazy loading)"""
        if self._claude_client is None:
            if not self.is_available():
                raise HTTPException(
                    status_code=500, 
                    detail="Claude API not available. Please set CLAUDE_KEY environment variable."
                )
            claude_api_key = os.getenv("CLAUDE_KEY")
            self._claude_client = anthropic.Anthropic(api_key=claude_api_key)
        return self._claude_client
    
    async def extract_text_from_image(self, image_base64: str) -> SimpleOCRResponse:
        """Extract text from base64 encoded image using Claude. Returns plain text only."""

        try:
            # Get Claude client
            client = self._get_claude_client()

            # Determine image format from base64 data
            image_data = base64.b64decode(image_base64)
            pil_image = Image.open(io.BytesIO(image_data))

            # Convert to supported format if needed
            if pil_image.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                buffer = io.BytesIO()
                pil_image.save(buffer, format='PNG')
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                media_type = "image/png"
            else:
                media_type = f"image/{pil_image.format.lower()}"

            # Prompts for plain text OCR output
            system_prompt = (
                "You are an expert OCR system. Extract all visible text from the image. "
                "If the text contains mathematical expressions or equations, format them using MathJAX: use $...$ for inline math and $$...$$ for display equations (e.g., \\frac{a}{b}, \\sqrt{x}, superscripts as x^{2}, subscripts as a_{i}). "
                "Return ONLY the extracted text with no additional commentary, labels, or JSON."
            )
            user_prompt = "Extract and return only the text from this image. When writing any equations, use MathJAX formatting as described."

            # Claude API call
            response = client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                        ],
                    }
                ],
            )

            # Gather all text blocks into a single string
            response_text_parts: List[str] = []
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    response_text_parts.append(block.text)
            full_text = "\n".join([p for p in response_text_parts if p]).strip()

            return SimpleOCRResponse(
                full_text=full_text,
                success=True,
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Claude OCR processing failed: {str(e)}",
            )
