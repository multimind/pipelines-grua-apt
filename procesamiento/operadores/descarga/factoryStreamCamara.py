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

class FactoryStreamCamara:

    def __init__(self,
        nombre_camara,
        url_camara,
        usuario,
        password,
        tipo_autenticacion,
        ruta_base_descarga,
        tiempo_dormir=3,
        timeout_peticiones=3,
        tiempo_espera_error=5):

        self.nombre_camara=nombre_camara
        self.url_camara=url_camara
        self.usuario=usuario
        self.password=password
        self.tipo_autenticacion=tipo_autenticacion
        self.ruta_base_descarga=ruta_base_descarga
        self.tiempo_dormir=tiempo_dormir
        self.timeout_peticiones=timeout_peticiones
        self.tiempo_espera_error=tiempo_espera_error
        self.errores=0
        self.descarga_fallida=0

        ruta_camara=ruta_base_descarga+"/"+nombre_camara

        if not os.path.exists(ruta_camara):
            os.mkdir(ruta_camara)

        if not os.path.exists(ruta_camara+"/corruptas"):
            os.mkdir(ruta_camara+"/corruptas")

        if not os.path.exists(ruta_camara+"/status"):
            os.mkdir(ruta_camara+"/status")

        if not os.path.exists(ruta_camara+"/status/metricas"):
            os.mkdir(ruta_camara+"/status/metricas")
            
        if not os.path.exists(ruta_camara+"/factores"):
            os.mkdir(ruta_camara+"/factores")

        if not os.path.exists(ruta_camara+"/pintado_trabajador"):
            os.mkdir(ruta_camara+"/pintado_trabajador")

        if not os.path.exists(ruta_camara+"/pintado_maquina"):
            os.mkdir(ruta_camara+"/pintado_maquina")


        

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

        if not os.path.exists(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/"):
            os.mkdir(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/")

        if not os.path.exists(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas"):
            os.mkdir(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas")

        while True:
            try:
                texto_tiempo=datetime.now(hora_america).strftime('%Y_%m_%d_%H_%M_%S')+"-"+self.nombre_camara+"-"+str(indice)+"-full"
                indice=indice+1

                nombre_imagen=texto_tiempo+".jpg"

                ruta_captura=self.ruta_base_descarga+"/"+self.nombre_camara+"/"+nombre_imagen

                if self.tipo_autenticacion=='basic':
                    response = requests.get(self.url_camara, auth = HTTPBasicAuth(self.usuario, self.password),timeout=self.timeout_peticiones)
                elif self.tipo_autenticacion=='digest':
                    response = requests.get(self.url_camara, auth = HTTPDigestAuth(self.usuario, self.password),timeout=self.timeout_peticiones)

                logging.debug("Respuesta Camara de Video: {}".format(response))

                if response.status_code==503:
                    logging.error("ERROR: camara no disponible")
                    #time.sleep(self.tiempo_dormir)
                    time.sleep(10)
                    continue

                if response.status_code==200:

                    file = open(ruta_captura, "wb")
                    file.write(response.content)

                    imagen_descargada = Image.open(io.BytesIO(response.content))
                    ancho, alto = imagen_descargada.size

                    imagen_descargada.close()

                    file.close()

                    json_datos = {
                        "nombre_imagen": nombre_imagen, # la ruta base sale desde inferencia
                        "ruta_base":self.ruta_base_descarga+"/"+self.nombre_camara,
                        "ancho":ancho,
                        "alto":alto,
                        "factores":[],
                        "factor_riesgo":"no"
                    }
                    #print("         ->descarga")
                    observer.on_next(json_datos)
                else:
                    logging.debug("CASO1")
                    nombre_captura=self.ruta_base_descarga+"/"+self.nombre_camara+"/corruptas/"+nombre_imagen

                    file = open(nombre_captura, "wb")
                    file.write(response.content)
                    file.close()

                    self.descarga_fallida=self.descarga_fallida+1

                    if not os.path.exists(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/"):
                        os.mkdir(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/")

                    if not os.path.exists(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas"):
                        os.mkdir(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas")

                    with open(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas/status",'w') as f:
                        f.write(self.nombre_camara+".error_descarga "+str(self.errores)+"\n")
                        f.write(self.nombre_camara+".descarga_fallida "+str(self.descarga_fallida))

                if self.tiempo_dormir==0:
                    continue

                time.sleep(self.tiempo_dormir)

            except ConnectionError as e:
                logging.debug("CASO2")

                time.sleep(self.tiempo_espera_error)
                logging.error(e)
                self.errores=self.errores+1

                with open(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas/status",'w') as f:
                    f.write(self.nombre_camara+".exepciones "+str(self.errores)+"\n")
                    f.write(self.nombre_camara+".descarga_fallida "+str(self.descarga_fallida))

            except requests.exceptions.ReadTimeout as e:
                logging.debug("CASO3")
                time.sleep(self.tiempo_espera_error)
                logging.error(e)
                self.errores=self.errores+1

                with open(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas/status",'w') as f:
                    f.write(self.nombre_camara+".exepciones "+str(self.errores)+"\n")
                    f.write(self.nombre_camara+".descarga_fallida "+str(self.descarga_fallida))

            except Exception as e:
                logging.exception("CASO4")

                self.escribir_error("","","")
                time.sleep(self.tiempo_espera_error)
                logging.error(e)
                self.errores=self.errores+1

                with open(self.ruta_base_descarga+"/"+self.nombre_camara+"/status/metricas/status",'w') as f:
                    f.write(self.nombre_camara+".exepciones "+str(self.errores)+"\n")
                    f.write(self.nombre_camara+".descarga_fallida "+str(self.descarga_fallida))
        observer.on_completed()
