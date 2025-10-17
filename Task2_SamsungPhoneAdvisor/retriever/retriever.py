import psycopg2
import json
import decimal
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import os

# ----------------------------------------------------------------------
#                           CONFIG
# ----------------------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:%40mbush99@localhost:5432/samsung_db")

# ----------------------------------------------------------------------
#                   SAFE JSON SERIALIZATION
# ----------------------------------------------------------------------
def safe_json_dumps(data, **kwargs):
    """Custom JSON serializer to handle Decimal and other non-serializable objects."""
    def default(o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return str(o)
    return json.dumps(data, default=default, **kwargs)

# ----------------------------------------------------------------------
#                     SAFE JSON LOADER
# ----------------------------------------------------------------------
def safe_json_load(val):
    """Safely load JSON string or return dict if already parsed."""
    if not val:
        return {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {"raw": str(val)}

# ----------------------------------------------------------------------
#                    DATABASE FETCH UTILITIES
# ----------------------------------------------------------------------
def fetch_phone_by_name(model_name: str) -> Optional[Dict[str, Any]]:
    """Fetch one phone by model name (exact match or close)."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT name, year, price, display, battery, camera, platform, memory, body, misc
        FROM phones WHERE LOWER(name) = LOWER(%s)
        LIMIT 1;
    """, (model_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    keys = ["name", "year", "price", "display", "battery", "camera", "platform", "memory", "body", "misc"]
    data = dict(zip(keys, row))

    # Safely ensure JSON fields are dicts
    for key in ["display", "battery", "camera", "platform", "memory", "body", "misc"]:
        data[key] = safe_json_load(data[key])

    return data


def fetch_best_under_price(limit_price: float, focus_features: List[str]) -> Optional[Dict[str, Any]]:
    """
    Find the best phone under a certain price.
    Uses simple heuristics based on the focus (battery, camera, display).
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, price, battery, camera, display, platform, misc
        FROM phones
        WHERE price IS NOT NULL AND price <= %s
        ORDER BY price DESC
        LIMIT 10;
    """, (limit_price,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return None

    best_phone = None
    best_score = 0

    for r in rows:
        name, price, battery, camera, display, platform, misc = r
        phone = {
            "name": name,
            "price": float(price) if price else None,
            "battery": safe_json_load(battery),
            "camera": safe_json_load(camera),
            "display": safe_json_load(display),
            "platform": safe_json_load(platform),
            "misc": safe_json_load(misc)
        }

        # Simple scoring logic
        score = 0
        if "battery" in focus_features:
            bat_text = (phone["battery"].get("Summary") or "").lower()
            if "5000" in bat_text: score += 3
            elif "4500" in bat_text: score += 2
        if "camera" in focus_features:
            cam_text = json.dumps(phone["camera"]).lower()
            if "200mp" in cam_text: score += 3
            elif "108mp" in cam_text: score += 2
        if "display" in focus_features:
            disp_text = json.dumps(phone["display"]).lower()
            if "120hz" in disp_text: score += 2
            if "amoled" in disp_text: score += 1

        # Default factor — higher price likely means higher tier
        score += (phone["price"] or 0) / 1000.0

        if score > best_score:
            best_score = score
            best_phone = phone

    return best_phone


def build_comparison(models: List[str]) -> Dict[str, Any]:
    """Fetch and prepare comparison data between two or more models."""
    results = []
    for m in models:
        phone = fetch_phone_by_name(m)
        if phone:
            results.append(phone)

    if len(results) < 2:
        return {"error": "Need two valid models for comparison."}

    return {"phones": results}

# ----------------------------------------------------------------------
#                  MAIN RETRIEVAL INTERFACE
# ----------------------------------------------------------------------
def retrieve_from_db(parsed_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for the retriever.
    Takes NLU output and returns structured DB results.
    """
    intent = parsed_query["intent"]
    models = parsed_query.get("models", [])
    price_limit = parsed_query.get("price_limit")
    focus = parsed_query.get("focus_features", [])

    if intent == "specs" and models:
        phone = fetch_phone_by_name(models[0])
        return {"type": "specs", "data": phone}

    elif intent == "compare" and len(models) >= 2:
        return {"type": "compare", "data": build_comparison(models)}

    elif intent == "find_best" and price_limit:
        best = fetch_best_under_price(price_limit, focus)
        return {"type": "find_best", "data": best}

    else:
        return {"type": "unknown", "data": None}

# ----------------------------------------------------------------------
#                       TESTING ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    from nlu.nlu import parse_question

    print("🔎 Samsung Phone Advisor — Retriever Module")
    print("Type 'exit' to quit.\n")

    while True:
        q = input("Ask something: ")
        if q.lower() in ["exit", "quit"]:
            break
        parsed = parse_question(q)
        result = retrieve_from_db(parsed)
        print(safe_json_dumps(result, indent=2))
