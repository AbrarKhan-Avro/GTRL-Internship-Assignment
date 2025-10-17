import json
import re
from pathlib import Path

RAW_FILE = Path(__file__).resolve().parent / "samsung_phones.json"
OUTPUT_FILE = Path(__file__).resolve().parent / "processed_phones.json"

def extract_year(value):
    """Extract year (int) from strings like 'Released 2022, February'"""
    if not value or value == "N/A":
        return None
    match = re.search(r"(20\d{2}|19\d{2})", value)
    return int(match.group(0)) if match else None

def process_entry(raw):
    # Helper to safely get fields
    def get(*keys):
        for k in keys:
            if k in raw and raw[k] not in ["N/A", "", None]:
                return raw[k]
        return None

    processed = {
        "Name": get("Name"),
        "Network": {
            "Technology": get("nettech"),
            "2G": get("net2g"),
            "3G": get("net3g"),
            "4G": get("net4g"),
            "5G": get("net5g"),
            "Speed": get("speed")
        },
        "Launch & Status": {
            "Release date": get("Release date"),
            "Year": get("year") or extract_year(get("Release date") or ""),
            "Status": get("status")
        },
        "Body": {
            "Dimensions": get("dimensions"),
            "Weight": get("Weight") or get("weight"),
            "Build": get("build"),
            "SIM": get("sim"),
            "Body other": get("bodyother")
        },
        "Display": {
            "Summary": get("Display"),
            "Type": get("displaytype"),
            "Size": get("displaysize"),
            "Resolution": get("displayresolution"),
            "Protection": get("displayprotection"),
            "Other": get("displayother")
        },
        "Platform": {
            "OS": get("OS") or get("os"),
            "Hardware": get("Hardware"),
            "Chipset": get("chipset"),
            "CPU": get("cpu"),
            "GPU": get("gpu")
        },
        "Memory": {
            "Summary": get("Storage"),
            "Internal": get("internalmemory"),
            "Card slot": get("memoryslot"),
            "Other": get("memoryother")
        },
        "Camera": {
            "Main": {
                "Modules": get("cam1modules"),
                "Features": get("cam1features"),
                "Video": get("cam1video")
            },
            "Selfie": {
                "Modules": get("cam2modules"),
                "Features": get("cam2features"),
                "Video": get("cam2video")
            }
        },
        "Comms": {
            "WLAN": get("wlan"),
            "Bluetooth": get("bluetooth"),
            "GPS": get("gps"),
            "NFC": get("nfc"),
            "Radio": get("radio"),
            "USB": get("usb")
        },
        "Features": {
            "Sensors": get("sensors"),
            "Other": get("featuresother")
        },
        "Battery": {
            "Summary": get("Battery"),
            "Description": get("batdescription1"),
            "Life": get("batlife2")
        },
        "Misc": {
            "URL": get("URL"),
            "Colors": get("colors"),
            "Models": get("models"),
            "Benchmark": get("tbench"),
            "SAR US": get("sar-us"),
            "SAR EU": get("sar-eu"),
            "Price": get("price")
        }
    }

    return processed


def main():
    print("📂 Loading raw data...")
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"Found {len(raw_data)} phones. Processing...")
    processed_data = [process_entry(p) for p in raw_data]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! Processed data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
