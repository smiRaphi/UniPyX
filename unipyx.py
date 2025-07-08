import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import re,json,ast
from time import sleep
from shutil import rmtree
from lib.dldb import DLDB,xopen,gtmp
from lib.main import extract as _extract
TRIDR = re.compile(r'(\d{1,3}\.\d)% \(.*\) (.+) \(\d+(?:/\d+){1,2}\)')
EIPER1 = re.compile(r'Overlay : +(.+) > Offset : [\da-f]+h')

TDB:dict = json.load(xopen('lib/tdb.json'))
DDB:list[dict] = json.load(xopen('lib/ddb.json'))
TDBF = set(sum(TDB.values(),[]))
db = DLDB()

def cleanp(i:str):
    i = i.replace('/','\\').rstrip('\\')
    while i.endswith('\\.'): i = i[:-1].rstrip('\\')
    while i.startswith('.\\'): i = i[1:].lstrip('\\')
    i = i.replace('\\.\\','\\')
    return os.path.abspath(i)
def checktdb(i:list):
    o = []
    for x in i:
        if not x.lower() in TDBF: continue
        for t in TDB:
            if x.lower() in TDB[t]: o.append(t)
    return o
def analyze(inp:str):
    inp = cleanp(inp)
    _,o,_ = db.run(['trid','-n:5',inp])
    ts = [x[1] for x in TRIDR.findall(o) if float(x[0]) >= 10]

    if os.path.isfile(inp):
        f = open(inp,'rb')
        if f.read(2) == b'MZ':
            f.seek(0x3C)
            f.seek(int.from_bytes(f.read(4),'little'))
            if f.read(4) == b'PE\0\0':
                f.close()
                log = gtmp('.log')
                db.run(['exeinfope',inp + '*','/s','/log:' + log])
                for _ in range(15):
                    if os.path.exists(log) and os.path.getsize(log): break
                    sleep(0.1)
                if os.path.exists(log):
                    lg = open(log,encoding='utf-8').read().strip()
                    os.remove(log)
                    m = EIPER1.search(lg)
                    if m: ts.append(m[1])
                    for x in lg.split('\n')[0].split(' - ')[1:]: ts.append(x.split('(')[0].split('[')[0].strip(' ,!:;'))
            else: f.close()
        else: f.close()

    nts = checktdb(ts)
    nts = list(set(nts))
    for x in DDB:
        if 'rq'  in x and not (x['rq']  in nts or (x['rq'] == None and not nts)): continue
        if 'rqr' in x and not (x['rqr'] in ts or (x['rqr'] == None and not ts )): continue
        if x['d'] == 'py':
            lc = {}
            exec('def check(inp):\n\t' + x['py'].replace('\n','\n\t'),globals={},locals=lc)
            if lc['check'](inp):
                if x.get('s'): nts = [x['rs']]
                else: nts.append(x['rs'])
        elif x['d']['c'] == 'ext': ret = inp.lower().endswith(x['d']['v'])
        elif os.path.isfile(inp):
            if x['d']['c'] == 'contain':
                cv = ast.literal_eval('"' + x['d']['v'] + '"').encode()
                f = open(inp,'rb')
                sp = x['d']['r'][0]
                if sp < 0: sp = f.seek(0,2) + sp
                if sp < 0: sp = 0
                f.seek(sp)
                ret = cv in f.read(x['d']['r'][1])
                f.close()
            elif x['d']['c'] == 'isat':
                cv = ast.literal_eval('"' + x['d']['v'] + '"').encode()
                f = open(inp,'rb')
                sp = x['d']['o']
                if sp < 0: sp = f.seek(0,2) + sp
                if sp < 0: sp = 0
                f.seek(sp)
                ret = f.read(len(cv)) == cv
                f.close()
        if ret:
            if x.get('s'): nts = [x['rs']]
            else: nts.append(x['rs'])
    if not nts: print(ts)

    return nts
def extract(inp:str,out:str,ts:list[str]=None):
    out = cleanp(out)
    assert not os.path.exists(out),'Output directory already exists'
    inp = cleanp(inp)
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
