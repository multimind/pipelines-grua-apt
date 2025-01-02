import pika
import pickle
import configparser
from logging.handlers import RotatingFileHandler

import os

from ultralytics import YOLO

import torch
import logging
import argparse
from PIL import Image,ImageDraw

model=None
nombre_canal=None

ruta_boxes=None
ruta_tiles=None
ruta_pintadas=None

channel=None
 
def save_image_patches(image_path, patch_size, output_dir,model,parte_entera,parte_fraccional):
    global channel
    image = Image.open(image_path)
 
    img_width, img_height = image.size

    os.makedirs(output_dir, exist_ok=True)

    patch_width, patch_height = patch_size
    count = 0

    hay_despunte=False

    detecciones=[]

    for y in range(0, img_height, patch_height):
        for x in range(0, img_width, patch_width):
           
            coordenadas_crop = (x, y, x + patch_width, y + patch_height)
            patch = image.crop(coordenadas_crop)

            results = model(patch)[0] 
            classes = results.names

            boxes = results.boxes.data.tolist()

            draw = ImageDraw.Draw(patch)
            
            for box in boxes:
                class_id = box[-1]
                confidence = box[4]

                if confidence<0.8:
                    continue

                clase=str(classes.get(int(class_id)))

                x1=box[0]
                y1=box[1]
                x2=box[2]
                y2=box[3]

                if y1 < 250 and y2 < 250:
                    continue

                string_deteccion = str(clase)+','+str(int(x1))+","+str(int(y1))+","+str(int(x2))+","+str(int(y2))+","+str(parte_entera)+","+str(parte_fraccional)
                detecciones.append(string_deteccion)

                outline="white"
                if clase=="despunte":
                    outline="yellow"
                elif clase=="trabajador":
                    outline="blue"
                
                draw.rectangle((x1,y1,x2,y2), outline = outline ,width=5)

                hay_despunte=True
            
            image.paste(patch, coordenadas_crop)

    if hay_despunte:
        print("CON despunte: "+image_path)
        solo_nombre = os.path.basename(image_path)

        ruta_full_pintada=ruta_pintadas+"/"+solo_nombre
        image.save(ruta_full_pintada)

        ruta_full_boxes=ruta_boxes+"/"+solo_nombre+".txt"

        f = open(ruta_full_boxes, "+w")

        for deteccion in detecciones:
            f.write(deteccion+"\n")
    
        f.close() 

        channel.basic_publish(exchange='', routing_key="posible_alerta_despuntes", body=ruta_full_boxes)
    else:
        print("sin despunte: "+image_path)
        os.remove(image_path)
 
def log_setup(path, level):

    if not os.path.isdir("logs/despuntes/"):
            os.makedirs("logs/despuntes/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
    
def inferir_imagen(nombre_imagen, model):
    global ruta_boxes
    solo_nombre = os.path.basename(nombre_imagen)
    solo_nombre = solo_nombre.replace(".jpg", "")

    partes = solo_nombre.split("_")

    parte_entera = int(partes[0])
    parte_fraccional = int(partes[1])

    patch_size = (640, 640)  
    nombres_tiles=save_image_patches(nombre_imagen,patch_size,ruta_tiles,model, parte_entera, parte_fraccional)
    
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
    global nombre_canal
    
    global ruta_boxes
    global ruta_tiles
    global ruta_pintadas
    global channel

    nombre_canal=config["PROCESAMIENTO"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_tiles=config["PROCESAMIENTO"]["ruta_tiles"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    
    model = YOLO(config.get("PESOS","ruta"))
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=nombre_canal)

    channel.basic_consume(queue=nombre_canal, on_message_callback=callback)

    channel.start_consuming()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el servidor de procesamiento de despuntes')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/despuntes/servidor_despuntes.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)

