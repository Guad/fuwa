from flask import Flask
import string, random

app = Flask(__name__)

def genHash(seed):
    base = string.ascii_lowercase+string.digits
    random.seed(seed)
    hash_value = ""
    for i in range(5):
        hash_value += random.choice(base)
    return hash_value


@app.route('/')
def index():
	return 'file upload goes here'

@app.route('/<filename>/')
def getFile(filename):
	return 'requested file is ' + filename


if __name__ == '__main__':
	app.debug = True
	app.run() 