import io
import socket
import struct
import time, argparse
import picamera

ap = argparse.ArgumentParser()
ap.add_argument("--ip", type=str, default='10.0.0.123')
ap.add_argument("--videoport", action="store_true")
ap.add_argument("--burst", action="store_true")
args = vars(ap.parse_args())

# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server)
client_socket = socket.socket()
client_socket.connect((args["ip"], 8000))
print 'connected'
i=0
fps_mod = 8
start_time = 0
# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        # Start a preview and let the camera warm up for 2 seconds
        camera.start_preview()
        time.sleep(2)
        print 'starting reads'

        # Note the start time and construct a stream to hold image data
        # temporarily (we could write it directly to connection but in this
        # case we want to find out the size of each capture first to keep
        # our protocol simple)
        start = time.time()
        stream = io.BytesIO()
        for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=args["videoport"], burst = args["burst"]):
            # Write the length of the capture to the stream and flush to
            # ensure it actually gets sent
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            # Rewind the stream and send the image data over the wire
            stream.seek(0)
            connection.write(stream.read())
            # If we've been capturing for more than 30 seconds, quit
            if time.time() - start > 30:
                break
            # Reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
            print 'capture: ', str(i)
            i += 1
            if i % fps_mod == 0:
                if start_time == 0:
                    start_time = time.time()
                else:
                    fps_calcd = float(fps_mod) / float(time.time() - start_time)
                    print 'FPS: ', str(fps_calcd)
                    start_time = time.time()
                
    # Write a length of zero to the stream to signal we're done
    connection.write(struct.pack('<L', 0))
finally:
    connection.close()
    client_socket.close()