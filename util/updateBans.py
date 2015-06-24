"""Takes a list of files which have been uploaded, deletes them, and adds them to the banlist"""
import sys, os, hashlib, shutil, string, random

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

banlist = []
with open(sys.argv[1], 'r') as fin:
    for f in fin:
        f = f.rstrip() 
        if os.path.isdir("../static/files/" + f):
            f = "../static/files/" + f + "/" + os.listdir("../static/files/" + f)[0]
        fhash = getmd5(f)
        fname = genHash(fhash)
        reason = sys.argv[2]
        banlist.append({'hash':fhash, 'filename':fname, 'reason':reason})
        shutil.rmtree(os.path.abspath(os.path.join(f, os.pardir)))

with open('../banlist.csv', 'a') as bans:
    for pair in banlist:
        bans.write(pair['hash'] + ',' + pair['filename'] + ',' + pair['reason'] + '\n')
          
