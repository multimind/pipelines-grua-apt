import rx
import logging
import json
from util import util_poligonos

def verificar_zona_de_riesgo(zonas) -> json:
    """Verificar zona de riesgo.

    Esta función lee un poligono, definido en ``zonas`` y comprueba sí el trabajador se encuentra dentro de la zona de riesgo.

    :param json zonas: Archivo ``json`` que define un poligono correspondiente a la zona de riesgo.
   
    :return: Arreglo en formato ``json``
    :rtype: json
    """
    def __clasificador(source):
        def subscribe(observer , scheduler=None):
            def on_next(json_de_imagen):
                logging.debug("#### verificar_zona_de_riesgo ###")
                logging.debug("Imagen: {} verificar_zona_de_riesgo".format(json_de_imagen["nombre_imagen"]))
                detecciones_trabajadores =  json_de_imagen["detecciones_trabajador"]
                en_zona_de_riesgo = []

                for deteccion_trabajador in detecciones_trabajadores:
                    seccion_clase = deteccion_trabajador["clase"]
                    x1=int(deteccion_trabajador["x1"])
                    x2=int(deteccion_trabajador["x2"])
                    y1=int(deteccion_trabajador["y1"])
                    y2=int(deteccion_trabajador["y2"])


                    for zona in zonas:
                        logging.debug("Verificando trabajador en zona de riesgo")
                        resultado = util_poligonos.box_dentro_poligono(x1,y1,x2,y2,zona)

                        if(resultado == True):
                            en_zona_de_riesgo.append({"clase":seccion_clase,"x1":x1,"y1":y1,"x2":x2,"y2":y2})

                if len(en_zona_de_riesgo) > 0:
                    print("Trabajador en zona de riesgo")

                json_de_imagen["trabajador_zona_de_riesgo"] = en_zona_de_riesgo

                observer.on_next(json_de_imagen)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler
            )
        return rx.create(subscribe)

    return __clasificador
