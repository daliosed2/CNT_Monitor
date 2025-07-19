# -*- coding: utf-8 -*-
"""
CNT Monitor – avisa a Discord cuando aparece un nuevo PDF entre los 10 más recientes
DEPENDENCIAS:
    pip install requests beautifulsoup4 python-dotenv
ARCHIVO .env:
    DISCORD_WEBHOOK=https://discord.com/api/webhooks/XXXXXXXX
"""

import json, os, re, requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

URL        = "https://www.cnt.com.ec/repositorio-legal"
STATE_FILE = Path("cnt_docs.json")

load_dotenv()
WEBHOOK = os.getenv("DISCORD_WEBHOOK", "").strip()

def obtener_documentos():
    html = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0 CNTMonitor/1.0"},
        timeout=30
    ).text
    soup = BeautifulSoup(html, "html.parser")
    docs = []
    for art in soup.find_all("article"):
        a = art.find("a", href=True)
        if not a:
            continue
        href  = a["href"].strip()
        title = " ".join(a.stripped_strings)
        docs.append({"id": href, "titulo": title, "url": href})
    return docs[:10]   # 👈 solo los 10 primeros

def cargar_estado():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else []

def guardar_estado(ids):
    STATE_FILE.write_text(json.dumps(list(ids), indent=2, ensure_ascii=False))

def notify(txt:str):
    ts = datetime.now().strftime("[%d/%m %H:%M] ")
    print(ts + re.sub(r"[^\x00-\x7F]", " ", txt))
    if WEBHOOK:
        requests.post(WEBHOOK, json={"content": txt}, timeout=10)

def run_once():
    conocidos = set(cargar_estado())
    notify(f"CNT Monitor: {len(conocidos)} PDFs conocidos (top-10 lógica)")
    nuevos = []
    for d in obtener_documentos():
        if d["id"] not in conocidos:
            nuevos.append(d)
            conocidos.add(d["id"])
            notify(f"📄 Nuevo PDF: {d['titulo']}\n{d['url']}")
    if nuevos:
        guardar_estado(conocidos)
    else:
        notify("Sin novedades en esta pasada")

if __name__ == "__main__":
    run_once()
