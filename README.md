# pipelines-grua-apt

#funciona! permite testear comunicacion
GST_DEBUG=3  gst-launch-1.0 rtspsrc location=rtsp://192.168.1.102:554/Streaming/Channels/101 user-id=admin user-pw=123456 ! fakesink

#funciona!, describe el stream
gst-discoverer-1.0 rtsp://admin:123456@192.168.1.102:554/Streaming/Channels/101 user-id=ad

#funciona!, la camara tiene que estar codificando video en h264
GST_DEBUG=3  gst-launch-1.0 rtspsrc location=rtsp://192.168.1.102:554/Streaming/Channels/101 user-id=admin user-pw=123456 ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! jpegenc ! multifilesink location="frame_%05d.jpg"

#funciona!, decodifica a una cierta velocidad (15frames por segundo en este caso)
GST_DEBUG=3  gst-launch-1.0 rtspsrc location=rtsp://192.168.1.102:554/Streaming/Channels/101 user-id=admin user-pw=123456 ! rtph264depay ! h264parse ! avdec_h264 ! videorate ! video/x-raw,framerate=15/1 ! videoconvert ! jpegenc ! multifilesink location="frame_%05d.jpg"

 