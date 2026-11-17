from stt.speech_to_text import listen_and_transcribe

print("Test: microphone")

try:
    result = listen_and_transcribe(seconds=5)
    print("Result:", result)
except Exception as e:
    print("Microphone test failed:", e)
