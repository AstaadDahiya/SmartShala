"""
app.py — SmartShala: Streamlit UI & Orchestration.

Voice-enabled AI teaching assistant for classroom smart boards.
Supports two modes:
  🎤 → "samjhao" → Hinglish concept explanation displayed + read aloud
  🎤 → "quiz lo" → MCQ quiz displayed one question at a time + read aloud

Designed for large-screen / smart-board viewing: dark theme, large fonts,
high contrast, minimal clutter. Product-grade UI for school deployment.
"""

import hashlib
import logging

import streamlit as st

from config import Config
from stt import transcribe
from intent import extract_intent
from content import generate_explanation, generate_quiz, check_curriculum_relevance
from tts import speak

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("smartshala")


# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SmartShala — AI Teaching Assistant",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Custom CSS — Professional School Product Design
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ── Google Fonts ──────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root Variables — Professional Light Theme ─────────────── */
:root {
    --primary: #1a56db;
    --primary-light: #eff6ff;
    --primary-border: #bfdbfe;
    --primary-hover: #1e40af;

    --success: #059669;
    --success-light: #ecfdf5;
    --success-border: #a7f3d0;

    --warning: #d97706;
    --warning-light: #fffbeb;
    --warning-border: #fde68a;

    --error: #dc2626;
    --error-light: #fef2f2;
    --error-border: #fecaca;

    --gray-900: #111827;
    --gray-700: #374151;
    --gray-500: #6b7280;
    --gray-400: #9ca3af;
    --gray-300: #d1d5db;
    --gray-200: #e5e7eb;
    --gray-100: #f3f4f6;
    --gray-50: #f9fafb;
    --white: #ffffff;

    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    --shadow-lg: 0 10px 25px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);

    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --radius-xl: 20px;
    --radius-full: 9999px;
}

/* ── Base ──────────────────────────────────────────────────── */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background: var(--white) !important;
}

/* ── Single subtle animation ──────────────────────────────── */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── Header / Brand ────────────────────────────────────────── */
.brand-container {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    animation: fadeIn 0.4s ease-out;
}
.brand-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    display: block;
}
.brand-title {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: var(--gray-900);
    margin: 0;
    line-height: 1.1;
}
.brand-tagline {
    font-size: 1rem;
    color: var(--gray-500);
    font-weight: 400;
    margin-top: 0.4rem;
    letter-spacing: 0.2px;
}
.brand-divider {
    width: 48px;
    height: 3px;
    background: var(--primary);
    border-radius: var(--radius-full);
    margin: 1.25rem auto 0;
}

/* ── Class Badges ──────────────────────────────────────────── */
.class-badges {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 1.25rem;
    flex-wrap: wrap;
}
.class-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: var(--radius-full);
    font-size: 0.78rem;
    font-weight: 500;
    background: var(--primary-light);
    color: var(--primary);
    border: 1px solid var(--primary-border);
    transition: background 0.15s ease;
}
.class-badge:hover {
    background: #dbeafe;
}

/* ── Status Indicator ──────────────────────────────────────── */
.status-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 8px 20px;
    border-radius: var(--radius-full);
    font-size: 0.88rem;
    font-weight: 500;
    margin: 1rem auto 0;
    width: fit-content;
}
.status-ready {
    background: var(--success-light);
    color: var(--success);
    border: 1px solid var(--success-border);
}
.status-working {
    background: var(--warning-light);
    color: var(--warning);
    border: 1px solid var(--warning-border);
}
.status-error {
    background: var(--error-light);
    color: var(--error);
    border: 1px solid var(--error-border);
}
.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
}
.status-dot-ready { background: var(--success); }
.status-dot-working { background: var(--warning); }
.status-dot-error { background: var(--error); }

/* ── Voice Input Section ───────────────────────────────────── */
.voice-section {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
.voice-label {
    font-size: 1rem;
    color: var(--gray-700);
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.voice-hint {
    font-size: 0.82rem;
    color: var(--gray-400);
    margin-top: 0.35rem;
}

/* ── Section Divider ───────────────────────────────────────── */
.section-divider {
    border: none;
    height: 1px;
    background: var(--gray-200);
    margin: 1.5rem 0;
}

/* ── Text Input Section ────────────────────────────────────── */
.text-input-section {
    animation: fadeIn 0.4s ease-out 0.1s both;
}
.text-input-label {
    font-size: 0.8rem;
    color: var(--gray-500);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}

/* ── Transcript Display ────────────────────────────────────── */
.transcript-card {
    background: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-left: 3px solid var(--primary);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    animation: fadeIn 0.3s ease-out;
}
.transcript-label {
    font-size: 0.72rem;
    color: var(--gray-400);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-bottom: 0.35rem;
}
.transcript-text {
    font-size: 1.05rem;
    color: var(--gray-700);
    font-style: italic;
    line-height: 1.6;
}

/* ── Content Cards (Shared) ────────────────────────────────── */
.content-card {
    background: var(--white);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-xl);
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: var(--shadow-lg);
    animation: fadeIn 0.4s ease-out;
    position: relative;
    overflow: hidden;
}
.content-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--primary);
}

