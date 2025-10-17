import json
import decimal
from typing import Dict, Any
from generator.hf_client import generate_response

# ----------------------------------------------------------------------
#                SAFE JSON SERIALIZATION HANDLER
# ----------------------------------------------------------------------
def safe_json_dumps(data, **kwargs):
    """Safely dump Python objects to JSON, converting Decimals and others."""
    def default(o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return str(o)
    return json.dumps(data, default=default, **kwargs)

# ----------------------------------------------------------------------
#                       SUMMARY FUNCTIONS
# ----------------------------------------------------------------------
def summarize_specs(data: Dict[str, Any]) -> str:
    if not data:
        return "No phone data found."

    name = data.get("name", "Unknown")
    year = data.get("year", "N/A")

    prompt = f"""
Summarize the specifications of {name} ({year}).
Focus on display, battery, camera, chipset, and storage.
Be concise and informative.

Data:
{safe_json_dumps(data, indent=2)}
"""
    return generate_response(prompt)

# ----------------------------------------------------------------------
def summarize_comparison(data: Dict[str, Any], focus: list) -> str:
    phones = data.get("phones", [])
    if len(phones) < 2:
        return "I need at least two phones to compare."

    focus_text = ", ".join(focus) if focus else "overall performance and value"

    prompt = f"""
Compare these Samsung phones focusing on {focus_text}:
{safe_json_dumps(phones, indent=2)}

Provide a clear comparison and end with a recommendation.
"""
    return generate_response(prompt)

# ----------------------------------------------------------------------
def summarize_best_choice(data: Dict[str, Any], focus: list, limit: float) -> str:
    if not data:
        return "I couldn't find any phones under your price range."

    name = data.get("name")
    prompt = f"""
You are a Samsung Phone Advisor.
A user asked for the best phone under ${limit}, focusing on {', '.join(focus) if focus else 'overall performance'}.

Here are the phone details:
{safe_json_dumps(data, indent=2)}

Explain briefly why {name} is a strong choice and who it’s best for.
"""
    return generate_response(prompt)

# ----------------------------------------------------------------------
def generate_final_answer(retrieved: Dict[str, Any], parsed_query: Dict[str, Any]) -> str:
    rtype = retrieved.get("type")
    data = retrieved.get("data")
    focus = parsed_query.get("focus_features", [])
    price = parsed_query.get("price_limit")

    if rtype == "specs":
        return summarize_specs(data)
    elif rtype == "compare":
        return summarize_comparison(data, focus)
    elif rtype == "find_best":
        return summarize_best_choice(data, focus, price)
    else:
        return "I'm sorry, I couldn't find relevant information for your question."
