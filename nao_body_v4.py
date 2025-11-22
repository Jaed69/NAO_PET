# -*- coding: utf-8 -*-
import socket
import struct
import sys
import os
import time

# --- RUTA SDK ---
BASE_SDK = r"C:\pynaoqi-python2.7-2.8.6.23" 
RUTA_LIB = os.path.join(BASE_SDK, "lib")
if RUTA_LIB not in sys.path: sys.path.insert(0, RUTA_LIB)

from naoqi import ALProxy
import numpy as np
import cv2

SERVER_IP = '127.0.0.1'
SERVER_PORT = 8080
ROBOT_IP = "169.254.169.128" 
SENTIDO_MARCHA = 1.0 
AREA_META = 0.10

# --- ANIMACIÓN DE SEÑALAR ---
def senalar_y_celebrar(motion, tts, nombre_objeto):
    print "👉 SENALANDO OBJETIVO..."
    
    # 1. Detener caminata por completo
    motion.stopMove()
    
    # 2. Configuración del brazo derecho para señalar
    # RShoulderPitch: 0.0 (Brazo horizontal)
    # RShoulderRoll: -0.1 (Ligeramente abierto)
    # RElbowRoll: 0.1 (Codo casi estirado)
    # RHand: 1.0 (Mano abierta)
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"]
    angles = [0.0, -0.1, 0.1, 1.5, 1.0]
    
    # Mover brazo rapido (0.2 de velocidad)
    motion.setAngles(names, angles, 0.2)
    
    # 3. Hablar (Fonética Spanglish para "Encontré lo que buscas")
    # Frase: "Encontré lo que buscas: [Objeto]"
    frase = "\\rspd=95\\ En-con-treh. lo. keh. bus-cas. " + nombre_objeto
    tts.say(frase)
    
    # Mantener la pose 2 segundos
    time.sleep(2)
    
    # 4. Bajar el brazo (Posición relajada)
    angles_relax = [1.5, 0.0, 0.0, 0.0, 0.0]
    motion.setAngles(names, angles_relax, 0.1)

def main():
    print "=== CUERPO V8 (FINAL CON GESTOS) ==="
    
    try:
        video = ALProxy("ALVideoDevice", ROBOT_IP, 9559)
        motion = ALProxy("ALMotion", ROBOT_IP, 9559)
        tts = ALProxy("ALTextToSpeech", ROBOT_IP, 9559)
        posture = ALProxy("ALRobotPosture", ROBOT_IP, 9559)
    except:
        print "Error conectando al NAO."
        return

    tts.setLanguage("English")
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP, SERVER_PORT))
        tts.say("\\rspd=90\\ Listo.")
    except:
        print "Falta correr el cerebro primero."
        return

    motion.wakeUp()
    posture.goToPosture("StandInit", 0.5)
    
    sub_name = "nao_final_" + str(time.time())
    handle = video.subscribeCamera(sub_name, 0, 1, 11, 30)

    head_yaw = 0.0
    head_pitch = 0.0
    
    # Variables de estado
    modo_anterior = 0 
    ya_celebre = False # Para que no señale infinitamente

    try:
        while True:
            img_nao = video.getImageRemote(handle)
            if img_nao:
                width, height = img_nao[0], img_nao[1]
                array = img_nao[6]
                img_np = np.frombuffer(array, dtype=np.uint8).reshape((height, width, 3))
                _, img_encoded = cv2.imencode('.jpg', img_np, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                data = img_encoded.tostring()

                client.setblocking(1)
                try:
                    client.sendall(struct.pack("L", len(data)) + data)
                except:
                    break

                client.setblocking(0)
                try:
                    raw_data = client.recv(4096)
                    if raw_data:
                        mensajes = raw_data.split('#')
                        mensajes_validos = [m for m in mensajes if len(m) > 5]
                        
                        if len(mensajes_validos) > 0:
                            msg = mensajes_validos[-1]
                            
                            if "LOST" not in msg:
                                try:
                                    parts = msg.split(',')
                                    if len(parts) >= 6:
                                        dx = float(parts[0])
                                        dy = float(parts[1])
                                        area = float(parts[2])
                                        obj_name = parts[4] # Nombre en inglés
                                        puede_caminar = int(float(parts[5]))

                                        # TRADUCCION FONETICA DEL OBJETO
                                        obj_fonetico = obj_name
                                        if obj_name == "person": obj_fonetico = "Pair-saw-nah"
                                        if obj_name == "cell phone": obj_fonetico = "Cel-u-lar"
                                        if obj_name == "bottle": obj_fonetico = "Bo-te-yah"

                                        # 1. CABEZA (Rastreo)
                                        head_yaw -= dx * 0.06
                                        head_pitch += dy * 0.06
                                        head_yaw = max(-1.5, min(1.5, head_yaw))
                                        head_pitch = max(-0.5, min(0.5, head_pitch))
                                        motion.setAngles(["HeadYaw", "HeadPitch"], [head_yaw, head_pitch], 0.15)

                                        # 2. LOGICA DE COMPORTAMIENTO
                                        if puede_caminar == 0:
                                            # ESTADO: PARADO / ESPERANDO
                                            if modo_anterior == 1:
                                                motion.stopMove()
                                                tts.say("\\rspd=110\\ Stop.")
                                            ya_celebre = False # Reseteamos para la proxima vez
                                        
                                        else:
                                            # ESTADO: BUSCANDO / CAMINANDO
                                            if modo_anterior == 0:
                                                tts.say("\\rspd=110\\ Voy.")
                                            
                                            # Calcular movimiento
                                            vx = 0.0
                                            vth = head_yaw * 0.5
                                            
                                            # DISTANCIA
                                            if area < AREA_META:
                                                # Aún lejos -> Caminar
                                                vx = 0.25 * SENTIDO_MARCHA
                                                ya_celebre = False # Aun no llegamos
                                                print ">> AVANZANDO"
                                                motion.moveToward(vx, 0.0, vth)
                                                
                                            elif area > (AREA_META + 0.15):
                                                # Demasiado cerca -> Retroceder
                                                vx = -0.1 * SENTIDO_MARCHA
                                                print "<< RETROCEDIENDO"
                                                motion.moveToward(vx, 0.0, vth)
                                                
                                            else:
                                                # LLEGAMOS A LA META!
                                                if not ya_celebre:
                                                    # Ejecutar acción final
                                                    senalar_y_celebrar(motion, tts, obj_fonetico)
                                                    ya_celebre = True # Marcar como hecho
                                                    
                                                # Mantenerse quieto pero alerta
                                                motion.stopMove()
                                                print "🌟 OBJETIVO ENCONTRADO"

                                        modo_anterior = puede_caminar

                                except ValueError:
                                    pass
                except socket.error:
                    pass

    except KeyboardInterrupt:
        motion.stopMove()
        motion.rest()
    finally:
        video.unsubscribe(handle)
        client.close()

if __name__ == "__main__":
    main()