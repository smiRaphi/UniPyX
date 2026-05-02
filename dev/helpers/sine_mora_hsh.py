import os
from lib.file import File
from lib.crypto import sdbm

P = r"<dir>"
HL = []
for x in os.listdir(P):
    x = os.path.join(P,x)
    if not x.endswith('.bin') or not os.path.isfile(x): continue
    f = File(x,endian='<')
    while f:
        for _ in range(3): HL.append(f.readu32())
        f.skip(4)
        f.skip(f.readu32())
    f.close()
HL = set(HL)
PL = set([x for x in open('sine_mora.hsh').read().split('\n') if x])

def chk(i,prf=True):
    if type(i) in {tuple,set,list}:
        for x in i: chk(x)
        return
    if type(i) == bytes: i = i.decode('ascii')
    h = sdbm(i.encode('ascii'))
    if prf: print(f'{h:08X} | {i}')
    if i in PL:
        if prf: print('Already in DB')
    elif h in HL:
        if not prf: print(f'{h:08X} | {i}')
        print('Yay! :D')
        PL.add(i)
    else:
        if prf: print('Nay D:')

if 0:
    L1 = ('_norm.dds','_mask.dds','_diff.dds')
    exts = [x for x in PL if len(x) in {3,4}]
    while 1:
        i = input(': ')
        if not i: break
        if i.startswith('ds "') and i[-1] == '"': i = i[4:-1]
        if i.endswith(L1):
            for x in L1: chk(i.rsplit('_',1)[0] + x)
        elif not '.' in i and not '/' in i:
            for x in exts: chk(i + '.' + x,prf=False)
        else: chk(i)
elif 0:
    PM = r"<dir>\render"
    import re
    R1 = re.compile(r'(?m)^\t"([^"])" *: *\{')
    RS = [re.compile(x) for x in {r'"RENDERSTATEBLOCK" *: *"([^"]+)"',r'"(?:VERTEX|PIXEL)SHADER" *: *\["([^"]+)" *,',r'"SAMPLERSTATE" *: *\["[^"]*" *, *"([^"]+)"\]'}]

    for x in os.listdir(PM):
        if x.endswith('.mtl'):
            d = open(os.path.join(PM,x),'r').read()
            assert d.startswith('{\n\t"')

            for x in R1.findall(d): chk(x.lower() + '.mtl')
            for r in RS: chk(r.findall(d))
elif 0:
    exts = [x for x in PL if len(x) in {3,4}]
    for x in PL.copy():
        if len(x) > 4:
            for ex in exts: chk((x.split('/')[-1] if '/' in x else os.path.splitext(x)[0]) + '.' + ex,prf=False)
elif 0:
    def chkm(x:str):
        if x[-1].isdigit(): x = ''.join([x for x in x[:-1] if not x.isdigit()])
        chk(x.strip('_') + '.sph',prf=False)
        for ix in range(0,100):
            chk(f'{x}{ix}.dds',prf=False)
            chk(f'{x}{ix:02d}.sph',prf=False)

    L1 = ('_norm','_diff','_mask')
    PS = r"<dir>"
    for x in os.listdir(PS):
        if not x.endswith('.sph'): continue
        f = File(os.path.join(PS,x),endian='<')

        f.skip(4)
        mc = f.reads32()
        assert mc > 1
        f.seek(0)

        try:
            for _ in range(mc):
                f.skip(8)
                u1 = f.readu32()
                assert u1 <= 1
                if u1:
                    f.skip(4*6)
                    sc = f.readu32()
                    for _ in range(sc):
                        f.skip(12)
                        f.skip(f.readu32())
                        f.skip(f.readu32()*2 + 4)
                        chk(f.read(f.readu32()),prf=False) # mtl
                        vc = f.readu32()
                        for _ in range(vc):
                            kn = f.read(f.readu32()).decode('ascii')
                            vn = f.read(f.readu32()).decode('ascii')
                            if kn in {'SEP_TEXTURE_DIFFUSE','SEP_TEXTURE_OPACITY','SEP_TEXTURE_NORMAL'}:
                                bn = vn.rsplit('/',1)[-1]
                                if bn.endswith(L1):
                                    for sx in L1: chk(bn.rsplit('_',1)[0] + sx + '.dds',prf=False)
                                else: chk(bn + '.dds',prf=False)
                                if len(vn.split('/')) == 5: chkm(vn.split('/')[3])
                            else: raise NotImplementedError(f'{kn}: {vn} ({x})')
                        f.skip(f.readu32() * 0x44)
                    chkm(f.read(f.readu32()).decode('ascii'))
                else: f.skip(f.readu32())
                f.skip(4*16)
        except:
            print(x,f.pos)
            raise

        f.close()
elif 0:
    for i1 in ('tira','siriad','prologue','moneta','factory','enkie','cardinal','bokumono'):
        for i2 in ('small','small_locked','big','big_locked'):
            x = f'stage_{i1}_{i2}'
            chk(x + '.dds',prf=False)
            chk('textures/gui/frontend/' + x,prf=False)
    for i1 in ('survive','manipulate','maneuver','evade','aim'):
        for i2 in range(1,4):
            for i3 in ('','_locked','_small','_small_locked'):
                for i4 in ('','_pc','_ps3','_xbox'):
                    x = f'ch_{i1}_{i2:02d}{i3}{i4}'
                    chk(x + '.dds',prf=False)
                    chk('textures/gui/frontend/' + x,prf=False)
    for i1 in ('zepelin','tsuchigumo','sub','steropes','papacarlo','palladion','ophanim','melkor','matouschka','libelle','kolobok','factory','domus'):
        for i2 in ('small','small_locked','big','big_locked'):
            x = f'boss_{i1}_{i2}'
            chk(x + '.dds',prf=False)
            chk('textures/gui/frontend/' + x,prf=False)
elif 0:
    fs = set([x.rsplit('.',1)[0] for x in PL if not '/' in x])
    ds = set([x.rsplit('/',1)[0] + '/' for x in PL if '/' in x])
    for d in ds:
        for f in fs: chk(d + f,prf=False)

for x in PL.copy():
    if x.endswith('.dds'):
        x = x[:-4]
        p = 'textures/'
        if x.startswith('gui_'): chk(p + 'gui/' + x,prf=False)
        chk(p + x,prf=False)
        for i1 in os.listdir(r"<dir>"): chk(f'objects/levels/{i1[:-4]}/{x[:-4]}',prf=False)
    elif x.endswith(('.sph')):
        chk('objects/' + x[:-4],prf=False)
        for i1 in os.listdir(r"<dir>"): chk(f'objects/levels/{i1[:-4]}/{x[:-4]}',prf=False)
    elif x.endswith(('.bson')): chk(f'scenes/{x[:-5]}',prf=False)
    elif x.endswith(('.sub')): chk(f'subtitles/{x[:-4]}',prf=False)
    elif x.startswith('textures/'): chk(x.rsplit('/',1)[1] + '.dds',prf=False)
    elif x.startswith('objects/'): chk(x.rsplit('/',1)[1] + '.sph',prf=False)
    elif x.startswith('scenes/'): chk(x.rsplit('/',1)[1] + '.bson',prf=False)
    elif x.startswith('subtitles/'): chk(x.rsplit('/',1)[1] + '.sub',prf=False)

print(f'{len(PL)} / {len(HL)} | {len(PL)/len(HL)*100:.2f}%')
open('sine_mora.hsh','w').write('\n'.join(sorted(PL)))
