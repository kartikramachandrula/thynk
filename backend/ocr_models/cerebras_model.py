import os
import base64
import io
from PIL import Image
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()
from cerebras.cloud.sdk import Cerebras

from .base_ocr import BaseOCR, OCRResponse

# CEREBRAS AVAILABLE
try:
    import cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False
    print("Cerebras not available. Install cerebras to use Cerebras OCR.")


class CerebrasModel(BaseOCR):
    """Cerebras OCR implementation (scaffold)"""
    
    def __init__(self):
        self._client = None
        self._cerebras_client = None
    
    def is_available(self) -> bool:
        """Check if Cerebras is available (placeholder)"""
        # TODO: replace with actual availability check once wired
        return CEREBRAS_AVAILABLE and os.getenv("CEREBRAS_API_KEY") is not None
    
    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        return "Cerebras"
    
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
    
    async def extract_text_from_image(self, image_base64: str) -> OCRResponse:
        """Extract text from base64 encoded image (not implemented)."""
        try:
            # Get Cerebras client
            client = self._get_cerebras_client()
            
            # Determine image format from base64 data
            image_data = base64.b64decode(image_base64)
            pil_image = Image.open(io.BytesIO(image_data))
            
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

            # Make API call to Cerebras with text-only message (model: gpt-oss-120b)
            # Note: Cerebras chat API uses OpenAI-like schema and typically returns text content.
            # If/when image inputs are supported, this will need to be adapted.
            response = client.chat.completions.create(
                model="gpt-oss-120b",
                messages=[
                    {
                        "role": "user",
                        "content": f"{system_prompt}\n\n{user_prompt}",
                    }
                ],
                max_tokens=4000,
            )
            
            # Parse the response text from Cerebras
            try:
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
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Claude OCR processing failed: {str(e)}"
            )
