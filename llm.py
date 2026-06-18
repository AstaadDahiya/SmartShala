"""
llm.py — Provider-agnostic LLM client wrapper for SmartShala.

Exposes two functions:
  - generate(user_prompt, system_prompt) → raw text
  - generate_json(user_prompt, system_prompt) → parsed dict

Currently configured strictly for Gemini API.
"""

import json
import logging
import re

from config import Config
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(user_prompt: str, system_prompt: str, max_tokens: int = 1024) -> str:
    """Generate text from the configured Gemini provider. Returns raw string."""
    logger.debug(f"LLM generate (gemini): {user_prompt[:80]}...")
    return _gemini_generate(user_prompt, system_prompt, max_tokens)


def generate_json(
    user_prompt: str,
    system_prompt: str,
    max_tokens: int = 1024,
) -> dict:
    """Generate structured JSON from the LLM. Parses, retries once on failure."""
    raw = generate(user_prompt, system_prompt, max_tokens)

    # Attempt 1: parse directly
    parsed = _try_parse_json(raw)
    if parsed is not None:
        return parsed

    # Attempt 2: retry with a stricter instruction
    logger.warning("JSON parse failed on first attempt. Retrying with stricter prompt.")
    retry_prompt = (
        f"{user_prompt}\n\n"
        "IMPORTANT: You MUST return ONLY valid JSON. "
        "No markdown code fences, no extra text before or after the JSON."
    )
    raw_retry = generate(retry_prompt, system_prompt, max_tokens)

    parsed = _try_parse_json(raw_retry)
    if parsed is not None:
        return parsed

    raise ValueError(
        f"LLM did not return valid JSON after 2 attempts.\n"
        f"Last raw response: {raw_retry[:500]}"
    )


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _try_parse_json(text: str) -> dict | None:
    """Try to extract and parse JSON from a string. Returns None on failure."""
    text = text.strip()

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences (```json ... ```)
    stripped = re.sub(r"^```(?:json)?\s*", "", text)
    stripped = re.sub(r"\s*```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Find the first { ... } block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

def _gemini_generate(user_prompt: str, system_prompt: str, max_tokens: int) -> str:
    """Generate using Google Gemini API with retry + model fallback."""
    import time

    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    # Models to try in order (fallback chain)
    models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
    ]

    last_error = None
    for model_name in models:
        for attempt in range(3):
            try:
                logger.debug(f"LLM: trying {model_name} (attempt {attempt + 1})")

                config_kwargs = {
                    "system_instruction": system_prompt,
                    "max_output_tokens": max(max_tokens, 2048),
                    "temperature": 0.7,
                    "response_mime_type": "application/json",
                }

                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(**config_kwargs),
                )

                return response.text

            except Exception as e:
                last_error = e
                error_str = str(e)
                if "503" in error_str or "429" in error_str:
                    wait = (attempt + 1) * 2
                    logger.warning(
                        f"LLM {model_name} attempt {attempt + 1} failed: "
                        f"{error_str[:80]}. Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                    continue
                else:
                    logger.error(f"LLM {model_name} non-retryable error: {e}")
                    break

    raise ValueError(f"All LLM attempts failed. Last error: {last_error}")
