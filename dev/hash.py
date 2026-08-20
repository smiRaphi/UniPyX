import sys,os
sys.path.append(os.getcwd())

from lib.dldb import DLDB
db = DLDB()
from lib.crypto import crc_hash,HASHTS
from sys import argv

if len(argv) == 2 and argv[1].isdigit() and not os.path.exists(argv[1]):
    s = int(argv[1])
    hshs = [x for x in HASHTS if HASHTS[x] == s]
    print('\n'.join(sorted(hshs)))
    sys.exit()
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
    if x in HASHTS:
        crc = crc_hash(i,x)
        sz = HASHTS[x]
    else:
        crc = crc_hash(i,x,bytes=True)
        sz = len(crc)
        crc = int.from_bytes(crc,'big')
    if (sz,crc) in DN: continue
    DN.add((sz,crc))
    cs.append((x,sz,crc))

mx = max([len(x) for x in hshs])
cs.sort(key=lambda x:(x[1],x[2]))
for x,sz,crc in cs:
    if crc.bit_length() > sz * 8: print(x,crc)
    print(f'{x.ljust(mx)} | {crc:0{sz*2}X}')
