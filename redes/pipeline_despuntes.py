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
from notificar_monitoreo import NotificadorMonitoreo
 
nombre_canal=None

ruta_boxes=None
ruta_tiles=None
ruta_pintadas=None
ruta_frames=None
sector=None

url_telegram=None
canal_id=None

channel=None
grupos=[]

estado="SIN_DESPUNTES"

primer_grupo=None
segundo_grupo=None

notificador_monitoreo=None

def reconstruct_timestamp(integer_part, fractional_part):
    timestamp = float(integer_part) + int(fractional_part) / 1_000_000
    reconstructed_datetime = datetime.datetime.fromtimestamp(timestamp)
    return reconstructed_datetime

class Despunte:
    def __init__(self, timestamp,clase,x1,y1,x2,y2):
        self.timestamp=timestamp
        self.clase=clase
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
        self.conexion=None

    def centro(self):

        cx=self.x1+int((self.x2-self.x1)/2.0)
        cy=self.y1+int((self.y2-self.y1)/2.0)

        return (cx,cy)

    #revisda si el actual corresponde al anterior mas un movimiento en el eje y
    def esta_conectado_con(self,anterior):
        cx,cy=self.centro()

        anterior_cx,anterior_cy=anterior.centro()

        print("actual")
        print(cx,cy)

        print("anterior")
        print(anterior_cx,anterior_cy)

        delta=25

        # verifica que este en la misma columna!
        if cx>anterior_cx-delta and cx<anterior_cx+delta:

            delta_y= cy - anterior_cy

            # se ha desplazado en el eje y
            if abs(delta_y) >= 10:
                return True
            else:
                print("distancia en y incorrecta!!!")

        else:
            print("en columnas distintas")
            return False

        return False


class GrupoDespuntes:
    def __init__(self, despuntes, timestamp):
        self.despuntes=despuntes
        self.timestamp=timestamp
        self.eliminar=False
        self.conexion=None
        self.alerta=0
        self.solo_nombre=None

def log_setup(path, level):

    if not os.path.isdir("logs/despuntes/"):
            os.makedirs("logs/despuntes/")

    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024,
                                  backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
    
def buscar_despuntes(url_box):
    global ruta_boxes
    global grupos

    grupo_despuntes=GrupoDespuntes([],[])
    
    f = open(url_box, "r")
    boxes = f.readlines()
    f.close()

    solo_nombre=os.path.basename(url_box)

    partes = solo_nombre.split("_")

    parte_entera=partes[0]
    parte_flotante=partes[1]

    timestamp=reconstruct_timestamp(parte_entera,parte_flotante)

    grupo_despuntes.solo_nombre=solo_nombre
    grupo_despuntes.timestamp=timestamp

    hay_despuntes=False

    for box in boxes:
        partes=box.split(",")

        clase=partes[0]
        x1=int(partes[1])
        y1=int(partes[2])
        x2=int(partes[3])
        y2=int(partes[4])

        despunte=Despunte(timestamp,clase,x1,y1,x2,y2)
        grupo_despuntes.despuntes.append(despunte)
        hay_despuntes=True

    return hay_despuntes, grupo_despuntes

def calcular_despuntes():

    global grupos
    global ruta_pintadas
    global ruta_frames
    global ruta_boxes
    global estado

    if len(grupos)<=1:
        return

    grupo_anterior=grupos[-1]
    grupo_actual=grupos[-2]

    grupo_anterior.eliminar=False

    indice_corto_circuito=None
       
    delta=grupo_actual.timestamp-grupo_anterior.timestamp

    segundos=delta.total_seconds()

    if segundos>5:
        print("mas de 5 segundos, se elimina la conexion anterior!")
        grupo_eliminado=grupos.pop(0) # elimina el grupo anterior

        nombre=grupo_eliminado.solo_nombre
        
        os.remove(ruta_boxes+"/"+nombre)

        nombre=nombre.replace(".txt","")

        if os.path.exists(ruta_frames+"/"+nombre):
            os.remove(ruta_frames+"/"+nombre)
        
        if os.path.exists(ruta_pintadas+"/"+nombre):
            os.remove(ruta_pintadas+"/"+nombre)
        
        return

    hay_conexion=False
        
    for despunte_actual in grupo_actual.despuntes:

        for despunte_anterior in grupo_anterior.despuntes:

            if despunte_actual.conexion == None and despunte_actual.esta_conectado_con(despunte_anterior):
                print("conectando!!!!!!!!!!!!!!!!!1dos!!!")
                despunte_actual.conexion=despunte_anterior
                #grupo_despuntes.alerta=1
                hay_conexion=True
            else:
                print("desconectado!!!")
        
    if hay_conexion==True:
        pass
    else:
        print("sin conexiones!, eliminando!")

        nombre=grupos[-1].solo_nombre

        if os.path.exists(ruta_boxes+"/"+nombre):
            os.remove(ruta_boxes+"/"+nombre)

        nombre=nombre.replace(".txt","")

        archivo_frame=ruta_frames+"/"+nombre
        print("borrando: "+archivo_frame)
        
        #if os.path.exists(archivo_frame):
        #     os.remove(archivo_frame)
        # else:
        #     print("no se puede borrar: "+archivo_frame)

        # if os.path.exists(ruta_pintadas+"/"+nombre):
        #     os.remove(ruta_pintadas+"/"+nombre)

        #grupos = grupos[-1:]



    #else:
    #    print("elimina anterior!")
    #    #grupo_eliminado=grupos.pop(0) # elimina el grupo anterior
    #    #nombre=grupo_eliminado.solo_nombre

