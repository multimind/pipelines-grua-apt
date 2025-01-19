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
import random 

model=None
nombre_canal=None

ruta_boxes=None
ruta_tiles=None
ruta_pintadas=None
ruta_trabajadores=None
ruta_crops=None

canal_posible_alerta=None
canal_alerta_despunte_grande=None

channel=None
 
def save_image_patches(image_path, patch_size, output_dir,model,parte_entera,parte_fraccional):
    global channel
    global ruta_trabajadores
    global ruta_pintadas
    global ruta_crops
    global canal_posible_alerta
    global canal_alerta_despunte_grande

    image = Image.open(image_path)
 
    img_width, img_height = image.size

    os.makedirs(output_dir, exist_ok=True)

    patch_width, patch_height = patch_size
    count = 0

    hay_despunte=False
    hay_despunte_grande=False
    hay_trabajador=False

    detecciones=[]

    mensajes_full=[]
    rectangulos_full=[]
    indice_crop=0

    for y in range(0, img_height, patch_height):
        for x in range(0, img_width, patch_width):
           
            coordenadas_crop = (x, y, x + patch_width, y + patch_height)
            patch = image.crop(coordenadas_crop)

            results = model(patch)[0] 
            classes = results.names

            boxes = results.boxes.data.tolist()

            #draw = ImageDraw.Draw(patch)
            
            for box in boxes:
                class_id = box[-1]
                confidence = box[4]
                
                clase=str(classes.get(int(class_id)))

                if confidence<0.75:
                    print("descarto: "+clase)
                    print("probabilidad: "+str(confidence))
                    continue

                x1=box[0]
                y1=box[1]
                x2=box[2]
                y2=box[3]

                random_number = random.randint(1, 100)

                if random_number>0.7:
                    solo_nombre = os.path.basename(image_path)
                    cropped_img = image.crop((x1,y1,x2,y2))
                    cropped_img.save(ruta_crops+"/"+solo_nombre+"_"+str(indice_crop)+".jpg")

                    delta=150
                    x1_expandido=x1-delta

                    if x1_expandido<0:
                        x1_expandido=0

                    x2_expandido=x2+delta

                    if x2_expandido>=patch_width:
                        x2_expandido=patch_width-1

                    y1_expandido=y1-delta
                    if y1_expandido<0:
                        y1_expandido=0

                    y2_expandido=y2+delta

                    if y2_expandido>=patch_height:
                        y2_expandido=patch_height-1

                    cropped_img = image.crop((x1_expandido,y1_expandido,x2_expandido,y2_expandido))
                    cropped_img.save(ruta_crops+"/expandida_"+solo_nombre+"_"+str(indice_crop)+".jpg")

                    indice_crop=indice_crop+1

                string_deteccion = str(clase)+','+str(int(x1))+","+str(int(y1))+","+str(int(x2))+","+str(int(y2))+","+str(parte_entera)+","+str(parte_fraccional)
               
                print("clase!")
                print(clase)
                outline="white"
                if clase=="despunte":
                    outline="yellow"
                elif clase=="trabajador":
                    outline="blue"
                elif clase=="despunte-grande":
                    outline="red"

                text = clase+": "+str(int(confidence*100))+"%"
                font = ImageFont.truetype("Roboto-Regular.ttf", size=20)

                y_mensaje = y1
                
                delta_y=30

                if y1-delta_y>0:
                    y_mensaje=y1-delta_y

                position = (x1, y_mensaje)  

                position_full=(x1+x,y_mensaje+y)

                mensajes_full.append((position_full,text,outline))

                rectangulos_full.append((x+x1,y+y1,x+x2,y+y2,outline))

                if clase=="despunte":
                    detecciones.append(string_deteccion)
                    hay_despunte=True
                elif clase=="trabajador":
                    hay_trabajador=True
                elif clase=="despunte-grande":
                    hay_despunte_grande=True
                    detecciones.append(string_deteccion)
            
            #image.paste(patch, coordenadas_crop)

    #pinta en coordenadas globales    
    if hay_despunte or hay_despunte_grande or hay_trabajador:
        draw = ImageDraw.Draw(image)

        for mensaje in mensajes_full:
            draw.text(mensaje[0],mensaje[1],fill=mensaje[2],font=font)        

        for rectangulo in rectangulos_full:
            draw.rectangle((rectangulo[0],rectangulo[1],rectangulo[2],rectangulo[3]), outline = rectangulo[4] ,width=5)

    if hay_despunte_grande:
        print("CON despunte: "+image_path)
        solo_nombre = os.path.basename(image_path)

        ruta_full_pintada=ruta_pintadas+"/"+solo_nombre
        image.save(ruta_full_pintada)
    
        channel.basic_publish(exchange='', routing_key=canal_alerta_despunte_grande, body=ruta_full_pintada)

    elif hay_despunte:
        print("CON despunte: "+image_path)
        solo_nombre = os.path.basename(image_path)

        ruta_full_pintada=ruta_pintadas+"/"+solo_nombre
        image.save(ruta_full_pintada)

        ruta_full_boxes=ruta_boxes+"/"+solo_nombre+".txt"

        f = open(ruta_full_boxes, "+w")

        for deteccion in detecciones:
            f.write(deteccion+"\n")
    
        f.close() 
 
        channel.basic_publish(exchange='', routing_key=canal_posible_alerta, body=ruta_full_boxes)

    elif hay_trabajador:
        #lanzar alerta para el otro procesamiento de trabajadores en zona
        solo_nombre = os.path.basename(image_path)
        ruta_full_trabajadores=ruta_trabajadores+"/"+solo_nombre
        #mueve la original a otra ruta
        #shutil.move(image_path,ruta_full_trabajadores)
        os.remove(image_path)
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
    global ruta_crops
    global ruta_trabajadores
    global channel

    global canal_posible_alerta
    global canal_alerta_despunte_grande

    nombre_canal=config["RABBIT_ENTRADA"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_tiles=config["PROCESAMIENTO"]["ruta_tiles"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_trabajadores=config["PROCESAMIENTO"]["ruta_trabajadores"]
    ruta_crops=config["PROCESAMIENTO"]["ruta_crops"]

    canal_posible_alerta=config["RABBIT_SALIDA"]["canal_posible_alerta"]
    canal_alerta_despunte_grande=config["RABBIT_SALIDA"]["canal_alerta_despunte_grande"]
    
    model = YOLO(config.get("PESOS","ruta"))
    
    model.model.to(config["CONTEXTO"]["contexto"])
    
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

