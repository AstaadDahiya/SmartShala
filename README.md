# 🎓 SmartShala — Voice-Enabled AI Teaching Assistant

> A voice-first AI co-pilot that helps teachers in Indian classrooms get instant Hinglish explanations and run quick quizzes — hands-free, on a smart board.

**Built for the Connecting Dreams Foundation — Round 2 Assignment (Option A)**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎤 **Voice Input** | Tap to speak in Hindi, English, or Hinglish — the app understands all |
| 📚 **Explain Mode** | Say *"Photosynthesis samjhao"* → get a short Hinglish explanation with key points |
| 📝 **Quiz Mode** | Say *"Gravity pe quiz lo"* → get 4 MCQs with answers and explanations |
| 🔊 **Audio Playback** | Every response is read aloud via Hindi neural TTS |
| ⌨️ **Text Fallback** | Type your question if voice input doesn't work |
| 🌙 **Dark/Light Mode** | Toggle between light (presentation) and dark (classroom) themes |
| 🛡️ **Guardrails** | Off-topic or inappropriate requests are politely redirected |

## 🏗️ Architecture

```
Voice/Text Input → STT (Gemini) → Intent Extraction (LLM)
                                        ↓
                              ┌─────────┴─────────┐
                              ↓                   ↓
                      Explain (LLM)         Quiz (LLM)
                              ↓                   ↓
                      Hinglish Content    MCQ Questions
                              ↓                   ↓
                      Display + TTS       Display + TTS
```

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Frontend / UI** | Streamlit |
| **LLM** | Google Gemini (2.5 Flash → 2.0 Flash Lite fallback) |
| **Speech-to-Text** | Gemini multimodal audio transcription |
| **Text-to-Speech** | edge-tts (Microsoft Hindi neural voice — free) |
| **Data Models** | Pydantic v2 |

## 🚀 Running Locally

### Prerequisites
- **Python 3.10+**
- A **Gemini API key** — get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/AstaadDahiya/SmartShala.git
cd SmartShala

# 2. Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📂 Project Structure

```
SmartShala/
├── app.py              # Streamlit UI & orchestration (main entry point)
├── config.py           # Centralised config from environment variables
├── llm.py              # Gemini LLM client with retry & model fallback
├── stt.py              # Speech-to-text via Gemini multimodal
├── tts.py              # Text-to-speech via edge-tts (free)
├── intent.py           # Intent & topic extraction (LLM call #1)
├── content.py          # Explanation & quiz generation (LLM call #2)
├── models.py           # Pydantic response schemas
├── prompts/            # System prompt templates
│   ├── intent_system.txt
│   ├── explain_system.txt
│   └── quiz_system.txt
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .streamlit/
│   └── config.toml     # Streamlit theme configuration
└── files/              # Documentation
    ├── PRD.md          # Product requirements document
    ├── TECH.md         # Technical design & architecture
    └── TASKS.md        # Build plan & timeline
```

## 🎯 Prompt Design

- **Intent Extraction**: Classifies each request as `explain`, `quiz`, or `unclear` and extracts a normalised topic — strict JSON output
- **Explanation Prompt**: Generates 2–4 sentence Hinglish explanations with key points, tuned for Class 6–8 reading level
- **Quiz Prompt**: Produces 4 MCQs with 4 options each, correct answer index, and Hinglish explanation
- **Curriculum Guardrails**: Lightweight keyword check + LLM-level content filtering

Prompt templates are in `prompts/` — see `files/TECH.md` §5 for full design rationale.

## 🌍 Localisation

- **Output Language**: Hinglish (code-mixed Hindi-English in Latin/Roman script) — matches how students and teachers in Haryana government schools actually communicate
- **TTS Voice**: `hi-IN-MadhurNeural` — Hindi neural voice that handles code-switching well
- **STT**: Gemini's multilingual audio model handles Hindi, English, and Hinglish seamlessly

## 🔒 Security

- API keys are loaded from environment variables (`.env`) — never committed to git
- `.env` is in `.gitignore` — only `.env.example` (with empty values) is tracked
- No user data is stored or logged

## ⚠️ Known Limitations

- STT accuracy for heavily code-mixed speech can vary — text input fallback exists for this reason
- No session persistence — each browser session starts fresh
- Streamlit's UI has limitations compared to a full React/Next.js frontend
- Requires internet connection for Gemini API and edge-tts

## 📝 License

Built as a Round 2 technical assignment for the **Connecting Dreams Foundation** AI Builders programme.

## 👨‍💻 Author

**Aryaan Dahiya** — [GitHub](https://github.com/AstaadDahiya)
