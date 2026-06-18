# TECH.md — SmartShala: Technical Design

Companion to `PRD.md`. This document defines architecture, stack, prompt design, and deployment so an agentic IDE (e.g. Antigravity) can implement the project with minimal back-and-forth.

---

## 1. Architecture Overview

```
                ┌─────────────────────────────────────────┐
                │              Browser UI                  │
                │   (Streamlit app — "smart board" view)   │
                │                                           │
                │  [🎤 Tap to Speak]  → records audio       │
                │  Transcript display                       │
                │  Result panel (explanation / quiz card)   │
                │  🔊 audio playback (TTS)                   │
                └───────────────┬───────────────────────────┘
                                 │ audio bytes / text
                                 ▼
                ┌─────────────────────────────────────────┐
                │              Backend (Python)             │
                │                                           │
                │  1. STT module  → transcript               │
                │  2. Intent/Topic parser (LLM call #1)      │
                │  3. Content generator (LLM call #2)        │
                │       - explain mode → JSON                │
                │       - quiz mode    → JSON                │
                │  4. TTS module  → audio bytes              │
                └───────────────┬───────────────────────────┘
                                 │
                                 ▼
                ┌─────────────────────────────────────────┐
                │           External APIs / Models          │
                │  - LLM: Gemini API (verify current model    │
                │    name at build time) — provider-agnostic  │
                │  - STT: faster-whisper (local dev) /         │
                │    Whisper API (cloud deploy)               │
                │  - TTS: edge-tts (free, Hindi neural voices)│
                └─────────────────────────────────────────┘
```

## 2. Tech Stack & Justification

| Layer | Choice | Why |
|---|---|---|
| Frontend/App | **Streamlit** | Matches the brief's suggested stack, fastest to build a "smart board" style UI, trivial free deployment (Streamlit Community Cloud) → satisfies "Live URL" deliverable quickly |
| Audio capture | `st.audio_input` (built into Streamlit ≥1.38) | No extra JS components needed; records mic audio directly in-browser |
| STT | **faster-whisper** (local dev, `small`/`base` model) · **OpenAI Whisper API** (cloud deploy) — toggled via `STT_BACKEND` env var in `stt.py` | faster-whisper: free, runs offline, decent Hindi/code-mixed accuracy · Whisper API: reliable on cloud hosts where faster-whisper's C++ deps won't install |
| LLM | **Gemini API** (verify current model name at build time via `google.generativeai.list_models()`) — abstracted behind a thin `llm.py` so swapping to OpenAI/Anthropic is a one-file change | Free tier available, strong Hindi/Hinglish generation, fast |
| TTS | **edge-tts** (Microsoft Edge neural voices, free, no API key) — e.g. `hi-IN-MadhurNeural` / `hi-IN-SwaraNeural` | Handles Hinglish text reasonably, no cost, simple Python API |
| Config | `python-dotenv` | Keep API keys out of source |
| Deployment | Streamlit Community Cloud (or Hugging Face Spaces as backup) | Free, one-click deploy from GitHub |

> **Provider-agnostic by design:** `llm.py`, `stt.py`, and `tts.py` each expose a single function (`generate(...)`, `transcribe(...)`, `speak(...)`). If you have an OpenAI or Anthropic key instead of Gemini, only `llm.py` needs to change — the rest of the app is unaffected. Document whichever provider you actually use in the README.

## 3. Component Design

### 3.1 `stt.py` — Speech-to-Text
- Input: audio bytes (WAV) from `st.audio_input`.
- Output: transcript string.
- Implementation: reads `STT_BACKEND` from env:
  - `faster_whisper` (default, local dev): uses `faster-whisper` with `language="hi"` or auto-detect.
  - `whisper_api` (cloud deploy): sends audio to OpenAI Whisper API (requires `OPENAI_API_KEY`).
- Fallback: if transcription confidence is very low or empty, prompt the user to type the request instead (text input field always visible as a backup).

