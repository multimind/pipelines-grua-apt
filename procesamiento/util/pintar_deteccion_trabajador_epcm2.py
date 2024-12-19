from PIL import Image, ImageDraw
import logging
import rx
import cv2
import requests
import os
from util import util_poligonos
import logging

def pintar_deteccion_trabajador(zonas,enviar_alerta,telegram_url,chat_id,ruta_factores,ruta_no_factores):
    def _cliente_segmentador_barra(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):
                logging.getLogger("PIL").setLevel(logging.ERROR)

                logging.info("Pintar deteccion trabajador")
                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                boxes = json_datos["boxes"]

                img = Image.open(ruta_base +"/"+ nombre_archivo).convert("RGB")
                img_copy = img.copy()

                draw = ImageDraw.Draw(img)


                for box in boxes:
                    x, y, x1, y1 = box
                    draw.rectangle([x, y, x1, y1], outline ="green",width=3)



                img_con_alerta = False
                involucrados_zona = 0
                for box in boxes:
                    for zona in zonas:
                        #draw.polygon(zona, outline="blue", width=3)
                        x, y, x1, y1 = box
                        resultado=util_poligonos.base_box_dentro_poligono(x,y,x1,y1,zona)
                        #resultado=util_poligonos.base_box_dentro_poligono(555,363,689,515,zona)
                        logging.info("Factor zona prohibida {}".format(resultado))
                        if(resultado == True):
                            draw.rectangle([x, y, x1, y1], outline ="red",width=3)
                            img_con_alerta = True
                            involucrados_zona += 1
                        #else:
                        #    draw.rectangle([x, y, x1, y1], outline ="green",width=3)

                if img_con_alerta:
                    for zona in zonas:
                        puntos = list(zona.exterior.coords)
                        draw.polygon([(x, y ) for x, y in puntos], outline="red", width=5)

                json_datos["enviar_alerta"] = False
                json_datos["involucrados"] = involucrados_zona
                
                if img_con_alerta:
                    logging.info("Trabajador en Zona Prohibida")
                    img.save(ruta_factores + "/"+nombre_archivo)
                    json_datos["ruta_factor"] = ruta_factores + "/"+nombre_archivo
                    json_datos["mensaje"] = "EPCM2 Trabajador en Zona Prohibida " + str(involucrados_zona) + " involucrados"
                    json_datos["enviar_alerta"] = True
                    

                else:
                    img_copy.save(ruta_no_factores + "/"+nombre_archivo)

                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _cliente_segmentador_barra