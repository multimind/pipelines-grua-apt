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
fecha_anterior=datetime.datetime.now()

url_telegram=None
canal_id=None

channel=None
grupos=[]

def reconstruct_timestamp(integer_part, fractional_part):
    timestamp = float(integer_part) + int(fractional_part) / 1_000_000
    reconstructed_datetime = datetime.datetime.fromtimestamp(timestamp)
    return reconstructed_datetime

def log_setup(path, level):

    if not os.path.isdir("logs/despuntes/"):
            os.makedirs("logs/despuntes/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
 
def enviar_alertas(url_despunte):
    global ruta_pintadas
    global url_telegram
    global canal_id
    global fecha_anterior
    
    print("ALERTA!!!!")

    solo_nombre=os.path.basename(url_despunte)

    partes = solo_nombre.split("_")

    parte_entera=partes[0]
    parte_flotante=partes[1]

    timestamp=datetime.datetime.now()

    elapsed_time=timestamp-fecha_anterior

    segundos_transcurridos=elapsed_time.total_seconds()

    if segundos_transcurridos<60:
        fecha_anterior=datetime.datetime.now()
        print("descartado por muy cercanos!!!")
        print(segundos_transcurridos)
    elif os.path.isfile(url_despunte):
        archivo = open(url_despunte,'rb')

        print("url")
        mensaje="despunte grande"
                            
        url = url_telegram + "/sendPhoto?chat_id=" + canal_id + "&text=" + mensaje

        files={'photo': archivo}
        values={'upload_file' : url_despunte, 'mimetype':'image/jpg','caption':mensaje }

        response = requests.post(url,files=files,data=values)

        archivo.close()
        print("enviada!!!!")
    else:
        print("sin envio!")

    
# Callback for handling messages
def callback(ch, method, properties, body):
    global ruta_frames
    print(f"Received: {body.decode()}")

    url_despunte=body.decode()

    if not os.path.isfile(url_despunte):
        print("archivo no existe: "+url_despunte)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        if url_despunte.endswith(".jpg"):
            enviar_alertas(url_despunte)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
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

    parser = argparse.ArgumentParser(description='Inicia el pipeline de procesamiento de despuntes grandes')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/pipeline_despuntes_grande/servidor_despuntes.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)