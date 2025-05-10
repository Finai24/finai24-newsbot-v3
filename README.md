# FinAI24 Newsbot 🤖📰

Bot automatizzato per FinAI24 che:
- Legge da feed RSS
- Classifica categoria con GPT-4
- Genera articoli originali
- Pubblica sul CMS Strapi

## Setup
1. Duplica `.env.example` in `.env` e inserisci le tue chiavi
2. Installa dipendenze: `pip install -r requirements.txt`
3. Avvia: `python finai24_newsbot.py`

## Deploy su Render
- Tipo: Cron Job
- Schedule: */10 * * * *
- Command: python finai24_newsbot.py
- Env Vars: OPENAI_API_KEY, STRAPI_API_TOKEN, MODELLO_OPENAI=gpt-4
