import time
import gi
from gi.repository import Gst, GObject
from datetime import datetime

gi.require_version('Gst', '1.0')

# Initialize GStreamer
Gst.init(None)

# Create the pipeline
pipeline = Gst.parse_launch(
    "rtspsrc location=rtsp://192.168.1.102:554/Streaming/Channels/101 user-id=admin user-pw=Hik13579 ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! jpegenc ! appsink name=sink"
)

# Get the appsink element
appsink = pipeline.get_by_name("sink")

def on_new_sample(sink):
    sample = sink.emit("pull-sample")
    if sample:
        # Get timestamp from sample (seconds since epoch)
        timestamp = sample.get_buffer().pts / Gst.SECOND
        timestamp_str = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S-%f')

        # Get the frame and save it as a JPEG file with the timestamp
        caps = sample.get_caps()
        width = caps.get_structure(0).get_int("width")[1]
        height = caps.get_structure(0).get_int("height")[1]
        buffer = sample.get_buffer()

        # Create the filename based on the timestamp
        filename = f"frame_{timestamp_str}.jpg"

        # Save the frame as an image
        success, map_info = buffer.map(Gst.MapFlags.READ)
        if success:
            with open(filename, "wb") as f:
                f.write(map_info.data)
            buffer.unmap(map_info)

    return Gst.FlowReturn.OK

# Connect the signal for new sample
appsink.connect("new-sample", on_new_sample)

# Start the pipeline
pipeline.set_state(Gst.State.PLAYING)

# Run the GStreamer main loop
loop = GObject.MainLoop()
try:
    loop.run()
except KeyboardInterrupt:
    pass

# Stop the pipeline
pipeline.set_state(Gst.State.NULL)
