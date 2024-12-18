import os
import time
import requests
from datetime import datetime
from requests.auth import HTTPDigestAuth
from concurrent.futures import ThreadPoolExecutor
import argparse
import signal
import configparser
import pytz
import cv2

def limpiar(dir,ult_file):
    for file in os.listdir(dir):
        if file != ult_file:
            os.remove(dir+file)
    print(f"Directorio limpio: {dir}")

def procesar(config):
    
  
    username = config["CAMARA"]["username"]
    password = config["CAMARA"]["password"]
    url = config["CAMARA"]["url"]

    ruta_base_descarga=config["CAPTURA"]["ruta_base_descarga"]
    frameskip=config["CAPTURA"]["frameskip"]
    tiempo_espera_error=config["CAPTURA"]["tiempo_espera_error"]
    nombre_camara = config["CAPTURA"]["nombre_camara"]
    
    hora_america=pytz.timezone('America/Lima')

    indice=1

    vidcap = cv2.VideoCapture(self.url_rtsp,cv2.CAP_FFMPEG)

    if (vidcap.isOpened() == False):
        print("no se puede abrir archivo: "+self.url_rtsp)
    return

    while (vidcap.isOpened()):
        try:
            datetime_actual=datetime.now(hora_america)

            texto_fecha=datetime_actual.strftime('%Y_%m_%d')
            texto_hora=datetime_actual.strftime('%H_%M_%S_%f')
                
            nombre_imagen=texto_fecha+'-'+texto_hora+"-"+nombre_camara+".jpg"

            ruta_captura=ruta_base_descarga+"/"+nombre_camara+"/"+nombre_imagen

            ret, frame = vidcap.read()

            if not self.frame_skip ==0:
                for z in range(self.frame_skip):
                    ret, frame = vidcap.read()

            if ret == False:
                print("frame es nulo!!!!")
                logging.error("FRAME EN NULO!")

                time.sleep(tiempo_espera_error)

                logging.error("Reconectando")

                while (True):
                    print("tratando de abrir nuevamente")
                    vidcap = cv2.VideoCapture(url,cv2.CAP_FFMPEG)
                    
                    if vidcap.isOpened():
                        break
                    else:
                        time.sleep(2*60)
                continue

            cv2.imwrite(ruta_captura,frame)

            imagen_descargada = Image.open(ruta_captura)
            ancho, alto = imagen_descargada.size
            imagen_descargada.close()

        except Exception as e:
            logging.exception("Error en Factory Stream mp4")
            print(e)
            time.sleeptiempo_espera_error

def signal_handler(key, frame):
	print("\n[*] Saliendo\n")
	sys.exit(1)

if __name__ == "__main__":
    
    signal = signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description='Pipeline puente grua')
    parser.add_argument('archivo_configuracion', help='Path to configuration .ini file')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.archivo_configuracion)

    procesar(config)
