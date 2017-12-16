import io, time
import socket
import struct
from PIL import Image
import numpy as np
import cv2
from StringIO import StringIO

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
# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb')
try:
    while True:
        # Read the length of the image as a 32-bit unsigned int. If the
        # length is zero, quit the loop
        try:
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
        except:
            print 'nah'
        # Construct a stream to hold the image data and read the image
        # data from the connection
        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))
        # Rewind the stream, open it as an image with PIL and do some
        # processing on it
        image_stream.seek(0)
        if True:
            image = Image.open(image_stream)
            print('Image is %dx%d' % image.size)
            image.verify()
        #print('Image is verified')
        print 'received: ', str(i)
        i+=1
        
        image = Image.open(image_stream)
        img = convert_image(image)
        print img.shape
        cv2.imshow('feed',img)
        if cv2.waitKey(1)== ord('q'):
            print 'poke a q'

        if i % fps_mod == 0:
                if start_time == 0:
                    start_time = time.time()
                else:
                    fps_calcd = float(fps_mod) / float(time.time() - start_time)
                    print 'FPS: ', str(fps_calcd)
                    start_time = time.time()

                    

        
                    

finally:
    connection.close()
    server_socket.close()