import pika

ruta_base="/home/gonzalo/sm/pipelines-grua-apt/qa/casos/caso_unico"

imagenes=["1735734824_490019_1920_1080.jpg","1735734825_490029_1920_1080.jpg","1735734855_490099_1920_1080.jpg"]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue="imagen_despuntes")
channel.confirm_delivery()

for imagen in imagenes:
    
    ruta=ruta_base+"/"+imagen
    channel.basic_publish(exchange='', routing_key="imagen_despuntes", body=ruta)
    i=input()