import pika
import shutil


#ruta_base="/home/gonzalo/sm/yolo_despuntes/qa"
#imagenes=["1735936153_61937_2688_1520.jpg","1735936168_639607_2688_1520.jpg"]

ruta_base="/home/gonzalo/sm/yolo_despuntes/qa/caso_trabajador"
imagenes=["1736056834_552324_2688_1520.jpg"]



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