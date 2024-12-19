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
import time

class FactoryStreamCarpeta:

    def __init__(self,nombre_caso_prueba,ruta_caso_prueba,ruta_base_descarga):
        self.nombre_caso_prueba=nombre_caso_prueba
        self.ruta_caso_prueba=ruta_caso_prueba
        self.ruta_base_descarga=ruta_base_descarga
        self.errores=0

        ruta_carpeta_nueva=ruta_base_descarga+"/"+nombre_caso_prueba
        if not os.path.exists(ruta_carpeta_nueva):
            os.mkdir(ruta_carpeta_nueva)

        if not os.path.exists(ruta_carpeta_nueva+"/factores"):
            os.mkdir(ruta_carpeta_nueva+"/factores")

        if not os.path.exists(ruta_carpeta_nueva+"/videos"):
            os.mkdir(ruta_carpeta_nueva+"/videos")

    def crear_stream(self):
        self.stream= create(self.leer_datos)
        return self.stream

    def leer_datos(self,observer, scheduler):
        start = time.time()

        archivos=os.listdir(self.ruta_caso_prueba)
        archivos.sort()

        # if (len(archivos) == 0):
        #     logging.error("No hay archivos en la carpeta. El proceso se detiene")

        for i in range(len(archivos)):

            imagen = self.ruta_caso_prueba+'/'+archivos[i]

            hora_america=pytz.timezone('America/Santiago')

            datetime_actual=datetime.now(hora_america)

            texto_fecha=datetime_actual.strftime('%Y_%m_%d')
            texto_hora=datetime_actual.strftime('%H_%M_%S_%f')
            
            nombre_imagen=texto_fecha+'-'+texto_hora+"-"+self.nombre_caso_prueba+"-"+str(i)+".jpg"
            print(nombre_imagen)

            ruta_captura=self.ruta_base_descarga+"/"+self.nombre_caso_prueba+"/"+nombre_imagen

            shutil.copyfile(imagen, ruta_captura)

            imagen_descargada = Image.open(imagen)
            ancho, alto = imagen_descargada.size
            imagen_descargada.close()      

            json_datos = {
                        "nombre_imagen": nombre_imagen, # la ruta base sale desde inferencia
                        "ruta_base":self.ruta_base_descarga+"/"+self.nombre_caso_prueba,
                        #"datetime":datetime_actual,
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

        end = time.time()
        print("tiempo transcurrido lectura_imagen: %f" % (end - start))
        observer.on_completed()