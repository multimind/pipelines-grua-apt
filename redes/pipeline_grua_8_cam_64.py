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
ruta_pintadas=None
ruta_frames=None
sector=None
ruta_crops=None

url_telegram=None
canal_id=None

channel=None
grupos=[]

estado="SIN_TRABAJADOR"

primer_grupo=None
segundo_grupo=None

def enviar_alerta(ruta_imagen):

    try:

        if os.path.isfile(ruta_imagen):
            archivo = open(ruta_imagen,'rb')
                                
            mensaje="ingreso trabajador"
                                
            url = url_telegram + "/sendPhoto?chat_id=" + canal_id + "&text=" + mensaje

            files={'photo': archivo}
            values={'upload_file' : ruta_imagen, 'mimetype':'image/jpg','caption':mensaje }

            response = requests.post(url,files=files,data=values)

            archivo.close()

        else:
            print("sin envio")

    except Exception as e:
        print("ERROR EN ENVIO TELEGRAM")
        print(e)

def reconstruct_timestamp(integer_part, fractional_part):
    timestamp = float(integer_part) + int(fractional_part) / 1_000_000
    reconstructed_datetime = datetime.datetime.fromtimestamp(timestamp)
    return reconstructed_datetime

def log_setup(path, level):

    if not os.path.isdir("logs/pipeline_grua8/"):
            os.makedirs("logs/pipeline_grua8/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
     
# Callback for handling messages
def callback(ch, method, properties, body):
    global ruta_frames
    global estado
    global primer_grupo

    print(f"Received: {body.decode()}")

    url_box=body.decode()
    print(url_box)
    
    #os.remove(url_frame)

    #/data/runtime_camara1/boxes/1738504260_121319_1920_1080.jpg.txt;sin
    partes=url_box.split(";")

    ruta_imagen=partes[0].replace(".txt","")

    if estado=="SIN_TRABAJADOR":

        if partes[1]=="sin":
            if os.path.isfile(partes[0]):
                os.remove(partes[0])

            if os.path.isfile(ruta_imagen):
                os.remove(ruta_imagen)

        elif partes[1]=="con":

            estado="CON_TRABAJADOR"
            enviar_alerta(ruta_imagen)
    else:

        if partes[1]=="sin":
            os.remove(partes[0])
            os.remove(ruta_imagen)
            estado="SIN_TRABAJADOR"

            if os.path.isfile(partes[0]):
                os.remove(partes[0])

            if os.path.isfile(ruta_imagen):
                os.remove(ruta_imagen)

        elif partes[1]=="con":
            pass

def procesar(config):
    global model
    global nombre_canal
    
    global ruta_boxes
    global channel
    global ruta_frames
    global sector

    global url_telegram
    global canal_id

    nombre_canal=config["RABBIT_ENTRADA"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_frames=config["PROCESAMIENTO"]["ruta_frames"]
    sector=config["PROCESAMIENTO"]["sector"]
   
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

    log_setup("logs/pipeline_grua8/servidor_camara_64.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)