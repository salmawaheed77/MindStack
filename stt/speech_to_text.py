import os
import warnings

# Tell Python where the project's ffmpeg is (so no one needs to edit PATH)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["PATH"] += os.pathsep + os.path.join(BASE_DIR, "ffmpeg", "bin")

import whisper

# Hide a harmless warning that appears when running on CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

_model = None  # the model is loaded once, then reused


def _get_model(model_name="base"):
    """Load the Whisper model the first time, then reuse it."""
    global _model
    if _model is None:
        _model = whisper.load_model(model_name)
    return _model


def transcribe_audio(audio_path):
    """Take the path of an audio file and return the recognized text."""
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _get_model()
    result = model.transcribe(audio_path, fp16=False)
    return result["text"].strip()
import tempfile

import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000  # Whisper works best with 16 kHz audio


def listen_and_transcribe(seconds=5):
    """Record from the microphone for a few seconds and return the text."""
    print(f"Listening for {seconds} seconds... speak now.")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()  # wait until recording is finished
    print("Processing...")

    # Save to a temporary file, transcribe it, then delete the file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        sf.write(tmp_path, audio, SAMPLE_RATE)
        return transcribe_audio(tmp_path)
    finally:
        os.remove(tmp_path)