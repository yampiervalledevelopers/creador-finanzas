import customtkinter as ctk
import threading
import asyncio
import subprocess
import sys
import json
import os
import re
import random
import base64
import logging
import shutil
import time
from tkinter import filedialog
from openai import OpenAI
import requests

# ==========================================
# LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ==========================================
# IMAGEMAGICK (detección automática)
# ==========================================
imagemagick_path = shutil.which("magick")
if imagemagick_path:
    os.environ["IMAGEMAGICK_BINARY"] = imagemagick_path
else:
    posible = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
    if os.path.exists(posible):
        os.environ["IMAGEMAGICK_BINARY"] = posible

import numpy as np
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    CompositeAudioClip,
    afx,
)
from moviepy.video.fx.all import crop

# Importaciones Oficiales para YouTube
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# CONFIGURACIÓN VISUAL
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

REQUEST_TIMEOUT = 60


# ==========================================
# MOTOR MULTIGÉNERO (CUALQUIER NICHO VIRAL)
# ==========================================
GENEROS_CANAL = {
    "💰 Finanzas, Negocios y Geopolítica": {
        "rol_guionista": (
            "Eres un director creativo y guionista experto en retención viral para YouTube y Shorts "
            "del nicho de finanzas, negocios, inversiones y geopolítica económica."
        ),
        "instruccion_tono": "Tono revelador, urgente, analítico y magnético, como revelando un secreto financiero multimillonario.",
        "cierre_estructura": "Cierra SIEMPRE con un DATO REAL verificable, cifra histórica o reflexión financiera de alto impacto.",
        "estilo_visual_ia": (
            "Cinematic hyperrealistic documentary scene, dramatic financial thriller lighting, "
            "8k resolution, photorealistic, Arri Alexa 35mm."
        ),
        "youtube_category_id": "27",
    },
    "✂️ Clipping Viral / Remix de Tendencias": {
        "rol_guionista": (
            "Eres un experto en Clipping Viral, curaduría de momentos de alto impacto, podcasts, polémicas "
            "y re-edición dinámica estilo TikTok/Reels/Shorts con retención del 100%."
        ),
        "instruccion_tono": "Ritmo ultra rápido, directo al grano en el primer segundo, lenguaje juvenil y magnético sin relleno.",
        "cierre_estructura": "Cierra con una pregunta polémica abierta que obligue a la audiencia a debatir en los comentarios.",
        "estilo_visual_ia": (
            "High-energy viral social media visual, ultra-sharp modern studio lighting, dynamic contrast, "
            "hyperrealistic 8k, eye-catching composition."
        ),
        "youtube_category_id": "24",
    },
    "👻 Terror, Misterio y Creepypasta (Oscuro / Suspenso)": {
        "rol_guionista": (
            "Eres un maestro del terror psicológico, misterios sin resolver, casos paranormales y creepypastas "
            "inmersivos al estilo de DrossRotzank y canales de horror cinematográfico."
        ),
        "instruccion_tono": "Atmósfera inquietante, misteriosa, inmersiva y escalofriante. Usa pausas [PAUSA] para crear tensión.",
        "cierre_estructura": "Cierra con un giro perturbador (plot twist), un detalle escalofriante real o una advertencia final.",
        "estilo_visual_ia": (
            "Dark cinematic horror atmosphere, eerie volumetric fog, unsettling shadows, "
            "moonlight and flickering dim light, creepy hyperrealistic 8k, A24 horror film aesthetic."
        ),
        "youtube_category_id": "24",
    },
    "🧸 Animación 3D Estilo Pixar / Disney": {
        "rol_guionista": (
            "Eres un director creativo y narrador de historias emotivas, carismáticas y visualmente mágicas "
            "al estilo de Pixar Animation Studios y Disney."
        ),
        "instruccion_tono": "Narrativa emotiva, expresiva, cinematográfica y entrañable que conecta con todas las edades.",
        "cierre_estructura": "Cierra con un mensaje memorable, emotivo o inspirador que deje huella en el espectador.",
        "estilo_visual_ia": (
            "3D Pixar and Disney animation style, cute expressive characters, Unreal Engine 5 render, "
            "Octane render, vibrant warm subsurface scattering lighting, rich textures, 8k."
        ),
        "youtube_category_id": "1",
    },
    "🌈 Infantil, Cuentos y Fábulas Educativas": {
        "rol_guionista": (
            "Eres un escritor especializado en cuentos infantiles mágicos, fábulas con moraleja y curiosidades "
            "educativas súper divertidas para niños y familias."
        ),
        "instruccion_tono": "Alegre, entusiasta, claro, mágico, lleno de asombro, onomatopeyas suaves y vocabulario apto para niños.",
        "cierre_estructura": "Cierra con una moraleja positiva, dulce y una pregunta divertida para los niños.",
        "estilo_visual_ia": (
            "Whimsical colorful children's storybook 3D illustration, magical fairy-tale world, "
            "adorable friendly characters, bright cheerful lighting, Pixar/DreamWorks kids style, 8k."
        ),
        "youtube_category_id": "1",
    },
    "🎌 Anime Épico / Manga (Estilo Shonen / Ghibli)": {
        "rol_guionista": (
            "Eres un guionista experto en narrativa épica estilo Anime japonés, batallas legendarias, "
            "filosofía de personajes y mundos fantásticos."
        ),
        "instruccion_tono": "Épico, apasionado, dramático y cargado de adrenalina o belleza poética japonesa.",
        "cierre_estructura": "Cierra con una frase filosófica legendaria digna de un final de episodio de anime.",
        "estilo_visual_ia": (
            "Masterpiece Japanese anime cinematography, Makoto Shinkai and Ufotable visual style, "
            "dramatic anime lighting, vibrant cel-shaded colors, detailed epic background, 8k."
        ),
        "youtube_category_id": "1",
    },
    "💥 Acción, Ciencia Ficción y Cyberpunk (Hollywood IMAX)": {
        "rol_guionista": (
            "Eres un director de blockbusters de Hollywood experto en acción trepidante, futuro distópico, "
            "ciencia ficción, tecnología militar y supervivencia extrema."
        ),
        "instruccion_tono": "Adrenalina pura, ritmo vertiginoso, impacto cinematográfico de tráiler IMAX.",
        "cierre_estructura": "Cierra con una revelación impactante sobre el futuro o una frase épica de película.",
        "estilo_visual_ia": (
            "Hollywood IMAX sci-fi action blockbuster scene, Denis Villeneuve and Christopher Nolan style, "
            "neon cyberpunk or epic futuristic scale, volumetric explosions and rain, 8k photorealistic."
        ),
        "youtube_category_id": "24",
    },
    "🏛️ Historia, Mitología e Imperios Antiguos": {
        "rol_guionista": (
            "Eres un historiador y narrador épico especializado en civilizaciones antiguas, mitología, "
            "batallas históricas y secretos prohibidos de la humanidad."
        ),
        "instruccion_tono": "Solemne, épico, envolvente y lleno de asombro histórico.",
        "cierre_estructura": "Cierra conectando el hecho histórico o mito con una lección eterna para el presente.",
        "estilo_visual_ia": (
            "Epic historical movie scene, Ridley Scott Gladiator aesthetic, ancient civilization grandeur, "
            "golden hour torchlight and dust particles, hyperrealistic 8k cinematography."
        ),
        "youtube_category_id": "27",
    },
    "🕵️ True Crime / Casos Reales e Investigación": {
        "rol_guionista": (
            "Eres un periodista de investigación y documentalista experto en True Crime, desapariciones, "
            "estafas reales y perfiles criminales estilo Netflix."
        ),
        "instruccion_tono": "Serio, intrigante, forense, reconstruyendo las pistas minuto a minuto con suspenso.",
        "cierre_estructura": "Cierra con el veredicto real del caso o el misterio que aún sigue abierto hoy.",
        "estilo_visual_ia": (
            "Netflix true crime documentary cinematography, moody neo-noir detective lighting, "
            "rainy crime scene street, 35mm film grain, hyperrealistic 8k."
        ),
        "youtube_category_id": "25",
    },
    "🦁 Motivación, Estoicismo y Éxito Personal": {
        "rol_guionista": (
            "Eres un mentor de alto rendimiento, filosofía estoica, disciplina inquebrantable y psicología "
            "del éxito personal."
        ),
        "instruccion_tono": "Poderoso, profundo, inspirador, directo al alma y con autoridad moral.",
        "cierre_estructura": "Cierra con un reto práctico para aplicar hoy mismo y una cita estoica memorable.",
        "estilo_visual_ia": (
            "Cinematic stoic aesthetic, dramatic chiaroscuro lighting, marble statues and lone warrior silhouette, "
            "moody atmospheric mist, 8k ultra-detailed."
        ),
        "youtube_category_id": "27",
    },
    "😂 Diversión, Curiosidades Virales y Humor": {
        "rol_guionista": (
            "Eres un creador viral de entretenimiento, datos locos que parecen falsos pero son reales, "
            "humor inteligente y cultura de internet."
        ),
        "instruccion_tono": "Súper entretenido, chispeante, irónico, ágil y sorprendente cada 3 segundos.",
        "cierre_estructura": "Cierra con el dato más absurdo o divertido y un remate cómico.",
        "estilo_visual_ia": (
            "Vibrant hyper-detailed surreal and fun cinematic scene, bright pop colors, "
            "expressive dynamic angle, 8k ultra-sharp."
        ),
        "youtube_category_id": "24",
    },
    "🎮 Gaming, Tecnología y Cultura Pop": {
        "rol_guionista": (
            "Eres un creador experto en videojuegos, secretos ocultos (easter eggs), inteligencia artificial, "
            "gadgets futuristas y cultura geek."
        ),
        "instruccion_tono": "Dinámico, apasionado, experto y lleno de referencias que encantan a los gamers.",
        "cierre_estructura": "Cierra preguntando a la comunidad cuál es su teoría o juego favorito.",
        "estilo_visual_ia": (
            "Unreal Engine 5 next-gen gaming cinematic render, RGB neon reflections, "
            "ray-tracing global illumination, ultra-detailed 8k."
        ),
        "youtube_category_id": "20",
    },
}


# ==========================================
# UTILIDADES
# ==========================================
def limpiar_nombre(texto):
    """Sanitiza un texto para usarlo como nombre de archivo."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", texto)[:80]


# ==========================================
# SERVICIOS (lógica separada de la GUI)
# ==========================================
class OpenAIService:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de OpenAI.")
        self.client = OpenAI(api_key=api_key)

    def generar_guion(self, modelo, prompt, genero_key=None):
        info_genero = GENEROS_CANAL.get(
            genero_key,
            GENEROS_CANAL["💰 Finanzas, Negocios y Geopolítica"],
        )
        res = self.client.chat.completions.create(
            model=modelo,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"{info_genero['rol_guionista']} Respondes siempre en JSON válido.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(res.choices[0].message.content)

    def generar_guion_extra_largo(self, modelo, prompt_maestro, genero_key=None, callback_progreso=None):
        """
        Genera un guion EXTRA LARGO (3,200 a 4,200+ palabras reales, ~20-28 minutos)
        dividiendo la creación en:
        1) Diseño de Arquitectura de 5 Capítulos Documentales.
        2) Redacción profunda e independiente de cada capítulo (650-850 palabras + 8 escenas por capítulo)
           para romper el límite de tokens de salida de una sola petición de OpenAI.
        """
        info_genero = GENEROS_CANAL.get(
            genero_key,
            GENEROS_CANAL["💰 Finanzas, Negocios y Geopolítica"],
        )
        estilo_visual = info_genero["estilo_visual_ia"]

        if callback_progreso:
            callback_progreso("📐 Paso 1/6: Diseñando estructura de 5 Capítulos para el Mega-Documental...")

        prompt_estructura = f"""Basado en esta solicitud del usuario:
{prompt_maestro}

Diseña la arquitectura maestra de un MEGA-DOCUMENTAL EXTENSO dividido en 5 CAPÍTULOS profundos que no se repitan entre sí:
- Capítulo 1: El Gancho Brutal, el Misterio Central y por qué cambia todo.
- Capítulo 2: El Origen Oculto, la Historia y las Raíces Profundas.
- Capítulo 3: El Mecanismo Interno, Casos Reales, Pruebas y Detalles Inéditos.
- Capítulo 4: El Clímax, el Giro Oscuro/Revelador y las Consecuencias Extremas.
- Capítulo 5: El Impacto en el Futuro, Lección Magistral y Gran Cierre Épico.

Devuelve ESTRICTAMENTE un JSON con:
- 'titulo_seo': título viral de alto CTR para el documental completo.
- 'descripcion_seo': descripción completa con marcas de tiempo aproximadas y hashtags.
- 'capitulos': lista de 5 objetos, cada uno con:
    - 'numero': 1 al 5
    - 'titulo': título magnético del capítulo
    - 'instrucciones_detalladas': qué debe desarrollar a fondo este capítulo sin repetir los demás."""

        res_est = self.client.chat.completions.create(
            model=modelo,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"{info_genero['rol_guionista']} Respondes siempre en JSON válido.",
                },
                {"role": "user", "content": prompt_estructura},
            ],
        )
        datos_est = json.loads(res_est.choices[0].message.content)
        capitulos = datos_est.get("capitulos", [])
        if not capitulos or len(capitulos) < 3:
            capitulos = [
                {"numero": i, "titulo": f"Parte {i}", "instrucciones_detalladas": f"Desarrolla a fondo el acto {i}."}
                for i in range(1, 6)
            ]

        guion_total_partes = []
        escenas_totales = []
        keywords_totales = []
        prompts_totales = []
        resumen_previo = ""

        for idx, cap in enumerate(capitulos, start=1):
            num_cap = cap.get("numero", idx)
            tit_cap = cap.get("titulo", f"Capítulo {idx}")
            inst_cap = cap.get("instrucciones_detalladas", "")

            if callback_progreso:
                callback_progreso(
                    f"✍️ Paso {idx + 1}/6: Escribiendo Capítulo {idx}/{len(capitulos)} ('{tit_cap[:35]}...')..."
                )

            regla_inicio = (
                "Empieza en el segundo 0 con un GANCHO BRUTAL sin saludos genéricos."
                if idx == 1
                else "Continúa directamente el hilo narrativo del capítulo anterior SIN volver a saludar ni presentarte."
            )
            regla_cierre = (
                info_genero["cierre_estructura"]
                if idx == len(capitulos)
                else "Deja un puente de intriga (cliffhanger) que conecte con el siguiente capítulo."
            )

            prompt_cap = f"""Estás escribiendo el CAPÍTULO {num_cap} de {len(capitulos)} de un Mega-Documental en Español.
Título del Capítulo {num_cap}: "{tit_cap}"
Qué debes desarrollar a fondo en este capítulo: {inst_cap}
Tono obligatorio: {info_genero['instruccion_tono']}

CONTEXTO DE LO YA NARRADO ANTES (NO LO REPITAS):
{resumen_previo[-1800:] if resumen_previo else 'Este es el primer capítulo.'}

REGLAS ESTRICTAS PARA ESTE CAPÍTULO:
1. EXTENSIÓN: Escribe entre 650 y 850 palabras REALES en español solo para este capítulo. Prohibido resumir; incluye ejemplos concretos, datos, nombres, atmósfera y usa [PAUSA] para silencios dramáticos.
2. INICIO: {regla_inicio}
3. CIERRE DEL CAPÍTULO: {regla_cierre}
4. ESCENAS VISUALES: Divide este capítulo en 8 escenas cronológicas.

Devuelve ESTRICTAMENTE un objeto JSON con:
- 'narracion_capitulo': (el texto completo de 650-850 palabras en ESPAÑOL de este capítulo)
- 'escenas': (lista de 8 objetos ordenados cronológicamente, cada uno con:
    - 'narracion': el párrafo o fragmento de este capítulo que se narra en esa escena,
    - 'keyword_pexels': búsqueda concreta de 2 a 4 palabras en INGLÉS para video stock (evita palabras abstractas),
    - 'prompt_ia': prompt cinematográfico detallado en INGLÉS con estilo "{estilo_visual}", sin texto ni marcas de agua)"""

            res_cap = self.client.chat.completions.create(
                model=modelo,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"{info_genero['rol_guionista']} Escribes capítulos extensos, profundos y envolventes "
                            f"sin resumir jamás. Respondes siempre en JSON válido."
                        ),
                    },
                    {"role": "user", "content": prompt_cap},
                ],
            )
            datos_cap = json.loads(res_cap.choices[0].message.content)
            texto_cap = datos_cap.get("narracion_capitulo", "").strip()
            escenas_cap = datos_cap.get("escenas", [])

            if not texto_cap and escenas_cap:
                texto_cap = " ".join(e.get("narracion", "") for e in escenas_cap).strip()

            if texto_cap:
                guion_total_partes.append(texto_cap)
                resumen_previo += f"\n[Cap {num_cap}]: {texto_cap[:450]}..."

            for e in escenas_cap:
                escenas_totales.append(e)
                if e.get("keyword_pexels"):
                    keywords_totales.append(e["keyword_pexels"])
                if e.get("prompt_ia"):
                    prompts_totales.append(e["prompt_ia"])

        guion_completo = "\n\n[PAUSA]\n\n".join(guion_total_partes)
        return {
            "guion_locucion": guion_completo,
            "escenas": escenas_totales,
            "keywords_visuales": keywords_totales,
            "prompts_visuales": prompts_totales,
            "titulo_seo": datos_est.get("titulo_seo", "Documental Completo"),
            "descripcion_seo": datos_est.get("descripcion_seo", ""),
        }

    def transcribir(self, ruta_audio, con_segmentos=False):
        granularities = ["segment", "word"] if con_segmentos else ["word"]
        ruta_enviar = ruta_audio
        archivo_temp_ligero = None

        # OpenAI Whisper tiene límite de 25 MB. Si el audio de un video EXTRA LARGO pesa > 22 MB,
        # creamos una copia temporal comprimida a 16kHz / 48kbps para que nunca falle.
        try:
            if os.path.exists(ruta_audio) and os.path.getsize(ruta_audio) > 22 * 1024 * 1024:
                archivo_temp_ligero = ruta_audio + "_whisper_16k.mp3"
                clip_a = AudioFileClip(ruta_audio)
                clip_a.write_audiofile(
                    archivo_temp_ligero,
                    fps=16000,
                    nbytes=2,
                    codec="libmp3lame",
                    bitrate="48k",
                    logger=None,
                )
                clip_a.close()
                ruta_enviar = archivo_temp_ligero

            with open(ruta_enviar, "rb") as audio_file:
                return self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=granularities,
                )
        finally:
            if archivo_temp_ligero and os.path.exists(archivo_temp_ligero):
                try:
                    os.remove(archivo_temp_ligero)
                except Exception:
                    pass

    def detectar_momentos_virales(self, transcripcion_texto, duracion_total, num_clips=3, dur_min=15, dur_max=45):
        """
        Analiza la transcripción con timestamps de un video largo y devuelve los mejores fragmentos virales
        para hacer Clipping automático.
        """
        prompt = f"""Analiza la siguiente transcripción con marcas de tiempo de un video de {duracion_total:.1f} segundos.
