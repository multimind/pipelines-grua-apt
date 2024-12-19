import rx
import os
import scp
from paramiko import SSHClient
from scp import SCPClient
import paramiko
import logging
import datetime
import pytz
import requests
import shutil
def enviar_video_factor(ssh,ip_servidor,puerto,usuario,ruta_destino,keyfile, sector_id, enviar_alerta_amazon):
    def _principal(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_de_imagen):
                #print("En funcion on_next")
                #print("ENVIANDO AMAZON", flush=True)
                #logging.info("ENVIANDO AMAZON")
                #"""
                #print("Enviando Amazon {} Destino: {}".format(ip_servidor,ruta_destino))
                if json_de_imagen["enviar_amazon"] and enviar_alerta_amazon:
                    logging.info("Enviando Amazon {} Destino: {}".format(ip_servidor,ruta_destino))
                    involucrados = json_de_imagen["involucrados"]
                    duracion = json_de_imagen["duracion_video"]

                    hora_america = pytz.timezone('America/Lima')
                    fecha = datetime.datetime.now(hora_america).strftime("%Y-%m-%d_%H-%M-%S")
                    fecha = datetime.datetime.now(hora_america).isoformat()

                    ruta_origen = json_de_imagen["ruta_video"]
                    nombre_video = os.path.basename(ruta_origen)

                    logging.info("Enviando {} a servidor {} Destino: {}".format(nombre_video,ip_servidor,ruta_destino))

                    data = {
                            "fecha": fecha,
                            "involucrados": involucrados,
                            "duracion": duracion,
                            "url_imagen": "path",
                            "sector":  sector_id,
                            "factor_riesgo": 1,
                            "ancho_imagen": 1920,
                            "alto_imagen": 1080,
                            "video_generado": True,
                        }
                    
                    url = "http://"+ip_servidor+":"+puerto+"/api/incidentes/"
                    response_amazon = requests.post(url, data=data)
                
                    data = response_amazon.json()
                    #print(data)
                    logging.info("Respuesta de servidor Amazon {}".format(data))
                    logging.info("Enviando video a servidor Amazon {}".format(data["id"]))
                    
                    try:
                        ssh.connect(ip_servidor, port=22, username=usuario,timeout=15, key_filename=keyfile)
                    except Exception as e:
                        logging.error("error al conectar con servidor {} {}".format(e,e.args))
                    with SCPClient(ssh.get_transport()) as scp_client:
                        try:
                            scp_client.put(ruta_origen,ruta_destino+"/"+str(data["id"])+".mp4")
                        except Exception as e:
                            logging.error("error al enviar video {} {}".format(e,e.args))

                    directorio_video = os.path.dirname(ruta_origen)
                    nombre_video = nombre_video.replace(".mp4","-"+str(data["id"])+".mp4")

                    os.rename(ruta_origen, os.path.join(directorio_video, nombre_video))
                     
                observer.on_next(json_de_imagen)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _principal



