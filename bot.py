import os
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()
SEEN_FILE = "seen_jobs.json"

SLASH = chr(47)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
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
    url = "https:" + SLASH + SLASH + "api.telegram.org" + SLASH + "bot" + TOKEN + SLASH + "sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
    print("Telegram Antwort:", r.status_code, r.text)
    time.sleep(0.5)

def check_rss_feeds(seen):
    new_found = False
    queries = [
        '"Praktische Tätigkeit 1" Berlin',
        '"Praktische Tätigkeit 1" Brandenburg',
        '"PT1" Psychotherapie Berlin',
        '"PT1" Psychotherapie Brandenburg',
        '"PiA" Psychiatrie Berlin',
        '"PiA" Psychiatrie Brandenburg',
        '"Psychologe in Ausbildung" Berlin'
    ]
    
    for q in queries:
        encoded_q = urllib.parse.quote(q)
        feeds = [
            "https:" + SLASH + SLASH + "://google.com" + SLASH + "rss" + SLASH + "search?q=" + encoded_q + "&hl=de&gl=DE&ceid=DE:de",
            "https:" + SLASH + SLASH + "://bing.com" + SLASH + "news" + SLASH + "search?q=" + encoded_q + "&format=rss"
        ]
        for feed_url in feeds:
            try:
                resp = requests.get(feed_url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item")[:5]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    guid = item.findtext("guid", link)
                    if guid and guid not in seen:
                        seen.add(guid)
                        new_found = True
                        msg = f"🆕 <b>Neuer PT1/PiA-Treffer!</b>\n\n<b>{title}</b>\n🔗 <a href='{link}'>Zur Ausschreibung</a>"
                        send_telegram(msg)
            except Exception as e:
                print("Feed Fehler:", e)
                continue
    return new_found

def check_clinics(seen):
    new_found = False
    clinic_pages = [
        ("Vivantes Karriere", "https:" + SLASH + SLASH + "karriere.vivantes.de" + SLASH + "stellenangebote"),
        ("Charité Karriere", "https:" + SLASH + SLASH + "karriere.charite.de" + SLASH + "stellenangebote"),
        ("Alexianer Karriere", "https:" + SLASH + SLASH + "www.alexianer.de" + SLASH + "karriere" + SLASH + "stellenangebote"),
        ("Oberberg Kliniken", "https:" + SLASH + SLASH + "www.oberbergkliniken.de" + SLASH + "karriere" + SLASH + "stellenangebote"),
        ("Theodor-Wenzel-Werk", "https:" + SLASH + SLASH + "www.tww-berlin.de" + SLASH + "karriere" + SLASH + "stellenangebote"),
        ("Klinikum Ernst von Bergmann", "https:" + SLASH + SLASH + "www.evb-gesundheit.de" + SLASH + "karriere" + SLASH + "stellenangebote")
    ]
    keywords = ["praktische tätigkeit", "pt1", "pt 1", "pia", "psychotherapeut in ausbildung", "psychologin in ausbildung", "psychologe in ausbildung"]

    for name, url in clinic_pages:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                html_lower = resp.text.lower()
                for kw in keywords:
                    if kw in html_lower:
                        key = f"{name}:{kw}"
                        if key not in seen:
                            seen.add(key)
                            new_found = True
                            msg = f"🏥 <b>Klinik-Treffer bei {name}!</b>\nAuf der Karriereseite wurde das Stichwort <b>„{kw}“</b> gefunden.\n🔗 <a href='{url}'>Direkt zur Klinik-Jobbörse</a>"
                            send_telegram(msg)
                        break
        except Exception as e:
            print(f"Klinik Fehler ({name}):", e)
    return new_found

def search_jobs():
    seen = load_seen()
    is_first_run = len(seen) == 0

    found_rss = check_rss_feeds(seen)
    found_clinics = check_clinics(seen)

    if is_first_run:
        send_telegram("✅ <b>Verbindung steht!</b> Dein PT1-Bot für Berlin & Brandenburg ist jetzt aktiv und meldet dir ab sofort neue Treffer.")

    if found_rss or found_clinics:
        save_seen(seen)

if __name__ == "__main__":
    search_jobs()




