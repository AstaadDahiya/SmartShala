"""
intent.py — Intent & Topic Extraction (LLM call #1).

Classifies a teacher's spoken transcript into:
  - explain  → teacher wants a concept explained
  - quiz     → teacher wants a quiz on a topic
  - unclear  → request is ambiguous, off-topic, or unrecognised

Also extracts the normalised topic string.

Public API:
  extract_intent(transcript) → IntentResult
"""

import logging
import os

from llm import generate_json
from models import IntentResult

logger = logging.getLogger(__name__)

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "intent_system.txt")


def extract_intent(transcript: str) -> IntentResult:
    """Extract intent and topic from a teacher's spoken transcript."""
    if not transcript or not transcript.strip():
        return IntentResult(mode="unclear", topic=None)

    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    user_prompt = f'Teacher said: "{transcript}"'

    try:
        result = generate_json(user_prompt, system_prompt, max_tokens=150)
        intent = IntentResult(**result)
        logger.info(f"Intent: mode={intent.mode}, topic={intent.topic}")
        return intent

    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        # Graceful degradation — ask for clarification instead of crashing
        return IntentResult(mode="unclear", topic=None)
