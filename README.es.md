# 🤖 NAO V2 - Sistema de Control Inteligente para Robot NAO

Este proyecto implementa un sistema de control avanzado para el robot humanoide NAO, dotándolo de capacidades de visión artificial (YOLOv8) y procesamiento de lenguaje natural para seguir instrucciones de voz y rastrear objetos en tiempo real.

## 📋 Descripción

El sistema se divide en dos módulos principales que se comunican vía Sockets TCP/IP:

1.  **El Cerebro (`nao_brain_v3.py`)**:
    *   Se ejecuta en una computadora externa (PC/Servidor).
    *   Procesa el video enviado por el robot utilizando **YOLO-World** para detección de objetos en tiempo real.
    *   Escucha comandos de voz a través del micrófono del PC (`modulo_oido`).
    *   Utiliza un LLM (Ollama) para interpretar intenciones complejas (`modulo_cerebro`).
    *   Envía comandos de movimiento y control al robot.

2.  **El Cuerpo (`nao_body_v4.py`)**:
    *   Se ejecuta en el entorno del robot (o una máquina con NAOqi SDK compatible, Python 2.7).
    *   Transmite el video de la cámara del NAO al cerebro.
    *   Recibe coordenadas y comandos de navegación.
    *   Ejecuta movimientos (caminar, mover la cabeza) y síntesis de voz (TTS).

## 🚀 Funcionalidades

*   **Rastreo Visual**: El robot mueve la cabeza para seguir objetos detectados (personas, celulares, botellas, etc.).
*   **Navegación Autónoma**: Puede caminar hacia un objetivo detectado hasta alcanzar una distancia segura.
*   **Control por Voz**:
    *   *Comandos Directos*: "Acércate", "Ven", "Para", "Quieto".
    *   *Inteligencia Artificial*: Puede interpretar órdenes para buscar objetos específicos (ej. "Busca una botella").
*   **Interacción**: El robot habla y señala los objetos cuando los encuentra.

## 🛠️ Requisitos

### Para el "Cerebro" (PC)
*   Python 3.8+
*   Librerías principales:
    *   `ultralytics` (YOLOv8)
    *   `opencv-python`
    *   `torch` (con soporte CUDA recomendado)
    *   `numpy`
    *   Ollama (para el módulo de cerebro)

### Para el "Cuerpo" (Robot NAO)
*   Python 2.7 (Estándar en NAOqi)
*   SDK de NAOqi (`pynaoqi`)
*   Librerías: `opencv` (versión compatible con Py2.7), `numpy`.

## 🔧 Instalación y Uso

1.  **Configuración de Red**:
    *   Asegúrate de que tanto el PC como el NAO estén en la misma red.
    *   Edita `nao_body_v4.py` y ajusta `SERVER_IP` con la IP de tu PC.
    *   Edita `nao_body_v4.py` y ajusta `ROBOT_IP` con la IP de tu NAO.

2.  **Ejecutar el Cerebro**:
    En tu PC, ejecuta el script principal:
    ```bash
    python nao_brain_v3.py
    ```
    *Esperar a que cargue el modelo YOLO y el servidor socket.*

3.  **Ejecutar el Cuerpo**:
    Conéctate al robot (o desde tu entorno con NAOqi) y corre:
    ```bash
    python nao_body_v4.py
    ```

## 📂 Estructura del Proyecto

*   `nao_brain_v3.py`: Script principal del servidor de procesamiento.
*   `nao_body_v4.py`: Script cliente que controla el hardware del robot.
*   `modulo_oido.py`: Sistema de reconocimiento de voz.
*   `modulo_cerebro.py`: Interfaz con el LLM (Ollama).
*   `yolov8s-worldv2.pt`: Modelo de pesos para la red neuronal.

## ⚠️ Notas
*   El script del cuerpo asume que el SDK de NAOqi está en `C:\pynaoqi-python2.7-2.8.6.23`. Ajusta la variable `BASE_SDK` si tu instalación es diferente.
