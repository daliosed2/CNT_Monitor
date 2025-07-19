
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

def enviar_mensaje_discord(nuevos_articulos):
    """
    Envía uno o varios mensajes a Discord.
    Si hay más de 25 artículos, los divide en varios mensajes.
    """
    if not DISCORD_WEBHOOK_URL:
        print("Error: La variable DISCORD_WEBHOOK_URL no está configurada.")
        return

    # Convertimos el set a una lista para poder dividirla
    lista_articulos = sorted(list(nuevos_articulos))
    total_articulos = len(lista_articulos)
    
    # Límite de campos por embed de Discord
    LIMITE_POR_MENSAJE = 20

    # Calculamos cuántos mensajes necesitaremos
    total_mensajes = (total_articulos + LIMITE_POR_MENSAJE - 1) // LIMITE_POR_MENSAJE

    # Dividimos la lista en trozos (chunks) y enviamos un mensaje por cada trozo
    for i in range(0, total_articulos, LIMITE_POR_MENSAJE):
        chunk = lista_articulos[i:i + LIMITE_POR_MENSAJE]
        mensaje_actual = (i // LIMITE_POR_MENSAJE) + 1

        fields = []
        for articulo in chunk:
            nombre_archivo = articulo.split('/')[-1]
            fields.append({
                "name": f"📄 {nombre_archivo}",
                "value": f"[Descargar aquí]({articulo})",
                "inline": False
            })

        # Construimos el payload del embed
        payload = {
            "embeds": [{
                "title": f"Nuevos Documentos Publicados (Parte {mensaje_actual}/{total_mensajes})",
                "color": 1940991, # Color azul
                "fields": fields,
                "footer": {
                    "text": f"Revisión automática a las {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }]
        }
        
        # El texto principal solo se envía en el primer mensaje
        if i == 0:
            payload["content"] = f"**¡Alerta! Se encontraron {total_articulos} nuevos documentos en el Repositorio Legal de CNT.**"

        try:
            print(f"Enviando mensaje {mensaje_actual}/{total_mensajes} a Discord...")
            respuesta = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
            respuesta.raise_for_status()
            print("Mensaje enviado con éxito.")
            # Añadimos una pausa de 1 segundo para no saturar la API de Discord
            time.sleep(1) 
        except requests.RequestException as e:
            print(f"Error al enviar el mensaje a Discord: {e}")
            # Si un mensaje falla, no intentamos con los siguientes
            break

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
```

### **Pasos a Seguir**

1.  **Reemplaza el Código:** Ve a tu repositorio en GitHub, abre el archivo `monitor_cnt.py` y reemplaza todo su contenido con el código que te acabo de dar.
2.  **Guarda los Cambios:** Haz "Commit" de los cambios para guardarlos en tu repositorio.
3.  **Prueba de Nuevo:** Ahora, para la prueba de fuego, vuelve a ejecutar el workflow manualmente desde la pestaña "Actions".

Esta vez, en lugar de un solo mensaje fallido, deberías empezar a recibir en Discord una serie de mensajes, cada uno con una parte de la lista de los 824 artículos, hasta que se completen todos.

¡Con este cambio, tu bot será mucho más robusto y estará listo para cualquier cantidad de actualizacion
