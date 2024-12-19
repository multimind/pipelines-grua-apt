from PIL import Image, ImageDraw
import logging
import rx
import cv2
import requests
import os
from util import util_poligonos
import logging

def pintar_deteccion_trabajador(enviar_alerta,telegram_url,chat_id,ruta_factores,ruta_no_factores):
    def _cliente_segmentador_barra(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):
                logging.getLogger("PIL").setLevel(logging.ERROR)

                logging.info("Pintar deteccion trabajador")
                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                boxes = json_datos["boxes"]

                img = Image.open(ruta_base +"/"+ nombre_archivo).convert("RGB")
                draw = ImageDraw.Draw(img)


                img_con_alerta = False
                involucrados_zona = 0

                if len(boxes) > 0:
                    img_con_alerta = True

                    for box in boxes:
                        x, y, x1, y1 = box
                        draw.rectangle([x, y, x1, y1], outline ="red",width=5)
                        involucrados_zona += 1

                json_datos["enviar_alerta"] = False
                json_datos["involucrados"] = involucrados_zona
                
                if img_con_alerta:
                    logging.info("Trabajador en Zona Prohibida")
                    img.save(ruta_factores + "/"+nombre_archivo)
                    json_datos["ruta_factor"] = ruta_factores + "/"+nombre_archivo
                    json_datos["mensaje"] = "Trabajador en Zona Prohibida " + str(involucrados_zona) + " involucrados"
                    json_datos["enviar_alerta"] = True
                    

                else:
                    img.save(ruta_no_factores + "/"+nombre_archivo)

                #os.remove(ruta_base +"/"+ nombre_archivo)
                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _cliente_segmentador_barra