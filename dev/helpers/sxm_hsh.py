CHARAS = {'','B06','MIU','USI','KYO','KTR','Z03','NEG','YAI','NAT','B08','HAY','ITU','MAD','KIY','LUC','B05','Z07','B02','B07','UEK','SHI','USB','Z01','TIO','DOR','TAK','INU','YJO','MG','REK','DVI','BAN','CRO','Z04','JAB','HAK','B03','BOS','TOK','KAO','\x00\x00\x00','TIG','RTA','B04','IPO','OYJ','DVL','B09','KOT','DMY','GAS','KEN','TOR','NOB','Z05','RYO','Z02','AOI','MEC','SJO','YOS','CRY','Z06','KAM','B01','HAP'}
FAC = r"<fab/fac/fah path>"

PL = set([x for x in open('sxm.hsh').read().split('\n') if x])
import os
FL = [os.path.join(FAC,x) for x in os.listdir(FAC) if x.endswith(('.fah','.fab','.fac')) and x != 'sxm.fac']

import sys
if sys.argv[1:] == ['x']:
    import subprocess
    from lib.file import HashLib
    bhl = 'bin/hashes/sxm.bhl'
    if os.path.exists(bhl): os.remove(bhl)
    hl = HashLib.new(bhl,'sxm',fmt=lambda i:i.lower().replace(b'\\',b'/'),encoding='ascii')
    hl.add(PL)
    hl.save()

    lst = FL
    while lst:
        cl,lst = lst[:32],lst[32:]
        while cl:
            prcs = []
            for x in cl:
                od = os.path.dirname(FAC) + '/' + os.path.basename(x)[:-4]
                prcs.append((subprocess.Popen([sys.executable,'unipyx.py',x,od],stdout=-1,stderr=-1),od,x))
            for p in prcs:
                p[0].wait()
                if os.path.exists(p[1]): cl.remove(p[2])
    sys.exit()

from lib.file import File,sxm_hash

HL = set()
for fe in FL:
    f = File(fe,endian='<')
    assert f.read(4) == b'FARC'
    f.skip(4)
    c = f.readu32()
    f.skip(4)
    for _ in range(c):
        f.skip(8)
        HL.add(f.readu64())
    f.close()

def chk(i,prf=True):
    if type(i) in {tuple,set,list}:
        for x in i: chk(x)
        return
    if type(i) == bytes: i = i.decode('ascii')
    i = i.replace('\\','/')
    h = sxm_hash(i.lower().encode('ascii'))
    if prf: print(f'{h:08X} | {i}')
    if i in PL:
        if prf: print('Already in DB')
        return True
    elif h in HL:
        if not prf: print(f'{h:08X} | {i}')
        print('Yay! :D')
        PL.add(i)
        return True
    else:
        if prf: print('Nay D:')
        return False

if 1:
    while 1:
        i = input(': ')
        if not i: break
        if i.startswith('ds "') and i[-1] == '"': i = i[4:-1].replace('\\\\','\\')
        elif i[0] == i[-1] == '"': i = i[1:-1].replace('\\\\','\\')
        chk(i)
elif 0:
    hl = set()
    for x in PL:
        h = sxm_hash(x.lower().encode('ascii'))
        if h in hl:
            print(':c')
            input(x)
        elif not h in HL:
            print('?')
            input(x)
        else: hl.add(h)
elif 0:
    for x1 in CHARAS:
        for z in {'model','motion'}:
            x = f'data\\chara\\{z}\\{x1}\\{x1}_'
            for y in {'DR','DM','AT','NT'}:
                for ix in range(10000):
                    for ex in {'','_A','_B','_C','_D','_E','_F','_G','_H','_I','_J','_K','_L'}: chk(f'{x}{y}{ix:04d}{ex}.gmo',False)
            for y in {'body','face','handL','handR'}:
                for ix in range(100): chk(f'{x}{y}_{ix:02d}.gmo',False)
elif 0:
    for x1 in CHARAS:
        chk(f'data\\chara\\{x1}.cpk',False)
        for ix in range(100): chk(f'data\\chara\\{x1}{ix:01d}.cpk',False)
