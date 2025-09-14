import os
import base64
import io
from PIL import Image
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()
from cerebras.cloud.sdk import Cerebras

<<<<<<< HEAD
from .base_ocr import BaseOCR, OCRResponse
=======
import json

from .base_ocr import BaseOCR, OCRResponse, SimpleOCRResponse, TextPhrase
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512

# CEREBRAS AVAILABLE
try:
    import cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False
    print("Cerebras not available. Install cerebras to use Cerebras OCR.")


class CerebrasModel(BaseOCR):
    """Cerebras OCR implementation (scaffold)"""
    
    def __init__(self, model_type: str = "gpt-oss-120b", max_tokens: int = 512):
        """Initialize Cerebras model.

        Allowed model_type values:
<<<<<<< HEAD
        - "llama3.1-8b"
        - "gpt-oss-120b" (default)
        - "qwen-3-32b"
        """
        allowed = {"llama3.1-8b", "gpt-oss-120b", "qwen-3-32b"}
=======
        - "gpt-oss-120b" (default)
        """
        allowed = {"gpt-oss-120b"}
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
        if model_type not in allowed:
            raise ValueError(f"Unsupported Cerebras model_type: {model_type}. Allowed: {sorted(allowed)}")

        self._model_name = model_type
        self._client = None
        self._cerebras_client = None
        self._max_tokens = max(1, int(max_tokens))
    
    def is_available(self) -> bool:
        """Check if Cerebras is available (placeholder)"""
        # TODO: replace with actual availability check once wired
        return CEREBRAS_AVAILABLE and os.getenv("CEREBRAS_API_KEY") is not None
    
    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        return f"Cerebras - {self._model_name}"
    
    def _get_cerebras_client(self):
        """Initialize Cerebras client (not implemented)."""
        if self._cerebras_client is None:
            if not self.is_available():
                raise HTTPException(
                    status_code=500, 
                    detail="Cerebras API not available. Please set CEREBRAS_API_KEY environment variable."
                )
            cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
            self._cerebras_client = Cerebras(api_key=cerebras_api_key)
        return self._cerebras_client
    
<<<<<<< HEAD
    async def extract_text_from_image(self, image_base64: str) -> OCRResponse:
=======
    async def extract_text_from_image(self, image_base64: str) -> SimpleOCRResponse:
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
        """Extract text from base64 encoded image (not implemented)."""
        try:
            # Get Cerebras client
            client = self._get_cerebras_client()
            
            # Determine image format from base64 data
            image_data = base64.b64decode(image_base64)
            pil_image = Image.open(io.BytesIO(image_data))
            
<<<<<<< HEAD
            # Convert to supported format if needed
            if pil_image.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                # Convert to PNG
                buffer = io.BytesIO()
                pil_image.save(buffer, format='PNG')
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Create structured prompt for OCR
            system_prompt = """You are an expert OCR system. Extract all visible text from the image and return it as structured JSON.

For each piece of text you detect, provide the exact text content.

Be thorough and detect all text, including small text, watermarks, and text in different orientations.
Return ONLY the JSON response, no additional text or formatting."""
            
            user_prompt = "Please extract all text from this image and return the structured JSON response."
=======
            # Always downscale and compress to keep prompt size under context limits
            # - Resize to max 512px on the longest side
            # - Re-encode as JPEG quality 50
            try:
                max_dim = 512
                pil_image = pil_image.convert('RGB')
                pil_image.thumbnail((max_dim, max_dim))
                buffer = io.BytesIO()
                pil_image.save(buffer, format='JPEG', quality=50, optimize=True)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            except Exception:
                # Fallback to original base64 if compression fails
                image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Prompt for plain text OCR output. Provide the image bytes as base64 inline.
            # NOTE: Cerebras chat API does not (yet) support image content blocks; we pass base64 inline.
            system_prompt = (
                "You are an expert OCR system. You will be given an image encoded as base64 bytes. "
                "Decode it and transcribe ALL visible text. If the text contains mathematical expressions or equations, format them using MathJAX: use $...$ for inline math and $$...$$ for display equations (e.g., \\frac{a}{b}, \\sqrt{x}, superscripts as x^{2}, subscripts as a_{i}). "
                "Return ONLY the extracted text with no additional commentary, labels, or JSON."
            )
            user_prompt = (
                "Extract and return only the text from this image (base64 below). When writing any equations, use MathJAX formatting as described.\n\n"
                "IMAGE_BASE64:\n" + image_base64
            )
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512

            # Make API call to Cerebras with text-only message (model: gpt-oss-120b)
            # Note: Cerebras chat API uses OpenAI-like schema and typically returns text content.
            # If/when image inputs are supported, this will need to be adapted.
            response = client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {
                        "role": "user",
                        "content": f"{system_prompt}\n\n{user_prompt}",
                    }
                ],
                max_tokens=self._max_tokens,
            )
            
            # Parse the response text from Cerebras
            try:
<<<<<<< HEAD
                response_text = response.choices[0].message.content
            except Exception:
                response_text = ""

            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text

            try:
                parsed_response = json.loads(json_text)
            except json.JSONDecodeError:
                parsed_response = {"phrases": [{"text": response_text}]}

            # Validate and normalize against schema
            try:
                if not isinstance(parsed_response, dict):
                    raise ValueError("Response is not a JSON object")

                if "phrases" not in parsed_response:
                    raise ValueError("Missing 'phrases' field in response")

                if not isinstance(parsed_response["phrases"], list):
                    raise ValueError("'phrases' field must be an array")

                validated_phrases = []
                for i, phrase in enumerate(parsed_response["phrases"]):
                    if not isinstance(phrase, dict):
                        raise ValueError(f"Phrase {i} is not an object")
                    if "text" not in phrase:
                        raise ValueError(f"Phrase {i} missing required text field")
                    if not isinstance(phrase["text"], str):
                        raise ValueError(f"Phrase {i} text must be a string")
                    validated_phrases.append({"text": phrase["text"], "confidence": 0.9})  # Default confidence
                parsed_response["phrases"] = validated_phrases
            except (ValueError, KeyError) as e:
                print(f"JSON validation error: {e}")
                parsed_response = {"phrases": [{"text": "", "confidence": 0.9}]}
            
            # Extract phrases
            phrases_data = parsed_response.get("phrases", [])
            phrases = [TextPhrase(text=p["text"], confidence=p["confidence"]) for p in phrases_data]
            
            # Calculate full text and average confidence
            full_text = " ".join([phrase.text for phrase in phrases])
            avg_confidence = sum([phrase.confidence for phrase in phrases]) / len(phrases) if phrases else 0.0
            
            # Log results
            for phrase in phrases:
                print(f"{phrase.text} (confidence: {phrase.confidence})")
            
            return OCRResponse(
                phrases=phrases,
                full_text=full_text,
                average_confidence=avg_confidence,
                success=True
=======
                full_text = (response.choices[0].message.content or "").strip()
            except Exception:
                full_text = ""

            return SimpleOCRResponse(
                full_text=full_text,
                success=True,
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
<<<<<<< HEAD
                detail=f"Claude OCR processing failed: {str(e)}"
=======
                detail=f"Cerebras OCR processing failed: {str(e)}"
>>>>>>> 948a37ea296a26d67b78ce30e503ad388b399512
            )
