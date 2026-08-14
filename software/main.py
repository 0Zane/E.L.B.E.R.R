from stt import listen
from tts import speak
from boot import bootsound
import ollama

# Initialize the Ollama client
client = ollama.Client()
model="ELBERR"


if __name__ == "__main__":
    bootsound()
    while True:
        text = listen()
        response = client.generate(model=model, prompt=text)
        speak(response)