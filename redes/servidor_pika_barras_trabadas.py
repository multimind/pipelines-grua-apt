import pika
import pickle
import configparser
from logging.handlers import RotatingFileHandler
import cv2
import os

from ultralytics import YOLO

import torch
import logging
import argparse
from PIL import Image,ImageDraw,ImageFont
import shutil
import random 
import numpy as np
from scipy.interpolate import interp1d
from PIL import Image
import numpy as np
from scipy.interpolate import interp1d
from PIL import Image
import requests

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

zona1=None
zona2=None
zona3=None

url_telegram=None
canal_id=None

font = ImageFont.truetype("Roboto-Regular.ttf", size=20)

curve = [
            (0, 0), (132,0), (172, 255),(255, 255)
        ]

estado="NORMAL"

def pil_to_cv2(pil_image):
    """Convert a PIL image to an OpenCV image."""
    cv_image = np.array(pil_image)  # Convert PIL image to NumPy array
    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR
    return cv_image

def apply_color_curve_pillow(image, curve):
    """
    Apply a custom color curve to the RGB channels of the image using Pillow.
    :param image: Pillow Image object
    :param curve: List of (x, y) pairs defining the color curve
    :return: Modified Image object
    """
    # Extract the x and y values from the curve
    x_vals, y_vals = zip(*curve)

    # Interpolate the curve to create a LUT (Look-Up Table) for pixel mapping
    lut = np.interp(np.arange(256), x_vals, y_vals).clip(0, 255).astype(np.uint8)

    # Split image into R, G, and B channels
    r, g, b = image.split()

    # Apply LUT to each channel
    r = r.point(lambda i: lut[i])
    g = g.point(lambda i: lut[i])
    b = b.point(lambda i: lut[i])

    # Merge channels back and return
    return Image.merge("RGB", (r, g, b))

class Zona:
    def __init__(self, x1,y1,ancho,alto):
        self.x1=x1
        self.y1=y1
        self.ancho=ancho
        self.alto=alto
 
