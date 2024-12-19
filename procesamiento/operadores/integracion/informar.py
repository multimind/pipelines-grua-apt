import rx
import os
import requests
import logging
import datetime
from PIL import Image,ImageDraw,ImageFont

def informar_vida(ip_servidor, puerto,dic_hora_envio):
    def _informar_vida(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):

                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                ruta_imagen = os.path.join(ruta_base, nombre_archivo)

                hora_dic_str = dic_hora_envio["hora"]
                hora_actual_str =  datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

                hora_dic = datetime.datetime.strptime(hora_dic_str, "%Y-%m-%d_%H-%M-%S")
                hora_actual = datetime.datetime.strptime(hora_actual_str, "%Y-%m-%d_%H-%M-%S")

                # Restar los objetos datetime
                diferencia = hora_actual - hora_dic
                

                if diferencia.total_seconds() >= 15 * 60:
                    logging.info(f"Diferencia en segundos: {diferencia.total_seconds() / 60}")

                    dic_hora_envio["hora"] = hora_actual_str
                    url = "http://"+ip_servidor+":"+puerto+"/metodos/api-telegram"

                    mensaje = "Imagen de vida "

                    data = {
                        'message': mensaje,
                        'resource': 'image'
                    }
                    
                    with open(ruta_imagen, 'rb') as f:
                        files = {
                            'file': f
                        }

                        response_amazon = requests.post(url, files=files, data=data)
                        logging.info("Respuesta de servidor Telegran-Amazon {}".format(response_amazon))
                    
                    if response_amazon.status_code == 200:
                        logging.info('Recurso de vida subido!')
                    else:
                        logging.error(f'Error al subir recurso de vida: {response_amazon.status_code}')

                
                # Puedes usar la diferencia (timedelta) como necesites

                    
                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _informar_vida



