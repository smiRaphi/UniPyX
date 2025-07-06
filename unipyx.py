import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import re,json,traceback
from shutil import rmtree
from lib.dldb import DLDB,xopen
from lib.main import extract as _extract
TRIDR = re.compile(r'(\d{1,3}\.\d)% \(.*\) (.+) \(\d+(?:/\d+){1,2}\)')

TDB:dict = json.load(xopen('lib/tdb.json'))
TDBF = set(sum(TDB.values(),[]))
db = DLDB()

def analyze(inp:str):
    _,o,_ = db.run(['trid','-n:5',inp])
    trid = TRIDR.findall(o)
    ts = []
    for x in trid:
        if float(x[0]) <= 10 or not x[1].lower() in TDBF: continue
        for t in TDB:
            if x[1].lower() in TDB[t]: ts.append(t)
    if not ts: print(trid)
    return ts
def extract(inp:str,out:str,ts:list[str]=None):
    out = os.path.abspath(out).replace('/','\\')
    assert not os.path.exists(out),'Output directory already exists'
    inp = os.path.abspath(inp).replace('/','\\')
    if ts == None: ts = analyze(inp)
    assert ts,'Unknown file type'

    for x in ts:
        print('Trying with',x)
        os.makedirs(out,exist_ok=True)
        if not _extract(inp,out,x,db):break
        rmtree(out)
    else: raise Exception("Could not extract")
    print('Extracted successfully to',out)

if __name__ == '__main__':
    from sys import argv

    inp = argv[1]
    if len(argv) > 2: out = argv[2]
    else:
        out = os.path.splitext(inp)[0]
        c = 1
        while os.path.exists(out): out = os.path.splitext(inp)[0] + '_' + str(c);c += 1
    extract(inp,out)