elif 0:
    for x in CHARAS:
        chk(f'data/particle/{x}/particle{x}.emt',False)
        chk(f'data/particle/{x}/particle{x}.tpk',False)
        chk(f'data/particle/{x}/particle{x}.fab',False)
        chk(f'data/particle/SUPPORT/{x}/particle{x}.emt',False)
        chk(f'data/particle/SUPPORT/{x}/particle{x}.tpk',False)
        chk(f'data/particle/SUPPORT/{x}/particle{x}.fab',False)
        chk(f'data/particle/{x}/object/ParObj{x}.epk',False)
        chk(f'data/particle/{x}/SPK_{x}.spk',False)
        chk(f'data/particle/{x}/p{x}.fab',False)
        chk(f'data/particle/{x}/pack{x}.fab',False)
        chk(f'data/particle/{x}/{x}.fab',False)
        chk(f'data/particle/{x}.fab',False)
        chk(f'data/particle/{x}/particle.fab',False)
        chk(f'data/particle/SUPPORT/{x}/object/ParObj{x}.epk',False)
        chk(f'data/particle/SUPPORT/{x}/SPK_{x}.spk',False)
        chk(f'data/particle/SUPPORT/{x}/p{x}.fab',False)
        chk(f'data/particle/SUPPORT/{x}/pack{x}.fab',False)
        chk(f'data/particle/SUPPORT/{x}/{x}.fab',False)
        chk(f'data/particle/SUPPORT/{x}.fab',False)
        for ix in range(100):
            chk(f'data/particle/{x}{ix:01d}/particle{x}{ix:01d}.emt',False)
            chk(f'data/particle/{x}{ix:01d}/particle{x}{ix:01d}.tpk',False)
            chk(f'data/particle/{x}{ix:01d}/particle{x}{ix:01d}.fab',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/particle{x}{ix:01d}.emt',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/particle{x}{ix:01d}.tpk',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/particle{x}{ix:01d}.fab',False)
            chk(f'data/particle/{x}{ix:01d}/object/ParObj{x}{ix:01d}.epk',False)
            chk(f'data/particle/{x}{ix:01d}/SPK_{x}{ix:01d}.spk',False)
            chk(f'data/particle/{x}{ix:01d}/p{x}{ix:01d}.fab',False)
            chk(f'data/particle/{x}{ix:01d}/pack{x}{ix:01d}.fab',False)
            chk(f'data/particle/{x}{ix:01d}/{x}{ix:01d}.fab',False)
            chk(f'data/particle/{x}{ix:01d}.fab',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/object/ParObj{x}{ix:01d}.epk',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/SPK_{x}{ix:01d}.spk',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/p{x}{ix:01d}.fab',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/pack{x}{ix:01d}.fab',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}/{x}{ix:01d}.fab',False)
            chk(f'data/particle/SUPPORT/{x}{ix:01d}.fab',False)
elif 0:
    bp = 'data/particle/{}/p{}.fac'
    TST = [''] + [str(x) for x in range(100)]
    for c in CHARAS:
        for t in TST: chk(bp.format(c + t,c + t),False)
elif 0:
    for ix in range(100): chk(f'data/bg/B{ix:02d}.bpk',False)
elif 0:
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
        for ix1 in range(10000):
            chk(f'data/chara/{a}{ix1:02d}.cpk',False)
            chk(f'data/chara/{a}{ix1:04d}.cpk',False)
elif 0:
    for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
        for ix1 in range(10000):
            chk(f'data/bg/S{ix1:02d}{a}.bpk',False)
            chk(f'data/bg/S{ix1:04d}{a}.bpk',False)
elif 0:
    for x0 in {'EP','RE'}:
        for x1 in {'_ZH1','_ZH2','_ZH3','_ZGH','_ZBD','_ZH32','_ZBD2','_ZO1','_ZO2','_ZO3','','_MCN','_MYS','_ADV','_B01','_B02','_B03'}:
            for x2 in {'_L2','_L1','_L0',''}:
                chk(f'data/quest/{x0}{x1}{x2}.bin',False)
                chk(f'data/quest/{x0}{x1}{x2}.csv',False)
elif 0:
    for x in {'mess_unlock','mess_staff','mess_quest_op','mess_quest_ed','mess_ACTION_LABEL','mess_lobbychar'}:
        chk(f'data/mess/{x}.bin',False)
elif 0:
    chk('data/particle/object/ParObjQ.epk',False)
    chk('data/particle/SPK0001.spk',False)
    for ix in range(100):
        chk(f'data/particle/S{ix:02d}/object/ParObjS{ix:02d}.epk',False)
        chk(f'data/particle/S{ix:02d}/SPK_S{ix:02d}.spk',False)
        chk(f'data/particle/SUPPORT/S{ix:02d}/object/ParObjS{ix:02d}.epk',False)
        chk(f'data/particle/SUPPORT/S{ix:02d}/SPK_S{ix:02d}.spk',False)
        chk(f'data/particle/SUPPORT/S{ix:02d}/pS{ix:02d}.fab',False)
elif 0:
    chk('data/particle/particle.emt',False)
    chk('data/particle/particle.tpk',False)
    for ix in range(100):
        chk(f'data/particle/S{ix:02d}/particleS{ix:02d}.emt',False)
        #chk(f'data/particle/S{ix:02d}/particleS{ix:02d}.tpk',False)
        chk(f'data/particle/SUPPORT/S{ix:02d}/particleS{ix:02d}.emt',False)
        #chk(f'data/particle/SUPPORT/S{ix:02d}/particleS{ix:02d}.tpk',False)
elif 0:
    for x in {'se','bgm'}:
        for ex in {'phd','pbd','pef','at3'}:
            for ix in range(1000):
                chk(f'data/sound/{x}{ix:03d}.{ex}',False)
elif 0:
    for x in CHARAS:
        chk(f'data/Battle/script/pl_{x.lower()}_cmds.so',False)
        chk(f'data/Battle/script/pl_{x.lower()}.so',False)
elif 0:
    for ix in range(100):
        chk(f'data/Battle/script/st_{ix}.so',False)
        chk(f'data/Battle/script/st_b{ix:02d}.so',False)
        if chk(f'data/Battle/script/st_s{ix:02d}.so',False):
            chk(f'data/Battle/script/st_s{ix:02d}v.so',False)
            for ix2 in range(100): chk(f'data/Battle/script/st_s{ix:02d}{ix2:02d}.so',False)
elif 0:
    EXTS = {'csv','cpk','dat','res','bin','emt','epk','tpk','fab','bpk','cpk','gimx','spk','fac'}
    for p in PL.copy():
        bp = os.path.splitext(p)[0]
        for x in EXTS:
            chk(bp + '.' + x,False)
            for abc in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789': chk(bp + abc + '.' + x,False)
elif 0:
    RD = r"<p>\sxm\data\sequence"
    for p in os.listdir(RD):
        if p.endswith('.res'):
            f = open(os.path.join(RD,p),'rb')
            f.seek(0x40)
            if f.read(4) != b'\xC0\0\0\0':
                f.close()
                continue
            f.seek(0xC0 + 0x3C)
            f.seek(0xC0 + int.from_bytes(f.read(4),'little'))
            strs = f.read(0x50000).split(b'\0\0',1)[0]
            f.close()
            for x in strs.split(b'\0'): chk(f'data/sequence/{x.decode("ascii")}',False)
elif 0:
    strs = 'abcdefghijklmnopqrstuvwxyz0123456789_'
    def a(abc,c,fnc):
        c -= 1
        if c < 0: fnc(abc)
        else:
            for x in strs: a(abc + x,c,fnc)
    a('',4,lambda abc: chk(f'data/sequence/btl_{abc}.res',False))

print(f'{len(PL)} / {len(HL)} | {len(PL)/len(HL)*100:.2f}%')
open('sxm.hsh','w').write('\n'.join(sorted(PL)))
