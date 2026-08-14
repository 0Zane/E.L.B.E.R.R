from ai import LLM
from stt import listen
from tts import speak
from boot import bootsound
import ollama

# Initialize the Ollama client
client = ollama.Client()


if __name__ == "__main__":
    bootsound()
    while True:
        text = listen()
        response = LLM(text)
        speak(response)