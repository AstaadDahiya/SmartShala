"""
tts.py — Text-to-Speech module for SmartShala.

Uses edge-tts (free Microsoft Edge neural voices) to generate
spoken audio from Hinglish text. Caches results in memory to
avoid redundant synthesis on Streamlit reruns.

Public API:
  speak(text) → bytes (MP3 audio)
"""

import asyncio
import hashlib
import io
import logging

from config import Config

logger = logging.getLogger(__name__)

# In-memory cache: hash → MP3 bytes
_tts_cache: dict[str, bytes] = {}


def speak(text: str) -> bytes:
    """Convert Hinglish text to speech. Returns MP3 audio bytes."""
    if not text:
        return b""

    # Cache key includes text + voice name
    cache_key = hashlib.md5(
        f"{text}:{Config.TTS_VOICE}".encode("utf-8")
    ).hexdigest()

    if cache_key in _tts_cache:
        logger.debug(f"TTS cache hit: '{text[:50]}...'")
        return _tts_cache[cache_key]

    logger.info(f"TTS generating audio ({Config.TTS_VOICE}): '{text[:80]}...'")
    audio_bytes = _run_async(_generate_audio(text, Config.TTS_VOICE))
    _tts_cache[cache_key] = audio_bytes
    return audio_bytes


# ---------------------------------------------------------------------------
# edge-tts async implementation
# ---------------------------------------------------------------------------

async def _generate_audio(text: str, voice: str) -> bytes:
    """Generate speech audio using edge-tts (async)."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    audio_data = buffer.getvalue()
    logger.debug(f"TTS generated {len(audio_data)} bytes of audio")
    return audio_data


def _run_async(coro):
    """Run an async coroutine, handling existing event loops gracefully."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — safe to use asyncio.run()
        return asyncio.run(coro)

    # We're inside an existing event loop (e.g. some Streamlit environments).
    # Run in a separate thread to avoid blocking.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result(timeout=30)
