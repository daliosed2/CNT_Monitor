# -*- coding: utf-8 -*-
import calendar, json, os, re, requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

URL        = "https://www.cnt.com.ec/repositorio-legal"
STATE_FILE = Path("cnt_docs.json")
load_dotenv()
WEBHOOK = os.getenv("DISCORD_WEBHOOK", "").strip()

# ---------- helpers de fecha ----------
MES_ABR = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
MES_NOM = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
P_FULL      = re.compile(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})')
P_MES_AÑO   = re.compile(r'([A-Za-z]{3,9})\s+(\d{4})')
P_AÑO       = re.compile(r'(\d{4})')

def extraer_fecha(txt:str) -> datetime:
    if m := P_FULL.search(txt):
        d,mn,a = map(int, m.groups()); return datetime(a,mn,d)
    if m := P_MES_AÑO.search(txt):
        mes, a = m.groups(); mi = MES_ABR.get(mes.lower()) or MES_NOM.get(mes.lower()) or 1
        return datetime(int(a), mi, 1)
    if m := P_AÑO.search(txt):
        return datetime(int(m.group(1)),1,1)
    return datetime(1900,1,1)

# ---------- scraping ----------
def obtener_documentos():
    html = requests.get(URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    docs=[]
    for art in soup.find_all("article"):
        a = art.find("a", href=True)
        if not a: continue
        href  = a["href"].strip()
        title = " ".join(a.stripped_strings)
        fecha = extraer_fecha(title + " " + href)
        docs.append({"id": href, "titulo": title, "url": href, "fecha": fecha})
    docs.sort(key=lambda d:d["fecha"], reverse=True)   # más recientes primero
    return docs[:10]                                   # solo top-10

# ---------- estado ----------
def cargar_estado():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else []

def guardar_estado(ids):
    STATE_FILE.write_text(json.dumps(list(ids), indent=2, ensure_ascii=False))

def notify(msg:str):
    ts = datetime.now().strftime("[%d/%m %H:%M] ")
    print(ts + re.sub(r"[^\x00-\x7F]", " ", msg))
    if WEBHOOK:
        requests.post(WEBHOOK, json={"content": msg}, timeout=10)

def run_once():
    conocidos=set(cargar_estado())
    notify(f"CNT Monitor: {len(conocidos)} conocidos (top-10 por fecha)")
    nuevos=[]
    for d in obtener_documentos():
        if d["id"] not in conocidos:
            nuevos.append(d); conocidos.add(d["id"])
            notify(f"📄 Nuevo PDF: {d['titulo']}\n{d['url']}")
    if nuevos: guardar_estado(conocidos)
    else: notify("Sin novedades en esta pasada")

if __name__=="__main__":
    run_once()
