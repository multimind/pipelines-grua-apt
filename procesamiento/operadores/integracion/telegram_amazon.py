import rx
import os
import requests
import logging
def enviar_imagen_factor(ip_servidor, puerto,enviar_alerta_telegram, modo):
    def _cliente_segmentador_barra(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):
                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                ruta_imagen = ruta_base +"/"+ nombre_archivo

                enviar_alerta = json_datos["enviar_alerta"]

                if enviar_alerta and enviar_alerta_telegram:
                    ruta_factor = json_datos["ruta_factor"]
                    logging.info("Enviando imagen telegram {}".format(ruta_factor))
                    mensaje = json_datos["mensaje"]

                    #url = "http://3.87.52.239:8000/metodos/api-telegram"
                    url = "http://"+ip_servidor+":"+puerto+"/metodos/api-telegram"


                    data = {
                        'message': mensaje,
                        'resource': 'image',
                        'env': modo
                    }
                    
                    with open(ruta_factor, 'rb') as f:
                        files = {
                            'file': f
                        }

                        response_amazon = requests.post(url, files=files, data=data)
                        logging.info("Respuesta de servidor Telegran-Amazon {}".format(response_amazon))
                    
                    if response_amazon.status_code == 200:
                        logging.info('Recurso subido!')
                    else:
                        logging.error(f'Error al subir recurso: {response_amazon.status_code}')
                        #logging.error(response_amazon)

                    #os.remove(ruta_imagen)
                    
                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _cliente_segmentador_barra



