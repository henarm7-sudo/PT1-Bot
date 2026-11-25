import os
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SEEN_FILE = "seen_jobs.json"

KEYWORDS = ["Praktische Tätigkeit", "PT1", "PiA", "Psychologe in Ausbildung"]
REGIONS = ["Berlin", "Brandenburg"]

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "X-API-Key": "jobboerse-jobsuche"
}

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_telegram(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
    time.sleep(0.5)

def check_arbeitsagentur(seen):
    new_found = False
    for region in REGIONS:
        for kw in KEYWORDS:
            try:
                params = {"was": kw, "wo": region, "size": 50}
                resp = requests.get(
                    "https://arbeitsagentur.de",
                    headers=BROWSER_HEADERS,
                    params=params,
                    timeout=15
                )
                if resp.status_code != 200 or not resp.text.strip():
                    continue
                data = resp.json()
            except Exception:
                continue

            for job in data.get("stellenangebote", []):
                ref_nr = job.get("refnr")
                titel = job.get("titel", "")
                arbeitgeber = job.get("arbeitgeber", "Unbekannt")
                ort = job.get("arbeitsort", {}).get("ort", region)

                check_text = (titel + " " + arbeitgeber).lower()
                if any(w in check_text for w in ["pt1", "pt 1", "praktische tätigkeit", "pia", "psychotherap", "psycholog"]):
                    if ref_nr and ref_nr not in seen:
                        seen.add(ref_nr)
                        new_found = True
                        link = f"https://arbeitsagentur.de{ref_nr}"
                        msg = f"🆕 <b>Neue PT1/PiA-Stelle (Arbeitsagentur)!</b>\n\n<b>{titel}</b>\n🏥 {arbeitgeber}\n📍 {ort}\n🔗 <a href='{link}'>Zur Ausschreibung</a>"
                        send_telegram(msg)
    return new_found

def check_web_feeds(seen):
    new_found = False
    queries = [
        '"Praktische Tätigkeit 1" Berlin OR Brandenburg',
        '"PT1" Psychotherapie Berlin OR Brandenburg',
        '"PiA" Psychiatrie Berlin OR Brandenburg'
    ]
    for q in queries:
        try:
            url = f"https://google.com{urllib.parse.quote(q)}&hl=de&gl=DE&ceid=DE:de"
            resp = requests.get(url, headers={"User-Agent": BROWSER_HEADERS["User-Agent"]}, timeout=15)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:10]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                guid = item.findtext("guid", link)
                if guid and guid not in seen:
                    seen.add(guid)
                    new_found = True
                    msg = f"🌐 <b>Neuer Web-Treffer (PT1/PiA)!</b>\n\n<b>{title}</b>\n🔗 <a href='{link}'>Zum Beitrag / zur Seite</a>"
                    send_telegram(msg)
        except Exception:
            continue
    return new_found

def search_jobs():
    seen = load_seen()
    found_aa = check_arbeitsagentur(seen)
    found_web = check_web_feeds(seen)
    if found_aa or found_web:
        save_seen(seen)

if __name__ == "__main__":
    search_jobs()

