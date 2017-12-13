from __future__ import print_function # In python 2.7
import time,os,sys,random, cv2
from flask import Flask
from flask import send_file
from flask import render_template
from picamera.array import PiRGBArray
from picamera import PiCamera

app = Flask(__name__)

camera = PiCamera()
camera.start_preview()
time.sleep(2)
#rawCapture = PiRGBArray(camera)

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
    t = []
    fs = []
    for i in range(10):
        fs.append(open('static/pic' + i + '.jpg', 'wb'))
    
    try:
        for i in range(10):
            t0 = time.time()
            camera.capture(fs[i])
            t1 = time.time()
            t.append(t1 - t0)
        for _t in t:
            print(str(_t), file=sys.stderr)
        image = rawCapture.array
        cv2.imwrite("static/img1.jpg",image)
        #time.sleep(1)
    except Exception as e:
        print(e.message,  file = sys.stderr)
    t1 = time.time()
    out_str = 'time: ' + str(t1 - t0)
    print(out_str, file=sys.stderr)
    fn = "static/pic1.jpg"
    f[0].close()
    return send_file(fn, mimetype="img/jpg")

