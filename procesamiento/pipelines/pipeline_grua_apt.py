from rx.subject import Subject
from rx import operators as ops
from rx import interval
import numpy as np
import cv2

import sys
sys.path.append('../')
sys.path.append('/home/multimind/sm/safetymind-aceros-arequipa/procesamiento')

from operadores.descarga import factoryStreamRtsp
from operadores.descarga import factoryStreamMp4
from operadores.descarga import factoryStreamCarpeta
from operadores.descarga import factoryStreamPullCarpeta
from operadores.debug import print_observer
from operadores.integracion import socket_red_neuronal
from operadores.medicion import calcular_areas_gruas
from operadores.dibujo import pintar_grua_apt
from operadores.deteccion import trabajador_en_zona_grua
from operadores.debug import guardar_raros
from operadores.alerta import operador_generar_alerta
from operadores.limpiar import operador_limpiar
from operadores.limpiar import operador_limpiar_delay
from operadores.transformar_datos import convertir_boxes_json
from util import configuracion_logger
import logging
import configparser
import pytz
from util import util_poligonos

from joblib import dump, load
from paramiko import SSHClient
import paramiko
from datetime import datetime
import argparse
import os

def procesar(config):

    nombre_camara="101"
    ambiente="local"

    configuracion_logger.configurar(nombre_camara,logging.DEBUG, False)

    factory_camara=None

    if config["STREAM"]["tipo"]=="rtsp":

        factory_camara= factoryStreamRtsp.FactoryStreamRtsp(nombre_camara,
            config["CAMARA"]["url"],
            config["DESCARGA"]["ruta_descarga"], 
            config.getint("CAMARA","frameskip"))
    elif config["STREAM"]["tipo"]=="mp4":
        factory_camara= factoryStreamMp4.FactoryStreamMp4(nombre_camara,
            config["VIDEO"]["ruta_video"],
            config["DESCARGA"]["ruta_descarga"])
 
    elif config["STREAM"]["tipo"]=="carpeta":
        factory_camara= factoryStreamCarpeta.FactoryStreamCarpeta(nombre_camara,
            config["STREAM_CARPETA"]["ruta_carpeta"],
            config["DESCARGA"]["ruta_descarga"])
    elif config["STREAM"]["tipo"]=="pull_carpeta":
        factory_camara= factoryStreamPullCarpeta.FactoryStreamPullCarpeta(nombre_camara,
            config["PULL_CARPETA"]["ruta_carpeta"])

    stream=factory_camara.crear_stream()

    hora_america = pytz.timezone('America/Santiago')

    variables_globales={"cantidad_alertas":0}
    
    #pika_red_neuronal.procesar_imagen(nombre_canaral,"detecciones",None, "detectron2"),
    #socket_red_neuronal.procesarImagen(config["RED_DETECCION_GRUA"]["ip"],int(config["RED_DETECCION_GRUA"]["puerto"]),"detecciones",None, "detectron2"),
      
    cola_borrar=[]  
    delay=3
       
    compuesto=stream.pipe(
        convertir_boxes_json.convertir(),
        calcular_areas_gruas.calcular("estructura_imanes",variables_globales,config.getint("GRUA","delta_x"),config.getint("GRUA","delta_y")),
        trabajador_en_zona_grua.detectar(variables_globales),
        pintar_grua_apt.pintar(variables_globales,config["DESCARGA"]["pintados"]),
        #operador_generar_alerta.alerta_imagen(variables_globales,config["TELEGRAM"]["url"],config["TELEGRAM"]["chat_id"],config["DESCARGA"]["pintados"]),
        guardar_raros.guardar(variables_globales,config["DESCARGA"]["raros"]),
        operador_limpiar_delay.limpiar(variables_globales,config["DESCARGA"]["pintados"],cola_borrar,delay)
    )

    printObserver=print_observer.PrintObserver()

    compuesto.subscribe(printObserver)

if __name__ == "__main__":
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

    parser = argparse.ArgumentParser(description="Archivo de configu")
    parser.add_argument("ruta_archivo_configuracion")
    
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.ruta_archivo_configuracion)

    procesar(config)