Encuentra los {num_clips} fragmentos MÁS VIRALES, polémicos, emocionantes o con mayor retención para subirlos como Shorts/TikToks/Reels.
Cada clip debe durar entre {dur_min} y {dur_max} segundos y tener sentido completo por sí mismo.

TRANSCRIPCIÓN CON TIMESTAMPS:
{transcripcion_texto[:14000]}

Devuelve ESTRICTAMENTE un objeto JSON con la llave "clips", donde cada elemento tenga:
- "inicio": (número float en segundos donde empieza el clip)
- "fin": (número float en segundos donde termina el clip)
- "titulo_seo": (título viral corto con emojis y hashtags para publicar este clip)
- "gancho_texto": (la primera frase impactante que se dice en el clip)
- "razon_viral": (breve explicación de por qué este fragmento será viral)
"""
        res = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Eres un editor experto en Clipping Viral para TikTok, YouTube Shorts y Reels. Respondes siempre en JSON válido.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(res.choices[0].message.content).get("clips", [])

    def generar_imagen(self, prompt, nombre_archivo, vertical=True):
        size = "1024x1536" if vertical else "1536x1024"
        try:
            res = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
            )
            if getattr(res.data[0], "b64_json", None):
                image_bytes = base64.b64decode(res.data[0].b64_json)
            else:
                image_bytes = requests.get(res.data[0].url, timeout=REQUEST_TIMEOUT).content
        except Exception:
            size_dalle = "1024x1792" if vertical else "1792x1024"
            res = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size_dalle,
                response_format="b64_json",
            )
            image_bytes = base64.b64decode(res.data[0].b64_json)

        with open(nombre_archivo, "wb") as f:
            f.write(image_bytes)
        return nombre_archivo

    def generar_voz_tts(self, guion, ruta_salida, voz="onyx", modelo_tts="tts-1"):
        """
        Genera locución con OpenAI Audio TTS (~$0.015 por 1,000 caracteres: ~15x más barato que ElevenLabs).
        Soporta guiones largos dividiendo automáticamente en bloques de 3,800 caracteres.
        """
        texto_limpio = re.sub(r"\[\s*PAUSA\s*\]", "... ", guion, flags=re.IGNORECASE)
        texto_limpio = re.sub(r"\[[^\]]+\]", "", texto_limpio)
        texto_limpio = re.sub(r"\s{2,}", " ", texto_limpio).strip()

        bloques = ElevenLabsService.dividir_en_bloques(texto_limpio)
        voz_id = voz.split()[0].lower() if voz else "onyx"

        with open(ruta_salida, "wb") as f_out:
            for bloque in bloques:
                res = self.client.audio.speech.create(
                    model=modelo_tts,
                    voice=voz_id,
                    input=bloque,
                    response_format="mp3",
                )
                f_out.write(res.content)
        return ruta_salida


class EdgeTTSService:
    """
    Locución Neuronal de Microsoft Edge 100% GRATIS ($0.00), sin límite de caracteres y sin API Key.
    Incluye las voces hispanas más virales para canales Faceless de finanzas y documentales.
    """

    VOCES_GRATIS = {
        "Álvaro (España - Profunda / Viral TikTok)": "es-ES-AlvaroNeural",
        "Jorge (México - Narrador Profesional)": "es-MX-JorgeNeural",
        "Gonzalo (Colombia - Clara / Dinámica)": "es-CO-GonzaloNeural",
        "Alonso (EE.UU. Latino - Documental Pro)": "es-US-AlonsoNeural",
        "Tomás (Argentina - Cercana / Storytelling)": "es-AR-TomasNeural",
        "Dalia (México - Femenina Ejecutiva)": "es-MX-DaliaNeural",
    }

    @classmethod
    def asegurar_instalacion(cls):
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts", "--quiet"])

    @classmethod
    def generar_voz(cls, guion, ruta_salida, nombre_voz=None, velocidad="+6%"):
        cls.asegurar_instalacion()
        import edge_tts

        voz_id = cls.VOCES_GRATIS.get(nombre_voz, "es-ES-AlvaroNeural")
        texto_limpio = re.sub(r"\[\s*PAUSA\s*\]", " ... ", guion, flags=re.IGNORECASE)
        texto_limpio = re.sub(r"\[[^\]]+\]", "", texto_limpio)
        texto_limpio = re.sub(r"\s{2,}", " ", texto_limpio).strip()

        async def _guardar():
            communicate = edge_tts.Communicate(texto_limpio, voz_id, rate=velocidad)
            await communicate.save(ruta_salida)

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_guardar())
        finally:
            loop.close()
        return ruta_salida


class ElevenLabsService:
    VOCES = {
        "Adam (Profunda / Narrador)": "pNInz6obpgDQGcFmaJgB",
        "Brian (Grave / Documental Épico)": "nPczCjzI2devNBz1zQrb",
        "Daniel (Autoridad / Finanzas y Noticias)": "onwK4e9ZLuTAKqWW03F9",
        "Antoni (Dinámica / Joven)": "ErXwobaYiN019PkySvjV",
        "Arnold (Fuerte / Cine)": "VR6AewLTigWG4xSOukaG",
        "Josh (Cálida / Storytelling)": "TxGEqnHWrfWFTfGW9XjX",
    }
    VOCES_OPENAI = {
        "Onyx (OpenAI - Profunda / Lobo Wall Street)": "onyx",
        "Echo (OpenAI - Cálida / Documental)": "echo",
        "Ash (OpenAI - Dinámica / Directa)": "ash",
        "Alloy (OpenAI - Neutra / Noticias)": "alloy",
        "Nova (OpenAI - Femenina Enérgica)": "nova",
    }
    MAX_CHARS_POR_BLOQUE = 3800

    def __init__(self, api_key, voice_id=None, model_id="eleven_multilingual_v2"):
        if not api_key:
            raise ValueError("Falta la API key de ElevenLabs.")
        self.api_key = api_key
        self.voice_id = voice_id or self.VOCES["Adam (Profunda / Narrador)"]
        self.model_id = model_id

    @staticmethod
    def limpiar_guion_para_tts(guion):
        """Convierte marcadores [PAUSA] en silencios reales SSML y limpia anotaciones de dirección."""
        texto = re.sub(
            r"\[\s*PAUSA\s*\]",
            ' <break time="0.8s" /> ',
            guion,
            flags=re.IGNORECASE,
        )
        # Elimina indicaciones entre corchetes como [Música], [Tono serio], etc.
        texto = re.sub(r"\[[^\]]+\]", "", texto)
        return re.sub(r"\s{2,}", " ", texto).strip()

    @classmethod
    def dividir_en_bloques(cls, texto):
        """Divide guiones largos por párrafos u oraciones sin cortar palabras para evitar límites de ElevenLabs."""
        if len(texto) <= cls.MAX_CHARS_POR_BLOQUE:
            return [texto]

        bloques = []
        actual = ""
        for parrafo in re.split(r"(\n+)", texto):
            if len(actual) + len(parrafo) <= cls.MAX_CHARS_POR_BLOQUE:
                actual += parrafo
            else:
                if actual.strip():
                    bloques.append(actual.strip())
                if len(parrafo) <= cls.MAX_CHARS_POR_BLOQUE:
                    actual = parrafo
                else:
                    oraciones = re.split(r"(?<=[.!?])\s+", parrafo)
                    actual = ""
                    for oracion in oraciones:
                        if len(actual) + len(oracion) + 1 <= cls.MAX_CHARS_POR_BLOQUE:
                            actual = f"{actual} {oracion}".strip()
                        else:
                            if actual:
                                bloques.append(actual)
                            actual = oracion
        if actual.strip():
            bloques.append(actual.strip())
        return bloques

    def generar_voz(self, guion, ruta_salida):
        texto_limpio = self.limpiar_guion_para_tts(guion)
        bloques = self.dividir_en_bloques(texto_limpio)

        with open(ruta_salida, "wb") as f_out:
            for idx, bloque in enumerate(bloques):
                payload = {
                    "text": bloque,
                    "model_id": self.model_id,
                    "voice_settings": {
                        "stability": 0.45,
                        "similarity_boost": 0.80,
                        "style": 0.25,
                        "use_speaker_boost": True,
                    },
                }
                if idx > 0:
                    payload["previous_text"] = bloques[idx - 1][-300:]
                if idx < len(bloques) - 1:
                    payload["next_text"] = bloques[idx + 1][:300]

                res = requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
                    json=payload,
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    timeout=180,
                )
                res.raise_for_status()
                f_out.write(res.content)
        return ruta_salida


class PexelsService:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de Pexels.")
        self.api_key = api_key

    def buscar_videos(self, keyword, cantidad, orientacion):
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            params={
                "query": keyword,
                "per_page": cantidad,
                "orientation": orientacion,
                "size": "medium",
            },
            headers={"Authorization": self.api_key},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("videos", [])

    @staticmethod
    def elegir_mejor_archivo(video_obj, vertical=True):
        """Selecciona el archivo MP4 más cercano a 1080p/720p en vez de usar video_files[0] al azar."""
        archivos = [
            vf for vf in video_obj.get("video_files", [])
            if vf.get("link") and vf.get("file_type", "video/mp4") == "video/mp4"
        ]
        if not archivos:
            archivos = video_obj.get("video_files", [])
        if not archivos:
            return None

        target_altura = 1920 if vertical else 1080
        target_ancho = 1080 if vertical else 1920

        def puntaje(vf):
            w = vf.get("width") or 0
            h = vf.get("height") or 0
            # Penalizar resoluciones mayores a 1080p (4K muy pesados) o menores a 720p
            penalizacion_4k = 2000 if max(w, h) > 2000 else 0
            penalizacion_baja = 1500 if max(w, h) < 720 else 0
            return abs(w - target_ancho) + abs(h - target_altura) + penalizacion_4k + penalizacion_baja

        mejor = min(archivos, key=puntaje)
        return mejor.get("link")

    @staticmethod
    def descargar(url, ruta_salida):
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        with open(ruta_salida, "wb") as f:
            f.write(resp.content)
        return ruta_salida


class PixabayService:
    """
    Banco de videos HD/4K 100% GRATIS con API Key.
    Obtén tu key gratis en: https://pixabay.com/api/docs/
    """

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de Pixabay (es 100% gratis en pixabay.com/api/docs/).")
        self.api_key = api_key

    def buscar_videos(self, keyword, cantidad=3):
        resp = requests.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": self.api_key,
                "q": keyword,
                "per_page": max(3, cantidad),
                "video_type": "film",
                "safesearch": "true",
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("hits", [])

    @staticmethod
    def elegir_mejor_archivo(hit_obj):
        """Elige la variante HD (medium = 1080p o large = 1920p) de Pixabay."""
        videos = hit_obj.get("videos", {})
        for calidad in ("medium", "large", "small", "tiny"):
            url = videos.get(calidad, {}).get("url")
            if url:
                return url
        return None


class PollinationsService:
    """
    Generador de Imágenes IA con modelo FLUX 100% GRATIS ($0.00).
    Se combina con el motor Ken Burns para crear clips en movimiento a costo cero.
    """

    @staticmethod
    def generar_imagen_flux(prompt, ruta_salida, vertical=True, api_key=None):
        ancho, alto = (1080, 1920) if vertical else (1920, 1080)
        seed = random.randint(1, 999999)
        prompt_url = requests.utils.quote(prompt)
        url = (
            f"https://image.pollinations.ai/prompt/{prompt_url}"
            f"?width={ancho}&height={alto}&model=flux&nologo=true&seed={seed}"
        )
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = requests.get(url, headers=headers, timeout=90)
        resp.raise_for_status()
        with open(ruta_salida, "wb") as f:
            f.write(resp.content)
        return ruta_salida


class ReplicateVideoService:
    """
    Plataforma Pago-Por-Uso por segundo de GPU (Wan 2.1 Ultra Económico, LTX-Video, Hailuo).
    Obtén tu token en: https://replicate.com/account/api-tokens
    """

    MODELOS = {
        "Wan 2.1 (Económico ~$0.05/clip)": "wavespeedai/wan-2.1-t2v-480p",
        "Minimax Video-01 (Cine)": "minimax/video-01",
    }

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta el API Token de Replicate.")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generar_video(self, prompt, ruta_salida, modelo_nombre="Wan 2.1 (Económico ~$0.05/clip)", vertical=True, max_intentos=60):
        modelo_slug = self.MODELOS.get(modelo_nombre, "wavespeedai/wan-2.1-t2v-480p")
        aspect_ratio = "9:16" if vertical else "16:9"
        resp = requests.post(
            f"https://api.replicate.com/v1/models/{modelo_slug}/predictions",
            headers=self.headers,
            json={"input": {"prompt": prompt, "aspect_ratio": aspect_ratio}},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        pred = resp.json()
        url_estado = pred.get("urls", {}).get("get")
        if not url_estado:
            raise Exception("Replicate no devolvió URL de seguimiento.")

        for _ in range(max_intentos):
            r_est = requests.get(url_estado, headers=self.headers, timeout=REQUEST_TIMEOUT)
            r_est.raise_for_status()
            data = r_est.json()
            status = data.get("status")
            if status == "succeeded":
                output = data.get("output")
                video_url = output[0] if isinstance(output, list) else output
                vid = requests.get(video_url, timeout=REQUEST_TIMEOUT)
                vid.raise_for_status()
                with open(ruta_salida, "wb") as f:
                    f.write(vid.content)
                return ruta_salida
            if status in ("failed", "canceled"):
                raise Exception(f"Replicate falló ({status}): {data.get('error')}")
            time.sleep(8)
        raise TimeoutError("Replicate tardó demasiado en generar el video.")


class StabilityVideoService:
    """Generador de video IA (Stability AI - Image to Video)."""

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de Stability AI.")
        self.api_key = api_key

    def iniciar_generacion(self, ruta_imagen):
        with open(ruta_imagen, "rb") as f:
            resp = requests.post(
                "https://api.stability.ai/v2beta/image-to-video",
                headers={"authorization": f"Bearer {self.api_key}"},
                files={"image": f},
                data={"seed": 0, "cfg_scale": 1.8, "motion_bucket_id": 127},
                timeout=REQUEST_TIMEOUT,
            )
        resp.raise_for_status()
        return resp.json().get("id")

    def descargar_resultado(self, generation_id, ruta_salida, max_intentos=30):
        for _ in range(max_intentos):
            resp = requests.get(
                f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}",
                headers={
                    "authorization": f"Bearer {self.api_key}",
                    "accept": "video/*",
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 202:
                time.sleep(10)
                continue
            resp.raise_for_status()
            with open(ruta_salida, "wb") as f:
                f.write(resp.content)
            return ruta_salida
        raise TimeoutError("Stability tardó demasiado en generar el video.")


class RunwayVideoService:
    """Plantilla para integración oficial de Runway (SDK o API)."""

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de Runway.")
        self.api_key = api_key

    def generar_desde_imagen(self, ruta_imagen, prompt, ruta_salida):
        raise NotImplementedError(
            "Configura aquí tu integración oficial de Runway (SDK o API)."
        )


class FalVideoService:
    """
    Generador de video e imagen IA vía Fal.ai (Pago por uso puro sin mensualidad).
    Incluye Kling 3.0 (Standard y Pro), ingeniería de cámara estilo Higgsfield,
    y los motores más baratos del mercado (Flux Schnell $0.003, LTX $0.02, Wan 2.1 $0.05).
    Obtén tu key en: https://fal.ai/dashboard/keys
    """

    MODELOS = {
        "Kling 3.0 Standard (~$0.42/clip - Top Cine)": "fal-ai/kling-video/v3/standard/text-to-video",
        "Kling 3.0 Pro (~$0.56/clip - Master)": "fal-ai/kling-video/v3/pro/text-to-video",
        "Wan 2.1 (~$0.05/clip Calidad/Precio)": "fal-ai/wan-t2v",
        "LTX-Video (~$0.02/clip Ultra Barato)": "fal-ai/ltx-video",
        "Flux Schnell + Ken Burns (~$0.003/clip)": "fal-ai/flux/schnell",
        "Kling 1.6 Standard (Económico)": "fal-ai/kling-video/v1.6/standard/text-to-video",
        "MiniMax Hailuo (Realismo Top)": "fal-ai/minimax/video-01",
        "Seedance Lite": "fal-ai/bytedance/seedance/v1/lite/text-to-video",
        "Luma Dream Machine": "fal-ai/luma-dream-machine",
    }

    CAMARAS_HIGGSFIELD = {
        "Automático (Rotar cámaras Higgsfield)": [
            "Higgsfield DoP style fast crash zoom-in onto subject, 35mm anamorphic lens, subtle film grain, motion blur",
            "Dynamic FPV drone sweeping shot flying through scene, ultra-cinematic lighting, shallow depth of field",
            "Slow dramatic dolly-in push shot, 35mm cinema camera, volumetric lighting, high contrast shadows",
            "Handheld documentary tracking camera movement, raw hyperrealistic texture, natural lens flare",
            "Bullet-time slow-motion orbital camera pan around subject, dramatic rim lighting, IMAX 70mm look",
        ],
        "Crash Zoom (Impacto Brutal para Ganchos)": (
            "Higgsfield DoP signature whip crash zoom-in, sudden dramatic focus, 35mm anamorphic lens, cinematic motion blur"
        ),
        "FPV Drone (Vuelo Épico Cinematográfico)": (
            "High-speed FPV drone camera sweeping smoothly through the environment, epic scale, photorealistic 35mm film"
        ),
        "Dolly In Anamórfico 35mm (Documental Pro)": (
            "Slow tension-building dolly-in camera movement, 35mm anamorphic bokeh, moody volumetric lighting, film grain"
        ),
        "Handheld / Cámara en Mano Realista": (
            "Organic handheld cinema camera movement, gritty hyperrealistic documentary aesthetic, natural lighting"
        ),
        "Bullet Time / Cámara Lenta Orbital": (
            "Slow-motion 120fps orbital camera arc around the subject, suspended particles, dramatic Hollywood lighting"
        ),
    }

    @classmethod
    def aplicar_camara_higgsfield(cls, prompt_base, opcion_camara, idx_escena=0, estilo_genero=None):
        preset = cls.CAMARAS_HIGGSFIELD.get(opcion_camara)
        if isinstance(preset, list):
            directiva_camara = preset[idx_escena % len(preset)]
        elif isinstance(preset, str):
            directiva_camara = preset
        else:
            directiva_camara = cls.CAMARAS_HIGGSFIELD["Automático (Rotar cámaras Higgsfield)"][0]
        base_visual = estilo_genero or "Cinematic hyperrealistic scene, 8k resolution"
        return (
            f"{base_visual}: {prompt_base}. "
            f"Camera direction: {directiva_camara}. "
            f"No text, no watermark."
        )

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de Fal.ai.")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def _endpoint(self, modelo):
        ruta = self.MODELOS.get(modelo, "fal-ai/wan-t2v")
        return f"https://queue.fal.run/{ruta}"

    def generar_imagen_flux_schnell(self, prompt, ruta_imagen, vertical=True):
        """Genera una imagen hiperrealista con Flux Schnell en Fal.ai (~$0.003 USD)."""
        image_size = "portrait_16_9" if vertical else "landscape_16_9"
        resp = requests.post(
            "https://fal.run/fal-ai/flux/schnell",
            headers=self.headers,
            json={"prompt": prompt, "image_size": image_size, "num_inference_steps": 4},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        img_url = resp.json()["images"][0]["url"]
        img_bytes = requests.get(img_url, timeout=REQUEST_TIMEOUT)
        img_bytes.raise_for_status()
        with open(ruta_imagen, "wb") as f:
            f.write(img_bytes.content)
        return ruta_imagen

    def iniciar_generacion(self, prompt, modelo, vertical=True):
        aspect_ratio = "9:16" if vertical else "16:9"
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }
        if "Kling" in modelo or "Seedance" in modelo:
            payload["duration"] = "5"
        resp = requests.post(
            self._endpoint(modelo),
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["request_id"], data.get("status_url"), data.get("response_url")

    def esperar_y_descargar(self, status_url, response_url, ruta_salida, max_intentos=60):
        for _ in range(max_intentos):
            status_resp = requests.get(status_url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            status_resp.raise_for_status()
            estado = status_resp.json().get("status")

            if estado == "COMPLETED":
                final = requests.get(response_url, headers=self.headers, timeout=REQUEST_TIMEOUT)
                final.raise_for_status()
                datos_final = final.json()
                video_url = (
                    datos_final.get("video", {}).get("url")
                    or (datos_final.get("videos", [{}])[0].get("url") if datos_final.get("videos") else None)
                )
                if not video_url:
                    raise Exception(f"Fal.ai no devolvió URL de video: {datos_final}")
                video_bytes = requests.get(video_url, timeout=REQUEST_TIMEOUT)
                video_bytes.raise_for_status()
                with open(ruta_salida, "wb") as f:
                    f.write(video_bytes.content)
                return ruta_salida

            if estado in ("FAILED", "ERROR"):
                raise Exception(f"Fal.ai falló al generar el video (estado: {estado}).")

            time.sleep(8)

        raise TimeoutError("Fal.ai tardó demasiado en generar el video.")


class ClippingService:
    """
    Módulo de Clipping Viral y Re-edición Inteligente:
    1. Descarga videos virales de YouTube, Shorts, TikTok, Instagram Reels o X usando yt-dlp.
    2. Extrae el audio y detecta los momentos más virales con Whisper + OpenAI.
    3. Recorta clips automáticamente en formato 9:16 o 16:9 con Transformación Anti-Copyright
       (Espejo Horizontal + Zoom Dinámico 106% + Reencuadre) o los divide en B-Roll para Remix con nueva voz.
    """

    @staticmethod
    def asegurar_yt_dlp():
        try:
            import yt_dlp  # noqa: F401
            return True
        except ImportError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "yt-dlp", "--quiet"],
                check=True,
                timeout=120,
            )
            return True

    @classmethod
    def descargar_video_url(cls, url, carpeta_destino):
        """Descarga un video desde YouTube, TikTok, Reels o X en formato MP4 listo para reeditar."""
        if not url:
            raise ValueError("Ingresa un enlace (URL) válido de YouTube, TikTok, Instagram o X.")
        cls.asegurar_yt_dlp()
        import yt_dlp

        os.makedirs(carpeta_destino, exist_ok=True)
        timestamp = int(time.time())
        plantilla_salida = os.path.join(carpeta_destino, f"viral_source_{timestamp}.%(ext)s")

        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
            "outtmpl": plantilla_salida,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            archivo_descargado = ydl.prepare_filename(info)
            if not os.path.exists(archivo_descargado):
                base, _ = os.path.splitext(archivo_descargado)
                if os.path.exists(base + ".mp4"):
                    archivo_descargado = base + ".mp4"
            titulo_original = info.get("title", "Video Viral")
            duracion = info.get("duration", 0)
            return archivo_descargado, titulo_original, duracion

    @staticmethod
    def extraer_audio(ruta_video, ruta_audio_salida):
        clip = VideoFileClip(ruta_video)
        try:
            if clip.audio is None:
                raise ValueError("El video seleccionado no contiene pista de audio.")
            clip.audio.write_audiofile(ruta_audio_salida, fps=16000, nbytes=2, codec="libmp3lame", logger=None)
            duracion = clip.duration
        finally:
            clip.close()
        return ruta_audio_salida, duracion

    @staticmethod
    def formatear_transcripcion_con_timestamps(transcript_obj):
        segmentos = getattr(transcript_obj, "segments", None)
        if not segmentos and isinstance(transcript_obj, dict):
            segmentos = transcript_obj.get("segments", [])
        lineas = []
        if segmentos:
            for seg in segmentos:
                ini = seg.get("start", 0.0) if isinstance(seg, dict) else getattr(seg, "start", 0.0)
                fin = seg.get("end", 0.0) if isinstance(seg, dict) else getattr(seg, "end", 0.0)
                txt = (seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", "")).strip()
                lineas.append(f"[{ini:.1f}s - {fin:.1f}s] {txt}")
        else:
            palabras = getattr(transcript_obj, "words", None) or []
            bloque_actual = []
            ini_bloque = 0.0
            for idx, w in enumerate(palabras):
                palabra = w.get("word", "") if isinstance(w, dict) else getattr(w, "word", "")
                ini = w.get("start", 0.0) if isinstance(w, dict) else getattr(w, "start", 0.0)
                fin = w.get("end", 0.0) if isinstance(w, dict) else getattr(w, "end", 0.0)
                if not bloque_actual:
                    ini_bloque = ini
                bloque_actual.append(palabra)
                if len(bloque_actual) >= 10 or idx == len(palabras) - 1:
                    lineas.append(f"[{ini_bloque:.1f}s - {fin:.1f}s] {' '.join(bloque_actual)}")
                    bloque_actual = []
        return "\n".join(lineas)

    @staticmethod
    def recortar_y_transformar_clip(
        ruta_video_origen,
        inicio,
        fin,
        ruta_salida,
        formato_actual="SHORT",
        anti_copyright=True,
        conservar_audio=True,
    ):
        """
        Recorta un subclip, lo adapta a 9:16 o 16:9, y aplica filtros Anti-Copyright
        (Modo Espejo Horizontal + Zoom 108% + ligero ajuste de velocidad 1.03x opcional)
        para evitar detección de contenido duplicado al resubir.
        """
        from moviepy.video.fx import all as vfx

        clip = VideoFileClip(ruta_video_origen)
        try:
            ini_seguro = max(0.0, min(float(inicio), clip.duration - 1.0))
            fin_seguro = max(ini_seguro + 1.5, min(float(fin), clip.duration))
            sub = clip.subclip(ini_seguro, fin_seguro)

            if not conservar_audio:
                sub = sub.without_audio()

            # Aplicar Espejo Horizontal y Zoom extra si anti_copyright está activo
            if anti_copyright:
                sub = sub.fx(vfx.mirror_x)
                sub = sub.fx(vfx.colorx, 1.06)

            ancho_obj, alto_obj = (1080, 1920) if formato_actual == "SHORT" else (1920, 1080)
            factor_zoom = 1.08 if anti_copyright else 1.0

            ratio_clip = sub.w / sub.h
            ratio_target = ancho_obj / alto_obj
            if ratio_clip > ratio_target:
                sub = sub.resize(height=int(alto_obj * factor_zoom))
            else:
                sub = sub.resize(width=int(ancho_obj * factor_zoom))

            sub = sub.crop(
                x_center=sub.w / 2,
                y_center=sub.h / 2,
                width=ancho_obj,
                height=alto_obj,
            )

            sub.write_videofile(
                ruta_salida,
                fps=24,
                codec="libx264",
                audio_codec="aac" if conservar_audio else None,
                logger=None,
            )
            sub.close()
        finally:
            clip.close()
        return ruta_salida


class VideoRenderer:
    """Lógica de recorte, efecto Ken Burns (zoom dinámico), mezcla de música y subtítulos virales Pro."""

    FUENTES_WINDOWS = [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
    ]

    def __init__(self, formato_actual):
        self.formato_actual = formato_actual

    @property
    def dimensiones(self):
        if self.formato_actual == "SHORT":
            return 1080, 1920
        return 1920, 1080

    @classmethod
    def cargar_fuente(cls, tamano):
        for ruta in cls.FUENTES_WINDOWS:
            if os.path.exists(ruta):
                try:
                    return PIL.ImageFont.truetype(ruta, tamano)
                except Exception:
                    continue
        return PIL.ImageFont.load_default()

    def procesar_recorte_clip(self, ruta_clip, duracion):
        ancho, alto = self.dimensiones
        clip_orig = VideoFileClip(ruta_clip).without_audio()
        if clip_orig.duration < duracion:
            clip = afx.audio_loop(clip_orig, duration=duracion) if False else clip_orig.loop(duration=duracion)
        else:
            clip = clip_orig.subclip(0, duracion)
        ratio_obj = ancho / alto
        if (clip.w / clip.h) > ratio_obj:
            clip = clip.resize(height=alto)
        else:
            clip = clip.resize(width=ancho)
        return crop(
            clip,
            width=ancho,
            height=alto,
            x_center=clip.w / 2,
            y_center=clip.h / 2,
        )

    def convertir_imagen_a_clip(self, ruta_imagen, ruta_video, duracion=4, zoom_max=0.14):
        """Convierte una imagen estática en un clip de video con efecto Ken Burns (Zoom suave progresivo)."""
        ancho, alto = self.dimensiones
        img_base = PIL.Image.open(ruta_imagen).convert("RGB")
        ratio_obj = ancho / alto
        w_orig, h_orig = img_base.size

        if (w_orig / h_orig) > ratio_obj:
            nuevo_h = int(alto * (1 + zoom_max))
            nuevo_w = int(w_orig * (nuevo_h / h_orig))
        else:
            nuevo_w = int(ancho * (1 + zoom_max))
            nuevo_h = int(h_orig * (nuevo_w / w_orig))

        img_base = img_base.resize((nuevo_w, nuevo_h), PIL.Image.Resampling.LANCZOS)

        def generar_frame_ken_burns(get_frame, t):
            progreso = min(1.0, max(0.0, t / max(duracion, 0.1)))
            escala = 1.0 + (zoom_max * progreso)
            recorte_w = int(nuevo_w / escala)
            recorte_h = int(nuevo_h / escala)
            x1 = max(0, (nuevo_w - recorte_w) // 2)
            y1 = max(0, (nuevo_h - recorte_h) // 2)
            recortada = img_base.crop((x1, y1, x1 + recorte_w, y1 + recorte_h))
            final_pil = recortada.resize((ancho, alto), PIL.Image.Resampling.BILINEAR)
            return np.array(final_pil)

        clip = ImageClip(np.array(img_base.resize((ancho, alto)))).set_duration(duracion)
        clip = clip.fl(generar_frame_ken_burns)
        clip.write_videofile(
            ruta_video,
            fps=24,
            codec="libx264",
            audio=False,
            logger=None,
        )
        clip.close()
        return ruta_video

    def obtener_miniatura(self, ruta_video):
        try:
            clip = VideoFileClip(ruta_video)
            frame = clip.get_frame(min(0.5, clip.duration / 2))
            clip.close()
            imagen_pil = PIL.Image.fromarray(frame)
            return ctk.CTkImage(
                light_image=imagen_pil,
                dark_image=imagen_pil,
                size=(90, 50),
            )
        except Exception:
            logging.exception("No se pudo generar miniatura de %s", ruta_video)
            return None

    def _renderizar_bloque_subtitulo(self, palabras_bloque, idx_activa, color_acento, color_base, stroke_color, stroke_width, fontsize):
        ancho_video, _ = self.dimensiones
        ancho_lienzo = int(ancho_video * 0.92)
        alto_lienzo = int(fontsize * 2.8)
        img = PIL.Image.new("RGBA", (ancho_lienzo, alto_lienzo), (0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(img)
        fuente = self.cargar_fuente(fontsize)

        textos = [w.word.upper().strip() for w in palabras_bloque if w.word.strip()]
        if not textos:
            return None

        espacio = draw.textlength(" ", font=fuente)
        anchos = [draw.textlength(t, font=fuente) for t in textos]
        ancho_total = sum(anchos) + espacio * max(0, len(textos) - 1)

        # Si el bloque es más ancho que el lienzo, reducimos fuente proporcionalmente
        if ancho_total > ancho_lienzo - 40:
            factor = (ancho_lienzo - 40) / max(ancho_total, 1)
            fuente = self.cargar_fuente(max(32, int(fontsize * factor)))
            espacio = draw.textlength(" ", font=fuente)
            anchos = [draw.textlength(t, font=fuente) for t in textos]
            ancho_total = sum(anchos) + espacio * max(0, len(textos) - 1)

        x_actual = (ancho_lienzo - ancho_total) / 2
        y_pos = (alto_lienzo - fontsize) / 2

        for i, palabra in enumerate(textos):
            es_numero_o_dinero = bool(re.search(r"[\d\$%€]", palabra))
            color_palabra = color_acento if (i == idx_activa or es_numero_o_dinero) else color_base
            # Sombra profunda para contraste en cualquier video
            draw.text(
                (x_actual + 4, y_pos + 4),
                palabra,
                font=fuente,
                fill=(0, 0, 0, 210),
                stroke_width=stroke_width,
                stroke_fill=(0, 0, 0, 210),
            )
            draw.text(
                (x_actual, y_pos),
                palabra,
                font=fuente,
                fill=color_palabra,
                stroke_width=stroke_width,
                stroke_fill=stroke_color,
            )
            x_actual += anchos[i] + espacio

        return np.array(img)

    def crear_subtitulos(self, transcript, estilo, palabras_por_bloque=3):
        """
        Genera subtítulos estilo Hormozi / Viral en bloques cortos de 2-3 palabras,
        resaltando la palabra activa y números/dinero sin depender de ImageMagick.
        """
        clips_texto = []
        if "Hormozi" in estilo:
            color_acento, color_base, stroke_color, stroke_width = "#FFD700", "#FFFFFF", "#000000", 5
            fontsize = 78 if self.formato_actual == "SHORT" else 58
        elif "Clásico" in estilo:
            color_acento, color_base, stroke_color, stroke_width = "#00E676", "#FFFFFF", "#000000", 4
            fontsize = 68 if self.formato_actual == "SHORT" else 50
        else:
            color_acento, color_base, stroke_color, stroke_width = "#FF1744", "#FFFFFF", "#000000", 5
            fontsize = 82 if self.formato_actual == "SHORT" else 62

        palabras = [w for w in getattr(transcript, "words", []) if getattr(w, "word", "").strip()]
        if not palabras:
            return clips_texto

        pos_y = 0.72 if self.formato_actual == "SHORT" else 0.78

        for i in range(0, len(palabras), palabras_por_bloque):
            bloque = palabras[i : i + palabras_por_bloque]
            for idx_local, word_info in enumerate(bloque):
                inicio = word_info.start
                fin = bloque[idx_local + 1].start if idx_local + 1 < len(bloque) else word_info.end
                if fin - inicio <= 0.02:
                    fin = inicio + 0.15
                try:
                    rgba_array = self._renderizar_bloque_subtitulo(
                        bloque,
                        idx_local,
                        color_acento,
                        color_base,
                        stroke_color,
                        stroke_width,
                        fontsize,
                    )
                    if rgba_array is None:
                        continue
                    txt_clip = (
                        ImageClip(rgba_array, transparent=True)
                        .set_position(("center", pos_y), relative=True)
                        .set_start(inicio)
                        .set_end(fin)
                    )
                    clips_texto.append(txt_clip)
                except Exception:
                    logging.exception("Error creando bloque de subtítulo")
                    continue
        return clips_texto

    @staticmethod
    def mezclar_audio_con_musica(audio_voz, ruta_musica, volumen_musica=0.10):
        """Mezcla la locución con música de fondo en bucle (Auto-Ducking) y fadeout final."""
        if not ruta_musica or not os.path.exists(ruta_musica):
            return audio_voz, None
        try:
            bgm = AudioFileClip(ruta_musica)
            if bgm.duration < audio_voz.duration:
                bgm_loop = afx.audio_loop(bgm, duration=audio_voz.duration)
            else:
                bgm_loop = bgm.subclip(0, audio_voz.duration)
            bgm_loop = bgm_loop.volumex(volumen_musica).audio_fadeout(min(1.5, audio_voz.duration * 0.1))
            mezcla = CompositeAudioClip([bgm_loop, audio_voz]).set_duration(audio_voz.duration)
            return mezcla, bgm
        except Exception:
            logging.exception("No se pudo mezclar música de fondo")
            return audio_voz, None


# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
class StudioApp(ctk.CTk):
    ARCHIVO_VOZ = "voz_temp.mp3"
    ARCHIVO_KEYS = "config_keys.json"
    ARCHIVO_CACHE = "cache_proyecto.json"
    ARCHIVO_HISTORIAL = "historial_serie.txt"
    CARPETA_ASSETS = "assets_generados"

    def __init__(self):
        super().__init__()
        self.title("🎬 Studio Automator Pro v14.0 - AI Scene Sync & Dynamic FX")
        self.geometry("1340x880")
        os.makedirs(self.CARPETA_ASSETS, exist_ok=True)

        self.keywords_actuales = []
        self.prompts_visuales = []
        self.escenas_guion = []
        self.pool_videos = []
        self.formato_actual = "SHORT"
        self.ruta_musica_fondo = ""

        self.timeline_data = []
        self.duracion_total_audio = 0
        self.ruta_video_publicar = ""
        self.imagenes_timeline = []
        self.ruta_video_clipping = ""
        self.clips_virales_detectados = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self.crear_panel_izquierdo()
        self.crear_panel_derecho()

        self.cargar_keys()
        self.cargar_cache()

    # ==========================================
    # HELPERS DE HILOS Y ESTADO
    # ==========================================
    def ejecutar_en_hilo(self, funcion):
        threading.Thread(target=funcion, daemon=True).start()

    def mostrar_estado(self, mensaje, color="white"):
        self.after(0, lambda: self.lbl_estado.configure(text=mensaje, text_color=color))

    def cambiar_estado_boton(self, boton, estado, texto=None):
        if texto:
            self.after(0, lambda: boton.configure(state=estado, text=texto))
        else:
            self.after(0, lambda: boton.configure(state=estado))

    @property
    def es_vertical(self):
        return self.formato_actual == "SHORT"

    @property
    def es_extra_largo(self):
        return self.formato_actual == "EXTRA_LARGO"

    def obtener_formato_seleccionado(self):
        val = self.menu_formato.get() if hasattr(self, "menu_formato") else "SHORT"
        if "SHORT" in val:
            return "SHORT"
        if "EXTRA LARGO" in val:
            return "EXTRA_LARGO"
        return "LARGO"

    @property
    def info_genero_actual(self):
        genero_key = self.menu_genero.get() if hasattr(self, "menu_genero") else ""
        return GENEROS_CANAL.get(
            genero_key,
            GENEROS_CANAL["💰 Finanzas, Negocios y Geopolítica"],
        )

    @property
    def estilo_visual_genero_actual(self):
        return self.info_genero_actual["estilo_visual_ia"]

    # ==========================================
    # PANEL IZQUIERDO
    # ==========================================
    def crear_panel_izquierdo(self):
        frame_izq = ctk.CTkScrollableFrame(self)
        frame_izq.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(
            frame_izq, text="⚙️ CONFIGURACIÓN",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(10, 5))

        self.entrada_tema = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Tema del Video...")
        self.entrada_tema.pack(padx=20, pady=5)

        self.menu_formato = ctk.CTkOptionMenu(
            frame_izq,
            values=[
                "SHORT (Vertical)",
                "LARGO (Horizontal Normal)",
                "EXTRA LARGO (Documental por Capítulos)",
            ],
            width=300,
        )
        self.menu_formato.pack(padx=20, pady=5)

        ctk.CTkLabel(
            frame_izq, text="🎭 Género / Nicho del Canal:",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#FFAB00",
        ).pack(anchor="w", padx=20, pady=(10, 0))
        self.menu_genero = ctk.CTkOptionMenu(
            frame_izq,
            values=list(GENEROS_CANAL.keys()),
            width=300,
            fg_color="#E65100",
        )
        self.menu_genero.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🧠 Motor de Inteligencia Artificial:").pack(anchor="w", padx=20, pady=(10, 0))
        self.menu_motor_ia = ctk.CTkOptionMenu(
            frame_izq,
            values=["gpt-4o (Alta Calidad / Largo)", "gpt-4o-mini (Rápido / Económico)"],
            width=300, fg_color="#E91E63",
        )
        self.menu_motor_ia.pack(padx=20, pady=5)

        ctk.CTkLabel(
            frame_izq, text="🎙️ Motor de Locución (Gratis / Pago por Uso):",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#00E676",
        ).pack(anchor="w", padx=20, pady=(12, 0))
        self.menu_motor_voz = ctk.CTkOptionMenu(
            frame_izq,
            values=[
                "Edge-TTS Neuronal (100% GRATIS - Sin Límites)",
                "OpenAI TTS-1 (Ultra Barato ~$0.01/short)",
                "OpenAI TTS-1-HD (Alta Definición ~$0.02/short)",
                "ElevenLabs Flash v2.5 (50% Mitad de Precio)",
                "ElevenLabs Multilingual v2 (Calidad Estudio)",
            ],
            width=300, fg_color="#00897B",
            command=self.actualizar_voces_disponibles,
        )
        self.menu_motor_voz.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🗣️ Voz del Narrador:").pack(anchor="w", padx=20, pady=(5, 0))
        self.menu_voz_eleven = ctk.CTkOptionMenu(
            frame_izq,
            values=list(EdgeTTSService.VOCES_GRATIS.keys()),
            width=300, fg_color="#1976D2",
        )
        self.menu_voz_eleven.pack(padx=20, pady=5)

        # FUENTE VISUAL
        ctk.CTkLabel(
            frame_izq, text="🎨 Fuente de Visuales (Gratis y Pago por Uso):",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#9C27B0",
        ).pack(anchor="w", padx=20, pady=(15, 0))
        self.menu_fuente_visual = ctk.CTkOptionMenu(
            frame_izq,
            values=[
                "🔥 Híbrido Viral (Gancho Kling 3.0 + Resto Gratis/Barato)",
                "Combo Gratis HD (Pexels + Pixabay)",
                "Pexels (Clips reales - Gratis)",
                "Pixabay (Clips reales - Gratis)",
                "Pollinations Flux IA (100% Gratis + Ken Burns)",
                "Fal.ai (Kling 3.0 / Wan 2.1 / LTX / Flux)",
                "Replicate (Pago por uso: Wan 2.1 / Minimax)",
                "OpenAI Images (IA + Zoom Ken Burns)",
                "Stability Video (IA)",
                "Runway Video (IA)",
            ],
            width=300, fg_color="#9C27B0",
        )
        self.menu_fuente_visual.pack(padx=20, pady=5)

        # MODELO FAL
        ctk.CTkLabel(frame_izq, text="🎞️ Modelo Fal.ai (Kling 3.0 / Económicos):").pack(anchor="w", padx=20, pady=(5, 0))
        self.menu_modelo_fal = ctk.CTkOptionMenu(
            frame_izq,
            values=list(FalVideoService.MODELOS.keys()),
            width=300, fg_color="#673AB7",
        )
        self.menu_modelo_fal.pack(padx=20, pady=5)

        # CÁMARA ESTILO HIGGSFIELD
        ctk.CTkLabel(frame_izq, text="🎥 Cámara Estilo Higgsfield (IA):").pack(anchor="w", padx=20, pady=(5, 0))
        self.menu_camara_higgsfield = ctk.CTkOptionMenu(
            frame_izq,
            values=list(FalVideoService.CAMARAS_HIGGSFIELD.keys()),
            width=300, fg_color="#AD1457",
        )
        self.menu_camara_higgsfield.pack(padx=20, pady=5)

        # MODELO REPLICATE
        ctk.CTkLabel(frame_izq, text="⚡ Modelo Replicate (Pago por uso):").pack(anchor="w", padx=20, pady=(5, 0))
        self.menu_modelo_replicate = ctk.CTkOptionMenu(
            frame_izq,
            values=list(ReplicateVideoService.MODELOS.keys()),
            width=300, fg_color="#512DA8",
        )
        self.menu_modelo_replicate.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🔑 API Keys (Gratis / Pago por uso):").pack(anchor="w", padx=20, pady=(15, 0))
        self.entrada_openai = ctk.CTkEntry(frame_izq, width=300, placeholder_text="OpenAI sk-...", show="*")
        self.entrada_openai.pack(padx=20, pady=2)
        self.entrada_eleven = ctk.CTkEntry(frame_izq, width=300, placeholder_text="ElevenLabs", show="*")
        self.entrada_eleven.pack(padx=20, pady=2)
        self.entrada_pexels = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Pexels (Gratis)", show="*")
        self.entrada_pexels.pack(padx=20, pady=2)
        self.entrada_pixabay = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Pixabay (Gratis en pixabay.com/api/docs)", show="*")
        self.entrada_pixabay.pack(padx=20, pady=2)
        self.entrada_fal = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Fal.ai (Pago por uso barato)", show="*")
        self.entrada_fal.pack(padx=20, pady=2)
        self.entrada_replicate = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Replicate r8_... (Pago por uso)", show="*")
        self.entrada_replicate.pack(padx=20, pady=2)
        self.entrada_stability = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Stability AI", show="*")
        self.entrada_stability.pack(padx=20, pady=2)
        self.entrada_runway = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Runway", show="*")
        self.entrada_runway.pack(padx=20, pady=2)

        self.btn_guardar = ctk.CTkButton(
            frame_izq, text="💾 Guardar Ajustes", command=self.guardar_keys,
            fg_color="#4CAF50", height=30,
        )
        self.btn_guardar.pack(padx=20, pady=10)

        ctk.CTkLabel(
            frame_izq, text="🎵 Música de Fondo (Auto-Ducking):",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#00BCD4",
        ).pack(anchor="w", padx=20, pady=(10, 2))
        frame_bgm = ctk.CTkFrame(frame_izq, fg_color="transparent")
        frame_bgm.pack(fill="x", padx=20, pady=2)
        self.btn_bgm = ctk.CTkButton(
            frame_bgm, text="📂 Elegir MP3 Fondo", command=self.seleccionar_musica_fondo,
            fg_color="#00838F", width=180, height=28,
        )
        self.btn_bgm.pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            frame_bgm, text="❌", width=36, height=28, fg_color="#555555",
            command=self.quitar_musica_fondo,
        ).pack(side="left")
        self.lbl_bgm = ctk.CTkLabel(frame_izq, text="Sin música de fondo", text_color="gray", font=ctk.CTkFont(size=12))
        self.lbl_bgm.pack(anchor="w", padx=20)
        self.slider_vol_bgm = ctk.CTkSlider(frame_izq, from_=0.02, to=0.35, number_of_steps=33, width=300)
        self.slider_vol_bgm.set(0.10)
        self.slider_vol_bgm.pack(padx=20, pady=4)

        ctk.CTkLabel(
            frame_izq, text="🔤 Subtítulos (Whisper IA):",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#E91E63",
        ).pack(anchor="w", padx=20, pady=(15, 5))
        self.switch_subs = ctk.CTkSwitch(frame_izq, text="Quemar Subtítulos Automáticos", progress_color="#E91E63")
        self.switch_subs.pack(anchor="w", padx=20, pady=5)
        self.switch_subs.select()

        self.menu_estilos_subs = ctk.CTkOptionMenu(
            frame_izq,
            values=[
                "Estilo Hormozi (Amarillo/Negro)",
                "Estilo Clásico (Blanco/Negro)",
                "Estilo Alerta (Rojo/Blanco)",
            ],
            width=300, fg_color="#333333",
        )
        self.menu_estilos_subs.pack(padx=20, pady=5)

        ctk.CTkLabel(
            frame_izq, text="📝 SEO (Para Guion y Publicación):",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 5))
        self.entrada_titulo = ctk.CTkEntry(frame_izq, width=300, placeholder_text="El título aparecerá aquí...")
        self.entrada_titulo.pack(padx=20, pady=5)

        self.caja_desc = ctk.CTkTextbox(frame_izq, width=300, height=80, wrap="word")
        self.caja_desc.pack(padx=20, pady=5)

        self.lbl_estado = ctk.CTkLabel(frame_izq, text="Estado: Listo.", text_color="green", wraplength=280)
        self.lbl_estado.pack(side="bottom", pady=20)

    # ==========================================
    # MEMORIA (KEYS Y CACHE)
    # ==========================================
    def seleccionar_musica_fondo(self):
        archivo = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.m4a")])
        if archivo:
            self.ruta_musica_fondo = archivo
            self.lbl_bgm.configure(text=f"🎵 {os.path.basename(archivo)}", text_color="#00E676")
            self.guardar_cache()

    def quitar_musica_fondo(self):
        self.ruta_musica_fondo = ""
        self.lbl_bgm.configure(text="Sin música de fondo", text_color="gray")
        self.guardar_cache()

    def limpiar_pool_clips(self):
        self.pool_videos = []
        self.timeline_data = []
        self.actualizar_lista_clips_ui()
        for w in self.timeline_ui.winfo_children():
            w.destroy()
        self.guardar_cache()
        self.mostrar_estado("🧹 Pool de clips limpiado para nuevo video.", "yellow")

    def actualizar_voces_disponibles(self, motor_elegido=None):
        motor = motor_elegido or self.menu_motor_voz.get()
        if motor.startswith("Edge-TTS"):
            voces = list(EdgeTTSService.VOCES_GRATIS.keys())
        elif motor.startswith("OpenAI"):
            voces = list(ElevenLabsService.VOCES_OPENAI.keys())
        else:
            voces = list(ElevenLabsService.VOCES.keys())
        self.menu_voz_eleven.configure(values=voces)
        if self.menu_voz_eleven.get() not in voces:
            self.menu_voz_eleven.set(voces[0])

    def guardar_keys(self):
        keys_data = {
            "openai": self.entrada_openai.get().strip(),
            "elevenlabs": self.entrada_eleven.get().strip(),
            "pexels": self.entrada_pexels.get().strip(),
            "pixabay": self.entrada_pixabay.get().strip(),
            "stability": self.entrada_stability.get().strip(),
            "runway": self.entrada_runway.get().strip(),
            "fal": self.entrada_fal.get().strip(),
            "replicate": self.entrada_replicate.get().strip(),
            "genero_canal": self.menu_genero.get(),
            "motor_ia": self.menu_motor_ia.get(),
            "motor_voz": self.menu_motor_voz.get(),
            "voz_eleven": self.menu_voz_eleven.get(),
            "fuente_visual": self.menu_fuente_visual.get(),
            "modelo_fal": self.menu_modelo_fal.get(),
            "camara_higgsfield": self.menu_camara_higgsfield.get(),
            "modelo_replicate": self.menu_modelo_replicate.get(),
        }
        try:
            with open(self.ARCHIVO_KEYS, "w") as f:
                json.dump(keys_data, f)
            self.mostrar_estado("✅ Ajustes guardados.", "#00FF00")
        except Exception as e:
            logging.exception("Error al guardar keys")
            self.mostrar_estado(f"❌ Error al guardar: {e}", "red")

    def cargar_keys(self):
        if not os.path.exists(self.ARCHIVO_KEYS):
            return
        try:
            with open(self.ARCHIVO_KEYS, "r") as f:
                k = json.load(f)
            if k.get("openai"):
                self.entrada_openai.insert(0, k["openai"])
            if k.get("elevenlabs"):
                self.entrada_eleven.insert(0, k["elevenlabs"])
            if k.get("pexels"):
                self.entrada_pexels.insert(0, k["pexels"])
            if k.get("pixabay"):
                self.entrada_pixabay.insert(0, k["pixabay"])
            if k.get("stability"):
                self.entrada_stability.insert(0, k["stability"])
            if k.get("runway"):
                self.entrada_runway.insert(0, k["runway"])
            if k.get("fal"):
                self.entrada_fal.insert(0, k["fal"])
            if k.get("replicate"):
                self.entrada_replicate.insert(0, k["replicate"])
            if k.get("genero_canal") and k["genero_canal"] in GENEROS_CANAL:
                self.menu_genero.set(k["genero_canal"])
            if k.get("motor_ia"):
                self.menu_motor_ia.set(k["motor_ia"])
            if k.get("motor_voz"):
                self.menu_motor_voz.set(k["motor_voz"])
                self.actualizar_voces_disponibles(k["motor_voz"])
            if k.get("voz_eleven"):
                self.menu_voz_eleven.set(k["voz_eleven"])
            if k.get("fuente_visual"):
                self.menu_fuente_visual.set(k["fuente_visual"])
            if k.get("modelo_fal") and k["modelo_fal"] in FalVideoService.MODELOS:
                self.menu_modelo_fal.set(k["modelo_fal"])
            if k.get("camara_higgsfield") and k["camara_higgsfield"] in FalVideoService.CAMARAS_HIGGSFIELD:
                self.menu_camara_higgsfield.set(k["camara_higgsfield"])
            if k.get("modelo_replicate") and k["modelo_replicate"] in ReplicateVideoService.MODELOS:
                self.menu_modelo_replicate.set(k["modelo_replicate"])
        except Exception:
            logging.exception("Error al cargar keys")

    def guardar_cache(self):
        datos = {
            "prompt": self.caja_prompt.get("0.0", "end").strip(),
            "guion": self.caja_guion.get("0.0", "end").strip(),
            "titulo": self.entrada_titulo.get(),
            "desc": self.caja_desc.get("0.0", "end").strip(),
            "videos": self.pool_videos,
            "keywords": self.keywords_actuales,
            "prompts_visuales": self.prompts_visuales,
            "escenas_guion": self.escenas_guion,
            "musica_fondo": self.ruta_musica_fondo,
        }
        try:
            with open(self.ARCHIVO_CACHE, "w") as f:
                json.dump(datos, f)
        except Exception:
            logging.exception("Error al guardar cache")

    def cargar_cache(self):
        if not os.path.exists(self.ARCHIVO_CACHE):
            return
        try:
            with open(self.ARCHIVO_CACHE, "r") as f:
                datos = json.load(f)
            if datos.get("prompt"):
                self.caja_prompt.insert("0.0", datos["prompt"])
            if datos.get("guion"):
                self.caja_guion.insert("0.0", datos["guion"])
            if datos.get("titulo"):
                self.entrada_titulo.insert(0, datos["titulo"])
            if datos.get("desc"):
                self.caja_desc.insert("0.0", datos["desc"])
            self.pool_videos = [v for v in datos.get("videos", []) if os.path.exists(v)]
            self.keywords_actuales = datos.get("keywords", [])
            self.prompts_visuales = datos.get("prompts_visuales", [])
            self.escenas_guion = datos.get("escenas_guion", [])
            if datos.get("musica_fondo") and os.path.exists(datos["musica_fondo"]):
                self.ruta_musica_fondo = datos["musica_fondo"]
                self.lbl_bgm.configure(text=f"🎵 {os.path.basename(self.ruta_musica_fondo)}", text_color="#00E676")
            self.actualizar_lista_clips_ui()
        except Exception:
            logging.exception("Error al cargar cache")

    # ==========================================
    # PANEL DERECHO
    # ==========================================
    def crear_panel_derecho(self):
        frame_der = ctk.CTkFrame(self)
        frame_der.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        ctk.CTkLabel(
            frame_der, text="🎛️ SALA DE PRODUCCIÓN",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(10, 5))

        self.pestanas = ctk.CTkTabview(frame_der, height=450)
        self.pestanas.pack(fill="both", padx=20, pady=(5, 15), expand=True)

        self.tab_guion = self.pestanas.add("📝 1. Guion y Prompt")
        self.tab_clips = self.pestanas.add("🎬 2. Gestor Clips")
        self.tab_timeline = self.pestanas.add("🎞️ 3. Storyboard (Timeline)")
        self.tab_publicar = self.pestanas.add("🚀 4. Publicador")
        self.tab_clipping = self.pestanas.add("✂️ 5. Clipping y Re-edición")

        # --- PESTAÑA 1 ---
        frame_titulo_guion = ctk.CTkFrame(self.tab_guion, fg_color="transparent")
        frame_titulo_guion.pack(fill="x", padx=5, pady=(5, 0))
        ctk.CTkLabel(
            frame_titulo_guion, text="🧠 Prompt Maestro:",
            font=ctk.CTkFont(weight="bold", size=15),
        ).pack(side="left")

        self.switch_serie = ctk.CTkSwitch(
            frame_titulo_guion,
            text="🔗 MODO SERIE (Continuar historia anterior)",
            progress_color="#9C27B0",
        )
        self.switch_serie.pack(side="right")

        self.caja_prompt = ctk.CTkTextbox(
            self.tab_guion, height=180, font=ctk.CTkFont(size=15),
            fg_color="#1e1e1e", border_color="#4CAF50", border_width=1, wrap="word",
        )
        self.caja_prompt.pack(fill="x", padx=5, pady=5)
        self.btn_enviar_prompt = ctk.CTkButton(
            self.tab_guion, text="🤖 Enviar al Guionista (OpenAI)",
            command=self.hilo_enviar_guionista, fg_color="#E91E63", height=35,
        )
        self.btn_enviar_prompt.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            self.tab_guion, text="📝 Guion de Locución:",
            font=ctk.CTkFont(weight="bold", size=15),
        ).pack(anchor="w", padx=5, pady=(10, 0))
        self.caja_guion = ctk.CTkTextbox(
            self.tab_guion, height=150, font=ctk.CTkFont(size=15),
            fg_color="#2b2b2b", wrap="word",
        )
        self.caja_guion.pack(fill="both", expand=True, padx=5, pady=5)

        # --- PESTAÑA 2 ---
        self.lista_clips_ui = ctk.CTkScrollableFrame(self.tab_clips, fg_color="#1a1a1a")
        self.lista_clips_ui.pack(fill="both", expand=True, padx=5, pady=5)
        frame_btn_clips = ctk.CTkFrame(self.tab_clips, fg_color="transparent")
        frame_btn_clips.pack(fill="x", padx=5, pady=5)
        self.btn_auto_clips = ctk.CTkButton(
            frame_btn_clips, text="🤖 Generar Visuales (Sincronizados)",
            command=self.hilo_paso3, fg_color="#9C27B0",
        )
        self.btn_auto_clips.pack(side="left", expand=True, padx=2)
        ctk.CTkButton(
            frame_btn_clips, text="💻 Cargar PC",
            command=self.cargar_desde_pc, fg_color="#FF9800",
        ).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(
            frame_btn_clips, text="🧹 Limpiar Pool",
            command=self.limpiar_pool_clips, fg_color="#455A64",
        ).pack(side="right", expand=True, padx=2)

        # --- PESTAÑA 3 ---
        self.timeline_ui = ctk.CTkScrollableFrame(self.tab_timeline, fg_color="#1a1a1a")
        self.timeline_ui.pack(fill="both", expand=True, padx=5, pady=5)
        frame_btn_exportar = ctk.CTkFrame(self.tab_timeline, fg_color="transparent")
        frame_btn_exportar.pack(fill="x", padx=5, pady=5)
        self.btn_exp_mp4 = ctk.CTkButton(
            frame_btn_exportar, text="⬇️ Exportar MP4 Final",
            command=self.hilo_exportar_mp4, fg_color="#F44336", state="disabled",
        )
        self.btn_exp_mp4.pack(side="left", expand=True, padx=5)
        self.btn_exp_capcut = ctk.CTkButton(
            frame_btn_exportar, text="📁 Exportar a CapCut",
            command=self.hilo_exportar_capcut, fg_color="#607D8B", state="disabled",
        )
        self.btn_exp_capcut.pack(side="right", expand=True, padx=5)

        # --- PESTAÑA 4 ---
        self.lbl_video_pub = ctk.CTkLabel(
            self.tab_publicar, text="Ningún video seleccionado.",
            text_color="yellow", font=ctk.CTkFont(weight="bold"),
        )
        self.lbl_video_pub.pack(pady=(10, 5))

        frame_btn_pub = ctk.CTkFrame(self.tab_publicar, fg_color="transparent")
        frame_btn_pub.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(
            frame_btn_pub, text="🎬 Usar Video del Proyecto",
            command=self.cargar_video_proyecto, fg_color="#2196F3",
        ).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(
            frame_btn_pub, text="📂 Cargar Video Externo (PC)",
            command=self.cargar_video_externo, fg_color="#FF9800",
        ).pack(side="right", expand=True, padx=2)

        ctk.CTkLabel(self.tab_publicar, text="Título del Video:").pack(anchor="w", padx=10, pady=(15, 0))
        self.entrada_titulo_pub = ctk.CTkEntry(self.tab_publicar, font=ctk.CTkFont(size=14))
        self.entrada_titulo_pub.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.tab_publicar, text="Descripción y Hashtags:").pack(anchor="w", padx=10, pady=(5, 0))
        self.caja_desc_pub = ctk.CTkTextbox(self.tab_publicar, height=100, wrap="word", font=ctk.CTkFont(size=13))
        self.caja_desc_pub.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.tab_publicar, text="Privacidad:").pack(anchor="w", padx=10, pady=(5, 0))
        self.menu_privacidad = ctk.CTkOptionMenu(
            self.tab_publicar, values=["Privado", "Oculto", "Público"], fg_color="#004D40"
        )
        self.menu_privacidad.pack(fill="x", padx=10, pady=5)

        self.btn_publicar_yt = ctk.CTkButton(
            self.tab_publicar, text="🚀 PUBLICAR EN YOUTUBE",
            command=self.hilo_publicar_youtube, fg_color="#D32F2F", height=40,
            font=ctk.CTkFont(weight="bold", size=15),
        )
        self.btn_publicar_yt.pack(fill="x", padx=10, pady=15)

        # --- PESTAÑA 5: CLIPPING Y RE-EDICIÓN VIRAL ---
        ctk.CTkLabel(
            self.tab_clipping,
            text="✂️ ESTUDIO DE CLIPPING Y RE-EDICIÓN DE VIDEOS VIRALES",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FFAB00",
        ).pack(anchor="w", padx=10, pady=(6, 2))

        frame_url_clip = ctk.CTkFrame(self.tab_clipping, fg_color="transparent")
        frame_url_clip.pack(fill="x", padx=10, pady=4)
        self.entrada_url_viral = ctk.CTkEntry(
            frame_url_clip,
            placeholder_text="Pega URL de YouTube, Shorts, TikTok, Instagram Reels o X...",
        )
        self.entrada_url_viral.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_descargar_viral = ctk.CTkButton(
            frame_url_clip,
            text="⬇️ Descargar URL",
            command=self.hilo_descargar_viral_url,
            fg_color="#E65100",
            width=145,
        )
        self.btn_descargar_viral.pack(side="left", padx=2)
        ctk.CTkButton(
            frame_url_clip,
            text="📂 Video PC",
            command=self.cargar_video_clipping_pc,
            fg_color="#546E7A",
            width=105,
        ).pack(side="left", padx=2)

        self.lbl_video_clipping = ctk.CTkLabel(
            self.tab_clipping,
            text="Ningún video viral cargado aún.",
            text_color="gray",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.lbl_video_clipping.pack(anchor="w", padx=12, pady=(0, 4))

        frame_opciones_clip = ctk.CTkFrame(self.tab_clipping, fg_color="transparent")
        frame_opciones_clip.pack(fill="x", padx=10, pady=4)
        self.switch_anticopyright = ctk.CTkSwitch(
            frame_opciones_clip,
            text="🛡️ Anti-Copyright (Espejo Horizontal + Zoom 108% + Color)",
            progress_color="#00E676",
        )
        self.switch_anticopyright.pack(side="left", padx=(0, 10))
        self.switch_anticopyright.select()

        self.menu_cant_clips = ctk.CTkOptionMenu(
            frame_opciones_clip,
            values=[
                "3 Clips Virales (15s - 40s)",
                "5 Clips Virales (15s - 40s)",
                "1 Clip Principal (25s - 55s)",
            ],
            width=210,
            fg_color="#37474F",
        )
        self.menu_cant_clips.pack(side="right")

        frame_acciones_clip = ctk.CTkFrame(self.tab_clipping, fg_color="transparent")
        frame_acciones_clip.pack(fill="x", padx=10, pady=4)
        self.btn_auto_clipping = ctk.CTkButton(
            frame_acciones_clip,
            text="✂️ MODO 1: Extraer Mejores Clips (Voz Original + Subs)",
            command=self.hilo_auto_clipping,
            fg_color="#FF6F00",
            height=34,
        )
        self.btn_auto_clipping.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_remix_completo = ctk.CTkButton(
            frame_acciones_clip,
            text="🔄 MODO 2: Re-editar con Tu Voz (Clonar Éxito + Nuevo Guion)",
            command=self.hilo_remix_completo,
            fg_color="#8E24AA",
            height=34,
        )
        self.btn_remix_completo.pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.lista_clipping_ui = ctk.CTkScrollableFrame(self.tab_clipping, fg_color="#1a1a1a")
        self.lista_clipping_ui.pack(fill="both", expand=True, padx=10, pady=6)

        # --- BOTONES DE FLUJO ---
        frame_flujo = ctk.CTkFrame(frame_der, fg_color="transparent")
        frame_flujo.pack(fill="x", padx=20, pady=5)
        self.btn_paso1 = ctk.CTkButton(
            frame_flujo, text="1. Generar Prompt",
            command=self.hilo_crear_prompt, fg_color="#4CAF50",
        )
        self.btn_paso1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.btn_paso2 = ctk.CTkButton(
            frame_flujo, text="2. Grabar Voz",
            command=self.hilo_paso2, fg_color="#2196F3",
        )
        self.btn_paso2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.btn_paso4 = ctk.CTkButton(
            frame_flujo, text="3. Crear Storyboard",
            command=self.hilo_generar_timeline, fg_color="#607D8B",
        )
        self.btn_paso4.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        frame_flujo.columnconfigure((0, 1, 2), weight=1)

    # ==========================================
    # UI Y STORYBOARD
    # ==========================================
    def actualizar_lista_clips_ui(self):
        for w in self.lista_clips_ui.winfo_children():
            w.destroy()
        for ruta in self.pool_videos:
            fila = ctk.CTkFrame(self.lista_clips_ui, fg_color="#2b2b2b")
            fila.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(fila, text=f"🎥 {os.path.basename(ruta)}").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(
                fila, text="❌", width=40, fg_color="#D32F2F",
                command=lambda r=ruta: self.eliminar_clip(r),
            ).pack(side="right", padx=5)

    def eliminar_clip(self, ruta):
        if ruta in self.pool_videos:
            self.pool_videos.remove(ruta)
        self.actualizar_lista_clips_ui()
        self.guardar_cache()

    def cargar_desde_pc(self):
        archivos = filedialog.askopenfilenames(filetypes=[("Videos", "*.mp4 *.mov")])
        if archivos:
            for arch in archivos:
                if arch not in self.pool_videos:
                    self.pool_videos.append(arch)
            self.actualizar_lista_clips_ui()
            self.guardar_cache()

    def dibujar_timeline_ui(self):
        self.mostrar_estado("Generando previsualización del Storyboard...", "orange")
        for w in self.timeline_ui.winfo_children():
            w.destroy()
        self.imagenes_timeline = []

        renderer = VideoRenderer(self.formato_actual)

        pista_audio = ctk.CTkFrame(self.timeline_ui, fg_color="#004D40", corner_radius=0)
        pista_audio.pack(fill="x", pady=5)
        ctk.CTkLabel(
            pista_audio,
            text=f"🎵 PISTA DE VOZ (Duración: {self.duracion_total_audio:.1f}s)",
            font=ctk.CTkFont(weight="bold"),
        ).pack(pady=10)

        ctk.CTkLabel(
            self.timeline_ui,
            text="🎬 STORYBOARD (Puedes Reordenar o Cambiar Clips)", anchor="w",
        ).pack(fill="x", pady=(10, 0))

        for i, item in enumerate(self.timeline_data):
            bloque = ctk.CTkFrame(self.timeline_ui, fg_color="#1565C0", border_color="black", border_width=1)
            bloque.pack(fill="x", pady=2, padx=10)

            img = renderer.obtener_miniatura(item["archivo"])
            if img:
                self.imagenes_timeline.append(img)
                ctk.CTkLabel(bloque, image=img, text="").pack(side="left", padx=5, pady=5)

            narracion_escena = item.get("narracion", "")
            subtexto_escena = f"\n🗣️ \"{narracion_escena[:65]}...\"" if narracion_escena else ""
            texto = (
                f"Escena #{item['orden']} [{item['inicio']:.1f}s - {item['fin']:.1f}s] "
                f"({item['duracion']:.1f}s)\n🎥 {os.path.basename(item['archivo'])}{subtexto_escena}"
            )
            ctk.CTkLabel(bloque, text=texto, justify="left").pack(side="left", padx=10)

            frame_controles = ctk.CTkFrame(bloque, fg_color="transparent")
            frame_controles.pack(side="right", padx=10)

            btn_up = ctk.CTkButton(
                frame_controles, text="⬆️", width=30, fg_color="#555555",
                command=lambda idx=i: self.mover_clip_arriba(idx),
            )
            btn_up.pack(side="left", padx=2)
            if i == 0:
                btn_up.configure(state="disabled")

            btn_down = ctk.CTkButton(
                frame_controles, text="⬇️", width=30, fg_color="#555555",
                command=lambda idx=i: self.mover_clip_abajo(idx),
            )
            btn_down.pack(side="left", padx=2)
            if i == len(self.timeline_data) - 1:
                btn_down.configure(state="disabled")

            ctk.CTkButton(
                frame_controles, text="🔄 Cambiar", width=60, fg_color="#E65100",
                command=lambda idx=i: self.reemplazar_clip(idx),
            ).pack(side="left", padx=5)

        self.mostrar_estado("✅ Storyboard interactivo listo.", "green")

    def mover_clip_arriba(self, idx):
        if idx > 0:
            self.timeline_data[idx]["archivo"], self.timeline_data[idx - 1]["archivo"] = (
                self.timeline_data[idx - 1]["archivo"],
                self.timeline_data[idx]["archivo"],
            )
            self.dibujar_timeline_ui()

    def mover_clip_abajo(self, idx):
        if idx < len(self.timeline_data) - 1:
            self.timeline_data[idx]["archivo"], self.timeline_data[idx + 1]["archivo"] = (
                self.timeline_data[idx + 1]["archivo"],
                self.timeline_data[idx]["archivo"],
            )
            self.dibujar_timeline_ui()

    def reemplazar_clip(self, idx):
        if len(self.pool_videos) > 1:
            opciones = [v for v in self.pool_videos if v != self.timeline_data[idx]["archivo"]]
            if opciones:
                self.timeline_data[idx]["archivo"] = random.choice(opciones)
                self.dibujar_timeline_ui()

    # ==========================================
    # HILOS
    # ==========================================
    def hilo_crear_prompt(self):
        self.ejecutar_en_hilo(self.ejecutar_crear_prompt)

    def hilo_enviar_guionista(self):
        self.ejecutar_en_hilo(self.ejecutar_enviar_guionista)

    def hilo_paso2(self):
        self.ejecutar_en_hilo(self.ejecutar_paso2)

    def hilo_paso3(self):
        self.ejecutar_en_hilo(self.ejecutar_paso3)

    def hilo_generar_timeline(self):
        self.ejecutar_en_hilo(self.ejecutar_generar_timeline)

    def hilo_exportar_mp4(self):
        self.ejecutar_en_hilo(self.ejecutar_exportar_mp4)

    def hilo_exportar_capcut(self):
        self.ejecutar_en_hilo(self.ejecutar_exportar_capcut)

    def hilo_publicar_youtube(self):
        self.ejecutar_en_hilo(self.ejecutar_publicar_youtube)

    def hilo_descargar_viral_url(self):
        self.ejecutar_en_hilo(self.ejecutar_descargar_viral_url)

    def hilo_auto_clipping(self):
        self.ejecutar_en_hilo(self.ejecutar_auto_clipping)

    def hilo_remix_completo(self):
        self.ejecutar_en_hilo(self.ejecutar_remix_completo)

    # ==========================================
    # PASO 1: PROMPT (MULTIGÉNERO DINÁMICO)
    # ==========================================
    def ejecutar_crear_prompt(self):
        self.after(0, lambda: self.pestanas.set("📝 1. Guion y Prompt"))
        tema = self.entrada_tema.get().strip()
        if not tema:
            self.mostrar_estado("❌ Escribe un tema primero.", "red")
            return

        self.formato_actual = self.obtener_formato_seleccionado()
        genero_nombre = self.menu_genero.get()
        info_gen = self.info_genero_actual

        if self.es_vertical:
            reglas_formato = f"""2. LONGITUD: Escribe un guion explosivo de máximo 90-110 palabras.
