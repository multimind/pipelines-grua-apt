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

    url_image=body.decode()
    print(url_image)


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