"""Streaming speech-to-text: energy VAD + faster-whisper tiny.en."""

from __future__ import annotations

import os
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

TARGET_RATE = 16000
FRAME_MS = 30
START_FRAMES = 3          # 90 ms of speech to start
END_FRAMES = 16           # 480 ms of silence to stop
PRE_ROLL_FRAMES = 10      # 300 ms kept before speech
MIN_SPEECH_FRAMES = 8     # 240 ms minimum utterance
MAX_SECONDS = 10
SETTLE_FRAMES = 6         # ~180 ms of TTS echo discarded
CALIBRATE_FRAMES = 6      # ~180 ms noise-floor sample
NOISE_FLOOR_MIN = 0.004
PAD_FRAMES = 2            # keep a little silence for Whisper

# Whisper tiny loves to hallucinate these on noise / silence.
_JUNK = {
    "",
    ".",
    "you",
    "thank you",
    "thanks",
    "thanks for watching",
    "thank you for watching",
    "thank you for watching.",
    "please subscribe",
    "subtitles by",
    "the",
    "mm-hmm",
    "hmm",
    "uh",
    "um",
}


def _cpu_threads() -> int:
    return max(1, os.cpu_count() or 4)


def load_whisper() -> WhisperModel:
    threads = _cpu_threads()
    last_error = None
    for compute in ("int8", "int8_float16", "float32"):
        try:
            return WhisperModel(
                "tiny.en",
                device="cpu",
                compute_type=compute,
                cpu_threads=threads,
                num_workers=1,
            )
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Could not load Whisper: {last_error}") from last_error


def _rms(frame: np.ndarray) -> float:
    x = np.asarray(frame, dtype=np.float32).reshape(-1)
    return float(np.sqrt(np.mean(x * x) + 1e-12))


