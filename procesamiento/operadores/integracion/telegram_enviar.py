import rx
import os
import requests
import logging

from datetime import datetime

def enviar_imagen_factor(chat_id,telegram_url,enviar_alerta_telegram):
    def _cliente_segmentador_barra(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):
                print("==dentro enviar alerta")

                enviar_alerta = json_datos["enviar_alerta"]

                if enviar_alerta and enviar_alerta_telegram:

                    current_time = datetime.now()

                    ultima_alerta=variables_globales["ultima_alerta"]

                    confirmar_alerta=False

                    if ultima_alerta==None:
                        confirmar_alerta=True
                    else:

                        diferencia=current_time-ultima_alerta

                        if diferencia.seconds < 60:
                            confirmar_alerta=False
                        else
                            confirmar_alerta=True

                    if confirmar_alerta=True:
                        ruta_factor = json_datos["ruta_factor"]
                        logging.info("Enviando imagen telegram {}".format(ruta_factor))
                        mensaje = json_datos["mensaje"]

                        archivo = open(ruta_factor, "rb")

                        files = {'photo': archivo}
                        values = {'upload_file': ruta_factor, 'mimetype':'image/jpg','caption':mensaje}
                        url_ = telegram_url + "sendPhoto?chat_id=" + chat_id + "&text=" + mensaje
                        response = requests.post(url_,files=files,data=values)
                        archivo.close()

                        logging.info("Respuesta de servidor Telegran-Amazon {}".format(response))
                        
                        if response.status_code == 200:
                            logging.info('Recurso subido!')
                        else:
                            logging.error(f'Error al subir recurso: {response.status_code}')

                        variables_globales["ultima_alerta"]=current_time
                    #os.remove(ruta_imagen)

                print("==fin  enviar alerta")        
                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _cliente_segmentador_barra