/* ── Explain Mode ──────────────────────────────────────────── */
.explain-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 1.5rem;
}
.explain-icon {
    font-size: 1.6rem;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--primary-light);
    border-radius: var(--radius-lg);
    border: 1px solid var(--primary-border);
    flex-shrink: 0;
}
.explain-topic {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--gray-900);
    line-height: 1.2;
    letter-spacing: -0.3px;
}
.explain-body {
    font-size: 1.15rem;
    line-height: 1.85;
    color: var(--gray-700);
    margin-bottom: 1.5rem;
    padding: 0;
}
.key-points-header {
    font-size: 0.72rem;
    color: var(--gray-400);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 700;
    margin-bottom: 0.75rem;
}
.key-point-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    background: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-md);
    transition: background 0.15s ease;
}
.key-point-item:hover {
    background: var(--primary-light);
    border-color: var(--primary-border);
}
.key-point-num {
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--primary);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
    margin-top: 1px;
}
.key-point-text {
    font-size: 1.02rem;
    color: var(--gray-700);
    line-height: 1.55;
}

/* ── Quiz Mode ─────────────────────────────────────────────── */
.quiz-header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 8px;
}
.quiz-topic-label {
    font-size: 0.75rem;
    color: var(--gray-400);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 700;
}
.quiz-progress-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: var(--radius-full);
    font-size: 0.78rem;
    font-weight: 600;
    background: var(--primary-light);
    color: var(--primary);
    border: 1px solid var(--primary-border);
}
.quiz-question-text {
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--gray-900);
    line-height: 1.5;
    margin: 1rem 0 1.25rem;
}
.quiz-option {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0.9rem 1.15rem;
    margin-bottom: 0.5rem;
    background: var(--white);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-md);
    transition: all 0.15s ease;
    cursor: default;
}
.quiz-option:hover {
    background: var(--gray-50);
    border-color: var(--gray-300);
}
.quiz-option-label {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    font-weight: 600;
    background: var(--gray-100);
    color: var(--gray-500);
    border: 1px solid var(--gray-200);
    flex-shrink: 0;
}
.quiz-option-text {
    font-size: 1.08rem;
    color: var(--gray-700);
    line-height: 1.45;
}
.quiz-option-correct {
    background: var(--success-light) !important;
    border-color: var(--success-border) !important;
}
.quiz-option-correct .quiz-option-label {
    background: var(--success) !important;
    color: white !important;
    border-color: var(--success) !important;
}
.quiz-option-correct .quiz-option-text {
    color: var(--success) !important;
    font-weight: 600;
}
.quiz-option-wrong {
    opacity: 0.35;
}
.quiz-answer-card {
    background: var(--success-light);
    border: 1px solid var(--success-border);
    border-radius: var(--radius-md);
    padding: 1.15rem 1.35rem;
    margin-top: 1rem;
    animation: fadeIn 0.3s ease-out;
}
.quiz-answer-label {
    font-size: 0.72rem;
    color: var(--success);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.quiz-answer-text {
    font-size: 1.08rem;
    color: var(--success);
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.quiz-explanation-text {
    font-size: 0.98rem;
    color: var(--gray-700);
    line-height: 1.6;
}

/* ── Info / Warning / Error Cards ──────────────────────────── */
.info-card {
    text-align: center;
    padding: 1.5rem 2rem;
    border-radius: var(--radius-md);
    margin: 1rem 0;
    animation: fadeIn 0.3s ease-out;
}
.info-card-clarify {
    background: var(--warning-light);
    border: 1px solid var(--warning-border);
    color: var(--warning);
}
.info-card-error {
    background: var(--error-light);
    border: 1px solid var(--error-border);
    color: var(--error);
}
.info-card-offtopic {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    color: #c2410c;
}
.info-card-icon {
    font-size: 1.75rem;
    display: block;
    margin-bottom: 0.4rem;
}
.info-card-title {
    font-size: 1.08rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
}
.info-card-body {
    font-size: 0.95rem;
    opacity: 0.85;
    line-height: 1.5;
}

/* ── Audio Player Section ──────────────────────────────────── */
.audio-section {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.75rem 1.15rem;
    background: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-md);
    margin: 1rem 0;
}
.audio-icon {
    font-size: 1.3rem;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--primary-light);
    border-radius: var(--radius-sm);
    flex-shrink: 0;
}

