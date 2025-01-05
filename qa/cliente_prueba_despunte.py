import pika
import shutil
import configparser
import argparse

#ruta_base="/home/gonzalo/sm/yolo_despuntes/qa"
#imagenes=["1735936153_61937_2688_1520.jpg","1735936168_639607_2688_1520.jpg"]
#ruta_base="/home/gonzalo/sm/yolo_despuntes/qa/caso_trabajador"
#imagenes=["1736056834_552324_2688_1520.jpg"]

def procesar(config):
    ruta_base=config["CASO"]["ruta_base"]
    string_imagenes=config["CASO"]["imagenes"]

    imagenes=string_imagenes.split(",")

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue="imagen_despuntes")
    channel.confirm_delivery()

    for imagen in imagenes:
        
        ruta=ruta_base+"/"+imagen

        ruta_copiada="/home/gonzalo/sm/pipelines-grua-apt/qa/casos/temporal/"+imagen

        shutil.copy(ruta,ruta_copiada)
        
        nombre_canal="imagen_despuntes"
        channel.basic_publish(exchange='', routing_key=nombre_canal, body=ruta_copiada)
        print("imagen: "+ruta+" ha sido enviada a canal: "+nombre_canal)
        print("presione para continuar")
        i=input()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Inicia el pipeline de pruebas')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    procesar(config)