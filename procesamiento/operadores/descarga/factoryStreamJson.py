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
import ast
import pickle

class FactoryStreamJson:

    def __init__(self, ruta_carpeta):
        
        if not os.path.exists(ruta_carpeta):
            os.mkdir(ruta_carpeta)
            
        self.ruta_carpeta = ruta_carpeta
        self.archivos_procesados = set(os.listdir(ruta_carpeta))

    def crear_stream(self):
        self.stream = create(self.leer_datos)
        return self.stream

    def leer_datos(self,observer, scheduler):
        try:
            while True:
                archivos_actuales = set(os.listdir(self.ruta_carpeta))
                nuevos_archivos = archivos_actuales - self.archivos_procesados

                for file_name in nuevos_archivos:
                    archivo = os.path.join(self.ruta_carpeta, file_name)
                    print(f"Nuevo archivo detectado: {file_name}")

                    with open(archivo, 'rb') as file:
                        loaded_data_str = pickle.load(file)
                        
                    os.remove(archivo)

                    observer.on_next(loaded_data_str)

                time.sleep(1)

        except Exception as e:
            observer.on_error(e)