import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

print("\n🚀 Iniciando máquina de publicación... Preparando carga a YouTube.")

# Los permisos que el bot necesita (Solo subir videos)
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# El nombre exacto del archivo que genera tu creador.py
NOMBRE_VIDEO = "VIDEO_YOUTUBE_LISTO.mp4"

def subir_a_youtube():
    # Verificamos que el creador.py ya haya terminado su trabajo
    if not os.path.exists(NOMBRE_VIDEO):
        print(f"❌ ¡ALTO! No encuentro el archivo '{NOMBRE_VIDEO}'.")
        print("Asegúrate de ejecutar primero tu archivo 'creador.py' para que genere el video.")
        return

    try:
        # 1. Autenticación (Pedirá permiso en tu navegador la primera vez)
        flujo = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        credenciales = flujo.run_local_server(port=0) 
        
        youtube = build('youtube', 'v3', credentials=credenciales)
        
        # 2. Preparamos la estrategia SEO
        titulo_viral = "La Verdad Siniestra del Mundial de Fútbol | ¿Inversión o Ruina?"
        etiquetas_seo = ['finanzas', 'mundial', 'dinero', 'economia', 'inversion']
        
        descripcion_optimizada = f"""{titulo_viral}
        
Descubre la oscura realidad económica detrás de organizar una Copa del Mundo. ¿Es realmente rentable para un país o es una trampa financiera?

🔔 ¡Suscríbete para dominar tus finanzas y vencer al sistema!

Tags: {', '.join(etiquetas_seo)}
#Finanzas #Dinero #Inversiones
"""

        cuerpo_video = {
            'snippet': {
                'title': titulo_viral,
                'description': descripcion_optimizada,
                'tags': etiquetas_seo,
                'categoryId': '27' # 27 es la categoría de "Educación" en YouTube
            },
            'status': {
                'privacyStatus': 'private', # Lo sube en PRIVADO para tu revisión
                'selfDeclaredMadeForKids': False
            }
        }
        
        # 3. Cargamos el archivo de video
        archivo_media = MediaFileUpload(NOMBRE_VIDEO, chunksize=-1, resumable=True)
        
        # 4. ¡Disparamos el misil a los servidores de Google!
        print("📤 Subiendo el video... (La velocidad depende de tu internet, paciencia)")
        peticion_subida = youtube.videos().insert(
            part="snippet,status",
            body=cuerpo_video,
            media_body=archivo_media
        )
        
        respuesta_youtube = peticion_subida.execute()
        
        print(f"\n🎉 ¡MISIÓN CUMPLIDA! El video ya está en tu canal de YouTube.")
        print(f"🔗 Enlace del video: https://youtu.be/{respuesta_youtube['id']}")

    except Exception as e:
        print(f"\n❌ Error crítico al subir a YouTube: {e}")

# Ejecutamos la función
subir_a_youtube()