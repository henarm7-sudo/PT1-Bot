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
        # PT1 & PiA allgemein
        '"Praktische Tätigkeit 1" Berlin OR Brandenburg',
        '"Praktische Tätigkeit 1" Wittenberg OR Dessau OR Magdeburg OR Neubrandenburg',
        '"PT1" Psychotherapie Berlin OR Brandenburg',
        '"PiA" Psychiatrie OR Psychosomatik Berlin OR Brandenburg',
        # Alexianer, Havelhöhe & Privatkliniken
        '"Alexianer" Berlin Psychologe OR Psychologin OR PiA OR PT1',
        '"St. Joseph-Krankenhaus" Weißensee Psychologe OR Psychologin OR PiA OR PT1',
        '"Krankenhaus Hedwigshöhe" Psychologe OR Psychologin OR PiA OR PT1',
        '"St. Hedwig-Krankenhaus" Psychologe OR Psychologin OR PiA OR PT1',
        '"Havelhöhe" Psychologe OR Psychologin OR PiA OR PT1',
        '"Limes Schlossklinik" Fürstenwalde Psychologe OR Psychologin OR PiA',
        '"Heiligenfeld" Berlin Psychologe OR Psychologin OR PiA',
        '"Privatklinik" Psychiatrie OR Psychosomatik Psychologe OR Psychologin Berlin OR Brandenburg',
        # Forensik, Maßregelvollzug & Justizvollzug
        '"Plötzensee" Psychologe OR Psychologin OR PiA OR PT1',
        '"Justizvollzugskrankenhaus" Berlin Psychologe OR Psychologin OR PiA OR PT1',
        '"Justizvollzugsanstalt" OR "JVA" Berlin OR Brandenburg Psychologe OR Psychologin OR PiA OR PT1',
        '"Maßregelvollzug" Berlin OR Brandenburg Psychologe OR Psychologin OR PiA OR PT1',
        '"Forensische Psychiatrie" Berlin OR Brandenburg OR Uchtspringe Psychologe OR Psychologin OR PiA OR PT1',
        # Psychosomatik-Rehas & Stationäre Suchttherapie
        '"Psychosomatik" Reha Psychologe OR Psychologin Berlin OR Brandenburg',
        '"Rehaklinik Hoher Fläming" Bad Belzig Psychologe OR Psychologin OR PiA',
        '"Heinrich-Heine-Klinik" Potsdam Psychologe OR Psychologin OR PiA',
        '"Klinik am See" Rüdersdorf Psychologe OR Psychologin OR PiA',
        '"Fachklinik Wolletzsee" Angermünde Psychologe OR Psychologin OR PiA',
        '"Reha-Zentrum Seehof" Teltow Psychologe OR Psychologin OR PiA',
        '"Suchttherapie" OR "Suchtrehabilitation" Psychologe OR Psychologin Berlin OR Brandenburg',
        '"MEDIAN Klinik" Berlin OR Grünheide OR Hoppegarten Psychologe OR Psychologin OR PiA',
        '"Salus Klinik Lindow" Psychologe OR Psychologin OR PiA',
        '"Fontane-Klinik" Motzen Psychologe OR Psychologin OR PiA',
        '"Tannenhof Berlin-Brandenburg" Psychologe OR Psychologin OR PiA',
        # Reguläre Psychologen-Stellen allgemein
        '"Psychologe" OR "Psychologin" Klinik Berlin Stellenangebot',
        '"Psychologe" OR "Psychologin" Klinik Brandenburg Stellenangebot',
        '"M.Sc. Psychologie" Berlin OR Brandenburg Stellenangebot',
        # Weitere Berliner & Brandenburger Kliniken
        '"Vivantes" Psychologe OR Psychologin OR PiA OR PT1',
        '"Charité" Psychologe OR Psychologin OR PiA OR PT1',
        '"Theodor-Wenzel-Werk" Psychologe OR Psychologin OR PiA OR PT1',
        '"LAGO" Wannsee OR "Drogentherapie-Zentrum" Psychologe OR Psychologin OR PiA',
        '"Jüdisches Krankenhaus" Berlin Psychologe OR Psychologin OR PiA OR PT1',
        '"Königin Elisabeth Herzberge" OR "KEH" Psychologe OR Psychologin OR PiA OR PT1',
        '"Park-Klinik Sophie Charlotte" Psychologe OR Psychologin OR PiA OR PT1',
        '"DRK Kliniken Berlin" Psychologe OR Psychologin OR PiA OR PT1',
        '"St. Joseph Krankenhaus" Tempelhof Psychologe OR Psychologin OR PiA OR PT1',
        '"Helios" Berlin-Buch OR "Emil von Behring" Psychologe OR Psychologin OR PiA OR PT1',
        '"Schlosspark-Klinik" Berlin Psychologe OR Psychologin OR PiA OR PT1',
        '"Ernst von Bergmann" Potsdam Psychologe OR Psychologin OR PiA OR PT1',
        '"Oberberg" Berlin OR Brandenburg OR Potsdam OR "Wendisch Rietz" Psychologe OR Psychologin OR PiA OR PT1',
        '"Martin Gropius Krankenhaus" OR "GLG" Psychologe OR Psychologin OR PiA OR PT1',
        '"Immanuel Klinik Rüdersdorf" Psychologe OR Psychologin OR PiA OR PT1',
        '"Asklepios" Brandenburg OR Teupitz OR Lübben OR Pasewalk Psychologe OR Psychologin OR PiA OR PT1',
        '"Ruppiner Kliniken" OR "Universitätsklinikum Ruppin" Psychologe OR Psychologin OR PiA OR PT1',
        '"Havelland Kliniken" Nauen Psychologe OR Psychologin OR PiA OR PT1',
        '"Oberhavel Kliniken" Hennigsdorf Psychologe OR Psychologin OR PiA OR PT1',
        '"Johanniter" Treuenbrietzen Psychologe OR Psychologin OR PiA OR PT1',
        '"Carl Thiem" OR "MUL-CT" Cottbus Psychologe OR Psychologin OR PiA OR PT1',
        '"Klinikum Frankfurt (Oder)" Psychologe OR Psychologin OR PiA OR PT1',
        '"Klinik Bosse Wittenberg" OR "St. Joseph-Krankenhaus Dessau" Psychologe OR Psychologin OR PiA OR PT1',
        '"Salus" Uchtspringe OR Bernburg Psychologe OR Psychologin OR PiA OR PT1',
        '"Dietrich-Bonhoeffer-Klinikum" Neubrandenburg OR Neustrelitz Psychologe OR Psychologin OR PiA OR PT1',
        '"Elblandkliniken" Riesa Psychologe OR Psychologin OR PiA OR PT1',
        '"Seenland Klinikum" Hoyerswerda Psychologe OR Psychologin OR PiA OR PT1'
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
                        msg = f"🆕 <b>Neuer Stellen-Treffer!</b>\n\n<b>{title}</b>\n🔗 <a href='{link}'>Zur Ausschreibung</a>"
                        send_telegram(msg)
            except Exception as e:
                print("Feed Fehler:", e)
                continue
    return new_found

