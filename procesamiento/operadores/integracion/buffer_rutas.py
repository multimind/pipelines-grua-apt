import rx
import logging
import os
import subprocess
import requests
import datetime

def buffer(almacen,ruta_videos,enviar_alerta_telegram, modo):
    def __principal(source):
        def subscribe(observer, scheduler = None):
            def on_next(json_de_imagen):

                enviar_alerta = json_de_imagen["enviar_alerta"]
                if enviar_alerta:
                    logging.debug("Buffer: Imagen con factor {} largo :{}".format(json_de_imagen["nombre_imagen"],len(almacen["data"])))
                    almacen["data"] = almacen["data"] + [json_de_imagen["ruta_factor"]]
                    almacen["involucrados"] = almacen["involucrados"] + [json_de_imagen["involucrados"]]
                    #observer.on_completed()
                    return
                    #json_de_imagen["enviar_amazon"] = False
                    #observer.on_next(json_de_imagen)


                if not enviar_alerta:
                    largo = len(almacen["data"])
                    logging.debug("Buffer: Imagen sin Factor largo:{}".format(largo))


                    if largo == 0:
                        del almacen["data"][:]
                        del almacen["involucrados"][:]
                        logging.info("Buffer: sin imagenes en buffer:{}".format(largo))
                        json_de_imagen["enviar_amazon"] = False
                        observer.on_next(json_de_imagen)
                        #return
                    
                    if largo > 0 and almacen["tolerancia_fn"] < 15:
                        almacen["tolerancia_fn"] = almacen["tolerancia_fn"] + 1 
                        return

                    
                    if largo > 0 and almacen["tolerancia_fn"] >= 15:
                        logging.debug("Buffer: Imagen sin Factor con imagenes en buffer:{}".format(largo))
                        nombre_listado_reducido = "./listado_reducido.txt"
                        nombre_video = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".mp4"
                        ruta_video = ruta_videos+"/"+nombre_video
                        #print("fin",almacen["data"])

                        logging.info("Buffer: Creando video ..")
                        fps = "1"
                        with open(nombre_listado_reducido, "w") as f:
                            for archivo in almacen["data"]:
                                f.write("file '" +archivo + "'\n")

                        subprocess.run(["ffmpeg","-y","-r", fps,"-safe","0","-f","concat","-i",nombre_listado_reducido,ruta_video,"-filter:v","scale=1000:-1","-loglevel", "quiet" ])
                        
                        
                        duracion = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of",
                                "default=noprint_wrappers=1:nokey=1", ruta_video],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

                        duracion_video = int(float(duracion.stdout))
                        #print("duracion: {}".format(duracion_video))

                        logging.info("Buffer: Video creado ..")
                        logging.info("Duracion Video: {}".format(duracion_video))

                        json_de_imagen["duracion_video"] = duracion_video
                        
                        if enviar_alerta_telegram:

                            url = "http://3.87.52.239:8000/metodos/api-telegram"

                            mensaje = "Trabajador en Zona Prohibida - involucrados " + str(max(almacen["involucrados"]))
                            
                            data = {
                                'message': mensaje,
                                'resource': 'video',
                                'env': modo
                            }
                            
                            with open(ruta_video, 'rb') as f:
                                files = {
                                    'file': f
                                }

                                response_amazon = requests.post(url, files=files, data=data)

                            logging.info("Buffer: Enviando {} a Telegram".format(ruta_video))
                            
                            if response_amazon.status_code == 200:
                                logging.info('Imagen enviada!')
                            else:
                                logging.info("Error al subir recurso: {}".format(response_amazon.status_code))

                        json_de_imagen["ruta_video"] = ruta_video
                        json_de_imagen["enviar_amazon"] = True
                        logging.info("Buffer: Enviando a operador Amazon")
                        json_de_imagen["involucrados"] = max(almacen["involucrados"])
                        del almacen["data"][:]
                        del almacen["involucrados"][:]
                        almacen["tolerancia_fn"] = 0
                        logging.info("{}".format(json_de_imagen))
                        #print("saltando a operador amazon")
                        observer.on_next(json_de_imagen)
                        
            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler
            )
        return rx.create(subscribe)
    return __principal

        

            