from lib.crypto import crc_hash

P = r"C:\Users\grego\Downloads\1,000,000 Pyramid, Th\1,000,000 Pyramid, The (USA).nkit"

BL = {
    "vuccqp.mem",
    "FNNNNNNRNKKKKKKNKHHHHHHJHEEEEEEFE.txt",
    "a344ed.scn",
    "chf_nohatshoulderstraight_80s01_ora_t1.txs.snd",
}

import os,re,itertools
def rldir(i:str,files=True) -> list[str]:
    i = str(i)
    o = []
    for x in os.listdir(i):
        x = i + '\\' + x
        if os.path.isfile(x): o.append(x)
        else:
            if not files: o.append(x)
            o += rldir(x,files=files)
    return o

L = set([int(x,16) for x in open('check.list','r').read().split('\n')])
nl = open('ludia.hsh','rb').read().replace(b'\r',b'').split(b'\n')
l = set([crc_hash(x,'crc32_ludia') for x in nl])
nl = set([x.decode('ascii') for x in nl])

ABC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def chk(n,prx=True,first=True):
    if n in BL: return
    if first:
        if any(c in ABC for c in n):
            chk(n.lower(),False,False)
        if '_' in n:
            chk('_'.join([x.capitalize() for x in n.split('_')]),False,False)

    h = crc_hash(n.encode('ascii'),'crc32_ludia')
    if h in l:
        if prx: print('Already in DB')
    elif h in L:
        n = n.decode()
        print(f'{h:08X} | {n}')
        print('Yay! :D')
        nl.add(n)
        l.add(h)
    else:
        if prx: print('Nay D:')

EXS = {'tpl','xml','txs','vtx','spt','mat','mdl','dsp','cam','txt','csv','hdr','anm','fon','msh','scn','bin','mem','loc','snd','dsp','flow'}

if 0:
    for n in nl.copy(): chk(n,False)
if 0:
    while 1:
        i = input(': ')
        if not i: break
        if i.startswith('ds "') and i[-1] == '"': i = i[4:-1].replace('\\\\','\\')
        elif i[0] == i[-1] == '"': i = i[1:-1].replace('\\\\','\\')
        chk(i,True)
        if i.endswith('.png'): chk(i[:-3] + 'tpl',True)
if 0:
    rg = re.compile(r'[\0-,\:-@`\{-\xFF]([a-zA-Z0-9_\-\./\\]{5,256})[\0-,\:-@`\{-\xFF]'.encode())
    for f in rldir(P):
        for r in rg.findall(open(f,'rb').read()):
            try: r = r.decode('ascii');assert r.isprintable()
            except: continue
            if '/' in r: r = r.split('/')[-1]
            if '\\' in r: r = r.split('\\')[-1]
            chk(r,False)
            for x in EXS:
                chk(r + '.' + x,False)
            if '.' in r:
                r = os.path.splitext(r)[0]
                for x in EXS:
                    chk(r + '.' + x,False)
if 0:
    for n in nl:
        n = os.path.splitext(n)[0]
        chk(n.upper(),False)
        for x in EXS: chk(n.upper() + '.' + x,False)
if 0:
    for f in rldir(P):
        f = os.path.basename(f)
        chk(f,False)
        f = os.path.splitext(f)[0]
        for x in EXS:
            chk(f + '.' + x,False)
if 1:
    rp = re.compile(r'\d{1,4}')
    fns = [x for x in nl if rp.search(x)]

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

            chk("".join(result),False)
if 1:
    for n in nl.copy():
        if '_' in n: chk(n.split('_',1)[1],False)
if 1:
    for x in ('Thumbnail_','sfx_','prsc_','prs_','gstrc_'):
        for n in nl.copy():
            n = os.path.splitext(n)[0]
            for ex in EXS:
                chk(x + n + '.' + ex,False)
    for x in ('_material','_prsc','_prs'):
        for n in nl.copy():
            n = os.path.splitext(n)[0]
            for ex in EXS:
                chk(x + n + '.' + ex,False)
if 1:
    for x in EXS:
        for n in nl.copy(): chk(os.path.splitext(n)[0] + '.' + x,False)

print(f'{len(l)} / {(len(L))} | {len(l)/(len(L))*100:.2f}%')
nl = '\n'.join(sorted(nl)).encode('ascii')
open('ludia.hsh','wb').write(nl)
