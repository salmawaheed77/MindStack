import pyttsx3

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS error: {e}")

if __name__ == "__main__":
    speak("Text to speech is working")