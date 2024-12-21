import gi
import numpy as np
from PIL import Image

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gst, GLib

from PIL import Image
import time
from datetime import datetime

def on_new_sample(sink):
    sample = sink.emit("pull-sample")

    if not sample:
        return Gst.FlowReturn.ERROR
    
        # Get the buffer from the sample
    buffer = sample.get_buffer()

    # Map the buffer to access the data
    success, map_info = buffer.map(Gst.MapFlags.READ)
    if not success:
        return Gst.FlowReturn.ERROR

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
 
        print(width)
        print(height)

        bpp = 3  # Bytes per pixel for RGB
        expected_size = width * height * bpp
        actual_size = len(map_info.data)

        if actual_size != expected_size:
            print(f"Warning: Buffer size mismatch (expected {expected_size}, got {actual_size})")
            return Gst.FlowReturn.OK

        data = np.frombuffer(map_info.data, np.uint8).reshape((height, width, bpp))

        # Save the image using PIL (optional)
        image = Image.fromarray(data, "RGB")

        timestamp = time.time()

        integer_part = int(timestamp)
        fractional_part = int((timestamp - integer_part) * 1_000_000)

        nombre_captura=integer_part+"_"+fractional_part

        image.save(nombre_captura+".jpg")
        print("Frame saved as frame.jpg")

    finally:
        buffer.unmap(map_info)

    return Gst.FlowReturn.OK

def main():
    # Initialize GStreamer
    Gst.init(None)

    # Create the pipeline
    pipeline = Gst.parse_launch(
        "rtspsrc location=rtsp://192.168.1.102:554/Streaming/Channels/101 user-id=admin user-pw=Hik13579 protocols=tcp ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink"
    )

    # Get the appsink element
    appsink = pipeline.get_by_name("sink")

    # Set the appsink to emit signals
    appsink.set_property("emit-signals", True)
    appsink.set_property("sync", False)

    # Connect the new-sample signal to the callback
    appsink.connect("new-sample", on_new_sample)

    # Start the pipeline
    pipeline.set_state(Gst.State.PLAYING)

    # Run the main loop
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Clean up
        pipeline.set_state(Gst.State.NULL)

# Run the script
if __name__ == "__main__":
    main()
