# Creador Finanzas — Estudio Automatizado de Videos con IA

Aplicación de escritorio en Python (CustomTkinter + MoviePy) para la creación automatizada de videos largos y Shorts de finanzas/economía con Inteligencia Artificial y publicación directa en YouTube.

## Características principales
- **Generación de guiones de alta retención** con OpenAI (`gpt-4o-mini` / `gpt-4o`).
- **Locución realista (TTS)** mediante **ElevenLabs** (`eleven_multilingual_v2`).
- **Búsqueda y generación de material visual**:
  - Banco de videos **Pexels**
  - **Stability AI** (Image-to-Video)
  - **Runway**
  - **Fal.ai** (Kling / Luma Dream Machine)
- **Edición y renderizado automático** con **MoviePy** y subtítulos dinámicos.
- **Publicación directa en YouTube** vía Google YouTube Data API v3 (`OAuth2`).

## Estructura del proyecto
- `aplicacion mejorada con gilab.py`: Versión principal mejorada con arquitectura modular de proveedores (OpenAI, ElevenLabs, Pexels, Stability AI, Runway, Fal.ai) e interfaz gráfica en CustomTkinter.
- `app_visual.py`: Interfaz visual de estudio en CustomTkinter.
- `creador.py`: Script de línea de comandos para generación y montaje por capítulos.
- `publicador.py`: Módulo de autenticación OAuth2 y subida a YouTube.

## Configuración
1. Crea un archivo `config_keys.json` en la raíz del proyecto (o guarda las llaves desde la interfaz gráfica):
   ```json
   {
     "openai": "sk-...",
     "elevenlabs": "sk_...",
     "pexels": "...",
     "stability": "...",
     "runway": "...",
     "fal": "...",
     "motor_ia": "Pexels (Gratis)"
   }
   ```
2. Para publicar en YouTube, coloca tu archivo `client_secret.json` de Google Cloud Console en la raíz del proyecto.
