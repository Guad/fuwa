import string, random, hashlib, os, json, sqlite3 as lite
from time import strftime
from shutil import rmtree
from waitress import serve
from flask import Flask, url_for, flash, Markup, render_template, request, redirect, abort, send_from_directory
from werkzeug import secure_filename
from subprocess import call
from threading import Timer

# Load config file
config = {}
with open('config.ini', 'r') as configuration:
    for line in configuration.read().splitlines():
        line = line.split('==')
        config[line[0]] = line[1]

dangerousExtensions = ['zip', 'rar', '7z', 'dll', 'exe', 'com']
bannedExtensions = ['ade', 'adp', 'bat', 'chm', 'cmd', 'com',
                    'cpl', 'exe', 'hta', 'ins', 'isp', 'jse',
                    'lib', 'lnk', 'mde', 'msc', 'msp', 'mst',
                    'pif', 'scr', 'sct', 'shb', 'sys', 'vb',
                    'vbe', 'vbs', 'vxd', 'wsc', 'wsf', 'wsh']
BANEXTENSIONS = True # Main switch
UPLOAD_LIMIT = 10 * 1024 * 1024 # 10MiB upload limit

banlist = []
def reloadBanlist(update=True):
    """
    Load banlist, you must create an empty file named
    'banlist.csv' in the root directory first.
    """
    global banlist
    print('[%s] Starting banlist reload.' % strftime('%H:%M:%S'))
    banlist = []
    entries = 0
    with open('banlist.csv', 'r') as bans:
        for line in bans.read().splitlines():
            if len(line) == 0: 
                continue
            entries += 1
            line = line.split(',');
            banlist.append({'hash':line[0], 'filename':line[1], 'reason':line[2]})
    print('[%s] Banlist reload complete. Found %i entries.' % (strftime('%H:%M:%S'), entries))
    if update:
        tim = Timer(60 * 30, reloadBanlist) # every 30 minutes
        tim.daemon = True
        tim.start()

reloadBanlist()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = UPLOAD_LIMIT  
app.secret_key = config['SECRET_KEY']

def genHash(seed, leng=6):
    """ Generate five letter filenames for our files. """
    base = string.ascii_lowercase + string.digits
    random.seed(seed)
    hash_value = ""
    for i in range(leng):
        hash_value += random.choice(base)
    return hash_value

def getDirnameExtension(f):
    """ 
    Gets the dirname and extension of the file. 
    Checks for file hash collision and then for unique filename collision.
    """
    hasher = hashlib.md5()
    buf = f.read()
    f.seek(0)
    hasher.update(buf)
    finalHash = hasher.hexdigest()
    dirname = genHash(finalHash)

    extension = ''
    tmpExt = ''
    if(len(f.filename.split('.')) != 1):
        if('.'.join(f.filename.split('.')[-2:]) == 'tar.gz'):
            extension = '.'.join(f.filename.split('.')[-2:])
        else:
            extension = f.filename.split('.')[-1]
        tmpExt = '.' + extension
        dirname += tmpExt

    """
    1. Check if md5 Hash exists in files.db
    2. Check if generated ufn exists in files.db
    3. If it does, add salt and re-do
    4. 5 tries maximum.
    """

    con = lite.connect('files.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM files WHERE md5Hash=?', (finalHash,))
    data = cur.fetchone()

    if data: # Duplicate
        return [dirname, extension, '', True]

    tries = 0
    maxTries = 5
    while tries < maxTries:
        cur.execute('SELECT * FROM files WHERE safeName=?', (dirname,))
        data = cur.fetchone()
        if data:
            # Collision
            dirname = genHash(finalHash + 'thisisnotasecret') + tmpExt
        else:
            break
    con.close()    
    return [dirname, extension, finalHash, False]

def writeBanlist():
    """
    Format example:
    6a9101971cb90eb4310013c0eff14397,f7a8f,virus
    f5dbef316466ea3552dafedae68e2841,fa212,cheesepizza
    """
    with open('banlist.csv', 'w') as bans:
        for pair in banlist:
            bans.write(pair['hash'] + ',' + pair['filename'] + ',' + pair['reason'] + '\n')

def addToBanlist(fhash, fname, reason):
    reloadBanlist(update=False)
    banlist.append({'hash':fhash, 'filename':fname, 'reason':reason})
    writeBanlist()

def checkFileHash(fhash): # returns: true for clean and false for dirty.
    return not any(d['hash'] == fhash for d in banlist)

def checkFileName(fname):
    return not any(d['filename'] == fname for d in banlist)

def databaseEntry(fname, fhash, forigname):
    con = lite.connect('files.db')
    with con:
        cur = con.cursor()
        cur.execute('INSERT INTO files (md5Hash, safeName, origName) VALUES (?, ?, ?)', (fhash, fname, forigname))
    con.commit()

def databaseRemoval(fhash):
    con = lite.connect('files.db')
    with con:
        cur = con.cursor()
        cur.execute('DELETE FROM files WHERE md5Hash=?', (fhash,))
    con.commit()

def createDatabaseTable():
    con = lite.connect('files.db')
    with con:
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS files '
            + '(md5Hash TEXT, safeName TEXT, origName TEXT, '
            + 'dateUploaded TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

