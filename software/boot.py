import os
import subprocess
import time

def bootsound():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    audio_file = os.path.join(script_dir, "../booting.WAV")

    time.sleep(5)

    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "120%"])
    subprocess.run(["paplay", audio_file])