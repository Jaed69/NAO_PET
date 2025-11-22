import torch
from ultralytics import YOLOWorld
import time

# CONFIGURACIÓN
MODELO_YOLO = "yolov8s-worldv2.pt"

class SistemaVision:
    def __init__(self):
        print(f"🚀 [VISIÓN] Iniciando sistema ocular ({MODELO_YOLO})...")
        self.model = YOLOWorld(MODELO_YOLO)
        self.clase_actual = "person"
        
        # Optimización de Hardware
        if torch.cuda.is_available():
            print("⚡ [VISIÓN] GPU Detectada. Activando modo CUDA.")
            self.model.to('cuda')
        else:
            print("⚠️ [VISIÓN] No se detectó GPU. Usando CPU (Más lento).")

        # Configuración inicial segura
        self.cambiar_objetivo("person")

    def cambiar_objetivo(self, nuevo_objetivo):
        """
        Cambia lo que YOLO busca en tiempo real.
        Retorna True si el cambio fue exitoso.
        """
        if nuevo_objetivo == self.clase_actual:
            return False

        print(f"🔄 [VISIÓN] Reconfigurando retina para buscar: '{nuevo_objetivo}'")
        try:
            self.model.set_classes([nuevo_objetivo])
            self.clase_actual = nuevo_objetivo
            return True
        except Exception as e:
            print(f"❌ [VISIÓN] Error al cambiar clases: {e}")
            return False

    def detectar(self, frame, confianza=0.12):
        """
        Realiza la inferencia en el frame actual.
        Retorna los resultados de YOLO.
        """
        # verbose=False evita que llene la consola de texto basura
        results = self.model.predict(frame, conf=confianza, verbose=False)
        return results

    def obtener_target_actual(self):
        return self.clase_actual