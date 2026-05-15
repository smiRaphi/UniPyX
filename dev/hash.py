import sys,os
sys.path.append(os.getcwd())

from lib.dldb import DLDB
db = DLDB()
from lib.crypto import crc_hash,HASHTS
from sys import argv

if len(argv) == 3:
    if argv[2].isdigit():
        s = int(argv[2])
        hshs = [x for x in HASHTS if HASHTS[x] == s]
    else: hshs = [argv[2]]
else: hshs = list(HASHTS)

i = argv[1]
if i[:1] == '*':
    i = i[1:]
    print('Input:',i)
    i = i.encode('ansi')
elif i[:1] == ':':
    i = bytes.fromhex(i[1:])
    print('Input:',i.hex(' ').upper())
else:
    print('Input:',i)
    i = open(i,'rb').read()

DN = set()
cs = []
for x in hshs:
    crc = crc_hash(i,x)
    if crc in DN: continue
    DN.add(crc)
    cs.append((x,crc))

mx = max([len(x) for x in hshs])
cs.sort(key=lambda x:x[1])
for x,crc in cs:
    print(f'{x.ljust(mx)} | {hex(crc)[2:].upper().zfill(HASHTS[x]*2)}')
