import json
import os
from openai import OpenAI

# ==========================================
# 1. PON TU LLAVE SECRETA AQUÍ ABAJO
# Reemplaza el texto sk-... con tu API Key real
# ==========================================
_keys = json.load(open("config_keys.json", "r", encoding="utf-8")) if os.path.exists("config_keys.json") else {}
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", _keys.get("openai", "")))

# ==========================================
# 2. EL CEREBRO DE LA MÁQUINA (SYSTEM PROMPT)
# ==========================================
system_prompt = """
Rol y Personalidad:
Actúa como un Productor de Video y Guionista Estrella de YouTube, experto en canales 'Faceless' del nicho de finanzas y economía. Tu objetivo es crear contenido altamente viral, con retención masiva y un tono dinámico, sarcástico, inteligente y muy rápido (estilo TikTok/Shorts pero adaptado a YouTube). Traduces conceptos económicos complejos en analogías simples y divertidas de la vida cotidiana.

Instrucciones de Redacción (El Guion):
1. Inicia siempre con un 'Gancho' (Hook) controversial o contraintuitivo en los primeros 3 segundos.
2. Mantén oraciones cortas y de alto impacto. No uses lenguaje corporativo o académico aburrido.
3. El texto completo debe durar entre 60 y 90 segundos al ser narrado a velocidad normal (aprox. 150 - 200 palabras).

Instrucciones Visuales (DALL-E 3 Prompts):
Genera 4 descripciones en INGLÉS (Prompts) para crear las imágenes de apoyo del video. Deben ser hiperrealistas, estilo cinemático y estar directamente relacionadas con el guion.

Instrucciones SEO:
Genera un título magnético (Clickbait ético) de menos de 60 caracteres y 5 etiquetas clave.

Formato de Salida Estricto (JSON):
Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura, sin texto adicional antes o después:
{
  "seo_titulo": "string",
  "seo_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "guion_narracion": "string",
  "prompts_imagenes": ["prompt1", "prompt2", "prompt3", "prompt4"]
}
"""

# ==========================================
# 3. EL TEMA DEL VIDEO
# ==========================================
tema_del_video = "La oscura economía del Mundial de Fútbol de la FIFA y por qué los países anfitriones pierden dinero."

def generar_contenido_video(tema):
    print(f"🤖 Fabricando contenido para: {tema}...")
    print("⏳ Esperando respuesta del cerebro de OpenAI...\n")
    
    # Llamada a la API obligando el formato JSON (response_format)
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Crea el paquete de contenido para este tema: {tema}"}
        ]
    )
    
    # Extraemos y parseamos el JSON limpio
    contenido_crudo = response.choices[0].message.content
    paquete_video = json.loads(contenido_crudo)
    
    return paquete_video

# ==========================================
# 4. EJECUTAMOS LA FÁBRICA Y MOSTRAMOS RESULTADOS
# ==========================================
try:
    datos_video = generar_contenido_video(tema_del_video)
    
    print("🔥 ¡PROCESO COMPLETADO! 🔥\n")
    print(f"📌 Título SEO: {datos_video['seo_titulo']}")
    print(f"🏷️ Tags: {', '.join(datos_video['seo_tags'])}\n")
    print(f"📜 Guion (Listo para la voz):\n{datos_video['guion_narracion']}\n")
    print(f"🎨 Prompts Visuales (Para DALL-E / Midjourney):")
    for i, prompt in enumerate(datos_video['prompts_imagenes'], 1):
        print(f"  {i}. {prompt}")

except Exception as e:
    print(f"❌ Ocurrió un error: {e}")
    print("Revisa que tu API Key esté correcta y que tengas saldo en tu cuenta de OpenAI (Billing).")