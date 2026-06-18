"""
stt.py — Speech-to-Text module for SmartShala.

Uses Gemini's native multimodal capabilities to transcribe audio.
Gemini handles any audio format (WAV, WebM/Opus, MP3, etc.) directly,
which solves the format mismatch issue with Streamlit's audio_input
(records WebM/Opus, not WAV).

Public API:
  transcribe(audio_bytes) → str
"""

import logging

from config import Config
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# System prompt tuned for Hinglish classroom transcription
_TRANSCRIPTION_PROMPT = (
    "You are a speech-to-text transcription engine. "
    "Transcribe the following audio EXACTLY as spoken. "
    "The speaker is a teacher in an Indian school speaking Hinglish "
    "(mixed Hindi-English in Latin/Roman script). "
    "Rules:\n"
    "- Output ONLY the transcription text, nothing else.\n"
    "- Use Latin/Roman script (not Devanagari).\n"
    "- Preserve the natural code-mixing (Hindi words in Latin script + English words).\n"
    "- If nothing is spoken or audio is silent/noise, return an empty string.\n"
    "- Do NOT add any labels, prefixes, explanations, or formatting.\n"
    "- Common classroom phrases: 'samjhao', 'batao', 'quiz lo', 'test lo', "
    "'kya hai', 'define karo', 'explain karo'."
)


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to text using Gemini. Returns transcript string."""
    if not audio_bytes:
        return ""

    logger.info(f"STT: transcribing {len(audio_bytes)} bytes via Gemini")

    # Detect MIME type from the audio bytes header
    mime_type = _detect_mime_type(audio_bytes)
    logger.debug(f"STT: detected MIME type: {mime_type}")

    # Models to try in order (fallback chain)
    models = ["gemini-2.5-flash", "gemini-2.0-flash-lite"]
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    last_error = None
    for model_name in models:
        for attempt in range(3):
            try:
                logger.debug(f"STT: trying {model_name} (attempt {attempt + 1})")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Content(
                            parts=[
                                types.Part.from_bytes(
                                    data=audio_bytes,
                                    mime_type=mime_type,
                                ),
                                types.Part.from_text(text=_TRANSCRIPTION_PROMPT),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        max_output_tokens=300,
                        temperature=0.1,
                    ),
                )

                transcript = response.text.strip() if response.text else ""
                transcript = _clean_transcript(transcript)

                logger.info(f"STT ({model_name}): transcript='{transcript[:100]}'")
                return transcript

            except Exception as e:
                last_error = e
                error_str = str(e)
                # Retry on 503 (overloaded) or 429 (rate limit)
                if "503" in error_str or "429" in error_str:
                    wait = (attempt + 1) * 2  # 2s, 4s, 6s
                    logger.warning(
                        f"STT {model_name} attempt {attempt + 1} failed: {error_str[:80]}. "
                        f"Retrying in {wait}s..."
                    )
                    import time
                    time.sleep(wait)
                    continue
                else:
                    # Non-retryable error — skip to next model
                    logger.error(f"STT {model_name} non-retryable error: {e}")
                    break

    logger.error(f"All STT attempts failed. Last error: {last_error}")
    raise last_error


def _detect_mime_type(audio_bytes: bytes) -> str:
    """Detect audio MIME type from file header bytes."""
    # WebM (Matroska) — Streamlit's audio_input format
    if audio_bytes[:4] == b"\x1a\x45\xdf\xa3":
        return "audio/webm"
    # WAV
    if audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "audio/wav"
    # MP3 (ID3 tag or sync word)
    if audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
        return "audio/mp3"
    # OGG
    if audio_bytes[:4] == b"OggS":
        return "audio/ogg"
    # FLAC
    if audio_bytes[:4] == b"fLaC":
        return "audio/flac"
    # M4A / AAC (ftyp box)
    if audio_bytes[4:8] == b"ftyp":
        return "audio/mp4"
    # Default to webm (most common from browsers)
    logger.warning("Could not detect audio MIME type, defaulting to audio/webm")
    return "audio/webm"


def _clean_transcript(text: str) -> str:
    """Remove common LLM artifacts from the transcript."""
    if not text:
        return ""

    # Remove quotes that the LLM might wrap the transcript in
    text = text.strip('"\'')

    # Remove common prefixes the LLM might add
    prefixes_to_remove = [
        "Transcription:",
        "Transcript:",
        "The speaker said:",
        "The teacher said:",
        "Speaker:",
    ]
    for prefix in prefixes_to_remove:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    return text.strip()
