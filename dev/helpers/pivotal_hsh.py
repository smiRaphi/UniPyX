from lib.crypto import crc_hash

import os
D = r"C:\Users\grego\Downloads\conflictdesertstorm\conflictdesertstorm_pc_dat\mission3"
if not os.path.exists(D + '/$unk'): exit()
L = [int(x.split('.')[0],16) for x in os.listdir(D + '/$unk')]

def add(n):
    n = n.upper()
    if isinstance(n,str): n = n.encode('ascii')
    h = crc_hash(n,'pivotal')
    if h in L:
        print(n.decode())
        L.remove(h)

bd = os.path.basename(D).upper()
if bd.startswith('MISSION'):
    for x in {'FAS','OCT','QTD','RMD','RFX','ENV'}: add(bd + '.' + x)
    add('GW' + bd + '.IMG')
    add('M0' + bd[7] + 'STRS.LOC')
    if len(bd) > 8: add('M0' + bd[7:9] + 'STRS.LOC')

import re,itertools

EX = {'PRB','DDS','PNG','TGA','BMP'}
if 1:
    ex = [x.encode('ascii') for x in EX]
    R = re.compile(b'\0([A-Z0-9_\\.]{4,})\0')
    chk = set()
    for f in os.listdir(D) + os.listdir(D + '/$unk'):
        if not os.path.isfile(os.path.join(D,f)): continue
        d = open(os.path.join(D,f),'rb').read()
        ms = R.findall(d)
        for x in ex:
            for m in ms: chk.add(m.upper().split(b'.')[0] + b'.' + x)

    for x in chk: add(x)
if 1:
    for f in os.listdir(D):
        if not os.path.isfile(os.path.join(D,f)): continue
        for x in EX: add(f.upper().split('.')[0] + '.' + x)
if 0:
    fns = [x.upper().split('.')[0].split('_') for x in os.listdir(D) if os.path.isfile(os.path.join(D,x))]
    nms = []
    for fn in fns:
        for ix,fnp in enumerate(fn):
            if ix >= len(nms): nms.append([])
            if fnp not in nms[ix]: nms[ix].append(fnp)
    for x in nms: x.sort()

    for ln in range(len(nms)):
        ln += 1
        for n in itertools.product(*nms[:ln]):
            for x in EX: 
                add('_'.join(n) + '.' + x)
if 1:
    rp = re.compile(r'\d+')
    fns = [x.upper() for x in os.listdir(D) if os.path.isfile(os.path.join(D,x)) and rp.search(x)]

    DN = set()
    for f in fns:
        text_parts = rp.split(f)
        digit_blocks = rp.findall(f)
        dna = (*(len(x) for x in digit_blocks),*text_parts)
        if dna in DN: continue
        DN.add(dna)

        digit_generators = []
        for d in digit_blocks:
            length = len(d) - 1
            gen = (f"{i:0{length}d}" for i in range(10**length))
            digit_generators.append(gen)

        for digit_combo in itertools.product(*digit_generators):
            result = []
            for ix in range(len(digit_combo)):
                result.append(text_parts[ix])
                result.append(digit_combo[ix])
            result.append(text_parts[-1])

            add("".join(result))
