import customtkinter as ctk
import threading
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

    def generar_guion(self, modelo, prompt):
        res = self.client.chat.completions.create(
            model=modelo,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un director creativo y guionista experto en retención viral para YouTube y Shorts "
                        "del nicho de finanzas, inversiones y geopolítica económica. Respondes siempre en JSON válido."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(res.choices[0].message.content)

    def transcribir(self, ruta_audio):
        with open(ruta_audio, "rb") as audio_file:
            return self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )

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


class ElevenLabsService:
    VOCES = {
        "Adam (Profunda / Narrador)": "pNInz6obpgDQGcFmaJgB",
        "Antoni (Dinámica / Joven)": "ErXwobaYiN019PkySvjV",
        "Arnold (Autoridad / Documental)": "VR6AewLTigWG4xSOukaG",
        "Josh (Cálida / Storytelling)": "TxGEqnHWrfWFTfGW9XjX",
    }
    MAX_CHARS_POR_BLOQUE = 3800

    def __init__(self, api_key, voice_id=None):
        if not api_key:
            raise ValueError("Falta la API key de ElevenLabs.")
        self.api_key = api_key
        self.voice_id = voice_id or self.VOCES["Adam (Profunda / Narrador)"]

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
                    "model_id": "eleven_multilingual_v2",
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
    Generador de video IA vía Fal.ai (Kling, Seedance, Luma, etc.).
    Patrón submit + poll. Text-to-video directo. Pago por uso.
    Obtén tu key en: https://fal.ai/dashboard/keys
    """

    MODELOS = {
        "Kling": "fal-ai/kling-video/v1.6/standard/text-to-video",
        "Seedance": "fal-ai/bytedance/seedance/v1/lite/text-to-video",
        "Luma": "fal-ai/luma-dream-machine",
    }

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de Fal.ai.")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def _endpoint(self, modelo):
        ruta = self.MODELOS.get(modelo, self.MODELOS["Kling"])
        return f"https://queue.fal.run/{ruta}"

    def iniciar_generacion(self, prompt, modelo, vertical=True):
        aspect_ratio = "9:16" if vertical else "16:9"
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": "5",
        }
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
                video_url = final.json()["video"]["url"]
                video_bytes = requests.get(video_url, timeout=REQUEST_TIMEOUT)
                video_bytes.raise_for_status()
                with open(ruta_salida, "wb") as f:
                    f.write(video_bytes.content)
                return ruta_salida

            if estado in ("FAILED", "ERROR"):
                raise Exception(f"Fal.ai falló al generar el video (estado: {estado}).")

            time.sleep(10)

        raise TimeoutError("Fal.ai tardó demasiado en generar el video.")


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
            frame_izq, values=["SHORT (Vertical)", "LARGO (Horizontal)"], width=300
        )
        self.menu_formato.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🧠 Motor de Inteligencia Artificial:").pack(anchor="w", padx=20, pady=(10, 0))
        self.menu_motor_ia = ctk.CTkOptionMenu(
            frame_izq,
            values=["gpt-4o (Alta Calidad / Largo)", "gpt-4o-mini (Rápido / Económico)"],
            width=300, fg_color="#E91E63",
        )
        self.menu_motor_ia.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🎙️ Voz ElevenLabs:").pack(anchor="w", padx=20, pady=(8, 0))
        self.menu_voz_eleven = ctk.CTkOptionMenu(
            frame_izq,
            values=list(ElevenLabsService.VOCES.keys()),
            width=300, fg_color="#1976D2",
        )
        self.menu_voz_eleven.pack(padx=20, pady=5)

        # FUENTE VISUAL
        ctk.CTkLabel(
            frame_izq, text="🎨 Fuente de Visuales:",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#9C27B0",
        ).pack(anchor="w", padx=20, pady=(15, 0))
        self.menu_fuente_visual = ctk.CTkOptionMenu(
            frame_izq,
            values=[
                "Pexels (Clips reales)",
                "OpenAI Images (IA + Zoom Ken Burns)",
                "Stability Video (IA)",
                "Runway Video (IA)",
                "Fal.ai (Kling/Seedance/Luma)",
            ],
            width=300, fg_color="#9C27B0",
        )
        self.menu_fuente_visual.pack(padx=20, pady=5)

        # MODELO FAL
        ctk.CTkLabel(frame_izq, text="🎞️ Modelo Fal.ai:").pack(anchor="w", padx=20, pady=(5, 0))
        self.menu_modelo_fal = ctk.CTkOptionMenu(
            frame_izq, values=["Kling", "Seedance", "Luma"], width=300, fg_color="#673AB7",
        )
        self.menu_modelo_fal.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🔑 API Keys:").pack(anchor="w", padx=20, pady=(15, 0))
        self.entrada_openai = ctk.CTkEntry(frame_izq, width=300, placeholder_text="OpenAI sk-...", show="*")
        self.entrada_openai.pack(padx=20, pady=2)
        self.entrada_eleven = ctk.CTkEntry(frame_izq, width=300, placeholder_text="ElevenLabs", show="*")
        self.entrada_eleven.pack(padx=20, pady=2)
        self.entrada_pexels = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Pexels", show="*")
        self.entrada_pexels.pack(padx=20, pady=2)
        self.entrada_stability = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Stability AI", show="*")
        self.entrada_stability.pack(padx=20, pady=2)
        self.entrada_runway = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Runway", show="*")
        self.entrada_runway.pack(padx=20, pady=2)
        self.entrada_fal = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Fal.ai", show="*")
        self.entrada_fal.pack(padx=20, pady=2)

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

    def guardar_keys(self):
        keys_data = {
            "openai": self.entrada_openai.get().strip(),
            "elevenlabs": self.entrada_eleven.get().strip(),
            "pexels": self.entrada_pexels.get().strip(),
            "stability": self.entrada_stability.get().strip(),
            "runway": self.entrada_runway.get().strip(),
            "fal": self.entrada_fal.get().strip(),
            "motor_ia": self.menu_motor_ia.get(),
            "voz_eleven": self.menu_voz_eleven.get(),
            "fuente_visual": self.menu_fuente_visual.get(),
            "modelo_fal": self.menu_modelo_fal.get(),
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
            if k.get("stability"):
                self.entrada_stability.insert(0, k["stability"])
            if k.get("runway"):
                self.entrada_runway.insert(0, k["runway"])
            if k.get("fal"):
                self.entrada_fal.insert(0, k["fal"])
            if k.get("motor_ia"):
                self.menu_motor_ia.set(k["motor_ia"])
            if k.get("voz_eleven") and k["voz_eleven"] in ElevenLabsService.VOCES:
                self.menu_voz_eleven.set(k["voz_eleven"])
            if k.get("fuente_visual"):
                self.menu_fuente_visual.set(k["fuente_visual"])
            if k.get("modelo_fal"):
                self.menu_modelo_fal.set(k["modelo_fal"])
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

    # ==========================================
    # PASO 1: PROMPT
    # ==========================================
    def ejecutar_crear_prompt(self):
        self.after(0, lambda: self.pestanas.set("📝 1. Guion y Prompt"))
        tema = self.entrada_tema.get().strip()
        if not tema:
            self.mostrar_estado("❌ Escribe un tema primero.", "red")
            return

        self.formato_actual = "SHORT" if "SHORT" in self.menu_formato.get() else "LARGO"

        if self.es_vertical:
            reglas_formato = """2. LONGITUD: Escribe un guion explosivo de máximo 90-100 palabras.
