ENC = 'ascii'
FMT = lambda x:x.lower() # x: bytes
iFMT = lambda x:x #'/'+x.replace('\\','/').lstrip('/') # x: str

import os,sys
argv = sys.argv
sys.path.append(os.getcwd())
from lib.crypto import HashLib

if argv[1] == 'd':
    h = HashLib(argv[2],fmt=FMT,encoding=ENC).loadb()
    for x in sorted(h.db):
        print(f'{x:0{h.hs*2}X} | {h.db[x]}')
    sys.exit()
elif argv[1] == 'sd':
    h = HashLib(argv[2],fmt=FMT,encoding=ENC).loadb()
    for x in h.db.values(): print(x)
    sys.exit()
elif argv[1] == 'c':
    h = HashLib(argv[2],fmt=FMT,encoding=ENC).loadb()
    print(len(h.db))
    sys.exit()

algo = argv[1]
if algo in {'xxh32','xxh64','xxh128','xxh3_64','xxh3_128',
            'murmur3','mmh3','murmur3_32','mmh3_32','murmur3_128','mmh3_128'}:
    from lib.dldb import DLDB
    d = DLDB()

h = HashLib.new(os.path.splitext(os.path.basename(argv[2]))[0] + '.bhl',algo,fmt=FMT,encoding=ENC)
for x in argv[2:]:
    if x.endswith('.bhl'): l = HashLib(x,fmt=FMT,encoding=ENC).loadb().db.values()
    else:
        l = open(x,encoding=ENC).read().split('\n')
        if l and len(l[0]) > (h.hs*2+1) and l[0][h.hs*2] == '|' and all(x in '0123456789abcdefABDEF' for x in l[0][:h.hs*2]):
            l = [e[h.hs*2+1:] for e in l if len(e) > (h.hs*2+1)]
    h.add([iFMT(e) for e in l])
h.save()
