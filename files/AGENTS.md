# AGENTS.md — Instructions for AI Agents Working on This Project

This file gives any AI coding agent (Antigravity, etc.) the context and conventions needed to work on this project effectively. Read this first, then `PRD.md`, `TECH.md`, and `TASKS.md`.

## Project Context

This is a 7-day prototype for the Connecting Dreams Foundation Round 2 assignment: a **voice-enabled AI teaching assistant** for a government school teacher, optimised for use on a classroom smart board. Full requirements are in `PRD.md`; architecture and prompt design are in `TECH.md`; the day-by-day plan is in `TASKS.md`.

**This is a prototype/demo, not production software.** Prioritise a working, polished end-to-end loop over completeness, extra features, or robustness beyond what's needed for a live demo.

## Working Conventions

1. **Follow `TASKS.md` in order.** Don't jump ahead to later days' work until the current day's "Done when" condition is met. If a task seems irrelevant or already done, say so explicitly rather than skipping silently.
2. **Stay in scope.** The selected requirements are *Live Concept Simplification* + *Voice-Triggered Quizzing* only (see `PRD.md` §5/§6). Don't build the other two requirements (Bilingual Dictation/Translation, Hands-Free Activity Guide) unless `TASKS.md`'s "If You're Ahead of Schedule" section is reached.
3. **Keep the module boundaries from `TECH.md` §2–6** (`stt.py`, `intent.py`, `content.py`, `tts.py`, `llm.py`, `app.py`). This keeps the provider-agnostic design intact and makes it easy to swap APIs.
4. **Never hardcode API keys.** Always read from environment variables via `python-dotenv`, and keep `.env` out of git (already in `.gitignore`). Update `.env.example` if you add new config variables.
5. **Validate LLM JSON output.** Any LLM call that's supposed to return JSON should be parsed defensively (try/except, retry once on failure, then fall back to a friendly error — see `TECH.md` §9).
6. **Test after every meaningful change.** Run `streamlit run app.py` and walk through the relevant flow (explain mode, quiz mode, or both) before considering a task done.
7. **Hinglish quality matters.** When writing or editing prompts in `prompts/*.txt`, follow the style guide in `TECH.md` §5.2 — natural code-mixed Hindi-English in Latin script, short sentences, Class 6–8 reading level. If output sounds too formal/pure-Hindi or too pure-English, revise the prompt examples.
8. **UI must be "smart board" usable.** Large fonts, high contrast, minimal clutter, clear listening/thinking/speaking states. If unsure, err toward bigger and simpler.
9. **If you hit a blocker** (e.g., an API key isn't available, a library fails to install in this environment), don't silently substitute a completely different architecture — flag it clearly, propose the smallest viable workaround consistent with `TECH.md`, and note it in a `NOTES.md` file at the project root for the human to review. (This file is gitignored — it's a scratch pad, not a deliverable.)
10. **Commit messages** should be short and descriptive (e.g., `feat: add quiz mode content generation`, `fix: handle empty STT transcript`).

## Definition of "Done" for the Project

All four items below are required (per `PRD.md` §10):
- [ ] Live URL (deployed, working in a fresh browser session)
- [ ] Public GitHub repository
- [ ] README with tech stack, prompt design, and localisation notes
- [ ] Video walkthrough (≤3 minutes)

## Things NOT to Do

- Don't add user authentication, databases, or persistent storage — out of scope (`PRD.md` §6).
- Don't switch the core stack (Streamlit) mid-project without flagging it — see `TECH.md` §13 for the documented alternative and what changing it would involve.
- Don't remove the text-input fallback or the visible transcript — both are deliberate empathy/UX choices for a non-technical teacher user (`PRD.md` §4, §8.1).
- Don't add content/topics beyond standard school curriculum subjects, and don't let the assistant fabricate facts/statistics — keep explanations conceptual and textbook-level (`PRD.md` §8.6, `TECH.md` §5.2).
