# PRD — SmartShala: Voice-Enabled AI Teaching Assistant

**Project codename:** SmartShala
**Assignment:** Connecting Dreams Foundation, Round 2 — Option A
**Deadline:** 20 June 2026
**Evaluation weighting:** Technical 40% · Empathy/UX 30% · AI/Prompt 30%

---

## 1. Background

Connecting Dreams Foundation (CDF) works on grassroots leadership development and human-centred design with youth, micro-entrepreneurs, community organisations and government bodies. This brief asks for a prototype AI co-pilot for a teacher in a Haryana government school, to be used live during class on a classroom smart board, where students speak a mix of Hindi and English ("Hinglish").

The deliverable is a **functional proof of concept**, not a production product — but it must clearly demonstrate technical competence, empathy for the end user (a working teacher with no technical training), and thoughtful AI/prompt design.

## 2. Problem Statement

A government school teacher in Haryana needs a **hands-free** assistant they can talk to during a live lesson. The assistant should listen for spoken requests, respond in a way that's natural for Hinglish-speaking students, and display supporting visuals on the smart board — without the teacher needing to touch a keyboard or mouse mid-lesson.

## 3. Goals & Success Criteria

| Goal | How it's demonstrated |
|---|---|
| **Technical (40%)** | Working end-to-end voice pipeline (speech in → AI processing → speech + visual out), deployed to a live URL, clean repo |
| **Empathy / UX (30%)** | Interface usable from across a classroom (large text, high contrast), minimal interaction steps, teacher-friendly language, graceful handling of noisy/ambiguous input |
| **AI / Prompt (30%)** | Reliable Hinglish output, age-appropriate simplification, consistent structured output for quizzes, sensible guardrails on scope |

## 4. Target User & Persona

**Mrs. Sunita Devi**, 38, teaches Science to Classes 6–8 in a government secondary school in Haryana. Her classroom has a shared smart board. She is comfortable with basic tech (WhatsApp, YouTube) but not with typing long prompts or managing software. During a lesson she wants to:
- Quickly get a simple explanation of a concept a student is struggling with, in the mixed Hindi-English her students actually speak.
- Run a quick verbal quiz to check understanding without stopping to write questions on the board.

## 5. Selected Requirements (Choose 2 of 4)

We are building:

1. **Live Concept Simplification** — teacher asks (by voice) for a topic to be explained simply; the assistant gives a short Hinglish explanation with a supporting visual on screen.
2. **Voice-Triggered Quizzing** — teacher asks (by voice) for a quiz on a topic; the assistant announces questions verbally and displays them with options on screen.

**Why these two:** both features share one core pipeline — *voice input → topic/intent extraction → LLM generates Hinglish content → render on screen → read aloud via TTS*. Building one robust pipeline that serves both features maximises the chance of a polished, working demo within the timeline, rather than splitting effort across unrelated subsystems. They also form a natural classroom loop: **explain → check understanding**.

*(Bilingual Dictation/Translation and Hands-Free Activity Guide are noted as stretch goals — see TECH.md §12.)*

## 6. Scope

### In scope
- Voice input (microphone) for teacher commands
- Intent detection: "explain X" vs "quiz me on X" (vs unclear → ask for clarification)
- LLM-generated Hinglish explanations (2–4 sentences, age-appropriate for Classes 6–8)
- LLM-generated quiz questions (MCQ, 3–5 questions per topic) with answer key
- On-screen display optimised for a large/projected screen (big fonts, high contrast, minimal clutter)
- Text-to-speech playback of explanations and quiz questions in Hindi/Hinglish-friendly voice
- Basic topic guardrails (keep content to school-curriculum subjects; politely decline off-topic/inappropriate requests)
- Deployed live demo (Streamlit Community Cloud or Hugging Face Spaces)

### Out of scope (for this round)
- User accounts / multi-teacher profiles
- Persistent lesson history / analytics dashboards
- Real smart-board hardware integration (we simulate "smart board" as a large browser display)
- Multi-language support beyond Hindi/English/Hinglish
- Bilingual dictation & translation, hands-free activity guide (documented as future work)

## 7. User Stories

- *As a teacher*, I press a single "listen" button, say "Iske baare mein simple tareeke se samjhao — photosynthesis", and within a few seconds I see a short Hinglish explanation on screen and hear it read aloud, so I can keep teaching without breaking flow.
- *As a teacher*, I say "Photosynthesis pe quiz le lo", and the assistant displays 3–5 multiple-choice questions one at a time, reads each one aloud, and shows the correct answer after a short pause/on request.
- *As a teacher*, if my request is unclear or off-topic, the assistant asks a short clarifying question instead of guessing or giving an unrelated answer.

