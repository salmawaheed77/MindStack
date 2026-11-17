import pyttsx3

_engine = None

def get_engine():
    global _engine

    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 150)

    return _engine


def speak(text):
    try:
        engine = get_engine()
        engine.say(text)
        engine.runAndWait()
        return True

    except Exception as e:
        print(f"TTS error: {e}")
        return False


if __name__ == "__main__":
    speak("Text to speech is working")
