"""Play the boot sting once PulseAudio is actually up."""

from __future__ import annotations

import os
import shutil
import subprocess
import time

_VOLUME = "120%"
_PULSE_WAIT_S = 8.0


def _wait_for_pulse(timeout: float = _PULSE_WAIT_S) -> bool:
    if not shutil.which("pactl"):
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(
            ["pactl", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return True
        time.sleep(0.15)
    return False


def bootsound() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    audio_file = os.path.abspath(os.path.join(script_dir, "..", "booting.WAV"))

    _wait_for_pulse()

    if shutil.which("pactl"):
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", _VOLUME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    if not os.path.isfile(audio_file):
        print(f"[boot] missing {audio_file}", flush=True)
        return

    player = shutil.which("paplay") or shutil.which("aplay")
    if not player:
        print("[boot] paplay/aplay not found", flush=True)
        return
    subprocess.run(
        [player, audio_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
