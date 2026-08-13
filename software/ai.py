import requests

def LLM(prompt):

    response = requests.post("http://localhost:11434/api/generate", json={"model": "qwen3:4b", "prompt": prompt, "stream": False})
    result = response.json()
    message = result.get("response", "")
    return message

