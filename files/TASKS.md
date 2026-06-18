# TASKS.md — Build Plan (13–20 June 2026)

Use this as the working checklist inside Antigravity. Each day has a goal, concrete tasks, and a "definition of done" so the agent (and you) can verify progress before moving on. Read `PRD.md` and `TECH.md` before starting Day 1.

---

## Day 1 (Sat 13 June) — Project Skeleton & Setup
**Goal:** A running (empty-ish) Streamlit app with API access confirmed.

- [ ] Initialize git repo, create folder structure from `TECH.md` §6
- [ ] Create `requirements.txt`, `.env.example`, `.gitignore`
- [ ] Set up virtual environment, install dependencies
- [ ] Obtain LLM API key (Gemini/OpenAI/Anthropic) and confirm a basic test call works
- [ ] Build minimal `app.py`: title, sidebar "About" text, placeholder layout for mic button + result panel
- [ ] Push initial commit to a public GitHub repo

**Done when:** `streamlit run app.py` shows a basic page locally; one successful test call to the LLM API logged in console.

---

## Day 2 (Sun 14 June) — Audio Capture & STT Foundation
**Goal:** Voice in → transcript shown on screen (stub or real).

- [ ] Add `st.audio_input` mic recorder to `app.py`
- [ ] Implement `config.py` — centralise all env-var reads, validate required keys at startup (fail fast)
- [ ] Implement `stt.py` with `STT_BACKEND` toggle:
  - `faster_whisper`: integrate faster-whisper with `base` or `small` model (local dev)
  - `whisper_api`: stub for OpenAI Whisper API (fill in Day 7 for deployment)
- [ ] Display the transcript on screen after recording
- [ ] Add a text-input fallback field for typed requests
- [ ] Test with 2–3 Hinglish phrases; note any accuracy issues

**Done when:** Recording your voice and seeing a transcript on screen works reliably. Text fallback also works.

---

## Day 3 (Mon 15 June) — Intent Extraction + LLM Wrapper
**Goal:** Transcript → structured `{mode, topic}`.

- [ ] Implement `llm.py` (provider-agnostic wrapper around chosen LLM API, JSON-mode helper)
- [ ] Implement `models.py` — Pydantic models for `ExplainResponse`, `QuizResponse` (see `TECH.md` §3.3)
- [ ] Write `prompts/intent_system.txt` per `TECH.md` §5.1
- [ ] Implement `intent.py`, call LLM, parse JSON, handle parse failures (retry once)
- [ ] Manually test with: "photosynthesis ko samjhao", "fractions pe quiz lo", "tell me a joke" (should be `unclear`), "samjhao aur quiz bhi le lo" (compound — should pick first intent)

**Done when:** All four test phrases above return the expected `mode`/`topic` (or `unclear`/first-intent for compound).

---

## Day 4 (Tue 16 June) — Content Generation (Explain + Quiz)
**Goal:** Topic → Hinglish explanation JSON and quiz JSON.

- [ ] Write `prompts/explain_system.txt` and `prompts/quiz_system.txt` per `TECH.md` §5.2–5.4 (include 2–3 Hinglish style examples)
- [ ] Implement `content.py` with `generate_explanation(topic)` and `generate_quiz(topic)`
- [ ] Render explain-mode result in `app.py`: heading, explanation paragraph, key points list
- [ ] Render quiz-mode result: one-question-at-a-time cards with options, "Reveal Answer"/"Next" buttons, progress indicator
- [ ] Test end-to-end (voice → transcript → intent → content → display) for both modes on 2–3 topics each

**Done when:** Saying "explain X" and "quiz me on X" both produce sensible Hinglish output displayed clearly, for at least 3 different school subjects/topics.

---

## Day 5 (Wed 17 June) — Text-to-Speech + Smart-Board UI Polish
**Goal:** Output is read aloud; UI looks good from a distance.

- [ ] Implement `tts.py` using `edge-tts` (try `hi-IN-MadhurNeural` / `hi-IN-SwaraNeural`, pick whichever sounds more natural for Hinglish)
- [ ] Wire up autoplay audio for explanations and quiz questions/options
- [ ] Add "Listening / Thinking / Speaking" status indicator
- [ ] Increase font sizes, improve contrast, simplify layout for "smart board" viewing (test by zooming out or viewing on a TV/projector if possible)
- [ ] Cache TTS audio per text to avoid redundant synthesis

**Done when:** The full loop (tap mic → speak → see + hear result) feels smooth, and the UI is legible from across a room.

---

## Day 6 (Thu 18 June) — Guardrails, Error Handling, Testing Pass
**Goal:** The app degrades gracefully and stays on-topic.

- [ ] Add curriculum-relevance check (lightweight LLM classification or keyword heuristic) per `TECH.md` §5.5; off-topic → friendly Hinglish redirect message (spoken + shown)
- [ ] Wrap STT/LLM/TTS calls in try/except with friendly error messages + retry option
- [ ] Test edge cases: silence, very short/garbled audio, ambiguous topic, off-topic request, very long request
- [ ] Tune Hinglish prompts based on what you've seen so far (tone, length, code-mixing balance)
- [ ] Code cleanup: remove dead code, add docstrings/comments, ensure `requirements.txt` is accurate

**Done when:** No raw errors/crashes appear in the UI for any tested edge case; off-topic requests are handled gracefully.

---

## Day 7 (Fri 19 June) — Deployment + Documentation
**Goal:** Live URL working; repo presentable.

- [ ] Deploy to Streamlit Community Cloud (or Hugging Face Spaces if issues arise) — see `TECH.md` §8
- [ ] Add API keys as platform secrets (never commit `.env`)
- [ ] Test the **live deployed URL** end-to-end (mic permissions, latency, audio playback)
- [ ] Finish `README.md`: setup instructions, tech stack, prompt design summary, localization approach, link to live demo
- [ ] Add screenshots to README (explain mode + quiz mode)
- [ ] Final commit + tag (e.g. `v1.0`)

**Done when:** Live URL works in a fresh browser/incognito window; README is complete and accurate.

---

## Day 8 (Sat 20 June) — Video Walkthrough + Submission
**Goal:** Submit on time.

- [ ] Script a short walkthrough (≤3 min): problem framing (10–15s), demo of explain mode, demo of quiz mode, brief mention of architecture/guardrails, closing
- [ ] Record screen + voice (e.g. OBS, Loom)
- [ ] Upload video (YouTube unlisted / Google Drive link) and add link to README
- [ ] Final sanity check: live URL, GitHub repo (public), README, video link all working
- [ ] Submit via the application form with subject line: `FullName | AI Assignment`

**Done when:** All 4 deliverables (Live URL · Public GitHub repo · README · Video) are ready and submission sent before the deadline.

---

## If You're Ahead of Schedule
Pick up a stretch goal from `TECH.md` §12 (Bilingual Dictation & Translation, or Hands-Free Activity Guide) — but only after Days 1–7's core loop is fully working and polished. A smaller, more reliable demo beats a larger, flakier one.
