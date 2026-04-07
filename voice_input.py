"""Voice input utilities for the interview application."""

from __future__ import annotations

import speech_recognition as sr


def record_voice() -> tuple[str | None, str | None]:
    """Record voice from the microphone and convert it to text.

    Returns:
        tuple[str | None, str | None]:
            - recognized text (or None)
            - error message (or None)
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=30)
    except sr.WaitTimeoutError:
        return None, "No voice detected. Please try again and speak clearly."
    except OSError:
        return None, "Microphone is not available. Please check your audio device settings."

    try:
        text = recognizer.recognize_google(audio)
        return text, None
    except sr.UnknownValueError:
        return None, "Could not understand audio due to noise or unclear speech."
    except sr.RequestError as exc:
        return None, f"Speech recognition service is unavailable right now: {exc}"