/* ── Buttons ───────────────────────────────────────────────── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    border-radius: var(--radius-md) !important;
    padding: 0.55rem 1.25rem !important;
    transition: all 0.15s ease !important;
    border: 1px solid var(--gray-200) !important;
    background: var(--white) !important;
    color: var(--gray-700) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
    background: var(--gray-50) !important;
    border-color: var(--gray-300) !important;
    box-shadow: var(--shadow-md) !important;
}
.stButton > button[kind="primary"] {
    background: var(--primary) !important;
    border: 1px solid var(--primary) !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-hover) !important;
    border-color: var(--primary-hover) !important;
    box-shadow: var(--shadow-md) !important;
}

/* ── New Question / CTA Button ─────────────────────────────── */
.cta-section {
    text-align: center;
    padding: 0.5rem 0;
}

/* ── Progress Bar ──────────────────────────────────────────── */
.stProgress > div > div > div {
    background: var(--primary) !important;
    border-radius: var(--radius-full) !important;
}
.stProgress > div > div {
    background: var(--gray-100) !important;
    border-radius: var(--radius-full) !important;
}

/* ── Streamlit Overrides ───────────────────────────────────── */
.stTextInput > div > div > input {
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--gray-300) !important;
    background: var(--white) !important;
    color: var(--gray-900) !important;
    padding: 0.65rem 0.9rem !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.1) !important;
}
.stTextInput label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    color: var(--gray-500) !important;
    font-weight: 500 !important;
}

/* Override containers */
div[data-testid="stVerticalBlock"] > div[data-testid="stExpander"],
div.stContainer {
    border-color: var(--gray-200) !important;
}

/* ── Sidebar ───────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--gray-50) !important;
    border-right: 1px solid var(--gray-200) !important;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: var(--gray-900) !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    font-size: 0.88rem !important;
    color: var(--gray-500) !important;
}

/* ── Feature Cards (Sidebar) ──────────────────────────────── */
.feature-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.7rem 0.85rem;
    border-radius: var(--radius-md);
    background: var(--white);
    border: 1px solid var(--gray-200);
    margin-bottom: 0.5rem;
    box-shadow: var(--shadow-sm);
}
.feature-icon {
    font-size: 1.2rem;
    flex-shrink: 0;
    margin-top: 1px;
}
.feature-text {
    font-size: 0.82rem;
    color: var(--gray-500);
    line-height: 1.45;
}
.feature-text strong {
    color: var(--gray-900);
    font-weight: 600;
}

/* ── Footer ────────────────────────────────────────────────── */
.app-footer {
    text-align: center;
    padding: 2rem 1rem 1rem;
    margin-top: 2rem;
    border-top: 1px solid var(--gray-100);
}
.footer-brand {
    font-size: 0.78rem;
    color: var(--gray-400);
    letter-spacing: 0.3px;
}
.footer-tagline {
    font-size: 0.68rem;
    color: var(--gray-300);
    margin-top: 0.2rem;
}

/* ── Hide Streamlit Defaults ───────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* ── Audio Input Styling ───────────────────────────────────── */
.stAudioInput > label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: var(--gray-500) !important;
}

/* ── Responsive for Smart Boards ───────────────────────────── */
@media (min-width: 1200px) {
    .brand-title { font-size: 2.8rem; }
    .explain-topic { font-size: 2rem; }
    .explain-body { font-size: 1.25rem; }
    .quiz-question-text { font-size: 1.55rem; }
    .quiz-option-text { font-size: 1.15rem; }
    .key-point-text { font-size: 1.1rem; }
}

