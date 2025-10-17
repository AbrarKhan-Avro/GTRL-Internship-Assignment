import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

if not HF_API_KEY:
    raise ValueError("Missing HF_API_KEY in your .env file")

# Public, free instruction-tuned model
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

def generate_response(prompt: str, max_new_tokens: int = 400) -> str:
    """Generate text using Hugging Face hosted Falcon 7B Instruct."""
    try:
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": max_new_tokens, "temperature": 0.7}
        }

        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)

        if response.status_code != 200:
            return f"[Error: Hugging Face API returned {response.status_code} - {response.text}]"

        data = response.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()
        elif isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
        else:
            return str(data)

    except Exception as e:
        return f"[Error contacting Hugging Face API: {e}]"

# ---------------------- TEST ----------------------
if __name__ == "__main__":
    test_prompt = "Summarize the key features of Samsung Galaxy S24 Ultra in 3 sentences."
    print(generate_response(test_prompt))
