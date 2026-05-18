from lib.crypto import crc_hash

P = r"<path>"
BL = {
    'DDgvP.aif',
    'UefT.cfg',
    'DD34EUd2.lng',
    'bIn',
    'eYe.tm2',
    'CTBB42CC2.exe',
    'WfueeVVfUfeeVu',
    '4B3C4CD.pub',
    'fttdVVeVeedUFF.vso',
    'SaoPS.irx',
    'S334DDUUUUUUTT.png',
    'EVuuvfWWutUUES.png',
    '.d444444e444eeee4effffgff44.-----bc',
    'VeUVVeUVUVUeT.png',
    '44TC454D34443.ids',
}
CRCC = b"________________________________________________0123456789_______ABCDEFGHIJKLMNOPQRSTUVWXYZ______ABCDEFGHIJKLMNOPQRSTUVWXYZ_____________________________________________________________________________________________________________________________________".replace(b'_',b'\0')
fmt = lambda x:x[:0x40].translate(CRCC)

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
nl = open('apetec.hsh','rb').read().replace(b'\r',b'').split(b'\n')
l = set([crc_hash(x.translate(CRCC),'crc32_mpeg2') for x in nl])
nl = set([x.decode('ascii') for x in nl])

def chk(n,prx=True,first=True):
    if n in BL: return

    h = crc_hash(fmt(n.encode('ascii')),'crc32_mpeg2')
    if h in l:
        if prx: print(f'Already in DB | {h:08X}')
    elif h in L:
        print(f'{h:08X} | {n}')
        print('Yay! :D')
        nl.add(n)
        l.add(h)
    else:
        if prx: print('Nay D:')

EXS = {'dll','bnk','exe','pso','vso','tm2','lng','ids','aus','aif','sli','h','cfg','pub','txt','sip','bin','mpg','img','irx','pss','ico','png','tga','psd'}

if 0:
    for n in nl.copy(): chk(n,False)
if 0:
    while 1:
        i = input(': ')
        if not i: break
        if i.startswith('ds "') and i[-1] == '"': i = i[4:-1].replace('\\\\','\\')
        elif i[0] == i[-1] == '"': i = i[1:-1].replace('\\\\','\\')
        chk(i,True)
if 0:
    rg = re.compile(r'(?:(?<=[\0-,\:-@`\{-\xFF])|^)([a-zA-Z0-9_\-\./\\]{4,64})(?:(?=[\0-,\:-@`\{-\xFF])|$)'.encode())
    fs = rldir(P)
    fs = [P + '/Data1.aif',P + '/SIEGE.EXE',P + '/SLES_534.35',P + '/DATA2.bin']
    for f in fs:
        if not os.path.exists(f): continue
        for rr in rg.findall(open(f,'rb').read()):
            for r in rr.replace(b'\\',b'/').split(b'/'):
                try: r = r.decode('ascii');assert r.isprintable()
                except: continue
                chk(r,False)
                for x in EXS:
                    chk(r + '.' + x,False)
                if '.' in r:
                    r = os.path.splitext(r)[0]
                    for x in EXS:
                        chk(r + '.' + x,False)
if 1:
    for n in nl.copy():
        n = os.path.splitext(n)[0]
        chk(n,False)
        for x in EXS: chk(n + '.' + x,False)
if 1:
    for f in rldir(P):
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
            length = len(d)
            gen = (f"{i:0{length}d}" for i in range(10**length))
            digit_generators.append(gen)

        for digit_combo in itertools.product(*digit_generators):
            result = []
            for ix in range(len(digit_combo)):
                result.append(text_parts[ix])
                result.append(digit_combo[ix])
            result.append(text_parts[-1])

            chk("".join(result),False)
if 0:
    for n in nl.copy():
        if '_' in n:
            for r in os.path.splitext(n)[0].split('_'):
                for x in EXS: chk(r + '.' + x,False)
if 1:
    for x in ('PC_','PS2_','M1_','M2_','M3_','M4_','M5_','FLAG_','TEXT_','Language_','STR_'):
        for n in nl.copy():
            n = os.path.splitext(n)[0]
            b = n.split('_',1)[-1]
            for ex in EXS:
                chk(x + n + '.' + ex,False)
                chk(x + b + '.' + ex,False)
    for x in ('PS2','PC','_ENG','_FRE','_GER','_SPA','_POR','_ITA','_NOR','_DAN','_DUT','_SWE','_SAS','_FRENCH','_GERMAN','_ENGLISH'):
        for n in nl.copy():
            n = os.path.splitext(n)[0]
            b = n.rsplit('_',1)[0]
            for ex in EXS:
                chk(n + x + '.' + ex,False)
                chk(b + x + '.' + ex,False)
            if n.endswith('PC'):
                for ex in EXS:
                    chk(n[:-2] + x + '.' + ex,False)
                    chk(b[:-2] + x + '.' + ex,False)
            if n.endswith('PS2'):
                for ex in EXS:
                    chk(n[:-3] + x + '.' + ex,False)
                    chk(b[:-3] + x + '.' + ex,False)
if 0:
    for x in EXS:
        for n in nl.copy(): chk(os.path.splitext(n)[0] + '.' + x,False)

print(f'{len(l)} / {(len(L))} | {len(l)/(len(L))*100:.2f}%')
nl = '\n'.join(sorted(nl)).encode('ascii')
open('apetec.hsh','wb').write(nl)