### 3.2 `intent.py` — Intent & Topic Extraction (LLM call #1)
- Input: transcript.
- Output (JSON): `{"mode": "explain" | "quiz" | "unclear", "topic": "<string or null>"}`
- Implementation: single LLM call with a strict system prompt + JSON schema (see §5.1). Keep this call small/cheap (low max tokens).
- **Compound requests** (e.g. "samjhao aur quiz bhi le lo"): the parser picks the *first* detected intent. After that intent is fulfilled, the UI prompts for the second (e.g. "Ab quiz shuru karein?").

### 3.3 `content.py` — Content Generation (LLM call #2)
- **Explain mode** → `{"topic": ..., "explanation": "...", "key_points": ["...", "..."]}`
- **Quiz mode** → `{"topic": ..., "questions": [{"question": "...", "options": ["A","B","C","D"], "correct_index": 0, "explanation": "..."}]}`
- Both use Hinglish style guide (§5.2).
- Validate output with Pydantic models:

```python
from pydantic import BaseModel

class ExplainResponse(BaseModel):
    topic: str
    explanation: str
    key_points: list[str]

class QuizQuestion(BaseModel):
    question: str
    options: list[str]       # exactly 4
    correct_index: int       # 0–3
    explanation: str

class QuizResponse(BaseModel):
    topic: str
    questions: list[QuizQuestion]  # 3–5 items
```

### 3.4 `tts.py` — Text-to-Speech
- Input: text string (Hinglish).
- Output: audio bytes (mp3) playable via `st.audio(..., autoplay=True)`.
- Implementation: `edge-tts` with a Hindi neural voice. Cache generated audio per text to avoid re-synthesising on reruns.
- **⚠️ Autoplay caveat:** most browsers block autoplay unless the user has already interacted with the page. Since the teacher taps a mic button first, autoplay usually works — but add a visible "▶ Play" button as a fallback in case it doesn't.

### 3.5 `app.py` — Streamlit UI
- Large "Tap to Speak" recorder at top.
- Status indicator: Listening → Transcribing → Thinking → Speaking.
- Transcript shown for confirmation (teacher trust/empathy requirement).
- Result panel:
  - **Explain mode:** big topic heading, explanation paragraph, bullet key points.
  - **Quiz mode:** one question card at a time (large text, lettered options A–D), "Reveal Answer" and "Next Question" buttons, progress indicator (e.g. "Question 2 of 4").
- Text input fallback (always visible, smaller, below the mic button) for when voice fails.
- Sidebar (collapsible): brief "About this tool" note for evaluators.

## 4. Data Flow (Sequence)

**Explain mode**
1. Teacher taps mic, speaks: *"Photosynthesis ko simple tareeke se samjhao"*
2. `stt.py` → transcript: "photosynthesis ko simple tareeke se samjhao"
3. `intent.py` → `{"mode": "explain", "topic": "photosynthesis"}`
4. `content.py` → explanation JSON
5. UI renders heading + explanation + key points
6. `tts.py` → audio of explanation → autoplay

**Quiz mode**
1. Teacher taps mic, speaks: *"Photosynthesis pe quiz le lo"*
2. `stt.py` → transcript
3. `intent.py` → `{"mode": "quiz", "topic": "photosynthesis"}`
4. `content.py` → list of MCQs
5. UI renders Question 1 card; `tts.py` reads question + options aloud
6. Teacher taps "Reveal Answer" → shows correct option + 1-line explanation (read aloud)
7. "Next Question" cycles through remaining questions

**Unclear/off-topic**
- `intent.py` returns `mode: "unclear"` or topic fails a basic curriculum-relevance check in `content.py` → UI shows/says a short Hinglish clarifying message and resets to listening state.

## 5. Prompt Design

### 5.1 Intent Extraction System Prompt (sketch)

```
You are a classroom assistant's intent parser. The teacher speaks in Hinglish
(mixed Hindi-English, Latin script). Given their transcribed request, output
ONLY a JSON object:
{
  "mode": "explain" | "quiz" | "unclear",
  "topic": "<short topic string in English, or null>"
}
Rules:
- "explain", "samjhao", "batao", "kya hai" → mode "explain"
- "quiz", "test", "sawal", "poochho" → mode "quiz"
- If no clear school-subject topic is present, mode "unclear", topic null.
- Topic should be a normalized English term (e.g. "photosynthesis", "fractions").
Return JSON only, no extra text.
```

