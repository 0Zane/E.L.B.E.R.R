"""espeak-ng TTS. Speaks one sentence at a time so LLM streaming can overlap."""

from __future__ import annotations

import shutil
import subprocess

_ESPEAK = None


def _espeak_bin() -> str:
    global _ESPEAK
    if _ESPEAK is None:
        _ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")
    if not _ESPEAK:
        raise FileNotFoundError("espeak-ng is not installed or not on PATH")
    return _ESPEAK


def speak(text: str) -> None:
    if not isinstance(text, str):
        text = getattr(text, "response", None) or str(text)
    text = " ".join(text.split())
    if not text:
        return
    subprocess.run(
        [
            _espeak_bin(),
            "-v",
            "en",
            "-s",
            "165",
            "-a",
            "140",
            "--stdin",
        ],
        input=text.encode("utf-8"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
