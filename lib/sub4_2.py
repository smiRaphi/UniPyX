from lib.main import *

def extract4_2(inp:str,out:str,t:str):
    run = db.run
    i = inp
    o = out

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

    return 1
