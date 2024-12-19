import pytz
import requests
from datetime import datetime
from rx import create
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
import time
import os
from PIL import Image,ImageDraw,ImageStat
import logging
import shutil

class FactoryTestImagen:

    def __init__(self,nombre_caso_prueba,ruta_caso_prueba,ruta_base_descarga):
        self.nombre_caso_prueba=nombre_caso_prueba
        self.ruta_caso_prueba=ruta_caso_prueba
        self.ruta_base_descarga=ruta_base_descarga
        self.errores=0

        ruta_camara=ruta_base_descarga+"/"+nombre_caso_prueba
        if not os.path.exists(ruta_camara):
            os.mkdir(ruta_camara)

    def crear_stream(self):
        self.stream= create(self.leer_datos)
        return self.stream

    def leer_datos(self,observer, scheduler):

        hora_america=pytz.timezone('America/Santiago')

        indice=1

        texto_fecha=datetime.now(hora_america).strftime('%Y_%m_%d')
        texto_hora=datetime.now(hora_america).strftime('%H_%M_%S_%f')

        nombre_imagen=texto_fecha+'-'+texto_hora+"-"+self.nombre_caso_prueba+"-"+str(indice)+".jpg"

        ruta_captura=self.ruta_base_descarga+"/"+self.nombre_caso_prueba+"/"+nombre_imagen

        shutil.copyfile(self.ruta_caso_prueba, ruta_captura)

        imagen_descargada = Image.open(self.ruta_caso_prueba)
        ancho, alto = imagen_descargada.size
        imagen_descargada.close()

        

        json_datos = {
                "nombre_imagen": nombre_imagen, # la ruta base sale desde inferencia
                "ruta_base":self.ruta_base_descarga+"/"+self.nombre_camara,
                "fecha":texto_fecha,
                "hora":texto_hora,
                "ancho":ancho,
                "alto":alto,
                "factores":[]
        }

        observer.on_next(json_datos)

        try: 
            os.remove(ruta_captura)
        except: pass

        observer.on_completed()
