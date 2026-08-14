import sys
import subprocess


def speak(text):
    subprocess.run(["espeak-ng", "-v", "en", text])