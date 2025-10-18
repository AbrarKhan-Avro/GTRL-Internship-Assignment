import re
import json
import spacy
from rapidfuzz import fuzz
from typing import Dict, Any, List

import psycopg2
from dotenv import load_dotenv
import os
from difflib import SequenceMatcher

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:%40mbush99@localhost:5432/samsung_db")

# (Run once before using: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

def get_all_model_names() -> List[str]:
    """Fetch all phone names from the DB for fuzzy matching."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT name FROM phones;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

ALL_MODELS = get_all_model_names()

def detect_intent(question: str) -> str:
    """Detect what kind of question the user is asking."""
    q = question.lower()

    if any(x in q for x in ["compare", "difference", "vs", "versus"]):
        return "compare"

    if any(x in q for x in ["spec", "specs", "details", "features", "information", "info"]):
        return "specs"

    if any(x in q for x in ["best", "recommend", "suggest", "which phone", "good for"]):
        return "find_best"

    if any(x in q for x in ["price", "cost", "how much"]):
        return "price"

    return "general"

def extract_focus_features(question: str) -> List[str]:
    """
    Detect key features being asked about (battery, camera, display, etc.)
    Handles natural words like 'photography', 'selfie', 'battery life', etc.
    """
    mapping = {
        "battery": ["battery", "battery life", "charge", "charging"],
        "camera": ["camera", "photo", "photography", "selfie", "picture", "lens"],
        "display": ["display", "screen", "amoled", "resolution", "size"],
        "performance": ["performance", "speed", "processor", "chipset", "cpu", "gpu"],
        "storage": ["storage", "memory", "ram", "rom"],
        "design": ["weight", "dimension", "build", "thickness"]
    }
    q = question.lower()
    found = []
    for key, words in mapping.items():
        if any(w in q for w in words):
            found.append(key)
    return found

def extract_price_filter(question: str) -> float:
    """
    Detect if user mentions a price limit (e.g., under $1000, below 700 USD).
    Avoid picking up model numbers like 'S23' or 'S21'.
    """
    q = question.lower().replace(",", "")
    match = re.search(r"(?:under|below|less than|\$)\s*\$?(\d{2,5})", q)
    if match:
        return float(match.group(1))
    return None

def extract_model_names(question: str) -> Dict[str, Any]:
    """
    Robust Samsung phone model extractor.
    Detects how many models were mentioned, handles suffix tags properly,
    ensures matches exist in the database, and reports missing ones accurately.
    """

    q_raw = question.lower()
    q_clean = re.sub(r"[^a-z0-9\s\+]", " ", q_raw)
    q_clean = re.sub(r"\s+", " ", q_clean).strip()

    candidates = re.findall(
        r"\b(?:galaxy\s+)?(?:s|a|m|f)\d{1,3}(?:\s?(?:ultra|fe|lite|plus|pro|4g|5g))?\b",
        q_clean
    )
    candidates = list(dict.fromkeys(candidates))  # deduplicate

    normalized_candidates = []
    for c in candidates:
        c = c.strip()
        if c.startswith("galaxy "):
            c = c.replace("galaxy ", "")
        normalized_candidates.append(c.strip())

    matched = []
    missing = []

    for cand in normalized_candidates:
        best_match = None
        best_ratio = 0
        for model in ALL_MODELS:
            norm_model = normalize_model_name(model)
            ratio = fuzz.ratio(cand, norm_model)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = model

        # Only count strong matches
        if best_ratio >= 90 and best_match:
            if best_match not in matched:
                matched.append(best_match)
        else:
            missing.append(cand.upper())

    result = {"models": matched}
    if missing:
        result["missing_models"] = missing
    return result



def normalize_model_name(text: str) -> str:
    """Simplify a phone name for easier comparison."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\+]", " ", text)  # remove symbols
    text = re.sub(r"\b(samsung|galaxy)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def parse_question(question: str) -> Dict[str, Any]:
    """Main entry point for NLU — returns structured understanding of question."""

    intent = detect_intent(question)
    focus = extract_focus_features(question)
    price_limit = extract_price_filter(question)

    # Updated: extract_model_names now returns dict with possible missing models
    model_result = extract_model_names(question)
    models = model_result.get("models", [])
    missing = model_result.get("missing_models", [])

    result = {
        "intent": intent,
        "focus_features": focus,
        "price_limit": price_limit,
        "models": models,
        "original": question
    }

    # Add missing models to result if any
    if missing:
        result["missing_models"] = missing

    # Add helper notes for CLI feedback
    if not models and missing:
        result["note"] = f"⚠️ No valid models found in database. Unknown models: {', '.join(missing)}"
    elif missing:
        result["note"] = f"⚠️ Some models not found in database: {', '.join(missing)}"
    elif not models and any(x.isdigit() for x in question):
        result["note"] = "⚠️ Model mentioned not found in database."

    return result


if __name__ == "__main__":
    print("🔍 Samsung Phone Advisor — NLU Module")
    print("Type 'exit' to quit.\n")
    while True:
        q = input("Ask something about Samsung phones: ")
        if q.lower() in ["exit", "quit"]:
            break
        parsed = parse_question(q)
        print(json.dumps(parsed, indent=2))