3. TONO DEL GÉNERO ({genero_nombre}): {info_gen['instruccion_tono']}
4. ESTRUCTURA (Gancho, Nudo y Desenlace):
   - GANCHO: Empieza en el segundo 0 con un impacto brutal o intriga extrema. CERO saludos.
   - NUDO: Desarrolla la historia/conflicto con ritmo trepidante y tensión constante.
   - DESENLACE: {info_gen['cierre_estructura']}"""
            num_keywords = "6 a 10"
            etiqueta_modo = ""
        elif self.es_extra_largo:
            reglas_formato = f"""2. MODO EXTRA LARGO POR CAPÍTULOS (DOCUMENTAL EXTENSO DE 20 A 28 MINUTOS):
   - El sistema redactará este documental en 5 CAPÍTULOS PROFUNDOS independientes (650 a 850 palabras por capítulo = ~3,500 a 4,200 palabras reales en total y 40 escenas visuales).
3. TONO DEL GÉNERO ({genero_nombre}): {info_gen['instruccion_tono']}
4. ESTRUCTURA DOCUMENTAL DE 5 ACTOS:
   - CAPÍTULO 1: Gancho brutal, planteamiento del misterio/problema central y promesa de revelación.
   - CAPÍTULO 2: El origen oculto, antecedentes históricos y contexto profundo.
   - CAPÍTULO 3: Análisis exhaustivo, casos reales con nombres y fechas, mecanismos internos.
   - CAPÍTULO 4: El clímax, giro inesperado, pruebas contundentes y consecuencias extremas.
   - CAPÍTULO 5: El impacto en el futuro y cierre magistral ({info_gen['cierre_estructura']})."""
            num_keywords = "40 (8 por cada uno de los 5 capítulos)"
            etiqueta_modo = "[MODO EXTRA LARGO POR CAPÍTULOS]\n"
        else:
            reglas_formato = f"""2. LONGITUD: Escribe un guion MUY EXTENSO de 1600 a 1800 palabras (10-12 min). Usa [PAUSA] para silencios dramáticos.
