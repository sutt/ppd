from __future__ import print_function # In python 2.7
import sys
from flask import Flask
from flask import send_file
from flask import render_template
app = Flask(__name__)

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
    print('hey', file = sys.stderr)
    return render_template('img_temp.html')

#app.run(host="127.0.0.1", port=5000, threaded=True)
    