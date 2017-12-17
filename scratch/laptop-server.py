import io, time, argparse
import socket
import struct
from PIL import Image
import numpy as np
import cv2
from StringIO import StringIO

ap = argparse.ArgumentParser()
ap.add_argument("--noprint", action="store_false")
ap.add_argument("--nodisplay", action="store_false")
args = vars(ap.parse_args())

def convert_image(img_obj):
    return np.array(img_obj)

# def convert_image(img_obj):
#     return np.array(img_obj.convert('RGB'))

def convert_image2(r):
    return Image.open(StringIO(r.content))

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)
i = 0
fps_mod = 8
start_time = 0

connection = server_socket.accept()[0].makefile('rb')
try:
    while True:
        try:
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
        except:
            print 'nah'

        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))
        image_stream.seek(0)

        if args["noprint"]:
            image = Image.open(image_stream)
            print('Image is %dx%d' % image.size)
            image.verify()
            print 'received: ', str(i)

        i+=1

        image = Image.open(image_stream)
        img = convert_image(image)

        if args["nodisplay"]:
            cv2.imshow('feed',img)
            if cv2.waitKey(1)== ord('q'):
                print 'poke a q'

        if args["noprint"]:
            print img.shape
            if i % fps_mod == 0:
                if start_time == 0:
                    start_time = time.time()
                else:
                    fps_calcd = float(fps_mod) / float(time.time() - start_time)
                    print 'FPS: ', str(fps_calcd)
                    start_time = time.time()
        else:
            if i==1:
                print 'started...'

finally:
    connection.close()
    server_socket.close()
    print 'Total is: ', str(i)