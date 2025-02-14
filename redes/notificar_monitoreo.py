import pika
import json
import time

RABBITMQ_HOST = 'localhost' 
QUEUE_NAME = 'reportar_monitoreo'

class NotificadorMonitoreo:
    def __init__(self,segundos_entre_llamadas,mensaje):
        self.delta_envio=delta_envio
        self.tiempo_anterior=time.time()
        self.mensaje=mensaje

    def notificar_monitoreo_rabbit():

        tiempo_actual=time.time()

        transcurrido = tiempo_actual - self.tiempo_anterior

        if transcurrido<self.segundos_entre_llamadas:
            return

        self.tiempo_anterior=time.time()

        try:
            # Connect to RabbitMQ
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()

            # Declare the queue (idempotent operation)
            channel.queue_declare(queue=QUEUE_NAME)

            # Publish the message
            channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=json.dumps(self.mensaje))

            # Close the connection
            connection.close()

        except Exception as e:
            print(f"[!] Error: {e}")

