P = r"<Archer Maclean's Mercury>\PSP_GAME\USRDIR"

import sys,os
if sys.argv[1:] == ['x']:
    import subprocess
    for x in os.listdir(P):
        if not x.endswith('.paq'): continue
        subprocess.call([sys.executable,'unipyx.py',P + '\\' + x,P + '\\out'])
    sys.exit()

crcs = []
for p in os.listdir(P):
    if not p.endswith('.paq'): continue
    p = os.path.join(P,p)
    with open(p,'rb') as f:
        f.seek(4)
        c = int.from_bytes(f.read(4),'little')
        f.seek(0x10)
        for _ in range(c):
            crcs.append(int.from_bytes(f.read(4),'little'))
            f.seek(12,1)
crcs = set(crcs)

CRCC = b"________________________________________________0123456789_______ABCDEFGHIJKLMNOPQRSTUVWXYZ______ABCDEFGHIJKLMNOPQRSTUVWXYZ_____________________________________________________________________________________________________________________________________"
from zlib import crc32
crc = lambda x: crc32((x.encode('ascii') if isinstance(x,str) else x).translate(CRCC))
l = {crc(x.strip()):x.strip() for x in open('bin/archer_mac_mercury.hsh','rb').readlines() if x.strip() and crc(x.strip()) in crcs}

def chk(i,first=True):
    if isinstance(i,str): i = i.encode('ascii')
    if first:
        if i.endswith((b'.zen',b'.col',b'.cam')):
            for x in {b'zen',b'col',b'cam'}: chk(i[:-3] + x,False)
            chk(i.rsplit(b'/',1)[0] + b'/Surfaces.txt',False)
            return
        elif i.startswith(b'data/Levels/') and i.endswith((b'.txt',b'.TXT')) and len(i.split(b'/')) == 4:
            i = i.rsplit(b'/',1)[0]
            for x in {b'Emitters.txt',b'Level.TXT',b'MaterialObjects.txt',b'NewLogic.txt',b'RL_Level.txt',b'Surfaces.txt',b'radiation.txt',b'Objects.TXT',b'Lights.TXT'}: chk(i + b'/' + x,False)
            chk(i + b'/' + i.rsplit(b'/',1)[1] + b'.zen',True)
            return
    else: print(i.decode('ascii'))
    c = crc(i)
    if c in l: print('Already in DB')
    elif c in crcs:
        print('Yay! :D')
        l[c] = i
    else: print('Nay D:')

# import re
# for x in re.findall(r'Level \d+="(.+)"',open(r"<Archer Maclean's Mercury>\PSP_GAME\USRDIR\General\data\Scripts\MercuryLevel.ini").read()):
#     chk(f'data/Levels/{x}/Level.TXT',True)
# for x in l.copy():
#     if b'Active_Objects' in l[x]: chk(l[x])
P2 = r"<Archer Maclean's Mercury>\PSP_GAME\USRDIR\out"
for x in os.listdir(P2):
    if not x.endswith('.DEAD'): continue
    f = open(os.path.join(P2,x),'rb')
    f.seek(0x10)
    n = f.read(0x1000).split(b'\0')[0].decode('ascii').rsplit('/',1)[1]
    assert n.endswith(('.mb','.ma')),x
    for x2 in range(1,10): chk(f'data/Active_Objects/World{x2}/{n[:-3]}/{n[:-2]}zen',True)

# while 1:
#     i = input(': ')
#     if not i: break
#     chk(i.replace('\\','/'))

print(f'{len(l)} / {len(crcs)} | {len(l)/len(crcs)*100:.2f}%')
d = b'\n'.join(sorted(l.values()))
open('bin/archer_mac_mercury.hsh','wb').write(d)
