""" Scans the entire files directory and inserts data into the database. """
import os, hashlib, random, string, sqlite3 as lite
PATH_TO_DB = '../files.db'

def genHash(seed, leng=6):
    """ Generate five letter filenames for our files. """
    base = string.ascii_lowercase + string.digits
    random.seed(seed)
    hash_value = ""
    for i in range(leng):
        hash_value += random.choice(base)
    return hash_value

def getmd5(filename):
    md5 = hashlib.md5()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(8192), b''): 
            md5.update(chunk)
    return md5.hexdigest()

def databaseEntry(fname, fhash, forigname):
    con = lite.connect(PATH_TO_DB)
    with con:
        cur = con.cursor()
        cur.execute('INSERT INTO files (md5Hash, safeName, origName) VALUES (?, ?, ?)', (fhash, fname, forigname))
    con.commit()

def checkEntryExists(fhash):
    con = lite.connect(PATH_TO_DB)
    cur = con.cursor()
    cur.execute('SELECT * FROM files WHERE md5Hash=?', (fhash,))
    data = cur.fetchone()
    return not not data

dirs = os.listdir("../static/files/")
hashes = {}
for f in dirs:
    d = "../static/files/" + f + "/"
    if not os.path.isdir(d):
        continue
    f = d + os.listdir(d)[0]
    fhash = getmd5(f)
    fname = genHash(fhash)
    hashes[f] = (fname, fhash)

for f in dirs:
    d = "../static/files/" + f + "/"
    if not os.path.isdir(d):
        continue
    fpath = d + os.listdir(d)[0]
    fname = hashes[fpath][0]
    fhash = hashes[fpath][1]
    forigname = os.listdir(d)[0]
    if not checkEntryExists(fhash):
        databaseEntry(f, fhash, forigname)
        print("Added %s" % f)