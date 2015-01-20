import string
import random
import hashlib
import os
from time import strftime
from threading import Timer
from shutil import rmtree

import flask
from werkzeug import secure_filename


# Load config file
config = {}
with open('config.ini', 'r') as configuration:
    for line in configuration.read().splitlines():
        line = line.split('==')
        config[line[0]] = line[1]

app = flask.Flask(__name__)  # Initialize our application
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Set the upload limit to 10MiB
app.secret_key = config['SECRET_KEY']


def genHash(seed, leng=5):  # Generate five letter filenames for our files
    base = string.ascii_lowercase + string.digits
    random.seed(seed)
    hash_value = ""
    for i in range(leng):
        hash_value += random.choice(base)
    return hash_value


def rememberFile(dirname=None, filename=None):  # Add or read public files
    with open('publicFiles.ini', 'a+') as ghettoFile:
        if dirname and filename:  # Are arguments provided?
            ghettoFile.write(dirname + ' ' + filename + ' ' + strftime("%d/%m/%Y") + '\n')
        else:  # No they're not, we want to read the file.
            ghettoDB = []
            for ghettoRow in ghettoFile.read().splitlines():
                ghettoRow = ghettoRow.split()
                ghettoDB.append({'DIRNAME': ghettoRow[0], 'FILE': ghettoRow[1], 'TIME': ghettoRow[2]})
                # Make a list with the files
            ghettoDB.reverse()  # Most recent files are shown first.
            return ghettoDB


def destroyFile(dirname):
    try:
        print 'Removing file', dirname
        rmtree('static/files/%s' % dirname)
    except:
        pass  # The file probably doesn't exists so we carry on.


@app.route('/', methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
        """
			File upload happens here.
			We get your filename and convert it to our hash with your extension.
			Then we redirect to the file itself.
		"""
        uploaded = flask.request.files.getlist("file[]")
        for f in uploaded:
            if secure_filename(f.filename):
                hasher = hashlib.md5()
                buf = f.read()
                f.seek(0)  # Set cursor back to position 0 so we can read it again in the save function.
                # We hash the file to get its filename.
                # So that we can upload two different images with the same filename,
                hasher.update(buf)  # But not two same images with different filenames.
                if flask.request.form.get('suicide'):
                    dirname = genHash(hasher.hexdigest(), 8)
                else:
                    dirname = genHash(hasher.hexdigest())
                if not os.path.exists("static/files/%s" % dirname):  # Check if the folder already exists
                    os.mkdir('static/files/%s' % dirname)  # Make it
                    f.save('static/files/%s/%s' % (dirname, secure_filename(f.filename)))
                    print 'Uploaded file "%s" to %s' % (
                        secure_filename(f.filename), dirname)  # Log what file was uploaded
                    if flask.request.form.get('public') and not flask.request.form.get(
                            'suicide'):  # Did he check that box? Note that suicides can't be public.
                        rememberFile(dirname, secure_filename(f.filename))
                    flask.flash(flask.Markup('Uploaded file %s to <a href="%s">%s</a>') % (secure_filename(f.filename),
                                                                                           flask.url_for('getFile',
                                                                                                         dirname=dirname,
                                                                                                         filename=secure_filename(
                                                                                                             f.filename)),
                                                                                           dirname))  # Feedback to the user with the link.
                else:
                    flask.flash(flask.Markup('File %s already exists at <a href="%s">%s</a>') % (
                        secure_filename(f.filename), flask.url_for('getFile', dirname=dirname),
                        dirname))  # Feedback to the user with the link
            else:
                flask.flash('Invalid filename.', flask.url_for(index))

        return flask.redirect(flask.url_for('index'))  # Files are done uploading, go to index to receive the messages.
    else:
        return flask.render_template('index.html', posts=rememberFile())
        # Return the index to the client.


@app.route('/<dirname>')
@app.route('/<dirname>/<filename>')
def getFile(dirname, filename=None):  # File delivery to the client
    if filename:  # Dir and filename is provided
        if len(dirname) == 8:  # This is a suicide file
            d = []
            d.append(dirname)  # Timer needs a list as an argument.
            Timer(30, destroyFile, d).start()  # He has 30 seconds to download the file
            return flask.send_from_directory('static/files/%s' % dirname,
                                             filename)  # Gets the file 'filename' from the directory /static/files/
        else:
            return flask.send_from_directory('static/files/%s' % dirname,
                                             filename)  # Gets the file 'filename' from the directory /static/files/
    elif not filename:  # Filename is absent - we get it for them.
        if os.path.exists('static/files/%s' % dirname):  # Does it even exist?
            files = os.listdir('static/files/%s' % dirname)
            if files:  # Check if there's any file in the directory.
                return flask.redirect(flask.url_for('getFile', dirname=dirname, filename=files[0]))
                # Resend to the proper location to avoid file corruptions.
        else:
            flask.abort(404)  # File has not been found.


if __name__ == '__main__':
    app.run()  #Run our app.