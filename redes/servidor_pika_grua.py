import pika
import pickle
import configparser
from logging.handlers import RotatingFileHandler

import os
import cv2

from ultralytics import YOLO

import torch
import logging
import argparse

global model

def log_setup(path, level):

    if not os.path.isdir("logs/grua/"):
            os.makedirs("logs/grua/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
    
def inferir_imagen(nombre_imagen, model):

    results = model(nombre_imagen)[0] 
    boxes = results.boxes.data.tolist()
    classes = results.names

    respuesta = []

    if len(boxes) > 0:

        for box in boxes:
            class_id = box[-1]
            res = str(classes.get(int(class_id)))+':'+str(int(box[0]))+","+str(int(box[1]))+","+str(int(box[2]))+","+str(int(box[3]))

            confidence = box[4]

            if confidence>0.8:
                respuesta.append(res)

        if respuesta==[]:
            return [False,respuesta]

        return [True, respuesta]

    else:
        return [False, respuesta]

# Callback for handling messages
def callback(ch, method, properties, body):
    print(f"Received: {body.decode()}")

    url_frame=body.decode()

    inferir_imagen(url_frame, model):
 
def procesar(config):

    model = YOLO(config.get("PESOS","ruta"))
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='grua_apt')

    channel.basic_consume(queue='grua_apt', on_message_callback=callback)

    channel.start_consuming()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el servidor de procesamiento de gruas')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/grua/servidor_grua.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)

