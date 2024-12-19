from PIL import Image, ImageDraw
import logging
import rx
import cv2
import requests
import os
from util import util_poligonos

def pintar_deteccion_trabajador(config,ruta_factores,ruta_no_factores):
    def _cliente_segmentador_barra(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):

                zona_prohibida_2 = config["zona_prohibida_2"]
                zona_prohibida_1 = config["zona_prohibida_1"]
                estado_zona_prohibida_1 = config["estado_zona_prohibida_1"]
                estado_zona_prohibida_2 = config["estado_zona_prohibida_2"]

                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                boxes = json_datos["boxes"]

                img = Image.open(ruta_base +"/"+ nombre_archivo).convert("RGB")
                draw = ImageDraw.Draw(img)

                for box in boxes:
                    x, y, x1, y1 = box
                    draw.rectangle([x, y, x1, y1], outline ="green",width=3)

                img_con_alerta_zona1 = False
                involucrados_zona1 = 0

                if estado_zona_prohibida_1:
                    for box in boxes:
                        for zona in zona_prohibida_1:
                    
                            x, y, x1, y1 = box
                            resultado=util_poligonos.base_box_dentro_poligono(x,y,x1,y1,zona)
                            #resultado=util_poligonos.base_box_dentro_poligono(555,363,689,515,zona)
                            logging.info("Factor zona prohibida {}".format(resultado))
                            if(resultado == True):
                                draw.rectangle([x, y, x1, y1], outline ="red",width=3)
                                img_con_alerta_zona1 = True
                                involucrados_zona1 += 1
                            #else:
                            #    draw.rectangle([x, y, x1, y1], outline ="green",width=3)


                            
                img_con_alerta_zona2 = False
                involucrados_zona2 = 0

                if estado_zona_prohibida_2:
                    for box in boxes:
                        for zona in zona_prohibida_2:

                            x, y, x1, y1 = box
                            resultado=util_poligonos.base_box_dentro_poligono(x,y,x1,y1,zona)
                            #resultado=util_poligonos.base_box_dentro_poligono(555,363,689,515,zona)
                            logging.info("Factor zona prohibida {}".format(resultado))
                            if(resultado == True):
                                draw.rectangle([x, y, x1, y1], outline ="red",width=3)
                                img_con_alerta_zona2 = True
                                involucrados_zona2 += 1
                            #else:
                            #    draw.rectangle([x, y, x1, y1], outline ="green",width=3)

                if img_con_alerta_zona2:
                    for zona in zona_prohibida_2:
                        puntos = list(zona.exterior.coords)
                        draw.polygon([(x, y ) for x, y in puntos], outline="red", width=5)
                        draw.polygon([(x , y) for x, y in puntos], outline="red", width=5)

                if img_con_alerta_zona1:
                    for zona in zona_prohibida_1:
                        puntos = list(zona.exterior.coords)
                        draw.polygon([(x, y ) for x, y in puntos], outline="red", width=5)
                        draw.polygon([(x , y) for x, y in puntos], outline="red", width=5)
                
                if involucrados_zona1 > 0 and involucrados_zona2 > 0:
                    json_datos["involucrados"] = involucrados_zona1 + involucrados_zona2
                elif involucrados_zona1 > 0:
                    json_datos["involucrados"] = involucrados_zona1
                elif involucrados_zona2 > 0:
                    json_datos["involucrados"] = involucrados_zona2
                    

                json_datos["enviar_alerta"] = False
                if img_con_alerta_zona1 or img_con_alerta_zona2:
                    logging.info("Trabajador en Zona Prohibida")
                    img.save(ruta_factores + "/"+nombre_archivo)
                    json_datos["ruta_factor"] = ruta_factores + "/"+nombre_archivo
                    json_datos["mensaje"] = "BALANZA Trabajador en Zona Prohibida: involucrados {}".format(json_datos["involucrados"])
                    json_datos["enviar_alerta"] = True
                    
                else:
                    #img.save(ruta_no_factores + "/"+nombre_archivo)

                    os.remove(ruta_base +"/"+ nombre_archivo)
                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _cliente_segmentador_barra