def check_clinics(seen):
    new_found = False
    clinic_pages = [
        # Alexianer, Havelhöhe & Privatkliniken
        ("Alexianer Karriere (St. Hedwig, Hedwigshöhe, Weißensee)", "https:" + SLASH + SLASH + "www.alexianer.de" + SLASH + "karriere" + SLASH + "stellenangebote"),
        ("Alexianer Berlin-Weißensee (St. Joseph)", "https:" + SLASH + SLASH + "www.alexianer-berlin-weissensee.de" + SLASH + "karriere" + SLASH + "stellenangebote"),
        ("Alexianer Berlin-Hedwigkliniken", "https:" + SLASH + SLASH + "www.alexianer-berlin-hedwigkliniken.de" + SLASH + "karriere" + SLASH + "stellenangebote"),
        ("Gemeinschaftskrankenhaus Havelhöhe", "https:" + SLASH + SLASH + "www.havelhoehe.de" + SLASH + "karriere" + SLASH + "stellenangebote.html"),
        ("Limes Schlosskliniken (Fürstenwalde)", "https:" + SLASH + SLASH + "www.limes-schlosskliniken.de" + SLASH + "karriere" + SLASH),
        ("Heiligenfeld Kliniken (Berlin-Spandau)", "https:" + SLASH + SLASH + "www.heiligenfeld.de" + SLASH + "karriere" + SLASH + "stellenangebote" + SLASH),
        ("Oberberg Kliniken (Karriereportal)", "https:" + SLASH + SLASH + "www.oberbergkliniken.de" + SLASH + "karriere"),
        ("Oberberg Kliniken (Stellenangebote)", "https:" + SLASH + SLASH + "www.oberbergkliniken.de" + SLASH + "karriere" + SLASH + "stellenangebote"),
        ("Park-Klinik Sophie Charlotte (Privatklinik)", "https:" + SLASH + SLASH + "www.parkklinik-sophie-charlotte.de" + SLASH + "karriere" + SLASH),
        ("Schlosspark-Klinik Berlin", "https:" + SLASH + SLASH + "www.schlosspark-klinik.de" + SLASH + "karriere" + SLASH + "stellenangebote" + SLASH),
        # Psychosomatik-Rehas & Sucht-Rehas
        ("Reha-Zentrum Seehof Teltow (DRV Bund)", "https:" + SLASH + SLASH + "www.reha-klinik-seehof.de" + SLASH + "DE" + SLASH + "Karriere" + SLASH + "karriere_node.html"),
        ("Brandenburg Klinik Bernau-Waldsiedlung", "https:" + SLASH + SLASH + "www.brandenburgklinik.de" + SLASH + "karriere" + SLASH + "stellenangebote" + SLASH),
        ("Rehaklinik Hoher Fläming Bad Belzig", "https:" + SLASH + SLASH + "www.rehaklinik-hoher-flaeming.de" + SLASH + "karriere" + SLASH),
        ("Heinrich-Heine-Klinik Potsdam (Psychosomatik)", "https:" + SLASH + SLASH + "www.heinrich-heine-klinik.de" + SLASH + "karriere" + SLASH),
        ("Klinik am See Rüdersdorf (Psychosomatik)", "https:" + SLASH + SLASH + "://klinikamsee.com" + SLASH + "karriere" + SLASH + "stellenangebote" + SLASH),
        ("Fachklinik Wolletzsee Angermünde (GLG)", "https:" + SLASH + SLASH + "www.glg-karriere.de" + SLASH + "stellenangebote"),





