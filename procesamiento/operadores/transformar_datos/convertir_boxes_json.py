import rx
import logging
from util import util_poligonos
from util import transformacion
import shapely.affinity
from shapely.geometry import Point
import cv2
import numpy as np
from PIL import ImageDraw, Image
import os

def convertir():

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def on_next(json):
                print("==inicio convertir")
                try:
                    boxes=json[boxes]

                    dectecciones=[]

                    for box in boxes:
                        
                        clase, part2 = deteccion.split(":")
                        
                        part2 = part2.strip()

                        numbers = list(map(int, part2.split(',')))

                        detecciones.append({"clase":clase,"x1":numbers[0],"y1":numbers[1],"x2":numbers[2],"y2":numbers[3]})
              
                    json["detecciones"]=detecciones      
       
                except Exception as err:
                    print(err)
                    logging.error("Exception occurred", exc_info=True)
                print("==fin convertir")
                observer.on_next(json)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)

    return _principal