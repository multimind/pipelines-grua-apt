import rx
import logging
from util import util_poligonos
from util import transformacion
import shapely.affinity
from shapely.geometry import Point
import cv2
import numpy as np
from PIL import ImageDraw, Image

def pintar( variables_globales,ruta_pintada):

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def on_next(datos):

                try:
                    json = datos
                    
                    detecciones=json["detecciones"]
                    
                    nombre_imagen=json["nombre_imagen"]
                    ruta_base=json["ruta_base"]
                    
                    img = Image.open(ruta_base + '/' +nombre_imagen)
                    draw = ImageDraw.Draw(img)
                    
                    for deteccion in detecciones:
                        clase=deteccion["clase"]

                        x1 = int(deteccion["x1"])
                        x2 = int(deteccion["x2"])
                        y1 = int(deteccion["y1"])
                        y2 = int(deteccion["y2"])

                        outline="yellow"

                        if clase=="estructura_imanes":
                            outline="blue"
                        elif clase=="cono":
                            outline="orange"
                        elif clase=="trabajador":
                            if deteccion["seguro"]=="si":
                                outline="green"
                            elif deteccion["seguro"]=="no":
                                outline="red"

                        draw.rectangle((x1,y1,x2,y2), outline = outline ,width=5)

                    print(".....")

                    if "area_seguridad_roja" in variables_globales:
                        print("sss")
                        area_seguridad_roja=variables_globales["area_seguridad_roja"]
                        outline="yellow"
                        print("w")
                        draw.rectangle((area_seguridad_roja[0],area_seguridad_roja[1],area_seguridad_roja[2],area_seguridad_roja[3]), outline = outline ,width=5)
                        print("z")
                    img.save(ruta_pintada + "/" + nombre_imagen)

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