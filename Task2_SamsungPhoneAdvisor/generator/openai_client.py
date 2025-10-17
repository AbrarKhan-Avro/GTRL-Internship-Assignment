import os
import logging
import time
import textwrap
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Missing GROQ_API_KEY. Please set it in your .env file.")

client = Groq(api_key=GROQ_API_KEY)

# Use valid models supported by Groq (fallback order)
AVAILABLE_MODELS = [
    "openai/gpt-oss-120B",
    "openai/gpt-oss-20B"
]

# Central system prompt (easy to change)
SYSTEM_PROMPT = "You are a helpful and concise Samsung Phone Advisor."

# Default max tokens for most calls — raised from small values to allow longer outputs
DEFAULT_MAX_TOKENS = 1200

# Hard cap for a single retry (don't request infinite tokens)
MAX_TOKEN_CAP = 3000

def _looks_truncated(text: str) -> bool:
    """
    Heuristic to detect truncated output.
    Returns True if the text likely ended abruptly.
    """
    if not text:
        return True
    text = text.strip()
    # If ends with obvious ellipsis or an unfinished token, treat as truncated
    if text.endswith("...") or text.endswith(".."):
        return True
    # If very long but doesn't end with terminal punctuation, likely truncated
    if len(text) > 200 and text[-1] not in ".!?\"'%)":
        return True
    return False

def generate_response(prompt: str, temperature: float = 0.6, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    """
    Generate a response using the Groq chat completion API.
    If the returned content seems truncated, do one retry with a larger max_tokens (up to MAX_TOKEN_CAP).
    """
    prompt = textwrap.dedent(prompt).strip()
    last_error = None

    for model_name in AVAILABLE_MODELS:
        try:
            logger.info("Attempting model: %s (max_tokens=%s)", model_name, max_tokens)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            # Safe extraction of content
            content = ""
            try:
                content = response.choices[0].message.content.strip() if response.choices else ""
            except Exception:
                # Older/different response shapes — fallback to str(response)
                content = str(response).strip()

            logger.info("✅ Using model: %s", model_name)
            # If result looks truncated and we allowed fewer than the MAX_TOKEN_CAP, retry once
            if _looks_truncated(content) and max_tokens < MAX_TOKEN_CAP:
                logger.info("Output looks truncated. Retrying once with higher token limit (%s)...", MAX_TOKEN_CAP)
                try:
                    # short wait before retry
                    time.sleep(0.4)
                    response2 = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            # ask model to finish cleanly
                            {"role": "user", "content": prompt + "\n\nPlease finish the response completely and avoid cutting off mid-sentence."}
                        ],
                        temperature=temperature,
                        max_tokens=MAX_TOKEN_CAP
                    )
                    try:
                        content2 = response2.choices[0].message.content.strip() if response2.choices else ""
                    except Exception:
                        content2 = str(response2).strip()

                    # If second attempt returns non-empty, return it. Otherwise return first content.
                    if content2:
                        return content2
                    else:
                        return content or "[No content returned on retry.]"
                except Exception as e2:
                    logger.warning("Retry with higher token limit failed: %s", e2)
                    # If retry fails, return the original content (even if truncated) or error message
                    return content or f"[Error on retry: {e2}]"
            # If not truncated or we don't want to retry, return the content
            return content or "[No content returned.]"
        except Exception as e:
            last_error = e
            logger.warning("Model %s failed: %s", model_name, e)
            # try next model in the list
            continue

    # If we exhausted models
    return f"[Error contacting Groq API: all fallback models failed. Last error: {last_error}]"
