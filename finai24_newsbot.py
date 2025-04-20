import openai
import feedparser
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRAPI_API_TOKEN = os.getenv("STRAPI_API_TOKEN")
STRAPI_API_URL = "https://finai24-cms.onrender.com/api/articoli"
ARCHIVIO_FILE = "pubblicati.json"
FEED_LIST = "feeds.txt"
openai.api_key = OPENAI_API_KEY

def carica_storico():
    if os.path.exists(ARCHIVIO_FILE):
        with open(ARCHIVIO_FILE, "r") as f:
            return json.load(f)
    return []

def salva_storico(storia):
    with open(ARCHIVIO_FILE, "w") as f:
        json.dump(storia, f, indent=2)

def pulizia_storico(storia, giorni=60):
    cutoff = datetime.now(timezone.utc) - timedelta(days=giorni)
    return [s for s in storia if datetime.fromisoformat(s["timestamp"]) > cutoff]

def estrai_feed(feed_url):
    feed = feedparser.parse(feed_url)
    return feed.entries

def classifica_categoria(titolo, descrizione):
    prompt = f"""
Titolo: {titolo}
Descrizione: {descrizione}

In base al contenuto, assegna una e una sola categoria tra le seguenti:

macro, mercati, geopolitica, criptovalute, tecnologia, bancario-finanziario, energia, commodities, startup, altro

Rispondi solo con il nome della categoria, in minuscolo, senza spiegazioni.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Sei un assistente editoriale che classifica articoli per un sito di notizie finanziarie."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip().lower()

def genera_articolo(titolo, descrizione, link):
    prompt = f"""
Scrivi un articolo originale in stile giornalistico (~300-400 parole), basato su questa notizia:

Titolo: {titolo}
Descrizione: {descrizione}
Fonte: {link}

Scrivi con tono autorevole, dividi in paragrafi, e chiudi con un link alla fonte. Aggiungi una nota che l'articolo è stato generato da AI.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Sei un giornalista finanziario AI."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def pubblica_articolo(titolo, contenuto, fonte_url, categoria):
    headers = {
        "Authorization": f"Bearer {STRAPI_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "titolo": titolo,
            "contenuto": contenuto,
            "fonte": fonte_url,
            "categoria": categoria,
            "autore": "FinAI24 Newsbot",
            "publishedAt": datetime.now(timezone.utc).isoformat()
        }
    }
    response = requests.post(STRAPI_API_URL, headers=headers, json=payload)
    return response.status_code, response.text

def main():
    storico = carica_storico()
    storico = pulizia_storico(storico)

    with open(FEED_LIST, "r") as f:
        feed_urls = [line.strip() for line in f.readlines() if line.strip()]

    nuovi = 0
    for url in feed_urls:
        notizie = estrai_feed(url)
        for voce in notizie:
            titolo = voce.title
            link = voce.link
            if any(link == item["link"] for item in storico):
                continue

            descrizione = voce.get("summary", "")
            try:
                categoria = classifica_categoria(titolo, descrizione)
                articolo = genera_articolo(titolo, descrizione, link)
                status, resp = pubblica_articolo(titolo, articolo, link, categoria)
                print(f"✅ Pubblicato: {titolo} | Categoria: {categoria} | Status: {status}")
                storico.append({"link": link, "timestamp": datetime.now(timezone.utc).isoformat()})
                nuovi += 1
            except Exception as e:
                print(f"❌ Errore con '{titolo}': {e}")

    salva_storico(storico)
    print(f"🔁 Operazione completata. Nuovi articoli pubblicati: {nuovi}")

if __name__ == "__main__":
    main()
