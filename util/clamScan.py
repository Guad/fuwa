""" Scans the entire files directory and removes any files marked as viruses, adding them to the banlist """
import os, hashlib, random, string
from subprocess import call

def genHash(seed, leng=5):
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

dirs = os.listdir("../static/files/")
hashes = {}
for f in dirs:
    d = "../static/files/" + f + "/"
    if not os.path.isdir(d):
        continue
    of = f
    f = d + os.listdir(d)[0]
    fhash = getmd5(f)
    fname = genHash(fhash)
    hashes[of] = (fname, fhash)

call(["clamscan", "--recursive=yes","--infected", "--remove", "../static/files/"])
banlist = []

for f in dirs:
    d = "../static/files/" + f + "/"
    if not os.path.isdir(d):
        continue
    fname = hashes[f][0]
    fhash = hashes[f][1]
    reason = "virus"
    cleaned = True
    if not os.listdir(d):
        os.rmdir(d)
    else:
        cleaned = False
    if cleaned:
        banlist.append({'hash':fhash, 'filename':fname, 'reason':reason})

with open('../banlist.csv', 'a') as bans:
    for pair in banlist:
        bans.write(pair['hash'] + ',' + pair['filename'] + ',' + pair['reason'] + '\n')
