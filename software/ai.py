import ollama
from main import client

def LLM(prompt):

    model = "ELBERR"
    response = client.generate(model=model, prompt=prompt)
    return response.response