import flask 
import string, random

app = flask.Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

def genHash(seed):
    base = string.ascii_lowercase+string.digits
    random.seed(seed)
    hash_value = ""
    for i in range(5):
        hash_value += random.choice(base)
    return hash_value


@app.route('/', methods=['GET', 'POST'])
def index():
	if flask.request.method == 'POST':
		print 'test'
		"""
			NOTE
			SANITIZE INPUT HERE. ON THE TODO LIST.
		"""
		f = flask.request.files['file']
		extension = f.filename.split('.')[-1]
		filename = genHash(f.filename) + '.' + extension
		f.save('static/files/%s' % filename)
		return flask.redirect(flask.url_for('getFile', filename=filename))
	else:
		return flask.render_template('index.html')

@app.route('/<filename>/')
def getFile(filename):
	return flask.send_from_directory('static/files', filename)


if __name__ == '__main__':
	app.debug = True
	app.run() 