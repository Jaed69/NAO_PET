import cv2
import threading
import time
import torch
import socket
import struct
import numpy as np
from ultralytics import YOLOWorld
import warnings

# --- TUS MÓDULOS ---
import modulo_cerebro
from modulo_oido import SistemaOido

warnings.filterwarnings("ignore")

# --- CONFIGURACIÓN ---
MODELO_YOLO = "yolov8s-worldv2.pt"
HOST = '0.0.0.0'
PORT = 8080

class EstadoRobot:
    def __init__(self):
        self.objetivo_visual = "person"
        self.estado_sistema = "Iniciando..."
        self.ultimo_comando = ""
        self.puede_caminar = False # <--- POR SEGURIDAD EMPIEZA QUIETO
        self.lock = threading.Lock()

    def leer_objetivo(self):
        with self.lock: return self.objetivo_visual
    
    def actualizar_objetivo(self, obj):
        with self.lock: self.objetivo_visual = obj

    def set_caminar(self, valor):
        with self.lock: self.puede_caminar = valor
    
    def get_caminar(self):
        with self.lock: return self.puede_caminar
    
    def set_estado(self, txt):
        with self.lock: self.estado_sistema = txt

state = EstadoRobot()

# ==========================================
# 🧠 HILO DE INTELIGENCIA (OIDO + CEREBRO)
# ==========================================
def ciclo_inteligencia():
    oido = SistemaOido()
    state.set_estado("Cargando Ollama...")
    
    # 1. Calentar el Cerebro (LLM)
    if not modulo_cerebro.calentar_cerebro():
        state.set_estado("Error en LLM")
        print("❌ Error cargando el modelo de lenguaje")
    else:
        print("🤖 [IA] Inteligencia lista.")
        state.set_estado("Esperando orden...")

    while True:
        try:
            # A. ESCUCHAR
            audio = oido.escuchar()
            if audio:
                texto = oido.transcribir(audio)
                
                if texto:
                    print(f"🗣️ OÍDO: '{texto}'")
                    state.ultimo_comando = texto
                    texto_lower = texto.lower()

                    # --- NIVEL 1: REFLEJOS (Comandos de Movimiento) ---
                    # Estos tienen prioridad y NO pasan por la IA pesada
                    if "acércate" in texto_lower or "ven" in texto_lower or "camina" in texto_lower:
                        state.set_caminar(True)
                        state.set_estado("ACERCANDOSE")
                        print("✅ ORDEN: CAMINAR")
                        continue # Saltamos el resto del ciclo

                    if "para" in texto_lower or "alto" in texto_lower or "quieto" in texto_lower:
                        state.set_caminar(False)
                        state.set_estado("DETENIDO")
                        print("⛔ ORDEN: ALTO")
                        continue

                    # --- NIVEL 2: COGNITIVO (Cambio de Objetivo) ---
                    # Si no es movimiento, verificamos si es una orden para el LLM
                    activado, trigger = oido.verificar_trigger(texto)
                    
                    if activado:
                        state.set_estado("Pensando...")
                        print(f"🤔 Consultando cerebro por: {trigger}")
                        
                        # Preguntamos a Ollama/Tu modulo
                        nuevo_target = modulo_cerebro.pensar(texto)
                        
                        if nuevo_target and "null" not in nuevo_target:
                            # Limpiamos el string por si acaso
                            nuevo_target = nuevo_target.strip().lower()
                            state.actualizar_objetivo(nuevo_target)
                            state.set_estado(f"BUSCANDO: {nuevo_target.upper()}")
                            print(f"🎯 NUEVO OBJETIVO: {nuevo_target}")
                        else:
                            state.set_estado("No entendí el objeto")

        except Exception as e:
            print(f"Error en ciclo inteligencia: {e}")

# ==========================================
# 👁️ HILO PRINCIPAL (VISION + RED)
# ==========================================
def main():
    # Arrancar Hilo de Inteligencia
    t = threading.Thread(target=ciclo_inteligencia)
    t.daemon = True
    t.start()

    print(f"🚀 [VISION] Cargando YOLO ({MODELO_YOLO})...")
    model = YOLOWorld(MODELO_YOLO)
    if torch.cuda.is_available(): model.to('cuda')

    # Servidor Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"📡 Esperando conexión del cuerpo NAO...")

    conn, addr = server_socket.accept()
    print(f"🔗 Cuerpo conectado: {addr}")

    # Variables locales para optimizar el bucle
    target_vigente = "person"
    model.set_classes([target_vigente])
    
    data = b""
    payload_size = struct.calcsize("L")

    while True:
        try:
            # 1. RECEPCION DE VIDEO
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet: break
                data += packet
            if not data: break
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]
            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            h, w, _ = frame.shape
            cx, cy = w // 2, h // 2

            # 2. SINCRONIZAR MENTE Y VISTA
            nuevo_target = state.leer_objetivo()
            if nuevo_target != target_vigente:
                print(f"🔄 Cambiando lentes YOLO a: {nuevo_target}")
                model.set_classes([nuevo_target])
                target_vigente = nuevo_target

            # 3. INFERENCIA YOLO
            results = model.predict(frame, conf=0.13, verbose=False)
            
            # Preparar mensaje por defecto: "Nada encontrado"
            caminar_flag = 1 if state.get_caminar() else 0
            mensaje_robot = f"0,0,0,0,LOST,{caminar_flag}"

            if len(results[0].boxes) > 0:
                # Buscar el objeto más grande (más cercano)
                boxes = results[0].boxes
                best_box = None
                max_area = 0

                for box in boxes:
                    bx1, by1, bx2, by2 = box.xyxy[0].cpu().numpy()
                    area = (bx2 - bx1) * (by2 - by1)
                    if area > max_area:
                        max_area = area
                        best_box = box
                
                if best_box is not None:
                    x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
                    obj_cx = (x1 + x2) / 2
                    obj_cy = (y1 + y2) / 2
                    
                    # Cálculos para el robot
                    area_norm = max_area / (w * h)
                    err_x = (obj_cx - cx) / (w / 2)
                    err_y = (obj_cy - cy) / (h / 2)
                    count = len(boxes)

                    # FORMATO PROTOCOLO: dx, dy, area, count, name, FLAG_CAMINAR
                    mensaje_robot = f"{err_x:.2f},{err_y:.2f},{area_norm:.3f},{count},{target_vigente},{caminar_flag}"

                    # Visualización
                    annotated_frame = results[0].plot()
                    
                    # Overlay de estado
                    color_st = (0, 255, 0) if caminar_flag else (0, 0, 255)
                    estado_txt = "CAMINANDO" if caminar_flag else "ESPERANDO ORDEN"
                    cv2.putText(annotated_frame, estado_txt, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color_st, 2)
                    
                    cv2.imshow("CEREBRO CENTRAL", annotated_frame)
            else:
                cv2.imshow("CEREBRO CENTRAL", frame)

            # 4. ENVIAR AL ROBOT
            mensaje_final = mensaje_robot + "#"
            conn.sendall(mensaje_final.encode())

            if cv2.waitKey(1) == ord('q'): break

        except Exception as e:
            print(f"Error en bucle principal: {e}")
            break

    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()