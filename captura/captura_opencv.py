import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import argparse
import signal
import configparser
import cv2
import logging
from PIL import Image,ImageDraw,ImageStat
import sys
import pika

def limpiar(dir,ult_file):
    for file in os.listdir(dir):
        if file != ult_file:
            os.remove(dir+file)
    print(f"Directorio limpio: {dir}")

def procesar(config):
    
    ruta_mp4 = config["VIDEO"]["ruta"]

    ruta_frames=config["CAPTURA"]["ruta_frames"]
    frameskip=config.getint("CAPTURA","frameskip")
    tiempo_espera_error=config.getint("CAPTURA","tiempo_espera_error")

    indice=1

    vidcap = cv2.VideoCapture(ruta_mp4)

    if (vidcap.isOpened() == False):
        print("no se puede abrir archivo: "+ruta_mp4)
        return

    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    nombre_canal=config["RABBIT"]["nombre_cola"]
    print("nombre canal!")
    print(nombre_canal)

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=nombre_canal)
    channel.confirm_delivery()

    while (vidcap.isOpened()):
        try:
            timestamp = time.time()

            integer_part = int(timestamp)
            fractional_part = int((timestamp - integer_part) * 1_000_000)

            nombre_captura=str(integer_part)+"_"+str(fractional_part)

            nombre_captura=nombre_captura+"_"+str(width)+"_"+str(height)

            nombre_final=ruta_frames+"/"+nombre_captura+".jpg"

            ret, frame = vidcap.read()

            if not frameskip ==0:
                for z in range(frameskip):
                    ret, frame = vidcap.read()

            if ret == False:
                print("frame es nulo!!!!")
                logging.error("FRAME EN NULO!")

                time.sleep(tiempo_espera_error)

                logging.error("Reconectando")

                while (True):
                    print("tratando de abrir nuevamente")
                    vidcap = cv2.VideoCapture(ruta_mp4)
                    
                    if vidcap.isOpened():
                        break
                    else:
                        time.sleep(5)
                continue
            print(nombre_final)
            cv2.imwrite(nombre_final,frame)
            channel.basic_publish(exchange='', routing_key=nombre_canal, body=nombre_final)

        except Exception as e:
            logging.exception("Error en Factory Stream mp4")
            print(e)
            time.sleep(tiempo_espera_error)

def signal_handler(key, frame):
	print("\n[*] Saliendo\n")
	sys.exit(1)

if __name__ == "__main__":
    print("iniciando")
    signal = signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description='Pipeline captura opencv')
    parser.add_argument('archivo_configuracion', help='Path to configuration .ini file')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.archivo_configuracion)

    procesar(config)

