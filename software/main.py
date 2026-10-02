"""E.L.B.E.R.R. voice loop: mic -> text -> local LLM -> espeak-ng."""

from __future__ import annotations

import json
import os
import time
from threading import Thread

import ollama

from boot import bootsound
from llm import stream_sentences, warmup
from stt import Listener, load_whisper
from tts import speak
from uart_communication import (
    Esp32UART,
    commands_for_utterance,
)

MODEL = os.environ.get("ELBERR_MODEL", "ELBERR")
HISTORY_TURNS = 4


def _load_whisper_into(holder: dict) -> None:
    holder["model"] = load_whisper()


def main() -> None:
    started = time.perf_counter()
    holder: dict = {}
    stt_thread = Thread(target=_load_whisper_into, args=(holder,), daemon=True)
    stt_thread.start()

    bootsound()

    client = ollama.Client()
    print("Loading mind...", flush=True)
    warmup(client, MODEL)

    stt_thread.join()
    listener = Listener(model=holder["model"])
    listener.prime()

    esp32 = Esp32UART()
    esp32.start()
    print(f"Online in {time.perf_counter() - started:.1f}s", flush=True)

    history: list[dict] = []

    while True:
        text = listener.listen()
        print(f"> {text}", flush=True)
        history.append({"role": "user", "content": text})

        context = esp32.snapshot()
        requested_commands = commands_for_utterance(text)
        if requested_commands:
            command = requested_commands[0]
            try:
                context = esp32.request(command).result(timeout=esp32.response_timeout)
            except TimeoutError as exc:
                print(f"[uart] request timed out: {exc}", flush=True)
                context = esp32.snapshot()
                context["request_status"] = "timeout"
                context["requested_command"] = int(command)
            except RuntimeError as exc:
                print(f"[uart] request failed: {exc}", flush=True)
                context = esp32.snapshot()
                context["request_status"] = "unavailable"
                context["requested_command"] = int(command)

        messages = history[:-1] + [
            {
                "role": "user",
                "content": (
                    f"ESP32 data (JSON): {json.dumps(context, separators=(',', ':'))}\n"
                    f"User said: {text}"
                ),
            }
        ]
        reply_parts: list[str] = []
        t0 = time.perf_counter()
        first = True
        try:
            for sentence in stream_sentences(client, MODEL, messages):
                if first:
                    print(f"[llm] first audio {time.perf_counter() - t0:.2f}s", flush=True)
                    first = False
                print(f"< {sentence}", flush=True)
                speak(sentence)
                reply_parts.append(sentence)
        except Exception as exc:
            print(f"[llm] {exc}", flush=True)
            history.pop()
            continue

        if reply_parts:
            history.append({"role": "assistant", "content": " ".join(reply_parts)})
            history = history[-(HISTORY_TURNS * 2) :]


if __name__ == "__main__":
    main()
