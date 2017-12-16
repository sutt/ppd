from __future__ import print_function # In python 2.7
import time,os,sys,random, cv2
from flask import Flask
from flask import send_file
from flask import render_template
from picamera.array import PiRGBArray
from picamera import PiCamera
from io import BytesIO

app = Flask(__name__)

class Camera():
    
    def __init__(self,**kwargs):
        self.camera = PiCamera(resolution=(640,480))
        self.pause_time = 2
        self.rawCapture = PiRGBArray(self.camera)

        if kwargs.get('start_preview',False):
            self.camera.start_preview()
            time.sleep(self.pause_time)
            
        time.sleep(self.pause_time)
        print('camera ready...', file = sys.stderr)

    def set_resolution(self, w, h):
        self.camera.resolution = (w,h)

    def get_resoltuion(self):
        """We don't know how to do this"""
        return self.camera.resolution

    def set_fps(self, fps):
        self.camera.fps = fps

    def configure_basic(self):
        self.set_resolution(w = 640, h = 480)
        
        time.sleep(self.pause_time)
        print('camera configured...', file=sys.stderr)
        
        

cam = Camera()
cam.configure_basic()

my_stream = BytesIO

print('Launching Flask...', file = sys.stderr)


@app.route('/camclass/')
def cam_class():
    fn = "static/camclass.jpg"
    t0 = time.time()
    try:
        cam.camera.capture(cam.rawCapture, format="bgr")
        image = cam.rawCapture.array
        cv2.imwrite(fn,image)
        time.sleep(1)
    except Exception as e:
        print(e.message,  file = sys.stderr)
    
    t1 = time.time()
    out_str = 'time: ' + str(t1 - t0)
    print(out_str, file=sys.stderr)
    return send_file(fn, mimetype="img/jpg")



@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/pic/')
def banner():
    return send_file("static/myb2.jpg", mimetype="img/jpg")
    
@app.route('/pic_i/<ij>')
def get_pic(ij):
    fn = 'static/' + str(ij) + ".jpg"
    return send_file(fn, mimetype="img/jpg")

@app.route('/browser/')
def ret_html():
    return render_template('img_temp.html')

@app.route('/takeverysimple/')
def take_very_simple():
    
    t0 = time.time()
    try:
        camera.capture('static/verysimple.jpg')
        time.sleep(1)
    except Exception as e:
        print(e.message,  file = sys.stderr)
    
    t1 = time.time()
    out_str = 'time: ' + str(t1 - t0)
    print(out_str, file=sys.stderr)
    
    fn = "static/verysimple.jpg"
    return send_file(fn, mimetype="img/jpg")




@app.route('/takesimple/')
def take_simple():
    
    t0 = time.time()
    try:
        camera.capture(rawCapture, format="bgr")
        image = rawCapture.array
        cv2.imwrite("static/simple.jpg",image)
        time.sleep(1)
    except Exception as e:
        print(e.message,  file = sys.stderr)
    
    t1 = time.time()
    out_str = 'time: ' + str(t1 - t0)
    print(out_str, file=sys.stderr)
    
    fn = "static/simple.jpg"
    return send_file(fn, mimetype="img/jpg")


@app.route('/take/')
def take_pic():
    t = []
    fs = []
    for i in range(10):
        fn = 'static/pic' + str(i) + '.jpg'
        fs.append(open(fn, 'wb'))
    
    try:
        for i in range(10):
            t0 = time.time()
            camera.capture(fs[i])
            t1 = time.time()
            t.append(t1 - t0)
        for _t in t:
            print(str(_t), file=sys.stderr)
        camera.capture(rawCapture, format="bgr")
        image = rawCapture.array
        cv2.imwrite("static/img1.jpg",image)
        time.sleep(1)
    except Exception as e:
        print(e.message,  file = sys.stderr)
    t1 = time.time()
    out_str = 'time: ' + str(t1 - t0)
    print(out_str, file=sys.stderr)
    fn = "static/img1.jpg"
    fs[0].close()
    return send_file(fn, mimetype="img/jpg")

@app.route('/take2/')
def take_pic2():
    
    t = []
    # Set ISO to the desired value
    for i in range(10):
        t0 = time.time()
        camera.capture('static/out1.jpg')
        t1 = time.time()
        t.append(t1-t0)
    for _t in t:
        print(_t, file=sys.stderr)
    return 'done'
    

@app.route('/take3/')
def take_pic3():
    t0 = time.time()
    camera.capture_sequence(['image%02d.jpg' % i for i in range(10)])
    t1 = time.time()
    _t = t1- t0
    print(_t, file=sys.stderr)
    return 'done.'

@app.route('/take4/')
def take_pic4():
    t0 = time.time()
    print('START', file=sys.stderr)
    for i in  range(10):
        camera.capture(my_stream,format = 'jpeg')
        print('taken', file=sys.stderr)
        #my_stream.flush()
    t1 = time.time()
    _t = t1- t0
    print(_t, file=sys.stderr)
    my_stream.close()
    return 'done'

@app.route('/take5/')
def take_pic5():
    with PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.start_preview()
        time.sleep(2)
        start = time.time()
        camera.capture_sequence((
            'image%03d.jpg' % i
            for i in range(120)
            ), use_video_port=True)
        print('done.', file=sys.stderr)
        print('Captured 120 images at %.2ffps' % (120 / (time.time() - start)), file=sys.stderr)
        camera.stop_preview()
    return 'done.'

@app.route('/take6/')
def take_pic6():
    with PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 60
        camera.start_preview()
        time.sleep(2)
        start = time.time()
        camera.capture_sequence((
            'static/image%03d.jpg' % i
            for i in range(120)
            ), use_video_port=True)
        print('done.', file=sys.stderr)
        print('Captured 120 images at %.2ffps' % (120 / (time.time() - start)), file=sys.stderr)
        camera.stop_preview()
    return send_file('static/image119.jpg', mimetype='img/jpg')

    