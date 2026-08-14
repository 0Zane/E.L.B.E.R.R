import os
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
audio_file = os.path.join(script_dir, "../booting.WAV")

subprocess.run(["pactl set-sink-volume @DEFAULT_SINK@ 100%", audio_file])
subprocess.run(["paplay", audio_file])