## 8. Functional Requirements

### 8.1 Voice Input
- A clearly labelled "Tap to speak" control (large, smart-board friendly).
- Records audio, transcribes to text (Hindi/English/Hinglish supported).
- Shows the transcribed text on screen so the teacher can confirm what was heard.

### 8.2 Intent & Topic Extraction
- Classify the transcribed request into: `explain`, `quiz`, or `unclear`.
- Extract the subject/topic (e.g., "photosynthesis", "fractions", "the water cycle").
- If `unclear` or topic missing, respond with a short spoken+visual clarifying prompt (e.g., "Kis topic par?").

### 8.3 Concept Simplification ("explain" mode)
- Generate a 2–4 sentence Hinglish explanation suitable for Classes 6–8.
- Generate a short list (2–4) of key points / an analogy for the visual display.
- Display: large heading (topic), short explanation text, bullet key points.
- Read the explanation aloud via TTS.

### 8.4 Voice-Triggered Quiz ("quiz" mode)
- Generate 3–5 MCQs on the topic (question, 4 options, correct answer index, 1-line explanation).
- Display one question at a time with large text and option buttons/labels.
- Read the question and options aloud.
- After a configurable pause (or teacher tap), reveal the correct answer and brief explanation.
- Provide simple navigation (Next question / Repeat).
- If the teacher makes a compound request (e.g. "samjhao aur quiz bhi le lo"), pick the first intent and prompt for the second afterwards (e.g. "Ab quiz shuru karein?").

### 8.5 Display / "Smart Board" Mode
- Layout designed for viewing from a distance: large font sizes (≥28px body, ≥48px headings), high-contrast colour scheme, minimal text density.
- Dark background (e.g. `#1a1a2e`) to reduce eye strain in varied classroom lighting; light text (`#e0e0e0` / white).
- Single bright accent colour for interactive elements (mic button, quiz options).
- Single-column, centred layout — no visible sidebar during active use.
- Clear visual indicator when the assistant is listening (pulse/glow on mic) / thinking (spinner) / speaking (speaker icon).

### 8.6 Guardrails
- If requested topic is clearly outside school curriculum or inappropriate, respond with a polite redirect ("Yeh topic class ke liye nahi hai, kisi padhai wale topic ke baare mein puchiye").
- Keep explanations factually conservative — avoid invented statistics or unverifiable claims; favour well-established textbook-level facts.

## 9. Non-Functional Requirements

- **Latency:** end-to-end response (speech in → first visual/audio out) target ≤ 6–8 seconds on a typical connection.
- **Language:** natural Hinglish (code-mixed Hindi-English in Latin script), matching how teachers/students actually speak — not pure formal Hindi or pure English.
- **Accessibility:** usable without a keyboard during live use; large, legible UI.
- **Reliability:** if STT, LLM, or TTS calls fail, show a friendly error and allow retry — never a raw stack trace.
- **Cost:** prefer free-tier APIs / local models suitable for a student project demo.

## 10. Deliverables (per CDF brief)

- [ ] Live URL (deployed app)
- [ ] Public GitHub repository
- [ ] README covering tech stack, prompt design, and localisation approach
- [ ] Video walkthrough (max 3 minutes)

## 11. Suggested Timeline (13–20 June 2026)

See `TASKS.md` for the day-by-day breakdown.

## 12. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Hindi/Hinglish STT accuracy is unreliable | Show transcript for confirmation; allow text-input fallback |
| LLM output drifts into pure Hindi/English instead of Hinglish | Use explicit style examples in the system prompt; post-check/regenerate if needed |
| TTS voice doesn't handle Hinglish well | Use a Hindi neural voice (handles code-mixed text reasonably); test early |
| Running out of time before deadline | Lock scope to the 2 chosen requirements only; treat everything else as stretch |
| API rate limits / costs | Use free-tier models (Gemini/OpenAI free tier) with local fallbacks (faster-whisper, edge-tts) |

## 13. Open Questions for the Builder

- Which LLM provider do you have an API key for (Gemini, OpenAI, Anthropic)? TECH.md defaults to Gemini but is provider-agnostic.
- Any preference for hosting (Streamlit Community Cloud vs Hugging Face Spaces vs Vercel)?
