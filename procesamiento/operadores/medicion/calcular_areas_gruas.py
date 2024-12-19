import rx
import logging
from util import util_poligonos
from util import transformacion
import shapely.affinity
from shapely.geometry import Point
import cv2
import numpy as np

def calcular(clase, variables_globales,delta_x=100,delta_y=50):

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def on_next(datos):

                try:
                    json = datos
                    detecciones=json["detecciones"]
                    puntos_elipse = []

                    cantidad_estructuras=0

                    for deteccion in detecciones:
                        clase_deteccion = deteccion["clase"]
                        if not clase_deteccion in clase:
                            continue
                            
                        x1=int(deteccion["x1"])
                        x2=int(deteccion["x2"])
                        y1=int(deteccion["y1"])
                        y2=int(deteccion["y2"])
                            
                        puntos_elipse.append([x1, y1, x2, y2, clase])

                        variables_globales["estructura_imanes"] = [x1, y1, x2, y2, clase]

                        variables_globales["area_seguridad_roja"] = [x1-delta_x, y1-delta_y, x2+delta_x, y2+delta_y, "area_roja"]
                    
                        cantidad_estructuras=cantidad_estructuras+1

                    if not cantidad_estructuras ==1:
                        variables_globales["caso_raro_estructuras"]=cantidad_estructuras

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