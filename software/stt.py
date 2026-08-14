import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

MODEL = "tiny.en"
SAMPLE_RATE = 16000
CHUNK_SECONDS = 3

model = WhisperModel(
    MODEL,
    device="cpu",
    compute_type="int8"
)

print("Listening...")

while True:
    audio = sd.rec(
        int(CHUNK_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    audio = audio.flatten()

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