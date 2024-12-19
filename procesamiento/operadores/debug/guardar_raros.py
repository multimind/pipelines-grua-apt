import rx
import logging
from util import util_poligonos
from util import transformacion
import shapely.affinity
from shapely.geometry import Point
import cv2
import numpy as np
from PIL import ImageDraw, Image

def guardar( variables_globales,ruta_raros):

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def on_next(datos):

                try:
                    json = datos
                    print("guardar raros!!!")
                    print(datos)
                    print(variables_globales)

                    if 'caso_raro_estructuras' in variables_globales:
                        nombre_imagen=json["nombre_imagen"]
                        ruta_base=json["ruta_base"]
                        
                        img = Image.open(ruta_base + '/' +nombre_imagen)
                        img.save(ruta_raros+"/"+nombre_imagen)
                        del variables_globales['caso_raro_estructuras']
                        
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