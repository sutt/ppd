from __future__ import print_function # In python 2.7
import time,os,sys,random
from flask import Flask
from flask import send_file
from flask import render_template
from picamera.array import PiRGBArray
from picamera import PiCamera

app = Flask(__name__)

camera = PiCamera()
rawCapture = PiRGBArray(camera)

time.sleep(.1)
print('camera ready...', file = sys.stderr)

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

@app.route('/take/')
def take_pic():
    t0 = time.time()
    try:
        camera.capture(rawCapture,format="bgr")    
        image = rawCapture.array
        cv2.imwrite("static/img1.jpg",image)
        time.sleep(1)
    except:
        print('nah',  file = sys.stderr)
    t1 = time.time()
    out_str = 'time: ' + str(t1 - t0)
    print out_str
    fn = "static/img1.jpg"
    return send_file(fn, mimetype="img/jpg")
