import os
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()
SEEN_FILE = "seen_jobs.json"
S = chr(47)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}

def u(domain, path=""):
    return "https:" + S + S + domain + (S + path.replace("/", S) if path else "")

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_telegram(text):
    url = u("api.telegram.org", f"bot{TOKEN}/sendMessage")
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
    time.sleep(0.5)

def check_rss_feeds(seen):
    new_found = False
    queries = [
        '"Praktische Tätigkeit 1" Berlin OR Brandenburg',
        '"Praktische Tätigkeit 1" Wittenberg OR Dessau OR Magdeburg OR Neubrandenburg',
        '"PT1" Psychotherapie Berlin OR Brandenburg',
        '"PiA" Psychiatrie OR Psychosomatik Berlin OR Brandenburg',
        '"Plötzensee" OR "Justizvollzugskrankenhaus" Berlin Psychologe OR Psychologin OR PiA OR PT1',
        '"Justizvollzugsanstalt" OR "JVA" Berlin OR Brandenburg Psychologe OR Psychologin OR PiA OR PT1',
        '"Maßregelvollzug" OR "Forensische Psychiatrie" Berlin OR Brandenburg Psychologe OR Psychologin OR PiA OR PT1',
        '"Psychosomatik" Reha Psychologe OR Psychologin Berlin OR Brandenburg',
        '"Suchttherapie" OR "Suchtrehabilitation" Psychologe OR Psychologin Berlin OR Brandenburg',
        '"Psychologe" OR "Psychologin" Klinik Berlin OR Brandenburg Stellenangebot',
        '"M.Sc. Psychologie" Berlin OR Brandenburg Stellenangebot',
        '"Vivantes" OR "Charité" Psychologe OR Psychologin OR PiA OR PT1',
        '"Alexianer" OR "St. Joseph-Krankenhaus" OR "Hedwigshöhe" Berlin Psychologe OR Psychologin OR PiA OR PT1',
        '"Havelhöhe" OR "Theodor-Wenzel-Werk" Psychologe OR Psychologin OR PiA OR PT1',
        '"Jüdisches Krankenhaus" OR "KEH" OR "DRK Kliniken" Berlin Psychologe OR Psychologin OR PiA OR PT1',
        '"Oberberg" OR "Limes Schlossklinik" OR "Heiligenfeld" Berlin OR Brandenburg Psychologe OR Psychologin OR PiA',
        '"Ernst von Bergmann" Potsdam OR "Martin Gropius Krankenhaus" Psychologe OR Psychologin OR PiA OR PT1',
        '"Immanuel Klinik Rüdersdorf" OR "Asklepios" Brandenburg OR Teupitz OR Lübben Psychologe OR Psychologin OR PiA OR PT1',
        '"Ruppiner Kliniken" OR "Havelland Kliniken" OR "Oberhavel Kliniken" Psychologe OR Psychologin OR PiA OR PT1',
        '"MEDIAN Klinik" OR "Salus Klinik Lindow" OR "Fontane-Klinik" OR "Tannenhof" Psychologe OR Psychologin OR PiA',
        '"Klinik Bosse Wittenberg" OR "Salus" Uchtspringe OR "Dietrich-Bonhoeffer-Klinikum" Psychologe OR Psychologin OR PiA'
    ]
    for q in queries:
        eq = urllib.parse.quote(q)
        feeds = [
            u("://google.com", f"rss/search?q={eq}&hl=de&gl=DE&ceid=DE:de"),
            u("://bing.com", f"news/search?q={eq}&format=rss")
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
                        send_telegram(f"🆕 <b>Neuer Stellen-Treffer!</b>\n\n<b>{title}</b>\n🔗 <a href='{link}'>Zur Ausschreibung</a>")
            except Exception:
                continue
    return new_found

def check_clinics(seen):
    new_found = False
    clinic_pages = [
        ("Alexianer Verbund (St. Hedwig, Hedwigshöhe, Weißensee)", u("www.alexianer.de", "karriere/stellenangebote")),
        ("Alexianer Berlin-Weißensee (St. Joseph)", u("www.alexianer-berlin-weissensee.de", "karriere/stellenangebote")),
        ("Alexianer Berlin-Hedwigkliniken", u("www.alexianer-berlin-hedwigkliniken.de", "karriere/stellenangebote")),
        ("Gemeinschaftskrankenhaus Havelhöhe", u("www.havelhoehe.de", "karriere/stellenangebote.html")),
        ("Limes Schlosskliniken (Fürstenwalde)", u("www.limes-schlosskliniken.de", "karriere/")),
        ("Heiligenfeld Kliniken (Berlin-Spandau)", u("www.heiligenfeld.de", "karriere/stellenangebote/")),
        ("Oberberg Kliniken (Karriereportal)", u("www.oberbergkliniken.de", "karriere")),
        ("Oberberg Kliniken (Stellenangebote)", u("www.oberbergkliniken.de", "karriere/stellenangebote")),
        ("Park-Klinik Sophie Charlotte", u("www.parkklinik-sophie-charlotte.de", "karriere/")),
        ("Schlosspark-Klinik Berlin", u("www.schlosspark-klinik.de", "karriere/stellenangebote/")),
        ("Reha-Zentrum Seehof Teltow", u("www.reha-klinik-seehof.de", "DE/Karriere/karriere_node.html")),
        ("Brandenburg Klinik Bernau-Waldsiedlung", u("www.brandenburgklinik.de", "karriere/stellenangebote/")),
        ("Rehaklinik Hoher Fläming Bad Belzig", u("www.rehaklinik-hoher-flaeming.de", "karriere/")),
        ("Heinrich-Heine-Klinik Potsdam", u("www.heinrich-heine-klinik.de", "karriere/")),
        ("Klinik am See Rüdersdorf", u("://klinikamsee.com", "karriere/stellenangebote/")),
        ("Sana Kliniken Sommerfeld", u("www.sana.de", "sommerfeld/karriere")),
        ("MEDIAN Kliniken (Kladow, Grünheide, Hoppegarten)", u("www.median-kliniken.de", "de/karriere/stellenangebote/")),
        ("Salus Klinik Lindow", u("www.salus-lindow.de", "karriere/stellenangebote/")),
        ("Fontane-Klinik Motzen", u("www.fontane-klinik.de", "karriere/")),
        ("Tannenhof Berlin-Brandenburg", u("www.tannenhof.de", "jobs-karriere/")),
        ("Fachklinik LAGO am Wannsee (DTZ)", u("www.berlin-suchthilfe.de", "karriere")),
        ("JVA Plötzensee & Justizvollzug Berlin", u("www.berlin.de", "justizvollzug/karriere/")),
        ("Krankenhaus des Maßregelvollzugs Berlin (KMV)", u("www.berlin.de", "kmv/aktuelles/karriere/")),
        ("Karriereportal Land Berlin (Justiz & KMV)", u("www.karriereportal-stellen.berlin.de", "")),
        ("Institut für Forensische Psychiatrie (Charité)", u("forensik.charite.de", "ueber_das_institut/karriere/")),
        ("Justizvollzug Brandenburg (JVA)", u("mdj.brandenburg.de", "mdj/de/karriere/justizvollzug/")),
        ("Vivantes (alle Standorte)", u("karriere.vivantes.de", "jobs/")),
        ("Charité Berlin", u("karriere.charite.de", "stellenangebote")),
        ("Jüdisches Krankenhaus Berlin", u("www.juedisches-krankenhaus.de", "karriere/stellenangebote.html")),
        ("Ev. Krankenhaus Königin Elisabeth Herzberge (KEH)", u("www.keh-berlin.de", "de/karriere/stellenangebote")),
        ("DRK Kliniken Berlin", u("karriere.drk-kliniken-berlin.de", "stellenangebote/")),
        ("St. Joseph Krankenhaus Berlin (Tempelhof)", u("www.sjk.de", "karriere/stellenangebote/")),
        ("Helios Kliniken Berlin", u("www.helios-gesundheit.de", "karriere/jobs/")),
        ("Theodor-Wenzel-Werk (Therapie)", u("www.tww-berlin.de", "jobs/stellenangebote/therapeutische-berufe/")),
        ("Theodor-Wenzel-Werk (Gesamt)", u("www.tww-berlin.de", "jobs/stellenangebote/")),
        ("Klinikum Ernst von Bergmann Potsdam", u("karriere.evb-gesundheit.de", "jobs")),
        ("Martin Gropius Krankenhaus Eberswalde & Wolletzsee (GLG)", u("www.glg-karriere.de", "stellenangebote")),
        ("Immanuel Klinik Rüdersdorf", u("immanuelalbertinen.de", "karriere/stellenangebote/")),
        ("Asklepios Fachkliniken (Brandenburg/Teupitz/Lübben/Pasewalk)", u("://asklepios.com", "karriere/stellenangebote/")),
        ("Universitätsklinikum Ruppin-Brandenburg (ukrb)", u("karriere.ruppiner-kliniken.de", "")),
        ("Havelland Kliniken (Klinik Nauen)", u("www.havelland-kliniken.de", "Karriere/Stellenangebote/")),
        ("Oberhavel Kliniken (Klinik Hennigsdorf)", u("www.oberhavel-kliniken.de", "karriere/stellenangebote.html")),
        ("Johanniter-Krankenhaus Treuenbrietzen", u("www.johanniter.de", "johanniter-kliniken/johanniter-krankenhaus-im-flaeming-treuenbrietzen/karriere/")),
        ("Klinikum Frankfurt (Oder)", u("www.klinikumffo.de", "karriere/stellenangebote")),
        ("Medizinische Universität Lausitz Cottbus (MUL-CT)", u("karriere.mul-ct.de", "")),
        ("Alexianer Sachsen-Anhalt (Wittenberg & Dessau)", u("www.alexianer-sachsen-anhalt.de", "karriere/stellenangebote")),
        ("Salus Sachsen-Anhalt (Uchtspringe & Bernburg)", u("www.salus-lsa.de", "karriere/stellenangebote/")),
        ("Klinikum Magdeburg", u("www.klinikum-magdeburg.de", "karriere/stellenangebote/")),
        ("Universitätsmedizin Magdeburg", u("www.med.uni-magdeburg.de", "karriere/")),
        ("AWO Fachkrankenhaus Jerichow", u("www.awo-sachsen-anhalt.de", "karriere/")),
        ("Dietrich-Bonhoeffer-Klinikum (Neubrandenburg & Neustrelitz)", u("dbknb.de", "karriere/stellenangebote")),
        ("Elblandkliniken Sachsen (Riesa)", u("www.elblandkliniken.de", "karriere/stellenangebote/")),
        ("Lausitzer Seenland Klinikum Hoyerswerda", u("www.sana.de", "seenlandklinikum/karriere"))
    ]
    keywords = [
        "praktische tätigkeit", "pt1", "pt 1", "pt i", "pia",
        "psychotherapeut in ausbildung", "psychologin in ausbildung", "psychologe in ausbildung",
        "psychologe", "psychologin", "psycholog*in", "psycholog:in",
        "m.sc. psychologie", "klinischer psychologe", "klinische psychologin",
        "forensisch", "maßregelvollzug", "justizvollzug", "suchttherapeut", "suchttherapie",
        "psychosomatik", "psychosomatisch"
    ]

