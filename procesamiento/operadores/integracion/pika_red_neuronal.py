import rx
import random
import socket
import sys
import pickle
import json
import pytz
import requests
import logging
import traceback
from scipy.spatial import distance


def procesarImagen(canal,tag_detecciones,nombre_red="pixellib" ) -> json:
    """Procesa una imagen.

    Esta función envia una imagen, mediante un socket, para inferir en la red neuronal.

    :param str servidor: Dirección IP del servidor donde se encuentra la red neuronal.
    :param str puerto: Puerto donde se encuentra la red neuronal.
    :param str tag_detecciones: Etiqueta para realizar la detección.
    :param str nombre_red: Red neuronal utilizada para realizar la inferencia. Puede tomar valores ``detectron2`` y ``pixellib`` ( default is pixellib)
    :return: Arreglo en formato ``json``
    :rtype: json
    """

    def _clasificador(source):

        def subscribe(observer, scheduler = None):

            def on_next(json_datos):

                print("aca!")

                logging.debug(">> Iniciando socket red neuronal {} ".format(puerto))

                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                ruta_imagen = ruta_base +"/"+ nombre_archivo

                try:
                    arreglo_imagen=[str(ruta_imagen)]
                    print("aca???")
                    message = pickle.dumps(arreglo_imagen)
                    print("enviado")
                    sock.sendall(message)
                    print("antes recibir")
                    data = sock.recv(4096)
                    print("recibido")
                    sock.close()
                    data_recibida = pickle.loads(data)

                    detecciones=[]
                    if(data_recibida[1] == "nada:_"):
                        mensaje = "No se han encontrado personas: retornando 0"

                        json_datos[tag_detecciones]=detecciones

                        observer.on_next(json_datos)
                    else:
                        seccion_nombre_imagen=data_recibida[0]

                        nombre_imagen=seccion_nombre_imagen.split(":")[1]

                        seccion_detecciones=data_recibida[1:]

                        for deteccion in seccion_detecciones:

                            if deteccion.startswith("nada"):
                                continue

                            partes_deteccion=deteccion.split(":")
                            seccion_clase=partes_deteccion[0]
                            seccion_coordenadas=partes_deteccion[1].split(",")

                            #vienen en ese orden desde pixelib
                            if(nombre_red == "pixellib"):
                                x1=seccion_coordenadas[1]
                                y1=seccion_coordenadas[0]
                                x2=seccion_coordenadas[3]
                                y2=seccion_coordenadas[2]

                            if(nombre_red == "detectron2"):
                                x1=seccion_coordenadas[0]
                                y1=seccion_coordenadas[1]
                                x2=seccion_coordenadas[2]
                                y2=seccion_coordenadas[3]

                            logging.debug("\t"+"deteccion: clase "+seccion_clase+" x1 "+x1+" y1 "+y1+" x2 "+x2+" y2 "+y2)
                            detecciones.append({"clase":seccion_clase,"x1":x1,"y1":y1,"x2":x2,"y2":y2})

                        json_datos[tag_detecciones]=detecciones
                        observer.on_next(json_datos)

                except ConnectionRefusedError as cre:
                    logging.debug("No se puede conectar al socket de la red neuronal, verifique que la red esta ejecutandose en")
                    logging.debug("tipo: "+tag_detecciones)
                    logging.debug("ip: "+str(servidor))
                    logging.debug("puerto: "+str(puerto))
                    tb = traceback.format_exc()
                    logging.debug(""+str(cre))
                    logging.debug(""+tb)

                except Exception as e:
                    tb = traceback.format_exc()
                    logging.debug(""+str(e))
                    logging.debug(""+tb)
                finally:
                    mensaje = 'Cerrando Conexion'
                    sock.close()

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)
        

        return rx.create(subscribe)

    return _clasificador

 