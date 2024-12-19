from PIL import Image, ImageDraw
import logging
import rx
import cv2
import requests
def pintar_box_despunte(ruta_descarga_barra,ruta_factores,ruta_no_factores,zona,telegram_url,chat_id,enviar_alerta,version_modelo, nombre_camara):
    def _cliente_segmentador_barra(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):
                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                boxes_filtrados = json_datos["boxes_filtrados"]
                boxes_despunte = json_datos["boxes_despunte"]

                ruta_imagen = ruta_base +"/"+ nombre_archivo
                img = Image.open(ruta_imagen).convert("RGB")
                draw = ImageDraw.Draw(img)

                if len(boxes_despunte) > 0:
                    for box_barra, box_despunte in zip(boxes_filtrados, boxes_despunte):
                        imagen_con_despunte =  False
                        x1,y1,x2,y2 = box_barra
                        if len(box_despunte) > 0: 
                            for box in box_despunte:

                                x1_despunte,y1_despunte,x2_despunte,y2_despunte = box
                                print("pintando! ", box)

                                x1_final = x1 + x1_despunte
                                y1_final = y1 + y1_despunte
                                x2_final = x1 + x2_despunte
                                y2_final = y1 + y2_despunte

                                print("pintando! ", x1_final,y1_final,x2_final,y2_final)

                                thickness = 5
                                for i in range(thickness):
                                    draw.rectangle([x1_final+i, y1_final+i, x2_final+i, y2_final+i], outline ="red")
                                imagen_con_despunte = True
                    img.save(ruta_factores+"/"+nombre_archivo)
                else:
                    img.save(ruta_no_factores+"/"+nombre_archivo)
                
                numero_camara = nombre_camara.split("_")[1]
                print("aqui")
                print("Despunte detectado camara {} v{}".format(numero_camara,str(version_modelo)))
                if enviar_alerta:
                    if imagen_con_despunte:
                        archivo = open(ruta_factores+"/"+nombre_archivo, "rb")
                        mensaje = "Despunte detectado camara {} v{}".format(numero_camara,str(version_modelo))
                    else:
                        archivo = open(ruta_no_factores+"/"+nombre_archivo, "rb")
                        mensaje = "No se detecto despunte camara {} v{}".format(numero_camara,str(version_modelo))

                    files = {'photo': archivo}
                    values = {'upload_file': ruta_factores+"/"+nombre_archivo, 'mimetype':'image/jpg','caption':mensaje}
                    url_ = telegram_url + "sendPhoto?chat_id=" + chat_id + "&text=" + mensaje
                    response = requests.post(url_,files=files,data=values)
                    print(response)
                    archivo.close()
                        
                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _cliente_segmentador_barra