def calcular_alertas():
   
    
    print("numero de grupoas en calcular alertas!!!")
    print(len(grupos))
    
    if len(grupos)==2:
        print("ALERTA!!!!")


def detectar_movimiento_despunte(primer_grupo,segundo_grupo):

    global grupos
    global ruta_pintadas
    global ruta_frames
    global ruta_boxes
    global estado

    grupo_anterior=primer_grupo
    grupo_actual=segundo_grupo

    grupo_anterior.eliminar=False

    indice_corto_circuito=None
       
    delta=grupo_actual.timestamp-grupo_anterior.timestamp

    segundos=delta.total_seconds()

    if segundos>5:
        print("mas de 5 segundos, se elimina la conexion anterior!")
        grupo_eliminado=grupos.pop(0) # elimina el grupo anterior

        nombre=grupo_eliminado.solo_nombre
        
        os.remove(ruta_boxes+"/"+nombre)

        nombre=nombre.replace(".txt","")

        if os.path.exists(ruta_frames+"/"+nombre):
            os.remove(ruta_frames+"/"+nombre)
        
        if os.path.exists(ruta_pintadas+"/"+nombre):
            os.remove(ruta_pintadas+"/"+nombre)
        
        return False

    hay_conexion=False
        
    for despunte_actual in grupo_actual.despuntes:

        for despunte_anterior in grupo_anterior.despuntes:

            if despunte_actual.conexion == None and despunte_actual.esta_conectado_con(despunte_anterior):
                print("conectando!!!!!!!!!!!!!!!!!1dos!!!")
                despunte_actual.conexion=despunte_anterior
                #grupo_despuntes.alerta=1
                hay_conexion=True
            else:
                print("desconectado!!!")
        
    if hay_conexion==True:
        return True
    else:
        print("sin conexiones!, eliminando!")

        # nombre=grupos[-1].solo_nombre

        # if os.path.exists(ruta_boxes+"/"+nombre):
        #     os.remove(ruta_boxes+"/"+nombre)

        # nombre=nombre.replace(".txt","")

        # archivo_frame=ruta_frames+"/"+nombre
        # print("borrando: "+archivo_frame)
        
        # if os.path.exists(archivo_frame):
        # #     os.remove(archivo_frame)
        # # else:
        # #     print("no se puede borrar: "+archivo_frame)

        # # if os.path.exists(ruta_pintadas+"/"+nombre):
        # #     os.remove(ruta_pintadas+"/"+nombre)

        # grupos = grupos[-1:]
        return False
     
        
def enviar_alerta(grupo):
    global grupos
    global ruta_pintadas

    global url_telegram
    global canal_id
    global estado
    global nombre_canal
    global sector

    solo_nombre=grupo.solo_nombre
    solo_nombre=solo_nombre.replace(".txt","")

    ruta_imagen=ruta_pintadas+"/"+solo_nombre

    print("ruta alerta")
    print(ruta_imagen)

    try:

        if os.path.isfile(ruta_imagen):
            archivo = open(ruta_imagen,'rb')
                                
            mensaje="despunte"
                                
            url = url_telegram + "/sendPhoto?chat_id=" + canal_id + "&text=" + mensaje

            files={'photo': archivo}
            values={'upload_file' : ruta_pintadas+"/"+solo_nombre, 'mimetype':'image/jpg','caption':mensaje }

            response = requests.post(url,files=files,data=values)

            archivo.close()
                
            current_date_iso = datetime.datetime.now().date().isoformat()

            codigo_sector=-1
            if sector=="danielli":
                codigo_sector=3
            elif sector=="ats A":
                codigo_sector=4
            elif sector=="ats B":
                codigo_sector=5

            url_reporte="http://10.25.52.11:5555/despuntes"
                
            datos_post={
                "fecha":current_date_iso,
                "sector": codigo_sector,
                "ruta_imagen":"imagenes/despuntes",
                "tipo_producto": "Por definir"
            }

            response = requests.post(url_reporte, json=datos_post)

        else:
            print("sin envio")
        # # 

        #     
        #     danielli: 3
        #     ats A: 4
        #     ats B: 5


    except Exception as e:
        print("ERROR EN ENVIO TELEGRAM")
        print(e)


def guardar_crop(grupo_despuntes,ruta_imagen):

    pass


def borrar_imagen(url_box):
    global ruta_frames
    global ruta_boxes

    os.remove(url_box)

    solo_nombre=os.path.basename(url_box)
    solo_nombre=solo_nombre.replace(".txt","")

    if os.path.exists(ruta_frames+"/"+solo_nombre):
        os.remove(ruta_frames+"/"+solo_nombre)

