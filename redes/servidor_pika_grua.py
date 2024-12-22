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

model=None

def log_setup(path, level):

    if not os.path.isdir("logs/grua/"):
            os.makedirs("logs/grua/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
    
def inferir_imagen(nombre_imagen, model):

    solo_nombre = os.path.basename(nombre_imagen)

    results = model(nombre_imagen)[0] 
    boxes = results.boxes.data.tolist()
    classes = results.names

    respuesta = []

    ruta_boxes="/data/pipelines-grua-apt/captura"

    if len(boxes)==0:

        f = open(ruta_boxes+"/"+solo_nombre, "+w")
        f.write("")
        f.close()
        return

    seleccionados=[]
    
    for box in boxes:
        class_id = box[-1]
        res = str(classes.get(int(class_id)))+':'+str(int(box[0]))+","+str(int(box[1]))+","+str(int(box[2]))+","+str(int(box[3]))

        confidence = box[4]

        if confidence>0.8:
            seleccionados.append(res)

    f = open(ruta_boxes+"/"+solo_nombre, "+w")
       
    for seleccionado in seleccionados:
        f.write(seleccionado+"\n")
    
    f.close() 
    
# Callback for handling messages
def callback(ch, method, properties, body):
    global model
    print(f"Received: {body.decode()}")

    url_frame=body.decode()

    if not os.path.isfile(url_frame):
        print("archivo no existe: "+url_frame)
    else:
        inferir_imagen(url_frame, model)
 
def procesar(config):
    global model
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

