import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    try:
        engine.say(text)
        engine.runAndWait()
    finally:
        engine.stop()
