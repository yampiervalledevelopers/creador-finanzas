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

import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
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
                {"role": "system", "content": "Director experto en JSON."},
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
        size = "1024x1792" if vertical else "1792x1024"
        res = self.client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
        )
        image_bytes = base64.b64decode(res.data[0].b64_json)
        with open(nombre_archivo, "wb") as f:
            f.write(image_bytes)
        return nombre_archivo


class ElevenLabsService:
    VOICE_ID = "pNInz6obpgDQGcFmaJgB"

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Falta la API key de ElevenLabs.")
        self.api_key = api_key

    def generar_voz(self, guion, ruta_salida):
        res = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.VOICE_ID}",
            json={"text": guion, "model_id": "eleven_multilingual_v2"},
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=120,
        )
        res.raise_for_status()
        with open(ruta_salida, "wb") as f:
            f.write(res.content)
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
            },
            headers={"Authorization": self.api_key},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("videos", [])

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
    """Lógica de recorte, conversión de imagen a clip, miniaturas y subtítulos."""

    def __init__(self, formato_actual):
        self.formato_actual = formato_actual

    @property
    def dimensiones(self):
        if self.formato_actual == "SHORT":
            return 1080, 1920
        return 1920, 1080

    def procesar_recorte_clip(self, ruta_clip, duracion):
        ancho, alto = self.dimensiones
        clip = VideoFileClip(ruta_clip).without_audio().subclip(0, duracion)
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

    def convertir_imagen_a_clip(self, ruta_imagen, ruta_video, duracion=4):
        ancho, alto = self.dimensiones
        clip = ImageClip(ruta_imagen).set_duration(duracion)
        ratio_obj = ancho / alto
        if (clip.w / clip.h) > ratio_obj:
            clip = clip.resize(height=alto)
        else:
            clip = clip.resize(width=ancho)
        clip = crop(
            clip,
            width=ancho,
            height=alto,
            x_center=clip.w / 2,
            y_center=clip.h / 2,
        )
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

    def crear_subtitulos(self, transcript, estilo):
        clips_texto = []
        if "Hormozi" in estilo:
            color, stroke_color, stroke_width = "yellow", "black", 3
            fontsize = 80 if self.formato_actual == "SHORT" else 60
        elif "Clásico" in estilo:
            color, stroke_color, stroke_width = "white", "black", 2
            fontsize = 70 if self.formato_actual == "SHORT" else 50
        else:
            color, stroke_color, stroke_width = "red", "white", 3
            fontsize = 90 if self.formato_actual == "SHORT" else 70

        for word_info in transcript.words:
            texto = word_info.word.upper().strip()
            if not texto:
                continue
            inicio, fin = word_info.start, word_info.end
            if fin - inicio <= 0:
                continue
            try:
                txt_clip = TextClip(
                    texto,
                    fontsize=fontsize,
                    color=color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    font="Arial-Bold",
                )
                txt_clip = (
                    txt_clip.set_position(("center", 0.75))
                    .set_start(inicio)
                    .set_end(fin)
                )
                clips_texto.append(txt_clip)
            except Exception:
                logging.exception("Error creando subtítulo para %s", texto)
                continue
        return clips_texto


# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
class StudioApp(ctk.CTk):
    ARCHIVO_VOZ = "voz_temp.mp3"
    ARCHIVO_KEYS = "config_keys.json"
    ARCHIVO_CACHE = "cache_proyecto.json"
    ARCHIVO_HISTORIAL = "historial_serie.txt"

    def __init__(self):
        super().__init__()
        self.title("🎬 Studio Automator Pro v13.0 - FAL.AI VIDEO")
        self.geometry("1300x850")

        self.keywords_actuales = []
        self.prompts_visuales = []
        self.pool_videos = []
        self.formato_actual = "SHORT"

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
            values=["gpt-4o (Alta Calidad / Largo)", "gpt-3.5-turbo (Rápido / Barato)"],
            width=300, fg_color="#E91E63",
        )
        self.menu_motor_ia.pack(padx=20, pady=5)

        # FUENTE VISUAL
        ctk.CTkLabel(
            frame_izq, text="🎨 Fuente de Visuales:",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#9C27B0",
        ).pack(anchor="w", padx=20, pady=(15, 0))
        self.menu_fuente_visual = ctk.CTkOptionMenu(
            frame_izq,
            values=[
                "Pexels (Clips reales)",
                "OpenAI Images (IA)",
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
    def guardar_keys(self):
        keys_data = {
            "openai": self.entrada_openai.get().strip(),
            "elevenlabs": self.entrada_eleven.get().strip(),
            "pexels": self.entrada_pexels.get().strip(),
            "stability": self.entrada_stability.get().strip(),
            "runway": self.entrada_runway.get().strip(),
            "fal": self.entrada_fal.get().strip(),
            "motor_ia": self.menu_motor_ia.get(),
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
            self.pool_videos = datos.get("videos", [])
            self.keywords_actuales = datos.get("keywords", [])
            self.prompts_visuales = datos.get("prompts_visuales", [])
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
            frame_btn_clips, text="🤖 Generar Visuales",
            command=self.hilo_paso3, fg_color="#9C27B0",
        )
        self.btn_auto_clips.pack(side="left", expand=True, padx=2)
        ctk.CTkButton(
            frame_btn_clips, text="💻 Cargar PC",
            command=self.cargar_desde_pc, fg_color="#FF9800",
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

            texto = f"[{item['inicio']:.1f}s - {item['fin']:.1f}s]\n🎥 {os.path.basename(item['archivo'])}"
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

(IMPORTANTE: Tu respuesta DEBE ser estrictamente un objeto JSON con 5 llaves:
- 'guion_locucion': (tu texto en ESPAÑOL aplicando la estructura)
- 'keywords_visuales': (lista de {num_keywords} conceptos cortos en INGLÉS para buscar en bancos de video)
- 'prompts_visuales': (lista de {num_keywords} prompts DETALLADOS en INGLÉS para generadores de imágenes/video IA, estilo cinematográfico, sin texto ni marcas de agua)
- 'titulo_seo': (Un título clickbait para este episodio)
- 'descripcion_seo': (Descripción corta con hashtags))."""

        self.after(0, lambda: self.caja_prompt.delete("0.0", "end"))
        self.after(0, lambda: self.caja_prompt.insert("0.0", prompt_base))
        self.mostrar_estado("✅ Mega-Prompt creado (Modo Serie evaluado).", "yellow")

    # ==========================================
    # PASO 1b: ENVIAR A OPENAI
    # ==========================================
    def ejecutar_enviar_guionista(self):
        prompt_final = self.caja_prompt.get("0.0", "end").strip()
        if not prompt_final:
            self.mostrar_estado("❌ Primero genera el prompt.", "red")
            return

        self.mostrar_estado("Enviando a OpenAI... pensando guion...", "orange")
        self.cambiar_estado_boton(self.btn_enviar_prompt, "disabled")
        try:
            service = OpenAIService(self.entrada_openai.get().strip())
            modelo = self.menu_motor_ia.get().split()[0]
            datos = service.generar_guion(modelo, prompt_final)

            self.keywords_actuales = datos.get("keywords_visuales", [])
            self.prompts_visuales = datos.get("prompts_visuales", [])
            guion_generado = datos.get("guion_locucion", "Hubo un error.")

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
            self.mostrar_estado("✅ Guion generado y guardado en la Memoria de Series.", "green")
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

        self.mostrar_estado("Grabando Voz con ElevenLabs...", "yellow")
        self.cambiar_estado_boton(self.btn_paso2, "disabled")
        try:
            service = ElevenLabsService(self.entrada_eleven.get().strip())
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
            self.cambiar_estado_boton(self.btn_auto_clips, "normal", "🤖 Generar Visuales")

    def generar_clips_pexels(self):
        self.mostrar_estado("Buscando en Pexels...", "yellow")
        service = PexelsService(self.entrada_pexels.get().strip())
        ori = "portrait" if self.es_vertical else "landscape"
        cantidad = 2 if self.es_vertical else 4

        for kw in set(self.keywords_actuales):
            try:
                videos = service.buscar_videos(kw, cantidad, ori)
            except Exception:
                logging.exception("Error buscando %s en Pexels", kw)
                continue
            for i, v in enumerate(videos):
                nombre = f"clip_{limpiar_nombre(kw)}_{i}.mp4"
                try:
                    PexelsService.descargar(v["video_files"][0]["link"], nombre)
                    if nombre not in self.pool_videos:
                        self.pool_videos.append(nombre)
                except Exception:
                    logging.exception("Error descargando clip de Pexels")
        self.mostrar_estado("✅ Clips de Pexels descargados.", "green")

    def generar_clips_imagenes_openai(self):
        self.mostrar_estado("Generando imágenes con IA (OpenAI)...", "yellow")
        service = OpenAIService(self.entrada_openai.get().strip())
        renderer = VideoRenderer(self.formato_actual)
        prompts = self.prompts_visuales or self.keywords_actuales

        for i, prompt in enumerate(prompts):
            prompt_img = (
                f"Cinematic realistic scene about: {prompt}. "
                f"High detail, dramatic lighting, professional camera, no text, no watermark."
            )
            ruta_img = f"ai_image_{i}.png"
            ruta_video = f"ai_clip_{i}.mp4"
            try:
                self.mostrar_estado(f"🎨 Imagen IA {i + 1}/{len(prompts)}...", "yellow")
                service.generar_imagen(prompt_img, ruta_img, vertical=self.es_vertical)
                renderer.convertir_imagen_a_clip(ruta_img, ruta_video, duracion=4)
                if ruta_video not in self.pool_videos:
                    self.pool_videos.append(ruta_video)
            except Exception:
                logging.exception("Error generando imagen IA %s", i)
        self.mostrar_estado("✅ Clips IA (imágenes) generados.", "green")

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
            ruta_img = f"ai_base_{i}.png"
            ruta_video = f"stability_clip_{i}.mp4"
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
            ruta_img = f"ai_base_runway_{i}.png"
            ruta_video = f"runway_clip_{i}.mp4"
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
            ruta_video = f"fal_{limpiar_nombre(modelo)}_{i}.mp4"
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
    # PASO 3b: STORYBOARD
    # ==========================================
    def ejecutar_generar_timeline(self):
        self.mostrar_estado("Calculando Línea de Tiempo...", "yellow")
        try:
            if not self.pool_videos:
                raise Exception("No hay clips.")
            if not os.path.exists(self.ARCHIVO_VOZ):
                raise Exception("Falta la Voz.")

            audio_clip = AudioFileClip(self.ARCHIVO_VOZ)
            self.duracion_total_audio = audio_clip.duration
            audio_clip.close()

            self.timeline_data = []
            mazo_videos = self.pool_videos.copy()
            random.shuffle(mazo_videos)

            tiempo_act = 0
            orden = 1
            while tiempo_act < self.duracion_total_audio:
                if not mazo_videos:
                    mazo_videos = self.pool_videos.copy()
                    random.shuffle(mazo_videos)
                video_elegido = mazo_videos.pop(0)
                corte = min(4.0, self.duracion_total_audio - tiempo_act)
                clip_b = VideoFileClip(video_elegido)
                duracion_real = min(corte, clip_b.duration)
                clip_b.close()
                self.timeline_data.append({
                    "orden": orden,
                    "archivo": video_elegido,
                    "inicio": tiempo_act,
                    "fin": tiempo_act + duracion_real,
                    "duracion": duracion_real,
                })
                tiempo_act += duracion_real
                orden += 1

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
        video_final = None
        try:
            clips_finales = [
                renderer.procesar_recorte_clip(i["archivo"], i["duracion"])
                for i in self.timeline_data
            ]
            audio_clip = AudioFileClip(self.ARCHIVO_VOZ)
            video_final = concatenate_videoclips(clips_finales, method="compose").set_audio(audio_clip)

            if self.switch_subs.get() == 1:
                service = OpenAIService(self.entrada_openai.get().strip())
                self.mostrar_estado("🎧 Whisper IA escuchando...", "orange")
                transcript = service.transcribir(self.ARCHIVO_VOZ)
                clips_de_texto = renderer.crear_subtitulos(transcript, self.menu_estilos_subs.get())
                if clips_de_texto:
                    video_final = CompositeVideoClip([video_final] + clips_de_texto)

            ruta_salida = f"FINAL_{self.formato_actual}.mp4"
            video_final.write_videofile(
                ruta_salida, fps=24, codec="libx264", audio_codec="aac", logger=None
            )
            self.mostrar_estado("🎉 ¡MP4 LISTO!", "#00FF00")

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
