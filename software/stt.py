import sounddevice as sd
import numpy as np
from scipy.signal import resample_poly
from faster_whisper import WhisperModel

INPUT_RATE = 48000
WHISPER_RATE = 16000
CHUNK_SECONDS = 3

model = WhisperModel(
    "tiny.en",
    device="cpu",
    compute_type="int8"
)

print("Listening...")

while True:

    audio = sd.rec(
        int(CHUNK_SECONDS * INPUT_RATE),
        samplerate=INPUT_RATE,
        channels=1,
        dtype="float32",
        device=0
    )

    sd.wait()

    audio = audio.flatten()

    audio = resample_poly(audio, WHISPER_RATE, INPUT_RATE)

    segments, info = model.transcribe(
        audio,
        language="en",
        beam_size=1,
        vad_filter=True
    )

    text = ""

    for segment in segments:
        text += segment.text

    if text.strip():
        print(">", text.strip())