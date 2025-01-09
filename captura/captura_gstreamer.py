import gi
import numpy as np
from PIL import Image

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gst, GLib

from PIL import Image
import time
from datetime import datetime
import os
import pika 
from systemd.daemon import notify
import argparse
import configparser

STATUS_FILE = None
ruta_frames=None
nombre_canal=None
frameskip=None
cuentaframe=0

def on_new_sample(sink,user_data):
    global ruta_frames
    global STATUS_FILE
    global nombre_canal
    global cuentaframe
    
    channel=user_data

    sample = sink.emit("pull-sample")

    cuentaframe=cuentaframe+1
    
    if not cuentaframe>=frameskip:
        return Gst.FlowReturn.OK

    cuentaframe=0

    if not sample:
        print("error!!!!")
        return Gst.FlowReturn.ERROR
    
        # Get the buffer from the sample
    buffer = sample.get_buffer()

    # Map the buffer to access the data
    success, map_info = buffer.map(Gst.MapFlags.READ)
    if not success:
        print("==fin mapeo")
    
        return Gst.FlowReturn.ERROR
    print("a0")

    # Convert the raw data into an image
    try:
       
        # Example assumes video is in RGB format
        caps = sample.get_caps()
        structure = caps.get_structure(0)
        format_ = structure.get_string("format")
        print(f"Detected format: {format_}")

        width = structure.get_int("width")[1]
        height = structure.get_int("height")[1]

        if format_ != "RGB":
            print("Unsupported format. Adjust GStreamer pipeline to output RGB.")
            return Gst.FlowReturn.OK

        print("a1")

        bpp = 3  # Bytes per pixel for RGB
        expected_size = width * height * bpp
        actual_size = len(map_info.data)

        if actual_size != expected_size:
            print(f"Warning: Buffer size mismatch (expected {expected_size}, got {actual_size})")
            return Gst.FlowReturn.OK

        data = np.frombuffer(map_info.data, np.uint8).reshape((height, width, bpp))

        # Save the image using PIL (optional)
        image = Image.fromarray(data, "RGB")

        width=1920
        height=1080
        new_size = (width, height)  
        image = image.resize(new_size)

        timestamp = time.time()

        integer_part = int(timestamp)
        fractional_part = int((timestamp - integer_part) * 1_000_000)

        nombre_captura=str(integer_part)+"_"+str(fractional_part)

        nombre_captura=nombre_captura+"_"+str(width)+"_"+str(height)

        nombre_final=ruta_frames+"/"+nombre_captura+".jpg"

        print("nombre_final")
        print(nombre_final)

        image.save(nombre_final)

        print("antes de publicar!!!")
        channel.basic_publish(exchange='', routing_key=nombre_canal, body=nombre_final)
        print("publicado!")
    
    except pika.exceptions.UnroutableError as e:
        print(f"Message could not be routed: {e}")
    finally:
        print("  antes unbuffer")
        if not(buffer is None or map_info is None):
            buffer.unmap(map_info)
        print("  despues buffer")

    print("==fin normal")
    
    #TODO: no escribirlo siempre, solo cada X frames
    with open(STATUS_FILE, "w") as f:
        f.write(str(time.time()))
    
    notify("WATCHDOG=1")

    return Gst.FlowReturn.OK

def main(config):
    global ruta_frames
    global nombre_canal
    global STATUS_FILE
    global frameskip
    global nombre_sink_gstreamer

    nombre_sink_gstreamer=config["CAPTURA"]["nombre_sink_gstreamer"]
    ruta_frames=config["CAPTURA"]["ruta_frames"]
    frameskip=int(config["CAPTURA"]["frameskip"])
    STATUS_FILE=config["CAPTURA"]["archivo_notificacion_servicio_systemd"]
  
    nombre_canal=config["RABBIT"]["nombre_cola"]
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=nombre_canal)
    channel.confirm_delivery()

    os.makedirs("frames", exist_ok=True)
    
    Gst.init(None)
    print(config["CAPTURA"]["pipeline_gstreamer"])

    pipeline = Gst.parse_launch(
        config["CAPTURA"]["pipeline_gstreamer"]
    )

    appsink = pipeline.get_by_name("sink")

    appsink.set_property("emit-signals", True)
    appsink.set_property("sync", False)

    appsink.connect("new-sample", on_new_sample,channel)

    pipeline.set_state(Gst.State.PLAYING)

    loop = GLib.MainLoop()
  
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Clean up
        loop.quit()
        pipeline.set_state(Gst.State.NULL)
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Captura gstreamer')
    parser.add_argument('archivo_configuracion')

    args = vars(parser.parse_args())
    archivo_configuracion = args['archivo_configuracion']

    config = configparser.ConfigParser()
    config.read(archivo_configuracion)

    main(config)
