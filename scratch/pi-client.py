import io, random
import socket
import struct
import time, argparse
import picamera

ap = argparse.ArgumentParser()
ap.add_argument("--ip", type=str, default='10.0.0.123')
ap.add_argument("--port", type=str, default='8000')
ap.add_argument("--runtime", type=str, default='30')
ap.add_argument("--videoport", action="store_true")
ap.add_argument("--skipper", action="store_true")
ap.add_argument("--bigger", action="store_true")
ap.add_argument("--burst", action="store_true")
ap.add_argument("--silenttimer", action="store_true")
ap.add_argument("--nodisplay", action="store_false")
args = vars(ap.parse_args())

# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server)
client_socket = socket.socket()
client_socket.connect((args["ip"], int(args["port"])))
print 'connected'
i=0
fps_mod = 8
start_time = 0
timelist = []
# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    with picamera.PiCamera() as camera:
        if args["bigger"]:
            camera.resolution = (1280, 720)    
        else:
            camera.resolution = (640, 480)
        # Start a preview and let the camera warm up for 2 seconds
        #camera.start_preview()
        time.sleep(2)
        print 'starting reads'

        # Note the start time and construct a stream to hold image data
        # temporarily (we could write it directly to connection but in this
        # case we want to find out the size of each capture first to keep
        # our protocol simple)
        start = time.time()
        stream = io.BytesIO()
        for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=args["videoport"], burst = args["burst"]):
            
            if args["nodisplay"]:
                if i % fps_mod == 0:
                    if start_time == 0:
                        start_time = time.time()
                    else:
                        fps_calcd = float(fps_mod) / float(time.time() - start_time)
                        print 'FPS: ', str(fps_calcd)
                        start_time = time.time()
                
            i += 1

            if args["skipper"]:
                if (random.uniform(0,1) > 0.5):
                #if (i % 2 == 0):
                    print 'skip'
                    continue
        
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            stream.seek(0)
            connection.write(stream.read())
            stream.seek(0)
            stream.truncate()
            if args["nodisplay"]:
                print 'capture: ', str(i)

            if args["silenttimer"]:
                if i != 1:
                    timelist.append(str(time.time() - time_last))
                time_last = time.time()
            
            if time.time() - start > int(args["runtime"]):
                break
            
                
    # Write a length of zero to the stream to signal we're done
    connection.write(struct.pack('<L', 0))
finally:
    connection.close()
    client_socket.close()
    if args["silenttimer"]:
        print 'writing ', str(len(timelist)), ' lines to perf.txt'
        f = open('perf.txt','w')
        f.write('\n'.join(timelist))
        f.close()

