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

def limpiar( variables_globales,ruta_pintados):

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def on_next(json):

                try:
                    solo_nombre=json["nombre_imagen"].replace(".jpg","")

                    os.remove("/data/pipelines-grua-apt/captura/boxes" + "/" + solo_nombre)
                 
                    if(variables_globales["alerta"]=="si"):
                        pass
                    else:
                        os.remove(json["ruta_base"]+"/"+json["nombre_imagen"])
                        os.remove(json["ruta_base"]+"/"+json["nombre_imagen"])

                    
                       
       
                except Exception as err:
                    print(err)
                    logging.error("Exception occurred", exc_info=True)

                observer.on_next(json)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)

    return _principal