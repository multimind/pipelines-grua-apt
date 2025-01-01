import pika
import pickle
import configparser
from logging.handlers import RotatingFileHandler

import os

import torch
import logging
import argparse
from PIL import Image,ImageDraw
import datetime
import math

nombre_canal=None

ruta_boxes=None
ruta_tiles=None
ruta_pintadas=None

channel=None
detecciones_despuntes=[]

def reconstruct_timestamp(integer_part, fractional_part):
    timestamp = float(integer_part) + int(fractional_part) / 1_000_000
    reconstructed_datetime = datetime.datetime.fromtimestamp(timestamp)
    return reconstructed_datetime

class Despunte:
    def __init__(self, timestamp,clase,x1,y1,x2,y2):
        self.timestamp=timestamp
        self.clase=clase
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
        self.conexion=None

    def centro(self):

        cx=self.x1+int((self.x2-self.x1)/2.0)
        cy=self.y1+int((self.y2-self.y1)/2.0)

        return (cx,cy)

    def esta_conectado_con(self,anterior):
        cx,cy=self.centro()

        anterior_cx,anterior_cy=anterior.centro()

        distancia = math.sqrt((cx - anterior_cx)**2 + (cy - anterior_cy)**2)

        print("distancia")
        print(distancia)

        if distancia >30:
            return False

        if cy>anterior_cy:
            return False

        return True

class GrupoDespuntes:
    def __init__(self, despuntes, timestamp):
        self.despuntes=despuntes
        self.timestamp=timestamp
        self.eliminar=False
        self.conexion=None
        self.alerta=0

def log_setup(path, level):

    if not os.path.isdir("logs/despuntes/"):
            os.makedirs("logs/despuntes/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
    
def analizar_box(url_box):
    global ruta_boxes
    global detecciones_despuntes
    
    print("box!")
    print(url_box)

    f = open(url_box, "r")
    boxes = f.readlines()
    f.close()

    print(boxes)

    solo_nombre=os.path.basename(url_box)

    partes = solo_nombre.split("_")

    parte_entera=partes[0]
    parte_flotante=partes[1]

    timestamp=reconstruct_timestamp(parte_entera,parte_flotante)

    grupo_despuntes=GrupoDespuntes([],[])

    grupo_despuntes.timestamp=timestamp

    for box in boxes:
        print(box.strip())
        partes=box.split(",")

        clase=partes[0]
        x1=int(partes[1])
        y1=int(partes[2])
        x2=int(partes[3])
        y2=int(partes[4])

        despunte=Despunte(timestamp,clase,x1,y1,x2,y2)
        grupo_despuntes.despuntes.append(despunte)

    detecciones_despuntes.append(grupo_despuntes)


def calcular_despuntes():

    global detecciones_despuntes

    print("numero de despuntes")
    print(len(detecciones_despuntes))

    if len(detecciones_despuntes)<=1:
        return

    anterior=None

    i=0

    for grupo_despuntes in detecciones_despuntes:
        grupo_despuntes.eliminar=False

    indice_corto_circuito=None

    # marca los despuntes muy antiguos
    for grupo_despuntes in reversed(detecciones_despuntes):
    
        if i==0:
            anterior=grupo_despuntes
            i=i+1
            continue
        
        delta=anterior.timestamp-grupo_despuntes.timestamp
        segundos=delta.total_seconds()

        if segundos>5:
            anterior.eliminar=True
            indice_corto_circuito=i+1
            break
        
        anterior=grupo_despuntes
        i=i+1

    #borra los despuntes antiguos
    if not indice_corto_circuito==None:
        detecciones_despuntes=detecciones_despuntes[:indice_corto_circuito]

    print("cuatos quedan")
    print(len(detecciones_despuntes))

    grupo_anterior=None
    i=0

    hay_conexion=False

    for grupo_despuntes in reversed(detecciones_despuntes):
    
        if i==0:
            grupo_anterior=grupo_despuntes
            i=i+1
            continue
        
        for despunte_actual in grupo_despuntes.despuntes:

            for despunte_anterior in grupo_anterior.despuntes:

                if despunte_actual.conexion == None and despunte_actual.esta_conectado_con(despunte_anterior):
                    print("conectados!!!")
                    despunte_actual.conexion=despunte_anterior
                    grupo_despuntes.alerta=1
                    hay_conexion=True
                else:
                    print("desconectado!!!")
        
        i=i+1


def calcular_alertas():
    global detecciones_despuntes

    suma_alertas=0

    for grupo_despuntes in reversed(detecciones_despuntes):
        suma_alertas=suma_alertas+grupo_despuntes.alerta

    print("suma alertas")
    print(suma_alertas)
        

# Callback for handling messages
def callback(ch, method, properties, body):
    print(f"Received: {body.decode()}")

    url_box=body.decode()

    if not os.path.isfile(url_box):
        print("archivo no existe: "+url_box)
    else:
        if url_box.endswith(".txt"):
            analizar_box(url_box)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            calcular_despuntes()
            calcular_alertas()

def procesar(config):
    global model
    global nombre_canal
    
    global ruta_boxes
    global ruta_tiles
    global ruta_pintadas
    global channel

    nombre_canal=config["PROCESAMIENTO"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_tiles=config["PROCESAMIENTO"]["ruta_tiles"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=nombre_canal)

    channel.basic_consume(queue=nombre_canal, on_message_callback=callback)

    channel.start_consuming()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el pipeline de procesamiento de despuntes')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/pipeline_despuntes/servidor_despuntes.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)