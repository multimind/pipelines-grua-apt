import pika
import shutil

ruta_base="/home/gonzalo/sm/pipelines-grua-apt/qa/casos/caso_unico"

imagenes=["1735850290_746678_1920_1080.jpg","1735850291_71394_1920_1080.jpg"]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue="imagen_despuntes")
channel.confirm_delivery()

for imagen in imagenes:
    
    ruta=ruta_base+"/"+imagen

    ruta_copiada="/home/gonzalo/sm/pipelines-grua-apt/qa/casos/temporal/"+imagen

    shutil.copy(ruta,ruta_copiada)
    
    channel.basic_publish(exchange='', routing_key="imagen_despuntes", body=ruta_copiada)
    i=input()