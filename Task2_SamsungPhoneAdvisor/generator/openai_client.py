import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Missing GROQ_API_KEY. Please set it in your .env file.")

client = Groq(api_key=GROQ_API_KEY)

# Use valid models supported by Groq
AVAILABLE_MODELS = [
    "openai/gpt-oss-120B",
    "openai/gpt-oss-20B"
]

def generate_response(prompt: str, temperature: float = 0.6, max_tokens: int = 400) -> str:
    for model_name in AVAILABLE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful and concise Samsung Phone Advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content.strip()
            print(f"✅ Using model: {model_name}")
            return content
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
    return "[Error contacting Groq API: all fallback models failed.]"

if __name__ == "__main__":
    test_prompt = "Summarize the key strengths of the Samsung Galaxy S24 Ultra."
    result = generate_response(test_prompt)
    print("\n--- AI Response ---\n", result)