def scanForViruses(dirname, fname, fhash, extension):
    fpath = 'static/files/%s/%s' % (dirname, fname)
    # Uses clamd, you must have it installed for this to work.
    call(["clamscan", "--quiet","--infected", "--remove", fpath])
    # If the file was removed, return False(There is a virus), otherwise True
    if not os.path.exists(fpath):
        dirtolog = dirname
        if(len(extension) != 0):
            dirtolog = dirname.rstrip('.' + extension)
        addToBanlist(fhash, dirtolog, 'virus')
        print('[VIRUS DETECTED] in file "%s", added to banlist and removed.' % fname)
        rmtree('static/files/%s' % dirname) # #scary
        databaseRemoval(fhash)

def handleUpload(f, js=True, api=False):
    """ Handles the main file upload behavior. """
    value = ""
    jsonDict = {}
    dirname, extension, fhash, duplicate = getDirnameExtension(f)
    if secure_filename(f.filename) and (not extension in bannedExtensions or not BANEXTENSIONS):
        # get variables
        sfilename = secure_filename(f.filename)
        if checkFileHash(fhash):
            # do the file saving
            if not duplicate:
                # if it it's not there, make the directory and save the file
                os.mkdir('static/files/%s' % dirname)
                f.save('static/files/%s/%s' % (dirname, sfilename))
                databaseEntry(dirname, fhash, sfilename)
                if(extension in dangerousExtensions):
                    t = Timer(60, scanForViruses, [dirname, sfilename, fhash, extension])
                    t.daemon = True
                    t.start()
                print('Uploaded file "%s" to %s' % (sfilename, dirname))

                # value is used with /js route, otherwise it's ignored
                url = url_for('getFile', dirname=dirname)
                if not api:
                    value = 'success:' + url + ':' + dirname
                else:
                    value = 'https://fuwa.se/' + dirname
                    jsonDict['status'] = 'success'
                    jsonDict['filename'] = dirname
                    jsonDict['url'] = value
                # if not js, then flash
                # used to prevent flashes from showing up upon refresh
                if not js:
                    message = 'Uploaded file %s to <a href="%s">%s</a>'
                    flash(Markup(message) % (sfilename, url, dirname))
            else:
                url = url_for('getFile', dirname=dirname)
                if not api:
                    value = 'exists:' + url + ':' + dirname
                else:
                    jsonDict['status'] = 'error'
                    jsonDict['error'] = 'exists'
                    jsonDict['url'] = url
                if not js:
                    message = 'File %s already exists at <a href="%s">%s</a>'
                    flash(Markup(message) % (sfilename, url, dirname))
        else: # This file is b&
            if not api:
                value = 'banned'
            else:
                jsonDict['status'] = 'error'
                jsonDict['error'] = 'banned'
            if not js:
                message = 'This file has been banned for violating our rules.'
                flash(Markup(message))
    else:
        value = 'error:filenameinvalid'
        if not js:
            flash('Invalid filename.', url_for('getIndex'))
        if api:
            jsonDict['status'] = 'error'
            jsonDict['error'] = 'invalidFilename'

    if not api:
        return value
    else:
        return jsonDict

@app.route('/', methods=['GET'])
def getIndex():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def postIndex():
    """
    File upload happens here.
    We get your filename and convert it to our hash with your extension.
    Then we redirect to the file itself.

    As we are using javascript upload, this is left for noscript users.
    """
    uploaded = request.files.getlist("file[]")
    for f in uploaded:
        handleUpload(f, js=False)
    return redirect(url_for('getIndex'))

@app.route('/api/upload', methods=['POST'])
def postIndexAPI():
    """
    This will handle uploads to the API, returning a JSON consisting
    of a list of uploaded files, with their respective statuses and
    uploaded URLs.
    """
    uploaded = request.files.getlist("file[]")
    res = []
    for f in uploaded:
        v = handleUpload(f, js=False, api=True)
        res.append(v)
    return json.dumps(res)

@app.route('/js', methods=['POST'])
def indexJS():
    """
    File upload for the js happens here.
    the normal one acts as a fallback.
    """
    uploaded = request.files.getlist("file[]")
    # handling value this way allows for multiple uploads to work
    # not that the web gui does this at the moment, but it's nice through curl
    value = []
    for f in uploaded:
        v = handleUpload(f)
        value.append(v)
    # it will return the return values delimited by a newline
    # doesn't break existing functionality
    return '\n'.join(value)

@app.route('/<dirname>')
@app.route('/<dirname>/<filename>')
def getFile(dirname, filename=None):
    """
    Flie delivery to the client.
    """
    if not checkFileName(dirname.split('.')[0]):
        abort(410)
    if filename:
        # If dir and filename  is provided, serve it directly
        return send_from_directory('static/files/%s' % dirname, filename)
    elif not filename:
        # Otherwise, find the filename and redirect back with it
        if os.path.exists('static/files/%s' % dirname):
            files = os.listdir('static/files/%s' % dirname)
            if files:
                # redirect back
                return redirect(url_for('getFile', dirname=dirname, filename=files[0]))
        else:
            abort(404)

@app.errorhandler(404) # Not found
def fileNotFound(e):
    return render_template('404.html'), 404

@app.errorhandler(410) # Removed
def fileRemoved(e):
    return render_template('410.html'), 410

if __name__ == '__main__':
    createDatabaseTable()
    #app.debug = True
    #app.run(host="0.0.0.0")
    serve(app, port=8002)
