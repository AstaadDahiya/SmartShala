"""
content.py — Content Generation (LLM call #2) for SmartShala.

Generates Hinglish educational content based on the extracted intent:
  - Explain mode → short explanation + key points
  - Quiz mode    → 3–5 multiple-choice questions

Also includes a lightweight curriculum-relevance heuristic.

Public API:
  generate_explanation(topic) → ExplainResponse
  generate_quiz(topic) → QuizResponse
  check_curriculum_relevance(topic) → bool
"""

import logging
import os

from llm import generate_json
from models import ExplainResponse, QuizResponse

logger = logging.getLogger(__name__)

_EXPLAIN_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "prompts", "explain_system.txt"
)
_QUIZ_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "prompts", "quiz_system.txt"
)


def generate_explanation(topic: str) -> ExplainResponse:
    """Generate a Hinglish explanation for a school topic."""
    with open(_EXPLAIN_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    user_prompt = (
        f'Topic: "{topic}". '
        f"Generate a clear, simple Hinglish explanation suitable for Class 6-8 students."
    )

    try:
        result = generate_json(user_prompt, system_prompt, max_tokens=600)
        response = ExplainResponse(**result)
        logger.info(f"Explanation generated for: {topic}")
        return response
    except Exception as e:
        logger.error(f"Explanation generation failed for '{topic}': {e}")
        raise


def generate_quiz(topic: str) -> QuizResponse:
    """Generate Hinglish MCQ quiz questions for a school topic."""
    with open(_QUIZ_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    user_prompt = (
        f'Topic: "{topic}". '
        f"Generate 4 multiple-choice questions for Class 6-8 students."
    )

    try:
        result = generate_json(user_prompt, system_prompt, max_tokens=1200)
        response = QuizResponse(**result)
        logger.info(
            f"Quiz generated for: {topic} ({len(response.questions)} questions)"
        )
        return response
    except Exception as e:
        logger.error(f"Quiz generation failed for '{topic}': {e}")
        raise


def check_curriculum_relevance(topic: str) -> bool:
    """Lightweight check: is this topic likely part of the Class 6-8 curriculum?

    Uses keyword matching — no LLM call needed. Returns True if the topic
    matches any known curriculum keyword, False otherwise.
    This is a soft gate: even if False, the LLM may still produce useful content.
    """
    curriculum_keywords = {
        # Science
        "photosynthesis", "gravity", "force", "motion", "cell", "atom",
        "molecule", "energy", "electricity", "magnet", "light", "sound",
        "heat", "water cycle", "ecosystem", "food chain", "nutrition",
        "respiration", "reproduction", "plant", "animal", "human body",
        "organ", "tissue", "bacteria", "virus", "chemical", "reaction",
        "acid", "base", "element", "compound", "mixture", "solar system",
        "planet", "earth", "moon", "star", "universe", "weather",
        "climate", "soil", "rock", "mineral", "metal", "nonmetal",
        "periodic table", "combustion", "friction", "pressure",
        "density", "speed", "velocity", "acceleration", "wave",
        "reflection", "refraction", "lens", "mirror", "spectrum",
        "pollution", "conservation", "biodiversity", "adaptation",
        "evolution", "genetics", "dna", "fossil", "earthquake",
        "volcano", "wind", "rain", "cloud", "ocean", "glacier",
        # Maths
        "fraction", "decimal", "percentage", "ratio", "proportion",
        "algebra", "geometry", "triangle", "circle", "area", "perimeter",
        "volume", "integer", "number", "equation", "graph", "data",
        "probability", "statistics", "angle", "line", "symmetry",
        "pattern", "measurement", "exponent", "square root", "factor",
        "multiple", "prime", "composite", "coordinate", "quadrilateral",
        "polygon", "congruence", "similarity", "theorem", "pythagoras",
        # Social Science / History / Civics
        "history", "geography", "constitution", "democracy", "government",
        "river", "mountain", "continent", "civilization", "empire",
        "freedom", "independence", "culture", "trade", "economy",
        "population", "migration", "agriculture", "industry",
        "mughal", "british", "india", "parliament", "rights",
        "duties", "judiciary", "legislature", "executive",
        # English / Language
        "grammar", "tense", "noun", "verb", "adjective", "pronoun",
        "adverb", "preposition", "conjunction", "sentence", "paragraph",
        "essay", "poem", "story", "vocabulary", "comprehension",
        "letter", "article", "speech", "debate",
    }

    topic_lower = topic.lower().strip()
    return any(kw in topic_lower for kw in curriculum_keywords)
