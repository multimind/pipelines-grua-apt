import pika
import pickle
import configparser
from logging.handlers import RotatingFileHandler
import os
import torch
import logging
import argparse
from PIL import Image, ImageDraw
import datetime
import math
import requests
import time

nombre_canal = None
ruta_boxes = None
ruta_pintadas = None
ruta_frames = None
sector = None
ruta_crops = None
url_telegram = None
canal_id = None
channel = None
grupos = []
estado = "SIN_TRABAJADOR"
primer_grupo = None
segundo_grupo = None

def enviar_alerta(ruta_imagen):
    pass

def reconstruct_timestamp(integer_part, fractional_part):
    timestamp = float(integer_part) + int(fractional_part) / 1_000_000
    return datetime.datetime.fromtimestamp(timestamp)

def log_setup(path, level):
    if not os.path.isdir("logs/pipeline_grua8/"):
        os.makedirs("logs/pipeline_grua8/")
    handler = RotatingFileHandler(path, maxBytes=1024 * 1024, backupCount=3)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)

# función que dibuja recuadros sobre la imagen usando las detecciones
def draw_boxes(image_path, detections, output_path):
    try:
        im = Image.open(image_path)
    except Exception as e:
        logging.error(f"error opening image {image_path}: {e}")
        return
    draw = ImageDraw.Draw(im)
    for detection in detections:
        box = detection.get("box")
        confidence = detection.get("confidence", 0)
        if box:
            draw.rectangle(box, outline="red", width=2)  # dibuja el recuadro
            text = f"{confidence * 100:.1f}%"  # convierte la confianza a porcentaje
            draw.text((box[0], box[1]), text, fill="red")  # escribe el porcentaje
    try:
        im.save(output_path)
        logging.info(f"saved image with boxes to {output_path}")
    except Exception as e:
        logging.error(f"error saving image {output_path}: {e}")
#
def callback(ch, method, properties, body):
    try:
        data = pickle.loads(body)
    except Exception as e:
        logging.error(f"error deserializing message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    logging.info(f"message received: {data}")
    image_path = data.get("image_path")
    detections = data.get("detections", [])
    if not image_path:
        logging.error("message missing 'image_path'")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    output_path = os.path.join(ruta_pintadas, os.path.basename(image_path))
    draw_boxes(image_path, detections, output_path)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def procesar(config):
    global nombre_canal, ruta_boxes, ruta_pintadas, ruta_frames, sector, url_telegram, canal_id, channel
    nombre_canal = config["RABBIT_ENTRADA"]["nombre_canal"]
    ruta_boxes = config["PROCESAMIENTO"]["ruta_boxes"]
    ruta_pintadas = config["PROCESAMIENTO"]["ruta_pintadas"]
    ruta_frames = config["PROCESAMIENTO"]["ruta_frames"]
    sector = config["PROCESAMIENTO"]["sector"]
    url_telegram = config["TELEGRAM"]["url_telegram"]
    canal_id = config["TELEGRAM"]["canal_id"]

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
            print(f"Unexpected error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Inicia el pipeline de procesamiento de despuntes')
    parser.add_argument('archivo_configuracion')
    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']
    log_setup("logs/pipeline_grua8/servidor_camara_64.log", logging.DEBUG)
    config = configparser.ConfigParser()
    config.read(archivo_configuracion)
    procesar(config)