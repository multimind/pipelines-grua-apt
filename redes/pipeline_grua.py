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
import random
import shutil

nombre_canal=None

ruta_boxes=None
ruta_pintadas=None
ruta_frames=None
ruta_raros=None

url_telegram=None
canal_id=None

channel=None
grupos=[]

estado="SIN_RIESGO"

primer_grupo=None
segundo_grupo=None

def log_setup(path, level):

    if not os.path.isdir("logs/grua/"):
            os.makedirs("logs/grua/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)

def reconstruct_timestamp(integer_part, fractional_part):
    timestamp = float(integer_part) + int(fractional_part) / 1_000_000
    reconstructed_datetime = datetime.datetime.fromtimestamp(timestamp)
    return reconstructed_datetime

def borrar_imagen(url_box):
    global ruta_frames
    global ruta_pintadas
    global ruta_boxes

    os.remove(url_box)

    solo_nombre=os.path.basename(url_box)
    solo_nombre=solo_nombre.replace(".txt","")

    if os.path.exists(ruta_frames+"/"+solo_nombre):
        os.remove(ruta_frames+"/"+solo_nombre)

    if os.path.exists(ruta_pintadas+"/"+solo_nombre):
        os.remove(ruta_pintadas+"/"+solo_nombre)

def enviar_alerta(pintada,mensaje):
    
    global url_telegram
    global canal_id
    global estado
    
    if os.path.isfile(pintada):
        print("imagen a enviar!")
        print(pintada)
        archivo = open(pintada,'rb')
                            
        url = url_telegram + "/sendPhoto?chat_id=" + canal_id + "&text=" + mensaje

        print(url)

        files={'photo': archivo}
        values={'upload_file' : pintada, 'mimetype':'image/jpg','caption':mensaje }

        response = requests.post(url,files=files,data=values)

        archivo.close()
            
        print("enviada!!!!")
    else:
        print("sin envio!")

def punto_dentro(x,y,rx1,ry1,rx2,ry2):  #el (0,0) esta en la esquina superior izquierda

    x_dentro=False

    if x>=rx1 and x<=rx2:
        x_dentro=True

    y_dentro=False

    if y>=ry1 and y<=ry2:
        y_dentro=True

    return x_dentro and y_dentro

def buscar_trabajador_en_area(deteccion,area_roja):
    
    x1=deteccion[1]
    y1=deteccion[2]
    x2=deteccion[3]
    y2=deteccion[4]

    c1=punto_dentro(x1,y1,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
              
    if c1:
        return True

    c2=punto_dentro(x1,y2,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
                
    if c2:
        return True

    c3=punto_dentro(x2,y2,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
                
    if c3:
        return True

    c4=punto_dentro(x2,y1,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
                
    if c4:
        return True

    return False

def calcular_factor(estructuras,trabajadores,ancho_imagen,alto_imagen,ruta_frames,nombre_imagen,delta_x=100,delta_y=150):
    global ruta_raros

    if len(trabajadores)==0:
        return False,None,None,None

    cx=int(ancho_imagen/2.0)
    cy=int(alto_imagen/2.0)

    cantidad_estructuras=len(estructuras)

    estructura_seleccionada=None

    area_seguridad_roja = None

    estructura_seleccionada=None

    if cantidad_estructuras==1:
        estructura_seleccionada=estructuras[0]

        x1=int(estructura_seleccionada[1])
        y1=int(estructura_seleccionada[2])
        x2=int(estructura_seleccionada[3])
        y2=int(estructura_seleccionada[4])

        print("---estrucrura:::")
        print(x1)
        print(y1)
        print(x2)
        print(y2)

        area_seguridad_roja= [x1-delta_x, y1-delta_y, x2+delta_x, y2+delta_y]
    else:

        minima=100000
                    
        for estructura in estructuras:

            x1=int(estructura[1])
            y1=int(estructura[2])
            x2=int(estructura[3])
            y2=int(estructura[4])

            print("---estrucrura:::")
            print(x1)
            print(y1)
            print(x2)
            print(y3)

            px=int(x1+(x2-x1/2.0))
            py=int(y1+(y2-y1/2.0))

            dx= (px-cx)*(px-cx)
            dy= (py-cy)*(py-cy)

            distancia=math.sqrt(dx+dy)

            if distancia<minima:
                minima=distancia
                estructura_seleccionada=estructura
                area_seguridad_roja= [x1-delta_x, y1-delta_y, x2+delta_x, y2+delta_y]

    if estructura_seleccionada==None:
        print("salgo aca?=???")

        random_number = random.randint(1, 100)

        if random > 35:
            shutil.copy(ruta_frames+"/"+nombre_imagen,ruta_raros+"/"+nombre_imagen)

        return True,False,None,None

    factor_riego=False

    print("por aca???????")
    for trabajador in trabajadores:

        print(trabajador)
        print(area_seguridad_roja)

        hay_trabajador=buscar_trabajador_en_area(trabajador,area_seguridad_roja)

        if hay_trabajador:
            factor_riego=True
            trabajador.append("inseguro")
        else:
            trabajador.append("seguro")

    return True,True,factor_riego,area_seguridad_roja

def procesar_boxes(url_box):

    f = open(url_box, "r")
    boxes = f.readlines()
    f.close()

    estructuras=[]
    trabajadores=[]

    for box in boxes:

        partes=box.split(",")

        clase=partes[0]
        
        print("-----ndjdj")
        print(box)

        partes=box.split(",")   

        nombre=partes[0]

        x1=int(partes[1])
        y1=int(partes[2])
        x2=int(partes[3])
        y2=int(partes[4])

        confidence=float(partes[5])

        timesamp_entero=int(partes[6])
        timesamp_decimal=int(partes[7])

        if clase=="estructura_imanes":
            estructuras.append([nombre,x1,y1,x2,y2,confidence,timesamp_entero,timesamp_decimal])
        elif clase=="trabajador":
            trabajadores.append([nombre,x1,y1,x2,y2,confidence,timesamp_entero,timesamp_decimal])

    return estructuras,trabajadores

    
# Callback for handling messages
def callback(ch, method, properties, body):
    global ruta_frames
    global ruta_pintadas
    global estado
    global primer_grupo

    print(f"Received: {body.decode()}")

    url_box=body.decode()

    solo_nombre=os.path.basename(url_box)
    solo_nombre=solo_nombre.replace(".txt","")

    print(solo_nombre)
    partes=solo_nombre.split("_")

    ancho_imagen=int(partes[2])
    alto_imagen=int(partes[3].replace(".jpg",""))

    print(ancho_imagen)
    print(alto_imagen)

    print("")
    print("--------- estado inicial: "+estado+" --------------")

    if not os.path.isfile(url_box):
        print("archivo no existe: "+url_box)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        if url_box.endswith(".txt"):
            print("por aca???")
            boxes,trabajadores=procesar_boxes(url_box)
            hay_trabajadores,hay_estructura,dentro_zona_riesgo,area_seguridad_roja=calcular_factor(boxes,trabajadores,ancho_imagen,alto_imagen,ruta_frames,solo_nombre)
           
            if dentro_zona_riesgo:

                #pintar estructura
                image = Image.open(ruta_pintadas+"/"+solo_nombre)
                draw = ImageDraw.Draw(image)
                draw.rectangle((area_seguridad_roja[0],area_seguridad_roja[1],area_seguridad_roja[2],area_seguridad_roja[3]), outline = "orange" ,width=5)
                image.save(ruta_pintadas+"/"+solo_nombre)

            ch.basic_ack(delivery_tag=method.delivery_tag)

            if estado=="SIN_RIESGO":

                if not hay_trabajadores or not hay_estructura or not dentro_zona_riesgo:
                    estado="SIN_RIESGO"
                    borrar_imagen(url_box)
                elif dentro_zona_riesgo:
                    estado="INICIO_DETECCION"
                    enviar_alerta(ruta_pintadas+"/"+solo_nombre,"Inicio")

            elif estado=="INICIO_DETECCION":
                
                if not hay_trabajadores or not dentro_zona_riesgo:
                    estado="SIN_RIESGO"
                    borrar_imagen(url_box)
                elif not hay_estructura:
                    estado="INICIO_DETECCION"
                    borrar_imagen(url_box)
                elif dentro_zona_riesgo:
                    estado="CONTINUA_DETECCION"
                    #buscar forma de mantener algunas
                    borrar_imagen(url_box)

            elif estado=="CONTINUA_DETECCION":
                
                if not hay_trabajadores or not dentro_zona_riesgo:
                    estado="SIN_RIESGO"
                    enviar_alerta(ruta_pintadas+"/"+solo_nombre,"Fin")
                elif not hay_estructura:
                    estado="CONTINUA_DETECCION"
                    borrar_imagen(url_box)
                elif dentro_zona_riesgo:
                    estado="CONTINUA_DETECCION"
                    borrar_imagen(url_box)
                
                
             

    print("--------- estado final: "+estado+" --------------")
           
def procesar(config):
    global model
    global nombre_canal
    
    global ruta_boxes
    global ruta_pintadas
    global channel
    global ruta_frames
    global ruta_raros

    global url_telegram
    global canal_id
    
    nombre_canal=config["PROCESAMIENTO"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_frames=config["PROCESAMIENTO"]["ruta_frames"]
    ruta_raros=config["PROCESAMIENTO"]["ruta_raros"]
   
    url_telegram=config["TELEGRAM"]["url_telegram"]
    canal_id=config["TELEGRAM"]["canal_id"]
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=nombre_canal)

    channel.basic_consume(queue=nombre_canal, on_message_callback=callback)

    channel.start_consuming()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el pipeline de procesamiento de grua')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/pipeline_grua/servidor_gura.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)