import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import re,json
from time import sleep
from shutil import rmtree
from lib.dldb import DLDB,xopen,gtmp
from lib.main import extract as _extract
TRIDR = re.compile(r'(\d{1,3}\.\d)% \(.*\) (.+) \(\d+(?:/\d+){1,2}\)')
EIPER1 = re.compile(r'Overlay : +(.+) > Offset : [\da-f]+h')
EIPER2 = re.compile(r'^.+? - .+? - ([^\(!\n:,\]\[]]+)')

TDB:dict = json.load(xopen('lib/tdb.json'))
DDB:list[dict] = json.load(xopen('lib/ddb.json'))
TDBF = set(sum(TDB.values(),[]))
db = DLDB()

def checktdb(i:list):
    o = []
    for x in i:
        if not x.lower() in TDBF: continue
        for t in TDB:
            if x.lower() in TDB[t]: o.append(t)
    return o
def analyze(inp:str):
    _,o,_ = db.run(['trid','-n:5',inp])
    ts = [x[1] for x in TRIDR.findall(o) if float(x[0]) >= 10]

    if os.path.isfile(inp) and open(inp,'rb').read(2) == b'MZ':
        log = gtmp('.log')
        db.run(['exeinfope',inp + '*','/s','/log:' + log])
        for _ in range(50):
            if os.path.exists(log) and os.path.getsize(log): break
            sleep(0.1)
        else: raise Exception('exeinfope timed out')
        lg = open(log,encoding='utf-8').read()
        os.remove(log)
        m = EIPER1.search(lg)
        if m: ts.append(m[1])
        m = EIPER2.search(lg)
        if m: ts.append(m[1].strip())

    nts = checktdb(ts)
    if not nts: print(ts)
    else: nts = list(set(nts))
    for x in DDB:
        if 'rq' in x and x['rq'] not in nts: continue
        if x['d']['c'] == 'contain' and os.path.isfile(inp):
            cv = x['d']['v'].encode()
            f = open(inp,'rb')
            sp = x['d']['r'][0]
            if sp < 0: sp = f.seek(0,2) + sp
            if sp < 0: sp = 0
            f.seek(sp)
            if cv in f.read(x['d']['r'][1]):
                if x.get('s'): nts = [x['rs']]
                else: nts.append(x['rs'])
            f.close()
                    
    return nts
def extract(inp:str,out:str,ts:list[str]=None):
    out = os.path.abspath(out).replace('/','\\')
    assert not os.path.exists(out),'Output directory already exists'
    inp = os.path.abspath(inp).replace('/','\\')
    if ts == None: ts = analyze(inp)
    assert ts,'Unknown file type'

    for x in ts:
        print('Trying format',x)
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
