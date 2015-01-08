import flask 
import string, random, hashlib, os
from werkzeug import secure_filename

#Load config file
config = {}
with open('config.ini', 'r') as file:
	for line in file.read().splitlines():
		line = line.split('==')
		config[line[0]] = line[1]

app = flask.Flask(__name__) #Initialize our application
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 #Set the upload limit to 10MiB
app.secret_key = config['SECRET_KEY']

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
		
		hasher = hashlib.md5() 		
		buf = f.read()		   		
		f.seek(0) #Set cursor back to position 0 so we can read it again in the save function.
									# We hash the file to get its filename.	   		
									# So that we can upload two different images with the same filename,
		hasher.update(buf)	   		# But not two same images with different filenames.
		dirname = genHash(hasher.hexdigest())
		if not os.path.exists("static/files/%s" % dirname): # Check if the folder already exists
			os.mkdir('static/files/%s' % dirname) #Make it
			f.save('static/files/%s/%s' % (dirname, secure_filename(f.filename)))
			print 'Uploaded file \'%s\'' % secure_filename(f.filename) #Log what file was uploaded
			return flask.redirect(flask.url_for('getFile', dirname=dirname,filename=secure_filename(f.filename)))
		else:
			flask.flash('File already exists in %s!' % dirname) #Display a message for the user.
			return flask.redirect(flask.url_for('index'))
	else:
		return flask.render_template('index.html')
		#Return the index to the client.

@app.route('/<dirname>/')
@app.route('/<dirname>/<filename>/')
def getFile(dirname, filename=None): #File delivery to the client
	if filename: #Dir and filename is provided
		return flask.send_from_directory('static/files/%s' % (dirname), filename) #Gets the file 'filename' from the directory /static/files/
	elif not filename: #Filename is absent - we get it for them.
		if os.path.exists('static/files/%s' % dirname): #Does it even exist?
			files = os.listdir('static/files/%s' % dirname)
			if files: #Check if there's any file in the directory.
				return flask.send_from_directory('static/files/%s' % (dirname), files[0])
		else:
			flask.abort(404)


if __name__ == '__main__':
	app.run() #Run our app.