import os
import json
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SEEN_FILE = "seen_jobs.json"

KEYWORDS = ["Praktische Tätigkeit", "PT1", "PiA", "Psychologe in Ausbildung"]
REGIONS = ["Berlin", "Brandenburg"]

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

def search_jobs():
    seen = load_seen()
    new_found = False
    headers = {"X-API-Key": "jobboerse-jobsuche"}
    
    for region in REGIONS:
        for kw in KEYWORDS:
            params = {"was": kw, "wo": region, "size": 50}
            resp = requests.get("https://arbeitsagentur.de", headers=headers, params=params)
            if resp.status_code != 200:
                continue
            
            jobs = resp.json().get("stellenangebote", [])
            for job in jobs:
                ref_nr = job.get("refnr")
                titel = job.get("titel", "")
                arbeitgeber = job.get("arbeitgeber", "Unbekannt")
                ort = job.get("arbeitsort", {}).get("ort", region)
                
                check_text = (titel + " " + arbeitgeber).lower()
                if any(word in check_text for word in ["pt1", "pt 1", "praktische tätigkeit", "pia", "psychotherap", "psycholog"]):
                    if ref_nr and ref_nr not in seen:
                        seen.add(ref_nr)
                        new_found = True
                        link = f"https://arbeitsagentur.de{ref_nr}"
                        msg = f"🆕 <b>Neue PT1/PiA-Stelle gefunden!</b>\n\n<b>{titel}</b>\n🏥 {arbeitgeber}\n📍 {ort}\n🔗 <a href='{link}'>Zur Ausschreibung</a>"
                        send_telegram(msg)

    if new_found:
        save_seen(seen)

if __name__ == "__main__":
    search_jobs()