3. TONO DEL GÉNERO ({genero_nombre}): {info_gen['instruccion_tono']}
4. ESTRUCTURA:
   - GANCHO: Revelación o escena inicial brutal.
   - NUDO: Explica TODOS los detalles, atmósfera y giros explícitamente. Desarrolla a fondo.
   - DESENLACE: {info_gen['cierre_estructura']}"""
            num_keywords = "15 a 20"
            etiqueta_modo = ""

        inyeccion_serie = ""
        if self.switch_serie.get() == 1 and os.path.exists(self.ARCHIVO_HISTORIAL):
            with open(self.ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                guion_anterior = f.read()[-4000:]
            inyeccion_serie = (
                f"\n\n[🚨 ALERTA: MODO SERIE ACTIVADO]: El usuario quiere que escribas la SIGUIENTE PARTE "
                f"de la historia. Aquí tienes el guion del episodio anterior para que mantengas la "
                f"continuidad, el tono y los personajes:\n\n--- GUION ANTERIOR ---\n{guion_anterior}\n"
                f"--- FIN GUION ANTERIOR ---\n\nTu tarea: Inicia este nuevo guion resolviendo el suspenso "
                f"del episodio anterior y crea un misterio completamente nuevo para este episodio."
            )

        prompt_base = f"""{etiqueta_modo}{info_gen['rol_guionista']}