def _resample(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if src_rate == dst_rate or audio.size == 0:
        return audio
    n = int(round(audio.size * dst_rate / src_rate))
    if n < 1:
        return np.zeros(0, dtype=np.float32)
    src_x = np.arange(audio.size, dtype=np.float32)
    dst_x = np.linspace(0, audio.size - 1, n, dtype=np.float32)
    return np.interp(dst_x, src_x, audio).astype(np.float32)


def _is_junk(text: str) -> bool:
    cleaned = text.strip().lower().strip(".!,?")
    return cleaned in _JUNK or len(cleaned) < 2


def _input_device():
    raw = os.environ.get("ELBERR_MIC_DEVICE", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return raw


class Listener:
    def __init__(self, model: WhisperModel | None = None) -> None:
        self.model = model or load_whisper()
        self.device = _input_device()
        self.capture_rate = TARGET_RATE
        self.noise_rms = NOISE_FLOOR_MIN
        self._configure_device()

    def prime(self) -> None:
        """Compile Whisper kernels so the first real utterance is not a cold start."""
        silence = np.zeros(TARGET_RATE // 4, dtype=np.float32)
        self._transcribe(silence)

    def _configure_device(self) -> None:
        try:
            info = sd.query_devices(self.device, "input")
        except Exception:
            print("Available audio devices:", flush=True)
            print(sd.query_devices(), flush=True)
            raise RuntimeError(
                "No input device. Set ELBERR_MIC_DEVICE to a device index from the list above."
            )

        default_rate = int(info.get("default_samplerate") or TARGET_RATE)
        name = info.get("name", "unknown")
        for rate in (TARGET_RATE, default_rate):
            try:
                sd.check_input_settings(
                    device=self.device,
                    samplerate=rate,
                    channels=1,
                    dtype="float32",
                )
                self.capture_rate = rate
                break
            except Exception:
                continue
        else:
            self.capture_rate = default_rate

        print(
            f"[stt] mic={name!r} rate={self.capture_rate} device={self.device}",
            flush=True,
        )

    def _threshold(self) -> float:
        return max(0.012, self.noise_rms * 4.0)

    def _open_stream(self) -> sd.InputStream:
        frame_samples = max(1, int(self.capture_rate * FRAME_MS / 1000))
        kwargs = {
            "samplerate": self.capture_rate,
            "channels": 1,
            "dtype": "float32",
            "device": self.device,
            "blocksize": frame_samples,
        }
        try:
            return sd.InputStream(latency="low", **kwargs)
        except Exception:
            return sd.InputStream(**kwargs)

    def _read_frame(self, stream: sd.InputStream) -> np.ndarray:
        frame_samples = stream.blocksize or max(1, int(self.capture_rate * FRAME_MS / 1000))
        data, _overflowed = stream.read(frame_samples)
        if data.ndim > 1:
            data = data[:, 0]
        return np.asarray(data, dtype=np.float32).reshape(-1)

    def _transcribe(self, audio_16k: np.ndarray) -> str:
        if audio_16k.size < TARGET_RATE * 0.2:
            return ""
        kwargs = {
            "language": "en",
            "beam_size": 1,
            "best_of": 1,
            "temperature": 0.0,
            "vad_filter": False,
            "condition_on_previous_text": False,
            "without_timestamps": True,
            "word_timestamps": False,
            "no_speech_threshold": 0.6,
        }
        try:
            segments, _info = self.model.transcribe(audio_16k, **kwargs)
        except TypeError:
            segments, _info = self.model.transcribe(
                audio_16k, language="en", beam_size=1, vad_filter=False
            )
        text = "".join(segment.text for segment in segments).strip()
        if _is_junk(text):
            return ""
        return text

    def listen(self) -> str:
        """Block until a non-empty utterance is transcribed."""
        frame_samples = max(1, int(self.capture_rate * FRAME_MS / 1000))
        max_frames = int(MAX_SECONDS * 1000 / FRAME_MS)

        while True:
            with self._open_stream() as stream:
                for _ in range(SETTLE_FRAMES):
                    self._read_frame(stream)

                cal = [_rms(self._read_frame(stream)) for _ in range(CALIBRATE_FRAMES)]
                self.noise_rms = max(NOISE_FLOOR_MIN, float(np.median(cal)))

                pre_roll: list[np.ndarray] = []
                voiced: list[np.ndarray] = []
                speech_run = 0
                silence_run = 0
                capturing = False
                print("Listening...", flush=True)

                while True:
                    frame = self._read_frame(stream)
                    if frame.size < frame_samples:
                        frame = np.pad(frame, (0, frame_samples - frame.size))

                    level = _rms(frame)
                    is_speech = level >= self._threshold()

                    if not capturing:
                        pre_roll.append(frame)
                        if len(pre_roll) > PRE_ROLL_FRAMES:
                            dropped = pre_roll.pop(0)
                            self.noise_rms = 0.95 * self.noise_rms + 0.05 * _rms(dropped)
                            self.noise_rms = max(NOISE_FLOOR_MIN, self.noise_rms)

                        if is_speech:
                            speech_run += 1
                            if speech_run >= START_FRAMES:
                                capturing = True
                                voiced = pre_roll[-PRE_ROLL_FRAMES:]
                                pre_roll = []
                                silence_run = 0
                        else:
                            speech_run = 0
                        continue

                    voiced.append(frame)
                    if is_speech:
                        silence_run = 0
                    else:
                        silence_run += 1

                    too_long = len(voiced) >= max_frames
                    ended = silence_run >= END_FRAMES
                    if not (ended or too_long):
                        continue

                    speech_frames = len(voiced) - (silence_run if ended else 0)
                    if speech_frames < MIN_SPEECH_FRAMES:
                        capturing = False
                        voiced = []
                        speech_run = 0
                        silence_run = 0
                        continue

                    if ended and silence_run > PAD_FRAMES:
                        voiced = voiced[: len(voiced) - silence_run + PAD_FRAMES]
                    audio = np.concatenate(voiced).astype(np.float32, copy=False)
                    break

            audio_16k = _resample(audio, self.capture_rate, TARGET_RATE)
            t0 = time.perf_counter()
            text = self._transcribe(audio_16k)
            took = time.perf_counter() - t0
            if text:
                print(f"[stt] {took:.2f}s  {text}", flush=True)
                return text
            print(f"[stt] {took:.2f}s  (ignored)", flush=True)
