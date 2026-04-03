import requests
import json

def ask_ollama(prompt: str, model: str = "mistral") -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

if __name__ == "__main__":
    answer = ask_ollama("What is the Consumer Protection Act in India?")
    print(answer)