Tu tema o idea para este episodio es: '{tema}'.

REGLAS DE ORO:
1. IDIOMA: TODO el guion, título y descripción DEBEN ESTAR EN ESPAÑOL (excepto las keywords y prompts visuales que van en INGLÉS).
{reglas_formato}
5. ESTILO VISUAL IA OBLIGATORIO PARA LAS ESCENAS: Adapta todos los 'prompt_ia' a la estética: "{info_gen['estilo_visual_ia']}"{inyeccion_serie}

(IMPORTANTE: Tu respuesta DEBE ser estrictamente un objeto JSON con estas llaves:
- 'guion_locucion': (tu texto completo en ESPAÑOL aplicando la estructura)
- 'escenas': (lista ordenada cronológicamente de {num_keywords} escenas que componen el guion; cada elemento debe ser un objeto con:
    - 'narracion': el fragmento exacto del guion que se narra en esta escena,
    - 'keyword_pexels': búsqueda corta de 2-4 palabras en INGLÉS para banco de video stock que represente visualmente esta escena,
    - 'prompt_ia': prompt cinematográfico detallado en INGLÉS siguiendo el estilo "{info_gen['estilo_visual_ia']}", sin texto ni marcas de agua)
- 'keywords_visuales': (lista en el mismo orden de los conceptos en INGLÉS de cada escena)
- 'prompts_visuales': (lista en el mismo orden de los prompts DETALLADOS en INGLÉS de cada escena)
- 'titulo_seo': (Un título magnético de alto CTR acorde al género {genero_nombre})
- 'descripcion_seo': (Descripción persuasiva con hashtags del nicho))."""

        self.after(0, lambda: self.caja_prompt.delete("0.0", "end"))
        self.after(0, lambda: self.caja_prompt.insert("0.0", prompt_base))
        self.mostrar_estado(
            f"✅ Mega-Prompt ({self.formato_actual}) creado para: {genero_nombre}",
            "yellow",
        )

    # ==========================================
    # PASO 1b: ENVIAR A OPENAI
    # ==========================================
    def ejecutar_enviar_guionista(self):
        prompt_final = self.caja_prompt.get("0.0", "end").strip()
        if not prompt_final:
            self.mostrar_estado("❌ Primero genera el prompt.", "red")
            return

        self.formato_actual = self.obtener_formato_seleccionado()
        self.cambiar_estado_boton(self.btn_enviar_prompt, "disabled")
        try:
            service = OpenAIService(self.entrada_openai.get().strip())
            modelo = self.menu_motor_ia.get().split()[0]

            if self.es_extra_largo or "[MODO EXTRA LARGO POR CAPÍTULOS]" in prompt_final:
                self.formato_actual = "EXTRA_LARGO"
                datos = service.generar_guion_extra_largo(
                    modelo,
                    prompt_final,
                    genero_key=self.menu_genero.get(),
                    callback_progreso=lambda msg: self.mostrar_estado(msg, "orange"),
                )
            else:
                self.mostrar_estado("Enviando a OpenAI... diseñando guion y escenas sincronizadas...", "orange")
                datos = service.generar_guion(modelo, prompt_final, genero_key=self.menu_genero.get())

            self.escenas_guion = datos.get("escenas", [])
            self.keywords_actuales = datos.get("keywords_visuales", [])
            self.prompts_visuales = datos.get("prompts_visuales", [])

            if self.escenas_guion:
                if not self.keywords_actuales:
                    self.keywords_actuales = [
                        e.get("keyword_pexels", "") for e in self.escenas_guion if e.get("keyword_pexels")
                    ]
                if not self.prompts_visuales:
                    self.prompts_visuales = [
                        e.get("prompt_ia", "") for e in self.escenas_guion if e.get("prompt_ia")
                    ]

            guion_generado = datos.get("guion_locucion", "")
            if not guion_generado and self.escenas_guion:
                guion_generado = " ".join(e.get("narracion", "") for e in self.escenas_guion).strip()
            if not guion_generado:
                guion_generado = "Hubo un error."

            self.after(0, lambda: self.caja_guion.delete("0.0", "end"))
            self.after(0, lambda: self.caja_guion.insert("0.0", guion_generado))

            if "titulo_seo" in datos:
                self.after(0, lambda: self.entrada_titulo.delete(0, "end"))
                self.after(0, lambda: self.entrada_titulo.insert(0, datos["titulo_seo"]))
            if "descripcion_seo" in datos:
                self.after(0, lambda: self.caja_desc.delete("0.0", "end"))
                self.after(0, lambda: self.caja_desc.insert("0.0", datos["descripcion_seo"]))

            with open(self.ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
                f.write(guion_generado)

            self.guardar_cache()
            num_palabras = len(guion_generado.split())
            self.mostrar_estado(
                f"✅ Guion ({num_palabras} palabras) y {len(self.escenas_guion) or len(self.keywords_actuales)} escenas listas.",
                "green",
            )
        except Exception as e:
            logging.exception("Error OpenAI")
            self.mostrar_estado(f"❌ Error OpenAI: {e}", "red")
        finally:
            self.cambiar_estado_boton(self.btn_enviar_prompt, "normal")

    # ==========================================
    # PASO 2: VOZ (MULTIMOTOR: GRATIS / OPENAI / ELEVENLABS)
    # ==========================================
    def ejecutar_paso2(self):
        guion = self.caja_guion.get("0.0", "end").strip()
        if not guion:
            self.mostrar_estado("❌ Primero genera o escribe un guion.", "red")
            return

        motor_voz = self.menu_motor_voz.get()
        voz_seleccionada = self.menu_voz_eleven.get()
        self.cambiar_estado_boton(self.btn_paso2, "disabled")
        try:
            if motor_voz.startswith("Edge-TTS"):
                self.mostrar_estado(f"🎙️ Grabando Voz Neuronal GRATIS ({voz_seleccionada})...", "yellow")
                EdgeTTSService.generar_voz(guion, self.ARCHIVO_VOZ, nombre_voz=voz_seleccionada)
                self.mostrar_estado("✅ Voz Neuronal Gratis guardada con éxito ($0.00).", "green")

            elif motor_voz.startswith("OpenAI"):
                modelo_tts = "tts-1-hd" if "HD" in motor_voz else "tts-1"
                voz_id = ElevenLabsService.VOCES_OPENAI.get(voz_seleccionada, "onyx")
                self.mostrar_estado(f"🎙️ Grabando Voz con OpenAI {modelo_tts} ({voz_id})...", "yellow")
                service = OpenAIService(self.entrada_openai.get().strip())
                service.generar_voz_tts(guion, self.ARCHIVO_VOZ, voz=voz_id, modelo_tts=modelo_tts)
                self.mostrar_estado(f"✅ Voz OpenAI ({modelo_tts}) guardada con éxito.", "green")

            else:
                model_id = "eleven_flash_v2_5" if "Flash" in motor_voz else "eleven_multilingual_v2"
                voice_id = ElevenLabsService.VOCES.get(voz_seleccionada)
                self.mostrar_estado(f"🎙️ Grabando Voz con ElevenLabs ({model_id})...", "yellow")
                service = ElevenLabsService(
                    self.entrada_eleven.get().strip(),
                    voice_id=voice_id,
                    model_id=model_id,
                )
                service.generar_voz(guion, self.ARCHIVO_VOZ)
                self.mostrar_estado(f"✅ Voz ElevenLabs ({model_id}) guardada con éxito.", "green")

        except requests.HTTPError as e:
            logging.exception("Error HTTP en Voz")
            self.mostrar_estado(
                f"❌ Error ElevenLabs ({e}). Tip: Cambia el motor a 'Edge-TTS Gratis' o 'OpenAI TTS-1'.",
                "red",
            )
        except Exception as e:
            logging.exception("Error Voz")
            self.mostrar_estado(f"❌ Error Voz: {e}", "red")
        finally:
            self.cambiar_estado_boton(self.btn_paso2, "normal")

    # ==========================================
    # PASO 3: VISUALES
    # ==========================================
    def ejecutar_paso3(self):
        fuente = self.menu_fuente_visual.get()
        if not self.keywords_actuales and not self.prompts_visuales:
            self.mostrar_estado("❌ Primero genera el guion (necesito keywords/prompts).", "red")
            return

        self.cambiar_estado_boton(self.btn_auto_clips, "disabled", "Generando...")
        try:
            # Limpiamos el pool anterior para que el nuevo video quede 100% sincronizado en orden
            self.pool_videos = []
            if "Híbrido Viral" in fuente:
                self.generar_clips_hibrido_viral()
            elif fuente.startswith("Combo Gratis"):
                self.generar_clips_combo_gratis()
            elif fuente.startswith("Pexels"):
                self.generar_clips_pexels()
            elif fuente.startswith("Pixabay"):
                self.generar_clips_pixabay()
            elif fuente.startswith("Pollinations"):
                self.generar_clips_pollinations()
            elif fuente.startswith("OpenAI Images"):
                self.generar_clips_imagenes_openai()
            elif fuente.startswith("Stability Video"):
                self.generar_clips_stability_video()
            elif fuente.startswith("Runway Video"):
                self.generar_clips_runway_video()
            elif fuente.startswith("Fal.ai"):
                self.generar_clips_fal()
            elif fuente.startswith("Replicate"):
                self.generar_clips_replicate()

            self.after(0, self.actualizar_lista_clips_ui)
            self.after(0, lambda: self.pestanas.set("🎬 2. Gestor Clips"))
            self.guardar_cache()
        except Exception as e:
            logging.exception("Error generando visuales")
            self.mostrar_estado(f"❌ Error visuales: {e}", "red")
        finally:
            self.cambiar_estado_boton(self.btn_auto_clips, "normal", "🤖 Generar Visuales (Sincronizados)")

    def generar_clips_pexels(self):
        self.mostrar_estado("Buscando clips HD en Pexels en orden de escena...", "yellow")
        service = PexelsService(self.entrada_pexels.get().strip())
        ori = "portrait" if self.es_vertical else "landscape"
        cantidad = 1 if self.es_vertical else (3 if self.es_extra_largo else 2)
        urls_descargadas = set()

        for idx_kw, kw in enumerate(self.keywords_actuales):
            try:
                self.mostrar_estado(
                    f"🔎 Pexels escena {idx_kw + 1}/{len(self.keywords_actuales)}: {kw}...",
                    "yellow",
                )
                videos = service.buscar_videos(kw, max(cantidad + 2, 4), ori)
            except Exception:
                logging.exception("Error buscando %s en Pexels", kw)
                continue
            descargados_escena = 0
            for i, v in enumerate(videos):
                if descargados_escena >= cantidad:
                    break
                nombre = os.path.join(
                    self.CARPETA_ASSETS,
                    f"escena_{idx_kw:02d}_{limpiar_nombre(kw)}_{i}.mp4",
                )
                try:
                    url_hd = PexelsService.elegir_mejor_archivo(v, vertical=self.es_vertical)
                    if not url_hd or url_hd in urls_descargadas:
                        continue
                    PexelsService.descargar(url_hd, nombre)
                    urls_descargadas.add(url_hd)
                    if nombre not in self.pool_videos:
                        self.pool_videos.append(nombre)
                    descargados_escena += 1
                except Exception:
                    logging.exception("Error descargando clip de Pexels")
        self.mostrar_estado(f"✅ {len(self.pool_videos)} Clips HD únicos de Pexels descargados.", "green")

    def generar_clips_pixabay(self):
        self.mostrar_estado("Buscando clips HD en Pixabay (100% Gratis)...", "yellow")
        service = PixabayService(self.entrada_pixabay.get().strip())
        cantidad = 1 if self.es_vertical else (3 if self.es_extra_largo else 2)
        urls_descargadas = set()

        for idx_kw, kw in enumerate(self.keywords_actuales):
            try:
                self.mostrar_estado(
                    f"🔎 Pixabay escena {idx_kw + 1}/{len(self.keywords_actuales)}: {kw}...",
                    "yellow",
                )
                hits = service.buscar_videos(kw, cantidad=max(cantidad + 2, 5))
            except Exception:
                logging.exception("Error buscando %s en Pixabay", kw)
                continue
            descargados_escena = 0
            for i, h in enumerate(hits):
                if descargados_escena >= cantidad:
                    break
                nombre = os.path.join(
                    self.CARPETA_ASSETS,
                    f"pixabay_{idx_kw:02d}_{limpiar_nombre(kw)}_{i}.mp4",
                )
                try:
                    url_hd = PixabayService.elegir_mejor_archivo(h)
                    if not url_hd or url_hd in urls_descargadas:
                        continue
                    PexelsService.descargar(url_hd, nombre)
                    urls_descargadas.add(url_hd)
                    if nombre not in self.pool_videos:
                        self.pool_videos.append(nombre)
                    descargados_escena += 1
                except Exception:
                    logging.exception("Error descargando clip de Pixabay")
        self.mostrar_estado(f"✅ {len(self.pool_videos)} Clips HD únicos de Pixabay descargados.", "green")

    def generar_clips_combo_gratis(self):
        """Alterna y respalda automáticamente entre Pexels y Pixabay para máxima variedad a costo $0."""
        self.mostrar_estado("Buscando en Combo Gratis HD (Pexels + Pixabay)...", "yellow")
        key_pexels = self.entrada_pexels.get().strip()
        key_pixabay = self.entrada_pixabay.get().strip()
        if not key_pexels and not key_pixabay:
            raise ValueError("Ingresa al menos tu API Key gratuita de Pexels o de Pixabay.")

        pexels = PexelsService(key_pexels) if key_pexels else None
        pixabay = PixabayService(key_pixabay) if key_pixabay else None
        ori = "portrait" if self.es_vertical else "landscape"
        clips_por_escena = 1 if self.es_vertical else (2 if self.es_extra_largo else 1)
        urls_descargadas = set()

        for idx_kw, kw in enumerate(self.keywords_actuales):
            descargados_escena = 0
            usar_pixabay_primero = (idx_kw % 2 == 1) and (pixabay is not None)
            orden_fuentes = ["pixabay", "pexels"] if usar_pixabay_primero else ["pexels", "pixabay"]

            for fuente in orden_fuentes:
                if descargados_escena >= clips_por_escena:
                    break
                if fuente == "pexels" and pexels:
                    try:
                        self.mostrar_estado(
                            f"🔎 Combo Gratis [{idx_kw + 1}/{len(self.keywords_actuales)}] Pexels: {kw}...",
                            "yellow",
                        )
                        videos = pexels.buscar_videos(kw, 4, ori)
                        for i_v, vid in enumerate(videos):
                            if descargados_escena >= clips_por_escena:
                                break
                            url_hd = PexelsService.elegir_mejor_archivo(vid, vertical=self.es_vertical)
                            if url_hd and url_hd not in urls_descargadas:
                                nombre = os.path.join(
                                    self.CARPETA_ASSETS,
                                    f"combo_{idx_kw:02d}_pexels_{i_v}_{limpiar_nombre(kw)}.mp4",
                                )
                                PexelsService.descargar(url_hd, nombre)
                                urls_descargadas.add(url_hd)
                                self.pool_videos.append(nombre)
                                descargados_escena += 1
                    except Exception:
                        logging.exception("Fallback de Pexels en Combo Gratis")
                elif fuente == "pixabay" and pixabay:
                    try:
                        self.mostrar_estado(
                            f"🔎 Combo Gratis [{idx_kw + 1}/{len(self.keywords_actuales)}] Pixabay: {kw}...",
                            "yellow",
                        )
                        hits = pixabay.buscar_videos(kw, cantidad=4)
                        for i_h, hit in enumerate(hits):
                            if descargados_escena >= clips_por_escena:
                                break
                            url_hd = PixabayService.elegir_mejor_archivo(hit)
                            if url_hd and url_hd not in urls_descargadas:
                                nombre = os.path.join(
                                    self.CARPETA_ASSETS,
                                    f"combo_{idx_kw:02d}_pixabay_{i_h}_{limpiar_nombre(kw)}.mp4",
                                )
                                PexelsService.descargar(url_hd, nombre)
                                urls_descargadas.add(url_hd)
                                self.pool_videos.append(nombre)
                                descargados_escena += 1
                    except Exception:
                        logging.exception("Fallback de Pixabay en Combo Gratis")

        self.mostrar_estado(f"✅ {len(self.pool_videos)} Clips Combo Gratis HD listos.", "green")

    def generar_clips_pollinations(self):
        """Genera escenas con IA Flux 100% GRATIS ($0) en Pollinations y las anima con Ken Burns."""
        self.mostrar_estado("Generando escenas IA con Pollinations Flux (100% Gratis)...", "yellow")
        renderer = VideoRenderer(self.formato_actual)
        prompts = self.prompts_visuales or self.keywords_actuales
        estilo_visual = self.estilo_visual_genero_actual

        for i, prompt in enumerate(prompts):
            prompt_img = (
                f"{estilo_visual}: {prompt}. "
                f"No text, no watermark."
            )
            ruta_img = os.path.join(self.CARPETA_ASSETS, f"flux_free_{i:02d}.png")
            ruta_video = os.path.join(self.CARPETA_ASSETS, f"flux_free_clip_{i:02d}.mp4")
            try:
                self.mostrar_estado(
                    f"🎨 Pollinations Flux Gratis {i + 1}/{len(prompts)} + Zoom Ken Burns...",
                    "yellow",
                )
                PollinationsService.generar_imagen_flux(prompt_img, ruta_img, vertical=self.es_vertical)
                renderer.convertir_imagen_a_clip(ruta_img, ruta_video, duracion=5)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except Exception:
                logging.exception("Error en Pollinations Flux escena %s", i)
        self.mostrar_estado("✅ Clips IA Gratis (Pollinations Flux + Ken Burns) listos.", "green")

    def generar_clips_replicate(self):
        modelo = self.menu_modelo_replicate.get()
        self.mostrar_estado(f"Generando video IA en Replicate ({modelo})...", "yellow")
        replicate = ReplicateVideoService(self.entrada_replicate.get().strip())
        prompts = self.prompts_visuales or self.keywords_actuales
        estilo_visual = self.estilo_visual_genero_actual

        for i, prompt in enumerate(prompts):
            prompt_video = (
                f"{estilo_visual}: {prompt}. "
                f"Smooth camera movement, no text, no watermark."
            )
            ruta_video = os.path.join(self.CARPETA_ASSETS, f"replicate_{i:02d}.mp4")
            try:
                self.mostrar_estado(f"⚡ Replicate {i + 1}/{len(prompts)} ({modelo})...", "yellow")
                replicate.generar_video(prompt_video, ruta_video, modelo_nombre=modelo, vertical=self.es_vertical)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except Exception:
                logging.exception("Error generando video Replicate %s", i)
        self.mostrar_estado("✅ Clips de video IA (Replicate) generados.", "green")

    def generar_clips_imagenes_openai(self):
        self.mostrar_estado("Generando imágenes con IA + Efecto Ken Burns...", "yellow")
        service = OpenAIService(self.entrada_openai.get().strip())
        renderer = VideoRenderer(self.formato_actual)
        prompts = self.prompts_visuales or self.keywords_actuales
        estilo_visual = self.estilo_visual_genero_actual

        for i, prompt in enumerate(prompts):
            prompt_img = (
                f"{estilo_visual}: {prompt}. "
                f"High detail, no text, no watermark."
            )
            ruta_img = os.path.join(self.CARPETA_ASSETS, f"ai_image_{i:02d}.png")
            ruta_video = os.path.join(self.CARPETA_ASSETS, f"ai_clip_{i:02d}.mp4")
            try:
                self.mostrar_estado(f"🎨 Imagen IA {i + 1}/{len(prompts)} (Zoom Dinámico)...", "yellow")
                service.generar_imagen(prompt_img, ruta_img, vertical=self.es_vertical)
                renderer.convertir_imagen_a_clip(ruta_img, ruta_video, duracion=5)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except Exception:
                logging.exception("Error generando imagen IA %s", i)
        self.mostrar_estado("✅ Clips IA con efecto Ken Burns generados.", "green")

    def generar_clips_stability_video(self):
        self.mostrar_estado("Generando video IA (Stability)...", "yellow")
        openai_service = OpenAIService(self.entrada_openai.get().strip())
        stability = StabilityVideoService(self.entrada_stability.get().strip())
        prompts = self.prompts_visuales or self.keywords_actuales
        estilo_visual = self.estilo_visual_genero_actual

        for i, prompt in enumerate(prompts):
            prompt_img = (
                f"{estilo_visual}: {prompt}. "
                f"High detail, no text, no watermark."
            )
            ruta_img = os.path.join(self.CARPETA_ASSETS, f"ai_base_{i:02d}.png")
            ruta_video = os.path.join(self.CARPETA_ASSETS, f"stability_clip_{i:02d}.mp4")
            try:
                self.mostrar_estado(f"🎬 Video IA {i + 1}/{len(prompts)} (imagen base)...", "yellow")
                openai_service.generar_imagen(prompt_img, ruta_img, vertical=self.es_vertical)

                self.mostrar_estado(f"🎬 Animando clip {i + 1}/{len(prompts)}...", "yellow")
                gen_id = stability.iniciar_generacion(ruta_img)
                stability.descargar_resultado(gen_id, ruta_video)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except Exception:
                logging.exception("Error generando video Stability %s", i)
        self.mostrar_estado("✅ Clips de video IA (Stability) generados.", "green")

    def generar_clips_runway_video(self):
        self.mostrar_estado("Generando video IA (Runway)...", "yellow")
        openai_service = OpenAIService(self.entrada_openai.get().strip())
        runway = RunwayVideoService(self.entrada_runway.get().strip())
        prompts = self.prompts_visuales or self.keywords_actuales

        for i, prompt in enumerate(prompts):
            ruta_img = os.path.join(self.CARPETA_ASSETS, f"ai_base_runway_{i:02d}.png")
            ruta_video = os.path.join(self.CARPETA_ASSETS, f"runway_clip_{i:02d}.mp4")
            try:
                openai_service.generar_imagen(prompt, ruta_img, vertical=self.es_vertical)
                runway.generar_desde_imagen(ruta_img, prompt, ruta_video)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except NotImplementedError:
                self.mostrar_estado(
                    "⚠️ Runway aún no está configurado. Edita RunwayVideoService.", "orange"
                )
                return
            except Exception:
                logging.exception("Error generando video Runway %s", i)
        self.mostrar_estado("✅ Clips de video IA (Runway) generados.", "green")

    def generar_clips_fal(self):
        modelo = self.menu_modelo_fal.get()
        estilo_camara = self.menu_camara_higgsfield.get()
        estilo_visual = self.estilo_visual_genero_actual
        self.mostrar_estado(f"Generando con Fal.ai ({modelo})...", "yellow")
        fal = FalVideoService(self.entrada_fal.get().strip())
        renderer = VideoRenderer(self.formato_actual)
        prompts = self.prompts_visuales or self.keywords_actuales

        for i, prompt in enumerate(prompts):
            prompt_video = FalVideoService.aplicar_camara_higgsfield(
                prompt, estilo_camara, idx_escena=i, estilo_genero=estilo_visual
            )
            ruta_video = os.path.join(self.CARPETA_ASSETS, f"fal_{limpiar_nombre(modelo)}_{i:02d}.mp4")
            try:
                self.mostrar_estado(f"🎬 Fal.ai {modelo} {i + 1}/{len(prompts)}...", "yellow")
                if "Flux Schnell" in modelo:
                    ruta_img = os.path.join(self.CARPETA_ASSETS, f"fal_flux_{i:02d}.png")
                    fal.generar_imagen_flux_schnell(prompt_video, ruta_img, vertical=self.es_vertical)
                    renderer.convertir_imagen_a_clip(ruta_img, ruta_video, duracion=5)
                else:
                    _, status_url, response_url = fal.iniciar_generacion(
                        prompt_video, modelo, vertical=self.es_vertical
                    )
                    fal.esperar_y_descargar(status_url, response_url, ruta_video)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except Exception:
                logging.exception("Error generando con Fal.ai %s", i)
        self.mostrar_estado(f"✅ Clips de Fal.ai ({modelo}) generados.", "green")

    def generar_clips_hibrido_viral(self):
        """
        Estrategia Pro de Retención + Bajo Costo:
        - Escena 1 (El Gancho de los primeros 5s): Se genera con Kling 3.0 Standard + Cámara Higgsfield Crash Zoom (~$0.42 USD).
        - Escenas 2..N (Resto del video): Se completan gratis con Pexels/Pixabay HD (o Pollinations Flux + Ken Burns si no hay clip).
        """
        self.mostrar_estado("🔥 Iniciando Modo Híbrido Viral (Gancho Kling 3.0 + Resto Gratis)...", "yellow")
        key_fal = self.entrada_fal.get().strip()
        key_pexels = self.entrada_pexels.get().strip()
        key_pixabay = self.entrada_pixabay.get().strip()
        renderer = VideoRenderer(self.formato_actual)
        estilo_visual = self.estilo_visual_genero_actual

        prompts = self.prompts_visuales or self.keywords_actuales
        keywords = self.keywords_actuales or self.prompts_visuales
        total_escenas = max(len(prompts), len(keywords))

        # 1. ESCENA 0 (EL GANCHO): Kling 3.0 Standard + Cámara Higgsfield
        gancho_listo = False
        if key_fal and prompts:
            try:
                fal = FalVideoService(key_fal)
                modelo_kling3 = "Kling 3.0 Standard (~$0.42/clip - Top Cine)"
                prompt_gancho = FalVideoService.aplicar_camara_higgsfield(
                    prompts[0],
                    "Crash Zoom (Impacto Brutal para Ganchos)",
                    idx_escena=0,
                    estilo_genero=estilo_visual,
                )
                ruta_gancho = os.path.join(self.CARPETA_ASSETS, "hibrido_00_GANCHO_KLING3.mp4")
                self.mostrar_estado("🔥 Generando Gancho (Escena 1) con Kling 3.0 + Cámara Higgsfield...", "orange")
                _, status_url, response_url = fal.iniciar_generacion(
                    prompt_gancho, modelo_kling3, vertical=self.es_vertical
                )
                fal.esperar_y_descargar(status_url, response_url, ruta_gancho)
                self.pool_videos.append(ruta_gancho)
                gancho_listo = True
            except Exception:
                logging.exception("Fallback en Gancho Kling 3.0")

        # 2. ESCENAS RESTANTES (o Escena 0 si no había API Key de Fal): Pexels/Pixabay Gratis -> Fallback Pollinations Flux Gratis
        pexels = PexelsService(key_pexels) if key_pexels else None
        pixabay = PixabayService(key_pixabay) if key_pixabay else None
        ori = "portrait" if self.es_vertical else "landscape"

        inicio_idx = 1 if gancho_listo else 0
        for idx in range(inicio_idx, total_escenas):
            kw = keywords[idx] if idx < len(keywords) else prompts[idx]
            prompt_esc = prompts[idx] if idx < len(prompts) else kw
            descargado = False

            if pexels and (idx % 2 == 1 or not pixabay):
                try:
                    self.mostrar_estado(f"🔎 Híbrido Escena {idx + 1}/{total_escenas} (Pexels Gratis): {kw}...", "yellow")
                    videos = pexels.buscar_videos(kw, 1, ori)
                    if videos:
                        url_hd = PexelsService.elegir_mejor_archivo(videos[0], vertical=self.es_vertical)
                        if url_hd:
                            nombre = os.path.join(self.CARPETA_ASSETS, f"hibrido_{idx:02d}_pexels.mp4")
                            PexelsService.descargar(url_hd, nombre)
                            self.pool_videos.append(nombre)
                            descargado = True
                except Exception:
                    logging.exception("Fallback Pexels en modo híbrido")

            if not descargado and pixabay:
                try:
                    self.mostrar_estado(f"🔎 Híbrido Escena {idx + 1}/{total_escenas} (Pixabay Gratis): {kw}...", "yellow")
                    hits = pixabay.buscar_videos(kw, cantidad=3)
                    if hits:
                        url_hd = PixabayService.elegir_mejor_archivo(hits[0])
                        if url_hd:
                            nombre = os.path.join(self.CARPETA_ASSETS, f"hibrido_{idx:02d}_pixabay.mp4")
                            PexelsService.descargar(url_hd, nombre)
                            self.pool_videos.append(nombre)
                            descargado = True
                except Exception:
                    logging.exception("Fallback Pixabay en modo híbrido")

            if not descargado:
                try:
                    self.mostrar_estado(
                        f"🎨 Híbrido Escena {idx + 1}/{total_escenas} (Pollinations Flux Gratis + Ken Burns)...",
                        "yellow",
                    )
                    ruta_img = os.path.join(self.CARPETA_ASSETS, f"hibrido_{idx:02d}_flux.png")
                    ruta_vid = os.path.join(self.CARPETA_ASSETS, f"hibrido_{idx:02d}_flux.mp4")
                    prompt_cam = FalVideoService.aplicar_camara_higgsfield(
                        prompt_esc, self.menu_camara_higgsfield.get(), idx_escena=idx, estilo_genero=estilo_visual
                    )
                    PollinationsService.generar_imagen_flux(prompt_cam, ruta_img, vertical=self.es_vertical)
                    renderer.convertir_imagen_a_clip(ruta_img, ruta_vid, duracion=5)
                    self.pool_videos.append(ruta_vid)
                except Exception:
                    logging.exception("Error fallback Pollinations en modo híbrido")

        self.mostrar_estado("🔥 ¡Clips Modo Híbrido Viral (Gancho Kling 3.0 + Resto Gratis) listos!", "green")

    # ==========================================
    # PASO 3b: STORYBOARD (SINCRONIZADO POR ESCENA)
    # ==========================================
    def ejecutar_generar_timeline(self):
        self.mostrar_estado("Sincronizando Línea de Tiempo con Escenas del Guion...", "yellow")
        try:
            if not self.pool_videos:
                raise Exception("No hay clips cargados o generados.")
            if not os.path.exists(self.ARCHIVO_VOZ):
                raise Exception("Falta grabar la Voz (Paso 2).")

            audio_clip = AudioFileClip(self.ARCHIVO_VOZ)
            self.duracion_total_audio = audio_clip.duration
            audio_clip.close()

            self.timeline_data = []
            # Calculamos pesos proporcionales según la cantidad de palabras de cada escena
            pesos_escenas = []
            textos_escenas = []
            if self.escenas_guion:
                for esc in self.escenas_guion:
                    txt = esc.get("narracion", "").strip()
                    palabras = max(3, len(txt.split()))
                    pesos_escenas.append(palabras)
                    textos_escenas.append(txt)

            total_palabras = sum(pesos_escenas) if pesos_escenas else 0
            num_bloques = max(len(self.escenas_guion), len(self.pool_videos))

            tiempo_act = 0.0
            orden = 1
            idx_clip = 0
            max_corte = 7.5 if self.es_extra_largo else 6.0

            while tiempo_act < self.duracion_total_audio - 0.05:
                video_elegido = self.pool_videos[idx_clip % len(self.pool_videos)]
                narracion_asociada = ""

                if pesos_escenas and total_palabras > 0:
                    # Calculamos qué escena corresponde al progreso actual del audio
                    progreso = min(0.999, tiempo_act / max(0.1, self.duracion_total_audio))
                    idx_escena_actual = min(len(pesos_escenas) - 1, int(progreso * len(pesos_escenas)))
                    narracion_asociada = textos_escenas[idx_escena_actual]

                    if len(self.pool_videos) <= len(pesos_escenas) and idx_clip < len(pesos_escenas):
                        proporcion = pesos_escenas[idx_clip] / total_palabras
                        duracion_objetivo = max(2.2, min(max_corte, self.duracion_total_audio * proporcion))
                    else:
                        duracion_objetivo = max(3.0, min(max_corte, self.duracion_total_audio / max(1, num_bloques)))
                else:
                    duracion_objetivo = max(2.5, min(max_corte, self.duracion_total_audio / max(1, num_bloques)))

                corte = min(duracion_objetivo, self.duracion_total_audio - tiempo_act)
                clip_b = VideoFileClip(video_elegido)
                duracion_real = min(corte, max(1.5, clip_b.duration))
                clip_b.close()

                self.timeline_data.append({
                    "orden": orden,
                    "archivo": video_elegido,
                    "inicio": tiempo_act,
                    "fin": tiempo_act + duracion_real,
                    "duracion": duracion_real,
                    "narracion": narracion_asociada,
                })
                tiempo_act += duracion_real
                orden += 1
                idx_clip += 1

            self.after(0, self.dibujar_timeline_ui)
            self.after(0, lambda: self.pestanas.set("🎞️ 3. Storyboard (Timeline)"))
            self.cambiar_estado_boton(self.btn_exp_mp4, "normal")
            self.cambiar_estado_boton(self.btn_exp_capcut, "normal")
        except Exception as e:
            logging.exception("Error Timeline")
            self.mostrar_estado(f"❌ Error Timeline: {e}", "red")

    # ==========================================
    # PASO 4: EXPORTAR MP4
    # ==========================================
    def ejecutar_exportar_mp4(self):
        if not self.timeline_data:
            self.mostrar_estado("❌ Primero crea el storyboard.", "red")
            return

        self.mostrar_estado("Renderizando MP4 Final...", "yellow")
        self.cambiar_estado_boton(self.btn_exp_mp4, "disabled")

        renderer = VideoRenderer(self.formato_actual)
        clips_finales = []
        audio_clip = None
        bgm_clip = None
        video_final = None
        try:
            clips_finales = [
                renderer.procesar_recorte_clip(i["archivo"], i["duracion"])
                for i in self.timeline_data
            ]
            audio_clip = AudioFileClip(self.ARCHIVO_VOZ)
            audio_mezclado, bgm_clip = renderer.mezclar_audio_con_musica(
                audio_clip,
                self.ruta_musica_fondo,
                volumen_musica=float(self.slider_vol_bgm.get()),
            )
            video_final = concatenate_videoclips(clips_finales, method="compose").set_audio(audio_mezclado)

            if self.switch_subs.get() == 1:
                service = OpenAIService(self.entrada_openai.get().strip())
                self.mostrar_estado("🎧 Whisper IA sincronizando subtítulos virales...", "orange")
                transcript = service.transcribir(self.ARCHIVO_VOZ)
                clips_de_texto = renderer.crear_subtitulos(transcript, self.menu_estilos_subs.get())
                if clips_de_texto:
                    video_final = CompositeVideoClip([video_final] + clips_de_texto)

            ruta_salida = f"FINAL_{self.formato_actual}.mp4"
            video_final.write_videofile(
                ruta_salida, fps=24, codec="libx264", audio_codec="aac", logger=None
            )
            self.mostrar_estado("🎉 ¡MP4 FINAL CON SUBTÍTULOS Y AUDIO LISTO!", "#00FF00")

            self.cargar_video_proyecto()
            self.after(0, lambda: self.pestanas.set("🚀 4. Publicador"))
        except Exception as e:
            logging.exception("Error exportando MP4")
            self.mostrar_estado(f"❌ Error: {e}", "red")
        finally:
            for clip in clips_finales:
                try:
                    clip.close()
                except Exception:
                    pass
            if bgm_clip:
                try:
                    bgm_clip.close()
                except Exception:
                    pass
            if audio_clip:
                try:
                    audio_clip.close()
                except Exception:
                    pass
            if video_final:
                try:
                    video_final.close()
                except Exception:
                    pass
            self.cambiar_estado_boton(self.btn_exp_mp4, "normal")

    # ==========================================
    # PASO 4b: EXPORTAR CAPCUT
    # ==========================================
    def ejecutar_exportar_capcut(self):
        if not self.timeline_data:
            self.mostrar_estado("❌ Primero crea el storyboard.", "red")
            return

        self.mostrar_estado("Preparando Carpeta...", "yellow")
        self.cambiar_estado_boton(self.btn_exp_capcut, "disabled")
        renderer = VideoRenderer(self.formato_actual)
        try:
            carpeta = f"PROYECTO_CAPCUT_{self.formato_actual}"
            os.makedirs(carpeta, exist_ok=True)
            shutil.copy(self.ARCHIVO_VOZ, os.path.join(carpeta, "00_PISTA_AUDIO.mp3"))
            for item in self.timeline_data:
                clip_procesado = renderer.procesar_recorte_clip(item["archivo"], item["duracion"])
                clip_procesado.write_videofile(
                    os.path.join(carpeta, f"CLIP_{item['orden']:02d}.mp4"),
                    fps=24, codec="libx264", logger=None,
                )
                clip_procesado.close()
            self.mostrar_estado("📂 ¡CARPETA LISTA!", "#00FF00")
        except Exception as e:
            logging.exception("Error exportando CapCut")
            self.mostrar_estado(f"❌ Error Carpeta: {e}", "red")
        finally:
            self.cambiar_estado_boton(self.btn_exp_capcut, "normal")

    # ==========================================
    # PUBLICADOR YOUTUBE
    # ==========================================
    def cargar_video_proyecto(self):
        self.ruta_video_publicar = f"FINAL_{self.formato_actual}.mp4"
        if os.path.exists(self.ruta_video_publicar):
            self.after(0, lambda: self.lbl_video_pub.configure(
                text=f"✅ Seleccionado: {self.ruta_video_publicar}", text_color="#00FF00"))
            self.after(0, lambda: self.entrada_titulo_pub.delete(0, "end"))
            self.after(0, lambda: self.entrada_titulo_pub.insert(0, self.entrada_titulo.get()))
            self.after(0, lambda: self.caja_desc_pub.delete("0.0", "end"))
            self.after(0, lambda: self.caja_desc_pub.insert("0.0", self.caja_desc.get("0.0", "end").strip()))
        else:
            self.after(0, lambda: self.lbl_video_pub.configure(
                text="❌ Aún no has renderizado el video final.", text_color="red"))

    def cargar_video_externo(self):
        archivo = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.mov *.avi")])
        if archivo:
            self.ruta_video_publicar = archivo
            self.after(0, lambda: self.lbl_video_pub.configure(
                text=f"✅ Seleccionado: {os.path.basename(archivo)}", text_color="#00FF00"))
            self.after(0, lambda: self.entrada_titulo_pub.delete(0, "end"))
            self.after(0, lambda: self.caja_desc_pub.delete("0.0", "end"))

    def ejecutar_publicar_youtube(self):
        self.mostrar_estado("Conectando con YouTube... ¡Revisa tu navegador web!", "orange")
        self.cambiar_estado_boton(self.btn_publicar_yt, "disabled")
        try:
            titulo = self.entrada_titulo_pub.get()
            desc = self.caja_desc_pub.get("0.0", "end").strip()

            if not self.ruta_video_publicar or not os.path.exists(self.ruta_video_publicar):
                raise Exception("El video seleccionado no existe.")
            if not os.path.exists("client_secret.json"):
                raise Exception("Falta el archivo 'client_secret.json'.")

            scopes = ["https://www.googleapis.com/auth/youtube.upload"]
            creds = None
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", scopes)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes)
                    creds = flow.run_local_server(port=0)
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            youtube = build("youtube", "v3", credentials=creds)
            estado_priv = {
                "Privado": "private",
                "Oculto": "unlisted",
                "Público": "public",
            }[self.menu_privacidad.get()]

            cat_id = self.info_genero_actual.get("youtube_category_id", "22")
            es_infantil = "Infantil" in self.menu_genero.get()

            body = {
                "snippet": {"title": titulo, "description": desc, "categoryId": cat_id},
                "status": {"privacyStatus": estado_priv, "selfDeclaredMadeForKids": es_infantil},
            }
            self.mostrar_estado("Subiendo video a YouTube... ¡Paciencia, no cierres la app!", "yellow")

            media = MediaFileUpload(self.ruta_video_publicar, chunksize=-1, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = request.execute()

            self.mostrar_estado(f"🎉 ¡ÉXITO! Video Publicado. ID: {response['id']}", "#00FF00")
        except Exception as e:
            logging.exception("Error al Publicar")
            self.mostrar_estado(f"❌ Error al Publicar: {e}", "red")
        finally:
            self.cambiar_estado_boton(self.btn_publicar_yt, "normal")

    # ==========================================
    # PASO 5: CLIPPING VIRAL Y RE-EDICIÓN INTELIGENTE
    # ==========================================
    def cargar_video_clipping_pc(self):
        archivo = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.mov *.mkv *.webm")])
        if archivo:
            self.ruta_video_clipping = archivo
            self.lbl_video_clipping.configure(
                text=f"✅ Video cargado (PC): {os.path.basename(archivo)}",
                text_color="#00E676",
            )
            self.mostrar_estado(f"📂 Video listo para Clipping o Re-edición: {os.path.basename(archivo)}", "green")

    def ejecutar_descargar_viral_url(self):
        url = self.entrada_url_viral.get().strip()
        if not url:
            self.mostrar_estado("❌ Pega primero el enlace (URL) del video viral.", "red")
            return

        self.cambiar_estado_boton(self.btn_descargar_viral, "disabled", "Descargando...")
        try:
            self.mostrar_estado("⬇️ Descargando video viral con yt-dlp (YouTube/TikTok/Reels/X)...", "yellow")
            ruta, titulo_orig, dur = ClippingService.descargar_video_url(url, self.CARPETA_ASSETS)
            self.ruta_video_clipping = ruta
            self.after(
                0,
                lambda: self.lbl_video_clipping.configure(
                    text=f"✅ Descargado ({dur:.0f}s): {titulo_orig[:55]}",
                    text_color="#00E676",
                ),
            )
            if not self.entrada_tema.get().strip():
                self.after(0, lambda: self.entrada_tema.insert(0, titulo_orig[:70]))
            self.mostrar_estado(f"✅ Video descargado y listo para reeditar: {os.path.basename(ruta)}", "green")
        except Exception as e:
            logging.exception("Error descargando URL viral")
            self.mostrar_estado(f"❌ Error al descargar URL: {e}", "red")
        finally:
            self.cambiar_estado_boton(self.btn_descargar_viral, "normal", "⬇️ Descargar URL")

    def ejecutar_auto_clipping(self):
        """
        MODO 1 (AUTO-CLIPPING):
        Extrae el audio del video descargado, transcribe con Whisper con marcas de tiempo,
        usa OpenAI para elegir los fragmentos más virales, y los recorta en formato 9:16 (o 16:9)
        con transformación Anti-Copyright opcional.
        """
        if not self.ruta_video_clipping or not os.path.exists(self.ruta_video_clipping):
            self.mostrar_estado("❌ Primero descarga un video por URL o carga uno desde tu PC.", "red")
            return

        self.formato_actual = "SHORT" if "SHORT" in self.menu_formato.get() else "LARGO"
        opcion_cant = self.menu_cant_clips.get()
        if opcion_cant.startswith("5"):
            num_clips, dur_min, dur_max = 5, 15, 40
        elif opcion_cant.startswith("1"):
            num_clips, dur_min, dur_max = 1, 25, 55
        else:
            num_clips, dur_min, dur_max = 3, 15, 40

        anti_copy = self.switch_anticopyright.get() == 1
        self.cambiar_estado_boton(self.btn_auto_clipping, "disabled", "Analizando y Cortando...")
        try:
            service = OpenAIService(self.entrada_openai.get().strip())
            ruta_audio_temp = os.path.join(self.CARPETA_ASSETS, "clipping_source_audio.mp3")
            self.mostrar_estado("🎧 Extrayendo audio del video viral...", "yellow")
            _, duracion_total = ClippingService.extraer_audio(self.ruta_video_clipping, ruta_audio_temp)

            self.mostrar_estado("🧠 Transcribiendo timestamps con Whisper IA...", "orange")
            transcript = service.transcribir(ruta_audio_temp, con_segmentos=True)
            texto_timestamps = ClippingService.formatear_transcripcion_con_timestamps(transcript)

            self.mostrar_estado(f"🔥 Detectando los {num_clips} momentos más virales con IA...", "orange")
            momentos = service.detectar_momentos_virales(
                texto_timestamps, duracion_total, num_clips=num_clips, dur_min=dur_min, dur_max=dur_max
            )
            if not momentos:
                momentos = [{
                    "inicio": 0.0,
                    "fin": min(35.0, duracion_total),
                    "titulo_seo": "Momento Viral Imperdible 🔥 #shorts #viral",
                    "gancho_texto": "Momento clave del video",
                    "razon_viral": "Segmento principal de alto impacto",
                }]

            self.clips_virales_detectados = []
            for idx, m in enumerate(momentos):
                ini = float(m.get("inicio", 0.0))
                fin = float(m.get("fin", min(ini + 30.0, duracion_total)))
                ruta_clip = os.path.join(self.CARPETA_ASSETS, f"CLIP_VIRAL_{idx + 1:02d}_{int(ini)}s_{int(fin)}s.mp4")
                self.mostrar_estado(
                    f"✂️ Recortando Clip Viral #{idx + 1}/{len(momentos)} [{ini:.1f}s - {fin:.1f}s]...",
                    "yellow",
                )
                ClippingService.recortar_y_transformar_clip(
                    self.ruta_video_clipping,
                    ini,
                    fin,
                    ruta_clip,
                    formato_actual=self.formato_actual,
                    anti_copyright=anti_copy,
                    conservar_audio=True,
                )
                m["archivo"] = ruta_clip
                self.clips_virales_detectados.append(m)

            self.after(0, self.dibujar_clips_virales_ui)
            self.mostrar_estado(
                f"🎉 ¡{len(self.clips_virales_detectados)} Clips Virales extraídos y reeditados con éxito!",
                "#00FF00",
            )
        except Exception as e:
            logging.exception("Error en Auto-Clipping")
            self.mostrar_estado(f"❌ Error en Auto-Clipping: {e}", "red")
        finally:
            self.cambiar_estado_boton(
                self.btn_auto_clipping,
                "normal",
                "✂️ MODO 1: Extraer Mejores Clips (Voz Original + Subs)",
            )

    def dibujar_clips_virales_ui(self):
        for w in self.lista_clipping_ui.winfo_children():
            w.destroy()

        for idx, clip_info in enumerate(self.clips_virales_detectados):
            card = ctk.CTkFrame(self.lista_clipping_ui, fg_color="#263238", corner_radius=8)
            card.pack(fill="x", padx=6, pady=5)

            ini = float(clip_info.get("inicio", 0))
            fin = float(clip_info.get("fin", 0))
            titulo = clip_info.get("titulo_seo", f"Clip Viral #{idx + 1}")
            razon = clip_info.get("razon_viral", "")
            archivo = clip_info.get("archivo", "")

            texto_card = (
                f"🔥 CLIP #{idx + 1} [{ini:.1f}s - {fin:.1f}s] ({fin - ini:.1f}s) — {titulo}\n"
                f"💡 Por qué es viral: {razon}\n"
                f"📁 Archivo: {os.path.basename(archivo)}"
            )
            ctk.CTkLabel(card, text=texto_card, justify="left", wraplength=540).pack(
                side="left", padx=10, pady=8
            )

            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.pack(side="right", padx=8, pady=6)
            ctk.CTkButton(
                btns,
                text="🔤 Quemar Subs Hormozi + Publicar",
                fg_color="#E91E63",
                width=210,
                command=lambda c=clip_info: self.hilo_quemar_subs_clip(c),
            ).pack(pady=2)
            ctk.CTkButton(
                btns,
                text="🚀 Enviar Directo al Publicador",
                fg_color="#2196F3",
                width=210,
                command=lambda c=clip_info: self.enviar_clip_a_publicador(c),
            ).pack(pady=2)

    def hilo_quemar_subs_clip(self, clip_info):
        self.ejecutar_en_hilo(lambda: self.ejecutar_quemar_subs_clip(clip_info))

    def ejecutar_quemar_subs_clip(self, clip_info):
        """Toma un clip recortado, transcribe su audio con Whisper, le quema subtítulos Hormozi + BGM opcional y lo manda al Publicador."""
        archivo_origen = clip_info.get("archivo", "")
        if not archivo_origen or not os.path.exists(archivo_origen):
            self.mostrar_estado("❌ El archivo del clip no existe.", "red")
            return

        self.mostrar_estado("🔤 Quemando Subtítulos Virales Hormozi en el clip...", "orange")
        renderer = VideoRenderer(self.formato_actual)
        video_base = None
        video_final = None
        bgm_clip = None
        try:
            service = OpenAIService(self.entrada_openai.get().strip())
            audio_temp = os.path.join(self.CARPETA_ASSETS, "temp_sub_clip.mp3")
            ClippingService.extraer_audio(archivo_origen, audio_temp)
            transcript = service.transcribir(audio_temp)

            video_base = VideoFileClip(archivo_origen)
            if self.ruta_musica_fondo and os.path.exists(self.ruta_musica_fondo) and video_base.audio:
                audio_mezclado, bgm_clip = renderer.mezclar_audio_con_musica(
                    video_base.audio,
                    self.ruta_musica_fondo,
                    volumen_musica=float(self.slider_vol_bgm.get()),
                )
                video_base = video_base.set_audio(audio_mezclado)

            clips_subs = renderer.crear_subtitulos(transcript, self.menu_estilos_subs.get())
            if clips_subs:
                video_final = CompositeVideoClip([video_base] + clips_subs)
            else:
                video_final = video_base

            base_sin_ext, _ = os.path.splitext(os.path.basename(archivo_origen))
            ruta_subtitulado = os.path.join(self.CARPETA_ASSETS, f"{base_sin_ext}_SUBS_LISTO.mp4")
            video_final.write_videofile(
                ruta_subtitulado, fps=24, codec="libx264", audio_codec="aac", logger=None
            )
            clip_info["archivo"] = ruta_subtitulado
            self.enviar_clip_a_publicador(clip_info)
            self.mostrar_estado("🎉 ¡Clip con Subtítulos Hormozi listo en el Publicador para subir!", "#00FF00")
        except Exception as e:
            logging.exception("Error quemando subtítulos al clip")
            self.mostrar_estado(f"❌ Error en subtítulos del clip: {e}", "red")
        finally:
            if bgm_clip:
                try:
                    bgm_clip.close()
                except Exception:
                    pass
            if video_final and video_final is not video_base:
                try:
                    video_final.close()
                except Exception:
                    pass
            if video_base:
                try:
                    video_base.close()
                except Exception:
                    pass

    def enviar_clip_a_publicador(self, clip_info):
        ruta = clip_info.get("archivo", "")
        titulo = clip_info.get("titulo_seo", "Clip Viral #shorts")
        razon = clip_info.get("razon_viral", "")
        desc = f"{titulo}\n\n{razon}\n\n#shorts #viral #clips #tendencias"
        self.ruta_video_publicar = ruta
        self.after(
            0,
            lambda: self.lbl_video_pub.configure(
                text=f"✅ Seleccionado: {os.path.basename(ruta)}", text_color="#00FF00"
            ),
        )
        self.after(0, lambda: self.entrada_titulo_pub.delete(0, "end"))
        self.after(0, lambda: self.entrada_titulo_pub.insert(0, titulo))
        self.after(0, lambda: self.caja_desc_pub.delete("0.0", "end"))
        self.after(0, lambda: self.caja_desc_pub.insert("0.0", desc))
        self.after(0, lambda: self.pestanas.set("🚀 4. Publicador"))

    def ejecutar_remix_completo(self):
        """
        MODO 2 (REMIX / CLONAR ÉXITO CON TU VOZ):
        1. Transcribe el video viral descargado con Whisper.
        2. Le pide a OpenAI que reescriba un guion 100% nuevo y aún más adictivo inspirado en ese video.
        3. Corta el video original en escenas B-Roll transformadas (Espejo Horizontal + Zoom Anti-Copyright + orden dinámico).
        4. Graba tu propia voz (Edge-TTS Gratis / OpenAI / ElevenLabs) y arma el Storyboard listo para exportar MP4.
        """
        if not self.ruta_video_clipping or not os.path.exists(self.ruta_video_clipping):
            self.mostrar_estado("❌ Primero descarga un video por URL o carga uno desde tu PC.", "red")
            return

        self.formato_actual = "SHORT" if "SHORT" in self.menu_formato.get() else "LARGO"
        anti_copy = self.switch_anticopyright.get() == 1
        self.cambiar_estado_boton(self.btn_remix_completo, "disabled", "Re-editando Video Completo...")
        try:
            service = OpenAIService(self.entrada_openai.get().strip())
            ruta_audio_temp = os.path.join(self.CARPETA_ASSETS, "remix_source_audio.mp3")
            self.mostrar_estado("🎧 Paso 1/4: Extrayendo y transcribiendo el video viral original...", "yellow")
            _, duracion_orig = ClippingService.extraer_audio(self.ruta_video_clipping, ruta_audio_temp)
            transcript = service.transcribir(ruta_audio_temp, con_segmentos=True)
            texto_original = getattr(transcript, "text", "") or ClippingService.formatear_transcripcion_con_timestamps(
                transcript
            )

            genero_nombre = self.menu_genero.get()
            info_gen = self.info_genero_actual
            self.mostrar_estado(f"🧠 Paso 2/4: Reescribiendo guion mejorado ({genero_nombre})...", "orange")

            prompt_remix = f"""Analiza la siguiente transcripción de un video que ya demostró ser viral:
