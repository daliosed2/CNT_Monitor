# monitor_cnt.py
import requests
from bs4 import BeautifulSoup
import os
import sys
import datetime
import time # Importamos la librería time para añadir pausas

# --- Configuración ---
URL = "https://www.cnt.com.ec/repositorio-legal"
NOMBRE_ARCHIVO_HISTORIAL = "articulos_conocidos.txt"

# --- URL del Webhook de Discord (se obtiene de las variables de entorno) ---
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

def enviar_mensaje_nuevos_articulos(nuevos_articulos):
    """
    Envía uno o varios mensajes a Discord cuando se encuentran nuevos artículos.
    Si hay más de 25 artículos, los divide en varios mensajes.
    """
    if not DISCORD_WEBHOOK_URL:
        print("Error: La variable DISCORD_WEBHOOK_URL no está configurada.")
        return

    lista_articulos = sorted(list(nuevos_articulos))
    total_articulos = len(lista_articulos)
    LIMITE_POR_MENSAJE = 20
    total_mensajes = (total_articulos + LIMITE_POR_MENSAJE - 1) // LIMITE_POR_MENSAJE

    for i in range(0, total_articulos, LIMITE_POR_MENSAJE):
        chunk = lista_articulos[i:i + LIMITE_POR_MENSAJE]
        mensaje_actual = (i // LIMITE_POR_MENSAJE) + 1

        fields = []
        for articulo in chunk:
            # La URL del artículo ya es el enlace directo al PDF
            nombre_archivo = articulo.split('/')[-1]
            fields.append({
                "name": f"📄 {nombre_archivo}",
                "value": f"[Abrir PDF aquí]({articulo})", # Enlace directo al PDF
                "inline": False
            })

        payload = {
            "embeds": [{
                "title": f"Nuevos Documentos Publicados (Parte {mensaje_actual}/{total_mensajes})",
                "color": 15105570, # Color naranja/ámbar para alerta
                "fields": fields,
                "footer": {
                    "text": f"Revisión automática a las {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }]
        }
        
        if i == 0:
            payload["content"] = f"**¡Alerta! Se encontraron {total_articulos} nuevos documentos en el Repositorio Legal de CNT.**"

        try:
            print(f"Enviando mensaje {mensaje_actual}/{total_mensajes} a Discord...")
            respuesta = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
            respuesta.raise_for_status()
            print("Mensaje enviado con éxito.")
            time.sleep(1) 
        except requests.RequestException as e:
            print(f"Error al enviar el mensaje a Discord: {e}")
            break

def enviar_mensaje_sin_cambios():
    """Envía un mensaje de éxito a Discord cuando no se encuentran nuevos artículos."""
    if not DISCORD_WEBHOOK_URL:
        print("Webhook de Discord no configurado, no se puede enviar mensaje de éxito.")
        return

    payload = {
        "embeds": [{
            "title": "✅ Revisión Completada",
            "description": "No se encontraron nuevos documentos en el Repositorio Legal de CNT. Todo está al día.",
            "color": 3066993, # Color verde para éxito
            "footer": {
                "text": f"Revisión automática a las {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }]
    }

    try:
        print("Enviando mensaje de 'Sin Cambios' a Discord...")
        respuesta = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
        respuesta.raise_for_status()
        print("Mensaje de 'Sin Cambios' enviado con éxito.")
    except requests.RequestException as e:
        print(f"Error al enviar el mensaje de 'Sin Cambios' a Discord: {e}")

def obtener_articulos_actuales():
    """Obtiene los enlaces de todos los artículos PDF de la página de CNT."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        respuesta = requests.get(URL, timeout=15, headers=headers)
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
        enviar_mensaje_nuevos_articulos(nuevos_articulos)
        with open(NOMBRE_ARCHIVO_HISTORIAL, 'w', encoding='utf-8') as f:
            for enlace in sorted(list(articulos_actuales)):
                f.write(enlace + '\n')
        print("El archivo de historial ha sido actualizado.")
    else:
        print("✅ No hay nuevos artículos. Todo está al día.")
        # Enviamos la notificación de que no se encontraron cambios
        enviar_mensaje_sin_cambios()

if __name__ == "__main__":
    main()
```</immersive>
