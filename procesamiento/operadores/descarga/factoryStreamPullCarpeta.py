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

class FactoryStreamPullCarpeta:

    def __init__(self,
        nombre_camara,
        ruta_carpeta):

        self.nombre_camara=nombre_camara
        self.ruta_carpeta=ruta_carpeta
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

                    archivo=archivo.rstrip(".jpg")

                    parts = archivo.split('_')

                    timestamp_entero=int(parts[0])
                    timestamp_fraccion=int(parts[1])

                    ancho = int(parts[2])
                    alto = int(parts[3])

                    json_datos = {
                        "nombre_imagen": archivo, 
                        "ruta_base":self.ruta_carpeta,
                        "timestamp_entero":timestamp_entero,
                        "timestamp_fraccion":timestamp_fraccion,
                        "ancho":ancho,
                        "alto":alto,
                        "factor_riesgo":"no"
                    }
                    print("aca???")
                    print(json)_datos
                    observer.on_next(json_datos)
                    print("sigo")


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
