"""Groq-powered question generation and answer evaluation utilities."""

from __future__ import annotations

import json
import os
import re

from dotenv import find_dotenv, load_dotenv
from groq import Groq


load_dotenv(find_dotenv(), override=True)

GROQ_MODEL = "llama3-8b-8192"


def _get_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if api_key is None or not api_key.strip():
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add GROQ_API_KEY=your_api_key_here to your .env file."
        )
    return api_key.strip()


def _format_groq_error(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    response_text = ""

    if response is not None:
        try:
            response_text = response.text
        except Exception:
            response_text = ""

    message = str(exc)
    parts = ["Groq API request failed"]
    if status_code:
        parts.append(f"HTTP {status_code}")
    if response_text:
        parts.append(response_text)
    elif message:
        parts.append(message)

    return ": ".join(parts)


def _call_groq(prompt: str, temperature: float = 0.4, max_tokens: int = 700) -> str:
    api_key = _get_api_key()
    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        error_message = _format_groq_error(exc)
        print(error_message)
        raise RuntimeError(error_message) from exc

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        print(f"Unexpected Groq API response: {response}")
        raise RuntimeError("Groq API returned an unexpected response.") from exc

    if not content:
        print(f"Empty Groq API response: {response}")
        raise RuntimeError("Groq API returned an empty response.")

    return content.strip()


def _clean_question_line(line: str) -> str:
    return re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()


def generate_ai_questions(topic: str) -> list[str]:
    """Generate five interview questions for any user-provided topic."""
    cleaned_topic = (topic or "").strip()
    if not cleaned_topic:
        raise ValueError("Topic cannot be empty.")

    prompt = (
        f"Generate 5 technical interview questions on {cleaned_topic}. "
        "Return only the questions, one per line, without numbering or extra text."
    )
    content = _call_groq(prompt, temperature=0.5, max_tokens=700)

    lines = [_clean_question_line(line) for line in content.splitlines() if line.strip()]
    questions = [line for line in lines if line]

    if len(questions) < 5:
        print(f"Groq returned too few questions: {content}")
        raise RuntimeError("Groq did not return enough questions.")

    return questions[:5]


def evaluate_answer(question: str, answer: str) -> dict[str, object]:
    """Score an answer out of 10 and return short feedback from Groq."""
    cleaned_question = (question or "").strip()
    cleaned_answer = (answer or "").strip()

    if not cleaned_answer:
        return {
            "score": 0.0,
            "feedback": "No answer was provided. Give a structured response with examples.",
        }

    prompt = f"""
Evaluate this interview answer.

Question: {cleaned_question}
Answer: {cleaned_answer}

Return strict JSON only with:
{{
  "score": number from 0 to 10,
  "feedback": "one short feedback sentence"
}}
"""
    content = _call_groq(prompt, temperature=0.2, max_tokens=300)

    json_match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not json_match:
        print(f"Groq returned non-JSON evaluation: {content}")
        raise RuntimeError("Groq did not return a JSON evaluation.")

    try:
        result = json.loads(json_match.group(0))
        score = round(float(result.get("score", 0)), 1)
        feedback = str(result.get("feedback", "")).strip()
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid Groq evaluation payload: {content}")
        raise RuntimeError("Groq returned an invalid evaluation payload.") from exc

    score = max(0.0, min(10.0, score))
    if not feedback:
        feedback = "Add more detail, structure, and a concrete example."

    return {"score": score, "feedback": feedback}


def generate_questions(topic: str, difficulty: str | None = None) -> list[str]:
    """Backward-compatible wrapper for older app code paths."""
    return generate_ai_questions(topic)