3. ESTRUCTURA (Gancho, Nudo y Desenlace):
   - GANCHO: Empieza con una afirmación polémica. CERO saludos.
   - NUDO: Cuenta una mini-historia, usa analogías y mantén la tensión.
   - DESENLACE: Cierra SIEMPRE con un DATO REAL verificable."""
            num_keywords = "6 a 10"
        else:
            reglas_formato = """2. LONGITUD: Escribe un guion MUY EXTENSO de 1600 a 1800 palabras (12 min). Usa [PAUSA] para silencios dramáticos.
3. TONO: Muy espontáneo y apasionado contándole un secreto a un amigo.
4. ESTRUCTURA:
   - GANCHO: Revelación brutal.
   - NUDO: Explica TODOS los detalles explícitamente. Desarrolla a fondo.
   - DESENLACE: Cierra con reflexión y un DATO REAL impactante."""
            num_keywords = "15 a 20"

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

        prompt_base = f"""Actúa como un guionista experto en retención para YouTube. Tu tema es: '{tema}'.

REGLAS DE ORO:
1. IDIOMA: TODO DEBE ESTAR EN ESPAÑOL (excepto las keywords y prompts visuales).
{reglas_formato}{inyeccion_serie}

(IMPORTANTE: Tu respuesta DEBE ser estrictamente un objeto JSON con estas llaves:
- 'guion_locucion': (tu texto completo en ESPAÑOL aplicando la estructura)
- 'escenas': (lista ordenada cronológicamente de {num_keywords} escenas que componen el guion; cada elemento debe ser un objeto con:
    - 'narracion': el fragmento exacto del guion que se narra en esta escena,
    - 'keyword_pexels': búsqueda corta de 2-4 palabras en INGLÉS para banco de video stock que represente visualmente esta escena,
    - 'prompt_ia': prompt cinematográfico detallado en INGLÉS para generar esta escena con IA, sin texto ni marcas de agua)
- 'keywords_visuales': (lista en el mismo orden de los conceptos en INGLÉS de cada escena)
- 'prompts_visuales': (lista en el mismo orden de los prompts DETALLADOS en INGLÉS de cada escena)
- 'titulo_seo': (Un título magnético de alto CTR para este episodio)
- 'descripcion_seo': (Descripción persuasiva con hashtags))."""

        self.after(0, lambda: self.caja_prompt.delete("0.0", "end"))
        self.after(0, lambda: self.caja_prompt.insert("0.0", prompt_base))
        self.mostrar_estado("✅ Mega-Prompt v14 con Sincronización de Escenas creado.", "yellow")

    # ==========================================
    # PASO 1b: ENVIAR A OPENAI
    # ==========================================
    def ejecutar_enviar_guionista(self):
        prompt_final = self.caja_prompt.get("0.0", "end").strip()
        if not prompt_final:
            self.mostrar_estado("❌ Primero genera el prompt.", "red")
            return

        self.mostrar_estado("Enviando a OpenAI... diseñando guion y escenas sincronizadas...", "orange")
        self.cambiar_estado_boton(self.btn_enviar_prompt, "disabled")
        try:
            service = OpenAIService(self.entrada_openai.get().strip())
            modelo = self.menu_motor_ia.get().split()[0]
            datos = service.generar_guion(modelo, prompt_final)

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
            self.mostrar_estado(
                f"✅ Guion y {len(self.escenas_guion) or len(self.keywords_actuales)} escenas sincronizadas listas.",
                "green",
            )
        except Exception as e:
            logging.exception("Error OpenAI")
            self.mostrar_estado(f"❌ Error OpenAI: {e}", "red")
        finally:
            self.cambiar_estado_boton(self.btn_enviar_prompt, "normal")

    # ==========================================
    # PASO 2: VOZ
    # ==========================================
    def ejecutar_paso2(self):
        guion = self.caja_guion.get("0.0", "end").strip()
        if not guion:
            self.mostrar_estado("❌ Primero genera o escribe un guion.", "red")
            return

        self.mostrar_estado("Grabando Voz con ElevenLabs (con pausas limpias)...", "yellow")
        self.cambiar_estado_boton(self.btn_paso2, "disabled")
        try:
            voice_id = ElevenLabsService.VOCES.get(self.menu_voz_eleven.get())
            service = ElevenLabsService(self.entrada_eleven.get().strip(), voice_id=voice_id)
            service.generar_voz(guion, self.ARCHIVO_VOZ)
            self.mostrar_estado("✅ Voz guardada con éxito.", "green")
        except requests.HTTPError as e:
            logging.exception("Error ElevenLabs")
            self.mostrar_estado(f"❌ Error ElevenLabs (verifica saldo/API): {e}", "red")
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
            if fuente.startswith("Pexels"):
                self.generar_clips_pexels()
            elif fuente.startswith("OpenAI Images"):
                self.generar_clips_imagenes_openai()
            elif fuente.startswith("Stability Video"):
                self.generar_clips_stability_video()
            elif fuente.startswith("Runway Video"):
                self.generar_clips_runway_video()
            elif fuente.startswith("Fal.ai"):
                self.generar_clips_fal()

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
        cantidad = 1 if self.es_vertical else 2

        for idx_kw, kw in enumerate(self.keywords_actuales):
            try:
                self.mostrar_estado(
                    f"🔎 Pexels escena {idx_kw + 1}/{len(self.keywords_actuales)}: {kw}...",
                    "yellow",
                )
                videos = service.buscar_videos(kw, cantidad, ori)
            except Exception:
                logging.exception("Error buscando %s en Pexels", kw)
                continue
            for i, v in enumerate(videos):
                nombre = os.path.join(
                    self.CARPETA_ASSETS,
                    f"escena_{idx_kw:02d}_{limpiar_nombre(kw)}_{i}.mp4",
                )
                try:
                    url_hd = PexelsService.elegir_mejor_archivo(v, vertical=self.es_vertical)
                    if not url_hd:
                        continue
                    PexelsService.descargar(url_hd, nombre)
                    if nombre not in self.pool_videos:
                        self.pool_videos.append(nombre)
                except Exception:
                    logging.exception("Error descargando clip de Pexels")
        self.mostrar_estado("✅ Clips HD de Pexels descargados en orden narrativo.", "green")

    def generar_clips_imagenes_openai(self):
        self.mostrar_estado("Generando imágenes con IA + Efecto Ken Burns...", "yellow")
        service = OpenAIService(self.entrada_openai.get().strip())
        renderer = VideoRenderer(self.formato_actual)
        prompts = self.prompts_visuales or self.keywords_actuales

        for i, prompt in enumerate(prompts):
            prompt_img = (
                f"Cinematic realistic scene about: {prompt}. "
                f"High detail, dramatic lighting, professional camera, no text, no watermark."
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

        for i, prompt in enumerate(prompts):
            prompt_img = (
                f"Cinematic realistic scene about: {prompt}. "
                f"High detail, dramatic lighting, no text, no watermark."
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
        self.mostrar_estado(f"Generando video IA con Fal.ai ({modelo})...", "yellow")
        fal = FalVideoService(self.entrada_fal.get().strip())
        prompts = self.prompts_visuales or self.keywords_actuales

        for i, prompt in enumerate(prompts):
            prompt_video = (
                f"Cinematic realistic scene about: {prompt}. "
                f"Smooth camera movement, dramatic lighting, no text, no watermark."
            )
            ruta_video = os.path.join(self.CARPETA_ASSETS, f"fal_{limpiar_nombre(modelo)}_{i:02d}.mp4")
            try:
                self.mostrar_estado(f"🎬 Fal.ai {modelo} {i + 1}/{len(prompts)}...", "yellow")
                _, status_url, response_url = fal.iniciar_generacion(
                    prompt_video, modelo, vertical=self.es_vertical
                )
                fal.esperar_y_descargar(status_url, response_url, ruta_video)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except Exception:
                logging.exception("Error generando video Fal.ai %s", i)
        self.mostrar_estado(f"✅ Clips de video IA (Fal.ai {modelo}) generados.", "green")

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

            while tiempo_act < self.duracion_total_audio - 0.05:
                video_elegido = self.pool_videos[idx_clip % len(self.pool_videos)]
                narracion_asociada = ""

                if pesos_escenas and idx_clip < len(pesos_escenas) and total_palabras > 0:
                    proporcion = pesos_escenas[idx_clip] / total_palabras
                    duracion_objetivo = max(2.2, min(6.0, self.duracion_total_audio * proporcion))
                    narracion_asociada = textos_escenas[idx_clip]
                else:
                    duracion_objetivo = max(2.5, min(4.5, self.duracion_total_audio / max(1, num_bloques)))

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

            body = {
                "snippet": {"title": titulo, "description": desc, "categoryId": "22"},
                "status": {"privacyStatus": estado_priv, "selfDeclaredMadeForKids": False},
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


if __name__ == "__main__":
    app = StudioApp()
    app.mainloop()
