import json
import os
import requests
# 🚨 PLAN B: Obligamos a Python a encontrar ImageMagick
import os
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
from openai import OpenAI
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 1. PON TUS LLAVES SECRETAS AQUÍ 
# ==========================================
_keys = json.load(open("config_keys.json", "r", encoding="utf-8")) if os.path.exists("config_keys.json") else {}
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", _keys.get("openai", "")))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", _keys.get("elevenlabs", ""))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", _keys.get("pexels", ""))

# ==========================================
# MÓDULO ACTUALIZADO: EL GUIONISTA DE RETENCIÓN EXTREMA
# ==========================================
print("🧠 Pensando como el Lobo de Wall Street... Escribiendo un guion de alta retención.")

tema_del_video = "¿Por qué los bancos no quieren que conozcas el interés compuesto?"

prompt_maestro = f"""
Actúa como un experto financiero carismático, disruptivo y directo (estilo 'Lobo de Wall Street' pero altamente educativo y honesto). 
Tu objetivo es escribir un guion de YouTube altamente viral y atrapante sobre el siguiente tema: '{tema_del_video}'.

REGLAS DE ORO PARA EL ALGORITMO Y LA RETENCIÓN:
1. LONGITUD ÉPICA: El guion debe ser MUY extenso, profundo y detallado. Escribe al menos 1200 a 1500 palabras. Necesitamos que la narración dure entre 8 y 10 minutos para poder monetizar con anuncios Mid-Roll.
2. GANCHO DE 3 SEGUNDOS: NO saludes. Nada de "Hola a todos, bienvenidos al canal". Empieza la primera línea con una afirmación brutal, un dato perturbador o una promesa que le vuele la cabeza al espectador. 
3. DINAMISMO Y PSICOLOGÍA: Usa analogías callejeras y visuales (ejemplo: "la inflación es como un parásito invisible en tu billetera"). Hazle preguntas directas al espectador para mantenerlo despierto. Usa un poco de sarcasmo suave contra el sistema tradicional.
4. ESTRUCTURA DEL VIDEO:
   - Gancho (0-30s): La cruda verdad o el secreto que vamos a revelar.
   - El Problema: Por qué el 99% de la gente es pobre o pierde dinero con esto.
   - El Desarrollo: Explica el concepto financiero paso a paso, como si el espectador tuviera 15 años, pero sin tratarlo de tonto.
   - La Solución/Estrategia: El plan de acción real y aplicable.
   - Outro: Un llamado a la acción (Call to Action) rápido e imperativo ("Suscríbete si no quieres que el sistema te siga robando").
5. FORMATO LIMPIO: Escribe ÚNICAMENTE lo que el locutor va a decir. NO incluyas acotaciones visuales, ni textos entre paréntesis como "(Música dramática)" o "(Transición)". Solo el texto puro para el motor de voz.
"""

respuesta = client.chat.completions.create(
    model="gpt-3.5-turbo", 
    messages=[
        {"role": "system", "content": "Eres el mejor guionista y estratega de retención de YouTube en el nicho de finanzas."},
        {"role": "user", "content": prompt_maestro}
    ],
    temperature=0.7 
)

guion_final = respuesta.choices[0].message.content
print("✅ Guion épico generado con éxito. Listo para la voz en off.")

# ==========================================
# EL LOCUTOR: GENERACIÓN DE VOZ CON ELEVENLABS
# ==========================================
print("\n🎙️ Entrando a la cabina de grabación de ElevenLabs...")

VOICE_ID = "pNInz6obpgDQGcFmaJgB" 
url_elevenlabs = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY
}

data = {
    "text": guion_final,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
    }
}

print("⏳ Grabando la voz en off... (Esto puede tardar dependiendo del largo del guion)")
respuesta_audio = requests.post(url_elevenlabs, json=data, headers=headers)

if respuesta_audio.status_code == 200:
    with open("voz_generada.mp3", "wb") as f:
        f.write(respuesta_audio.content)
    print("✅ ¡Voz generada y guardada como 'voz_generada.mp3'!")
else:
    print(f"❌ Error en ElevenLabs: {respuesta_audio.status_code} - {respuesta_audio.text}")


# ==========================================
# MÓDULO VISUAL AVANZADO: EDICIÓN POR CAPÍTULOS (MÉTODO PRÁCTICO)
# ==========================================
print("\n🎬 Activando el Motor de Edición por Capítulos...")

