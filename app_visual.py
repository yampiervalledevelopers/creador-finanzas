import customtkinter as ctk
import threading
import json
import os
import random
import requests
import shutil
from tkinter import filedialog
from openai import OpenAI

# 1. IMAGEMAGICK (El Pintor de Subtítulos)
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from moviepy.video.fx.all import crop

# Importaciones Oficiales para YouTube
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 🎨 CONFIGURACIÓN VISUAL
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class StudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎬 Studio Automator Pro v11.0 - STORYBOARD & SERIES")
        self.geometry("1300x850")
        
        self.keywords_actuales = []
        self.pool_videos = []
        self.formato_actual = "SHORT"
        
        self.timeline_data = [] 
        self.duracion_total_audio = 0
        self.ruta_video_publicar = ""
        self.imagenes_timeline = [] # Memoria RAM para las miniaturas del Storyboard

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self.crear_panel_izquierdo()
        self.crear_panel_derecho()
        
        self.cargar_keys()
        self.cargar_cache()

    # ==========================================
    # 🛡️ FUNCIONES DE SEGURIDAD
    # ==========================================
    def mostrar_estado(self, mensaje, color="white"):
        self.after(0, lambda: self.lbl_estado.configure(text=mensaje, text_color=color))

    def cambiar_estado_boton(self, boton, estado, texto=None):
        if texto: self.after(0, lambda: boton.configure(state=estado, text=texto))
        else: self.after(0, lambda: boton.configure(state=estado))

    # ==========================================
    # 🧱 PANEL IZQUIERDO
    # ==========================================
    def crear_panel_izquierdo(self):
        frame_izq = ctk.CTkScrollableFrame(self)
        frame_izq.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(frame_izq, text="⚙️ CONFIGURACIÓN", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 5))

        self.entrada_tema = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Tema del Video...")
        self.entrada_tema.pack(padx=20, pady=5)

        self.menu_formato = ctk.CTkOptionMenu(frame_izq, values=["SHORT (Vertical)", "LARGO (Horizontal)"], width=300)
        self.menu_formato.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🧠 Motor de Inteligencia Artificial:").pack(anchor="w", padx=20, pady=(10, 0))
        self.menu_motor_ia = ctk.CTkOptionMenu(frame_izq, values=["gpt-4o (Alta Calidad / Largo)", "gpt-3.5-turbo (Rápido / Barato)"], width=300, fg_color="#E91E63")
        self.menu_motor_ia.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="🔑 API Keys:").pack(anchor="w", padx=20, pady=(15, 0))
        self.entrada_openai = ctk.CTkEntry(frame_izq, width=300, placeholder_text="OpenAI sk-...", show="*")
        self.entrada_openai.pack(padx=20, pady=2)
        self.entrada_eleven = ctk.CTkEntry(frame_izq, width=300, placeholder_text="ElevenLabs", show="*")
        self.entrada_eleven.pack(padx=20, pady=2)
        self.entrada_pexels = ctk.CTkEntry(frame_izq, width=300, placeholder_text="Pexels", show="*")
        self.entrada_pexels.pack(padx=20, pady=2)

        self.btn_guardar = ctk.CTkButton(frame_izq, text="💾 Guardar Ajustes", command=self.guardar_keys, fg_color="#4CAF50", height=30)
        self.btn_guardar.pack(padx=20, pady=10)

        ctk.CTkLabel(frame_izq, text="🔤 Subtítulos (Whisper IA):", font=ctk.CTkFont(size=16, weight="bold"), text_color="#E91E63").pack(anchor="w", padx=20, pady=(15, 5))
        self.switch_subs = ctk.CTkSwitch(frame_izq, text="Quemar Subtítulos Automáticos", progress_color="#E91E63")
        self.switch_subs.pack(anchor="w", padx=20, pady=5)
        self.switch_subs.select() 
        
        self.menu_estilos_subs = ctk.CTkOptionMenu(frame_izq, values=["Estilo Hormozi (Amarillo/Negro)", "Estilo Clásico (Blanco/Negro)", "Estilo Alerta (Rojo/Blanco)"], width=300, fg_color="#333333")
        self.menu_estilos_subs.pack(padx=20, pady=5)

        ctk.CTkLabel(frame_izq, text="📝 SEO (Para Guion y Publicación):", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.entrada_titulo = ctk.CTkEntry(frame_izq, width=300, placeholder_text="El título aparecerá aquí...")
        self.entrada_titulo.pack(padx=20, pady=5)
        
        self.caja_desc = ctk.CTkTextbox(frame_izq, width=300, height=80, wrap="word")
        self.caja_desc.pack(padx=20, pady=5)

        self.lbl_estado = ctk.CTkLabel(frame_izq, text="Estado: Listo.", text_color="green", wraplength=280)
        self.lbl_estado.pack(side="bottom", pady=20)

    # ==========================================
    # 💾 FUNCIONES DE MEMORIA
    # ==========================================
    def guardar_keys(self):
        keys_data = {"openai": self.entrada_openai.get(), "elevenlabs": self.entrada_eleven.get(), "pexels": self.entrada_pexels.get(), "motor_ia": self.menu_motor_ia.get()}
        try:
            with open("config_keys.json", "w") as f: json.dump(keys_data, f)
            self.mostrar_estado("✅ Ajustes guardados.", "#00FF00")
        except Exception as e: self.mostrar_estado(f"❌ Error al guardar: {e}", "red")

    def cargar_keys(self):
        if os.path.exists("config_keys.json"):
            try:
                with open("config_keys.json", "r") as f:
                    k = json.load(f)
                    if k.get("openai"): self.entrada_openai.insert(0, k["openai"])
                    if k.get("elevenlabs"): self.entrada_eleven.insert(0, k["elevenlabs"])
                    if k.get("pexels"): self.entrada_pexels.insert(0, k["pexels"])
                    if k.get("motor_ia"): self.menu_motor_ia.set(k["motor_ia"])
            except: pass

    def guardar_cache(self):
        datos = {"prompt": self.caja_prompt.get("0.0", "end").strip(), "guion": self.caja_guion.get("0.0", "end").strip(), "titulo": self.entrada_titulo.get(), "desc": self.caja_desc.get("0.0", "end").strip(), "videos": self.pool_videos, "keywords": self.keywords_actuales}
        try:
            with open("cache_proyecto.json", "w") as f: json.dump(datos, f)
        except: pass

    def cargar_cache(self):
        if os.path.exists("cache_proyecto.json"):
            try:
                with open("cache_proyecto.json", "r") as f:
                    datos = json.load(f)
                    if datos.get("prompt"): self.caja_prompt.insert("0.0", datos["prompt"])
                    if datos.get("guion"): self.caja_guion.insert("0.0", datos["guion"])
                    if datos.get("titulo"): self.entrada_titulo.insert(0, datos["titulo"])
                    if datos.get("desc"): self.caja_desc.insert("0.0", datos["desc"])
                    self.pool_videos = datos.get("videos", [])
                    self.keywords_actuales = datos.get("keywords", [])
                    self.actualizar_lista_clips_ui()
            except: pass

    # ==========================================
    # 🧱 PANEL DERECHO (Pestañas de Edición)
    # ==========================================
    def crear_panel_derecho(self):
        frame_der = ctk.CTkFrame(self)
        frame_der.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        ctk.CTkLabel(frame_der, text="🎛️ SALA DE PRODUCCIÓN", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 5))

        self.pestanas = ctk.CTkTabview(frame_der, height=450)
        self.pestanas.pack(fill="both", padx=20, pady=(5, 15), expand=True)

        self.tab_guion = self.pestanas.add("📝 1. Guion y Prompt")
        self.tab_clips = self.pestanas.add("🎬 2. Gestor Clips")
        self.tab_timeline = self.pestanas.add("🎞️ 3. Storyboard (Timeline)") 
        self.tab_publicar = self.pestanas.add("🚀 4. Publicador") 

        # --- PESTAÑA 1: PROMPT Y GUION ---
        frame_titulo_guion = ctk.CTkFrame(self.tab_guion, fg_color="transparent")
        frame_titulo_guion.pack(fill="x", padx=5, pady=(5,0))
        ctk.CTkLabel(frame_titulo_guion, text="🧠 Prompt Maestro:", font=ctk.CTkFont(weight="bold", size=15)).pack(side="left")
        
        # 🔥 NUEVO BOTÓN: MODO SERIE 🔥
        self.switch_serie = ctk.CTkSwitch(frame_titulo_guion, text="🔗 MODO SERIE (Continuar historia anterior)", progress_color="#9C27B0")
        self.switch_serie.pack(side="right")

        self.caja_prompt = ctk.CTkTextbox(self.tab_guion, height=180, font=ctk.CTkFont(size=15), fg_color="#1e1e1e", border_color="#4CAF50", border_width=1, wrap="word")
        self.caja_prompt.pack(fill="x", padx=5, pady=5)
        self.btn_enviar_prompt = ctk.CTkButton(self.tab_guion, text="🤖 Enviar al Guionista (OpenAI)", command=self.hilo_enviar_guionista, fg_color="#E91E63", height=35)
        self.btn_enviar_prompt.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(self.tab_guion, text="📝 Guion de Locución:", font=ctk.CTkFont(weight="bold", size=15)).pack(anchor="w", padx=5, pady=(10,0))
        self.caja_guion = ctk.CTkTextbox(self.tab_guion, height=150, font=ctk.CTkFont(size=15), fg_color="#2b2b2b", wrap="word")
        self.caja_guion.pack(fill="both", expand=True, padx=5, pady=5)

        # --- PESTAÑA 2: GESTOR DE CLIPS ---
        self.lista_clips_ui = ctk.CTkScrollableFrame(self.tab_clips, fg_color="#1a1a1a")
        self.lista_clips_ui.pack(fill="both", expand=True, padx=5, pady=5)
        frame_btn_clips = ctk.CTkFrame(self.tab_clips, fg_color="transparent")
        frame_btn_clips.pack(fill="x", padx=5, pady=5)
        self.btn_auto_clips = ctk.CTkButton(frame_btn_clips, text="🤖 Auto Pexels", command=self.hilo_paso3, fg_color="#9C27B0")
        self.btn_auto_clips.pack(side="left", expand=True, padx=2)
        ctk.CTkButton(frame_btn_clips, text="💻 Cargar PC", command=self.cargar_desde_pc, fg_color="#FF9800").pack(side="right", expand=True, padx=2)

        # --- PESTAÑA 3: TIMELINE (STORYBOARD) ---
        self.timeline_ui = ctk.CTkScrollableFrame(self.tab_timeline, fg_color="#1a1a1a")
        self.timeline_ui.pack(fill="both", expand=True, padx=5, pady=5)
        frame_btn_exportar = ctk.CTkFrame(self.tab_timeline, fg_color="transparent")
        frame_btn_exportar.pack(fill="x", padx=5, pady=5)
        self.btn_exp_mp4 = ctk.CTkButton(frame_btn_exportar, text="⬇️ Exportar MP4 Final", command=self.hilo_exportar_mp4, fg_color="#F44336", state="disabled")
        self.btn_exp_mp4.pack(side="left", expand=True, padx=5)
        self.btn_exp_capcut = ctk.CTkButton(frame_btn_exportar, text="📁 Exportar a CapCut", command=self.hilo_exportar_capcut, fg_color="#607D8B", state="disabled")
        self.btn_exp_capcut.pack(side="right", expand=True, padx=5)

        # --- PESTAÑA 4: PUBLICADOR YOUTUBE ---
        self.lbl_video_pub = ctk.CTkLabel(self.tab_publicar, text="Ningún video seleccionado.", text_color="yellow", font=ctk.CTkFont(weight="bold"))
        self.lbl_video_pub.pack(pady=(10, 5))
        
        frame_btn_pub = ctk.CTkFrame(self.tab_publicar, fg_color="transparent")
        frame_btn_pub.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(frame_btn_pub, text="🎬 Usar Video del Proyecto", command=self.cargar_video_proyecto, fg_color="#2196F3").pack(side="left", expand=True, padx=2)
        ctk.CTkButton(frame_btn_pub, text="📂 Cargar Video Externo (PC)", command=self.cargar_video_externo, fg_color="#FF9800").pack(side="right", expand=True, padx=2)

        ctk.CTkLabel(self.tab_publicar, text="Título del Video:").pack(anchor="w", padx=10, pady=(15, 0))
        self.entrada_titulo_pub = ctk.CTkEntry(self.tab_publicar, font=ctk.CTkFont(size=14))
        self.entrada_titulo_pub.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.tab_publicar, text="Descripción y Hashtags:").pack(anchor="w", padx=10, pady=(5, 0))
        self.caja_desc_pub = ctk.CTkTextbox(self.tab_publicar, height=100, wrap="word", font=ctk.CTkFont(size=13))
        self.caja_desc_pub.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.tab_publicar, text="Privacidad:").pack(anchor="w", padx=10, pady=(5, 0))
        self.menu_privacidad = ctk.CTkOptionMenu(self.tab_publicar, values=["Privado", "Oculto", "Público"], fg_color="#004D40")
        self.menu_privacidad.pack(fill="x", padx=10, pady=5)

        self.btn_publicar_yt = ctk.CTkButton(self.tab_publicar, text="🚀 PUBLICAR EN YOUTUBE", command=self.hilo_publicar_youtube, fg_color="#D32F2F", height=40, font=ctk.CTkFont(weight="bold", size=15))
        self.btn_publicar_yt.pack(fill="x", padx=10, pady=15)

        # --- BOTONES DE FLUJO (INFERIORES) ---
        frame_flujo = ctk.CTkFrame(frame_der, fg_color="transparent")
        frame_flujo.pack(fill="x", padx=20, pady=5)
        self.btn_paso1 = ctk.CTkButton(frame_flujo, text="1. Generar Prompt", command=self.hilo_crear_prompt, fg_color="#4CAF50")
        self.btn_paso1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.btn_paso2 = ctk.CTkButton(frame_flujo, text="2. Grabar Voz", command=self.hilo_paso2, fg_color="#2196F3")
        self.btn_paso2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.btn_paso4 = ctk.CTkButton(frame_flujo, text="3. Crear Storyboard", command=self.hilo_generar_timeline, fg_color="#607D8B")
        self.btn_paso4.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        frame_flujo.columnconfigure((0,1,2), weight=1)

    # ==========================================
    # 🎬 FUNCIONES DE UI Y STORYBOARD
    # ==========================================
    def actualizar_lista_clips_ui(self):
        for w in self.lista_clips_ui.winfo_children(): w.destroy()
        for ruta in self.pool_videos:
            fila = ctk.CTkFrame(self.lista_clips_ui, fg_color="#2b2b2b"); fila.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(fila, text=f"🎥 {os.path.basename(ruta)}").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(fila, text="❌", width=40, fg_color="#D32F2F", command=lambda r=ruta: self.eliminar_clip(r)).pack(side="right", padx=5)

    def eliminar_clip(self, ruta):
        if ruta in self.pool_videos: self.pool_videos.remove(ruta)
        self.actualizar_lista_clips_ui(); self.guardar_cache() 

    def cargar_desde_pc(self):
        archivos = filedialog.askopenfilenames(filetypes=[("Videos", "*.mp4 *.mov")])
        if archivos:
            for arch in archivos:
                if arch not in self.pool_videos: self.pool_videos.append(arch)
            self.actualizar_lista_clips_ui(); self.guardar_cache() 

    # 🔥 GENERADOR DE MINIATURAS PARA EL STORYBOARD 🔥
    def obtener_miniatura(self, ruta_video):
        try:
            clip = VideoFileClip(ruta_video)
            # Tomamos una foto en el segundo 0.5 para evitar pantallas en negro
            frame = clip.get_frame(min(0.5, clip.duration / 2)) 
            clip.close()
            imagen_pil = PIL.Image.fromarray(frame)
            return ctk.CTkImage(light_image=imagen_pil, dark_image=imagen_pil, size=(90, 50))
        except:
            return None

    def dibujar_timeline_ui(self):
        self.mostrar_estado("Generando previsualización del Storyboard...", "orange")
        for w in self.timeline_ui.winfo_children(): w.destroy()
        self.imagenes_timeline = [] # Limpiar memoria RAM de fotos viejas

        pista_audio = ctk.CTkFrame(self.timeline_ui, fg_color="#004D40", corner_radius=0)
        pista_audio.pack(fill="x", pady=5)
        ctk.CTkLabel(pista_audio, text=f"🎵 PISTA DE VOZ (Duración: {self.duracion_total_audio:.1f}s)", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        ctk.CTkLabel(self.timeline_ui, text="🎬 STORYBOARD (Puedes Reordenar o Cambiar Clips)", anchor="w").pack(fill="x", pady=(10,0))
        
        # 🔥 CREACIÓN VISUAL DE LA LÍNEA DE TIEMPO INTERACTIVA 🔥
        for i, item in enumerate(self.timeline_data):
            bloque = ctk.CTkFrame(self.timeline_ui, fg_color="#1565C0", border_color="black", border_width=1)
            bloque.pack(fill="x", pady=2, padx=10)
            
            # Miniatura
            img = self.obtener_miniatura(item['archivo'])
            if img:
                self.imagenes_timeline.append(img)
                ctk.CTkLabel(bloque, image=img, text="").pack(side="left", padx=5, pady=5)

            # Texto
            texto = f"[{item['inicio']:.1f}s - {item['fin']:.1f}s]\n🎥 {os.path.basename(item['archivo'])}"
            ctk.CTkLabel(bloque, text=texto, justify="left").pack(side="left", padx=10)

            # Botones de Edición (NLE)
            frame_controles = ctk.CTkFrame(bloque, fg_color="transparent")
            frame_controles.pack(side="right", padx=10)
            
            btn_up = ctk.CTkButton(frame_controles, text="⬆️", width=30, fg_color="#555555", command=lambda idx=i: self.mover_clip_arriba(idx))
            btn_up.pack(side="left", padx=2)
            if i == 0: btn_up.configure(state="disabled") # El primero no puede subir más

            btn_down = ctk.CTkButton(frame_controles, text="⬇️", width=30, fg_color="#555555", command=lambda idx=i: self.mover_clip_abajo(idx))
            btn_down.pack(side="left", padx=2)
            if i == len(self.timeline_data) - 1: btn_down.configure(state="disabled") # El último no puede bajar más

            ctk.CTkButton(frame_controles, text="🔄 Cambiar", width=60, fg_color="#E65100", command=lambda idx=i: self.reemplazar_clip(idx)).pack(side="left", padx=5)
            
        self.mostrar_estado("✅ Storyboard interactivo listo.", "green")

    # 🔥 FUNCIONES INTERACTIVAS DEL STORYBOARD 🔥
    def mover_clip_arriba(self, idx):
        if idx > 0:
            # Solo intercambiamos el archivo visual, respetando los cortes exactos de audio
            self.timeline_data[idx]['archivo'], self.timeline_data[idx-1]['archivo'] = self.timeline_data[idx-1]['archivo'], self.timeline_data[idx]['archivo']
            self.dibujar_timeline_ui()

    def mover_clip_abajo(self, idx):
        if idx < len(self.timeline_data) - 1:
            self.timeline_data[idx]['archivo'], self.timeline_data[idx+1]['archivo'] = self.timeline_data[idx+1]['archivo'], self.timeline_data[idx]['archivo']
            self.dibujar_timeline_ui()

    def reemplazar_clip(self, idx):
        if len(self.pool_videos) > 1:
            opciones = [v for v in self.pool_videos if v != self.timeline_data[idx]['archivo']]
            if opciones:
                self.timeline_data[idx]['archivo'] = random.choice(opciones)
                self.dibujar_timeline_ui()

    # ==========================================
    # ⚙️ HILOS DE PRODUCCIÓN Y PROMPTS
    # ==========================================
    def hilo_crear_prompt(self): threading.Thread(target=self.ejecutar_crear_prompt).start()
    def hilo_enviar_guionista(self): threading.Thread(target=self.ejecutar_enviar_guionista).start()
    def hilo_paso2(self): threading.Thread(target=self.ejecutar_paso2).start()
    def hilo_paso3(self): threading.Thread(target=self.ejecutar_paso3).start()
    def hilo_generar_timeline(self): threading.Thread(target=self.ejecutar_generar_timeline).start()
    def hilo_exportar_mp4(self): threading.Thread(target=self.ejecutar_exportar_mp4).start()
    def hilo_exportar_capcut(self): threading.Thread(target=self.ejecutar_exportar_capcut).start()
    def hilo_publicar_youtube(self): threading.Thread(target=self.ejecutar_publicar_youtube).start()

    def ejecutar_crear_prompt(self):
        self.after(0, lambda: self.pestanas.set("📝 1. Guion y Prompt"))
        tema = self.entrada_tema.get()
        self.formato_actual = "SHORT" if "SHORT" in self.menu_formato.get() else "LARGO"
        
        # ESTRUCTURAS BASE
        if self.formato_actual == "SHORT":
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

        # 🔥 LA MAGIA DEL MODO SERIE 🔥
        inyeccion_serie = ""
        if self.switch_serie.get() == 1 and os.path.exists("historial_serie.txt"):
            with open("historial_serie.txt", "r", encoding="utf-8") as f:
                guion_anterior = f.read()
            inyeccion_serie = f"\n\n[🚨 ALERTA: MODO SERIE ACTIVADO]: El usuario quiere que escribas la SIGUIENTE PARTE de la historia. Aquí tienes el guion del episodio anterior para que mantengas la continuidad, el tono y los personajes:\n\n--- GUION ANTERIOR ---\n{guion_anterior}\n--- FIN GUION ANTERIOR ---\n\nTu tarea: Inicia este nuevo guion resolviendo el suspenso del episodio anterior y crea un misterio completamente nuevo para este episodio."

        prompt_base = f"""Actúa como un guionista experto en retención para YouTube. Tu tema es: '{tema}'.

REGLAS DE ORO:
1. IDIOMA: TODO DEBE ESTAR EN ESPAÑOL (excepto las keywords visuales).
{reglas_formato}{inyeccion_serie}

(IMPORTANTE: Tu respuesta DEBE ser estrictamente un objeto JSON con 4 llaves: 
- 'guion_locucion': (tu texto en ESPAÑOL aplicando la estructura)
- 'keywords_visuales': (lista de {num_keywords} conceptos en INGLÉS)
- 'titulo_seo': (Un título clickbait para este episodio)
- 'descripcion_seo': (Descripción corta con hashtags))."""
        
        self.after(0, lambda: self.caja_prompt.delete("0.0", "end"))
        self.after(0, lambda: self.caja_prompt.insert("0.0", prompt_base))
        self.mostrar_estado("✅ Mega-Prompt creado (Modo Serie evaluado).", "yellow")

    def ejecutar_enviar_guionista(self):
        self.mostrar_estado("Enviando a OpenAI... pensando guion...", "orange")
        self.cambiar_estado_boton(self.btn_enviar_prompt, "disabled")
        try:
            prompt_final = self.caja_prompt.get("0.0", "end").strip()
            client = OpenAI(api_key=self.entrada_openai.get())
            modelo_seleccionado = self.menu_motor_ia.get().split()[0] 
            
            res = client.chat.completions.create(model=modelo_seleccionado, response_format={"type": "json_object"}, messages=[{"role": "system", "content": "Director experto en JSON."}, {"role": "user", "content": prompt_final}])
            datos = json.loads(res.choices[0].message.content)
            
            self.keywords_actuales = datos.get("keywords_visuales", [])
            guion_generado = datos.get("guion_locucion", "Hubo un error.")
            
            self.after(0, lambda: self.caja_guion.delete("0.0", "end"))
            self.after(0, lambda: self.caja_guion.insert("0.0", guion_generado))
            
            if "titulo_seo" in datos:
                self.after(0, lambda: self.entrada_titulo.delete(0, "end"))
                self.after(0, lambda: self.entrada_titulo.insert(0, datos["titulo_seo"]))
            if "descripcion_seo" in datos:
                self.after(0, lambda: self.caja_desc.delete("0.0", "end"))
                self.after(0, lambda: self.caja_desc.insert("0.0", datos["descripcion_seo"]))
            
            # 🔥 GUARDAR EN LA MEMORIA A LARGO PLAZO PARA FUTURAS SERIES 🔥
            with open("historial_serie.txt", "w", encoding="utf-8") as f:
                f.write(guion_generado)

            self.guardar_cache() 
            self.mostrar_estado(f"✅ Guion generado y guardado en la Memoria de Series.", "green")
        except Exception as e: self.mostrar_estado(f"❌ Error OpenAI: {e}", "red")
        finally: self.cambiar_estado_boton(self.btn_enviar_prompt, "normal")

    def ejecutar_paso2(self):
        self.mostrar_estado("Grabando Voz con ElevenLabs...", "yellow")
        try:
            guion = self.caja_guion.get("0.0", "end").strip()
            res = requests.post("https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB", json={"text": guion, "model_id": "eleven_multilingual_v2"}, headers={"xi-api-key": self.entrada_eleven.get()})
            if res.status_code == 200:
                with open("voz_temp.mp3", "wb") as f: f.write(res.content)
                self.mostrar_estado("✅ Voz guardada con éxito.", "green")
            else:
                self.mostrar_estado(f"❌ Error ElevenLabs: Verifica tu saldo/API. Detalle: {res.text[:50]}...", "red")
        except Exception as e: self.mostrar_estado(f"❌ Error Voz: {e}", "red")

    def ejecutar_paso3(self):
        self.mostrar_estado("Buscando Pexels...", "yellow")
        self.cambiar_estado_boton(self.btn_auto_clips, "disabled", "Descargando...")
        try:
            ori = "portrait" if self.formato_actual == "SHORT" else "landscape"
            cantidad_descarga = 2 if self.formato_actual == "SHORT" else 4
            for kw in set(self.keywords_actuales):
                resp = requests.get(f"https://api.pexels.com/videos/search?query={kw}&per_page={cantidad_descarga}&orientation={ori}", headers={"Authorization": self.entrada_pexels.get()}).json()
                for i, v in enumerate(resp.get('videos', [])):
                    nombre = f"clip_{kw.replace(' ', '_')}_{i}.mp4"
                    with open(nombre, 'wb') as f: f.write(requests.get(v['video_files'][0]['link']).content)
                    if nombre not in self.pool_videos: self.pool_videos.append(nombre)
            self.after(0, self.actualizar_lista_clips_ui)
            self.after(0, lambda: self.pestanas.set("🎬 2. Gestor Clips"))
            self.guardar_cache() 
            self.mostrar_estado("✅ Clips descargados.", "green")
        except Exception as e: self.mostrar_estado(f"❌ Error Pexels: {e}", "red")
        finally: self.cambiar_estado_boton(self.btn_auto_clips, "normal", "🤖 Auto Pexels")

    def ejecutar_generar_timeline(self):
        self.mostrar_estado("Calculando Línea de Tiempo...", "yellow")
        try:
            if not self.pool_videos: raise Exception("No hay clips.")
            if not os.path.exists("voz_temp.mp3"): raise Exception("Falta la Voz.")
            
            audio_clip = AudioFileClip("voz_temp.mp3")
            self.duracion_total_audio = audio_clip.duration
            self.timeline_data = []
            mazo_videos = self.pool_videos.copy(); random.shuffle(mazo_videos)
            
            tiempo_act = 0; orden = 1
            while tiempo_act < self.duracion_total_audio:
                if not mazo_videos: mazo_videos = self.pool_videos.copy(); random.shuffle(mazo_videos)
                video_elegido = mazo_videos.pop(0)
                corte = min(4.0, self.duracion_total_audio - tiempo_act)
                clip_b = VideoFileClip(video_elegido)
                duracion_real = min(corte, clip_b.duration)
                self.timeline_data.append({"orden": orden, "archivo": video_elegido, "inicio": tiempo_act, "fin": tiempo_act + duracion_real, "duracion": duracion_real})
                tiempo_act += duracion_real; orden += 1
                clip_b.close()
                
            self.after(0, self.dibujar_timeline_ui)
            self.after(0, lambda: self.pestanas.set("🎞️ 3. Storyboard (Timeline)"))
            self.cambiar_estado_boton(self.btn_exp_mp4, "normal")
            self.cambiar_estado_boton(self.btn_exp_capcut, "normal")
        except Exception as e: self.mostrar_estado(f"❌ Error Timeline: {e}", "red")

    def procesar_recorte_clip(self, ruta_clip, duracion):
        ancho = 1080 if self.formato_actual == "SHORT" else 1920
        alto = 1920 if self.formato_actual == "SHORT" else 1080
        clip = VideoFileClip(ruta_clip).without_audio().subclip(0, duracion)
        ratio_obj = ancho / alto
        clip = clip.resize(height=alto) if (clip.w / clip.h) > ratio_obj else clip.resize(width=ancho)
        return crop(clip, width=ancho, height=alto, x_center=clip.w/2, y_center=clip.h/2)

    def motor_crear_subtitulos(self):
        self.mostrar_estado("🎧 Whisper IA escuchando...", "orange")
        client = OpenAI(api_key=self.entrada_openai.get())
        with open("voz_temp.mp3", "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="verbose_json", timestamp_granularities=["word"])
            
        clips_texto = []
        estilo = self.menu_estilos_subs.get()
        if "Hormozi" in estilo: color = 'yellow'; stroke_color = 'black'; stroke_width = 3; fontsize = 80 if self.formato_actual == "SHORT" else 60
        elif "Clásico" in estilo: color = 'white'; stroke_color = 'black'; stroke_width = 2; fontsize = 70 if self.formato_actual == "SHORT" else 50
        else: color = 'red'; stroke_color = 'white'; stroke_width = 3; fontsize = 90 if self.formato_actual == "SHORT" else 70

        for word_info in transcript.words:
            texto = word_info.word.upper().strip() 
            if not texto: continue 
            inicio = word_info.start; fin = word_info.end
            if fin - inicio <= 0: continue 
            try:
                txt_clip = TextClip(texto, fontsize=fontsize, color=color, stroke_color=stroke_color, stroke_width=stroke_width, font="Arial-Bold")
                txt_clip = txt_clip.set_position(('center', 0.75)).set_start(inicio).set_end(fin)
                clips_texto.append(txt_clip)
            except: continue 
        return clips_texto

    def ejecutar_exportar_mp4(self):
        self.mostrar_estado("Renderizando MP4 Final...", "yellow")
        self.cambiar_estado_boton(self.btn_exp_mp4, "disabled")
        try:
            clips_finales = [self.procesar_recorte_clip(i['archivo'], i['duracion']) for i in self.timeline_data]
            video_final = concatenate_videoclips(clips_finales, method="compose").set_audio(AudioFileClip("voz_temp.mp3"))
            
            if self.switch_subs.get() == 1:
                clips_de_texto = self.motor_crear_subtitulos()
                if clips_de_texto:
                    video_final = CompositeVideoClip([video_final] + clips_de_texto)
            
            ruta_salida = f"FINAL_{self.formato_actual}.mp4"
            video_final.write_videofile(ruta_salida, fps=24, codec="libx264", audio_codec="aac", logger=None)
            self.mostrar_estado("🎉 ¡MP4 LISTO!", "#00FF00")
            
            self.cargar_video_proyecto() 
            self.after(0, lambda: self.pestanas.set("🚀 4. Publicador"))
            
        except Exception as e: self.mostrar_estado(f"❌ Error: {e}", "red")
        finally: self.cambiar_estado_boton(self.btn_exp_mp4, "normal")

    def ejecutar_exportar_capcut(self):
        self.mostrar_estado("Preparando Carpeta...", "yellow")
        self.cambiar_estado_boton(self.btn_exp_capcut, "disabled")
        try:
            carpeta = f"PROYECTO_CAPCUT_{self.formato_actual}"
            os.makedirs(carpeta, exist_ok=True)
            shutil.copy("voz_temp.mp3", os.path.join(carpeta, "00_PISTA_AUDIO.mp3"))
            for i, item in enumerate(self.timeline_data):
                clip_procesado = self.procesar_recorte_clip(item['archivo'], item['duracion'])
                clip_procesado.write_videofile(os.path.join(carpeta, f"CLIP_{item['orden']:02d}.mp4"), fps=24, codec="libx264", logger=None)
                clip_procesado.close()
            self.mostrar_estado("📂 ¡CARPETA LISTA!", "#00FF00")
        except Exception as e: self.mostrar_estado(f"❌ Error Carpeta: {e}", "red")
        finally: self.cambiar_estado_boton(self.btn_exp_capcut, "normal")

    # ==========================================
    # 🚀 FUNCIONES DEL PUBLICADOR YOUTUBE 
    # ==========================================
    def cargar_video_proyecto(self):
        self.ruta_video_publicar = f"FINAL_{self.formato_actual}.mp4"
        if os.path.exists(self.ruta_video_publicar):
            self.after(0, lambda: self.lbl_video_pub.configure(text=f"✅ Seleccionado: {self.ruta_video_publicar}", text_color="#00FF00"))
            self.after(0, lambda: self.entrada_titulo_pub.delete(0, "end"))
            self.after(0, lambda: self.entrada_titulo_pub.insert(0, self.entrada_titulo.get()))
            self.after(0, lambda: self.caja_desc_pub.delete("0.0", "end"))
            self.after(0, lambda: self.caja_desc_pub.insert("0.0", self.caja_desc.get("0.0", "end").strip()))
        else:
            self.after(0, lambda: self.lbl_video_pub.configure(text="❌ Aún no has renderizado el video final.", text_color="red"))

    def cargar_video_externo(self):
        archivo = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.mov *.avi")])
        if archivo:
            self.ruta_video_publicar = archivo
            self.after(0, lambda: self.lbl_video_pub.configure(text=f"✅ Seleccionado: {os.path.basename(archivo)}", text_color="#00FF00"))
            self.after(0, lambda: self.entrada_titulo_pub.delete(0, "end"))
            self.after(0, lambda: self.caja_desc_pub.delete("0.0", "end"))

    def ejecutar_publicar_youtube(self):
        self.mostrar_estado("Conectando con YouTube... ¡Revisa tu navegador web!", "orange")
        self.cambiar_estado_boton(self.btn_publicar_yt, "disabled")
        try:
            titulo = self.entrada_titulo_pub.get()
            desc = self.caja_desc_pub.get("0.0", "end").strip()
            
            if not os.path.exists(self.ruta_video_publicar): raise Exception("El video seleccionado no existe.")
            if not os.path.exists("client_secret.json"): raise Exception("Falta el archivo 'client_secret.json'.")

            SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
            creds = None
            if os.path.exists('token.json'): creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token: token.write(creds.to_json())

            youtube = build('youtube', 'v3', credentials=creds)
            estado_priv = {"Privado": "private", "Oculto": "unlisted", "Público": "public"}[self.menu_privacidad.get()]

            body = {'snippet': {'title': titulo, 'description': desc, 'categoryId': '22'}, 'status': {'privacyStatus': estado_priv, 'selfDeclaredMadeForKids': False}}
            self.mostrar_estado("Subiendo video a YouTube... ¡Paciencia, no cierres la app!", "yellow")
            
            media = MediaFileUpload(self.ruta_video_publicar, chunksize=-1, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = request.execute()

            self.mostrar_estado(f"🎉 ¡ÉXITO! Video Publicado. ID: {response['id']}", "#00FF00")
        except Exception as e: self.mostrar_estado(f"❌ Error al Publicar: {e}", "red")
        finally: self.cambiar_estado_boton(self.btn_publicar_yt, "normal")

if __name__ == "__main__":
    app = StudioApp()
    app.mainloop()
    