### 5.2 Hinglish Style Guide (used in content prompts)

Provide 2–3 worked examples in the system prompt showing the target register, e.g.:
> "Photosynthesis ek process hai jisme plants sunlight, water aur carbon dioxide ka use karke apna food (glucose) banate hain, aur oxygen release karte hain. Isiliye plants ko humara 'natural oxygen factory' bhi kehte hain."

Guidelines to encode in the prompt:
- Target audience: Class 6–8 students (age ~11–14).
- Sentence length: short, 2–4 sentences for explanations.
- Code-mixing: natural Hindi-English mix in Latin script — not pure Hindi (Devanagari) and not pure formal English.
- Tone: friendly, encouraging, classroom-appropriate.
- No fabricated statistics, dates, or "facts" beyond standard textbook knowledge — if unsure, keep it general/conceptual.

### 5.3 Explain Mode Prompt (sketch)

```
System: [role + Hinglish style guide + 2-3 examples]
User: Topic: "{topic}". Generate JSON:
{
  "topic": "{topic}",
  "explanation": "<2-4 sentence Hinglish explanation, Class 6-8 level>",
  "key_points": ["<short point 1>", "<short point 2>", "<short point 3>"]
}
Return JSON only.
```

### 5.4 Quiz Mode Prompt (sketch)

```
System: [role + Hinglish style guide]

Example output for reference:
{
  "topic": "photosynthesis",
  "questions": [
    {
      "question": "Photosynthesis mein plants kya use karte hain?",
      "options": ["Sirf sunlight", "Sunlight, water aur CO2", "Sirf water", "Sirf CO2"],
      "correct_index": 1,
      "explanation": "Plants sunlight, water aur carbon dioxide teeno ka use karke glucose banate hain."
    }
  ]
}

User: Topic: "{topic}". Generate 3–5 multiple-choice questions, JSON:
{
  "topic": "{topic}",
  "questions": [
    {
      "question": "<Hinglish question text>",
      "options": ["A text", "B text", "C text", "D text"],
      "correct_index": 0,
      "explanation": "<1 sentence why this is correct, Hinglish>"
    }
  ]
}
Each question should test understanding of a different aspect of the topic.
Return JSON only.
```

### 5.5 Guardrail Check (lightweight, optional)
Before generating content, a simple keyword/topic-relevance check (or a single cheap LLM classification: "is this a school-curriculum topic for Classes 6-8? yes/no") can short-circuit clearly off-topic requests with a friendly redirect message, without needing a full RAG layer.

## 6. Folder Structure

```
smartshala-ai-teaching-assistant/
├── app.py                  # Streamlit UI & orchestration
├── config.py               # Centralised config (env vars, defaults, startup validation)
├── stt.py                  # Speech-to-text (faster-whisper / Whisper API)
├── intent.py               # Intent/topic extraction (LLM call #1)
├── content.py              # Explanation/quiz generation (LLM call #2)
├── tts.py                  # Text-to-speech
├── llm.py                  # Thin LLM client wrapper (provider-agnostic)
├── models.py               # Pydantic response models (ExplainResponse, QuizResponse)
├── prompts/
│   ├── intent_system.txt
│   ├── explain_system.txt
│   └── quiz_system.txt
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── PRD.md
├── TECH.md
├── TASKS.md
└── AGENTS.md
```

## 7. Configuration / Environment Variables

```
GEMINI_API_KEY=your_key_here     # or OPENAI_API_KEY / ANTHROPIC_API_KEY
LLM_PROVIDER=gemini               # gemini | openai | anthropic
WHISPER_MODEL_SIZE=small          # tiny | base | small (faster-whisper)
TTS_VOICE=hi-IN-MadhurNeural       # edge-tts voice name
```

## 8. Deployment Plan

