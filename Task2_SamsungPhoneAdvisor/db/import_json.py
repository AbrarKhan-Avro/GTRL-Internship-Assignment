import json
import psycopg2
from pathlib import Path
import re
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/samsung_db")

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "processed_phones.json"

def extract_price(value: str):
    """Extract numeric price and convert to USD regardless of currency format."""
    if not value or value == "N/A":
        return None

    # Clean and simplify text
    text = value.replace(",", "").replace("About", "").strip().upper()

    # Exchange rates (approximate, can be updated)
    CURRENCY_RATES = {
        'USD': 1.0,
        '$': 1.0,
        'EUR': 1.07,
        '€': 1.07,
        'GBP': 1.24,
        '£': 1.24,
        'INR': 0.012,
        '₹': 0.012
    }

    # Find all price+currency patterns
    matches = re.findall(r'([€$£₹]|USD|EUR|GBP|INR)\s?(\d+\.?\d*)', text)
    if not matches:
        # fallback: just numeric value without currency
        match = re.search(r"(\d{2,6})", text)
        return float(match.group(1)) if match else None

    usd_prices = []
    for symbol, val in matches:
        try:
            num = float(val)
            rate = CURRENCY_RATES.get(symbol, 1.0)
            usd_value = num * rate
            usd_prices.append(usd_value)
        except Exception:
            continue

    if not usd_prices:
        return None

    # if multiple prices found, take the smallest
    return round(min(usd_prices), 2)


def extract_year(value):
    """Extract a clean integer year from various formats like '2025, October 10' or 'Released 2023, Feb'"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    # find first 4-digit year in string
    match = re.search(r"(19|20)\d{2}", str(value))
    return int(match.group(0)) if match else None


def normalize_name(name: str):
    return name.lower().strip() if name else None


def safe_json(obj):
    """Ensure value is JSON serializable"""
    try:
        return json.dumps(obj)
    except Exception:
        return json.dumps({})


def main():
    print("📂 Loading processed data...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        phones = json.load(f)

    print(f"Found {len(phones)} processed phones")

    # Connect to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create table if not exists
    schema_path = Path(__file__).parent / "models.sql"
    with open(schema_path, "r", encoding="utf-8") as schema:
        cur.execute(schema.read())
    conn.commit()

    inserted, skipped = 0, 0

    for phone in phones:
        try:
            name = phone.get("Name")
            if not name:
                skipped += 1
                continue

            model_normalized = normalize_name(name)
            launch_info = phone.get("Launch & Status", {})

            # Extract year
            year = extract_year(launch_info.get("Year")) or extract_year(launch_info.get("Release date"))
            release_date = launch_info.get("Release date")
            status = launch_info.get("Status")

            # Extract and convert price to USD
            price = extract_price(phone.get("Misc", {}).get("Price"))

            cur.execute("""
                INSERT INTO phones (
                    name, model_normalized, year, release_date, status, price,
                    network, launch, body, display, platform, memory, camera,
                    comms, features, battery, misc, full_specs
                )
                VALUES (%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                name,
                model_normalized,
                year,
                release_date,
                status,
                price,
                safe_json(phone.get("Network")),
                safe_json(phone.get("Launch & Status")),
                safe_json(phone.get("Body")),
                safe_json(phone.get("Display")),
                safe_json(phone.get("Platform")),
                safe_json(phone.get("Memory")),
                safe_json(phone.get("Camera")),
                safe_json(phone.get("Comms")),
                safe_json(phone.get("Features")),
                safe_json(phone.get("Battery")),
                safe_json(phone.get("Misc")),
                safe_json(phone)
            ))

            inserted += 1

        except Exception as e:
            skipped += 1
            print(f"⚠️ Skipped {phone.get('Name', 'Unknown')} — {e}")
            conn.rollback()  # rollback only this failed insert
            continue

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Inserted {inserted} phones successfully!")
    if skipped:
        print(f"⚠️ Skipped {skipped} phones due to bad data")


if __name__ == "__main__":
    main()
