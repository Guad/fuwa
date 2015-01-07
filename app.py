from flask import Flask, request, render_template
import string, random

app = Flask(__name__)

def genHash(seed):
    base = string.ascii_lowercase+string.digits
    random.seed(seed)
    hash_value = ""
    for i in range(5):
        hash_value += random.choice(base)
    return hash_value


@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		print 'test'
		"""
			NOTE
			SANITIZE INPUT HERE. ON THE TODO LIST.
		"""
		f = request.files['the_file']
		extension = f.filename.split('.')[-1]
		filename = genHash(f.filename) + '.' + extension
		f.save('static/files/%s' % filename)
		return redirect(url_for('getFile', filename=filename))
	else:
		return render_template('index.html')

@app.route('/<filename>/')
def getFile(filename):
	return 'requested file is ' + filename


if __name__ == '__main__':
	app.debug = True
	app.run() 