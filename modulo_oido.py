import speech_recognition as sr
import io
import torch
import numpy as np
from faster_whisper import WhisperModel
from thefuzz import process, fuzz
import time

# CONFIGURACIÓN
MODELO_WHISPER = "small"
TRIGGERS = ["nao", "nau", "now", "no", "know", "robot", "causa", "kausa", "oye", "habla", "nada"]

class SistemaOido:
    def __init__(self):
        print(f"🎧 [OÍDO] Cargando Whisper ({MODELO_WHISPER})...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "int8_float16" if device == "cuda" else "int8"
        
        self.model = WhisperModel(MODELO_WHISPER, device=device, compute_type=compute)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000
        self.recognizer.pause_threshold = 0.8
        print("✅ [OÍDO] Sistema auditivo activo.")

    def escuchar(self):
        """Captura audio del micrófono y retorna el objeto audio o None."""
        try:
            with sr.Microphone() as source:
                # print("🎤 [OÍDO] Escuchando...", end="\r")
                try:
                    # Timeout corto para no bloquear el hilo principal
                    return self.recognizer.listen(source, timeout=1.5, phrase_time_limit=5)
                except sr.WaitTimeoutError:
                    return None
        except Exception as e:
            print(f"❌ [OÍDO] Error micrófono: {e}")
            return None

    def transcribir(self, audio_obj):
        """Convierte audio a texto."""
        if not audio_obj: return None
        
        start = time.time()
        audio_data = io.BytesIO(audio_obj.get_wav_data())
        
        # Prompt Contextual para ayudar a Whisper con jergas y objetos
        prompt = "Habla causa Nao, busca la billetera, mochila, reloj, laptop, botella, sed, libro."
        
        segmentos, _ = self.model.transcribe(
            audio_data, beam_size=1, language="es", vad_filter=True,
            initial_prompt=prompt
        )
        texto = " ".join([s.text for s in segmentos]).strip()
        
        duracion = (time.time() - start) * 1000
        if len(texto) > 2:
            print(f"🗣️  [OÍDO] Transcripción: '{texto}' ({int(duracion)}ms)")
            return texto
        return None

    def verificar_trigger(self, texto):
        """Verifica si llamaron al robot."""
        if not texto: return False, None
        texto_b = texto.lower()
        
        # 1. Fuzzy Match en la primera palabra
        match, score = process.extractOne(texto_b.split()[0], TRIGGERS, scorer=fuzz.ratio)
        if score >= 80: return True, match
        
        # 2. Búsqueda directa
        for t in TRIGGERS:
            if t in texto_b: return True, t
            
        return False, None