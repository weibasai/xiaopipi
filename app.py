
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
	return '<h1>welcome to the home of xiaopipi!</h1><img src="static/images/totoro.gif">'

@app.route('/user/<name>')
def hello(name):
	return '<h2>hi, %s' % name