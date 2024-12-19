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
import sys

class FactoryStreamMp4:

    def __init__(self,
        nombre_camara,
        archivo_mp4,
        ruta_base_descarga,
        frame_skip=0,
        tiempo_dormir=1,
        timeout_peticiones=3,
        tiempo_espera_error=5):

        self.nombre_camara=nombre_camara
        self.archivo_mp4=archivo_mp4
        self.ruta_base_descarga=ruta_base_descarga
        self.frame_skip=frame_skip
        self.tiempo_dormir=tiempo_dormir
        self.timeout_peticiones=timeout_peticiones
        self.tiempo_espera_error=tiempo_espera_error
        self.errores=0
        self.descarga_fallida=0

        ruta_camara=ruta_base_descarga+"/"+nombre_camara

        if not os.path.exists(ruta_camara):
            os.mkdir(ruta_camara)

        if not os.path.exists(ruta_camara+"/factores"):
            os.mkdir(ruta_camara+"/factores")

        if not os.path.exists(ruta_camara+"/videos"):
            os.mkdir(ruta_camara+"/videos")

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

    def getFrame(sec):
        vidcap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
        hasFrames,image = vidcap.read()
        if hasFrames:
            cv2.imwrite("image"+str(count)+".jpg", image)     # save frame as JPG file
        return hasFrames

    def leer_datos(self,observer, scheduler):

        hora_america=pytz.timezone('America/Santiago')

        indice=0

        vidcap = cv2.VideoCapture(self.archivo_mp4)

        if (vidcap.isOpened() == False):
            print("no se puede abrir archivo: "+self.archivo_mp4)
            observer.on_completed()
            return

        while (vidcap.isOpened()):
            try:
                datetime_actual=datetime.now(hora_america)

                texto_fecha=datetime_actual.strftime('%Y_%m_%d')
                texto_hora=datetime_actual.strftime('%H_%M_%S_%f')

                texto_tiempo=datetime.now(hora_america).strftime('%Y_%m_%d_%H_%M_%S')+"-"+self.nombre_camara+"-"+str(indice)+"-full"
                indice=indice+1

                nombre_imagen=texto_fecha+'-'+texto_hora+"-"+self.nombre_camara+"-"+str(indice)+".jpg"

                ruta_captura=self.ruta_base_descarga+"/"+self.nombre_camara+"/"+nombre_imagen

                ret, frame = vidcap.read()

                if not self.frame_skip ==0:
                    for z in range(self.frame_skip):
                        ret, frame = vidcap.read()

                if ret == False:
                    break

                cv2.imwrite(ruta_captura,frame)

                imagen_descargada = Image.open(ruta_captura)
                ancho, alto = imagen_descargada.size
                imagen_descargada.close()

                json_datos = {
                        "nombre_imagen": nombre_imagen, # la ruta base sale desde inferencia
                        "ruta_base":self.ruta_base_descarga+"/"+self.nombre_camara,
                        "datetime":datetime_actual,
                        "fecha":texto_fecha,
                        "hora":texto_hora,
                        "ancho":ancho,
                        "alto":alto,
                        "factor_riesgo":"no"
                }

                observer.on_next(json_datos)

                try: 
                    os.remove(ruta_captura)
                except: pass

            except Exception as e:
                logging.exception("Error en Factory Stream mp4")
                #logging.error(e)
                print("???")
                print(e)
                self.escribir_error("","","")
                time.sleep(self.tiempo_espera_error)

                self.errores=self.errores+1

                #with open(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas",'w') as f:
                #    f.write(self.nombre_camara+".exepciones "+str(self.errores)+"\n")
                #    f.write(self.nombre_camara+".descarga_fallida "+str(self.descarga_fallida))
        observer.on_completed()
