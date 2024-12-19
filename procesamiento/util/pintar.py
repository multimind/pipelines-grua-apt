from PIL import Image, ImageDraw
import logging
import rx
import cv2
import requests
import os

def pintar_despunte(ruta_descarga_barra,ruta_factores,ruta_no_factores,zona,telegram_url,chat_id,enviar_alerta,version_modelo, nombre_camara):
    def _cliente_segmentador_barra(source):
        def subscribe(observer, scheduler=None):
        
            def on_next(json_datos):
                ruta_base = json_datos["ruta_base"]
                nombre_archivo = json_datos["nombre_imagen"]
                tipo_de_muestra = json_datos["tipo_de_muestra"]
                boxes = json_datos["boxes_filtrados"]

                despunte_box = []
                for i,tipo in enumerate(tipo_de_muestra):
                    if tipo[1] == "despunte":
                        ruta_muestra =  tipo[0]
                        nombre_muestra = ruta_muestra.split("/")[-1]
                        barra_muestra = nombre_muestra.split("__")[0]
                        num_barra = int(barra_muestra.split("_")[1])
                        print("numero de barra: ",num_barra)

                        segmento_muestra = nombre_muestra.split("__")[1]
                        numero_segmento = segmento_muestra.split("_")[0]
                        print("nombre_muestra: {}\n barra_muestra: {}\n segmento_muestra:{}\n numero_segmento:{}".format(nombre_muestra,barra_muestra,segmento_muestra,numero_segmento))
                        print("ruta_descarga: {} ".format(ruta_descarga_barra+"/"+barra_muestra+".jpg"))

                        #Selecccion de barras

                        x1,y1,x2,y2 = boxes[num_barra]

                        distancia = (x2-x1) // 10

                        if numero_segmento == 0:
                            despunte_box.append([x1, y1, x1 + distancia, y2])
                        else:
                            distancia_final = distancia * int(numero_segmento)
                            despunte_box.append([x1 + distancia_final, y1, x1 + distancia_final + distancia, y2])




                #Dibujo de zona de interes

                poligono_wkt = zona.wkt
                ruta_imagen = ruta_base +"/"+ nombre_archivo
                img = Image.open(ruta_imagen).convert("RGB")
                draw = ImageDraw.Draw(img)
                poligono_str = poligono_wkt.replace("POLYGON ((", "").replace("))", "")
                puntos = [tuple(map(float, point.split())) for point in poligono_str.split(", ")]

                # Dibujar el polígono (contorno)
                #thickness = 5  # Define el grosor deseado
                #for i in range(thickness):
                #    draw.polygon([(x+i, y+i) for x, y in puntos], outline="green")
                #    draw.polygon([(x-i, y-i) for x, y in puntos], outline="green")

                if len(despunte_box) > 0:
                    thickness = 5
                    for box in despunte_box:
                        print("pintando box ", box)
                        for i in range(thickness):
                            x, y, x1, y1 = box
                            draw.rectangle([x-i, y-i, x1-i, y1-i], outline ="red")
                        img.save(ruta_factores+"/"+nombre_archivo)
                else:
                    img.save(ruta_no_factores+"/"+nombre_archivo)

                numero_camara = nombre_camara.split("_")[1]
                if enviar_alerta:
                    if len(despunte_box) > 0:
                        archivo = open(ruta_factores+"/"+nombre_archivo, "rb")
                        mensaje = "Despunte detectado camara {} v{}".format(numero_camara,str(version_modelo))
                    #else:
                    #    archivo = open(ruta_no_factores+"/"+nombre_archivo, "rb")
                    #    mensaje = "No se detecto despunte camara {} v{}".format(numero_camara,str(version_modelo))

                        files = {'photo': archivo}
                        values = {'upload_file': ruta_factores+"/"+nombre_archivo, 'mimetype':'image/jpg','caption':mensaje}
                        url_ = telegram_url + "sendPhoto?chat_id=" + chat_id + "&text=" + mensaje
                        response = requests.post(url_,files=files,data=values)
                        print(response)
                        archivo.close()

                os.remove(ruta_base+"/"+nombre_archivo)
                        
                observer.on_next(json_datos)
            
            return source.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
        
        return rx.create(subscribe)

    return _cliente_segmentador_barra