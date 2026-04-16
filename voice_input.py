"""Voice input utilities for the interview application."""

from __future__ import annotations

import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile


def record_voice() -> tuple[str | None, str | None]:
    recognizer = sr.Recognizer()
    fs = 44100
    duration = 5

    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        write(temp_file.name, fs, recording)

    except Exception:
        return None, "Mic not working"

    try:
        with sr.AudioFile(temp_file.name) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text, None

    except sr.UnknownValueError:
        return None, "Could not understand audio"
    except sr.RequestError:
        return None, "Speech service error"