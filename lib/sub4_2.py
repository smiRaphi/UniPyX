from lib.main import *
from lib.dldb import BDIR

def extract4_2(inp:str,out:str,t:str):
    run = db.run
    i = inp
    o = out

    def quickbms(scr:str,inf=i,ouf=o,print_try=True):
        scp = db.get(scr)
        if db.print_try and print_try: print('Trying with',scr)
        run(['quickbms','-Y',scp,inf,ouf],print_try=False)
        if listdir(ouf): return
        return 1

    match t:
        case 'Alter Echo REMF':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='<')

            class REMF:
                def __init__(self,o:str,c:int=None):
                    self.o = o
                    self.fts = {}
                    assert self.readt() == 'REMF'
                    f.skip(4)
                    assert self.readt() == 'HEAD'
                    f.skip(f.readu32())

                    if c:
                        for _ in range(c): self.read_block()
                        assert self.readt() == 'ENDC'
                    else:
                        while f and not self.read_block():pass

                def readt(self): return f.read(4).decode('ascii')[::-1]
                def read_block(self):
                    assert self.readt() == 'ENDC'
                    if not f: return 1
                    
                    n = self.readt()
                    s = f.readu32()
                    xoff = s + f.pos
                    match n:
                        case 'OSCR'|'SCRP'|'TRIG':
                            if not n in self.fts: self.fts[n] = 0
                            c = f.readu32()
                            for _ in range(c):
                                fn = f.read0s().decode()
                                xopen(o + f'/{n}{self.fts[n]}/{fn}','wb').write(f.read(f.readu32()))
                            self.fts[n] += 1
                        case 'PTGA':
                            if not n in self.fts: self.fts[n] = 0
                            c = f.readu32()
                            for _ in range(c):
                                f.skip(1)
                                fn = f.read0s().decode()
                                xopen(o + f'/{n}{self.fts[n]}/{fn}','wb').write(f.read(f.readu32()))
                            self.fts[n] += 1
                        case 'DBSS':
                            f.skip(4)
                            if not n in self.fts: self.fts[n] = 0
                            c = f.readu32()
                            for _ in range(c):
                                f.skip(4)
                                fn = f.read0s().decode()
                                xopen(o + f'/{n}{self.fts[n]}/{fn}','wb').write(f.read(f.readu32()))
                            self.fts[n] += 1
                        case 'DBPY':
                            f.skip(8)
                            if not n in self.fts: self.fts[n] = 0
                            c = f.readu32()
                            for _ in range(c):
                                f.skip(5)
                                fn = f.read0s().decode()
                                cc = f.readu32()
                                cp = f.pos
                                REMF(o + f'/{n}{self.fts[n]}/{noext(fn)}',c=cc)
                                lp = f.pos
                                f.seek(cp)
                                xopen(o + f'/{n}{self.fts[n]}/{fn}','wb').write(f.read(lp-cp))
                                f.seek(lp)
                            self.fts[n] += 1
                        case 'BLOK'|'LOD1':
                            if not n in self.fts: self.fts[n] = 0
                            c = 0
                            while f.pos < xoff:
                                sn = self.readt()
                                ss = f.readu32()
                                xopen(o + f'/{n}{self.fts[n]}/{sn}{c}.bin','wb').write(f.read(ss))
                                if not ss: break
                                c += 1
                            c = f.readu32()
                            for _ in range(c):
                                fn = f.read0s().decode()
                                xopen(o + f'/{n}{self.fts[n]}/{fn}','wb').write(f.read(f.readu32()))
                            self.fts[n] += 1
                        case 'PATH':
                            if not n in self.fts: self.fts[n] = 0
                            c = f.readu32()
                            for _ in range(c):
                                fn = f.read0s().decode()
                                xopen(o + f'/{n}{self.fts[n]}/{fn}','wb').write(f.read(f.readu32()*0x10))
                            self.fts[n] += 1
                        case 'CURV'|'LITE'|'MATC'|'JONT'|'JNAM'|'SGMT'|'BINF'|'SEND'|'PTH+'|'MCAM'|'AICH'|'XPLO'|\
                             'FRCE'|'ATAK'|'PHYS'|'PSAN'|'LTRL'|'AMAX'|'ACTN'|'DPND'|'ANIM'|'WTRL'|'AFLG'|'ASLT'|'ATTR'|\
                             'DBOJ'|'OBJS'|'DBSA'|'DBSE'|'ORDR'|'TASK'|'MARK'|'PSFX'|'OCCS'|'SPLS'|'COLL'|'IKCC'|\
                             'PLFX'|'MLBL'|'MNFO'|'CCFT':
                            if not n in self.fts: self.fts[n] = 0
                            xopen(o + f'/{n}{self.fts[n]}.bin','wb').write(f.read(s))
                            self.fts[n] += 1
                        case _: raise NotImplementedError(f'Unknown block: {n} at 0x{f.pos-8:04X} of 0x{s:04x} bytes')
                    f.seek(xoff)

            r = REMF(o)
            f.close()
            if r.fts: return
        case 'Alter Echo RAD':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='<')
            f.skip(4)
            assert f.read(5) == b'\0RAD\0'

            c = f.readu32()
            for _ in range(c):
                f.skip(4)
                fn = f.read0s().decode()
                xopen(o + '/' + fn,'wb').write(f.read(f.readu32()))
            xopen(o + '/$rest.bin','wb').write(f.read())
            f.close()
            if c: return
        case 'One Piece Battle Adventure APF FSM': raise NotImplementedError
        case 'Doom 3 Xbox GFC+GOB':
            t1,t2 = TmpFile('.gfc',path=o),TmpFile('.gob',path=o)
            t1.link(i)
            t2.link(noext(i) + '.gob')
            run(['razbsbor',basename(t1.p),basename(t2.p)],cwd=o)
            t1.destroy()
            t2.destroy()
            if exists(o + '/_' + basename(t2.p)) and listdir(o + '/_' + basename(t2.p)):
                copydir(o + '/_' + basename(t2.p),o,delete=True)
                return
        case 'Doom 3 Xbox Graph':
            tf = TmpFile('.d3tfull',path=o)
            tf.link(i)
            run(['razbsbor',basename(tf.p)],cwd=o)
            tf.destroy()
            if exists(o + '/_' + basename(tf.p)) and listdir(o + '/_' + basename(tf.p)):
                copydir(o + '/_' + basename(tf.p),o,delete=True)
                return
        case 'Culpa Innata SFS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='<')
            assert f.read(4) == b'SFS1'

            c = f.readu16()
            fs = [(f.read(f.readu16()).rstrip(b'\0').decode(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                xopen(o + '/' + fe[0],'wb').write(f.read(f.readu32()))
            f.close()
            if fs: return
        case 'PlayStation 3 Signed Package':
            run(['ps3_unpkg',i,o],env={'PS3_KEYS':db.get('ps3oskeys')})
            if listdir(o):
                if exists(o + '/content') and exists(o + '/info0') and exists(o + '/info1') and getsize(o + '/info0') == getsize(o + '/info1') == 0x40:
                    return extract4_2(o + '/content',o + '/OS Core','PlayStation 3 Core OS Package')
        case 'PlayStation 3 Core OS Package':
            run(['ps3_cosunpkg',i,o],env={'PS3_KEYS':db.get('ps3oskeys')})
            if listdir(o): return
        case 'PlayStation Trophy File':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='>')
            assert f.read(4) == b'\xDC\xA2\x4D\x00'

            v = f.readu32()
            if v not in (1,2,3): raise NotImplementedError(f'Version: {v}')
            f.skip(8)
            c = f.readu32()
            s = f.readu32()
            if s != 0x40: raise NotImplementedError(f'Entry Size: {s}')
            if v < 3: f.skip(0x28)
            else: f.skip(0x18)

            fs = []
            for _ in range(c):
                fs.append((f.read(0x20).rstrip(b'\0').decode(),f.readu64(),f.readu64()))
                f.skip(0x10)

            for fe in fs:
                f.seek(fe[1])
                xopen(o + '/' + fe[0],'wb').write(f.read(fe[2]))
            f.close()
            if fs: return
        case 'Phineas And Ferb WAD':
            if db.print_try: print('Trying with custom extractor') # WIP
            import json
            from lib.file import File
            f = File(inp,endian='>')
            assert f.read(8) == b'\0\0\0\0\0\x03\0\0'

            dicc = f.readu32()
            dico = f.readu32()
            cntc = f.readu32()
            cnto = f.readu32()
            f.skip(8)
            sdbc = f.readu32()
            sdbo = f.readu32()

            f.seek(sdbo)
            sdb = {}
            for _ in range(sdbc):
                h = f.readu32()
                sdb[h] = f.readu32()
            for h in sdb:
                f.seek(sdb[h])
                sdb[h] = f.read0s().decode()

            f.seek(dico)
            dic = {}
            for _ in range(dicc):
                nh = f.readu32()
                dic[sdb[nh]] = (f.readu32(),f.readu32())
            f.seek(cnto)
            cnt = {}
            for _ in range(cntc):
                c = (f.readu32(),f.readu32())
                f.skip(8)
                cnt[sdb[f.readu32()]] = c
                f.skip(4)

            ob = {}
            cc = None
            for tn in dic:
                f.seek(dic[tn][1])
                ob[tn] = {}
                for ix in range(dic[tn][0]):
                    nh = f.readu32()
                    if nh:
                        f.skip(1)
                        tp = f.readu8()
                        f.skip(2+4)
                        of = f.readu32()
                        if tp == 11: cc = (sdb[nh],of)
                        else: ob[tn][sdb[nh]] = (tp,of)
                    elif cc:
                        f.skip(1)
                        st = f.readu8()
                        f.skip(2)
                        if st == 14: cn = -1
                        else: cn = sdb[f.readu32()]
                        ob[tn][cc[0]] = (cn,cc[1])
                    else: raise ValueError(f.pos-4)
            for cn in cnt:
                f.seek(cnt[cn][1])
                if cn == 'WadFile':
                    if cn in ob: ob.pop(cn)
                    c = f.readu32()
                    f.seek(f.readu32())
                    fs = []
                    for _ in range(c): fs.append((sdb[f.readu32()],f.readu32(),f.readu32()))
                    for fe in fs:
                        f.seek(fe[2])
                        xopen(o + '/' + fe[0],'wb').write(f.read(fe[1]))
                elif cn in ob:
                    for tn in ob[cn]:
                        f.seek(cnt[cn][1] + ob[cn][tn][1])
                        match ob[cn][tn][0]:
                            case 1: v = f.readu8() != 0
                            case 2: v = f.readf32()
                            case 8: v = f.readu8()
                            case 11: raise ValueError('Unparsed class type')
                            case 12: v = f.readu32()
                            case _: raise NotImplementedError(cn + '/' + tn + ': ' + str(ob[cn][tn][0]))
                        ob[cn][tn] = v

            f.close()
            if ob: json.dump(ob,xopen(o + '/$' + tbasename(inp) + '.json','w',encoding='utf-8'),ensure_ascii=False,indent=4)
            if listdir(o): return
        case 'NCAA Gamebreaker PG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='<')

            c = f.readu32()
            fs = [f.readu32() for _ in range(c)]
            fs.append(f.size)
            for ix in range(len(fs)-1):
                f.seek(fs[ix])
                d = f.read(fs[ix+1]-fs[ix])
                if d[:4] == b'INDX': ext = 'indx'
                else: ext = guess_ext_ps2(d)
                open(o + f'/{ix:02d}.{ext}','wb').write(d)
            f.close()
            if fs: return
        case 'Orange Juice Encrypted':
            of = o + '\\' + basename(inp)
            run(['qpcrypt','decrypt',i,of])
            if exists(of) and getsize(of): return
        case 'Orange Juice LAG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='<')
            assert f.read(4) == b'LAG\0'
            f.skip(4)

            while f:
                fn = f.read(0x10).rstrip(b'\0').decode()
                w,h = f.readu32(),f.readu32()
                fmt = f.readu32()
                if not fmt in (1,2): raise NotImplementedError(f'Pixel format: 0x{fmt:2X}')
                xopen(o + f'/{fn}_{w}x{h}.{(0,"rgba8","argb16")[fmt]}','wb').write(f.read(f.readu32()))
            f.close()
            if listdir(o): return
        case 'Destruction Derby 2 DirInfo':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='<')

            fs = []
            while f:
                fn = f.read(0x12).split(b'\0',1)[0]
                if not fn: break
                fs.append((fn.decode('ascii'),f.readu16()*0x800,f.readu32()))

            for fe in fs:
                f.seek(fe[1])
                xopen(o + '/' + fe[0],'wb').write(f.read(fe[2]))
            f.close()
            if fs: return
        case 'One Piece Straw Wars Pirate Defense Resource':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='>')
            f.skip(8)

            c = f.readu32()
            fs = [(f.read(f.readu32()).rstrip(b'\0').decode(),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                xopen(o + '/' + fe[0],'wb').write(f.read(fe[2]))
            f.close()
            if fs: return
        case 'D1 Grand Prix Series 2005 BIN':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='<')

            c = f.readu32() - 1
            so = f.readu32()
            f.seek(so)
            sos = [f.readu32()+so for _ in range(c)]

            f.seek(12)
            fs = [(sos[ix],f.readu32(),f.readu32()) for ix in range(c)]
            for fe in fs:
                f.seek(fe[0])
                n = f.read0s().decode()
                f.seek(fe[1])
                xopen(o + '/' + n,'wb').write(f.read(fe[2]))
            f.close()
            if fs: return
        case 'RenderWare Texture Dictionary':
            mkdir(o)
            run(['rwexporter','-txd',i,o])
            if listdir(o): return
        case 'Groove World Archive':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='>')
            f.skip(12)

            rt = f.read0s().decode()
            c = f.readu32()
            fs = []
            for _ in range(c):
                f.skip(4)
                fs.append((f.readu32(),f.readu32(),f.read0s().decode()))
            for fe in fs:
                f.seek(fe[0])
                xopen(f'{o}/{rt}/{fe[2]}','wb').write(f.read(fe[1]))
            f.close()
            if fs: return
        case 'Metal Slug 3D PAK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) in (b'DATA',b'MENU',b'SEDT',b'STRD')
            f.skip(8)

            c = f.readu32()
            fs = [f.readu32() for _ in range(c+1)]
            for ix in range(c):
                f.seek(fs[ix])
                d = f.read(fs[ix+1]-fs[ix])
                if d[:4] == b'PK\0\x02': ext = 'pk'
                elif d[:4] in (b'DATA',b'MENU',b'SEDT',b'STRD'): ext = 'pak'
                else: ext = guess_ext_ps2(d)
                open(o + f'/{ix:02d}.{ext}','wb').write(d)
            if fs: return
        case 'OHRRPGCE RPG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='-')

            while f:
                fn = f.read0s().decode()
                while fn.startswith(('../','..\\')): fn = fn[3:] 
                xopen(o + '/' + fn,'wb').write(f.read(f.readu32()))
            f.close()
            if listdir(o): return
        case 'Ludia Dir':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(inp,endian='>')

            co = f.readu32()
            f.skip(0x1C)
            omp = {}
            for _ in range(co):
                op = f.readu32()
                vop = f.readu32()
                if vop == 1: omp[op] = f.pos + 0x18
                elif vop != 0: print('Unknown offset map bool:',vop,op,f.pos-8)
                f.skip(f.readu32()+0x14)

            c = f.readu32()
            f.skip(0x1C)
            fs = []
            for _ in range(c):
                fn = f.read(4).hex().upper()
                fn = f.read(4).hex().upper() + '/' + fn
                off = f.readu32()
                if off == 0: off = 0x40
                else: off = omp[off]
                fs.append((off+f.readu32(),f.readu32(),fn))
                f.skip(12)

            for fe in fs:
                f.seek(fe[0])
                d = f.read(fe[1])
                if d[:6] == b'<root>' and (d[-7:] == b'</root>' or d[-8:] == b'</root>\t' or d[-9:] == b'</root>\r\n'): ext = 'xml'
                elif d[:4] == b'\x00\x20\xAF\x30': ext = 'tpl'
                elif len(d) == 0x38 and d[:4] == b'\x02\0\0\x02' and d[0x20:0x24] == b'\0\0\0\x02' and d[0x28:0x34] == b'\x3F\x80\0\0\x3F\x80\0\0\0\0\0\x01': ext = 'mat'
                elif len(d) == 0x1C and d[:12] == b'\x02\0\0\x02\x07\xDA\x0B\x0C\x84\xDF\x2E\x3D': ext = 'spt'
                elif len(d) in (0x3C,0x20) and d[:12] == b'\x02\0\0\x02\x07\xDA\x0B\x0C\x9E\x44\xEB\xDC' and d[0x14:0x18] == b'\0\0\0\0' and d[0x1C:0x1F] == b'\0\0\0' and d[0x1F] in (0,1): ext = 'txs'
                elif len(d) == 0x70 and d[:12] == b'\x02\0\0\x02\x07\xDA\x0B\x0C\x11\xB7\x85\xc4': ext = 'mdl'
                elif len(d) == 0x6C and d[:12] == b'\x02\0\0\x02\x07\xDA\x0B\x0C\x8A\xDE\x4F\xA6': ext = 'cam'
                elif len(d) >= 0x2C and not len(d)%4 and len(d) <= 0x100 and d[:12] == b'\x02\0\0\x02\x07\xDA\x0B\x0C\x12\x0D\x26\x3D': ext = 'scn'
                elif not len(d)%8 and d[:12] == b'\x02\0\0\x02\x07\xDA\x0B\x0C\x75\xBF\xBD\xE6': ext = 'vtx'
                elif not len(d)%2 and d[:8] == b'\0\0\0\x02\0\0\0\x02' and d[11] and d[8:12] == d[12:16] == d[20:24]: ext = 'msh'
                else: ext = 'bin'
                xopen(o + f'/{fe[2]}.{ext}','wb').write(d)
            f.close()
            if fs: return
        case 'Mission Impossible 3 Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu16()
            fs = [f.readu32()+2+c*4 for _ in range(c)]
            for ix in range(c-1):
                f.seek(fs[ix])
                open(o + f'/{ix:02d}.bin','wb').write(f.read(fs[ix+1]-fs[ix]))
            f.close()
            if fs: return
        case 'Blade Runner TLK/MIX':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu16()
            bo = f.size-f.readu32()

            fs = [(f.read(4)[::-1].hex().upper(),f.readu32()+bo,f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                d = f.read(fe[2])
                if d[:2] == b'\x22\x56': ext = 'audio'
                elif d[:4] == b'FORM' and d[8:12] == b'WVQA': ext = 'wvqa'
                elif d[:3] == b'Set' and d[3:4].isdigit(): ext = 'set'
                else: ext = 'bin'
                open(o + f'/{fe[0]}.{ext}','wb').write(d)
            f.close()
            if fs: return
        case 'Nintendo HARC+HIDX':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            fd = open(noext(i) + '.har','rb')
            f = File(noext(i) + '.hix',endian='<')
            assert f.read(4) == b'HIDX' and fd.read(4) == b'HARC'

            c = f.readu32()
            fs = [(f.read(9).hex().upper(),f.readu32(),f.readu32()) for _ in range(c)]
            f.close()
            for fe in fs:
                fd.seek(fe[1]+12)
                d = fd.read(fe[2])
                if d[:4] == b'\x89PNG': ext = 'png'
                else: ext = 'bin'
                open(o + f'/{fe[0]}.{ext}','wb').write(d)
            fd.close()
            if fs: return
        case 'Petroglyph MEG':
            if db.print_try: print('Trying with custom extractor')
            from zlib import crc32
            from lib.file import File
            f = File(i,endian='<')

            fnc = f.readu32()
            fc = f.readu32()
            if fnc == fc: v = 1
            else:
                assert fc == 0x3F7D70A4
                assert fnc in (0x8FFFFFFF,0xFFFFFFFF)
                AES = fnc == 0x8FFFFFFF
                ds = f.readu32()
                fnc = f.readu32()
                fc = f.readu32()
                if AES:
                    try: from Cryptodome.Cipher import AES # type: ignore
                    except ImportError: from Crypto.Cipher import AES # type: ignore
                    v = 3

                    fns = f.readu32()
                    fns += -fns%0x10
                    f.skip(fns)
                    for _ in range(fc):
                        if f.readu16(): break
                        f.skip(0x12)
                    else: raise NotImplementedError('Encrypted archive without encrypted file entries, can\'t get/verify key')
                    ent = f.read(0x20)

                    DB = BDIR + '/bin/pet_megkeys.bdb'
                    if not exists(DB):
                        import re
                        bdb = open(DB,'wb')
                        for k in re.findall(r'Key: *([\dA-Fa-f]{32}).*<br */>\s*IV: *([\dA-Fa-f]{32})',db.c.get('https://modtools.petrolution.net/docs/MegFileFormat').text): bdb.write(bytes.fromhex(k[0] + k[1]))
                        bdb.close()
                    bdb = open(DB,'rb')
                    kdb = []
                    while True:
                        kiv = bdb.read(0x20)
                        if not kiv: break
                        kdb.append((kiv[:0x10],kiv[0x10:]))

                    for k,iv in kdb:
                        def aes(i:bytes): return AES.new(key=k,mode=AES.MODE_CBC,IV=iv).decrypt(i)
                        dent = aes(ent)
                        if not sum(dent[4:8]) and int.from_bytes(dent[12:16],'little') == ds:break
                    else: raise NotImplementedError('Key not found')
                else:
                    fns = f.readu32()
                    if (0x18+fns+fc*0x14) == ds:
                        aes = None
                        v = 3
                    else: v = 2

            f.seek([8,0x14,0x18][v-1])
            sdb = {}
            if v < 3 or not aes:
                for _ in range(fnc):
                    fn = f.read(f.readu16())
                    sdb[crc32(fn) & 0xFFFFFFFF] = fn.decode('ascii')
                if v == 3: f.seek(0x18+fns)
            else:
                fnd = aes(f.read(fns))
                for _ in range(fnc):
                    fnl = int.from_bytes(fnd[:2],'little')
                    fn,fnd = fnd[2:fnl+2],fnd[fnl+2:]
                    sdb[crc32(fn) & 0xFFFFFFFF] = fn.decode('ascii')

            fs = []
            dn = {}
            for _ in range(fc):
                if v == 3:
                    if f.readu16():
                        assert aes
                        fe = aes(f.read(0x20))
                        crc = int.from_bytes(fe[:4],'little')
                        fidx = int.from_bytes(fe[0x10:0x12],'little')
                        fe = [int.from_bytes(fe[8:12],'little'),int.from_bytes(fe[12:16],'little')]
                    else:
                        crc = f.readu32()
                        f.skip(4)
                        fe = [f.readu32(),f.readu32()]
                        fidx = f.readu16()
                else:
                    crc = f.readu32()
                    f.skip(4)
                    fe = [f.readu32(),f.readu32()]
                    fidx = f.readu32()

                icrc = list(sdb)[fidx-1]
                if not crc in sdb or (crc in dn and not icrc in dn): crc = icrc
                if not crc in dn: dn[crc] = 0
                fs.append([sdb[crc] + (f'.{dn[crc]}' if dn[crc] else '')] + fe)
                dn[crc] += 1

            for fe in fs:
                f.seek(fe[2])
                d = f.read(fe[1])
                if v == 3 and aes: d = aes(d + f.read(-fe[1]%0x10))[:fe[1]]
                xopen(o + '/' + fe[0],'wb').write(d)
            f.close()
            if fs: return
        case 'Petroglyph Zlib CH':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='>')
            f.skip(0x10)
            s = f.readu32()
            f.skip(0x10)
            open(o + '/' + basename(i),'wb').write(zlib.decompress(f.read(s)))
            f.close()
            if s: return
        case 'Petroglyph CHK List':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')
            f.skip(6)
            c = f.readu16()

            of = open(o + '/' + tbasename(i) + '.txt','w')
            for _ in range(c):
                assert f.readu32() == 0
                f.skip(2)
                nxp = f.readu16() + f.pos
                of.write(f.read(f.readu16()).decode() + '\n')
                f.seek(nxp)
            f.close()
            of.close()
            if c: return
        case 'Hatch Game Engine HATCH':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(5) == b'HATCH' and f.readu24() == 1
            c = f.readu16()

            sdb = open(db.get('hatch/sonic_galactic_demo2.txt')).read().replace('../','').replace('..\\','').split('\n')
            sdb += [
                "Music/Pause.ogg",
                "Music/Bonus.ogg",
                "Scenes/BonusStage/0.tmx",
                "Scenes/BonusStage/8.tmx",
                "Scenes/URZ/TileConfig.bin",
                "Scenes/Menus/LevelSelect.tmx",
                "Scenes/Menus/SpecialStageResults.tmx",
                "Sprites/CGZ/robocutscene/WhaleWaterDrip.bin",
                "Models/SpecialStage/Prism.mtl",
                "Objects/00D71C4D.ibc","Objects/031EE258.ibc","Objects/0346F6B3.ibc","Objects/064D6CFE.ibc","Objects/0A6E196B.ibc","Objects/13073F4D.ibc","Objects/14788EAA.ibc","Objects/171E1A4F.ibc","Objects/176FF6D0.ibc","Objects/195CC741.ibc","Objects/1F0F32D3.ibc","Objects/23F493FF.ibc","Objects/257B075B.ibc","Objects/2933F80F.ibc","Objects/2B6CE206.ibc","Objects/2B8DC6F8.ibc","Objects/2C73DA4E.ibc","Objects/2FB3F065.ibc","Objects/313D8216.ibc","Objects/3957C884.ibc","Objects/39F5D55A.ibc","Objects/3C0C7D95.ibc","Objects/3F1EE089.ibc","Objects/424A46AD.ibc","Objects/45E5BEB7.ibc","Objects/46C51724.ibc","Objects/470FBA93.ibc","Objects/47ABABD7.ibc","Objects/54A9000E.ibc","Objects/54B60127.ibc","Objects/59813EB6.ibc","Objects/5A21748A.ibc","Objects/5B950600.ibc","Objects/5CD8D231.ibc","Objects/619009F4.ibc","Objects/63259C4D.ibc","Objects/6469B94A.ibc","Objects/65A3AB98.ibc","Objects/662212AD.ibc","Objects/69D6F0D1.ibc","Objects/6AC70B8E.ibc","Objects/6CC0DFC4.ibc","Objects/7006C23B.ibc","Objects/700E6286.ibc","Objects/72A3605F.ibc","Objects/72B75E8B.ibc","Objects/74DC46AA.ibc","Objects/76B4E577.ibc","Objects/782C6CBB.ibc","Objects/78AA940F.ibc","Objects/795137D2.ibc","Objects/7967014D.ibc","Objects/7B85D0B3.ibc","Objects/7BF78CCB.ibc","Objects/7E855216.ibc","Objects/83159BB7.ibc","Objects/839DBFD7.ibc","Objects/859241D1.ibc","Objects/85A03876.ibc","Objects/87F2E47B.ibc","Objects/8F6881EB.ibc","Objects/9643FE12.ibc","Objects/A8BF5D29.ibc","Objects/AAEF9CF0.ibc","Objects/AC3BF2A9.ibc","Objects/B0BF217B.ibc","Objects/B320A756.ibc","Objects/B4531A19.ibc","Objects/B73D2477.ibc","Objects/BB0D7D0A.ibc","Objects/BBCBEFC8.ibc","Objects/BC0AEBD7.ibc","Objects/C0E8F4FB.ibc","Objects/C13D30D5.ibc","Objects/C3053FA6.ibc","Objects/C6F46193.ibc","Objects/C87BD4F5.ibc","Objects/CC00CC0C.ibc","Objects/CC98E906.ibc","Objects/CF6650EA.ibc","Objects/D1853F83.ibc","Objects/D20E5DD9.ibc","Objects/D2190C24.ibc","Objects/D23D0EF1.ibc","Objects/DAEA4D68.ibc","Objects/DB281BB8.ibc","Objects/DB7AF940.ibc","Objects/E018F13B.ibc","Objects/E1E8A679.ibc","Objects/E5F16295.ibc","Objects/E89B8F94.ibc","Objects/EB62E8A4.ibc","Objects/ECFD2F78.ibc","Objects/EF11E0C3.ibc","Objects/F0BBFC4A.ibc","Objects/F3FB47D5.ibc","Objects/F462DB66.ibc","Objects/F4F906AE.ibc","Objects/FA58AFC8.ibc",
                "Sprites/HPZ/SparkKino.png",
                "Sprites/CGZ/Teleporter.png",
                "Sprites/Global/Tornado.bin",
                "Sprites/Global/SelectionArrow.bin",
                "Sprites/HPZ/GreenFuse.bin",
                "Sprites/Menu/Options/ControllerKeys.bin",
                "SoundFX/Announcer/Sonic.wav",
                "SoundFX/Announcer/Knuckles.wav",
                "SoundFX/Announcer/Mighty.wav",
                "SoundFX/Announcer/ItsADraw.wav",
                "SoundFX/Announcer/Ray.wav",
                "SoundFX/Announcer/Tails.wav",
                "SoundFX/Announcer/Player4.wav",
                "SoundFX/Announcer/TailsWins.wav",
                "SoundFX/Announcer/SonicWins.wav",
                "SoundFX/Announcer/RayWins.wav",
                "SoundFX/Announcer/MightyWins.wav",
            ]
            sdb = {zlib.crc32(x.encode()):x for x in sdb}
            sdb |= {
                0x2A84DBA6:"$Unknown/unk_green_2A84DBA6.png",
                0x2E8D1037:"$Unknown/waterfall_anim1_2E8D1037.png",
                0x4A9387E1:"$Unknown/unk_yellow_4A9387E1.png",
                0x08DD0A7D:"$Unknown/CGZ_below_9.5_08DD0A7D.png",
                0x8DCA6B9E:"$Unknown/thank_you_for_playing_8DCA6B9E.png",
                0x13ED3987:"$Unknown/waterfall_anim2_flower_13ED3987.png",
                0x31EF6B33:"$Unknown/CGZ_act1bg_31EF6B33.png",
                0x122B55F1:"$Unknown/VIZ_VIZ2bg_122B55F1.png",
                0x77F3AE51:"$Unknown/bubble_77F3AE51.png",
                0x133C3367:"$Unknown/sonic_3d_tex_133C3367.png",
                0x692D6AE7:"$Unknown/waterfall_anim3_692D6AE7.png",
                0x730F0253:"$Unknown/act_screen_730F0253.png",
                0x3321A2AA:"$Unknown/whale_fire_3321A2AA.png",
                0x558B2F21:"$Unknown/island_558B2F21.png",
                0xE0304E8F:"$Unknown/sonic_3d_E0304E8F.fbx",
                0xEEFE54BA:"$Unknown/EEFE54BA.dae",
                0x54B5C58C:"$Unknown/URZ_54B5C58C.tmx",
            }

            fs = []
            for _ in range(c):
                crc = f.readu32()
                off = f.readu64()
                us = f.readu64()
                enc = f.readu32() & 2
                s = f.readu64()

                if crc in sdb:
                    fn = sdb[crc]
                    assert fn[:2] != '..'
                    #while fn.startswith(('../','..\\')): fn = fn[3:]
                else: fn = f'\0{crc:08X}.'

                fs.append([fn,off,s,us,(crc.to_bytes(4,'little')*4,zlib.crc32(us.to_bytes(8,'little')).to_bytes(4,'little')*4,(us >> 2) & 0x7F) if enc else ()])

            for fe in fs:
                f.seek(fe[1])
                d = f.read(fe[2])
                if fe[2] != fe[3]: d = zlib.decompress(d)
                if fe[4]:
                    d = bytearray(d)
                    swp = idx1 = 0
                    idx2 = 8
                    xr = fe[4][2]
                    for ix in range(fe[3]):
                        v = d[ix]
                        v ^= xr ^ fe[4][1][idx2];idx2 += 1
                        if swp: v = ((v & 0x0F) << 4) | (v >> 4)
                        v ^= fe[4][0][idx1];idx1 += 1
                        d[ix] = v

                        if idx1 < 16:
                            if idx2 > 12:
                                idx2 = 0
                                swp = not swp
                        elif idx2 <= 8:
                            idx1 = 0
                            swp = not swp
                        else:
                            xr = (xr + 2) & 0x7F
                            if swp:
                                swp = 0
                                idx1 = xr % 7
                                idx2 = (xr % 12) +2
                            else:
                                swp = 1
                                idx1 = (xr % 12) + 3
                                idx2 = xr % 7
                    d = bytes(d)
                if fe[0][0] == '\0':
                    fn = fe[0][1:]
                    if d[:4] == b'SPR\0': fn += 'spr'
                    elif d[:4] == b'TCOL': fn += 'tcol'
                    elif d[:4] == b'HTVM': fn += 'ibc'
                    elif d[:4] == b'HMAP': fn += 'hcm'
                    elif d[:4] == b'HMDL': fn += 'hmdl'
                    else: fn += guess_ext(d)
                else: fn = fe[0]
                xopen(o + '/' + fn,'wb').write(d)
            f.close()

            if fs: return
        case 'Hatch Game Engine HMAP':
            if db.print_try: print('Trying with custom extractor')
            import json
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(8) == b'HMAP\x00\x01\x02\x03'
            c = f.readu32()

            ob = {}
            for _ in range(c):
                k = f.read(4)[::-1].hex().upper()
                sc = f.readu32()
                ob[k] = []
                for _ in range(sc): ob[k].append(f.read(4)[::-1].hex().upper())

            f.close()
            if ob:
                json.dump(ob,open(o + f'/{tbasename(i)}.json','w'),indent=2)
                return
        case 'Tiled TMX/TSX':
            if db.print_try: print('Trying with custom extractor')
            import base64,zlib
            import xml.etree.ElementTree as ET

            tr = ET.parse(i)
            rt = tr.getroot()
            for l in rt.findall('layer'):
                n = l.get('name')
                for ix,d in enumerate(l.findall('data')):
                    rd = d.text
                    if d.get('encoding') == 'base64': rd = base64.b64decode(rd)
                    if d.get('compression') == 'zlib': rd = zlib.decompress(rd)
                    if type(rd) != bytes: rd = rd.encode()
                    xopen(o + f'/{n}/{ix}.bin','wb').write(rd)
            del tr
            if listdir(o): return
        case 'Pixelbite BAR':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'CRAB'
            f.seek(-8,2)
            f.seek(f.readu32())
            c = f.readu32()

            fs = []
            for _ in range(c):
                fs.append((f.readu32(),f.readu32(),f.readu8(),f.read(f.readu16())[:-1].decode()))
                assert fs[-1][2] in (0,1)
                f.skip(4)

            for fe in fs:
                f.seek(fe[0])
                if fe[2]:
                    assert f.read(4) == b'PxZP'
                    f.skip(4)
                    d = zlib.decompress(f.read(f.readu32()))
                else: d = f.read(fe[1])
                xopen(o + '/' + fe[3],'wb').write(d)
            f.close()
            if fs: return
        case 'Pixelbite ZIP':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'PxZP'
            f.skip(4)
            open(o + '/' + basename(i),'wb').write(zlib.decompress(f.read(f.readu32())))
            f.close()
            return
        case 'Codename Kids Next Door JAM2/FSTA':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            ty = f.read(4)
            assert ty in (b'FSTA',b'JAM2')

            tm = f.readu32()
            fo = f.readu32()
            dn = f.read(0x10).rstrip(b'\0').decode('ascii')
            if dn: dn += '/'
            fnc = f.readu16()
            exc = f.readu16()

            fndb = [f.read(8).rstrip(b'\0').decode('ascii') for _ in range(fnc)]
            exdb = [f.read(4).rstrip(b'\0').decode('ascii') for _ in range(exc)]
            f.skip(4)
            fs = []
            while f.pos < fo:
                fid = f.readu16()
                eid = f.readu16()
                off = f.readu32()
                if off >= fo:
                    fe = [off,(fndb[fid] + '.' + exdb[eid]).rstrip('.')]
                    if ty == b'FSTA': fe.append(f.readu32())
                    fs.append(fe)

            for ix,fe in enumerate(fs[:-1]):
                f.seek(fe[0])
                if ty == b'FSTA': d = f.read(fe[2])
                else:
                    s = f.readu32()
                    assert s == f.readu32()
                    f.skip(0x18)
                    d = f.read(s)
                xopen(o + f'/{dn}{fe[1]}','wb').write(d)
                set_ctime(o + f'/{dn}{fe[1]}',tm)
            f.close()
            if fs: return
        case 'High Impact Games WAD':
            if db.print_try: print('Trying with tjzip_dump')
            db.get('tjzip_dump')
            from bin.tjzip_dump import parse_hig_wad,tjzip_decompress,TJZIPError # type: ignore

            inp = open(i,'rb').read()
            try:
                _,coff,dsiz = parse_hig_wad(inp)
                coff = 0xC0 # force header size to 0xC0
                r,_ = tjzip_decompress(inp[coff:],dsiz,crc_table=None,limit_out=None,history_size=0x10000)
            except TJZIPError: return 1

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(r,endian='<')
            f.skip(13)

            while f:
                if not sum(f.read(4)):
                    f.skip(12)
                    continue
                p = f.read(0x60)
                f.back(0x60)
                if len(p.rstrip(b'\0')) >= 0x10:
                    try:d = p.rstrip(b'\0').decode('ascii')
                    except:f.skip(12)
                    else:
                        if d.isprintable():break
            else:
                f.close()
                open(o + '/' + basename(i) + '.bin','wb').write(r)
                return

            f.back(4)
            while f:
                while f and not sum(f.read(4)):f.skip(12)
                p = f.read(0x60)
                if len(p) != 0x60: break
                p = p.rstrip(b'\0').decode('ascii').replace(':','_')
                f.skip(4)
                s = f.readu32()
                f.skip(0x54)
                xopen(o + '/' + p,'wb').write(f.read(s))
                f.skip(-s%0x10)
            f.close()
            if listdir(o): return
        case 'Lucky Chicken TOC+HFF':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,encoding='utf-8')
            fd = open(noext(i) + '.hff','rb')

            c = int(f.readline().strip())
            for _ in range(c):
                l = f.readline().strip().split('|')
                fd.seek(int(l[3]))
                xopen(o + '/' + l[1].strip('/') + '/' + l[0],'wb').write(fd.read(int(l[2])))
            f.close()
            fd.close()
            if c: return
        case 'PSX PFW':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'PFW2'
            c = f.readu16()
            f.skip(10)

            fs = [((f.read(8).rstrip(b'\0').decode('ascii') + '.' + f.read(3).rstrip(b'\0').decode('ascii')).rstrip('.'),f.readu24(),f.readu16()*0x800) for _ in range(c)]
            for fe in fs:
                f.seek(fe[2])
                xopen(o + '/' + fe[0],'wb').write(f.read(fe[1]))
            f.close()
            if fs: return
        case 'Lucas Arts Bundle':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            doff = None
            fs = []
            def readb():
                nonlocal doff
                n = f.read(4).decode('ascii')
                s = f.readu32()
                p = f.pos + s

                match n:
                    case 'BUND':
                        while f.pos < p: readb()
                    case 'BNHD':
                        f.skip(6)
                        pd = f.readu32('<')
                        c = f.readu32('<')
                        k = f.read(1)
                        kv = k[0]
                        f.skip(0x13)

                        f.skip(pd*2)
                        for _ in range(c):
                            n = bytes(x ^ kv for x in f.read(0xC8).split(k)[0]).decode('ascii')
                            fs.append((n,f.readu32('<'),f.readu32('<'))) # le
                            f.skip(0x2C)
                    case 'BNDT':
                        assert not doff
                        doff = f.pos

                f.seek(p)
            readb()
            if not doff:
                print('Data chunk not found, correct full file may be on a different disc')
                return 1

            for fe in fs:
                f.seek(doff + fe[2])
                xopen(o + '/' + fe[0].lstrip('/\\'),'wb').write(f.read(fe[1]))
            f.close()
            if fs: return
        case 'Action Replay RAM Disk':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu32()
            f.skip(4)

            fs = [f.readu32() for _ in range(c)]
            for fe in fs:
                f.seek(fe)
                assert f.read(4) == b'\xA1'*4
                s = f.readu32()
                n = f.read0s().decode('ascii').replace(':','_').strip('/\\')
                f.read0s()
                f.alignpos(4)
                xopen(o + '/' + n,'wb').write(f.read(s))
            f.close()
            if fs: return
        case 'SharkPortSave':
            PLAT = {
                0x000:'PS2',
                0xF00:'GBA',
            }

            if db.print_try: print('Trying with custom extractor')
            from datetime import datetime
            from lib.file import File
            f = File(i,endian='<')
            def reads(): return f.read(f.readu32()).decode('utf-8')
            inf = open(o + '/$saves.txt','w',encoding='utf-8')

            c = 0
            while f:
                if reads() != 'SharkPortSave':break
                inf.write(f'{c}:\n')
                p = f.readu32()
                inf.write(f'Platform: {PLAT[p] if p in PLAT else "?"} [0x{p:08X}]\n')
                inf.write(f'Game: {reads()}\nSave/Date: {reads()}\nComment: {reads()}\n')
                s = f.readu32()
                inf.write(f'Size: 0x{s:X}\n')
                ep = f.pos + s

                if p == 0:
                    def reade(pn):
                        hs = f.readu16()
                        p = f.pos + hs - 2
                        n = f.read(0x40).rstrip(b'\0').decode('utf-8')
                        s = f.readu32()
                        f.skip(8)
                        m = f.readu16('>') # be
                        f.skip(2)
                        dr = m & 0x20
                        if not dr:
                            f.skip(1)
                            tm = datetime(second=f.readu8(),minute=f.readu8(),hour=f.readu8(),day=f.readu8(),month=f.readu8(),year=f.readu16()).timestamp()

                        f.seek(p)
                        if dr: [reade(pn + '/' + n) for _ in range(s-2)]
                        else:
                            xopen(pn + '/' + n,'wb').write(f.read(s))
                            set_ctime(pn + '/' + n,tm)
                    reade(o)
                else: raise NotImplementedError(f'Platform: 0x{p:08X}')

                f.seek(ep)
                inf.write(f'CRC: {f.readu32():08X}\n\n')
                c += 1
                f.alignpos(0x800)
            inf.close()
            f.close()
            if len(listdir(o)) > 1: return
        case 'Favorite Dear LKF': return quickbms('favorite_dear_lkf_script')
        case 'Favorite Dear MSG 1':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu16()//2
            f.seek(0)

            ofs = [f.readu16() for _ in range(c)]
            of = open(o + f'/{tbasename(i)}.txt','w',encoding='utf-8')
            for off in ofs:
                f.seek(off)
                s = f.readu16()
                s1 = f.readu16()
                if s1 < 0xA00: s = s1
                else: f.back(2)
                of.write(f.read(s).decode('shift-jis') + '\n\n')
            of.close()
            f.close()
            if ofs: return
        case 'Favorite Dear MSG 2':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu16()

            fs = [(f.readu16(),f.readu16()) for _ in range(c)]
            of = open(o + f'/{tbasename(i)}.txt','w',encoding='utf-8')
            for fe in fs:
                f.seek(fe[1])
                of.write(f'{fe[0]}:\n')
                for ix in [ix for ix in range(0x12) if sum(f.read(2))]:
                    of.write(f'{ix}:\n')
                    s = f.readu16()
                    of.write('\n'.join(x.decode('shift-jis') for x in f.read(s).split(b'\0')) + '\n')
                    f.skip(2)
                of.write('\n')
            of.close()
            f.close()
            if fs: return
        case 'Batman AC Resource':
            raise NotImplementedError
            # https://wiki.osdev.org/NE
            if db.print_try: print('Trying with custom extractor')
            from lib.file import EXE
            f = EXE(i)
            f.seek(f.reco)
        case 'Mini Metro Sound Bytes':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = 0
            while f:
                s = f.readu32()
                d = f.read(s)
                open(f'{o}/{c:03d}.{guess_ext(d)}','wb').write(d)
                c += 1
            f.close()
            if c: return
        case 'Metropolis Software ZAP': raise NotImplementedError
        case 'Def Jam Fight For NY: The Takeover PAKN':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'PAKN'
            c = f.readu32()
            ds = f.readu32() + 12

            fs = [(f.read(0x38).rstrip(b'\0').decode(),ds+f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                n = fe[0]
                while n.startswith(('./','../')): n = n.split('/',1)[1]
                xopen(f'{o}/{n}','wb').write(f.read(fe[2]))
            if fs: return
        case 'Pseudo Interactive PIX':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')
            if exists(dirname(i) + '/textures.pit'): fd = open(dirname(i) + '/textures.pit','rb')
            else: fd = None

            while f:
                s = f.readu32()
                if not s: break
                f.alignpos(0x800)
                sf = File(zlib.decompress(f.read(s)),endian='<')
                c = sf.readu32()

                for _ in range(c):
                    ss = sf.readu32()
                    n = sf.read0s().decode()
                    d = sf.read(ss)
                    xopen(f'{o}/{n}','wb').write(d)

                    if n.endswith('.x2m') and sum(d[0x18:0x1C]) and fd:
                        fd.seek(int.from_bytes(d[0x1C:0x20],'little'))
                        xopen(f'{o}/{n[:-4]}_big.x2m','wb').write(d[:0x20] + fd.read(int.from_bytes(d[0x18:0x1C],'little')))
                sf.close()

            if fd: fd.close()
            f.close()
            if listdir(o): return
        case 'Pseudo Interactive SmallF':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            off = f.readu32()
            fs = []
            while (f.pos+6) < off:
                fe = [f.read(f.readu8()).decode()]
                f.skip(1)
                fe.append(f.readu32())
                fs.append(fe)

            f.seek(off)
            for fe in fs: xopen(f'{o}/{fe[0]}','wb').write(f.read(fe[1]-f.pos))
            f.close()
            if fs: return
        case 'Novalogic Resource':
            KEYS = {b'\xAD\xDE\xED\xAC',b'\x2D\xDE\xED\xAC\xAD\xDE\xED\xAC\xAD\xDE\xED\xAC'}
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(12) == b'RESOURCE2xxx'
            c = f.readu32()

            fs = []
            for _ in range(c):
                rn = f.read(12)
                for k in KEYS:
                    try:
                        n = bytes(rn[x] ^ k[x%len(k)] for x in range(len(rn))).rstrip(b'\0').decode('ascii')
                        assert n and n.isprintable()
                    except:pass
                    else:break
                else: raise ValueError('File name with unknown key: ' + repr(rn) + ' ' + rn.hex())
                fs.append((n,f.readu32()+0x14,f.readu32())) 

            for fe in fs:
                f.seek(fe[1])
                xopen(f'{o}/{fe[0]}','wb').write(f.read(fe[2]))
            f.close()
            if fs: return
        case 'Specnaz UFF/BFS': raise NotImplementedError
        case 'Nicktoons Gravjet Racing LIN':
            if db.print_try: print('Trying with custom extractor')
            d = open(i,'rb').read()

            for fd in d.split(b'\xC0\xDE\0\1')[1:]:
                nl = int.from_bytes(fd[:4],'big')
                xopen(f'{o}/{fd[4+5:4+nl].decode().replace('://','/')}','wb').write(fd[4+nl:])

            if listdir(o): return
        case 'AmusementMakers Project B.G. Archive':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,BitReader
            f = File(i,endian='<')
            assert f.read(4) == b'PBG\x1A'
            f.skip(4)
            c = f.readu32()

            fs = []
            for _ in range(c):
                fs.append((f.readu32(),f.readu32()))
                f.skip(4)
            fs.sort(key=lambda x:x[1])
            fs.append((0,f.size))

            for ix,fe in enumerate(fs[:-1]):
                f.seek(fe[1])
                d = BitReader(f.read(fs[ix+1][1]-fe[1]))

                ob = bytearray()
                win = bytearray(8192)
                winp = 1
                while True:
                    flg = d.get_bit()
                    if flg is None: break
                    if flg:
                        b = d.get_bits(8)
                        ob.append(b)
                        win[winp] = b
                        winp = (winp + 1) & 0x1FFF
                    else:
                        of = d.get_bits(13)
                        if of == 0: break
                        l = d.get_bits(4) + 2
                        for x in range(l + 1):
                            b = win[(of + x) & 0x1FFF]
                            ob.append(b)
                            win[winp] = b
                            winp = (winp + 1) & 0x1FFF

                d = bytes(ob)[:fe[0]]
                open(f'{o}/{ix:02d}.{guess_ext(d)}','wb').write(d)

            f.close()
            if fs: return
        case 'Monolith Productions LTAR':
            from lib.file import File
            f = File(i)
            f._end = {b'LTAR':'<',b'RATL':'>'}[f.read(4)]

            v = f.readu32()
            f.skip(12)
            u1 = f.readu32()
            f.skip(8)
            u2 = sum(f.read(0x10))
            f.close()
            if v == 4 and u1 == 1 and not u2: s = 'shadow_of_mordor'
            elif v == 3 and u1 == 0 and u2: s = 'condemned2'
            elif v == 3 and u1 == 1 and u2: s = 'f.e.a.r.'
            else: raise NotImplementedError(f'Unknown LTAR Signature\nEndian: {f._end} Version: {v} u1: {u1} u2: {u2}')

            return quickbms(s)
        case 'Michigan: Report From Hell LF':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(2) == b'LF'
            c = f.readu16()

            bck = db.print_try
            db.print_try = False

            fs = [(f.readu32()*0x800,f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.read(fe[1])
                if d[:4] in (b'GMDF',b'GMOF',b'GCIF','NPVS',b'UV\0\0',b'SCR\0'): ext = d[:4].rstrip(b'\0').decode('ascii').lower()
                elif d == b'dummy': ext = 'dummy'
                elif not fe[1]%0x10 and (4+int.from_bytes(d[:4],'little')*8+(-(4+int.from_bytes(d[:4],'little')*8)%0x10)) == int.from_bytes(d[4:8],'little'): ext = 'bin.pck'
                elif d[0]+d[1] and not d[2] and d[3] == d[8] == 0x20 and not sum(d[4:8]) and d[9] == 2 and d[10] and d[11] and d[12] and d[13] and not d[14] and d[15].bit_count() == 1: ext = 'mdl'
                else: ext = guess_ext_ps2(d)
                fn = f'{o}/{ix:03d}.{ext}'
                xopen(fn,'wb').write(d)
                if ext == 'bin.pck': extract4_2(fn,fn[:-8] + '_ext','Michigan: Report From Hell BIN')

            db.print_try = bck
            f.close()
            if fs: return
        case 'Michigan: Report From Hell BIN':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu32()

            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.read(fe[1])
                if d[:4] in (b'GMDF',b'GMOF',b'GCIF','NPVS',b'UV\0\0',b'SCR\0'): ext = d[:4].rstrip(b'\0').decode('ascii').lower()
                elif d == b'dummy': ext = 'dummy'
                elif d[0]+d[1] and not d[2] and d[3] == d[8] == 0x20 and not sum(d[4:8]) and d[9] == 2 and d[10] and d[11] and d[12] and d[13] and not d[14] and d[15].bit_count() == 1: ext = 'mdl'
                else: ext = guess_ext_ps2(d)
                xopen(f'{o}/{ix:02d}.{ext}','wb').write(d)

            f.close()
            if fs: return
        case 'Metroid Prime 4 RFRM PACK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'RFRM'
            f.skip(0x10)
            assert f.read(4) == b'PACK' and f.readu32() == f.readu32() == 1 and f.read(4) == b'RFRM'
            f.skip(0x10)
            assert f.read(4) == b'TOCC' and f.readu32() == f.readu32() != 0 and f.read(4) == b'ADIR'
            f.skip(0x14)

            fc = f.readu32()
            fs = []
            for ix in range(fc):
                fe = [f'{o}/{ix}.' + f.read(4).decode('ascii').strip().lower() or 'bin']
                f.skip(0x18)
                fe.append(f.readu64())
                f.skip(8)
                fe.append(f.readu64())
                ec = f.readu64()
                if ec != 0: fe[0] += f'.enc{ec}'
                fs.append(fe)

            for fe in fs:
                f.seek(fe[1])
                open(fe[0],'wb').write(f.read(fe[2]))
            if fs: return
        case 'Metroid Prime 4 RFRM MSBT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'RFRM'
            f.skip(0x10)
            assert f.read(12) == b'MSBT\x10\0\0\0\x10\0\0\0'

            while f:
                n = f.read(4).decode('ascii')
                s = f.readu32()
                f.skip(0x10)
                d = f.read(s)
                open(o + f'/{n}.' + ('msbt' if d[:8] == b'MsgStdBn' else 'bin'),'wb').write(d)
            f.close()

            bv = db.print_try
            db.print_try = False
            for f in listdir(o):
                if f.endswith('.msbt'): extract(o + '\\' + f,o,'Nintendo MSBT')
            db.print_try = bv
            if listdir(o): return
        case 'Metroid Prime 4 RFRM ENUM':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'RFRM'
            f.skip(0x10)
            assert f.read(12) == b'ENUM\x0A\0\0\0\x0A\0\0\0'

            fc = f.readu32()
            of = open(o + '/' + tbasename(i) + '.txt','w')
            for ix in range(fc): of.write(f'{ix}: {f.read(4).hex().upper()}\n')
            of.close()
            if fc: return
        case 'Metroid Prime 4 Save': raise NotImplementedError()
        case 'Star Wars Early Learning DAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            off = f.readu32()
            f.seek(off)
            f.skip(8)
            tc = f.readu32()
            fs = []
            for _ in range(tc):
                n = o + '/' + f.read(4).decode('ascii')[::-1]
                mkdir(n)
                f.skip(4)
                c = f.readu32()
                for _ in range(c):
                    fs.append((f.readu32(),f.readu32(),n + '/' + f.read(f.readu8()).decode('ascii')))
                    f.skip(-(f.pos-off)%4)

            for fe in fs:
                f.seek(fe[0])
                xopen(fe[2],'wb').write(f.read(fe[1]))
            if fs: return

    return 1
