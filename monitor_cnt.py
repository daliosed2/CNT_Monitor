# -*- coding: utf-8 -*-
"""
CNT Monitor: avisa cuando aparece un PDF nuevo en https://www.cnt.com.ec/repositorio-legal
• Envía alerta al webhook de Discord (UTF-8 completo).
DEPENDENCIAS:
    pip install requests beautifulsoup4 python-dotenv
VARIABLE .env (misma carpeta):
    DISCORD_WEBHOOK=https://discord.com/api/webhooks/XXXXXXXX
"""

import json, os, re, requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

URL          = "https://www.cnt.com.ec/repositorio-legal"
STATE_FILE   = Path("cnt_docs.json")

load_dotenv()
WEBHOOK = os.getenv("DISCORD_WEBHOOK", "").strip()

def obtener_documentos():
    html  = requests.get(URL, timeout=20).text
    soup  = BeautifulSoup(html, "html.parser")
    arts  = soup.find_all("article")
    docs  = []
    for art in arts:
        a = art.find("a", href=True)
        if not a:
            continue
        href  = a["href"].strip()
        title = " ".join(a.stripped_strings)
        docs.append({"id": href, "titulo": title, "url": href})
    return docs

def cargar_estado():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else []

def guardar_estado(lista):
    STATE_FILE.write_text(json.dumps(lista, ensure_ascii=False, indent=2))

def notify(text:str):
    ts = datetime.now().strftime("[%d/%m %H:%M] ")
    print(ts + text)                                 # consola
    if WEBHOOK:
        requests.post(WEBHOOK, json={"content": text}, timeout=10)

def run_once():
    conocidos = {d["id"] for d in cargar_estado()}
    notify(f"Monitor CNT iniciado. PDFs conocidos: {len(conocidos)}")
    nuevos = []
    for d in obtener_documentos():
        if d["id"] not in conocidos:
            nuevos.append(d)
            conocidos.add(d["id"])
            notify(f"📄 Nuevo PDF: {d['titulo']}\n{d['url']}")
    if nuevos:
        guardar_estado([{"id": id_} for id_ in conocidos])
    else:
        notify("Sin novedades en esta pasada")

if __name__ == "__main__":
    run_once()
