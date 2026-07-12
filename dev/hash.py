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
        if not hshs: raise ValueError
    else: hshs = [argv[2]]
else: hshs = list(HASHTS)

i = argv[1]
if i[:1] == '*':
    i = i[1:]
    print('Input:',i)
    i = i.encode('latin1')
elif i[:1] == ':':
    i = bytes.fromhex(i[1:])
    print('Input:',i.hex(' ').upper())
elif i[:1] == '>':
    import ast
    i = ast.literal_eval('b"""' + i[1:] + '"""')
    print('Input:',repr(i)[2:-1])
else:
    print('Input:',i)
    i = open(i,'rb').read()

DN = set()
cs = []
for x in hshs:
    crc = crc_hash(i,x)
    if (HASHTS[x],crc) in DN: continue
    DN.add((HASHTS[x],crc))
    cs.append((x,crc))

mx = max([len(x) for x in hshs])
cs.sort(key=lambda x:(HASHTS[x[0]],x[1]))
for x,crc in cs:
    if crc.bit_length() > HASHTS[x] * 8: print(x,crc)
    cb = crc.to_bytes(HASHTS[x],'big')
    print(f'{x.ljust(mx)} | {crc:0{HASHTS[x]*2}X}')
