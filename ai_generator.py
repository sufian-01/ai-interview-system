"""Gemini-powered question generation utilities."""

from __future__ import annotations

import os

from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()


def _default_prompt(topic: str, difficulty: str) -> str:
    return (
        "You are an expert interviewer. "
        f"Generate exactly 5 concise interview questions about '{topic}' "
        f"for a '{difficulty}' difficulty level. "
        "Return each question on a new line without numbering."
    )


def generate_questions(topic: str, difficulty: str) -> list[str]:
    """Generate exactly five interview questions from Gemini."""
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY environment variable.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(_default_prompt(topic.strip(), difficulty))
    text = getattr(response, "text", "") or ""

    lines = [line.strip("-• \t") for line in text.splitlines() if line.strip()]
    questions = [line for line in lines if line.endswith("?")]

    if len(questions) < 5:
        # Keep non-question lines if Gemini omitted punctuation.
        questions = lines

    if len(questions) < 5:
        raise RuntimeError("Gemini did not return enough questions.")

    return questions[:5]
