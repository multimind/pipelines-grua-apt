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
import os

class FactoryStreamScreenshot:

    def __init__(self,
        nombre_camara,
        ruta_base_descarga,
        tiempo_espera_error=3):

        self.nombre_camara=nombre_camara
        self.ruta_base_descarga=ruta_base_descarga
        self.tiempo_espera_error=tiempo_espera_error
        self.errores=None

        ruta_camara=ruta_base_descarga+"/"+nombre_camara

        if not os.path.exists(ruta_camara):
            os.mkdir(ruta_camara)

        if not os.path.exists(ruta_camara+"/corruptas"):
            os.mkdir(ruta_camara+"/corruptas")

        if not os.path.exists(ruta_camara+"/status"):
            os.mkdir(ruta_camara+"/status")

        if not os.path.exists(ruta_camara+"/factores"):
            os.mkdir(ruta_camara+"/factores")

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

        hora_america=pytz.timezone('America/Santiago')

        indice=1

        while (True):
            try:
                texto_tiempo=datetime.now(hora_america).strftime('%Y_%m_%d_%H_%M_%S')+"-"+self.nombre_camara+"-"+str(indice)+"-full"
                indice=indice+1

                nombre_imagen=texto_tiempo+".jpg"

                ruta_captura=self.ruta_base_descarga+"/"+self.nombre_camara+"/"+nombre_imagen

                os.system("scrot -d 0 '"+ruta_captura+"'")

                #imagen_descargada = Image.open(io.BytesIO(frame))
                imagen_descargada = Image.open(ruta_captura)
                ancho, alto = imagen_descargada.size
                imagen_descargada.close()

                json_datos = {
                        "nombre_imagen": nombre_imagen, # la ruta base sale desde inferencia
                        "ruta_base":self.ruta_base_descarga+"/"+self.nombre_camara,
                        "ancho":ancho,
                        "alto":alto
                }

                observer.on_next(json_datos)

            except Exception as e:
                logging.exception("Error en Factory Stream Screenshot")
                #logging.error(e)
                print("???")
                print(e)
                self.escribir_error("","","")
                time.sleep(self.tiempo_espera_error)

                self.errores=self.errores+1

                with open(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas",'w') as f:
                    f.write(self.nombre_camara+".exepciones "+str(self.errores)+"\n")
                    f.write(self.nombre_camara+".descarga_fallida "+str(self.descarga_fallida))
        observer.on_completed()
