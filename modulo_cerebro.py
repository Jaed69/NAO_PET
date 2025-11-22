import requests
import time
import sys

# CONFIGURACIÓN
MODELO_OLLAMA = "gemma3n" 
URL_OLLAMA = "http://localhost:11434/api/generate"

# DICCIONARIO DE RAZONAMIENTO (Contexto para Gemma)
CLASES_DISPONIBLES = """
CONTEXTO VISUAL DEL ROBOT:
- person (gente, amigos, alguien)
- bottle (botellas, agua, bebidas, sed)
- cup (tazas, vasos, café)
- laptop (computadoras, trabajar, programar)
- book (libros, leer, estudiar, escribir)
- mouse (ratón pc, usar la compu)
- cell phone (celulares, llamar, chatear)
- wallet (billeteras, dinero, pagar)
- keys (llaves, abrir, salir)
- backpack (mochilas, guardar cosas)
- remote (controles tv)
- watch (reloj, hora)
- pen (escribir, lapicero)
- robot (humanoide, ciborg)
- can (latas, bebidas, refrescos)
- backpack (mochilas, guardar cosas)
- paper (papel, hojas, escribir)
"""

def calentar_cerebro():
    """Envía una petición vacía para cargar el modelo en VRAM."""
    print("🔥 [CEREBRO] Calentando motores (Cargando modelo en GPU)...")
    start = time.time()
    try:
        pensar("hola", debug=False)
        t = (time.time() - start) * 1000
        print(f"✅ [CEREBRO] Listo y caliente. Tiempo de arranque: {int(t)}ms")
        return True
    except Exception as e:
        print(f"❌ [CEREBRO] Error al calentar: {e}")
        return False

def pensar(texto_usuario, debug=True):
    """
    Traduce intención -> Objeto visual en inglés.
    """
    start = time.time()
    if debug: print(f"⚡ [CEREBRO] Analizando: '{texto_usuario}'...")

    prompt = f"""
    Eres el sistema de visión de un robot.
    Tu tarea es deducir qué OBJETO FÍSICO necesita el usuario.
    
    {CLASES_DISPONIBLES}

    REGLAS:
    1. Si pide algo abstracto ("tengo sueño"), busca el objeto relacionado ("bed" o "sofa").
    2. Si pide buscar a alguien, responde "person".
    3. Si no hay un objeto físico claro, responde "null".
    4. NO escribas oraciones. SOLO la palabra (o par de palabras).

    EJEMPLOS:
    - "Me muero de sed" -> bottle
    - "Quiero programar" -> laptop
    - "Donde me puedo sentar" -> chair
    - "Que hora es" -> watch
    - "Abre la puerta" -> door
    - "Limpia esto" -> trash can

    Frase: "{texto_usuario}"
    Respuesta (SOLO LA PALABRA EN INGLÉS O 'null'):
    """

    try:
        payload = {
            "model": MODELO_OLLAMA,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0, 
                "num_predict": 10 
            }
        }
        
        # Timeout de 30s para seguridad
        response = requests.post(URL_OLLAMA, json=payload, timeout=30)
        
        if response.status_code == 200:
            resultado = response.json()['response'].strip().lower()
            resultado = resultado.replace(".", "").replace('"', "").replace("'", "").split()[0]
            
            duracion = (time.time() - start) * 1000
            if debug: print(f"🧠 [CEREBRO] Resultado: '{resultado}' ({int(duracion)}ms)")
            
            return resultado
        else:
            print(f"❌ [CEREBRO] Error API: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ [CEREBRO] Error Conexión: {e}")
        return None