encabezados_pexels = {"Authorization": PEXELS_API_KEY}

archivo_audio = "voz_generada.mp3"
audio_principal = AudioFileClip(archivo_audio)
duracion_total = audio_principal.duration

print(f"⏱️ Duración detectada del video: {duracion_total:.2f} segundos.")

duracion_bloque = duracion_total / 3

capitulos = [
    {
        "nombre": "Bloque 1: El Problema / Dolor",
        "keywords": "stress money gas station empty wallet",
        "tiempo_inicio": 0,
        "tiempo_fin": duracion_bloque,
        "texto_pantalla": "EL GRAN PROBLEMA"
    },
    {
        "nombre": "Bloque 2: La Solución / El Cambio",
        "keywords": "electric car charging driving city",
        "tiempo_inicio": duracion_bloque,
        "tiempo_fin": duracion_bloque * 2,
        "texto_pantalla": "LA ALTERNATIVA"
    },
    {
        "nombre": "Bloque 3: Los Números / La Victoria",
        "keywords": "counting money smart phone profit chart",
        "tiempo_inicio": duracion_bloque * 2,
        "tiempo_fin": duracion_total,
        "texto_pantalla": "GANANCIAS REALES"
    }
]

clips_totales_video = []
ritmo_cambio = 4 

for num_cap, cap in enumerate(capitulos):
    print(f"\n📂 Procesando {cap['nombre']}...")
    duracion_necesaria_capitulo = cap['tiempo_fin'] - cap['tiempo_inicio']
    
    url_pexels = f"https://api.pexels.com/videos/search?query={cap['keywords']}&per_page=3&orientation=landscape"
    data_pexels = requests.get(url_pexels, headers=encabezados_pexels).json()
    
    archivos_locales_capitulo = []
    for i, video_data in enumerate(data_pexels.get('videos', [])):
        enlace_descarga = video_data['video_files'][0]['link']
        nombre_archivo = f"temp_cap_{num_cap}_clip_{i}.mp4"
        
        print(f"  ⬇️ Descargando apoyo visual para este bloque...")
        video_bytes = requests.get(enlace_descarga).content
        with open(nombre_archivo, 'wb') as f:
            f.write(video_bytes)
        archivos_locales_capitulo.append(nombre_archivo)
    
    if not archivos_locales_capitulo:
        print("⚠️ No se encontraron videos en Pexels para este bloque. Usando respaldo genérico.")
        continue

    tiempo_acumulado_cap = 0
    indice_clip = 0
    
    while tiempo_acumulado_cap < duracion_necesaria_capitulo:
        archivo_clip_actual = archivos_locales_capitulo[indice_clip % len(archivos_locales_capitulo)]
        clip_base = VideoFileClip(archivo_clip_actual).without_audio()
        
        tiempo_restante_cap = duracion_necesaria_capitulo - tiempo_acumulado_cap
        corte_plano = min(ritmo_cambio, tiempo_restante_cap)
        
        duracion_real_corte = min(corte_plano, clip_base.duration)
        clip_recortado = clip_base.subclip(0, duracion_real_corte)
        
        clip_texto = (TextClip(cap['texto_pantalla'], fontsize=75, color='white', font='Impact', bg_color='black')
                      .set_position('center')
                      .set_duration(duracion_real_corte))
        
        clip_final_bloque = CompositeVideoClip([clip_recortado, clip_texto])
        clips_totales_video.append(clip_final_bloque)
        
        tiempo_acumulado_cap += duracion_real_corte
        indice_clip += 1

# ==========================================
# RECOPILACIÓN Y RENDERIZADO FINAL
# ==========================================
print("\n🎛️ Sincronizando todos los capítulos con la pista de audio...")

video_sincronizado_sin_audio = concatenate_videoclips(clips_totales_video, method="compose")
video_final_con_voz = video_sincronizado_sin_audio.set_audio(audio_principal)

print("⏳ Exportando el archivo maestro 'VIDEO_YOUTUBE_LISTO.mp4'...")
video_final_con_voz.write_videofile(
    "VIDEO_YOUTUBE_LISTO.mp4", 
    fps=24, 
    codec="libx264", 
    audio_codec="aac",
    threads=4 
)

print("\n🏆 ¡PROCESO DE EDICIÓN AVANZADO COMPLETADO! Tu video está listo y sincronizado conceptualmente.")


