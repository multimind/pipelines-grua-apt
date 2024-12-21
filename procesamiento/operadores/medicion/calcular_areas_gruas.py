import rx
import logging
from util import util_poligonos
from util import transformacion
import shapely.affinity
from shapely.geometry import Point
import cv2
import numpy as np
import math

def calcular(clase, variables_globales,delta_x=100,delta_y=50):

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def on_next(datos):

                try:
                    print("estoy aca????!!")
                    json = datos
                    ancho=json["ancho"]
                    alto=json["alto"]

                    cx=int(ancho/2.0)
                    cy=int(alto/2.0)

                    detecciones=json["detecciones"]
                    puntos_elipse = []

                    cantidad_estructuras=0

                    estructuras=[]
                    for deteccion in detecciones:
                        clase_deteccion = deteccion["clase"]
                        if not clase_deteccion in clase:
                            continue
                        cantidad_estructuras=cantidad_estructuras+1
                        deteccion["seleccionada"]="no"
                        estructuras.append(deteccion)

                    estructura_seleccionada=None

                    if cantidad_estructuras==1:
                        estructura_seleccionada=estructuras[0]
                    else:

                        minima=100000
                    
                        for estructura in estructuras:

                            x1=int(deteccion["x1"])
                            x2=int(deteccion["x2"])
                            y1=int(deteccion["y1"])
                            y2=int(deteccion["y2"])

                            px=int(x1+(x2-x1/2.0))
                            py=int(y1+(y2-y1/2.0))

                            dx= (px-cx)*(px-cx)
                            dy= (py-cy)*(py-cy)
                            distancia=math.sqrt(dx+dy)

                            if distancia<minima:
                                minima=distancia
                                estructura_seleccionada=estructura

                    if not estructura_seleccionada==None:
                        estructura_seleccionada["seleccionada"]="si"
                        x1=int(estructura_seleccionada["x1"])
                        x2=int(estructura_seleccionada["x2"])
                        y1=int(estructura_seleccionada["y1"])
                        y2=int(estructura_seleccionada["y2"])

                        variables_globales["estructura_imanes"] = [x1, y1, x2, y2, "estructura_imanes"]

                        variables_globales["area_seguridad_roja"] = [x1-delta_x, y1-delta_y, x2+delta_x, y2+delta_y, "area_seguridad_roja"]
           
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