import pika
import pickle
import configparser
from logging.handlers import RotatingFileHandler

import os

from ultralytics import YOLO

import torch
import logging
import argparse
from PIL import Image,ImageDraw,ImageFont
import shutil
import time
import random

model=None
ruta_boxes=None
nombre_canal=None
ruta_pintadas=None
ruta_raros=None

canal_posible_alerta=None

channel=None
font=None

threshold_deteccion=0.0
threshold_deteccion_estructura_imanes=0.0

def log_setup(path, level):

    if not os.path.isdir("logs/grua/"):
            os.makedirs("logs/grua/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)

def inferir_imagen(ruta_imagen, model):
    global channel
    global ruta_boxes
    global font
    global canal_posible_alerta
    global threshold_deteccion

    solo_nombre = os.path.basename(ruta_imagen)
    solo_nombre = solo_nombre.replace(".jpg", "")

    partes = solo_nombre.split("_")

    parte_entera = int(partes[0])
    parte_fraccional = int(partes[1])

    results = model(ruta_imagen)[0] 

    boxes = results.boxes.data.tolist()
    classes = results.names

    respuesta = []

    hay_trabajador=False
   
    if len(boxes)==0:
        print("sin boxes!!!!")
        random_number = random.randint(1, 100)
        solo_el_nombre = os.path.basename(ruta_imagen)
        
        if random_number > 35:
            shutil.copy(ruta_imagen,ruta_raros+"/"+solo_el_nombre)
        
        
        os.remove(ruta_imagen)
        return

    image = Image.open(ruta_imagen)
    img_width, img_height = image.size

    detecciones=[]

    mensajes_full=[]
    rectangulos_full=[]
    
    for box in boxes:
        class_id = box[-1]
        confidence = box[4]

        clase=str(classes.get(int(class_id)))

        if clase=="estructura_imanes" and confidence<threshold_deteccion_estructura_imanes:
            print("descarto: "+clase)
            print("probabilidad: "+str(confidence))

            random_number = random.randint(1, 100)
            solo_el_nombre = os.path.basename(ruta_imagen)
            if random_number > 35:
                shutil.copy(ruta_imagen,ruta_raros+"/"+solo_el_nombre)

            continue

        elif confidence<threshold_deteccion:
            print("descarto: "+clase)
            print("probabilidad: "+str(confidence))
            continue

        x1=box[0]
        y1=box[1]
        x2=box[2]
        y2=box[3]

        outline="white"
        if clase=="estructura_imanes":
            outline="orange"
        elif clase=="trabajador":
            outline="blue"

        text = clase+": "+str(int(confidence*100))+"%"

        y_mensaje = y1
                
        delta_y=30

        if y1-delta_y>0:
            y_mensaje=y1-delta_y

        position_full=(x1,y_mensaje)

        mensajes_full.append((position_full,text,outline))

        rectangulos_full.append((x1,y1,x2,y2,outline))

        string_deteccion = str(clase)+','+str(int(x1))+","+str(int(y1))+","+str(int(x2))+","+str(int(y2))+","+str(confidence)+","+str(parte_entera)+","+str(parte_fraccional)

        if clase=="trabajador":
            detecciones.append(string_deteccion)
            hay_trabajador=True
        elif clase=="estructura_imanes":
            detecciones.append(string_deteccion)

    if hay_trabajador:
        draw = ImageDraw.Draw(image)

        for mensaje in mensajes_full:
            draw.text(mensaje[0],mensaje[1],fill=mensaje[2],font=font)        

        for rectangulo in rectangulos_full:
            draw.rectangle((rectangulo[0],rectangulo[1],rectangulo[2],rectangulo[3]), outline = rectangulo[4] ,width=5)

    if hay_trabajador:
        solo_nombre = os.path.basename(ruta_imagen)
        ruta_full_pintada=ruta_pintadas+"/"+solo_nombre
        image.save(ruta_full_pintada)

        ruta_full_boxes=ruta_boxes+"/"+solo_nombre+".txt"

        f = open(ruta_full_boxes, "+w")

        for deteccion in detecciones:
            f.write(deteccion+"\n")
    
        f.close() 

        print("alerta en: "+canal_posible_alerta)
 
        channel.basic_publish(exchange='', routing_key=canal_posible_alerta, body=ruta_full_boxes)
    else:
        print("sin trabajador!!!")
        os.remove(ruta_imagen)


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
    global ruta_pintadas
    global ruta_raros
    
    global channel

    global canal_posible_alerta

    global font 
    global threshold_deteccion
    global threshold_deteccion_estructura_imanes
    
    font= ImageFont.truetype("Roboto-Regular.ttf", size=20)
    
    nombre_canal=config["RABBIT_ENTRADA"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_raros=config["PROCESAMIENTO"]["ruta_raros"]
    threshold_deteccion=float(config["PROCESAMIENTO"]["threshold_deteccion"])
    threshold_deteccion_estructura_imanes=float(config["PROCESAMIENTO"]["threshold_deteccion_estructura_imanes"])

    canal_posible_alerta=config["RABBIT_SALIDA"]["canal_posible_alerta"]
    
    model = YOLO(config.get("PESOS","ruta"))
    
    model.model.to(config["CONTEXTO"]["contexto"])

    while True:
        try:
    
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()

            channel.queue_declare(queue=nombre_canal)

            channel.basic_consume(queue=nombre_canal, on_message_callback=callback)

            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            print(f"Connection error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
        except pika.exceptions.ChannelClosedByBroker as e:
            print(f"Channel closed by broker: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(e)
            print(f"Unexpected error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el servidor de procesamiento de gruas')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/grua/servidor_grua.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)