/* ── Dark Mode Overrides ───────────────────────────────────── */
body.dark-mode .stApp {
    background: #0f172a !important;
}
body.dark-mode {
    --primary: #6366f1;
    --primary-light: rgba(99, 102, 241, 0.1);
    --primary-border: rgba(99, 102, 241, 0.25);
    --primary-hover: #818cf8;

    --success: #34d399;
    --success-light: rgba(52, 211, 153, 0.08);
    --success-border: rgba(52, 211, 153, 0.2);

    --warning: #fbbf24;
    --warning-light: rgba(251, 191, 36, 0.08);
    --warning-border: rgba(251, 191, 36, 0.2);

    --error: #f87171;
    --error-light: rgba(248, 113, 113, 0.08);
    --error-border: rgba(248, 113, 113, 0.2);

    --gray-900: #f1f5f9;
    --gray-700: #cbd5e1;
    --gray-500: #94a3b8;
    --gray-400: #64748b;
    --gray-300: #334155;
    --gray-200: #1e293b;
    --gray-100: #1e293b;
    --gray-50: #0f172a;
    --white: #0f172a;

    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 10px 25px -3px rgba(0, 0, 0, 0.5);
}
body.dark-mode .content-card {
    background: #1e293b !important;
    border-color: #334155 !important;
}
body.dark-mode .content-card::before {
    background: #6366f1;
}
body.dark-mode .quiz-option {
    background: #1e293b !important;
    border-color: #334155 !important;
}
body.dark-mode .quiz-option:hover {
    background: #283548 !important;
    border-color: #475569 !important;
}
body.dark-mode .stTextInput > div > div > input {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #f1f5f9 !important;
}
body.dark-mode .stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}
body.dark-mode .stButton > button {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #cbd5e1 !important;
}
body.dark-mode .stButton > button:hover {
    background: #283548 !important;
    border-color: #475569 !important;
}
body.dark-mode .stButton > button[kind="primary"] {
    background: #6366f1 !important;
    border-color: #6366f1 !important;
    color: white !important;
}
body.dark-mode .stButton > button[kind="primary"]:hover {
    background: #818cf8 !important;
    border-color: #818cf8 !important;
}
body.dark-mode section[data-testid="stSidebar"] {
    background: #1e293b !important;
    border-right-color: #334155 !important;
}
body.dark-mode .feature-item {
    background: #0f172a !important;
    border-color: #334155 !important;
}
body.dark-mode .app-footer {
    border-top-color: #1e293b !important;
}
body.dark-mode .footer-brand {
    color: #64748b !important;
}
body.dark-mode .footer-tagline {
    color: #475569 !important;
}
body.dark-mode .stProgress > div > div {
    background: #1e293b !important;
}
body.dark-mode .stProgress > div > div > div {
    background: #6366f1 !important;
}
/* Dark mode — explicit text color overrides (CSS vars don't cascade in Streamlit) */
body.dark-mode .brand-title {
    color: #f1f5f9 !important;
}
body.dark-mode .brand-tagline {
    color: #94a3b8 !important;
}
body.dark-mode .brand-divider {
    background: #6366f1 !important;
}
body.dark-mode .class-badge {
    background: rgba(99, 102, 241, 0.1) !important;
    color: #a5b4fc !important;
    border-color: rgba(99, 102, 241, 0.25) !important;
}
body.dark-mode .status-ready {
    background: rgba(52, 211, 153, 0.08) !important;
    color: #34d399 !important;
    border-color: rgba(52, 211, 153, 0.2) !important;
}
body.dark-mode .status-dot-ready {
    background: #34d399 !important;
}
body.dark-mode .voice-label {
    color: #cbd5e1 !important;
}
body.dark-mode .voice-hint {
    color: #64748b !important;
}
body.dark-mode .section-divider {
    background: #1e293b !important;
}
body.dark-mode .text-input-label {
    color: #94a3b8 !important;
}
body.dark-mode .transcript-card {
    background: rgba(30, 41, 59, 0.5) !important;
    border-color: #334155 !important;
    border-left-color: #6366f1 !important;
}
body.dark-mode .transcript-label {
    color: #64748b !important;
}
body.dark-mode .transcript-text {
    color: #cbd5e1 !important;
}
body.dark-mode .explain-icon {
    background: rgba(99, 102, 241, 0.1) !important;
    border-color: rgba(99, 102, 241, 0.25) !important;
}
body.dark-mode .explain-topic {
    color: #f1f5f9 !important;
}
body.dark-mode .explain-body {
    color: #cbd5e1 !important;
}
body.dark-mode .key-points-header {
    color: #64748b !important;
}
body.dark-mode .key-point-item {
    background: rgba(30, 41, 59, 0.5) !important;
    border-color: #334155 !important;
}
body.dark-mode .key-point-item:hover {
    background: rgba(99, 102, 241, 0.08) !important;
    border-color: rgba(99, 102, 241, 0.2) !important;
}
body.dark-mode .key-point-num {
    background: #6366f1 !important;
}
body.dark-mode .key-point-text {
    color: #cbd5e1 !important;
}
body.dark-mode .quiz-topic-label {
    color: #64748b !important;
}
body.dark-mode .quiz-progress-badge {
    background: rgba(99, 102, 241, 0.1) !important;
    color: #a5b4fc !important;
    border-color: rgba(99, 102, 241, 0.25) !important;
}
body.dark-mode .quiz-question-text {
    color: #f1f5f9 !important;
}
body.dark-mode .quiz-option-label {
    background: #334155 !important;
    color: #94a3b8 !important;
    border-color: #475569 !important;
}
body.dark-mode .quiz-option-text {
    color: #cbd5e1 !important;
}
body.dark-mode .quiz-answer-card {
    background: rgba(52, 211, 153, 0.06) !important;
    border-color: rgba(52, 211, 153, 0.15) !important;
}
body.dark-mode .quiz-answer-label {
    color: #34d399 !important;
}
body.dark-mode .quiz-answer-text {
    color: #34d399 !important;
}
body.dark-mode .quiz-explanation-text {
    color: #cbd5e1 !important;
}
body.dark-mode .info-card-clarify {
    background: rgba(251, 191, 36, 0.06) !important;
    border-color: rgba(251, 191, 36, 0.15) !important;
    color: #fbbf24 !important;
}
body.dark-mode .info-card-error {
    background: rgba(248, 113, 113, 0.06) !important;
    border-color: rgba(248, 113, 113, 0.15) !important;
    color: #f87171 !important;
}
body.dark-mode .info-card-offtopic {
    background: rgba(251, 146, 60, 0.06) !important;
    border-color: rgba(251, 146, 60, 0.15) !important;
    color: #fb923c !important;
}
body.dark-mode .audio-section {
    background: rgba(30, 41, 59, 0.5) !important;
    border-color: #334155 !important;
}
body.dark-mode .audio-icon {
    background: rgba(99, 102, 241, 0.1) !important;
}
body.dark-mode .stTextInput label {
    color: #94a3b8 !important;
}
body.dark-mode .stAudioInput > label {
    color: #94a3b8 !important;
}
/* Dark mode — Streamlit native widget overrides */
body.dark-mode .stAudioInput > div {
    background: #1e293b !important;
    border-color: #334155 !important;
}
body.dark-mode .stAudioInput > div > div {
    background: #1e293b !important;
}
body.dark-mode [data-testid="stAudioInput"] {
    background: #1e293b !important;
    border-color: #334155 !important;
    border-radius: 10px !important;
}
body.dark-mode [data-testid="stAudioInput"] > div {
    background: #1e293b !important;
}
body.dark-mode .stMarkdown p,
body.dark-mode .stMarkdown span {
    color: #cbd5e1 !important;
}
body.dark-mode .stMarkdown strong {
    color: #f1f5f9 !important;
}
body.dark-mode .stMarkdown h1,
body.dark-mode .stMarkdown h2,
body.dark-mode .stMarkdown h3 {
    color: #f1f5f9 !important;
}
body.dark-mode hr {
    border-color: #1e293b !important;
    background: #1e293b !important;
}
body.dark-mode [data-testid="stHorizontalBlock"] {
    gap: 0.5rem;
}
/* Audio recorder specific overrides */
body.dark-mode audio {
    filter: invert(0.85) hue-rotate(180deg);
}
body.dark-mode [data-testid="stAudio"] > div {
    background: #1e293b !important;
    border-radius: 10px;
}
body.dark-mode [data-testid="stAudioInput"] div {
    color: #f1f5f9 !important;
}
/* Placeholder text color */
body.dark-mode ::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}
body.dark-mode :-ms-input-placeholder {
    color: #64748b !important;
}
body.dark-mode ::-ms-input-placeholder {
    color: #64748b !important;
}
/* Dark mode toggle button */
.theme-toggle-container {
    position: fixed;
    top: 14px;
    right: 20px;
    z-index: 999999;
}
.theme-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: var(--radius-full);
    font-size: 0.78rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    border: 1px solid var(--gray-200);
    background: var(--gray-50);
    color: var(--gray-500);
    transition: all 0.15s ease;
    box-shadow: var(--shadow-sm);
}
.theme-toggle-btn:hover {
    border-color: var(--gray-300);
    box-shadow: var(--shadow-md);
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session State Defaults
# ---------------------------------------------------------------------------
_defaults = {
    "transcript": None,
    "mode": None,
    "topic": None,
    "explain_data": None,
    "quiz_data": None,
    "quiz_index": 0,
    "show_answer": False,
    "tts_audio": None,
    "last_audio_hash": None,
    "last_text_input": "",
    "error_message": None,
    "off_topic": False,
}
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ---------------------------------------------------------------------------
# Validate Config
# ---------------------------------------------------------------------------
config_errors = Config.validate()
if config_errors:
    st.markdown(
        '<div class="brand-container">'
        '<span class="brand-icon">🎓</span>'
        '<h1 class="brand-title">SmartShala</h1>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.error("⚠️ Configuration issues — please fix before using:")
    for err in config_errors:
        st.warning(f"• {err}")
    st.info(
        "Copy `.env.example` to `.env`, add your Gemini API key, and restart.\n\n"
        "```bash\ncp .env.example .env\n# edit .env with your key\nstreamlit run app.py\n```"
    )
    st.stop()


# ---------------------------------------------------------------------------
# Helper: status HTML
# ---------------------------------------------------------------------------
def _status_html(label: str, icon: str, css_class: str, dot_class: str) -> str:
    return (
        f'<div class="status-bar {css_class}">'
        f'<span class="status-dot {dot_class}"></span>'
        f"{label}"
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------
def process_input(transcript: str) -> None:
    """Run the full pipeline: intent → content → TTS.  Stores results in
    session_state for display by the UI code below.
    """
    # Reset previous results
    st.session_state.explain_data = None
    st.session_state.quiz_data = None
    st.session_state.quiz_index = 0
    st.session_state.show_answer = False
    st.session_state.tts_audio = None
    st.session_state.error_message = None
    st.session_state.off_topic = False
    st.session_state.transcript = transcript

    if not transcript or not transcript.strip():
        st.session_state.mode = "unclear"
        st.session_state.error_message = (
            "Kuch sunai nahi diya. Dobara try karein! 🎤"
        )
        return

    # ── Step 1: Intent extraction ──────────────────────────────
    try:
        intent = extract_intent(transcript)
        st.session_state.mode = intent.mode
        st.session_state.topic = intent.topic
    except Exception as e:
        logger.error(f"Intent error: {e}")
        st.session_state.error_message = (
            "Samajh nahi aa raha — dobara bolein ya type karein! 🔄"
        )
        return

    # ── Step 2: Handle unclear / missing topic ─────────────────
    if intent.mode == "unclear" or not intent.topic:
        return  # UI will show clarification prompt

    # ── Step 2.5: Curriculum-relevance soft gate ───────────────
    if not check_curriculum_relevance(intent.topic):
        logger.warning(f"Off-topic? '{intent.topic}'")
        st.session_state.off_topic = True
        # Don't block — still try to generate (the LLM may refuse itself)

    # ── Step 3: Content generation ─────────────────────────────
    try:
        if intent.mode == "explain":
            result = generate_explanation(intent.topic)
            st.session_state.explain_data = result

            # TTS for explanation (non-fatal)
            try:
                st.session_state.tts_audio = speak(result.explanation)
            except Exception as te:
                logger.error(f"TTS error: {te}")

        elif intent.mode == "quiz":
            result = generate_quiz(intent.topic)
            st.session_state.quiz_data = result

            # TTS for first question (non-fatal)
            try:
                first_q = result.questions[0]
                tts_text = (
                    f"{first_q.question} "
                    + " ".join(
                        f"{chr(65+i)}: {opt}"
                        for i, opt in enumerate(first_q.options)
                    )
                )
                st.session_state.tts_audio = speak(tts_text)
            except Exception as te:
                logger.error(f"TTS error: {te}")

    except Exception as e:
        logger.error(f"Content generation error: {e}")
        st.session_state.error_message = (
            "Content banane mein problem aa gayi. Dobara try karein! 🔄"
        )


# ═══════════════════════════════════════════════════════════════
#  UI LAYOUT
# ═══════════════════════════════════════════════════════════════

# ── Dark/Light Mode Toggle + Apply ────────────────────────────
toggle_col1, toggle_col2 = st.columns([6, 1])
with toggle_col2:
    if st.button(
        "🌙 Dark" if not st.session_state.dark_mode else "☀️ Light",
        key="theme_toggle",
        use_container_width=True,
    ):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Apply dark mode class via JS (components.html reliably executes JS)
import streamlit.components.v1 as components
if st.session_state.dark_mode:
    components.html(
        '<script>window.parent.document.body.classList.add("dark-mode");</script>',
        height=0,
    )
else:
    components.html(
        '<script>window.parent.document.body.classList.remove("dark-mode");</script>',
        height=0,
    )

# ── Header / Branding ──────────────────────────────────────────
st.markdown(
    '<div class="brand-container">'
    '<span class="brand-icon">🎓</span>'
    '<h1 class="brand-title">SmartShala</h1>'
    '<p class="brand-tagline">AI Teaching Assistant for Indian Classrooms</p>'
    '<div class="brand-divider"></div>'
    '<div class="class-badges">'
    '<span class="class-badge">📘 Class 6</span>'
    '<span class="class-badge">📗 Class 7</span>'
    '<span class="class-badge">📙 Class 8</span>'
    '</div>'
    "</div>",
    unsafe_allow_html=True,
)

# ── Status Indicator ──────────────────────────────────────────
st.markdown(
    _status_html(
        "Tayaar hai — Bolein ya Type karein!",
        "🟢",
        "status-ready",
        "status-dot-ready",
    ),
    unsafe_allow_html=True,
)

# ── Voice Input ───────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

st.markdown(
    '<div class="voice-section">'
    '<p class="voice-label">🎤 Mic button dabayein aur bolein</p>'
    '<p class="voice-hint">Hindi, English, ya Hinglish — jo bhi comfortable ho</p>'
    "</div>",
    unsafe_allow_html=True,
)

audio = st.audio_input(
    "🎤 Tap to Speak",
    label_visibility="collapsed",
)

# Process NEW audio (skip if already processed)
if audio is not None:
    audio_bytes = audio.read()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()

    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("🤔 Sun raha hoon aur samajh raha hoon..."):
            try:
                transcript = transcribe(audio_bytes)
                process_input(transcript)
            except Exception as e:
                logger.error(f"STT pipeline error: {e}")
                st.session_state.error_message = (
                    "Audio samajhne mein dikkat aa gayi. "
                    "Neeche type karke try karein! ⌨️"
                )
        st.rerun()

# ── Text Input Fallback ───────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

st.markdown(
    '<p class="text-input-label">⌨️ Ya yahan type karein</p>',
    unsafe_allow_html=True,
)

text_col1, text_col2 = st.columns([5, 1])
with text_col1:
    text_input = st.text_input(
        "Type your question",
        placeholder="Jaise: 'photosynthesis samjhao' ya 'gravity pe quiz lo'",
        label_visibility="collapsed",
    )
with text_col2:
    st.markdown("<br>", unsafe_allow_html=True)  # vertical alignment
    send_clicked = st.button("Bhejo ➡️", use_container_width=True)

if send_clicked and text_input:
    if text_input != st.session_state.last_text_input:
        st.session_state.last_text_input = text_input
        with st.spinner("🤔 Soch raha hoon..."):
            process_input(text_input)
        st.rerun()

# ── Transcript Display ────────────────────────────────────────
if st.session_state.transcript:
    st.markdown(
        '<div class="transcript-card">'
        '<div class="transcript-label">📝 Aapne kaha</div>'
        f'<div class="transcript-text">"{st.session_state.transcript}"</div>'
        "</div>",
        unsafe_allow_html=True,
    )

# ── Error Message ─────────────────────────────────────────────
if st.session_state.error_message:
    st.markdown(
        '<div class="info-card info-card-error">'
        '<span class="info-card-icon">⚠️</span>'
        f'<div class="info-card-title">{st.session_state.error_message}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

# ── Off-topic Warning ────────────────────────────────────────
if st.session_state.off_topic and not st.session_state.error_message:
    st.markdown(
        '<div class="info-card info-card-offtopic">'
        '<span class="info-card-icon">📌</span>'
        '<div class="info-card-title">Yeh topic standard curriculum mein nahi mil raha</div>'
        '<div class="info-card-body">Phir bhi try kar raha hoon!</div>'
        "</div>",
        unsafe_allow_html=True,
    )

# ── Unclear / Clarification ──────────────────────────────────
if (
    st.session_state.mode == "unclear"
    and not st.session_state.error_message
    and st.session_state.transcript
):
    st.markdown(
        '<div class="info-card info-card-clarify">'
        '<span class="info-card-icon">🤔</span>'
        '<div class="info-card-title">Kis topic ke baare mein jaanna chahte hain?</div>'
        '<div class="info-card-body">'
        'Koi padhai wala topic bolein — jaise <b>"photosynthesis"</b>, '
        '<b>"fractions"</b>, ya <b>"gravity"</b>.'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
#  EXPLAIN MODE
# ═══════════════════════════════════════════════════════════════
if st.session_state.explain_data:
    data = st.session_state.explain_data

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    st.markdown(
        '<div class="content-card">'
        # Header
        '<div class="explain-header">'
        '<div class="explain-icon">📚</div>'
        f'<div class="explain-topic">{data.topic}</div>'
        "</div>"
        # Body
        f'<div class="explain-body">{data.explanation}</div>'
        # Key Points
        '<div class="key-points-header">Key Points</div>'
        + "".join(
            f'<div class="key-point-item">'
            f'<div class="key-point-num">{i + 1}</div>'
            f'<div class="key-point-text">{point}</div>'
            f"</div>"
            for i, point in enumerate(data.key_points)
        )
        + "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
#  QUIZ MODE
# ═══════════════════════════════════════════════════════════════
if st.session_state.quiz_data:
    quiz = st.session_state.quiz_data
    idx = st.session_state.quiz_index
    q = quiz.questions[idx]
    total = len(quiz.questions)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Build options HTML
    options_html = ""
    for i, opt in enumerate(q.options):
        label = chr(65 + i)
        if st.session_state.show_answer:
            if i == q.correct_index:
                css = "quiz-option quiz-option-correct"
            else:
                css = "quiz-option quiz-option-wrong"
        else:
            css = "quiz-option"
        options_html += (
            f'<div class="{css}">'
            f'<div class="quiz-option-label">{label}</div>'
            f'<div class="quiz-option-text">{opt}</div>'
            f"</div>"
        )

    st.markdown(
        '<div class="content-card">'
        # Header bar
        '<div class="quiz-header-bar">'
        f'<div class="quiz-topic-label">📝 {quiz.topic}</div>'
        f'<div class="quiz-progress-badge">Sawal {idx + 1} / {total}</div>'
        "</div>"
        + f'<div class="quiz-question-text">{q.question}</div>'
        + options_html
        + "</div>",
        unsafe_allow_html=True,
    )

    # Progress bar
    st.progress((idx + 1) / total)

    # Answer + explanation
    if st.session_state.show_answer:
        correct_label = chr(65 + q.correct_index)
        correct_text = q.options[q.correct_index]
        st.markdown(
            '<div class="quiz-answer-card">'
            '<div class="quiz-answer-label">✅ Sahi Jawab</div>'
            f'<div class="quiz-answer-text">{correct_label}) {correct_text}</div>'
            f'<div class="quiz-explanation-text">💡 {q.explanation}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    # Navigation buttons
    btn_cols = st.columns(3)

    with btn_cols[0]:
        if not st.session_state.show_answer:
            if st.button("👀 Jawab Dikhao", use_container_width=True):
                st.session_state.show_answer = True
                # TTS for answer
                try:
                    tts_text = (
                        f"Sahi jawab hai: {q.options[q.correct_index]}. "
                        f"{q.explanation}"
                    )
                    st.session_state.tts_audio = speak(tts_text)
                except Exception:
                    pass
                st.rerun()

    with btn_cols[1]:
        if idx < total - 1:
            if st.button("➡️ Agla Sawal", use_container_width=True):
                st.session_state.quiz_index = idx + 1
                st.session_state.show_answer = False
                # TTS for next question
                nq = quiz.questions[idx + 1]
                try:
                    tts_text = (
                        f"{nq.question} "
                        + " ".join(
                            f"{chr(65+i)}: {o}"
                            for i, o in enumerate(nq.options)
                        )
                    )
                    st.session_state.tts_audio = speak(tts_text)
                except Exception:
                    pass
                st.rerun()
        elif st.session_state.show_answer:
            st.markdown("🎉 **Quiz complete! Bahut acche!**")

    with btn_cols[2]:
        if st.button("🔄 Phir se shuru", use_container_width=True):
            st.session_state.quiz_index = 0
            st.session_state.show_answer = False
            # TTS for first question again
            fq = quiz.questions[0]
            try:
                tts_text = (
                    f"{fq.question} "
                    + " ".join(
                        f"{chr(65+i)}: {o}"
                        for i, o in enumerate(fq.options)
                    )
                )
                st.session_state.tts_audio = speak(tts_text)
            except Exception:
                pass
            st.rerun()


# ═══════════════════════════════════════════════════════════════
#  TTS AUDIO PLAYBACK
# ═══════════════════════════════════════════════════════════════
if st.session_state.tts_audio:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="audio-section">'
        '<div class="audio-icon">🔊</div>'
        '<div style="font-size: 1rem; color: var(--text-secondary); font-weight: 500;">'
        "Sunein — Audio Playback"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    # Auto-detect format: WAV starts with b'RIFF', MP3 with b'\xff\xfb' or b'ID3'
    audio_data = st.session_state.tts_audio
    audio_format = "audio/wav" if audio_data[:4] == b"RIFF" else "audio/mp3"
    st.audio(audio_data, format=audio_format, autoplay=True)


# ═══════════════════════════════════════════════════════════════
#  NEW QUESTION BUTTON
# ═══════════════════════════════════════════════════════════════
if st.session_state.explain_data or st.session_state.quiz_data:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div class="cta-section">', unsafe_allow_html=True)
    if st.button(
        "🎤 Naya Sawal Poochho",
        use_container_width=True,
        type="primary",
    ):
        for key in _defaults:
            st.session_state[key] = _defaults[key]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown(
    '<div class="app-footer">'
    '<div class="footer-brand">Built for Indian Classrooms • SmartShala v1.0</div>'
    '<div class="footer-tagline">Connecting Dreams Foundation</div>'
    "</div>",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════
#  SIDEBAR — About
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding: 1rem 0 0.5rem;">'
        '<span style="font-size: 2rem;">🎓</span>'
        '<h2 style="margin: 0.25rem 0 0; font-size: 1.2rem; font-weight: 800; '
        'color: #111827;">'
        "SmartShala</h2>"
        '<p style="font-size: 0.75rem; color: #6b7280; margin-top: 0.15rem;">'
        "AI Teaching Assistant</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        '<div class="feature-item">'
        '<span class="feature-icon">🎤</span>'
        '<div class="feature-text"><strong>Voice Input</strong><br>'
        "Hindi, English, ya Hinglish mein bolein</div>"
        "</div>"
        '<div class="feature-item">'
        '<span class="feature-icon">📚</span>'
        '<div class="feature-text"><strong>Explain Mode</strong><br>'
        '"Photosynthesis samjhao" — Short Hinglish explanation + key points</div>'
        "</div>"
        '<div class="feature-item">'
        '<span class="feature-icon">📝</span>'
        '<div class="feature-text"><strong>Quiz Mode</strong><br>'
        '"Gravity pe quiz lo" — Instant MCQ quiz with explanations</div>'
        "</div>"
        '<div class="feature-item">'
        '<span class="feature-icon">🔊</span>'
        '<div class="feature-text"><strong>Audio Playback</strong><br>'
        "Screen pe dekhein + awaaz mein sunein</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        '<div style="padding: 0.5rem;">'
        '<p style="font-size: 0.8rem; color: #374151; font-weight: 600; margin-bottom: 0.5rem;">'
        "Kaise use karein:</p>"
        '<p style="font-size: 0.8rem; color: #6b7280; line-height: 1.6;">'
        "1. 🎤 Mic button dabayein aur bolein<br>"
        "2. 📖 Screen pe explanation dekhein<br>"
        "3. 📝 Quiz mein 'Jawab Dikhao' dabayein<br>"
        "4. ⌨️ Ya type karke bhi pooch sakte hain!"
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; font-size: 0.7rem; color: #9ca3af;">'
        "🏫 Class 6–8 ke students ke liye<br>"
        "🛡️ Sirf padhai ke topics<br>"
        "Made with ❤️ for Indian Classrooms</p>",
        unsafe_allow_html=True,
    )
