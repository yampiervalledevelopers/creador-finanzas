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
import tkinter as tk
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
import PIL.ImageTk
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


class HistorialClipsUsados:
    """
    Memoria PERSISTENTE (entre videos y sesiones) de los clips de stock ya usados.
    Evita que un video nuevo vuelva a mostrar los mismos clips de Pexels/Pixabay
    que ya salieron en videos anteriores (aunque las palabras clave se parezcan).
    """

    ARCHIVO = "historial_clips_usados.json"
    MAX_REGISTROS = 5000
    _lock = threading.Lock()

    def __init__(self):
        self.usados = []
        self._set = set()
        try:
            if os.path.exists(self.ARCHIVO):
                with open(self.ARCHIVO, "r", encoding="utf-8") as f:
                    self.usados = [str(x) for x in json.load(f)]
                    self._set = set(self.usados)
        except Exception:
            logging.exception("No se pudo leer el historial de clips usados")

    @staticmethod
    def clave(fuente, video_obj, url=""):
        vid_id = video_obj.get("id") if isinstance(video_obj, dict) else None
        if vid_id:
            return f"{fuente}:{vid_id}"
        return f"url:{url}"

    def ya_usado(self, clave):
        return clave in self._set

    def registrar(self, clave):
        with self._lock:
            if clave in self._set:
                return
            self.usados.append(clave)
            self._set.add(clave)
            if len(self.usados) > self.MAX_REGISTROS:
                sobrantes = self.usados[: len(self.usados) - self.MAX_REGISTROS]
                self.usados = self.usados[-self.MAX_REGISTROS:]
                for s in sobrantes:
                    self._set.discard(s)
            try:
                with open(self.ARCHIVO, "w", encoding="utf-8") as f:
                    json.dump(self.usados, f)
            except Exception:
                logging.exception("No se pudo guardar el historial de clips usados")

    def limpiar(self):
        with self._lock:
            self.usados = []
            self._set = set()
            try:
                if os.path.exists(self.ARCHIVO):
                    os.remove(self.ARCHIVO)
            except Exception:
                pass


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

    def buscar_videos(self, keyword, cantidad, orientacion, pagina=1):
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            params={
                "query": keyword,
                "per_page": cantidad,
                "orientation": orientacion,
                "size": "medium",
                "page": max(1, int(pagina)),
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

    def buscar_videos(self, keyword, cantidad=3, pagina=1):
        resp = requests.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": self.api_key,
                "q": keyword[:95],
                "per_page": max(3, cantidad),
                "page": max(1, int(pagina)),
                "video_type": "film",
                "safesearch": "true",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 400:
            # Pixabay devuelve 400 cuando la página pedida no existe (no hay más resultados)
            return []
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

    def procesar_recorte_clip(self, ruta_clip, duracion, offset=0.0):
        ancho, alto = self.dimensiones
        clip_orig = VideoFileClip(ruta_clip).without_audio()
        dur_orig = max(0.2, float(clip_orig.duration or duracion))
        offset_seguro = max(0.0, float(offset or 0.0))
        if offset_seguro >= dur_orig - 0.15:
            offset_seguro = offset_seguro % max(0.15, dur_orig - 0.15)
        if offset_seguro > 0.05 and offset_seguro < dur_orig - 0.15:
            clip_base = clip_orig.subclip(offset_seguro, dur_orig)
        else:
            clip_base = clip_orig
        if clip_base.duration < duracion:
            clip = clip_base.loop(duration=duracion)
        else:
            clip = clip_base.subclip(0, duracion)
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
class ReproductorAudioMCI:
    """
    Reproductor de audio nativo de Windows (winmm / MCI) sin dependencias extra.
    Permite reproducir MP3/WAV, pausar y saltar a cualquier milisegundo (para sincronizar con el video).
    """

    def __init__(self, ruta_audio):
        self.alias = f"audio_prev_{id(self)}"
        self.abierto = False
        self.disponible = False
        try:
            import ctypes
            self._mci = ctypes.windll.winmm.mciSendStringW
            self.disponible = True
        except Exception:
            self._mci = None
            return
        if ruta_audio and os.path.exists(ruta_audio):
            ruta_abs = os.path.abspath(ruta_audio)
            if self._cmd(f'open "{ruta_abs}" type mpegvideo alias {self.alias}') == 0:
                self._cmd(f"set {self.alias} time format milliseconds")
                self.abierto = True

    def _cmd(self, comando):
        if not self._mci:
            return -1
        try:
            return self._mci(comando, None, 0, None)
        except Exception:
            logging.exception("Error MCI: %s", comando)
            return -1

    def reproducir_desde(self, segundos):
        if self.abierto:
            self._cmd(f"play {self.alias} from {int(max(0.0, segundos) * 1000)}")

    def pausar(self):
        if self.abierto:
            self._cmd(f"pause {self.alias}")

    def detener(self):
        if self.abierto:
            self._cmd(f"stop {self.alias}")

    def cerrar(self):
        if self.abierto:
            self._cmd(f"close {self.alias}")
            self.abierto = False


class VentanaPrevisualizacion(ctk.CTkToplevel):
    """
    Reproductor de Previsualización en Vivo (Redimensionable y Auto-Ajustable):
    - Controles y barra de progreso ARRIBA para que nunca queden ocultos fuera de pantalla.
    - Ventana 100% redimensionable con selector de tamaño (Compacto / Mediano / Grande / Auto-Ventana).
    - Precarga inteligente en segundo plano y Auto-Play inmediato con clic en el video o barra espaciadora.
    """

    FPS_PREVIEW = 15

    ESCALAS_VERTICAL = {
        "Compacto (216x384)": (216, 384),
        "Mediano (260x462)": (260, 462),
        "Grande (340x604)": (340, 604),
        "Auto (Ajustar ventana)": None,
    }
    ESCALAS_HORIZONTAL = {
        "Compacto (480x270)": (480, 270),
        "Mediano (640x360)": (640, 360),
        "Grande (854x480)": (854, 480),
        "Auto (Ajustar ventana)": None,
    }

    def __init__(self, master, segmentos, ruta_audio=None, vertical=True, titulo="Previsualización",
                 extraer_audio_de=None):
        super().__init__(master)
        self.title(f"▶️ {titulo}")
        self.segmentos = [s for s in segmentos if s.get("archivo") and os.path.exists(s["archivo"])]
        self.duracion_total = sum(float(s.get("duracion", 0)) for s in self.segmentos) if self.segmentos else 0.0
        self.vertical = vertical
        self.mapa_escalas = self.ESCALAS_VERTICAL if vertical else self.ESCALAS_HORIZONTAL

        # Detectar altura de pantalla para elegir el tamaño ideal que NUNCA se salga de la pantalla
        alto_pantalla = self.winfo_screenheight()
        ancho_pantalla = self.winfo_screenwidth()
        if vertical:
            if alto_pantalla <= 800:
                escala_inicial = "Mediano (260x462)"
                self.ancho_disp, self.alto_disp = (260, 462)
            else:
                escala_inicial = "Grande (340x604)"
                self.ancho_disp, self.alto_disp = (340, 604)
        else:
            if alto_pantalla <= 800:
                escala_inicial = "Mediano (640x360)"
                self.ancho_disp, self.alto_disp = (640, 360)
            else:
                escala_inicial = "Grande (854x480)"
                self.ancho_disp, self.alto_disp = (854, 480)

        self.modo_auto_ventana = False
        self.cache_clips = {}
        self.lock_clips = threading.Lock()
        self.reproduciendo = False
        self.listo_para_reproducir = False
        self.posicion = 0.0
        self.inicio_reloj = 0.0
        self.foto_actual = None
        self.cerrado = False
        self.arrastrando_slider = False
        self.audio = ReproductorAudioMCI(ruta_audio) if (ruta_audio and os.path.exists(ruta_audio)) else None

        ancho_win = max(480, self.ancho_disp + 60)
        alto_win = min(alto_pantalla - 70, self.alto_disp + 165)
        pos_x = max(20, (ancho_pantalla - ancho_win) // 2)
        pos_y = max(10, (alto_pantalla - alto_win) // 3)
        self.geometry(f"{ancho_win}x{alto_win}+{pos_x}+{pos_y}")
        self.minsize(380, 420)
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.after(400, lambda: self.attributes("-topmost", False) if not self.cerrado else None)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

        # ================== BARRA DE CONTROLES ARRIBA (SIEMPRE VISIBLE) ==================
        panel_top = ctk.CTkFrame(self, fg_color="#1A222C", corner_radius=8)
        panel_top.pack(fill="x", padx=10, pady=(8, 4))

        fila_botones = ctk.CTkFrame(panel_top, fg_color="transparent")
        fila_botones.pack(fill="x", padx=8, pady=(6, 2))

        self.btn_play = ctk.CTkButton(
            fila_botones, text="⏳ Cargando...", width=105, height=30,
            fg_color="#2E7D32", font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled", command=self.alternar_play,
        )
        self.btn_play.pack(side="left", padx=3)

        ctk.CTkButton(
            fila_botones, text="⏮️ Inicio", width=80, height=30,
            fg_color="#455A64", font=ctk.CTkFont(size=12), command=self.reiniciar,
        ).pack(side="left", padx=3)

        self.combo_escala = ctk.CTkOptionMenu(
            fila_botones,
            values=list(self.mapa_escalas.keys()),
            width=155,
            height=28,
            fg_color="#263238",
            button_color="#37474F",
            font=ctk.CTkFont(size=11),
            command=self._cambiar_escala,
        )
        self.combo_escala.set(escala_inicial)
        self.combo_escala.pack(side="left", padx=5)

        self.lbl_tiempo = ctk.CTkLabel(
            fila_botones, text=self._formato_tiempo(0),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#80CBC4",
        )
        self.lbl_tiempo.pack(side="right", padx=6)

        # Barra de progreso deslizable justo debajo de los botones
        self.slider = ctk.CTkSlider(
            panel_top, from_=0, to=max(0.1, self.duracion_total),
            command=self._al_mover_slider, height=16,
        )
        self.slider.set(0)
        self.slider.pack(fill="x", padx=12, pady=(2, 6))
        self.slider.bind("<ButtonPress-1>", lambda e: setattr(self, "arrastrando_slider", True))
        self.slider.bind("<ButtonRelease-1>", self._al_soltar_slider)

        # ================== SUBTÍTULO / NARRACIÓN ACTIVA ==================
        self.lbl_narracion = ctk.CTkLabel(
            self, text="💡 Haz clic sobre el video o presiona ESPACIO para Pausar / Reproducir",
            wraplength=ancho_win - 30, text_color="#FFD54F",
            font=ctk.CTkFont(size=12, weight="bold"), height=28,
        )
        self.lbl_narracion.pack(fill="x", padx=12, pady=(0, 2))

        # ================== LIENZO DE VIDEO CENTRAL ==================
        self.contenedor_video = ctk.CTkFrame(self, fg_color="#000000", corner_radius=8)
        self.contenedor_video.pack(fill="both", expand=True, padx=10, pady=(2, 8))

        self.lienzo = ctk.CTkLabel(
            self.contenedor_video,
            text="⏳ Preparando clips de video para reproducción fluida...",
            fg_color="#000000",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.lienzo.pack(expand=True)
        # Clic en el video alterna Play/Pausa
        self.lienzo.bind("<Button-1>", lambda e: self.alternar_play())
        self.contenedor_video.bind("<Button-1>", lambda e: self.alternar_play())
        self.bind("<space>", lambda e: self.alternar_play())
        self.contenedor_video.bind("<Configure>", self._al_redimensionar_contenedor)

        if not self.segmentos:
            self.lienzo.configure(text="❌ No hay clips válidos para previsualizar.")
            return

        # Precargar clips y audio en segundo plano y arrancar reproducción automáticamente
        threading.Thread(
            target=self._precargar_todo, args=(extraer_audio_de,), daemon=True
        ).start()

    # ---------- ajuste de tamaño ----------
    def _cambiar_escala(self, seleccion):
        dims = self.mapa_escalas.get(seleccion)
        if dims is None:
            self.modo_auto_ventana = True
            self._recalcular_dimensiones_auto()
        else:
            self.modo_auto_ventana = False
            self.ancho_disp, self.alto_disp = dims
            alto_pantalla = self.winfo_screenheight()
            ancho_win = max(480, self.ancho_disp + 60)
            alto_win = min(alto_pantalla - 65, self.alto_disp + 165)
            self.geometry(f"{ancho_win}x{alto_win}")
        if self.listo_para_reproducir and not self.reproduciendo:
            self._mostrar_frame(self.posicion)

    def _al_redimensionar_contenedor(self, evento):
        if self.modo_auto_ventana and evento.width > 100 and evento.height > 100:
            self._recalcular_dimensiones_auto(evento.width, evento.height)

    def _recalcular_dimensiones_auto(self, w_cont=None, h_cont=None):
        if w_cont is None or h_cont is None:
            w_cont = max(200, self.contenedor_video.winfo_width() - 16)
            h_cont = max(200, self.contenedor_video.winfo_height() - 16)
        ratio = (9 / 16) if self.vertical else (16 / 9)
        if (w_cont / max(1, h_cont)) > ratio:
            nuevo_alto = max(160, h_cont - 10)
            nuevo_ancho = int(nuevo_alto * ratio)
        else:
            nuevo_ancho = max(160, w_cont - 10)
            nuevo_alto = int(nuevo_ancho / ratio)
        self.ancho_disp, self.alto_disp = nuevo_ancho, nuevo_alto
        self.lbl_narracion.configure(wraplength=max(300, w_cont))

    # ---------- utilidades y precarga ----------
    def _formato_tiempo(self, t):
        total = self.duracion_total
        return f"{int(t // 60):02d}:{int(t % 60):02d} / {int(total // 60):02d}:{int(total % 60):02d}"

    def _precargar_todo(self, extraer_audio_de):
        # 1. Si es un clip con audio integrado, extraer audio temporal
        ruta_lista = None
        if extraer_audio_de and os.path.exists(extraer_audio_de):
            try:
                self.after(0, lambda: self.lienzo.configure(text="⏳ Extrayendo audio del clip..."))
                ruta_tmp = os.path.join("assets_generados", f"_preview_audio_{int(time.time())}.mp3")
                os.makedirs("assets_generados", exist_ok=True)
                clip_aud = VideoFileClip(extraer_audio_de)
                if clip_aud.audio is not None:
                    clip_aud.audio.write_audiofile(ruta_tmp, logger=None)
                    self.ruta_audio_temporal = ruta_tmp
                    ruta_lista = ruta_tmp
                clip_aud.close()
            except Exception:
                logging.exception("No se pudo extraer audio para la previsualización")

        # 2. Abrir cada archivo de video sin target_resolution (evita bloqueo en MoviePy 1.0.3)
        rutas_unicas = []
        for s in self.segmentos:
            r = s.get("archivo")
            if r and r not in rutas_unicas and os.path.exists(r):
                rutas_unicas.append(r)

        total_clips = len(rutas_unicas)
        for idx, ruta in enumerate(rutas_unicas, 1):
            if self.cerrado:
                return
            try:
                self.after(
                    0,
                    lambda i=idx, tot=total_clips: self.lienzo.configure(
                        text=f"⏳ Cargando clips de video ({i}/{tot})..."
                    ) if not self.cerrado else None,
                )
                clip_v = VideoFileClip(ruta, audio=False)
                # Decodificar primer frame para dejar el lector listo
                _ = clip_v.get_frame(0)
                with self.lock_clips:
                    self.cache_clips[ruta] = clip_v
            except Exception:
                logging.exception(f"No se pudo abrir clip para preview: {ruta}")

        def _activar_y_reproducir():
            if self.cerrado:
                return
            if ruta_lista:
                self.audio = ReproductorAudioMCI(ruta_lista)
            self.listo_para_reproducir = True
            self.btn_play.configure(state="normal", text="▶️ Play")
            self._mostrar_frame(0.0)
            # Iniciar reproducción automáticamente para que no aparezca detenido
            self.reproducir()

        self.after(0, _activar_y_reproducir)

    def _obtener_clip(self, ruta):
        with self.lock_clips:
            if ruta not in self.cache_clips:
                self.cache_clips[ruta] = VideoFileClip(ruta, audio=False)
            return self.cache_clips[ruta]

    def _segmento_en(self, t):
        acumulado = 0.0
        for seg in self.segmentos:
            dur = float(seg.get("duracion", 1.0))
            if t < acumulado + dur:
                return seg, t - acumulado
            acumulado += dur
        ultimo = self.segmentos[-1]
        return ultimo, max(0.0, float(ultimo.get("duracion", 1.0)) - 0.05)

    def _mostrar_frame(self, t):
        if self.cerrado or not self.listo_para_reproducir:
            return
        try:
            seg, t_local = self._segmento_en(t)
            clip = self._obtener_clip(seg["archivo"])
            t_clip = float(seg.get("offset", 0.0)) + t_local
            if clip.duration and clip.duration > 0.1:
                t_clip = t_clip % max(0.05, clip.duration - 0.08)
            frame = clip.get_frame(max(0.0, t_clip))
            img = PIL.Image.fromarray(frame)

            # Reencuadre centrado igual que el render final (9:16 o 16:9)
            ancho_obj = max(120, int(self.ancho_disp))
            alto_obj = max(120, int(self.alto_disp))
            ratio_obj = ancho_obj / alto_obj
            w, h = img.size
            if (w / h) > ratio_obj:
                nuevo_w = int(h * ratio_obj)
                x1 = (w - nuevo_w) // 2
                img = img.crop((x1, 0, x1 + nuevo_w, h))
            else:
                nuevo_h = int(w / ratio_obj)
                y1 = (h - nuevo_h) // 2
                img = img.crop((0, y1, w, y1 + nuevo_h))
            img = img.resize((ancho_obj, alto_obj), PIL.Image.Resampling.BILINEAR)

            self.foto_actual = ctk.CTkImage(light_image=img, dark_image=img, size=(ancho_obj, alto_obj))
            self.lienzo.configure(image=self.foto_actual, text="")
            narr = seg.get("narracion", "")
            if narr:
                self.lbl_narracion.configure(text=f"🗣️ {narr[:135]}")
            self.lbl_tiempo.configure(text=self._formato_tiempo(t))
            if not self.arrastrando_slider:
                self.slider.set(min(self.duracion_total, max(0.0, t)))
        except Exception as err:
            logging.exception("Error mostrando fotograma de previsualización")
            self.lbl_narracion.configure(text=f"⚠️ Fotograma omitido: {str(err)[:80]}")

    # ---------- controles ----------
    def alternar_play(self):
        if not self.listo_para_reproducir:
            return
        if self.reproduciendo:
            self.pausar()
        else:
            self.reproducir()

    def reproducir(self):
        if not self.segmentos or not self.listo_para_reproducir:
            return
        if self.posicion >= self.duracion_total - 0.08:
            self.posicion = 0.0
        self.reproduciendo = True
        self.inicio_reloj = time.perf_counter() - self.posicion
        if self.audio:
            self.audio.reproducir_desde(self.posicion)
        self.btn_play.configure(text="⏸️ Pausa", fg_color="#F9A825")
        self._tick()

    def pausar(self):
        self.reproduciendo = False
        if self.audio:
            self.audio.pausar()
        if not self.cerrado:
            self.btn_play.configure(text="▶️ Play", fg_color="#2E7D32")

    def reiniciar(self):
        if not self.listo_para_reproducir:
            return
        estaba = self.reproduciendo
        self.pausar()
        self.posicion = 0.0
        self._mostrar_frame(0.0)
        if estaba:
            self.reproducir()

    def _al_mover_slider(self, valor):
        if self.listo_para_reproducir and not self.reproduciendo:
            self.posicion = float(valor)
            self._mostrar_frame(self.posicion)

    def _al_soltar_slider(self, _evento=None):
        self.arrastrando_slider = False
        if not self.listo_para_reproducir:
            return
        estaba = self.reproduciendo
        if estaba:
            self.pausar()
        self.posicion = float(self.slider.get())
        self._mostrar_frame(self.posicion)
        if estaba:
            self.reproducir()

    def _tick(self):
        if not self.reproduciendo or self.cerrado:
            return
        t_inicio_frame = time.perf_counter()
        self.posicion = t_inicio_frame - self.inicio_reloj
        if self.posicion >= self.duracion_total:
            self.posicion = self.duracion_total
            self._mostrar_frame(max(0.0, self.duracion_total - 0.05))
            self.pausar()
            return
        self._mostrar_frame(self.posicion)
        t_gastado_ms = int((time.perf_counter() - t_inicio_frame) * 1000)
        espera_ms = max(15, int(1000 / self.FPS_PREVIEW) - t_gastado_ms)
        self.after(espera_ms, self._tick)

    def cerrar(self):
        self.cerrado = True
        self.reproduciendo = False
        if self.audio:
            self.audio.detener()
            self.audio.cerrar()
        with self.lock_clips:
            for clip in self.cache_clips.values():
                try:
                    clip.close()
                except Exception:
                    pass
            self.cache_clips = {}
        ruta_tmp = getattr(self, "ruta_audio_temporal", None)
        if ruta_tmp and os.path.exists(ruta_tmp):
            try:
                os.remove(ruta_tmp)
            except Exception:
                pass
        self.destroy()


class StudioApp(ctk.CTk):
    ARCHIVO_VOZ = "voz_temp.mp3"
    ARCHIVO_KEYS = "config_keys.json"
    ARCHIVO_CACHE = "cache_proyecto.json"
    ARCHIVO_HISTORIAL = "historial_serie.txt"
    CARPETA_ASSETS = "assets_generados"

    def __init__(self):
        super().__init__()
        self.title("🎬 Studio Automator Pro v14.0 - AI Scene Sync & Dynamic FX")
        ancho_scr = self.winfo_screenwidth()
        alto_scr = self.winfo_screenheight()
        ancho_app = min(1340, ancho_scr - 30)
        alto_app = min(860, alto_scr - 70)
        self.geometry(f"{ancho_app}x{alto_app}+10+10")
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

        # Estado del Editor Horizontal estilo CapCut (Pestaña 3)
        self.clip_seleccionado_idx = 0
        self.posicion_aguja = 0.0
        self.zoom_px_seg = 34.0
        self.reproduciendo_capcut = False
        self.inicio_reloj_capcut = 0.0
        self.audio_capcut = None
        self.cache_clips_capcut = {}
        self.cache_thumbs_capcut = {}
        self.refs_thumbs_canvas = []
        self.foto_monitor_capcut = None
        self.arrastrando_borde_idx = None
        self.arrastrando_aguja = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self.crear_panel_izquierdo()
        self.crear_panel_derecho()

        self.cargar_keys()
        self.cargar_cache()
        self.after(150, self.dibujar_timeline_ui)

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
                "SHORT (Vertical 9:16)",
                "LARGO (Horizontal Normal 16:9)",
                "EXTRA LARGO (Documental por Capítulos 16:9)",
            ],
            width=300,
        )
        self.menu_formato.pack(padx=20, pady=5)

        ctk.CTkLabel(
            frame_izq, text="⏱️ Duración del Short (Modo Vertical):",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF",
        ).pack(anchor="w", padx=20, pady=(6, 0))
        self.menu_duracion_short = ctk.CTkOptionMenu(
            frame_izq,
            values=[
                "⚡ Short Rápido (30s - 45s | ~95 palabras)",
                "🔥 Short Completo (1 Minuto | ~165 palabras)",
                "💰 Short Monetizable (1.5 a 2 Min | ~280 palabras)",
                "🎬 Short Extendido Máximo (2.5 a 3 Min | ~450 palabras)",
            ],
            width=300,
            fg_color="#006064",
        )
        self.menu_duracion_short.set("🔥 Short Completo (1 Minuto | ~165 palabras)")
        self.menu_duracion_short.pack(padx=20, pady=5)

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
        self.pausar_capcut()
        self.pool_videos = []
        self.timeline_data = []
        self.clip_seleccionado_idx = 0
        self.posicion_aguja = 0.0
        self.cerrar_cache_clips_capcut()
        self.actualizar_lista_clips_ui()
        self.dibujar_timeline_ui()
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
            "duracion_short": self.menu_duracion_short.get(),
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
            if k.get("duracion_short"):
                self.menu_duracion_short.set(k["duracion_short"])
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

        # --- PESTAÑA 3: EDITOR MULTIsPISTA HORIZONTAL ESTILO CAPCUT ---
        panel_capcut_top = ctk.CTkFrame(self.tab_timeline, fg_color="#141820", corner_radius=8)
        panel_capcut_top.pack(fill="x", padx=5, pady=(4, 3))

        # Mini-Monitor en vivo a la izquierda
        frame_monitor_capcut = ctk.CTkFrame(panel_capcut_top, fg_color="#07090D", width=200, height=150, corner_radius=6)
        frame_monitor_capcut.pack(side="left", padx=6, pady=6)
        frame_monitor_capcut.pack_propagate(False)

        self.lbl_monitor_capcut = ctk.CTkLabel(
            frame_monitor_capcut,
            text="🎬 Monitor CapCut\n(Clic = Play/Pausa)",
            text_color="#90A4AE",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.lbl_monitor_capcut.pack(expand=True, fill="both")
        self.lbl_monitor_capcut.bind("<Button-1>", lambda e: self.alternar_play_capcut())

        # Panel derecho de controles de transporte, corte e inspector
        frame_inspector = ctk.CTkFrame(panel_capcut_top, fg_color="transparent")
        frame_inspector.pack(side="left", fill="both", expand=True, padx=(2, 6), pady=4)

        # Fila 1: Transporte + Tiempo Digital + Zoom de Barra Horizontal
        fila_transporte = ctk.CTkFrame(frame_inspector, fg_color="#1E2530", corner_radius=6)
        fila_transporte.pack(fill="x", pady=(0, 3))

        self.btn_play_capcut = ctk.CTkButton(
            fila_transporte, text="▶️ Play", width=82, height=26,
            fg_color="#2E7D32", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.alternar_play_capcut,
        )
        self.btn_play_capcut.pack(side="left", padx=4, pady=3)

        ctk.CTkButton(
            fila_transporte, text="⏮️ 00:00", width=66, height=26,
            fg_color="#37474F", font=ctk.CTkFont(size=11),
            command=self.reiniciar_aguja_capcut,
        ).pack(side="left", padx=2, pady=3)

        self.lbl_tiempo_capcut = ctk.CTkLabel(
            fila_transporte, text="⏱️ 00:00.0 / 00:00.0",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#00E5FF",
        )
        self.lbl_tiempo_capcut.pack(side="left", padx=8)

        ctk.CTkButton(
            fila_transporte, text="⚖️ Ajustar a Voz", width=105, height=24,
            fg_color="#00695C", font=ctk.CTkFont(size=11, weight="bold"),
            command=self.ajustar_todo_al_audio,
        ).pack(side="right", padx=4, pady=3)

        ctk.CTkButton(
            fila_transporte, text="🔍+", width=38, height=24,
            fg_color="#263238", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.cambiar_zoom_timeline(1.25),
        ).pack(side="right", padx=2, pady=3)

        ctk.CTkButton(
            fila_transporte, text="🔍-", width=38, height=24,
            fg_color="#263238", font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.cambiar_zoom_timeline(0.8),
        ).pack(side="right", padx=2, pady=3)

        # Fila 2: Herramientas CapCut (Dividir / Mover / Cambiar / Insertar / Duplicar / Borrar)
        fila_tools = ctk.CTkFrame(frame_inspector, fg_color="transparent")
        fila_tools.pack(fill="x", pady=2)

        ctk.CTkButton(
            fila_tools, text="✂️ Dividir (Corte)", width=112, height=27,
            fg_color="#E91E63", hover_color="#AD1457",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.dividir_clip_en_aguja,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            fila_tools, text="⬅️ Izq", width=54, height=27,
            fg_color="#455A64", font=ctk.CTkFont(size=11),
            command=self.mover_clip_izquierda,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            fila_tools, text="➡️ Der", width=54, height=27,
            fg_color="#455A64", font=ctk.CTkFont(size=11),
            command=self.mover_clip_derecha,
        ).pack(side="left", padx=2)

        self.btn_reemplazo_auto = ctk.CTkButton(
            fila_tools, text="🔎 Reemplazar Auto", width=118, height=27,
            fg_color="#E65100", hover_color="#BF360C",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.reemplazar_clip_auto(),
        )
        self.btn_reemplazo_auto.pack(side="left", padx=2)

        ctk.CTkButton(
            fila_tools, text="📂 Elegir PC", width=78, height=27,
            fg_color="#546E7A", font=ctk.CTkFont(size=11),
            command=self.elegir_reemplazo_pc_timeline,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            fila_tools, text="➕ Insertar", width=74, height=27,
            fg_color="#1565C0", font=ctk.CTkFont(size=11),
            command=self.insertar_clip_timeline,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            fila_tools, text="📄 Duplicar", width=76, height=27,
            fg_color="#5E35B1", font=ctk.CTkFont(size=11),
            command=self.duplicar_clip_timeline,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            fila_tools, text="🗑️", width=36, height=27,
            fg_color="#C62828", font=ctk.CTkFont(size=11),
            command=self.eliminar_clip_timeline,
        ).pack(side="left", padx=2)

        # Fila 3: Recorte fino de Duración y Punto de Inicio (Offset) del Clip Seleccionado
        fila_trim = ctk.CTkFrame(frame_inspector, fg_color="#1A202C", corner_radius=6)
        fila_trim.pack(fill="x", pady=2)

        self.lbl_clip_activo_capcut = ctk.CTkLabel(
            fila_trim,
            text="🎯 Clip: Ninguno seleccionado",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFD54F",
            anchor="w",
        )
        self.lbl_clip_activo_capcut.pack(side="left", padx=6, pady=2)

        ctk.CTkButton(
            fila_trim, text="⏩+0.5s", width=52, height=22,
            fg_color="#37474F", font=ctk.CTkFont(size=10),
            command=lambda: self.ajustar_offset_clip_sel(0.5),
        ).pack(side="right", padx=2, pady=2)
        ctk.CTkButton(
            fila_trim, text="⏪-0.5s", width=52, height=22,
            fg_color="#37474F", font=ctk.CTkFont(size=10),
            command=lambda: self.ajustar_offset_clip_sel(-0.5),
        ).pack(side="right", padx=2, pady=2)
        ctk.CTkLabel(
            fila_trim, text="Inicio video:", font=ctk.CTkFont(size=10), text_color="#B0BEC5"
        ).pack(side="right", padx=(6, 2))

        ctk.CTkButton(
            fila_trim, text="+0.5s", width=44, height=22,
            fg_color="#00838F", font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: self.ajustar_duracion_clip_sel(0.5),
        ).pack(side="right", padx=2, pady=2)
        ctk.CTkButton(
            fila_trim, text="-0.5s", width=44, height=22,
            fg_color="#00838F", font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: self.ajustar_duracion_clip_sel(-0.5),
        ).pack(side="right", padx=2, pady=2)
        ctk.CTkButton(
            fila_trim, text="+0.1s", width=40, height=22,
            fg_color="#263238", font=ctk.CTkFont(size=10),
            command=lambda: self.ajustar_duracion_clip_sel(0.1),
        ).pack(side="right", padx=1, pady=2)
        ctk.CTkButton(
            fila_trim, text="-0.1s", width=40, height=22,
            fg_color="#263238", font=ctk.CTkFont(size=10),
            command=lambda: self.ajustar_duracion_clip_sel(-0.1),
        ).pack(side="right", padx=1, pady=2)
        ctk.CTkLabel(
            fila_trim, text="Duración:", font=ctk.CTkFont(size=10), text_color="#B0BEC5"
        ).pack(side="right", padx=(4, 2))

        # Fila 4: Narración / Subtítulo en el punto de la aguja
        self.lbl_sub_capcut = ctk.CTkLabel(
            frame_inspector,
            text="💡 Clic = seleccionar | Doble clic en un clip = 🔎 reemplazarlo automáticamente según su subtítulo | Clic derecho = más opciones",
            font=ctk.CTkFont(size=11),
            text_color="#CFD8DC",
            anchor="w",
        )
        self.lbl_sub_capcut.pack(fill="x", padx=4, pady=(2, 0))

        # --- LIENZO MULTIPISTA HORIZONTAL CAPCUT (REGLA + VIDEO + GUION + AUDIO + AGUJA ROJA) ---
        panel_pistas = ctk.CTkFrame(self.tab_timeline, fg_color="#0E1117", corner_radius=8)
        panel_pistas.pack(fill="both", expand=True, padx=5, pady=3)

        self.canvas_timeline = tk.Canvas(
            panel_pistas,
            bg="#10141D",
            height=205,
            highlightthickness=1,
            highlightbackground="#263238",
        )
        self.canvas_timeline.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        self.scroll_timeline_x = ctk.CTkScrollbar(
            panel_pistas, orientation="horizontal", command=self.canvas_timeline.xview
        )
        self.scroll_timeline_x.pack(fill="x", padx=4, pady=(2, 4))
        self.canvas_timeline.configure(xscrollcommand=self.scroll_timeline_x.set)

        # Eventos de mouse en la barra horizontal estilo CapCut
        self.canvas_timeline.bind("<ButtonPress-1>", self._al_clic_canvas_timeline)
        self.canvas_timeline.bind("<B1-Motion>", self._al_arrastrar_canvas_timeline)
        self.canvas_timeline.bind("<ButtonRelease-1>", self._al_soltar_canvas_timeline)
        self.canvas_timeline.bind("<Double-Button-1>", self._al_doble_clic_canvas_timeline)
        self.canvas_timeline.bind("<Button-3>", self._menu_contextual_clip)
        self.canvas_timeline.bind("<MouseWheel>", self._al_rueda_canvas_timeline)

        # Contenedor auxiliar por compatibilidad
        self.timeline_ui = panel_pistas

        # --- BARRA INFERIOR DE EXPORTACIÓN Y MONITOR FLOTANTE ---
        frame_btn_exportar = ctk.CTkFrame(self.tab_timeline, fg_color="transparent")
        frame_btn_exportar.pack(fill="x", padx=5, pady=4)
        self.btn_preview_timeline = ctk.CTkButton(
            frame_btn_exportar, text="🖥️ Abrir Previsualizador en Ventana Grande",
            command=self.abrir_previsualizacion_timeline, fg_color="#00897B", height=30,
        )
        self.btn_preview_timeline.pack(side="left", expand=True, padx=4)
        self.btn_exp_mp4 = ctk.CTkButton(
            frame_btn_exportar, text="⬇️ Exportar MP4 Final (con tus cortes)",
            command=self.hilo_exportar_mp4, fg_color="#F44336", state="disabled", height=30,
            font=ctk.CTkFont(weight="bold"),
        )
        self.btn_exp_mp4.pack(side="left", expand=True, padx=4)
        self.btn_exp_capcut = ctk.CTkButton(
            frame_btn_exportar, text="📁 Exportar a CapCut",
            command=self.hilo_exportar_capcut, fg_color="#607D8B", state="disabled", height=30,
        )
        self.btn_exp_capcut.pack(side="right", expand=True, padx=4)

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
                "3 Clips de 1 Minuto (50s - 70s)",
                "2 Clips Monetizables (1.5 a 2 Min)",
                "1 Clip Extendido (2 a 3 Minutos)",
            ],
            width=235,
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
        self.btn_escuchar_voz = ctk.CTkButton(
            frame_flujo, text="🔊 Escuchar Voz",
            command=self.alternar_escuchar_voz, fg_color="#6A1B9A",
        )
        self.btn_escuchar_voz.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        frame_flujo.columnconfigure((0, 1, 2, 3), weight=1)

    # ==========================================
    # PREVISUALIZACIÓN EN VIVO
    # ==========================================
    def abrir_previsualizacion_timeline(self):
        if not self.timeline_data:
            self.mostrar_estado("❌ Primero crea el Storyboard (Paso 3) para previsualizar.", "red")
            return
        self.pausar_capcut()
        segmentos = [
            {
                "archivo": item["archivo"],
                "duracion": item["duracion"],
                "offset": item.get("offset", 0.0),
                "narracion": item.get("narracion", ""),
            }
            for item in self.timeline_data
        ]
        ruta_audio = self.ARCHIVO_VOZ if os.path.exists(self.ARCHIVO_VOZ) else None
        VentanaPrevisualizacion(
            self,
            segmentos,
            ruta_audio=ruta_audio,
            vertical=self.es_vertical,
            titulo=f"Previsualización Storyboard ({self.duracion_total_timeline:.1f}s)",
        )
        self.mostrar_estado("▶️ Previsualización abierta en ventana flotante.", "#00E5FF")

    def previsualizar_clip(self, ruta, con_audio_propio=False):
        if not ruta or not os.path.exists(ruta):
            self.mostrar_estado("❌ El clip no existe.", "red")
            return
        self.pausar_capcut()
        try:
            clip = VideoFileClip(ruta, audio=False)
            duracion = clip.duration or 1.0
            ancho, alto = clip.w, clip.h
            clip.close()
        except Exception as e:
            self.mostrar_estado(f"❌ No se pudo abrir el clip: {e}", "red")
            return
        VentanaPrevisualizacion(
            self,
            [{"archivo": ruta, "duracion": duracion, "narracion": ""}],
            vertical=alto >= ancho,
            titulo=os.path.basename(ruta),
            extraer_audio_de=ruta if con_audio_propio else None,
        )

    def alternar_escuchar_voz(self):
        reproductor = getattr(self, "reproductor_voz", None)
        if reproductor:
            reproductor.detener()
            reproductor.cerrar()
            self.reproductor_voz = None
            self.btn_escuchar_voz.configure(text="🔊 Escuchar Voz", fg_color="#6A1B9A")
            return
        if not os.path.exists(self.ARCHIVO_VOZ):
            self.mostrar_estado("❌ Aún no has grabado la voz (Paso 2).", "red")
            return
        self.reproductor_voz = ReproductorAudioMCI(self.ARCHIVO_VOZ)
        if not self.reproductor_voz.abierto:
            self.reproductor_voz = None
            self.mostrar_estado("❌ No se pudo reproducir el audio en este equipo.", "red")
            return
        self.reproductor_voz.reproducir_desde(0)
        self.btn_escuchar_voz.configure(text="⏹️ Detener Voz", fg_color="#C62828")
        self.mostrar_estado("🔊 Reproduciendo la locución grabada...", "#00E5FF")

    # ==========================================
    # UI Y EDITOR HORIZONTAL MULTIPISTA CAPCUT
    # ==========================================
    X_ENCABEZADO_TIMELINE = 74

    @property
    def duracion_total_timeline(self):
        if not self.timeline_data:
            return float(self.duracion_total_audio or 0.0)
        return sum(float(i.get("duracion", 0.0)) for i in self.timeline_data)

    def cerrar_cache_clips_capcut(self):
        for c in self.cache_clips_capcut.values():
            try:
                c.close()
            except Exception:
                pass
        self.cache_clips_capcut = {}
        self.cache_thumbs_capcut = {}
        self.refs_thumbs_canvas = []

    def _obtener_clip_capcut(self, ruta):
        if ruta not in self.cache_clips_capcut:
            self.cache_clips_capcut[ruta] = VideoFileClip(ruta, audio=False)
        return self.cache_clips_capcut[ruta]

    def _obtener_thumb_capcut(self, ruta, offset=0.0):
        clave = (ruta, int(float(offset or 0.0) * 2))
        if clave in self.cache_thumbs_capcut:
            return self.cache_thumbs_capcut[clave]
        try:
            clip = self._obtener_clip_capcut(ruta)
            dur = max(0.2, float(clip.duration or 1.0))
            t_frame = min(dur - 0.05, max(0.0, float(offset or 0.0) + 0.25))
            frame = clip.get_frame(t_frame)
            img = PIL.Image.fromarray(frame).resize((64, 44), PIL.Image.Resampling.BILINEAR)
            photo = PIL.ImageTk.PhotoImage(img)
            self.cache_thumbs_capcut[clave] = photo
            return photo
        except Exception:
            return None

    def recalcular_tiempos_timeline(self):
        acumulado = 0.0
        for idx, item in enumerate(self.timeline_data):
            dur = round(max(0.5, float(item.get("duracion", 2.0))), 2)
            item["orden"] = idx + 1
            item["duracion"] = dur
            item["inicio"] = round(acumulado, 2)
            item["fin"] = round(acumulado + dur, 2)
            item.setdefault("offset", 0.0)
            item["offset"] = round(max(0.0, float(item["offset"])), 2)
            acumulado += dur
        if self.timeline_data:
            self.clip_seleccionado_idx = max(0, min(self.clip_seleccionado_idx, len(self.timeline_data) - 1))
        else:
            self.clip_seleccionado_idx = 0

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
            ctk.CTkButton(
                fila, text="▶️ Ver", width=60, fg_color="#00897B",
                command=lambda r=ruta: self.previsualizar_clip(r),
            ).pack(side="right", padx=2)

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

    def cambiar_zoom_timeline(self, factor):
        self.zoom_px_seg = max(10.0, min(110.0, self.zoom_px_seg * factor))
        self.dibujar_timeline_ui()

    def dibujar_timeline_ui(self):
        if not hasattr(self, "canvas_timeline"):
            return
        self.recalcular_tiempos_timeline()
        c = self.canvas_timeline
        c.delete("all")
        self.refs_thumbs_canvas = []

        x0 = self.X_ENCABEZADO_TIMELINE
        px_s = self.zoom_px_seg
        dur_clips = self.duracion_total_timeline
        dur_voz = float(self.duracion_total_audio or 0.0)
        dur_max = max(dur_clips, dur_voz, 15.0)
        ancho_total = max(840, int(x0 + (dur_max + 4.0) * px_s))
        alto_total = 202
        c.configure(scrollregion=(0, 0, ancho_total, alto_total))

        # Fondos de las 4 bandas horizontales
        c.create_rectangle(0, 0, ancho_total, 26, fill="#161B24", outline="")
        c.create_rectangle(0, 27, ancho_total, 108, fill="#11151E", outline="")
        c.create_rectangle(0, 109, ancho_total, 148, fill="#141824", outline="")
        c.create_rectangle(0, 149, ancho_total, 200, fill="#0F171A", outline="")

        # Líneas divisorias horizontales
        for y_div in (26, 108, 148):
            c.create_line(0, y_div, ancho_total, y_div, fill="#263238", width=1)

        # 1. REGLA DE TIEMPO SUPERIOR
        paso_principal = 1 if px_s >= 45 else (2 if px_s >= 24 else (5 if px_s >= 14 else 10))
        seg = 0.0
        while seg <= dur_max + 2.0:
            x = x0 + seg * px_s
            es_principal = (int(round(seg)) % paso_principal == 0) and abs(seg - round(seg)) < 0.01
            if es_principal:
                c.create_line(x, 12, x, 26, fill="#78909C", width=1)
                s_int = int(round(seg))
                etiqueta = f"{s_int // 60}:{s_int % 60:02d}" if s_int >= 60 else f"{s_int}s"
                c.create_text(x + 2, 3, text=etiqueta, anchor="nw", fill="#B0BEC5", font=("Segoe UI", 8, "bold"))
            else:
                c.create_line(x, 19, x, 26, fill="#37474F", width=1)
            seg += 0.5 if px_s >= 30 else 1.0

        # 2. PISTA 1: BLOQUES DE VIDEO CON MINIATURAS Y ASAS DE CORTE/RECORTE
        if not self.timeline_data:
            c.create_text(
                x0 + 260, 68,
                text="🎬 Pista de Video vacía — Pulsa '3. Crear Storyboard' o '➕ Insertar' para organizar tus clips aquí",
                fill="#78909C", font=("Segoe UI", 10, "bold"),
            )
        else:
            for idx, item in enumerate(self.timeline_data):
                x1 = x0 + item["inicio"] * px_s
                x2 = max(x1 + 18, x0 + item["fin"] * px_s)
                seleccionado = (idx == self.clip_seleccionado_idx)

                color_fondo = "#1E3A5F" if idx % 2 == 0 else "#172E4D"
                if seleccionado:
                    color_fondo = "#234876"
                color_borde = "#FFD600" if seleccionado else "#42A5F5"
                grosor_borde = 3 if seleccionado else 1

                c.create_rectangle(
                    x1 + 1, 31, x2 - 1, 104,
                    fill=color_fondo, outline=color_borde, width=grosor_borde,
                )

                # Miniatura(s) tipo filmstrip dentro del bloque
                thumb = self._obtener_thumb_capcut(item["archivo"], item.get("offset", 0.0))
                if thumb and (x2 - x1) > 34:
                    self.refs_thumbs_canvas.append(thumb)
                    x_thumb = int(x1 + 5)
                    while x_thumb + 64 < x2 - 8:
                        c.create_image(x_thumb, 52, image=thumb, anchor="nw")
                        x_thumb += 68
                    if x_thumb == int(x1 + 5):
                        c.create_image(int(x1 + 4), 52, image=thumb, anchor="nw")

                # Banda superior del bloque con # de clip, nombre y duración
                c.create_rectangle(x1 + 2, 32, x2 - 2, 50, fill="#0D1B2A", outline="")
                nombre_corto = os.path.basename(item["archivo"])
                if len(nombre_corto) > 16:
                    nombre_corto = nombre_corto[:14] + ".."
                off_val = float(item.get("offset", 0.0))
                txt_off = f" (+{off_val:.1f}s)" if off_val > 0.05 else ""
                etiqueta_clip = f"#{idx + 1} {nombre_corto} [{item['duracion']:.1f}s{txt_off}]"
                max_chars = max(5, int((x2 - x1 - 10) / 6.2))
                c.create_text(
                    x1 + 6, 35,
                    text=etiqueta_clip[:max_chars],
                    anchor="nw",
                    fill="#FFD54F" if seleccionado else "#FFFFFF",
                    font=("Segoe UI", 8, "bold"),
                )

                # Asa derecha interactiva para estirar/acortar duración con el mouse
                color_asa = "#FFD600" if seleccionado else "#64B5F6"
                c.create_rectangle(x2 - 6, 33, x2 - 1, 102, fill=color_asa, outline="")
                c.create_line(x2 - 3, 55, x2 - 3, 80, fill="#000000", width=1)

                # 3. PISTA 2: BLOQUES DE GUION / SUBTÍTULOS SINCRONIZADOS
                narr = item.get("narracion", "")
                c.create_rectangle(
                    x1 + 1, 113, x2 - 1, 144,
                    fill="#311B92" if idx % 2 == 0 else "#4527A0",
                    outline="#FFD54F" if seleccionado else "#7E57C2",
                    width=2 if seleccionado else 1,
                )
                if narr and (x2 - x1) > 28:
                    max_n = max(4, int((x2 - x1 - 8) / 6.0))
                    c.create_text(
                        x1 + 5, 121,
                        text=f"🗣️ {narr[:max_n]}",
                        anchor="nw",
                        fill="#FFF59D",
                        font=("Segoe UI", 8),
                    )

        # 4. PISTA 3: LOCUCIÓN (CON ONDA DE AUDIO VISUAL) Y MÚSICA DE FONDO
        if dur_voz > 0.1:
            x_fin_voz = x0 + dur_voz * px_s
            c.create_rectangle(
                x0, 153, x_fin_voz, 195,
                fill="#004D40", outline="#00E676", width=1,
            )
            # Dibujar barras de onda de sonido (waveform)
            x_onda = x0 + 6
            semilla = 1
            while x_onda < x_fin_voz - 4:
                semilla = (semilla * 1103515245 + 12345) & 0x7FFFFFFF
                altura_barra = 4 + (semilla % 14)
                c.create_line(
                    x_onda, 174 - altura_barra, x_onda, 174 + altura_barra,
                    fill="#00E676", width=2,
                )
                x_onda += 5
            txt_bgm = f" + 🎵 {os.path.basename(self.ruta_musica_fondo)}" if self.ruta_musica_fondo else ""
            c.create_rectangle(x0 + 4, 155, min(x_fin_voz - 2, x0 + 290), 170, fill="#00251A", outline="")
            c.create_text(
                x0 + 8, 156,
                text=f"🎙️ VOZ LOCUCIÓN ({dur_voz:.1f}s){txt_bgm}",
                anchor="nw", fill="#A7FFEB", font=("Segoe UI", 8, "bold"),
            )
        else:
            c.create_text(
                x0 + 180, 173,
                text="🎙️ Pista de Audio (Graba la voz en el Paso 2 para ver la onda aquí)",
                fill="#4DB6AC", font=("Segoe UI", 9),
            )

        # 5. COLUMNA IZQUIERDA FIJA DE ENCABEZADOS DE PISTA
        c.create_rectangle(0, 0, x0 - 2, alto_total, fill="#181F2C", outline="#263238")
        c.create_text(8, 6, text="📏 TIEMPO", anchor="nw", fill="#90A4AE", font=("Segoe UI", 8, "bold"))
        c.create_text(8, 58, text="🎬 VIDEO", anchor="nw", fill="#64B5F6", font=("Segoe UI", 9, "bold"))
        c.create_text(8, 121, text="🗣️ SUBS", anchor="nw", fill="#CE93D8", font=("Segoe UI", 8, "bold"))
        c.create_text(8, 166, text="🎵 AUDIO", anchor="nw", fill="#4DB6AC", font=("Segoe UI", 8, "bold"))

        # 6. AGUJA ROJA (PLAYHEAD CAPCUT) Y PANEL INSPECTOR
        self._actualizar_inspector_capcut()
        self._actualizar_aguja_canvas()
        if self.timeline_data and not self.reproduciendo_capcut:
            self._mostrar_frame_capcut(self.posicion_aguja)

    def _actualizar_aguja_canvas(self):
        if not hasattr(self, "canvas_timeline"):
            return
        c = self.canvas_timeline
        c.delete("aguja")
        x_aguja = self.X_ENCABEZADO_TIMELINE + self.posicion_aguja * self.zoom_px_seg
        # Cabezal pentagonal rojo estilo CapCut en la regla
        c.create_polygon(
            x_aguja - 7, 1,
            x_aguja + 7, 1,
            x_aguja + 7, 12,
            x_aguja, 21,
            x_aguja - 7, 12,
            fill="#FF1744", outline="#FFFFFF", width=1, tags="aguja",
        )
        # Línea vertical roja que atraviesa todas las pistas
        c.create_line(x_aguja, 20, x_aguja, 200, fill="#FF1744", width=2, tags="aguja")

        total = max(self.duracion_total_timeline, float(self.duracion_total_audio or 0.0))
        self.lbl_tiempo_capcut.configure(
            text=f"⏱️ {self._formatear_seg_capcut(self.posicion_aguja)} / {self._formatear_seg_capcut(total)}"
        )

    def _formatear_seg_capcut(self, seg):
        seg = max(0.0, float(seg))
        m = int(seg // 60)
        s = seg - (m * 60)
        return f"{m:02d}:{s:04.1f}"

    def _actualizar_inspector_capcut(self):
        if not self.timeline_data:
            self.lbl_clip_activo_capcut.configure(text="🎯 Clip: Ninguno en la línea de tiempo")
            return
        self.clip_seleccionado_idx = max(0, min(self.clip_seleccionado_idx, len(self.timeline_data) - 1))
        item = self.timeline_data[self.clip_seleccionado_idx]
        nombre = os.path.basename(item["archivo"])
        if len(nombre) > 22:
            nombre = nombre[:20] + ".."
        off = float(item.get("offset", 0.0))
        kw = (item.get("keyword") or "").strip()
        txt_kw = f" | 🔎 \"{kw[:22]}\"" if kw else ""
        self.lbl_clip_activo_capcut.configure(
            text=f"🎯 Clip #{item['orden']}: {nombre} | {item['inicio']:.1f}s-{item['fin']:.1f}s (Dur: {item['duracion']:.1f}s | Inicio: +{off:.1f}s){txt_kw}"
        )

    # ---------- Interacción con Mouse en el Lienzo Horizontal ----------
    def _al_clic_canvas_timeline(self, evento):
        if not hasattr(self, "canvas_timeline"):
            return
        if self.reproduciendo_capcut:
            self.pausar_capcut()

        x_canvas = self.canvas_timeline.canvasx(evento.x)
        y_canvas = evento.y
        x0 = self.X_ENCABEZADO_TIMELINE
        if x_canvas < x0:
            return

        tiempo_clic = max(0.0, (x_canvas - x0) / self.zoom_px_seg)
        dur_max = max(self.duracion_total_timeline, float(self.duracion_total_audio or 0.0), 0.1)
        self.posicion_aguja = min(dur_max, tiempo_clic)

        # Verificar si hizo clic en algún bloque o en su asa derecha de recorte (pista de video y=28..108)
        self.arrastrando_borde_idx = None
        for idx, item in enumerate(self.timeline_data):
            x1 = x0 + item["inicio"] * self.zoom_px_seg
            x2 = x0 + item["fin"] * self.zoom_px_seg
            if 28 <= y_canvas <= 108 and abs(x_canvas - x2) <= 8:
                self.clip_seleccionado_idx = idx
                self.arrastrando_borde_idx = idx
                self.dibujar_timeline_ui()
                return
            if x1 <= x_canvas <= x2:
                self.clip_seleccionado_idx = idx
                break

        self.arrastrando_aguja = True
        self.dibujar_timeline_ui()

    def _al_arrastrar_canvas_timeline(self, evento):
        if not hasattr(self, "canvas_timeline"):
            return
        x_canvas = self.canvas_timeline.canvasx(evento.x)
        x0 = self.X_ENCABEZADO_TIMELINE
        tiempo_mouse = max(0.0, (x_canvas - x0) / self.zoom_px_seg)

        # Si está arrastrando el borde derecho de un clip -> Recorte interactivo (Trim)
        if self.arrastrando_borde_idx is not None and 0 <= self.arrastrando_borde_idx < len(self.timeline_data):
            item = self.timeline_data[self.arrastrando_borde_idx]
            nueva_dur = round(max(0.6, tiempo_mouse - item["inicio"]), 2)
            item["duracion"] = nueva_dur
            self.posicion_aguja = item["inicio"] + nueva_dur
            self.dibujar_timeline_ui()
            return

        # Si está arrastrando la aguja roja -> Scrubbing en tiempo real
        if self.arrastrando_aguja:
            dur_max = max(self.duracion_total_timeline, float(self.duracion_total_audio or 0.0), 0.1)
            self.posicion_aguja = min(dur_max, max(0.0, tiempo_mouse))
            self._actualizar_aguja_canvas()
            self._mostrar_frame_capcut(self.posicion_aguja)

    def _al_soltar_canvas_timeline(self, _evento):
        if self.arrastrando_borde_idx is not None:
            self.mostrar_estado(
                f"↔️ Duración del Clip #{self.arrastrando_borde_idx + 1} ajustada a {self.timeline_data[self.arrastrando_borde_idx]['duracion']:.1f}s.",
                "#00E5FF",
            )
        self.arrastrando_borde_idx = None
        self.arrastrando_aguja = False

    def _idx_clip_en_evento(self, evento):
        """Devuelve el índice del clip bajo el mouse (pistas de VIDEO o SUBS), o None."""
        x_canvas = self.canvas_timeline.canvasx(evento.x)
        x0 = self.X_ENCABEZADO_TIMELINE
        if x_canvas < x0 or not (28 <= evento.y <= 148):
            return None
        for idx, item in enumerate(self.timeline_data):
            x1 = x0 + item["inicio"] * self.zoom_px_seg
            x2 = x0 + item["fin"] * self.zoom_px_seg
            if x1 <= x_canvas <= x2:
                return idx
        return None

    def _al_doble_clic_canvas_timeline(self, evento):
        idx = self._idx_clip_en_evento(evento)
        if idx is not None:
            self.arrastrando_borde_idx = None
            self.arrastrando_aguja = False
            self.reemplazar_clip_auto(idx)

    def _menu_contextual_clip(self, evento):
        idx = self._idx_clip_en_evento(evento)
        if idx is None:
            return
        self.pausar_capcut()
        self.clip_seleccionado_idx = idx
        self.dibujar_timeline_ui()
        item = self.timeline_data[idx]
        menu = tk.Menu(self, tearoff=0, bg="#1E2530", fg="#FFFFFF",
                       activebackground="#E65100", activeforeground="#FFFFFF", font=("Segoe UI", 10))
        menu.add_command(
            label=f"🔎 Reemplazar automático (busca: \"{self._consulta_visible(item)}\")",
            command=lambda: self.reemplazar_clip_auto(idx),
        )
        menu.add_command(label="✏️ Reemplazar buscando con mi propia palabra...",
                         command=lambda: self.reemplazar_clip_con_palabra(idx))
        menu.add_command(label="📂 Reemplazar con un video de mi PC...", command=self.elegir_reemplazo_pc_timeline)
        menu.add_command(label="🔄 Rotar con otro clip ya descargado", command=self.reemplazar_clip_seleccionado)
        menu.add_separator()
        menu.add_command(label="▶️ Ver este clip", command=lambda: self.previsualizar_clip(item["archivo"]))
        menu.add_command(label="✂️ Dividir en la aguja", command=self.dividir_clip_en_aguja)
        menu.add_command(label="📄 Duplicar", command=self.duplicar_clip_timeline)
        menu.add_command(label="🗑️ Eliminar", command=self.eliminar_clip_timeline)
        try:
            menu.tk_popup(evento.x_root, evento.y_root)
        finally:
            menu.grab_release()

    def _consulta_visible(self, item):
        kw = (item.get("keyword") or "").strip()
        if kw:
            return kw[:40]
        narr = (item.get("narracion") or "").strip()
        return (narr[:37] + "...") if len(narr) > 40 else (narr or "tema del video")

    def _generar_consulta_para_clip(self, item):
        """
        Obtiene la frase de búsqueda para el clip:
        1) La keyword visual en inglés que la IA asignó a esa escena del guion.
        2) Si no existe, convierte el subtítulo (narración) en 2-4 palabras visuales en inglés con OpenAI.
        3) Si no hay OpenAI, usa las palabras más importantes del subtítulo.
        """
        kw = (item.get("keyword") or "").strip()
        if kw:
            return kw
        narr = (item.get("narracion") or "").strip()
        if narr:
            key_openai = self.entrada_openai.get().strip()
            if key_openai:
                try:
                    service = OpenAIService(key_openai)
                    resp = service.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": (
                                "Convert the narration into a 2-4 word English search query for stock video "
                                "(Pexels/Pixabay) that visually represents it. Concrete, filmable things only. "
                                "Reply with ONLY the query, no quotes."
                            )},
                            {"role": "user", "content": narr[:500]},
                        ],
                        max_tokens=15,
                        temperature=0.4,
                    )
                    consulta = (resp.choices[0].message.content or "").strip().strip('"').strip("'")
                    if consulta:
                        item["keyword"] = consulta
                        return consulta
                except Exception:
                    logging.exception("No se pudo traducir el subtítulo a keyword visual")
            palabras = [p for p in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{5,}", narr)]
            if palabras:
                return " ".join(sorted(palabras, key=len, reverse=True)[:3])
        if self.keywords_actuales:
            return random.choice(self.keywords_actuales)
        return self.entrada_tema.get().strip() or "cinematic"

    def reemplazar_clip_con_palabra(self, idx=None):
        if not self.timeline_data:
            return
        idx = self.clip_seleccionado_idx if idx is None else idx
        dialogo = ctk.CTkInputDialog(
            title="✏️ Buscar clip con tu propia palabra",
            text=(
                f"Clip #{idx + 1} — Subtítulo:\n\"{(self.timeline_data[idx].get('narracion') or '')[:120]}\"\n\n"
                "Escribe qué quieres ver (mejor en inglés, ej: 'gold coins falling'):"
            ),
        )
        consulta = (dialogo.get_input() or "").strip()
        if consulta:
            self.timeline_data[idx]["keyword"] = consulta
            self.reemplazar_clip_auto(idx, consulta_manual=consulta)

    def reemplazar_clip_auto(self, idx=None, consulta_manual=None):
        """
        🔎 Reemplaza el clip por uno NUEVO buscado automáticamente con la palabra/frase de su subtítulo.
        Cada vez que lo pulses trae un clip distinto (nunca repite los ya usados).
        """
        if not self.timeline_data:
            self.mostrar_estado("❌ Primero crea el Storyboard (Paso 3).", "red")
            return
        if getattr(self, "_reemplazo_en_curso", False):
            self.mostrar_estado("⏳ Espera, ya estoy buscando un clip...", "orange")
            return
        if not self.entrada_pexels.get().strip() and not self.entrada_pixabay.get().strip():
            self.mostrar_estado("❌ Para reemplazar automáticamente necesitas tu API Key de Pexels o Pixabay.", "red")
            return

        idx = self.clip_seleccionado_idx if idx is None else idx
        idx = max(0, min(idx, len(self.timeline_data) - 1))
        self.clip_seleccionado_idx = idx
        self.pausar_capcut()
        self._reemplazo_en_curso = True
        self.btn_reemplazo_auto.configure(state="disabled", text="⏳ Buscando...")
        item_ref = self.timeline_data[idx]
        archivo_actual = item_ref["archivo"]

        def _trabajo():
            ruta_nueva = None
            consulta = consulta_manual
            try:
                if not consulta:
                    self.mostrar_estado(f"🧠 Analizando el subtítulo del Clip #{idx + 1}...", "orange")
                    consulta = self._generar_consulta_para_clip(item_ref)
                self.mostrar_estado(f"🔎 Buscando clip nuevo para Clip #{idx + 1}: \"{consulta}\"...", "yellow")
                fuente = self.menu_fuente_visual.get()
                orden = ["pixabay", "pexels"] if fuente.startswith("Pixabay") else ["pexels", "pixabay"]
                excluir = set(self.pool_videos) | {archivo_actual}
                rutas = self._descargar_stock_unico(
                    consulta, idx, orden, 1, prefijo="reemplazo", excluir_archivos=excluir,
                )
                ruta_nueva = rutas[0] if rutas else None
            except Exception as e:
                logging.exception("Error reemplazando clip automáticamente")
                self.mostrar_estado(f"❌ Error buscando clip: {e}", "red")

            def _aplicar():
                self._reemplazo_en_curso = False
                self.btn_reemplazo_auto.configure(state="normal", text="🔎 Reemplazar Auto")
                if not ruta_nueva:
                    self.mostrar_estado(
                        f"⚠️ No encontré clips nuevos para \"{consulta}\". Prueba clic derecho → '✏️ mi propia palabra'.",
                        "orange",
                    )
                    return
                # El clip pudo moverse de posición mientras buscaba: localizarlo por referencia
                pos = next((i for i, it in enumerate(self.timeline_data) if it is item_ref), None)
                if pos is None:
                    return
                item_ref["archivo"] = ruta_nueva
                item_ref["offset"] = 0.0
                if ruta_nueva not in self.pool_videos:
                    self.pool_videos.append(ruta_nueva)
                self.clip_seleccionado_idx = pos
                self.posicion_aguja = item_ref.get("inicio", self.posicion_aguja)
                self.actualizar_lista_clips_ui()
                self.guardar_cache()
                self.dibujar_timeline_ui()
                self.mostrar_estado(
                    f"✅ Clip #{pos + 1} reemplazado por uno nuevo de \"{consulta}\". (Doble clic otra vez = otra opción)",
                    "#00FF00",
                )

            self.after(0, _aplicar)

        threading.Thread(target=_trabajo, daemon=True).start()

    def _al_rueda_canvas_timeline(self, evento):
        direccion = -1 if evento.delta > 0 else 1
        self.canvas_timeline.xview_scroll(direccion * 2, "units")

    # ---------- Herramientas de Edición y Corte estilo CapCut ----------
    def dividir_clip_en_aguja(self):
        """
        ✂️ DIVIDIR (SPLIT):
        Parte el clip donde está la aguja roja en 2 clips independientes:
        - Parte 1: desde inicio hasta la aguja (mantiene offset original)
        - Parte 2: desde la aguja hasta el fin (su offset avanza exactamente lo que duró la Parte 1)
        Si la aguja está fuera o en la orilla del clip seleccionado, divide el clip seleccionado por la mitad.
        """
        if not self.timeline_data:
            self.mostrar_estado("❌ No hay clips en la barra horizontal para dividir.", "red")
            return
        self.pausar_capcut()

        # Buscar si la aguja está dentro de algún clip con margen de al menos 0.4s a cada lado
        idx_objetivo = None
        punto_corte_local = None
        for idx, item in enumerate(self.timeline_data):
            if item["inicio"] + 0.35 < self.posicion_aguja < item["fin"] - 0.35:
                idx_objetivo = idx
                punto_corte_local = round(self.posicion_aguja - item["inicio"], 2)
                break

        # Si la aguja estaba en 0.0 o muy en el borde, partir el clip seleccionado a la mitad
        if idx_objetivo is None:
            idx_objetivo = max(0, min(self.clip_seleccionado_idx, len(self.timeline_data) - 1))
            item = self.timeline_data[idx_objetivo]
            if item["duracion"] < 1.0:
                self.mostrar_estado("⚠️ Este clip ya es muy corto (< 1.0s) para dividirlo más.", "orange")
                return
            punto_corte_local = round(item["duracion"] / 2.0, 2)

        orig = self.timeline_data[idx_objetivo]
        dur_parte1 = round(max(0.5, punto_corte_local), 2)
        dur_parte2 = round(max(0.5, orig["duracion"] - dur_parte1), 2)
        offset_orig = float(orig.get("offset", 0.0))

        clip_parte1 = {
            "orden": orig["orden"],
            "archivo": orig["archivo"],
            "inicio": orig["inicio"],
            "fin": round(orig["inicio"] + dur_parte1, 2),
            "duracion": dur_parte1,
            "offset": offset_orig,
            "narracion": orig.get("narracion", ""),
        }
        clip_parte2 = {
            "orden": orig["orden"] + 1,
            "archivo": orig["archivo"],
            "inicio": round(orig["inicio"] + dur_parte1, 2),
            "fin": orig["fin"],
            "duracion": dur_parte2,
            "offset": round(offset_orig + dur_parte1, 2),
            "narracion": orig.get("narracion", ""),
        }

        self.timeline_data[idx_objetivo:idx_objetivo + 1] = [clip_parte1, clip_parte2]
        self.clip_seleccionado_idx = idx_objetivo + 1
        self.posicion_aguja = clip_parte2["inicio"]
        self.dibujar_timeline_ui()
        self.mostrar_estado(
            f"✂️ Clip dividido en 2 partes ({dur_parte1:.1f}s y {dur_parte2:.1f}s). Ahora puedes borrar, cambiar o mover cualquiera de las mitades.",
            "#00FF00",
        )

    def mover_clip_izquierda(self):
        if not self.timeline_data or self.clip_seleccionado_idx <= 0:
            return
        idx = self.clip_seleccionado_idx
        self.timeline_data[idx - 1], self.timeline_data[idx] = (
            self.timeline_data[idx],
            self.timeline_data[idx - 1],
        )
        self.clip_seleccionado_idx = idx - 1
        self.recalcular_tiempos_timeline()
        self.posicion_aguja = self.timeline_data[self.clip_seleccionado_idx]["inicio"]
        self.dibujar_timeline_ui()
        self.mostrar_estado(f"⬅️ Clip movido a la posición #{self.clip_seleccionado_idx + 1}.", "#00E5FF")

    def mover_clip_derecha(self):
        if not self.timeline_data or self.clip_seleccionado_idx >= len(self.timeline_data) - 1:
            return
        idx = self.clip_seleccionado_idx
        self.timeline_data[idx + 1], self.timeline_data[idx] = (
            self.timeline_data[idx],
            self.timeline_data[idx + 1],
        )
        self.clip_seleccionado_idx = idx + 1
        self.recalcular_tiempos_timeline()
        self.posicion_aguja = self.timeline_data[self.clip_seleccionado_idx]["inicio"]
        self.dibujar_timeline_ui()
        self.mostrar_estado(f"➡️ Clip movido a la posición #{self.clip_seleccionado_idx + 1}.", "#00E5FF")

    def mover_clip_arriba(self, idx):
        self.clip_seleccionado_idx = idx
        self.mover_clip_izquierda()

    def mover_clip_abajo(self, idx):
        self.clip_seleccionado_idx = idx
        self.mover_clip_derecha()

    def reemplazar_clip(self, idx):
        self.clip_seleccionado_idx = idx
        self.reemplazar_clip_seleccionado()

    def reemplazar_clip_seleccionado(self):
        if not self.timeline_data:
            return
        idx = self.clip_seleccionado_idx
        actual = self.timeline_data[idx]["archivo"]
        opciones = [v for v in self.pool_videos if v != actual and os.path.exists(v)]
        if opciones:
            if actual in self.pool_videos:
                pos_pool = (self.pool_videos.index(actual) + 1) % len(self.pool_videos)
                nuevo = self.pool_videos[pos_pool]
            else:
                nuevo = random.choice(opciones)
            self.timeline_data[idx]["archivo"] = nuevo
            self.timeline_data[idx]["offset"] = 0.0
            self.dibujar_timeline_ui()
            self.mostrar_estado(f"🔄 Clip #{idx + 1} cambiado por: {os.path.basename(nuevo)}", "#00E5FF")
        else:
            self.elegir_reemplazo_pc_timeline()

    def elegir_reemplazo_pc_timeline(self):
        if not self.timeline_data:
            self.mostrar_estado("❌ Primero crea el Storyboard o inserta un clip.", "red")
            return
        archivo = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.mov *.mkv *.webm")])
        if archivo and os.path.exists(archivo):
            if archivo not in self.pool_videos:
                self.pool_videos.append(archivo)
                self.actualizar_lista_clips_ui()
            idx = self.clip_seleccionado_idx
            self.timeline_data[idx]["archivo"] = archivo
            self.timeline_data[idx]["offset"] = 0.0
            self.dibujar_timeline_ui()
            self.mostrar_estado(f"📂 Clip #{idx + 1} reemplazado por: {os.path.basename(archivo)}", "#00FF00")

    def insertar_clip_timeline(self):
        self.pausar_capcut()
        archivo = filedialog.askopenfilename(
            title="Selecciona el video para insertar en la barra horizontal",
            filetypes=[("Videos", "*.mp4 *.mov *.mkv *.webm")],
        )
        if not archivo and self.pool_videos:
            archivo = random.choice(self.pool_videos)
        if not archivo or not os.path.exists(archivo):
            return
        if archivo not in self.pool_videos:
            self.pool_videos.append(archivo)
            self.actualizar_lista_clips_ui()

        nuevo_item = {
            "orden": len(self.timeline_data) + 1,
            "archivo": archivo,
            "inicio": 0.0,
            "fin": 3.0,
            "duracion": 3.0,
            "offset": 0.0,
            "narracion": "",
        }
        if self.timeline_data:
            pos_ins = min(len(self.timeline_data), self.clip_seleccionado_idx + 1)
            self.timeline_data.insert(pos_ins, nuevo_item)
            self.clip_seleccionado_idx = pos_ins
        else:
            self.timeline_data.append(nuevo_item)
            self.clip_seleccionado_idx = 0

        self.dibujar_timeline_ui()
        self.cambiar_estado_boton(self.btn_exp_mp4, "normal")
        self.cambiar_estado_boton(self.btn_exp_capcut, "normal")
        self.mostrar_estado(f"➕ Clip insertado en la posición #{self.clip_seleccionado_idx + 1}.", "#00FF00")

    def duplicar_clip_timeline(self):
        if not self.timeline_data:
            return
        idx = self.clip_seleccionado_idx
        copia = dict(self.timeline_data[idx])
        self.timeline_data.insert(idx + 1, copia)
        self.clip_seleccionado_idx = idx + 1
        self.dibujar_timeline_ui()
        self.mostrar_estado(f"📄 Clip #{idx + 1} duplicado.", "#00E5FF")

    def eliminar_clip_timeline(self):
        if not self.timeline_data:
            return
        if len(self.timeline_data) == 1:
            self.mostrar_estado("⚠️ Debe quedar al menos 1 clip en el Timeline.", "orange")
            return
        idx = self.clip_seleccionado_idx
        eliminado = self.timeline_data.pop(idx)
        self.clip_seleccionado_idx = max(0, min(idx, len(self.timeline_data) - 1))
        self.dibujar_timeline_ui()
        self.mostrar_estado(f"🗑️ Clip eliminado ({os.path.basename(eliminado['archivo'])}).", "yellow")

    def ajustar_duracion_clip_sel(self, delta_seg):
        if not self.timeline_data:
            return
        idx = self.clip_seleccionado_idx
        nueva_dur = round(max(0.5, float(self.timeline_data[idx]["duracion"]) + float(delta_seg)), 2)
        self.timeline_data[idx]["duracion"] = nueva_dur
        self.dibujar_timeline_ui()
        self.mostrar_estado(f"⏱️ Clip #{idx + 1}: duración ajustada a {nueva_dur:.1f}s.", "#00E5FF")

    def ajustar_offset_clip_sel(self, delta_seg):
        if not self.timeline_data:
            return
        idx = self.clip_seleccionado_idx
        item = self.timeline_data[idx]
        nuevo_off = round(max(0.0, float(item.get("offset", 0.0)) + float(delta_seg)), 2)
        item["offset"] = nuevo_off
        self.posicion_aguja = item["inicio"]
        self.dibujar_timeline_ui()
        self.mostrar_estado(
            f"🎞️ Clip #{idx + 1}: punto de inicio dentro del video movido a +{nuevo_off:.1f}s.",
            "#00E5FF",
        )

    def ajustar_todo_al_audio(self):
        """Escala proporcionalmente la duración de todos los clips para cuadrar al 100% con la pista de voz."""
        if not self.timeline_data or self.duracion_total_audio <= 0.2:
            self.mostrar_estado("⚠️ Primero genera la voz (Paso 2) y el Storyboard.", "orange")
            return
        suma_actual = self.duracion_total_timeline
        if suma_actual <= 0.1:
            return
        factor = float(self.duracion_total_audio) / suma_actual
        for item in self.timeline_data:
            item["duracion"] = round(max(0.5, item["duracion"] * factor), 2)
        self.recalcular_tiempos_timeline()
        # Ajustar diferencia de redondeo en el último clip
        dif = round(float(self.duracion_total_audio) - self.duracion_total_timeline, 2)
        if abs(dif) > 0.02 and self.timeline_data:
            self.timeline_data[-1]["duracion"] = round(max(0.5, self.timeline_data[-1]["duracion"] + dif), 2)
        self.dibujar_timeline_ui()
        self.mostrar_estado(
            f"⚖️ Todos los clips se sincronizaron exactamente a los {self.duracion_total_audio:.1f}s de tu locución.",
            "#00FF00",
        )

    # ---------- Reproductor en Vivo Integrado en el Timeline CapCut ----------
    def _segmento_capcut_en(self, t):
        for idx, seg in enumerate(self.timeline_data):
            if seg["inicio"] <= t <= seg["fin"] + 0.02:
                return idx, seg, max(0.0, t - seg["inicio"])
        ultimo = self.timeline_data[-1]
        return len(self.timeline_data) - 1, ultimo, max(0.0, ultimo["duracion"] - 0.05)

    def _mostrar_frame_capcut(self, t):
        if not self.timeline_data:
            return
        try:
            idx, seg, t_local = self._segmento_capcut_en(t)
            clip = self._obtener_clip_capcut(seg["archivo"])
            t_clip = float(seg.get("offset", 0.0)) + t_local
            if clip.duration and clip.duration > 0.1:
                t_clip = t_clip % max(0.05, clip.duration - 0.08)
            frame = clip.get_frame(max(0.0, t_clip))
            img = PIL.Image.fromarray(frame)

            ancho_m, alto_m = (82, 144) if self.es_vertical else (190, 108)
            ratio_obj = ancho_m / alto_m
            w, h = img.size
            if (w / h) > ratio_obj:
                nw = int(h * ratio_obj)
                x1 = (w - nw) // 2
                img = img.crop((x1, 0, x1 + nw, h))
            else:
                nh = int(w / ratio_obj)
                y1 = (h - nh) // 2
                img = img.crop((0, y1, w, y1 + nh))
            img = img.resize((ancho_m, alto_m), PIL.Image.Resampling.BILINEAR)

            self.foto_monitor_capcut = ctk.CTkImage(light_image=img, dark_image=img, size=(ancho_m, alto_m))
            self.lbl_monitor_capcut.configure(image=self.foto_monitor_capcut, text="")
            narr = seg.get("narracion", "")
            self.lbl_sub_capcut.configure(
                text=f"🗣️ Clip #{idx + 1}: \"{narr[:115]}\"" if narr else f"🎬 Viendo Clip #{idx + 1}: {os.path.basename(seg['archivo'])}"
            )
        except Exception:
            logging.exception("Error mostrando frame en monitor CapCut")

    def alternar_play_capcut(self):
        if self.reproduciendo_capcut:
            self.pausar_capcut()
        else:
            self.reproducir_capcut()

    def reproducir_capcut(self):
        if not self.timeline_data:
            self.mostrar_estado("❌ Primero crea el Storyboard (Paso 3) para reproducir el Timeline.", "red")
            return
        dur_max = self.duracion_total_timeline
        if self.posicion_aguja >= dur_max - 0.08:
            self.posicion_aguja = 0.0
        self.reproduciendo_capcut = True
        self.inicio_reloj_capcut = time.perf_counter() - self.posicion_aguja
        if os.path.exists(self.ARCHIVO_VOZ):
            if self.audio_capcut is None:
                self.audio_capcut = ReproductorAudioMCI(self.ARCHIVO_VOZ)
            self.audio_capcut.reproducir_desde(self.posicion_aguja)
        self.btn_play_capcut.configure(text="⏸️ Pausa", fg_color="#F9A825")
        self._tick_capcut()

    def pausar_capcut(self):
        self.reproduciendo_capcut = False
        if self.audio_capcut:
            self.audio_capcut.pausar()
        if hasattr(self, "btn_play_capcut"):
            self.btn_play_capcut.configure(text="▶️ Play", fg_color="#2E7D32")

    def reiniciar_aguja_capcut(self):
        estaba = self.reproduciendo_capcut
        self.pausar_capcut()
        self.posicion_aguja = 0.0
        self.clip_seleccionado_idx = 0
        self.dibujar_timeline_ui()
        if estaba:
            self.reproducir_capcut()

    def _tick_capcut(self):
        if not self.reproduciendo_capcut:
            return
        t0 = time.perf_counter()
        self.posicion_aguja = t0 - self.inicio_reloj_capcut
        dur_max = self.duracion_total_timeline
        if self.posicion_aguja >= dur_max:
            self.posicion_aguja = dur_max
            self._actualizar_aguja_canvas()
            self.pausar_capcut()
            return
        self._actualizar_aguja_canvas()
        self._mostrar_frame_capcut(self.posicion_aguja)
        gastado = int((time.perf_counter() - t0) * 1000)
        self.after(max(20, 66 - gastado), self._tick_capcut)

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
            dur_short = self.menu_duracion_short.get() if hasattr(self, "menu_duracion_short") else ""
            if "2.5 a 3 Min" in dur_short:
                rango_palabras = "420 a 480 palabras REALES (Short Extendido / Mini-Documental Vertical de 2.5 a 3 minutos). PROHIBIDO resumir; usa [PAUSA] para cambios de acto"
                num_keywords = "18 a 22"
            elif "1.5 a 2 Min" in dur_short:
                rango_palabras = "260 a 310 palabras REALES (Short / TikTok Monetizable de 90 a 120 segundos). Desarrolla cada punto con ejemplos y usa [PAUSA]"
                num_keywords = "14 a 16"
            elif "1 Minuto" in dur_short:
                rango_palabras = "155 a 180 palabras REALES (Short Completo de 60 segundos exactos)"
                num_keywords = "10 a 12"
            else:
                rango_palabras = "90 a 110 palabras (Short Rápido de 30 a 45 segundos)"
                num_keywords = "6 a 9"

            reglas_formato = f"""2. LONGITUD OBLIGATORIA: Escribe un guion vertical de {rango_palabras}.
3. TONO DEL GÉNERO ({genero_nombre}): {info_gen['instruccion_tono']}
4. ESTRUCTURA (Gancho, Desarrollo en Escalada y Desenlace):
   - GANCHO: Empieza en el segundo 0 con un impacto brutal o intriga extrema. CERO saludos.
   - DESARROLLO: Cuenta la historia/conflicto con ritmo trepidante, micro-ganchos cada 15 segundos y tensión constante sin relleno.
   - DESENLACE: {info_gen['cierre_estructura']}"""
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

            # NUEVO GUION = NUEVO VIDEO: se descartan los clips y el storyboard del video anterior
            # para que jamás se mezclen clips de otro tema en este video.
            self.pool_videos = []
            self.timeline_data = []
            self.clip_seleccionado_idx = 0
            self.posicion_aguja = 0.0
            self.after(0, self.pausar_capcut)
            self.after(0, self.cerrar_cache_clips_capcut)
            self.after(0, self.actualizar_lista_clips_ui)
            self.after(0, self.dibujar_timeline_ui)

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
        if getattr(self, "reproductor_voz", None):
            # Liberamos el archivo de voz si se está escuchando para poder sobrescribirlo
            self.after(0, self.alternar_escuchar_voz)
            time.sleep(0.4)
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
            self.timeline_data = []
            self.reproduciendo_capcut = False
            if self.audio_capcut:
                try:
                    self.audio_capcut.pausar()
                except Exception:
                    pass
            # Cerrar lectores de video abiertos (en Windows bloquean la sobrescritura de archivos)
            self.cerrar_cache_clips_capcut()
            self.after(0, self.dibujar_timeline_ui)
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

    # ==========================================
    # BÚSQUEDA DE STOCK SIN REPETIR (entre videos y sesiones)
    # ==========================================
    def _descargar_stock_unico(self, keyword, idx_escena, fuentes, cantidad=1, prefijo="clip",
                               excluir_archivos=None, max_paginas=4):
        """
        Busca y descarga 'cantidad' clips para 'keyword' que NUNCA se hayan usado antes
        (memoria persistente en historial_clips_usados.json). Recorre varias páginas de
        resultados de Pexels / Pixabay hasta encontrar clips nuevos.
        Devuelve la lista de rutas descargadas.
        """
        if not hasattr(self, "historial_clips"):
            self.historial_clips = HistorialClipsUsados()
        historial = self.historial_clips
        excluir_archivos = set(excluir_archivos or [])

        key_pexels = self.entrada_pexels.get().strip()
        key_pixabay = self.entrada_pixabay.get().strip()
        pexels = PexelsService(key_pexels) if key_pexels else None
        pixabay = PixabayService(key_pixabay) if key_pixabay else None
        ori = "portrait" if self.es_vertical else "landscape"
        marca = int(time.time() * 1000) % 10_000_000

        descargados = []
        candidatos_repetidos = []  # por si TODO ya fue usado: último recurso

        for fuente in fuentes:
            if len(descargados) >= cantidad:
                break
            for pagina in range(1, max_paginas + 1):
                if len(descargados) >= cantidad:
                    break
                try:
                    if fuente == "pexels" and pexels:
                        resultados = pexels.buscar_videos(keyword, 15, ori, pagina=pagina)
                    elif fuente == "pixabay" and pixabay:
                        resultados = pixabay.buscar_videos(keyword, cantidad=15, pagina=pagina)
                    else:
                        break
                except Exception:
                    logging.exception("Error buscando '%s' en %s (página %s)", keyword, fuente, pagina)
                    break
                if not resultados:
                    break

                for obj in resultados:
                    if len(descargados) >= cantidad:
                        break
                    if fuente == "pexels":
                        url_hd = PexelsService.elegir_mejor_archivo(obj, vertical=self.es_vertical)
                    else:
                        url_hd = PixabayService.elegir_mejor_archivo(obj)
                    if not url_hd:
                        continue
                    clave = HistorialClipsUsados.clave(fuente, obj, url_hd)
                    if historial.ya_usado(clave):
                        candidatos_repetidos.append((fuente, obj, url_hd, clave))
                        continue
                    nombre = os.path.join(
                        self.CARPETA_ASSETS,
                        f"{prefijo}_{idx_escena:02d}_{fuente}_{obj.get('id', marca)}_{limpiar_nombre(keyword)[:30]}.mp4",
                    )
                    if nombre in excluir_archivos:
                        continue
                    try:
                        PexelsService.descargar(url_hd, nombre)
                        historial.registrar(clave)
                        descargados.append(nombre)
                    except Exception:
                        logging.exception("Error descargando clip de %s", fuente)

        # Último recurso: si absolutamente todo ya estaba usado, toma uno repetido distinto al actual
        if not descargados and candidatos_repetidos:
            random.shuffle(candidatos_repetidos)
            for fuente, obj, url_hd, clave in candidatos_repetidos:
                nombre = os.path.join(
                    self.CARPETA_ASSETS,
                    f"{prefijo}_{idx_escena:02d}_{fuente}_{obj.get('id', marca)}_{limpiar_nombre(keyword)[:30]}.mp4",
                )
                if nombre in excluir_archivos:
                    continue
                try:
                    if not os.path.exists(nombre):
                        PexelsService.descargar(url_hd, nombre)
                    descargados.append(nombre)
                    break
                except Exception:
                    logging.exception("Error en último recurso de descarga")
        return descargados

    def _cantidad_clips_por_escena(self):
        es_short_extenso = self.es_vertical and len(self.keywords_actuales) >= 14
        if self.es_vertical:
            return 2 if es_short_extenso else 1
        return 3 if self.es_extra_largo else 2

    def generar_clips_pexels(self):
        self.mostrar_estado("Buscando clips HD NUEVOS en Pexels (sin repetir videos anteriores)...", "yellow")
        if not self.entrada_pexels.get().strip():
            raise ValueError("Falta la API key de Pexels.")
        cantidad = self._cantidad_clips_por_escena()
        for idx_kw, kw in enumerate(self.keywords_actuales):
            self.mostrar_estado(f"🔎 Pexels escena {idx_kw + 1}/{len(self.keywords_actuales)}: {kw}...", "yellow")
            for ruta in self._descargar_stock_unico(kw, idx_kw, ["pexels"], cantidad, prefijo="escena"):
                if ruta not in self.pool_videos:
                    self.pool_videos.append(ruta)
        self.mostrar_estado(f"✅ {len(self.pool_videos)} Clips HD únicos de Pexels descargados.", "green")

    def generar_clips_pixabay(self):
        self.mostrar_estado("Buscando clips HD NUEVOS en Pixabay (sin repetir videos anteriores)...", "yellow")
        if not self.entrada_pixabay.get().strip():
            raise ValueError("Falta la API key de Pixabay (es 100% gratis en pixabay.com/api/docs/).")
        cantidad = self._cantidad_clips_por_escena()
        for idx_kw, kw in enumerate(self.keywords_actuales):
            self.mostrar_estado(f"🔎 Pixabay escena {idx_kw + 1}/{len(self.keywords_actuales)}: {kw}...", "yellow")
            for ruta in self._descargar_stock_unico(kw, idx_kw, ["pixabay"], cantidad, prefijo="pixabay"):
                if ruta not in self.pool_videos:
                    self.pool_videos.append(ruta)
        self.mostrar_estado(f"✅ {len(self.pool_videos)} Clips HD únicos de Pixabay descargados.", "green")

    def generar_clips_combo_gratis(self):
        """Alterna y respalda automáticamente entre Pexels y Pixabay para máxima variedad a costo $0."""
        self.mostrar_estado("Buscando en Combo Gratis HD (Pexels + Pixabay, sin repetir)...", "yellow")
        key_pexels = self.entrada_pexels.get().strip()
        key_pixabay = self.entrada_pixabay.get().strip()
        if not key_pexels and not key_pixabay:
            raise ValueError("Ingresa al menos tu API Key gratuita de Pexels o de Pixabay.")
        clips_por_escena = 1 if self.es_vertical else (2 if self.es_extra_largo else 1)

        for idx_kw, kw in enumerate(self.keywords_actuales):
            orden_fuentes = ["pixabay", "pexels"] if (idx_kw % 2 == 1 and key_pixabay) else ["pexels", "pixabay"]
            self.mostrar_estado(f"🔎 Combo Gratis [{idx_kw + 1}/{len(self.keywords_actuales)}]: {kw}...", "yellow")
            for ruta in self._descargar_stock_unico(kw, idx_kw, orden_fuentes, clips_por_escena, prefijo="combo"):
                if ruta not in self.pool_videos:
                    self.pool_videos.append(ruta)

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

        # 2. ESCENAS RESTANTES (o Escena 0 si no había API Key de Fal): Pexels/Pixabay Gratis (SIN REPETIR) -> Fallback Pollinations Flux Gratis
        inicio_idx = 1 if gancho_listo else 0
        for idx in range(inicio_idx, total_escenas):
            kw = keywords[idx] if idx < len(keywords) else prompts[idx]
            prompt_esc = prompts[idx] if idx < len(prompts) else kw
            descargado = False

            if key_pexels or key_pixabay:
                orden = ["pexels", "pixabay"] if (idx % 2 == 1 or not key_pixabay) else ["pixabay", "pexels"]
                self.mostrar_estado(f"🔎 Híbrido Escena {idx + 1}/{total_escenas} (Stock Gratis): {kw}...", "yellow")
                rutas = self._descargar_stock_unico(kw, idx, orden, 1, prefijo="hibrido")
                if rutas:
                    self.pool_videos.append(rutas[0])
                    descargado = True

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
                keyword_asociada = ""

                if pesos_escenas and total_palabras > 0:
                    # Calculamos qué escena corresponde al progreso actual del audio
                    progreso = min(0.999, tiempo_act / max(0.1, self.duracion_total_audio))
                    idx_escena_actual = min(len(pesos_escenas) - 1, int(progreso * len(pesos_escenas)))
                    narracion_asociada = textos_escenas[idx_escena_actual]
                    esc = self.escenas_guion[idx_escena_actual] if idx_escena_actual < len(self.escenas_guion) else {}
                    keyword_asociada = esc.get("keyword_pexels", "") if isinstance(esc, dict) else ""
                    if not keyword_asociada and idx_escena_actual < len(self.keywords_actuales):
                        keyword_asociada = self.keywords_actuales[idx_escena_actual]

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
                    "offset": 0.0,
                    "narracion": narracion_asociada,
                    "keyword": keyword_asociada,
                })
                tiempo_act += duracion_real
                orden += 1
                idx_clip += 1

            self.clip_seleccionado_idx = 0
            self.posicion_aguja = 0.0
            self.after(0, self.cerrar_cache_clips_capcut)
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

        self.pausar_capcut()
        self.mostrar_estado("Renderizando MP4 Final...", "yellow")
        self.cambiar_estado_boton(self.btn_exp_mp4, "disabled")

        renderer = VideoRenderer(self.formato_actual)
        clips_finales = []
        audio_clip = None
        bgm_clip = None
        video_final = None
        try:
            clips_finales = [
                renderer.procesar_recorte_clip(i["archivo"], i["duracion"], offset=i.get("offset", 0.0))
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

        self.pausar_capcut()
        self.mostrar_estado("Preparando Carpeta...", "yellow")
        self.cambiar_estado_boton(self.btn_exp_capcut, "disabled")
        renderer = VideoRenderer(self.formato_actual)
        try:
            carpeta = f"PROYECTO_CAPCUT_{self.formato_actual}"
            os.makedirs(carpeta, exist_ok=True)
            shutil.copy(self.ARCHIVO_VOZ, os.path.join(carpeta, "00_PISTA_AUDIO.mp3"))
            for item in self.timeline_data:
                clip_procesado = renderer.procesar_recorte_clip(
                    item["archivo"], item["duracion"], offset=item.get("offset", 0.0)
                )
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

        self.formato_actual = self.obtener_formato_seleccionado()
        opcion_cant = self.menu_cant_clips.get()
        if "1 Minuto" in opcion_cant:
            num_clips, dur_min, dur_max = 3, 50, 70
        elif "1.5 a 2 Min" in opcion_cant:
            num_clips, dur_min, dur_max = 2, 85, 125
        elif "2 a 3 Minutos" in opcion_cant:
            num_clips, dur_min, dur_max = 1, 120, 178
        elif opcion_cant.startswith("5"):
            num_clips, dur_min, dur_max = 5, 15, 40
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
                text="▶️ Ver Clip (con audio)",
                fg_color="#00897B",
                width=210,
                command=lambda c=clip_info: self.previsualizar_clip(c.get("archivo", ""), con_audio_propio=True),
            ).pack(pady=2)
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

            dur_short = self.menu_duracion_short.get() if hasattr(self, "menu_duracion_short") else ""
            if not self.es_vertical:
                long_remix = "1200 a 1600 palabras (Formato Largo)"
                num_esc_remix = 16
            elif "2.5 a 3 Min" in dur_short:
                long_remix = "420 a 480 palabras REALES (Short Extendido de 2.5 a 3 minutos)"
                num_esc_remix = 18
            elif "1.5 a 2 Min" in dur_short:
                long_remix = "260 a 310 palabras REALES (Short Monetizable de 1.5 a 2 minutos)"
                num_esc_remix = 14
            elif "1 Minuto" in dur_short:
                long_remix = "155 a 180 palabras REALES (Short Completo de 1 minuto)"
                num_esc_remix = 10
            else:
                long_remix = "90 a 110 palabras (Short Rápido de 30-45 segundos)"
                num_esc_remix = 8

            prompt_remix = f"""Analiza la siguiente transcripción de un video que ya demostró ser viral:
--- TRANSCRIPCIÓN ORIGINAL ---
{texto_original[:8000]}
--- FIN TRANSCRIPCIÓN ---

Tu misión: Reescribe un guion 100% NUEVO, original, sin plagio literal pero conservando y potenciando la idea ganadora, el gancho y la estructura de retención, adaptado al género: {genero_nombre}.
Tono: {info_gen['instruccion_tono']}
Longitud: {long_remix}.
Cierre: {info_gen['cierre_estructura']}

Devuelve ESTRICTAMENTE un JSON con:
- 'guion_locucion': texto completo en ESPAÑOL para narrar.
- 'escenas': lista de {num_esc_remix} escenas ordenadas con 'narracion', 'keyword_pexels' y 'prompt_ia'.
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
