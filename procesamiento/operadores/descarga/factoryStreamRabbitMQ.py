import pytz
import requests
from datetime import datetime
from rx import create
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
import time
from PIL import Image,ImageDraw,ImageStat
import io
import configparser
import os
import logging
import cv2

class FactoryStreamRabbitMQ:

    def __init__(self,
        nombre_camara,
        nombre_canal):

        self.nombre_camara=nombre_camara
        self.nombre_canal=nombre_canal
        self.errores=0
        self.descarga_fallida=0

    def crear_stream(self):
        
        self.stream= create(self.leer_datos)
        return self.stream

    def escribir_error(self,ruta,tipo,camara):

        #config = configparser.ConfigParser()
        #config.read(camara+'.ini')

        #file = open(nombre_captura, "wb")
        #file.write(response.status_code)
        #file.close()

        return

    def leer_datos(self,observer, scheduler):

        while True:

            try:

                archivos = os.listdir(self.ruta_carpeta)
                
                if len(archivos)==0:
                    print("nada por procesar, duermo")
                    time.sleep(0.1)
                    continue

                archivos = sorted(archivos)

                for archivo in archivos:
                    
                    print("procesando"+archivo)

                    parts = archivo.split('_')

                    timestamp_entero=int(parts[0])
                    timestamp_fraccion=int(parts[1])

                    ancho = int(parts[2])
                    alto = int(parts[3])

                    f = open("/data/pipelines-grua-apt/captura/boxes/"+archivo, "r")
                    boxes = f.readlines()
                    f.close()

                    json_datos = {
                        "nombre_imagen": archivo+".jpg", 
                        "ruta_base": "/data/pipelines-grua-apt/captura/frames",
                        "boxes": boxes,
                        "timestamp_entero":timestamp_entero,
                        "timestamp_fraccion":timestamp_fraccion,
                        "ancho":ancho,
                        "alto":alto,
                        "factor_riesgo":"no"
                    }
                  
                  
                    observer.on_next(json_datos)
                  


            except Exception as e:
                logging.exception("Error en Factory Stream Pull Carpeta")
                #logging.error(e)
                
                print(e)
                self.escribir_error("","","")
             
                self.errores=self.errores+1

                with open(self.ruta_carpeta+"/"+self.nombre_camara+"/status/metricas",'w') as f:
                    f.write(self.nombre_camara+".exepciones "+str(self.errores)+"\n")
                    f.write(self.nombre_camara+".descarga_fallida "+str(self.descarga_fallida))


        observer.on_completed()
