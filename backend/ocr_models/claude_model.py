import base64
import io
import os
from PIL import Image
import anthropic
import json
from typing import List, Dict, Any
from fastapi import HTTPException

from .base_ocr import BaseOCR, OCRResponse, TextPhrase

# Claude API imports
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("Anthropic not available. Install anthropic to use Claude OCR.")

class ClaudeModel(BaseOCR):
    """Claude 3.5 Haiku implementation of the OCR interface"""
    
    def __init__(self):
        self._claude_client = None
    
    def is_available(self) -> bool:
        """Check if Claude is available"""
        return CLAUDE_AVAILABLE and os.getenv("CLAUDE_KEY") is not None
    
    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        return "Claude 3.5 Haiku"
    
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
    
    async def extract_text_from_image(self, image_base64: str) -> OCRResponse:
        """Extract text from base64 encoded image using Claude 3.5 Haiku"""
        
        try:
            # Get Claude client
            client = self._get_claude_client()
            
            # Determine image format from base64 data
            image_data = base64.b64decode(image_base64)
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Convert to supported format if needed
            if pil_image.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                # Convert to PNG
                buffer = io.BytesIO()
                pil_image.save(buffer, format='PNG')
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                media_type = "image/png"
            else:
                media_type = f"image/{pil_image.format.lower()}"
            
            # Define JSON schema for structured output
            json_schema = {
                "type": "object",
                "properties": {
                    "phrases": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "description": "The exact text content detected"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                    "description": "Confidence score from 0.0 to 1.0"
                                }
                            },
                            "required": ["text", "confidence"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["phrases"],
                "additionalProperties": False
            }
            
            # Create structured prompt for OCR
            system_prompt = """You are an expert OCR system. Extract all visible text from the image and return it as structured JSON.
            
For each piece of text you detect, provide:
- The exact text content
- A confidence score from 0.0 to 1.0 (where 1.0 is completely confident)

Be thorough and detect all text, including small text, watermarks, and text in different orientations.
Return only valid JSON that matches the required schema."""
            
            user_prompt = "Please extract all text from this image and return the structured JSON response."
            
            # Define a tool for structured output; the model must call this tool with valid JSON
            tools = [
                {
                    "name": "return_ocr",
                    "description": "Return the OCR result as structured JSON with phrases and confidences.",
                    "input_schema": json_schema,
                }
            ]

            # Make API call to Claude with tool-use to enforce schema
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
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
                tools=tools,
                tool_choice={"type": "tool", "name": "return_ocr"},
                extra_headers={
                    "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
                }
            )
            
            # Parse the response: prefer tool_use output
            parsed_response: Dict[str, Any] = {}
            tool_use_found = False
            for block in response.content:
                if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == "return_ocr":
                    # Anthropic SDK exposes tool input as `input`
                    parsed_response = dict(block.input) if hasattr(block, "input") else {}
                    tool_use_found = True
                    break

            if not tool_use_found:
                # Fallback to JSON parsing from text blocks
                response_text_parts: List[str] = []
                for block in response.content:
                    if getattr(block, "type", None) == "text":
                        response_text_parts.append(block.text)
                response_text = "\n".join([p for p in response_text_parts if p]).strip()

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
                    parsed_response = {"phrases": [{"text": response_text, "confidence": 0.7}]}

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
                    if "text" not in phrase or "confidence" not in phrase:
                        raise ValueError(f"Phrase {i} missing required fields")
                    if not isinstance(phrase["text"], str):
                        raise ValueError(f"Phrase {i} text must be a string")
                    if not isinstance(phrase["confidence"], (int, float)):
                        raise ValueError(f"Phrase {i} confidence must be a number")
                    confidence = max(0.0, min(1.0, float(phrase["confidence"])))
                    validated_phrases.append({"text": phrase["text"], "confidence": confidence})
                parsed_response["phrases"] = validated_phrases
            except (ValueError, KeyError) as e:
                print(f"JSON validation error: {e}")
                parsed_response = {"phrases": [{"text": "", "confidence": 0.0}]}
            
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
