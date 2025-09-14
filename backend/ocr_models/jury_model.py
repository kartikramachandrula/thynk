import os
from fastapi import HTTPException
import os

# Optional Anthropic import for aggregation step
try:
    import anthropic
    _ANTHROPIC_OK = True
except ImportError:
    _ANTHROPIC_OK = False

from .base_ocr import BaseOCR, SimpleOCRResponse, TextPhrase
from .claude_model import ClaudeModel
from .cerebras_model import CerebrasModel

# Placeholder availability flag for Jury (orchestrator always available)
JURY_AVAILABLE = True


class JuryModel(BaseOCR):
    """Jury OCR implementation that ensembles multiple models.

    Runs Claude and three Cerebras variants (llama3.1-8b, gpt-oss-120b, qwen-3-32b),
    with restricted tokens, and returns up to 4 outputs.
    """

    def __init__(self, cerebras_max_tokens: int = 256):
        self._cerebras_max_tokens = max(1, int(cerebras_max_tokens))

    def is_available(self) -> bool:
        """Orchestrator is available if at least one underlying model is available."""
        claude_ok = False
        try:
            claude_ok = ClaudeModel().is_available()
        except Exception:
            claude_ok = False

        cerebras_ok = False
        try:
            cerebras_ok = CerebrasModel().is_available()
        except Exception:
            cerebras_ok = False

        return JURY_AVAILABLE and (claude_ok or cerebras_ok)

    def get_model_name(self) -> str:
        """Get the name of the OCR model"""
        return "Jury (Claude + Cerebras ensemble)"

    def _get_jury_client(self):
        """No concrete client to initialize for the orchestrator."""
        return None

    async def extract_text_from_image(self, image_base64: str) -> SimpleOCRResponse:
        """Run multiple OCR backends and return up to 4 outputs as phrases."""
        texts: list[str] = []

        # 1) Run Claude (if available)
        try:
            claude = ClaudeModel()
            if claude.is_available():
                res = await claude.extract_text_from_image(image_base64)
                if res and res.full_text:
                    candidate = res.full_text.strip()
                    print("Jury candidate [Claude]:", candidate)
                    texts.append(candidate)
        except Exception as e:
            # Log and continue with others
            print(f"Jury: Claude failed: {e}")

        # 2) Run Cerebras variants (if available)
        cerebras_variants = [
            "gpt-oss-120b",
        ]
        for model_type in cerebras_variants:
            if len(texts) >= 4:
                break
            # try:
            cerebras = CerebrasModel(model_type=model_type, max_tokens=self._cerebras_max_tokens)
            if cerebras.is_available():
                res = await cerebras.extract_text_from_image(image_base64)
                if res and res.full_text:
                    candidate = res.full_text.strip()
                    print(f"Jury candidate [Cerebras::{model_type}]:", candidate)
                    texts.append(candidate)
            # except Exception as e:
            #     print(f"Jury: Cerebras ({model_type}) failed: {e}")

        # Keep only first 4 outputs
        texts = [t for t in texts if t]
        texts = texts[:4]

        # Log all candidates
        print(f"Jury candidates collected ({len(texts)}):")
        for i, t in enumerate(texts, start=1):
            print(f"  {i}. {t}")

        if not texts:
            raise HTTPException(status_code=500, detail="No OCR outputs available from ensemble")

        # Aggregate the four inputs using Claude 4 Sonnet (text-only). If unavailable, fall back.
        aggregated_text = None
        if _ANTHROPIC_OK and os.getenv("CLAUDE_KEY"):
            try:
                client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_KEY"))
                numbered = "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])
                system_prompt = (
                    "You are a world-class OCR aggregation system. You will be given up to four OCR outputs "
                    "that attempt to read the same scene. Your job is to produce a single, clean, faithful, and concise "
                    "final text that best represents the underlying content. Remove duplicates, resolve minor conflicts, "
                    "and prefer the clearly correct words. If any mathematical expressions or equations appear, ensure they are formatted using MathJAX: use $...$ for inline math and $$...$$ for display equations (e.g., \\frac{a}{b}, \\sqrt{x}, x^{2}, a_{i}). "
                    "Do not add commentary. Return ONLY the final text."
                )
                user_prompt = (
                    "Aggregate the following OCR candidate outputs into a single best representation. "
                    "When writing any equations, use MathJAX formatting as described.\n\n"
                    f"Candidates:\n{numbered}\n\nReturn only the final consolidated text."
                )
                resp = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=512,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                # Extract plain text from Anthropic response
                parts = []
                for block in getattr(resp, "content", []) or []:
                    if getattr(block, "type", None) == "text" and getattr(block, "text", None):
                        parts.append(block.text)
                aggregated_text = ("\n".join(parts)).strip() if parts else None
            except Exception as e:
                print(f"Jury: Aggregation with Claude failed: {e}")

        if not aggregated_text:
            # Fallback: choose the longest candidate as a heuristic
            aggregated_text = max(texts, key=len)

        # Log final aggregation result
        print("Jury aggregated text:", aggregated_text)

        return SimpleOCRResponse(
            full_text=aggregated_text,
            success=True,
        )
