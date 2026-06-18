"""
config.py — Centralised configuration for SmartShala.

Reads all settings from environment variables (via .env file or Streamlit Cloud
secrets), validates required values at startup, and exports typed config values.
Every other module imports Config from here — no scattered os.getenv() calls.
"""

import os
from dotenv import load_dotenv

# Load .env file (no-op if it doesn't exist, e.g. on Streamlit Cloud)
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # --- LLM & STT Provider (Gemini handles both) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # --- Text-to-Speech ---
    TTS_VOICE: str = os.getenv("TTS_VOICE", "hi-IN-MadhurNeural")

    # --- Debug ---
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration. Returns list of error strings (empty = valid)."""
        errors = []

        # Check LLM/STT API key
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required. Set it in your .env file.")

        return errors

    @classmethod
    def get_llm_api_key(cls) -> str:
        """Return the API key for the configured LLM provider."""
        return cls.GEMINI_API_KEY
