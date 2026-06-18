# SmartShala — Voice-Enabled AI Teaching Assistant

> A voice-first prototype that helps a teacher get a quick Hinglish concept explanation or run an instant quiz, hands-free, on a classroom smart board.
>
> Built for the Connecting Dreams Foundation Round 2 assignment (Option A: Voice-Enabled AI Teaching Assistant).

🔗 **Live demo:** _add link after deployment_
🎥 **Video walkthrough:** _add link after recording_

---

## What it does

1. The teacher taps **"Tap to Speak"** and asks, in Hinglish, for either:
   - an explanation of a topic (e.g. *"Photosynthesis ko simple tareeke se samjhao"*), or
   - a quiz on a topic (e.g. *"Fractions pe quiz le lo"*).
2. The app transcribes the request, figures out the intent and topic, and:
   - **Explain mode:** shows a short Hinglish explanation with key points, and reads it aloud.
   - **Quiz mode:** shows multiple-choice questions one at a time, reads each aloud, and reveals the answer on request.
3. If the request is unclear or off-topic, the app asks (in Hinglish) for clarification instead of guessing.

A text-input fallback is always available in case voice input doesn't work well.

## Why this scope

This prototype focuses on two of the four optional requirements from the brief — **Live Concept Simplification** and **Voice-Triggered Quizzing** — because they share one pipeline (voice → topic → Hinglish content → on-screen display + spoken playback) and together form a natural classroom loop: *explain a concept, then check understanding*. See `PRD.md` for the full rationale, and `TECH.md` §12 for documented stretch goals (Bilingual Dictation & Translation, Hands-Free Activity Guide).

## Tech Stack

| Component | Choice |
|---|---|
| App / UI | Streamlit |
| Speech-to-text | faster-whisper (local dev) / OpenAI Whisper API (cloud) |
| LLM | Gemini API (default) — provider-agnostic, swappable to OpenAI/Anthropic |
| Text-to-speech | edge-tts (Hindi neural voice) |

See `TECH.md` for full architecture, data flow, and prompt design details.

## Prompt Design (summary)

- A small "intent extraction" prompt classifies each request as `explain`, `quiz`, or `unclear`, and extracts a normalized topic.
- "Explanation" and "quiz" prompts include 2–3 worked Hinglish examples to keep generated content in natural code-mixed Hindi-English at a Class 6–8 reading level, and ask for strict JSON output.
- A lightweight relevance check redirects clearly off-topic requests with a friendly Hinglish message rather than generating unrelated content.

Full prompt templates live in `prompts/` and are documented in `TECH.md` §5.

## Localisation Approach

- Output language: **Hinglish** (code-mixed Hindi-English, Latin script) — matches how teachers and students in the target classroom actually communicate, rather than formal Hindi or English-only.
- TTS voice: Hindi neural voice (`hi-IN-MadhurNeural` / `hi-IN-SwaraNeural` via edge-tts), which handles code-mixed text reasonably well.
- STT: configured for Hindi/auto-detect to better capture code-mixed speech.

## Running Locally

### Prerequisites
- **Python 3.10+**
- **ffmpeg** installed (required by faster-whisper for audio processing):
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd smartshala-ai-teaching-assistant

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# then edit .env with your API key(s)

# 4. Run the app
streamlit run app.py
```

## Project Structure

```
smartshala-ai-teaching-assistant/
├── app.py              # Streamlit UI & orchestration
├── config.py           # Centralised config (env vars, defaults, validation)
├── stt.py              # Speech-to-text (faster-whisper / Whisper API)
├── intent.py           # Intent/topic extraction
├── content.py          # Explanation/quiz generation
├── tts.py              # Text-to-speech
├── llm.py              # LLM client wrapper
├── models.py           # Pydantic response models
├── prompts/            # System prompt templates
├── requirements.txt
├── .env.example
├── PRD.md              # Product requirements
├── TECH.md             # Technical design
├── TASKS.md            # Build plan
└── AGENTS.md           # AI agent working conventions
```

## Known Limitations / Future Work

- Bilingual Dictation & Translation and Hands-Free Activity Guide (the other two brief options) are not implemented — see `TECH.md` §12 for how they'd extend this architecture.
- STT accuracy for heavily code-mixed speech can vary; the text-input fallback exists for this reason.
- No persistence — each session starts fresh (acceptable for a live-demo prototype).

## Credits

Built as a Round 2 technical assignment for the **Connecting Dreams Foundation** AI Builders programme.
