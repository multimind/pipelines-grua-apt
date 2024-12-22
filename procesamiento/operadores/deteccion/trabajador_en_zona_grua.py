import rx
import logging
from util import util_poligonos
from util import transformacion
import shapely.affinity
from shapely.geometry import Point
import cv2
import numpy as np

def detectar(variables_globales):

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def punto_dentro(x,y,rx1,ry1,rx2,ry2):  #el (0,0) esta en la esquina superior izquierda

                x_dentro=False

                if x>=rx1 and x<=rx2:
                    x_dentro=True

                y_dentro=False

                if y>=ry1 and y<=ry2:
                    y_dentro=True

                return x_dentro and y_dentro

            def buscar_trabajador_en_area(deteccion,area_roja):

                x1=int(deteccion["x1"])
                x2=int(deteccion["x2"])
                y1=int(deteccion["y1"])
                y2=int(deteccion["y2"])

                c1=punto_dentro(x1,y1,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
              
                if c1:
                    return True

                c2=punto_dentro(x1,y2,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
                
                if c2:
                    return True

                c3=punto_dentro(x2,y2,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
                
                if c3:
                    return True

                c4=punto_dentro(x2,y1,area_roja[0],area_roja[1],area_roja[2],area_roja[3])
                
                if c4:
                    return True

                return False

            def on_next(datos):
                print("==inicio calcular trabajador")
                    
                try:
                    json = datos
                    detecciones=json["detecciones"]

                    trabajadores=[]
                    
                    variables_globales["alerta"]="no"

                    if "area_seguridad_roja" in variables_globales:
                        
                        area_roja=variables_globales["area_seguridad_roja"] 

                        hay_alerta=False                 
                        for deteccion in detecciones:
                            clase_deteccion = deteccion["clase"]
                        
                            if not clase_deteccion in "trabajador":
                                continue 
                            
                            hay_trabajador=buscar_trabajador_en_area(deteccion,area_roja)

                            
                            if hay_trabajador:
                                variables_globales["alerta"]="si"
                                deteccion["seguro"]="no"
                                hay_alerta=True
                            else:
                                deteccion["seguro"]="si"
                        
                        if hay_alerta:
                            variables_globales["cantidad_alertas"]=variables_globales["cantidad_alertas"]+1
                        else:
                            variables_globales["cantidad_alertas"]=0

                except Exception as err:
                    print(err)
                    logging.error("Exception occurred", exc_info=True)
                print("==fin trabajador")
                observer.on_next(json)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)

    return _principal