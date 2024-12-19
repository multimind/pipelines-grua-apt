from curses.ascii import alt
import rx
import random
import socket
import sys
import pickle
import json
import pytz
import requests
from PIL import ImageDraw, Image, ImageFont
from scipy.spatial import distance
import logging
import os
import numpy as np
from shapely.geometry import Polygon


def pintar_cuadro_delimitador(ruta_almacenado,tag_deteccion):
    def __principal(source):
        def subscribe(observer, scheduler = None):
            def on_next(json):


                print("############## Capa de Pintado de Cuadros ##############")

                if not os.path.exists(ruta_almacenado):
                    os.mkdir(ruta_almacenado)

                nombre_imagen=json["nombre_imagen"]
                ruta_base=json["ruta_base"]
                detecciones=json[tag_deteccion]

                font = ImageFont.load_default()
                font = ImageFont.truetype("Verdana.ttf",30)
                print(detecciones)
                #if len(detecciones) == 0:
                #    print("Sin Trabajadores")
                #    observer.on_next(json)

                if(len(detecciones) != 0):
                    ruta_imagen  = ruta_base +"/"+nombre_imagen
                    #logging.debug(ruta_imagen)
                    img = Image.open(ruta_imagen)
                    draw = ImageDraw.Draw(img)
                    for cuadro in detecciones:
                        clase = cuadro["clase"]
                        x1 = int(cuadro['x1'])
                        x2 = int(cuadro['x2'])
                        y1 = int(cuadro['y1'])
                        y2 = int(cuadro['y2'])

                        base = distance.euclidean((x1,y2), (x2,y2))
                        altura = distance.euclidean((x1,y2), (x1,y1))

                        area =  base*altura

                        cx = (x1+x2 ) // 2
                        cy = (y1+y2 ) // 2
                        
                        if(clase == "olla"):
                            draw.text((x1,y1), "Area: "+str(area),  align ="left",fill ="black", font = font)
                            draw.text((x1,y1+100), "x,y: "+str(cx)+","+str(cy),  align ="left",fill ="black", font = font)

                            #draw.text((x1,y1+100), "Altura/base: "+str(altura/base),  align ="left",fill ="black", font = font)
                            #draw.text((x1,y1+200), "Altura: "+str(altura),  align ="left",fill ="black", font = font)
                            #draw.text((x1,y1+300), "Base: "+str(base),  align ="left",fill ="black", font = font)

                        draw.rectangle((x1,y1,x2,y2), outline ="green",width=10)
                        #draw.text((x1,y1), clase,  align ="left",fill ="black",font=font)
                    #logging.debug("pintando {}".format(ruta_almacenado+"/"+nombre_imagen))
                    logging.info("pintando {}".format(ruta_almacenado+"/"+nombre_imagen))
                

                    img.save(ruta_almacenado+"/"+nombre_imagen)
                    logging.info("pintando en ",ruta_almacenado+"/"+nombre_imagen)
                    json["enviar_alerta"] = True
                    json["mensaje"] = "Trabajador en zona"
                    json["ruta_factor"] = os.path.join(ruta_almacenado,nombre_imagen)
                else:
                    os.remove(ruta_base+"/"+nombre_imagen)
                observer.on_next(json)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)
    return __principal



def filtrar_cuadro_delimitador():
    def __principal(source):
        def subscribe(observer, scheduler = None):
            def on_next(json):

                nombre_imagen=json["nombre_imagen"]
                ruta_base=json["ruta_base"]
                detecciones=json["detecciones"]

                aux = []
                for cuadro in detecciones:
                    x1 = int(cuadro['x1'])
                    x2 = int(cuadro['x2'])
                    y1 = int(cuadro['y1'])
                    y2 = int(cuadro['y2'])

                    a = (x1,y1)
                    c = (x2,y2)
                    b = (x1,y2)

                    base = distance.euclidean(b, c)
                    alto = distance.euclidean(a, b)

                    if(base > 39 and alto >80):
                        aux.append(cuadro)

                json["detecciones"] = aux
                observer.on_next(json)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)
    return __principal
