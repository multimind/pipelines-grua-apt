import rx
import logging
import requests
import os

def alerta_imagen(variables_globales,url, chat):

    def _principal(source):

        def subscribe(observer, scheduler = None):

            def on_next(datos):

                try:
                    json = datos

                    if(variables_globales["alerta"]=="si"):

                        imagen_a_enviar = json["ruta_base"] +'/' + json["nombre_imagen"]
                        
                        canal = chat

                        archivo = open(imagen_a_enviar,'rb')
                        
                        mensaje="Trabajador en zona prohibida"
                        
                        url_ = url + "sendPhoto?chat_id=" + canal + "&text=" + mensaje

                        files={'photo': archivo}
                        values={'upload_file' : imagen_a_enviar, 'mimetype':'image/jpg','caption':mensaje }

                        response = requests.post(url_,files=files,data=values)
                        archivo.close()

                except Exception as err:
                    print(err)
                    logging.error("Exception occurred", exc_info=True)


                observer.on_next(json)


            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)

    return _principal