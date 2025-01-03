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
import requests

nombre_canal=None

ruta_boxes=None
ruta_tiles=None
ruta_pintadas=None
ruta_frames=None

url_telegram=None
canal_id=None

channel=None
grupos=[]

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
        self.solo_nombre=None

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
    global grupos
    
    f = open(url_box, "r")
    boxes = f.readlines()
    f.close()

    solo_nombre=os.path.basename(url_box)

    partes = solo_nombre.split("_")

    parte_entera=partes[0]
    parte_flotante=partes[1]

    timestamp=reconstruct_timestamp(parte_entera,parte_flotante)

    grupo_despuntes=GrupoDespuntes([],[])
    grupo_despuntes.solo_nombre=solo_nombre

    grupo_despuntes.timestamp=timestamp

    for box in boxes:
        partes=box.split(",")

        clase=partes[0]
        x1=int(partes[1])
        y1=int(partes[2])
        x2=int(partes[3])
        y2=int(partes[4])

        despunte=Despunte(timestamp,clase,x1,y1,x2,y2)
        grupo_despuntes.despuntes.append(despunte)

    grupos.append(grupo_despuntes)


def calcular_despuntes():

    global grupos
    global ruta_pintadas
    global ruta_frames
    global ruta_boxes

    print("numero de despuntes")
    print(len(grupos))

    if len(grupos)<=1:
        return

    grupo_anterior=grupos[-1]
    grupo_actual=grupos[-2]

    grupo_anterior.eliminar=False

    indice_corto_circuito=None
       
    delta=grupo_actual.timestamp-grupo_anterior.timestamp

    segundos=delta.total_seconds()

    if segundos>5:
        print("mas de 5 segundos, se elimina la conexion anterior!")
        grupo_eliminado=grupos.pop(0) # elimina el grupo anterior

        nombre=grupo_eliminado.solo_nombre
        
        os.remove(ruta_boxes+"/"+nombre)

        nombre=nombre.replace(".txt","")

        if os.path.exists(ruta_frames+"/"+nombre):
            os.remove(ruta_frames+"/"+nombre)
        os.remove(ruta_pintadas+"/"+nombre)
        
        return

    hay_conexion=False
        
    for despunte_actual in grupo_actual.despuntes:

        for despunte_anterior in grupo_anterior.despuntes:

            if despunte_actual.conexion == None and despunte_actual.esta_conectado_con(despunte_anterior):
                print("conectados!!!")
                despunte_actual.conexion=despunte_anterior
                #grupo_despuntes.alerta=1
                hay_conexion=True
            else:
                print("desconectado!!!")
        
    if hay_conexion==False:
        print("sin conexiones!")
        grupo_eliminado=grupos.pop(0) # elimina el grupo anterior
        nombre=grupo_eliminado.solo_nombre

        if os.path.exists(ruta_boxes+"/"+nombre):
            os.remove(ruta_boxes+"/"+nombre)

        nombre=nombre.replace(".txt","")

        if os.path.exists(ruta_frames+"/"+nombre):
            os.remove(ruta_frames+"/"+nombre)
        os.remove(ruta_pintadas+"/"+nombre)

        return    

def calcular_alertas():
    global grupos
    global ruta_pintadas

    global url_telegram
    global canal_id
    
    if len(grupos)==2:
        print("ALERTA!!!!")

        grupo=grupos[0]
        solo_nombre=grupo.solo_nombre
        solo_nombre=solo_nombre.replace(".txt","")

        ruta_imagen=ruta_pintadas+"/"+solo_nombre

        print("ruta alerta")
        print(ruta_imagen)

        if os.path.isfile(ruta_imagen):
            archivo = open(ruta_imagen,'rb')
                            
            mensaje="despunte"
                            
            url = url_telegram + "sendPhoto?chat_id=" + canal_id + "&text=" + mensaje

            files={'photo': archivo}
            values={'upload_file' : ruta_pintadas+"/"+solo_nombre, 'mimetype':'image/jpg','caption':mensaje }

            response = requests.post(url,files=files,data=values)

            archivo.close()
            print("enviada!!!!")
        else:
            print("sin envio!")

    
# Callback for handling messages
def callback(ch, method, properties, body):
    global ruta_frames
    print(f"Received: {body.decode()}")

    url_box=body.decode()

    solo_nombre=os.path.basename(url_box)
    solo_nombre=solo_nombre.replace(".txt","")

    if not os.path.isfile(url_box):
        print("archivo no existe: "+url_box)
    else:
        if url_box.endswith(".txt"):
            analizar_box(url_box)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            calcular_despuntes()
            calcular_alertas()

    print("borrando!")
    url_frame=ruta_frames+"/"+solo_nombre

    if os.path.exists(url_frame):
        os.remove(url_frame)

def procesar(config):
    global model
    global nombre_canal
    
    global ruta_boxes
    global ruta_tiles
    global ruta_pintadas
    global channel
    global ruta_frames

    global url_telegram
    global canal_id

    nombre_canal=config["PROCESAMIENTO"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_tiles=config["PROCESAMIENTO"]["ruta_tiles"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_frames=config["PROCESAMIENTO"]["ruta_frames"]
   
    url_telegram=config["TELEGRAM"]["url_telegram"]
    canal_id=config["TELEGRAM"]["canal_id"]
    
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