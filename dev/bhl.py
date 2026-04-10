ENC = 'utf-8'
FMT = lambda x:x

import os,sys
argv = sys.argv
sys.path.append(os.getcwd())
from lib.file import HashLib

if argv[1] == 'd':
    h = HashLib(argv[2],fmt=FMT,encoding=ENC).loadb()
    for x in h.db:
        print(hex(x)[2:].upper().zfill(h.hs*2) + ' | ' + h.db[x])
    sys.exit()
elif argv[1] == 'sd':
    h = HashLib(argv[2],fmt=FMT,encoding=ENC).loadb()
    for x in h.db.values(): print(x)
    sys.exit()
elif argv[1] == 'c':
    h = HashLib(argv[2],fmt=FMT,encoding=ENC).loadb()
    print(len(h.db))
    sys.exit()

h = HashLib.new(os.path.splitext(os.path.basename(argv[2]))[0] + '.bhl',argv[1],fmt=FMT,encoding=ENC)
for x in argv[2:]:
    if x.endswith('.bhl'): h.add(HashLib(x,fmt=FMT,encoding=ENC).loadb().db.values())
    else: h.add(open(x,encoding=ENC).read().split('\n'))
h.save()