--- TRANSCRIPCIÓN ORIGINAL ---
{texto_original[:8000]}
--- FIN TRANSCRIPCIÓN ---

Tu misión: Reescribe un guion 100% NUEVO, original, sin plagio literal pero conservando y potenciando la idea ganadora, el gancho y la estructura de retención, adaptado al género: {genero_nombre}.
Tono: {info_gen['instruccion_tono']}
Longitud: {'90 a 110 palabras (Formato Short Vertical)' if self.es_vertical else '1200 a 1600 palabras (Formato Largo)'}.
Cierre: {info_gen['cierre_estructura']}

Devuelve ESTRICTAMENTE un JSON con:
- 'guion_locucion': texto completo en ESPAÑOL para narrar.
- 'escenas': lista de 8 escenas ordenadas con 'narracion', 'keyword_pexels' y 'prompt_ia'.
- 'keywords_visuales': lista de keywords en inglés.
- 'prompts_visuales': lista de prompts en inglés.
- 'titulo_seo': nuevo título aún más viral.
- 'descripcion_seo': descripción con hashtags."""

            modelo = self.menu_motor_ia.get().split()[0]
            datos = service.generar_guion(modelo, prompt_remix, genero_key=genero_nombre)

            self.escenas_guion = datos.get("escenas", [])
            self.keywords_actuales = datos.get("keywords_visuales", [])
            self.prompts_visuales = datos.get("prompts_visuales", [])
            guion_nuevo = datos.get("guion_locucion", "").strip()

            self.after(0, lambda: self.caja_guion.delete("0.0", "end"))
            self.after(0, lambda: self.caja_guion.insert("0.0", guion_nuevo))
            if "titulo_seo" in datos:
                self.after(0, lambda: self.entrada_titulo.delete(0, "end"))
                self.after(0, lambda: self.entrada_titulo.insert(0, datos["titulo_seo"]))
            if "descripcion_seo" in datos:
                self.after(0, lambda: self.caja_desc.delete("0.0", "end"))
                self.after(0, lambda: self.caja_desc.insert("0.0", datos["descripcion_seo"]))

            # Cortar el video original en múltiples B-Rolls reencuadrados y con filtro Anti-Copyright
            self.mostrar_estado("✂️ Paso 3/4: Re-editando escenas del video con filtro Anti-Copyright...", "yellow")
            num_cortes = max(6, len(self.escenas_guion) or 8)
            dur_segmento = max(3.5, duracion_orig / num_cortes)
            nuevos_brolls = []

            for i in range(num_cortes):
                ini = i * dur_segmento
                fin = min(duracion_orig, ini + min(5.5, dur_segmento))
                if fin - ini < 1.8:
                    break
                ruta_broll = os.path.join(self.CARPETA_ASSETS, f"remix_broll_{i:02d}.mp4")
                ClippingService.recortar_y_transformar_clip(
                    self.ruta_video_clipping,
                    ini,
                    fin,
                    ruta_broll,
                    formato_actual=self.formato_actual,
                    anti_copyright=anti_copy,
                    conservar_audio=False,
                )
                nuevos_brolls.append(ruta_broll)

            # Alternamos ligeramente el orden de los B-Rolls para romper la huella digital del video original
            if len(nuevos_brolls) > 3 and anti_copy:
                pares = nuevos_brolls[::2]
                impares = nuevos_brolls[1::2]
                nuevos_brolls = impares + pares

            self.pool_videos = nuevos_brolls
            self.after(0, self.actualizar_lista_clips_ui)

            # Grabar la nueva voz automáticamente y armar el Storyboard
            self.mostrar_estado("🎙️ Paso 4/4: Grabando tu nueva locución y armando el Storyboard...", "orange")
            self.ejecutar_paso2()
            self.ejecutar_generar_timeline()
            self.guardar_cache()
            self.mostrar_estado(
                "🎉 ¡Video Re-editado con Nuevo Guion, Tu Voz y Anti-Copyright listo en el Storyboard! Solo pulsa 'Exportar MP4 Final'.",
                "#00FF00",
            )
        except Exception as e:
            logging.exception("Error en Remix Completo")
            self.mostrar_estado(f"❌ Error en Remix Completo: {e}", "red")
        finally:
            self.cambiar_estado_boton(
                self.btn_remix_completo,
                "normal",
                "🔄 MODO 2: Re-editar con Tu Voz (Clonar Éxito + Nuevo Guion)",
            )


if __name__ == "__main__":
    app = StudioApp()
    app.mainloop()
