import flask 
import string, random

app = flask.Flask(__name__) #Initialize our application
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 #Set the upload limit to 10MiB

def genHash(seed): #Generate five letter filenames for our files
    base = string.ascii_lowercase+string.digits 
    random.seed(seed)
    hash_value = ""
    for i in range(5):
        hash_value += random.choice(base)
    return hash_value


@app.route('/', methods=['GET', 'POST'])
def index():
	if flask.request.method == 'POST':
		"""
			File upload happens here.
			We get your filename and convert it to our hash with your extension.
			Then we redirect to the file itself.
		"""
		f = flask.request.files['file']
		extension = f.filename.split('.')[-1]
		filename = genHash(f.filename) + '.' + extension
		f.save('static/files/%s' % filename)
		return flask.redirect(flask.url_for('getFile', filename=filename))
	else:
		return flask.render_template('index.html')
		#Return the index to the client.

@app.route('/<filename>/')
def getFile(filename): #File delivery to the client
	return flask.send_from_directory('static/files', filename)
	#Gets the file 'filename' from the directory /static/files/


if __name__ == '__main__':
	app.run() #Run our app.