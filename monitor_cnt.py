# monitor_cnt.py
import requests
from bs4 import BeautifulSoup
import os
import sys
import datetime

# --- Configuración ---
URL = "https://www.cnt.com.ec/repositorio-legal"
NOMBRE_ARCHIVO_HISTORIAL = "articulos_conocidos.txt"

# --- URL del Webhook de Discord (se obtiene de las variables de entorno) ---
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

def enviar_mensaje_discord(nuevos_articulos):
    """Envía un mensaje embed a un canal de Discord a través de un Webhook."""
    if not DISCORD_WEBHOOK_URL:
        print("Error: La variable DISCORD_WEBHOOK_URL no está configurada.")
        return

    fields = []
    for articulo in nuevos_articulos:
        nombre_archivo = articulo.split('/')[-1]
        fields.append({
            "name": f"📄 {nombre_archivo}",
            "value": f"[Descargar aquí]({articulo})",
            "inline": False
        })

    payload = {
        "content": f"**¡Alerta! Se encontraron {len(nuevos_articulos)} nuevos documentos en el Repositorio Legal de CNT.**",
        "embeds": [{
            "title": "Nuevos Documentos Publicados",
            "color": 1940991, # Color azul
            "fields": fields,
            "footer": {
                "text": f"Revisión automática a las {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }]
    }

    try:
        respuesta = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        respuesta.raise_for_status()
        print("Mensaje de notificación enviado a Discord con éxito.")
    except requests.RequestException as e:
        print(f"Error al enviar el mensaje a Discord: {e}")

def obtener_articulos_actuales():
    """Obtiene los enlaces de todos los artículos PDF de la página de CNT."""
    try:
        respuesta = requests.get(URL, timeout=15)
        respuesta.raise_for_status()
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        return {a['href'] for a in soup.select('article a[href]')}
    except requests.RequestException as e:
        print(f"Error al conectar con la URL: {e}")
        return None

def main():
    """Función principal que orquesta el monitoreo."""
    print("Iniciando revisión del repositorio legal de CNT...")
    articulos_conocidos = set()
    if os.path.exists(NOMBRE_ARCHIVO_HISTORIAL):
        with open(NOMBRE_ARCHIVO_HISTORIAL, 'r', encoding='utf-8') as f:
            articulos_conocidos = {line.strip() for line in f}

    articulos_actuales = obtener_articulos_actuales()
    if articulos_actuales is None:
        sys.exit(1)

    nuevos_articulos = articulos_actuales - articulos_conocidos

    if nuevos_articulos:
        print(f"¡Se encontraron {len(nuevos_articulos)} nuevos artículos!")
        enviar_mensaje_discord(nuevos_articulos)
        with open(NOMBRE_ARCHIVO_HISTORIAL, 'w', encoding='utf-8') as f:
            for enlace in sorted(list(articulos_actuales)):
                f.write(enlace + '\n')
        print("El archivo de historial ha sido actualizado.")
    else:
        print("✅ No hay nuevos artículos. Todo está al día.")

if __name__ == "__main__":
    main()
