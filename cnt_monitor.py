# -*- coding: utf-8 -*-
"""
CNT Monitor  —  Notifica a Discord cuando aparece un PDF nuevo (top-10 más recientes)

DEPENDENCIAS:
    pip install requests beautifulsoup4 python-dotenv

ARCHIVO .env (o secreto en GitHub Actions):
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/XXXXXXXX
"""

import calendar
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv

# ───────── CONFIG ─────────
URL        = "https://www.cnt.com.ec/repositorio-legal"
STATE_FILE = Path("cnt_docs.json")          # guarda IDs ya notificados

load_dotenv()
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

# ───────── UTIL: extraer fecha del título/URL ─────────
MES_ABR = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
MES_NOM = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
P_FULL      = re.compile(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})')   # 07-07-2025
P_MES_AÑO   = re.compile(r'([A-Za-z]{3,9})\s+(\d{4})')           # JUN 2025
P_AÑO       = re.compile(r'(\d{4})')

def extraer_fecha(txt: str) -> datetime:
    if m := P_FULL.search(txt):
        d, mth, a = map(int, m.groups())
        return datetime(a, mth, d)
    if m := P_MES_AÑO.search(txt):
        mes, a = m.groups()
        idx = MES_ABR.get(mes.lower()) or MES_NOM.get(mes.lower()) or 1
        return datetime(int(a), idx, 1)
    if m := P_AÑO.search(txt):
        return datetime(int(m.group(1)), 1, 1)
    return datetime(1900, 1, 1)   # muy antiguo si no hay fecha

# ───────── SCRAPING (devuelve top-10 por fecha) ─────────
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
        fecha = extraer_fecha(title + " " + href)
        docs.append({"id": href, "titulo": title, "url": href, "fecha": fecha})
    docs.sort(key=lambda d: d["fecha"], reverse=True)
    return docs[:10]     # solo los 10 más recientes

# ───────── ESTADO LOCAL ─────────
def cargar_estado():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else []

def guardar_estado(ids):
    STATE_FILE.write_text(json.dumps(list(ids), indent=2, ensure_ascii=False))

# ───────── NOTIFICACIÓN ─────────
def notify(msg: str):
    ts = datetime.now().strftime("[%d/%m %H:%M] ")
    print(ts + re.sub(r"[^\x00-\x7F]", " ", msg))        # log en consola

    if not WEBHOOK:
        print("⚠️  WEBHOOK vacía: revisa DISCORD_WEBHOOK_URL")
        return
    try:
        r = requests.post(WEBHOOK, json={"content": msg}, timeout=10)
        if r.status_code >= 400:
            print(f"⚠️  Discord {r.status_code}: {r.text[:100]}") 
    except Exception as e:
        print("⚠️  Excepción enviando a Discord:", e)

# ───────── UNA PASADA ─────────
def run_once():
    conocidos = set(cargar_estado())
    docs = obtener_documentos()
    nuevos = [d for d in docs if d["id"] not in conocidos]

    if nuevos:
        for d in nuevos:
            conocidos.add(d["id"])
            safe_url = quote(d["url"], safe=":/")           # codifica espacios
            notify(f"📄 Nuevo PDF: {d['titulo']}\n<{safe_url}>")
        guardar_estado(conocidos)
    else:
        notify("Sin novedades en esta pasada")

if __name__ == "__main__":
    run_once()
