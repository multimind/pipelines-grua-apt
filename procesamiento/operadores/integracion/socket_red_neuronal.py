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


def procesarImagen(servidor,puerto,tag_detecciones,fabrica=None,nombre_red="pixellib" ) -> json:
    """Procesa una imagen.

    Esta función envia una imagen, mediante un socket, para inferir en la red neuronal.

    :param str servidor: Dirección IP del servidor donde se encuentra la red neuronal.
    :param str puerto: Puerto donde se encuentra la red neuronal.
    :param str tag_detecciones: Etiqueta para realizar la detección.
    :param str or None fabrica: Optional; Sector del cual provienen las imágenes. ( default is None)
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

                if fabrica is not None:
                    ruta_imagen = json_datos["ruta_imagen_cortada"]

                #logging.debug("\truta_imagen: "+ ruta_imagen)
                #TODO: verificar si hay trabajadores para el caso de la red de detecciones_maquinas
                #OJO: que se perderían maquinas cuando no hay trabajador

                try:
                    print("conectando!?")
                    logging.debug("conectando con : {} {}".format(servidor,puerto))
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    server_address = (servidor, puerto)
                    sock.connect(server_address)

                    arreglo_imagen=[str(ruta_imagen)]

                    message = pickle.dumps(arreglo_imagen)
                    sock.sendall(message)
                    data = sock.recv(4096)
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


def procesar_validacion_trabajador() -> json:
    """Valida trabajador en imagen.

    Esta función envia una imagen, mediante un socket, para validar que se hayan encontrado personas (trabajadores) en la imagen.

    :return: Arreglo en formato ``json``
    :rtype: json
    """
    def _clasificador(source):

        def subscribe(observer, scheduler = None):

            def on_next(json_datos):
                logging.debug("Ingresando a red de validacion trabajador")
                ruta_base = json_datos["ruta_base"]
                nombre_imagen = json_datos["nombre_imagen"]
                detecciones_trabajador = json_datos["detecciones_trabajador"]

                coordenadas = []

                for trabajador in detecciones_trabajador:
                    x1 = int(trabajador['x1'])
                    x2 = int(trabajador['x2'])
                    y1 = int(trabajador['y1'])
                    y2 = int(trabajador['y2'])
                    coordenadas.append([x1,y1,x2,y2])


                resultados = []
                for x1,y1,x2,y2 in coordenadas:

                    crop = str(x1)+","+str(y1)+","+str(x2)+","+str(y2)

                    datos = [ruta_base+"/"+nombre_imagen, crop]

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = ('localhost', 9797)
                    mensaje = 'Conectando con {} por el puerto {}'.format(*server_address)
                    sock.connect(server_address)
                    try:
                        message = pickle.dumps(datos)
                        mensaje = 'Enviando datos: {!r}'.format(datos)
                        sock.sendall(message)
                        data = sock.recv(4096)
                        mensaje = 'Recibiendo respuesta de red: {!r}'.format( pickle.loads(data))
                        data_recibida = pickle.loads(data)
                        if(data_recibida == 1):
                            mensaje = "No se han encontrado personas: retornando 0"
                            resultados.append(data_recibida)
                        else:
                            mensaje = "Se han encontrado personas: retornando {}".format(data_recibida)
                            resultados.append(data_recibida)
                    finally:
                        mensaje = 'Cerrando Conexion'

                        sock.close()


                deteccion_valida = []
                for trabajador,res in zip(detecciones_trabajador,resultados):
                    if(res == 1):
                        deteccion_valida.append(trabajador)

                json_datos["detecciones_trabajador"] = deteccion_valida
                observer.on_next(json_datos)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)

    return _clasificador


def triplet_trabajadores(servidor, puerto, tag_detecciones, tag_clase, variables_globales):
    def _clasificador(source):

        def subscribe(observer, scheduler = None):

                def on_next(json_datos):
                    logging.debug(">> Iniciando socket triplet trabajadores {} ".format(puerto))

                    ruta_base = json_datos["ruta_base"]
                    nombre_imagen = json_datos["nombre_imagen"]
                    detecciones_trabajador = json_datos[tag_detecciones]
                    timeout = variables_globales["timeout"]

                    coordenadas = []
                    
                    if variables_globales["timeout"] == 0:

                        try:

                            for trabajador in detecciones_trabajador:
                                clase = trabajador["clase"]
                                x1 = int(trabajador['x1'])
                                x2 = int(trabajador['x2'])
                                y1 = int(trabajador['y1'])
                                y2 = int(trabajador['y2'])
                                coordenadas.append([x1,y1,x2,y2,clase])

                            resultados = []

                            for x1, y1, x2, y2, clase in coordenadas:
                                crop = str(x1)+","+str(y1)+","+str(x2)+","+str(y2)
                                datos = [ruta_base+"/"+nombre_imagen, crop]

                                logging.debug("conectando con : {} {}".format(servidor,puerto))

                                try:

                                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    sock.settimeout(5)
                                    server_address = (servidor, puerto)
                                    sock.connect(server_address)
                                    
                                    message = pickle.dumps(datos)
                                    sock.sendall(message)
                                    data = sock.recv(4096)
                                    sock.close()
                                    data_recibida = pickle.loads(data)

                                    deteccion = (data_recibida[1].split(':'))[1]

                                    if(deteccion.startswith(tag_clase)):
                                        resultados.append({"clase":clase,"x1":x1,"y1":y1,"x2":x2,"y2":y2})
                                except socket.timeout:
                                    variables_globales["timeout"] = 500
                                    print('TIMEOUT!!!!!!!!!!!!!')
                                finally:
                                    sock.close()

                            json_datos[tag_detecciones] = resultados
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
                            
                    else:
                        variables_globales["timeout"] -= 1


                return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)


        return rx.create(subscribe)
    
    return _clasificador

