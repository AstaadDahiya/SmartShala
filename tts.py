"""
tts.py — Text-to-Speech module for SmartShala.

Primary: Gemini TTS (uses the same API key as the LLM — no extra setup).
Fallback: edge-tts (free Microsoft Edge neural voices).

Caches results in memory to avoid redundant synthesis on Streamlit reruns.

Public API:
  speak(text) → bytes (WAV/MP3 audio)
"""

import base64
import hashlib
import io
import logging
import struct
import wave

from config import Config

logger = logging.getLogger(__name__)

# In-memory cache: hash → audio bytes
_tts_cache: dict[str, bytes] = {}


def speak(text: str) -> bytes:
    """Convert Hinglish text to speech. Returns audio bytes (WAV or MP3)."""
    if not text:
        return b""

    # Cache key
    cache_key = hashlib.md5(f"{text}:gemini-tts".encode("utf-8")).hexdigest()

    if cache_key in _tts_cache:
        logger.debug(f"TTS cache hit: '{text[:50]}...'")
        return _tts_cache[cache_key]

    # Try Gemini TTS first, then fall back to edge-tts
    audio_bytes = _try_gemini_tts(text)
    if not audio_bytes:
        logger.warning("Gemini TTS failed, trying edge-tts fallback...")
        audio_bytes = _try_edge_tts(text)

    if audio_bytes:
        _tts_cache[cache_key] = audio_bytes

    return audio_bytes or b""


# ---------------------------------------------------------------------------
# Gemini TTS (primary)
# ---------------------------------------------------------------------------

def _try_gemini_tts(text: str) -> bytes | None:
    """Generate speech using Gemini's native TTS model."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=Config.GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["audio"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore",  # Clear, natural voice
                        )
                    )
                ),
            ),
        )

        # Extract raw PCM audio data from response
        audio_part = response.candidates[0].content.parts[0]
        pcm_data = audio_part.inline_data.data

        if not pcm_data:
            logger.warning("Gemini TTS returned empty audio data")
            return None

        # Convert raw PCM to WAV (Gemini returns raw PCM at 24kHz, 16-bit, mono)
        wav_bytes = _pcm_to_wav(pcm_data, sample_rate=24000, channels=1, sample_width=2)

        logger.info(f"Gemini TTS generated {len(wav_bytes)} bytes of WAV audio")
        return wav_bytes

    except Exception as e:
        logger.error(f"Gemini TTS error: {e}")
        return None


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000,
                channels: int = 1, sample_width: int = 2) -> bytes:
    """Convert raw PCM bytes to a valid WAV file."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# edge-tts fallback
# ---------------------------------------------------------------------------

def _try_edge_tts(text: str) -> bytes | None:
    """Generate speech using edge-tts (fallback)."""
    try:
        import asyncio
        import edge_tts

        async def _generate():
            communicate = edge_tts.Communicate(text, Config.TTS_VOICE)
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            return buf.getvalue()

        audio_data = _run_async(_generate())
        if audio_data:
            logger.info(f"edge-tts generated {len(audio_data)} bytes of MP3 audio")
        return audio_data or None

    except Exception as e:
        logger.error(f"edge-tts error: {e}")
        return None


def _run_async(coro):
    """Run an async coroutine, handling existing event loops gracefully."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result(timeout=30)
