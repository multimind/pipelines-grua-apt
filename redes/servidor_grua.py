import socket
import pickle
import configparser
from logging.handlers import RotatingFileHandler

import os
import cv2

from ultralytics import YOLO

import torch
import logging
import argparse

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

            respuesta.append(res)

        return [True, respuesta]

    else:
        return [False, respuesta]


def run_socket(config):
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_address = ('localhost', config.getint("PUERTO","puerto"))
    
    mensaje = 'Iniciando servicio en {} el puerto {}'.format(*server_address)
    logging.info(mensaje)

    sock.bind(server_address)
    sock.listen(1)

    model = YOLO(config.get("PESOS","ruta"))
    
    mensaje = "Pesos de Red Cargados en Memoria"
    logging.info(mensaje)

    while True:
        mensaje = 'Esperando Conexion'
        print(mensaje)
        logging.info(mensaje)
        connection, client_address = sock.accept()
        try:
            mensaje = 'Conexion entrante desde: {} '.format(client_address)
            logging.info(mensaje)
            
            while True:
                data = connection.recv(4096)

                if data:
                    try:
                        data_recibida = pickle.loads(data)
                        ruta_de_imagen = data_recibida[0]

                        mensaje = "Datos recibidos: {}".format(data_recibida[0])
                        logging.info(mensaje)
                    except Exception as e:
                        mensaje = "{} {}".format(e, e.args)

                    try:
                        solo_nombre=os.path.basename(ruta_de_imagen)
                        resultado, respuesta = inferir_imagen(ruta_de_imagen, model)

                        print(respuesta)

                        if(len(respuesta) == 0):
                            respuesta=['imagen:'+str(solo_nombre)]+['nada:_']
                        else:
                            respuesta=['imagen:'+str(solo_nombre)]+respuesta

                        logging.info("Enviando Respuesta: {}".format(respuesta))
                        connection.sendall(pickle.dumps(respuesta))
                    except Exception as e:
                        logging.critical("{} {}".format(e,e.args))

                else:
                    mensaje = 'No hay mas datos de {} '.format(client_address)
                    logging.info(mensaje)
                    break

        finally:
            connection.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el servidor de procesamiento de gruas')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    log_setup("logs/grua/servidor_grua.log", logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    run_socket(config)


