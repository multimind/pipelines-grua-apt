import pika
import shutil

ruta_base="/home/gonzalo/sm/yolo_despuntes/qa/alerta_grande"

imagenes=["1735986747_358206_2688_1520.jpg"]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue="imagen_despuntes")
channel.confirm_delivery()

for imagen in imagenes:
    
    ruta=ruta_base+"/"+imagen

    ruta_copiada="/home/gonzalo/sm/pipelines-grua-apt/qa/casos/temporal/"+imagen

    shutil.copy(ruta,ruta_copiada)
    
    channel.basic_publish(exchange='', routing_key="alerta_despunte_grande", body=ruta_copiada)
    i=input()