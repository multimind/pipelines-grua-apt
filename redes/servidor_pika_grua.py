import pika
import pickle
import configparser
from logging.handlers import RotatingFileHandler

import os

from ultralytics import YOLO

import torch
import logging
import argparse

model=None
ruta_boxes=None
nombre_canal=None

def log_setup(path, level):

    if not os.path.isdir("logs/grua/"):
            os.makedirs("logs/grua/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
    
def inferir_imagen(nombre_imagen, model):
    global ruta_boxes
    solo_nombre = os.path.basename(nombre_imagen)
    solo_nombre = solo_nombre.replace(".jpg", "")

    results = model(nombre_imagen)[0] 
    boxes = results.boxes.data.tolist()
    classes = results.names

    respuesta = []

    if len(boxes)==0:

        f = open(ruta_boxes+"/"+solo_nombre, "+w")
        f.write("")
        f.close()
        os.remove(nombre_imagen)

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
    
    ch.basic_ack(delivery_tag=method.delivery_tag)
 
def procesar(config):
    global model
    global ruta_boxes
    global nombre_canal

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    nombre_canal=config["PROCESAMIENTO"]["nombre_canal"]

    model = YOLO(config.get("PESOS","ruta"))
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=nombre_canal)

    channel.basic_consume(queue=nombre_canal, on_message_callback=callback)

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

