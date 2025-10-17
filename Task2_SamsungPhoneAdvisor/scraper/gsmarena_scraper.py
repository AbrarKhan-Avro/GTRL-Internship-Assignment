import json
import time
import random
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE_URL = "https://www.gsmarena.com/"
SAMSUNG_URL = "https://www.gsmarena.com/samsung-phones-9.php"

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"},
]

OUTPUT_FILE = Path("data/samsung_phones.json")
DATA = []

def get_soup(url):
    headers = random.choice(HEADERS_LIST)
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200:
            return BeautifulSoup(res.text, "lxml")
        else:
            print(f"⚠️ HTTP {res.status_code} for {url}")
            return None
    except requests.RequestException as e:
        print(f"⚠️ Request error for {url}: {e}")
        return None

def scrape_phone(url):
    soup = get_soup(url)
    if not soup:
        return None

    specs = {"URL": url}
    specs["Name"] = soup.find("h1").get_text(strip=True) if soup.find("h1") else "N/A"

    # Quick key specs
    for key, spec in {
        "Release date": "released-hl",
        "Weight": "body-hl",
        "OS": "os-hl",
        "Storage": "storage-hl"
    }.items():
        tag = soup.find("span", {"data-spec": spec})
        specs[key] = tag.text.strip() if tag else "N/A"

    # Battery, Display, RAM, SoC
    for label, cls in {
        "Battery": "help-battery",
        "Display": "help-display",
        "Hardware": "help-expansion"
    }.items():
        li = soup.find("li", {"class": cls})
        if li:
            specs[label] = " ".join([t.strip() for t in li.stripped_strings][2:])
        else:
            specs[label] = "N/A"

    # All <td class="nfo">
    for td in soup.find_all("td", {"class": "nfo"}):
        data_spec = td.get("data-spec", "")
        value = " ".join(td.stripped_strings)
        if data_spec:
            specs[data_spec] = value

    return specs

def main():
    print("Fetching Samsung phone list...")
    soup = get_soup(SAMSUNG_URL)
    phone_links = [
        BASE_URL + a["href"]
        for a in soup.select("div.makers a")
        if a.get("href")
    ]
    print(f"Found {len(phone_links)} Samsung phones.")

    for i, url in enumerate(phone_links, 1):
        print(f"[{i}/{len(phone_links)}] Scraping {url}")
        data = scrape_phone(url)
        if data:
            DATA.append(data)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(DATA, f, ensure_ascii=False, indent=2)

        sleep_time = random.uniform(5, 15)
        if i % 10 == 0:
            sleep_time += random.uniform(20, 60)
        print(f"Sleeping for {sleep_time:.1f}s...")
        time.sleep(sleep_time)

    print(f"✅ Done. Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