def borrar_grupo(grupo):
    global ruta_frames
    global ruta_boxes
    global ruta_pintadas

    nombre=grupo.solo_nombre

    if os.path.exists(ruta_boxes+"/"+nombre):
        os.remove(ruta_boxes+"/"+nombre)

    nombre=nombre.replace(".txt","")

    archivo_frame=ruta_frames+"/"+nombre
        
    if os.path.exists(archivo_frame):
        os.remove(archivo_frame)
    else:
        print("no se puede borrar: "+archivo_frame)

    if os.path.exists(ruta_pintadas+"/"+nombre):
        os.remove(ruta_pintadas+"/"+nombre)
    
# Callback for handling messages
def callback(ch, method, properties, body):
    global ruta_frames
    global estado
    global primer_grupo
    global notificador_monitoreo

    notificador_monitoreo.notificar_monitoreo_rabbit()

    print(f"Received: {body.decode()}")

    url_box=body.decode()

    solo_nombre=os.path.basename(url_box)
    solo_nombre=solo_nombre.replace(".txt","")

    print("")
    print("--------- estado inicial: "+estado+" --------------")

    if not os.path.isfile(url_box):
        print("archivo no existe: "+url_box)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        if url_box.endswith(".txt"):
            hay_despuntes,grupo_despuntes=buscar_despuntes(url_box)
            ch.basic_ack(delivery_tag=method.delivery_tag)

            if estado=="SIN_DESPUNTES":

                if not hay_despuntes:
                    estado="SIN_DESPUNTES"
                    borrar_imagen(url_box)

                    primer_grupo=None
                    segundo_grupo=None
                else:
                    estado="PRIMER_DESPUNTE"
                    primer_grupo=grupo_despuntes

            elif estado=="PRIMER_DESPUNTE":

                if not hay_despuntes:
                    estado="SIN_DESPUNTES"
                    borrar_grupo(primer_grupo)
                    borrar_grupo(grupo_despuntes)
                    primer_grupo=None
                    segundo_grupo=None
                    borrar_imagen(url_box)
                else:

                    hay_movimiento = detectar_movimiento_despunte(grupo_despuntes,primer_grupo)
                    
                    print("hay movimiento???")
                    print(hay_movimiento)

                    if not hay_movimiento:
                        #borrar anterior
                        borrar_grupo(primer_grupo)
                        primer_grupo=grupo_despuntes
                        segundo_grupo=None
                        estado="PRIMER_DESPUNTE"
                        borrar_imagen(url_box)
                    else:

                        #enviar alerta 
                        enviar_alerta(primer_grupo)
                        estado="CONTINUA_DESPUNTE"
                
            elif estado=="CONTINUA_DESPUNTE":

                hay_movimiento = detectar_movimiento_despunte(grupo_despuntes,primer_grupo)

                if not hay_despuntes:
                    estado="SIN_DESPUNTES"
                    borrar_grupo(primer_grupo)
                    borrar_grupo(grupo_despuntes)
                    primer_grupo=None
                    segundo_grupo=None
                    borrar_imagen(url_box)
                elif hay_movimiento:
                    estado="CONTINUA_DESPUNTE"
                    #borrar anterior
                    primer_grupo=grupo_despuntes
                    borrar_imagen(url_box)
                    #ACA guardar crop!
                elif not hay_movimiento:
                    estado="PRIMER_DESPUNTE"
                    
                    borrar_grupo(primer_grupo)
                    primer_grupo=grupo_despuntes
                    borrar_imagen(url_box)

    print("--------- estado final: "+estado+" --------------")

    #enviar reporte cada x tiempo 
    #curl -X POST -H "Content-Type: application/json" -d ' {"id_servidor": 4, "id_servicio": 37, "estado":  1}' http://142.93.253.160/crear/reporte-servicio

def procesar(config):
    global model
    global nombre_canal
    
    global ruta_boxes
    global ruta_tiles
    global ruta_pintadas
    global channel
    global ruta_frames
    global sector

    global url_telegram
    global canal_id
    global notificador_monitoreo

    nombre_canal=config["PROCESAMIENTO"]["nombre_canal"]

    ruta_boxes=config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_tiles=config["PROCESAMIENTO"]["ruta_tiles"]
    ruta_pintadas=config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_frames=config["PROCESAMIENTO"]["ruta_frames"]
    sector=config["PROCESAMIENTO"]["sector"]
   
    url_telegram=config["TELEGRAM"]["url_telegram"]
    canal_id=config["TELEGRAM"]["canal_id"]

    id_servidor=int(config["MONITOREO"]["id_servidor"])
    id_servicio=int(config["MONITOREO"]["id_servicio"])
    
    mensaje= {
            "id_servidor": id_servidor,
            "id_servicio": id_servicio,
            "estado": 1,
    }

    notificador_monitoreo=NotificadorMonitoreo(4*60,mensaje)
    
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

    log_setup("logs/pipeline_despuntes/servidor_despuntes.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)