1. Push repo to GitHub (public).
2. Deploy via **Streamlit Community Cloud**: connect repo, set `app.py` as entrypoint, add secrets (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `STT_BACKEND=whisper_api`, etc.) in the dashboard's "Secrets" UI (never commit `.env`).
3. **STT strategy on cloud:** set `STT_BACKEND=whisper_api` in cloud secrets. `faster-whisper` requires C++ libraries (`ctranslate2`) and downloads ~500MB+ model weights at runtime — this is unreliable or impossible on Streamlit Community Cloud's limited environment. The OpenAI Whisper API is the recommended cloud STT backend.
4. If other cloud-environment issues arise, fall back to **Hugging Face Spaces (Streamlit SDK)**, which gives more control over the underlying environment via `packages.txt`/`requirements.txt`.
5. Verify the live URL works end-to-end (mic permissions require HTTPS — both platforms provide this by default).
6. Test TTS autoplay behaviour on the deployed URL — if blocked by the browser, the manual "Play" button fallback should work.

## 9. Guardrails & Error Handling

- Wrap every external call (STT, LLM, TTS) in try/except; show a friendly Hinglish error message (e.g. "Kuch gadbad ho gayi, dobara try karein") and a retry button — never show raw exceptions in the UI.
- Validate LLM JSON output (e.g. with `pydantic` or manual schema checks); if parsing fails, retry once with a stricter "return valid JSON only" reminder before falling back to an error message.
- Cap LLM `max_tokens` to keep responses concise and within latency targets.
- Log errors to console/file for debugging, but keep the UI clean.

## 10. Latency Budget (target ≤ 6–8s end-to-end)

| Step | Target |
|---|---|
| STT (faster-whisper, `small`, short clip) | ~1–2s |
| Intent extraction (LLM call #1, small prompt) | ~0.5–1s |
| Content generation (LLM call #2) | ~1.5–3s |
| TTS synthesis (edge-tts) | ~0.5–1.5s |

If totals run high, consider: smaller Whisper model, or combining intent+content into a single LLM call. A combined prompt sketch:

```
System: [role + Hinglish style guide]
User: Transcript: "{transcript}"
Determine if this is an explain or quiz request. Then generate content.
Return JSON:
{
  "mode": "explain" | "quiz" | "unclear",
  "topic": "<topic or null>",
  "content": { ... explain or quiz payload, or null if unclear ... }
}
```
Trade-off: saves one LLM round-trip (~0.5–1s) but the prompt is larger and less modular. Only use this if latency is consistently above the 8s target.

## 11. Testing Plan

- **Unit-level (manual or quick scripts):** feed sample Hinglish transcripts to `intent.py` and `content.py`, verify JSON shape and Hinglish tone.
- **Pipeline test:** record sample audio clips (a few topics, a few "quiz" requests, one off-topic request) and run through the full pipeline.
- **UI/UX pass:** view the app at a "smart board" distance (zoom out / project on a TV) — check font sizes, contrast, and that the listening/thinking/speaking states are obvious.
- **Edge cases:** silence/no speech, very long request, ambiguous topic, off-topic request (e.g. "tell me a joke").

## 12. Stretch Goals (Out of Scope for MVP)

If time permits after the core loop is solid:
- **Bilingual Dictation & Translation** — reuses STT + LLM translation prompt + side-by-side display.
- **Hands-Free Activity Guide** — reuses voice command parsing + adds an on-screen timer component (Streamlit `st.empty()` + loop, or `streamlit-autorefresh`).

Document these as "Future Work" in the README even if not implemented — shows awareness of the full brief.

## 13. Alternatives Considered

- **React/Next.js + Web Speech API**: viable if you prefer a JS/TS stack (matches typical full-stack experience) and want a more polished UI. Trade-off: more setup time for audio handling and deployment compared to Streamlit; Web Speech API's `hi-IN` recognition quality varies by browser. If choosing this route, mirror the same module boundaries (`stt`, `intent`, `content`, `tts` as API routes or hooks) and update this document accordingly.