def log_setup(path, level):

    if not os.path.isdir("logs/barras_trabadas/"):
            os.makedirs("logs/barras_trabadas/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
    
def enviar_alerta(ruta_imagen):
    solo_nombre = os.path.basename(ruta_imagen)
    
    archivo = open(ruta_imagen,'rb')
                                
    mensaje="barra trabada"
                                
    url = url_telegram + "/sendPhoto?chat_id=" + canal_id + "&text=" + mensaje

    files={'photo': archivo}
    values={'upload_file' : ruta_pintadas+"/"+solo_nombre, 'mimetype':'image/jpg','caption':mensaje }

    response = requests.post(url,files=files,data=values)

    archivo.close()
                
    print("enviada!!!!")
    
def inferir_imagen(ruta_imagen, model,parte_entera,parte_fraccional,zona):
    global ruta_boxes
    global ruta_crops
    global estado
    global ruta_pintadas
    global font
    
    print(ruta_imagen)
    
    image = Image.open(ruta_imagen)
    
    coordenadas_crop = (zona.x1, zona.y1, zona.x1 + zona.ancho, zona.y1 + zona.alto)
    crop_zona1= image.crop(coordenadas_crop)
    
    curve = [(0, 0), (132,0), (172, 255),(255, 255)]
    
    crop_filtrado=apply_color_curve_pillow(crop_zona1,curve)
    
    solo_nombre = os.path.basename(ruta_imagen)
    solo_nombre = solo_nombre.replace(".jpg", "")

    print("ruta crops")
    print(ruta_crops)
    #partes = solo_nombre.split("_")
    #crop_filtrado.save(ruta_crops+"/"+solo_nombre+".zona1.jpg")
    
    results = model(crop_filtrado)[0] 
    classes = results.names

    boxes = results.boxes.data.tolist()
    detecciones=[]
    mensajes_full=[]
    rectangulos_full=[]
    
    hay_barra_trabada=False
    
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

        string_deteccion = str(clase)+','+str(int(x1))+","+str(int(y1))+","+str(int(x2))+","+str(int(y2))+","+str(parte_entera)+","+str(parte_fraccional)
               
        print("clase!")
        print(clase)
        outline="white"
        
        if clase=="barra horizontal":
            outline="green"
        elif clase=="barra enrredada":
            outline="red"
        elif clase=="barra_vertical":
            outline="yellow"
        elif clase=="barra_vertical":
            outline="blue"
        elif clase=="puntos":
            outline="white"

        text = clase+": "+str(int(confidence*100))+"%"

        y_mensaje = y1
                
        delta_y=30

        if y1-delta_y>0:
            y_mensaje=y1-delta_y

        position = (x1, y_mensaje)  

        mensajes_full.append((position,text,outline))
        rectangulos_full.append((x1,y1,x2,y2,outline))

        if clase=="barra enrredada":
            hay_barra_trabada=True
            detecciones.append(string_deteccion)
        elif clase=="barra_vertical":
            hay_barra_trabada=True
            detecciones.append(string_deteccion)
        elif clase=="barra voladora":
            hay_barra_trabada=True
            detecciones.append(string_deteccion)
        elif clase=="barra doblada":
            hay_barra_trabada=True
            detecciones.append(string_deteccion)
  
    if hay_barra_trabada:
        draw = ImageDraw.Draw(crop_filtrado)
        
        draw_original = ImageDraw.Draw(image)

        for mensaje in mensajes_full:
            print(mensaje)
            print(mensaje[0])
            print(mensaje[1])
            print(mensaje[2])
            draw.text(mensaje[0],mensaje[1],fill=mensaje[2],font=font)        
            draw_original.text((zona.x1,zona.y1),mensaje[1],fill=mensaje[2],font=font)        

        for rectangulo in rectangulos_full:
            draw.rectangle((rectangulo[0],rectangulo[1],rectangulo[2],rectangulo[3]), outline = rectangulo[4] ,width=5)
            draw_original.rectangle((zona.x1,zona.y1,zona.x1+zona.ancho,zona.y1+zona.alto), outline = rectangulo[4] ,width=5)
            
        crop_filtrado.save(ruta_crops+"/"+solo_nombre+".zona1.jpg")
        
        if estado=="NORMAL":
            estado="BARRA_TRABADA"
            print("enviando alerta!!!")
            para_enviar=ruta_pintadas+"/pintada_"+solo_nombre+".jpg"
            print("guardando")
            print(para_enviar)
            image.save(para_enviar)
            enviar_alerta(para_enviar)
    else:
        
        if estado=="BARRA_TRABADA":
            estado="NORMAL"

    os.remove(ruta_imagen)
    
def callback(ch, method, properties, body):
    global model
    
    url_frame=body.decode()
    
    solo_nombre = os.path.basename(url_frame)
    solo_nombre = solo_nombre.replace(".jpg", "")

    partes = solo_nombre.split("_")
    parte_entera = int(partes[0])
    parte_fraccional = int(partes[1])

    if not os.path.isfile(url_frame):
        print("archivo no existe: "+url_frame)
    else:
        inferir_imagen(url_frame, model,parte_entera,parte_fraccional,zona1)
    
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

    global zona1
    global zona2
    global zona3
    
    global url_telegram
    global canal_id

    nombre_canal=config["RABBIT_ENTRADA"]["nombre_canal"]
    canal_posible_alerta=config["RABBIT_SALIDA"]["nombre_canal"]
    
    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_crops=config["PROCESAMIENTO"]["ruta_crops"]
    
    url_telegram=config["TELEGRAM"]["url_telegram"]
    canal_id=config["TELEGRAM"]["canal_id"]
    
    model = YOLO(config.get("PESOS","ruta"))
    model.model.to(config["CONTEXTO"]["contexto"])
    
    x1=config.getint("ZONA1","x1")
    y1=config.getint("ZONA1","y1")
    ancho=config.getint("ZONA1","ancho")
    alto=config.getint("ZONA1","alto")
    
    zona1=Zona(x1,y1,ancho,alto)
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=nombre_canal)
    channel.basic_consume(queue=nombre_canal, on_message_callback=callback)
    channel.start_consuming()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el servidor de procesamiento de barras trabadas')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/barras_trabadas/servidor_barras.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)

