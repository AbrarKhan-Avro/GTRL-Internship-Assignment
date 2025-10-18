import json
import decimal
from typing import Dict, Any, Optional, List
from generator.openai_client import generate_response

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that safely handles Decimal and other types."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        # Fallback for any other non-serializable type
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

def safe_json_dumps(data, **kwargs):
    """Safely dump Python objects to JSON, converting Decimals and others."""
    return json.dumps(data, cls=DecimalEncoder, **kwargs)

def summarize_specs(data: Dict[str, Any]) -> str:
    """Compose a text summary prompt for a single phone."""
    if not data:
        return "No phone data found."

    name = data.get("name", "Unknown")
    price = data.get("price")
    year = data.get("year")
    display = data.get("display", {}).get("Summary") or data.get("display", {}).get("Type")
    battery = data.get("battery", {}).get("Summary") or data.get("battery", {}).get("Description")
    camera = data.get("camera", {}).get("Main", {}).get("Modules")
    platform = data.get("platform", {}).get("Chipset")
    storage = data.get("memory", {}).get("Summary")

    prompt = f"""
    Summarize the key specifications of {name} ({year if year else 'N/A'}).
    Use natural, informative language suitable for a tech assistant.
    Mention display, battery, camera, chipset/platform, and storage details.

    Data (JSON):
    {safe_json_dumps(data, indent=2)}
    """

    # Allow a bit more tokens for a full single-device spec
    return generate_response(prompt, max_tokens=1500)

def summarize_comparison(data: Dict[str, Any], focus: Optional[List[str]]) -> str:
    """Compose a comparison prompt for two phones."""
    phones = data.get("phones", [])
    if len(phones) < 2:
        return "I need at least two valid phones to compare."

    names = [p.get("name", "unknown") for p in phones]
    focus_text = ", ".join(focus) if focus else "overall performance and value"

    prompt = f"""
    Compare the following Samsung phones for {focus_text}:
    {safe_json_dumps(phones, indent=2)}

    Provide a detailed but concise comparison.
    Highlight differences in camera, battery, display, and performance when relevant.
    End with a short, clear recommendation about which one is better for {focus_text}.
    Make sure the response is complete and doesn't get cut off.
    """

    # Comparisons can be long — request more tokens
    return generate_response(prompt, max_tokens=2000)

def summarize_best_choice(data: Dict[str, Any], focus: Optional[List[str]], limit: float) -> str:
    """Prompt for recommending the best phone under a price."""
    if not data:
        return "I couldn't find any phones under your price range."

    name = data.get("name", "Unknown")
    prompt = f"""
    You are a Samsung Phone Advisor.
    A user asked for the best Samsung phone under ${limit}, focusing on {', '.join(focus) if focus else 'overall performance'}.

    Here are details of a suggested phone:
    {safe_json_dumps(data, indent=2)}

    Write a short recommendation explaining why {name} is a great choice.
    Mention its main strengths and who it’s best suited for.
    Ensure the answer is complete and not truncated.
    """

    return generate_response(prompt, max_tokens=1400)

def generate_final_answer(retrieved: Dict[str, Any], parsed_query: Dict[str, Any]) -> str:
    """Selects which summarization method to use based on query type."""
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
