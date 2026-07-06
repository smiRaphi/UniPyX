from lib.main import *

OMTFS_XMP = {
    'mCTy':'mCTy',
    'WAVE':'wav',
    'SMK1':'smk',
    'SMK2':'smk',
    'SMAK':'smk',
    'SMKI':'smk',
    'Canv':'omc',
    'BLIT':'posh',
    'HCAn':'hca',
    '0HDR':'hdr',
    '0MFS':'omf',
}

def extract4_3(inp:str,out:str,t:str):
    run = db.run
    i = inp
    o = out

    match t:
        case 'Wangan Midnight TOC+DAT':
            db.try_custom()
            import zlib
            from lib.file import File
            f = File(i,endian='<')
            fd = open(noext(i) + '.dat','rb')
            asrt(f.read(4) == b'BLDh' and f.readu32() == 0)

            fc = bs = 0
            fs = []
            while f:
                n = f.read(4)
                ep = f.readu32() + f.pos

                if n == b'def ':
                    f.skip(4)
                    fc = f.readu32()
                    f.skip(8)
                    bs = f.readu64()
                elif n == b'inf ':
                    asrt(fc and bs)
                    for _ in range(fc):
                        fs.append([f.readu32()*bs,f.readu32(),f.readu32()])
                        f.skip(0x1C)
                elif n == b'tbl ':
                    asrt(fs)
                    for fe in fs: fe.append(f.read0s().decode('utf-8').lstrip('/'))

                f.seek(ep)
            f.close()

            for fe in fs:
                fd.seek(fe[0])
                d = fd.read(fe[1])
                if fe[2]:
                    asrt(d[:4] == b'GARC',d[:4])
                    asrt(d[8:12] == b'zlib',d[8:12])
                    d = File(d,endian=f._end)
                    d.skip(0x10)

                    while d:
                        n = d.read(4)
                        ep = d.readu32() + d.pos

                        if n == b'dat ':
                            ob = []
                            z = zlib.decompressobj()
                            while (d.pos+0x11) < ep: ob.append(z.decompress(d.read(d.readu64())))
                        d.seek(ep)
                    del d
                    asrt(ob,fe[0])
                    d = b''.join(ob)
                writefile(o + '/' + fe[3],d)
            if fs: return
        case 'Import Tuner Challenge TOC+DAT':
            db.try_custom()
            from lib.file import File,decompress
            from multiprocessing.pool import ThreadPool
            f = File(i,endian='>')
            fd = open(noext(i) + '.dat','rb')

            c = f.readu32()
            f.skip(12)

            offs = set()
            p = ThreadPool()
            def decc(ix,us,d,algo):
                ex = None
                if algo != 'none':
                    try: d = decompress(d,algo,db=db)
                    except EOFError: ex = 'ucl'
                    else: asrt(len(d) == us)

                if ex is None:
                    if len(d) > 0x80 and d[0x70:0x80] == b'mdl_Detail\0\0\0\0\0\0': ex = 'mdl'
                    elif len(d) >= 0x90 and d[0x70:0x90] == b'polySurfaceShape3\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' or d[0x80:0x90] == b'polySurfaceShape3\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0': ex = 'shp3'
                    elif d[:4] == b'XMB\0': ex = 'xmb'
                    elif d[:4] in {b'KBDS',b'DNBW'}: ex = d[:4].decode('ascii').lower()
                    elif b'Shape\0' in d[0x110:0x130]: ex = 'shp'
                    else: ex = guess_ext_xbox(d)
                writefile(f'{o}/{ix:04d}.{ex}',d)

            pcs = []
            for ix in range(c):
                of,zs,us = f.readu32(),f.readu32(),f.readu32()
                f.skip(4)
                if of in offs: continue
                offs.add(of)

                fd.seek(of*0x800)
                d = fd.read(zs)

                if d and zs == us: raise NotImplementedError(ix)
                elif not d: asrt(us == 0,ix)
                elif us != zs and d[:8] == b'\x00\xE9UCL\xFF\x01\x1A': pcs.append(p.apply_async(decc,(ix,us,d,'uclpack_itc')))
                else:
                    asrt(us in {0,zs},ix)
                    pcs.append(p.apply_async(decc,(ix,us,d,'none')))
            for pc in pcs: pc.get()
            p.close()
            p.join()

            f.close()
            fd.close()
            if c: return
        case 'CSI NY GRF':
            db.try_custom()
            from lib.file import File
            f = File(i)
            asrt(f.read(4) == b'GRF\x05')

            v = (b'\x01FRG',b'GRF\x01').index(f.read(4))
            if v == 0: f._end = '>'
            elif v == 1: f._end = '<'

            f.seek(f.readu32())
            ft = File(f.decompress(None,'zlib'),endian=f._end)
            fs = []
            if v == 0:
                ft.skip(6)
                c = ft.readu32()
                for _ in range(c):
                    ft.skip(13)
                    fs.append((ft.read(ft.readu32()).decode('utf-8'),ft.readu32(),ft.readu32(),ft.readu8()))
            elif v == 1:
                ft.skip(5)
                while ft:
                    ft.skip(10)
                    fs.append((ft.read(ft.readu8()).decode('utf-8'),ft.readu32(),ft.readu32(),ft.readu8()))
            del ft

            fs.sort(key=lambda x:x[1])
            fs.append((0,f.size))
            for ix,fe in enumerate(fs[:-1]):
                f.seek(fe[1])
                s = max(fs[ix+1][1]-fe[1],fe[2]) # don't trust file size fe[2]
                asrt(fe[3] == 1,f'{fe[3]}: {d[:8].hex()}')
                writefile(o + '/' + fe[0],f.decompress(s,'zlib'))

            f.close()
            if fs: return
        case 'Artech DAT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(8) == b'Artech\0\0' and f.readu16() == 2 and f.readu16() == 3 and f.readu64() == 1)

            c = f.readu32()
            f.skip(4)
            fs = []
            for _ in range(c):
                fe = [f.readu32(),f.readu32()]
                f.skip(4)
                fs.append(fe + [f.readu32()])

            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.decompress(fe[2] or fe[1],'zlib' if fe[2] and fe[2] != fe[1] else 'none')
                writefile(f'{o}/{ix:04d}.{guess_ext(d)}',d)

            f.close()
            if fs: return
        case 'Quantum3 DIR+WAD':
            db.try_custom()
            from lib.file import File
            f = File(noext(i) + '.dir',endian='<')
            fd = File(noext(i) + '.wad')

            c = f.readu32()
            fs = [(f.readc(0x20).rstrip(b'\0').decode('utf-8'),f.readc(0x20).rstrip(b'\0').decode('utf-8'),f.readu32(),f.readu32()) for _ in range(c)]
            f.close()

            asrt(fs and fs[0][3] == 0 and fs[0][2] != 0)
            if len(fs) > 1 and fs[0][2] == fs[1][3]: m = 1
            else: m = 0x800
            for fe in fs:
                fd.seek(fe[3] * m)
                writefile(o + '/' + fe[1] + '/' + fe[0],fd.readc(fe[2]))

            fd.close()
            if fs: return
        case 'Harry Potter and Prisoner of Azkaban IDS':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            fo = f.peek('u32')

            fs = []
            while f < fo:
                fe = (f.readu32(),f.readu32())
                if not fe[0]: break
                fs.append(fe)

            ob = []
            for fe in fs:
                f.seek(fe[0])
                ob.append(f'{fe[1]:03d}: {f.read0s().decode()}')
            f.close()
            if ob:
                writefile(f'{o}/{tbasename(i)}.txt','\n'.join(ob),'w')
                return
        case 'Harry Potter and Prisoner of Azkaban SDT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu32()

            fs = []
            for _ in range(c):
                fs.append(f.readu32())
                f.skip(4)
            fs.append(f.size)

            for ix,fe in enumerate(fs[:-1]):
                f.seek(fe)
                d = []
                tg = f.peek(4)
                while (f.pos+8) < fs[ix+1]:
                    s = f.peek('u32',poffset=4)
                    if not s: break
                    d.append(f.read(s))

                try: tg = tg.decode('ascii');asrt(tg.isprintable())
                except: ex = 'bin'
                else: ex = tg.lower()
                writefile(f'{o}/{ix:03d}.{ex}',b''.join(d))

            f.close()
            if fs: return
        case 'Red Baron VOL':
            if not extract(i,o,'GE:Red Baron VOL'): return
            BMSK = 0x7FFFFFFF
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'VOL ')
            ep = (f.readu32() & BMSK) + 8

            soff = 0
            fs = []
            while f < ep:
                n = f.read(4).decode('ascii')
                bep = (f.readu32() & BMSK) + f.pos
                match n:
                    case 'vols':
                        if f.readu32(): soff = f.pos
                    case 'voli':
                        while f < bep:
                            fo = f.readu32()
                            if fo != 0xFFFFFFFF: fs.append((fo,f.readu32()))
                            else: f.skip(4)
                            f.skip(6)
                f.seek(bep)

            for ix,fe in enumerate(fs):
                if soff:
                    f.seek(soff + fe[0])
                    fn = f.read0s().decode('ascii') + '.enc'
                else: fn = f'{ix:03d}.bin'
                f.seek(fe[1])
                asrt(f.read(4) == b'VBLK')
                writefile(o + '/' + fn,f.read(f.readu32() & BMSK))

            f.close()
            if fs: return
        case 'FlatOut BFS':
            td = TmpDir(path=o)
            run(['bfs2pack','x',i,'-q'],cwd=td.p)
            remove(td + '/memleaks.log',td + '/memory.log')
            copydir(td,o,True)
            td.destroy()
            if listdir(o): return
        case 'Package Resource Index XML':
            db.try_custom()
            from lib.crypto import decrypt
            import xml.etree.ElementTree as ET

            tr = ET.parse(i)
            for r in tr.getroot().find('ResourceMap').iter('NamedResource'):
                cdt = r.find('Candidate')
                if cdt.get('type') == 'EmbeddedData': writefile(o + '/' + r.get('uri').split('://',1)[1],decrypt(cdt.find('Base64Value').text,'b64'))
            del tr
            if listdir(o): return
        case 'Team Ari Encrypted RGSSAD'|'RPG Maker Archive':
            db.try_custom()
            from lib.pyob import PyOBinX
            keys = PyOBinX.dl('keys',db)
            from lib.file import File
            f = File(i,endian='<')
            sig = f.read(8)
            key = keys.wait()['rgssad'][sig]

            def rot(key): return (key * 7 + 3) & 0xFFFFFFFF
            def rotk():
                nonlocal key
                key = rot(key)
            def readu32():
                r = f.readu32() ^ key
                rotk()
                return r
            def read_name(n:int):
                ob = []
                for b in f.read(n):
                    ob.append(b ^ (key & 0xFF))
                    rotk()
                return bytes(ob)
            def read_data(n:int):
                tmpk = key
                ob = []
                for ix,b in enumerate(f.read(n)):
                    if ix != 0 and ix%4 == 0: tmpk = rot(tmpk)
                    ob.append(b ^ ((tmpk >> ((ix%4) * 8)) & 0xFF))
                return bytes(ob)

            while f:
                fn = read_name(readu32()).decode()
                writefile(o + '/' + fn,read_data(readu32()))

            f.close()
            if listdir(o): return
        case '3D Ultra Cool TBVolume':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(9) == b'TBVolume\0')

            f.skip(2)
            c = f.readu16()
            f.skip(4)
            writefile(o + '/$description.txt',f.read(0x18).rstrip(b'\0'))

            fs = []
            for _ in range(c):
                f.skip(4)
                fs.append(f.readu32())
            for of in fs:
                f.seek(of)
                fn = f.read(0x18).rstrip(b'\0').decode('ascii')
                writefile(o + '/' + fn,f.read(f.readu32()))

            f.close()
            if fs: return
        case '3D Ultra Cool PKX':
            db.try_custom()
            from lib.file import File,decompress
            f = File(i,endian='<')
            asrt(f.read(4) == b'PKX:')

            f.skip(8)
            ct = f.readu32()
            s = f.readu32()
            ds = f.readu32()

            if ct in {0x101,0x102}: d = decompress(f.read(s),{0x101:'lzo1x',0x102:'lzo1y'}[ct],usize=ds,db=db)
            else: raise NotImplementedError(hex(ct))
            f.close()

            writefile(o + '/' + basename(i),d)
            return
        case 'Disney\'s Tarzan FSD':
            db.try_custom()
            from lib.file import File
            from lib.crypto import HashLib
            HL = HashLib.dl('tarzan',db)
            f = File(i,endian='<')

            ep = f.size
            fs = []
            while f < ep:
                fe = (f.readu32(),f.readu32(),f.readu32())
                if not fe[0]: break
                fs.append(fe)
                ep = min(ep,fe[1])

            HL.wait()
            for fe in fs:
                f.seek(fe[1])
                d = f.read(fe[2])
                if fe[0] in HL: fn = HL[fe[0]].replace(':','')
                else:
                    if d.startswith(b'ESF'): ext = 'esf'
                    elif d.startswith(b'EGF'): ext = 'egf'
                    else: ext = 'bin'
                    fn = f'{fe[0]:08X}.{ext}'
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'Transformers: Devastation DAT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'DAT\0')
            c = f.readu32()

            oof = f.readu32()
            f.skip(4)
            nof = f.readu32()
            sof = f.readu32()

            fs = [[] for _ in range(c)]
            f.seek(oof)
            for fe in fs: fe.append(f.readu32())
            f.seek(sof)
            for fe in fs: fe.append(f.readu32())
            f.seek(nof)
            ns = f.readu32()
            for fe in fs: fe.append(f.read(ns).rstrip(b'\0').decode('ascii'))

            for fe in fs:
                f.seek(fe[0])
                writefile(o + '/' + fe[2],f.read(fe[1]))

            f.close()
            if fs: return
        case 'Transformers: Devastation BXM': raise NotImplementedError
        case 'Nexas New PAC':
            run(['garbro','-x',i],cwd=o)
            if listdir(o): return
        case 'Asura Engine Resource':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(8) == b'Asura   ')

            cs = {}
            while f:
                p = f.pos
                n = f.read(4).decode('latin1')
                if n == '\0\0\0\0': break
                ep = f.readu32() + p
                f.skip(8)

                match n:
                    case 'RSCF':
                        f.skip(8)
                        s = f.readu32()
                        fn = f.read(ep - f.pos - s).split(b'\0',1)[0].decode('ascii').strip(' \\/')
                        f.seek(ep - s)
                        writefile(o + '/' + fn,f.read(s))
                    case 'FONT':
                        u1 = f.readf32()
                        u2 = f.read(4).split(b'\0',1)
                        w = f.readf32()
                        h = f.readf32()
                        fnr = f.read(0x100).split(b'\0',1)

                        fn = o + f'/${n}/' + fnr[0].decode('ascii').strip(' \\/')
                        writefile(fn,f.read(ep - f.pos))
                        try: u2[1] = u2[1].rstrip(b'\0').decode('ascii')
                        except: u2[1] = u2[1].rstrip(b'\0').hex(' ').upper()
                        try: fnr[1] = fnr[1].rstrip(b'\0').decode('ascii')
                        except: fnr[1] = fnr[1].rstrip(b'\0').hex(' ').upper()
                        writefile(fn + '.txt',f'Unknown 1: {u1}\nUnknown 2: {u2[0].decode('ascii')}\nUnknown 2 Leftover: {u2[1]}\nWidth: {w}\nHeight: {h}\nFilename Leftover: {fnr[1]}\n','w')
                    case 'HANM':
                        f.back(8)
                        unk = f.readu32()
                        f.skip(4)
                        if unk == 5:
                            fn1 = f.read(0x80).split(b'\0',1)
                            fn2 = f.read(0x80).split(b'\0',1)
                            fn = o + f'/${n}/' + fn2[0].decode('ascii').strip(' \\/')
                            writefile(fn,f.read(ep - f.pos))
                            try: fn1[1] = fn1[1].rstrip(b'\0').decode('ascii')
                            except: fn1[1] = fn1[1].rstrip(b'\0').hex(' ').upper()
                            try: fn2[1] = fn2[1].rstrip(b'\0').decode('ascii')
                            except: fn2[1] = fn2[1].rstrip(b'\0').hex(' ').upper()
                            writefile(fn + '.txt',f'Name 1: {fn1[0].decode("ascii")}\nName 1 Leftover: {fn1[1]}\nName 2: {fn2[0].decode("ascii")}\nName 2 Leftover: {fn2[1]}\n','w')
                        elif unk == 6:
                            f.skip(4)
                            sp = f.readf32()
                            fn = o + f'/${n}/' + f.read0s().decode('ascii').strip(' \\/')
                            f.align(4,p)
                            writefile(fn,f.read(ep - f.pos))
                            writefile(fn + '.txt',f'Speed(?): {sp}\n','w')
                        else: raise NotImplementedError(f'Unknown: {n} {unk} @ 0x{p:X}')
                    case 'TEXT':
                        if not n in cs: cs[n] = 0

                        c = f.readu32()
                        of = xopen(o + f'/${n}/{cs[n]}.txt','w')
                        for _ in range(c):
                            of.write(f.read0s().decode('utf-8') + '\n')
                            f.align(4,p)
                        of.close()
                        cs[n] += 1
                    case 'TXFL'|'LITE'|'PHON'|'SHSN'|'NAV1'|'MLIN'|'SHAP'|'SMSG'|'CUTS'|'ENTI'|'npcc'|'HBPT'|'STPS'|'CTEV'|'FRAG'|'CTAT'|'PCLT':
                        if not n in cs: cs[n] = 0
                        writefile(o + f'/${n}/{cs[n]}.bin',f.read(ep - f.pos))
                        cs[n] += 1
                    case 'MSHV'|'NORM'|'MTXT'|'MSPF'|'EMOD'|'HMPT'|'CTTR':
                        f.skip(4)
                        fn = o + f'/${n}/' + f.read0s().decode('ascii').strip(' \\/')
                        f.align(4,p)
                        writefile(fn,f.read(ep - f.pos))
                    case 'MSHP'|'HSKN'|'CTAC':
                        f.skip(8)
                        fn = o + f'/${n}/' + f.read0s().decode('ascii').strip(' \\/')
                        f.align(4,p)
                        writefile(fn,f.read(ep - f.pos))
                    case 'SKYB':
                        if not n in cs: cs[n] = 0
                        xyz = (f.readf32(),f.readf32(),f.readf32())
                        f.skip(4)
                        skyfl = []
                        while f < (ep-4):
                            skyfl.append(f.read0s().decode('ascii'))
                            f.align(4,p)
                        writefile(f'{o}/${n}/{cs[n]}.txt',f'XYZ: {xyz[0]} {xyz[1]} {xyz[2]}\nUnknown: {f.readu32()}\nFile list:\n' + '\n'.join(skyfl),'w')
                        cs[n] += 1
                    case 'FNFO':
                        if not n in cs: cs[n] = 0
                        writefile(f'{o}/${n}/{cs[n]}.txt',f'File size: {f.readu32()}\n','w')
                        cs[n] += 1
                    case 'RSFL':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            sn = f.read0s().decode('ascii')
                            f.align(4,p)
                            ob.append(f'{sn}\n{f.readu32()}\n{f.readu32()}\n{f.readu32()}')
                        xopen(f'{o}/${n}/{cs[n]}.txt','\n\n'.join(ob),'w')
                        cs[n] += 1
                    case 'LTXT':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            ob.append(f.read(f.readu32()*2).rsplit(b'\0\0')[0].decode('utf-16le'))
                            f.align(4,p)
                        writefile(f'{o}/${n}/{cs[n]}.txt','\n\n'.join(ob),'w')
                        cs[n] += 1
                    case 'HTXT':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            ob.append(f.read(4)[::-1].hex().upper() + ': ' + f.read(f.readu32()*2).rsplit(b'\0\0')[0].decode('utf-16le'))
                            f.align(4,p)
                        writefile(f'{o}/${n}/{cs[n]}.txt','\n\n'.join(ob),'w')
                        cs[n] += 1
                    case 'TTXT':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            ob.append(f.read0s().decode('ascii'))
                            f.align(4,p)
                            ob[-1] += f': {f.readf32()} {f.readf32()} {f.readf32()} {f.readf32()} {f.readf32()}x{f.readf32()}'
                        writefile(f'{o}/${n}/{cs[n]}.txt','\n'.join(ob),'w')
                        cs[n] += 1
                    case _: raise NotImplementedError(f'Unknown: {n} @ 0x{p:X}')

                f.seek(ep)

            f.close()
            if listdir(o): return
        case 'GameMaker Archive':
            run(['undertalemodcli','load',i,'-s',dirname(db.get('undertalemodcli')) + '\\ExportAll.csx'],cwd=o,stdin='y')
            if listdir(o): return
        case 'Contact File Data':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'LF 2')

            f.skip(4)
            c = f.readu32()
            f.seek(f.readu32())
            fs = []
            for _ in range(c): fs.append((f.readu32() << 2,f.readu32()))
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.read(fe[1])
                if d[:0x40] == b'// -----------------------------------------\r\n// FileLinkNDS.H  ': fn = 'FileLinkNDS.H'
                else:
                    if d[:4] == b'SCR0': ext = 'scr'
                    else: ext = guess_ext_nds(d)
                    fn = f'{ix:04d}.{ext}'
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'Nemea File Archive':
            db.try_custom()
            from lib.pyob import PyOBinX
            KEY = PyOBinX.dl('keys',db)
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='<')
            asrt(f.read(4) == b'NFA0')

            f.skip(4)
            c = f.readu32()
            f.skip(4)
            fs = []
            key = list(KEY.wait()['nemea'])
            del key
            for _ in range(c):
                inf = decrypt(f.read(0x94),'dxor',*key)
                fs.append((int.from_bytes(inf[8:12],'little'),int.from_bytes(inf[12:16],'little'),inf[20:].rsplit(b'\0\0')[0].decode('utf-16le'))) # fe[2] = ,int.from_bytes(inf[16:20],'little')
            for fe in fs:
                f.seek(fe[1])
                #if fe[2]: print(decrypt(f.read(4),'xor',KEY).hex(),fe[0],fe[1],hex(fe[2]));raise
                writefile(o + '/' + fe[2],decrypt(f.read(fe[0]),'dxor',*key))

            f.close()
            if fs: return
        case 'D.N.A. Softwares Pack':
            db.try_custom()
            from lib.pyob import PyOBinX
            key = PyOBinX.dl('keys',db)
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'PACK')

            c = f.readu32()
            fs = []
            for _ in range(c):
                fn = f.read(0x40).rstrip(b'\0').decode('ascii')
                f.skip(8)
                fs.append((f.readu32(),f.readu32(),fn))
            key.wait()
            for fe in fs:
                f.seek(fe[0])
                d = f.read(fe[1])
                writefile(o + '/' + fe[2] + ('.lzss' if d[:4] == b'LZSS' else ''),d)
                if d[:4] == b'LZSS': writefile(o + '/' + fe[2],dnasoft_lzss_decrypt(d,key))

            f.close()
            if fs: return
        case 'D.N.A. Softwares LZSS':
            db.try_custom()
            from lib.pyob import PyOBinX
            key = PyOBinX.dl('keys',db)

            of = o + '/' + basename(i)
            if i.lower().endswith('.lzss'): of = of[:-5]
            key.wait()
            d = dnasoft_lzss_decrypt(readfile(i),key)
            writefile(of,d)
            return
        case '@N-Factory DAT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu32()

            fs = []
            for _ in range(c):
                fn = f.read(0x100).split(b'\0',1)[0].decode('ascii').replace('\\','/')
                while fn.startswith(('./','../')): fn = fn.split('/',1)[1]
                fs.append((f.readu32(),fn))
            for fe in fs: writefile(o + '/' + fe[1],f.read(fe[0]))

            f.close()
            if fs: return
        case 'UTG Software DDD':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'HTSW')

            c = f.readu32()
            asrt(f.readu64() == 0)
            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.readc(fe[1] - fe[0])
                writefile(o + '/' + f'{ix:02d}.{guess_ext(d)}',d)

            f.close()
            if fs: return
        case 'Braveheart BLB 2.0':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(8) == b'BLB2.0\0\0')

            f.skip(2)
            c = f.readu16()
            f.skip(0x12)
            nl = f.readu16()
            fs = []
            for _ in range(c):
                fs.append((f.read(nl).rstrip(b'\0').decode('ascii'),f.readu32()))
                f.skip(6)
            fs.sort(key=lambda x:x[1])
            fs.append((0,f.size))

            for ix in range(c):
                f.seek(fs[ix][1])
                writefile(o + '/' + fs[ix][0],f.readc(fs[ix+1][1] - fs[ix][1]))

            f.close()
            if fs: return
        case 'Looking Glass Resource':
            TMP = (
                "bin","string","image","font","anim","pall","shadtab","voc","shape","pict",
                "b2extern","b2reloc","b2code","b2header","b2resrvd","obj3d","stencil","movie",
                "rect",
                "palette512"
            )

            db.try_custom()
            from lib.file import File,decompress
            from multiprocessing.pool import ThreadPool
            f = File(i,endian='<')
            asrt(f.read(0x10) == b'LG Res File v2\r\n')

            cm = f.read(0x60).split(b'\x1A')[0]
            if cm: writefile(f'{o}/$comment.txt',cm)

            f.skip(12)
            f.seek(f.readu32())
            c = f.readu16()
            bo = f.readu32()
            fs = [(f.readu16(),f.readu24(),f.readu8(),f.readu24(),f.readu8()) for _ in range(c)]
            f.seek(bo)

            def dec(d,fn,fe):
                d = decompress(d,'lg_lzw' if fe[2] & 1 else ('implode' if fe[2] & 0x20 else 'none'))[:fe[1]]
                writefile(fn,d)
            def decc(d,ix1,ext,fsd,fe):
                d = decompress(d,'lg_lzw' if fe[2] & 1 else ('implode' if fe[2] & 0x20 else 'none'))[:fe[1]-fsd[0]]
                for ix in range(len(fsd)-1): writefile(f'{o}/{ix1}.{ext}/{ix:02d}.{ext}',d[fsd[ix] - fsd[0]:fsd[ix+1] - fsd[0]])
            p = ThreadPool()
            prcs = []

            for fe in fs:
                fn = f'{fe[0]:03d}'
                if fe[4] < len(TMP): ext = TMP[fe[4]]
                elif fe[4] == 0x30: ext = 'map'
                elif 0x40 > fe[4] >= 0x30: ext = f'app{fe[4]-0x2F:02d}'
                else: ext = f'{fe[4]:02d}'

                if fe[2] & 0x20: db.get('libblast')
                if fe[2] & 2:
                    cd = f.readu16()
                    fsd = [f.readu32() for _ in range(cd+1)]
                    f.skip(fsd[0] - (6 + cd*4))
                    prcs.append(p.apply_async(decc,(f.readc(fe[3]-fsd[0]),fn,ext,fsd,fe)))
                else: prcs.append(p.apply_async(dec,(f.readc(fe[3]),f'{o}/{fn}.{ext}',fe)))
                f.align(4)

            f.close()
            for prc in prcs: prc.get()
            p.close()
            p.join()
            if fs: return
        case 'Gwtar':
            db.try_custom()
            import re

            f = open(i,'rb')
            d = b''
            while not b'</script>' in d: d += f.read(0x1000)
            f.seek(len(d.split(b'</script>',1)[0]))
            d = f.read(0x100).decode('utf-8')
            asrt('let overhead' in d)

            f.seek(int(re.search(r'let +overhead *= *parseInt\("(\d+)"\)',d)[1]))
            tf = TmpFile('.tar',path=o)
            writefile(tf.p,f.read())
            f.close()

            r = extract(tf.p,o,'TAR')
            tf.destroy()
            return r
        case 'PlayStation V2 Trophy File':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            asrt(f.read(4) == b'\xB2\x28\xC6\x0A' and f.readu32() == 1)

            f.skip(8)
            c = f.readu32()
            f.seek(f.readu32() + 0x20)
            fs = []
            for _ in range(c):
                fs.append((f.read(0x20).rstrip(b'\0').decode('utf-8'),f.readu64(),f.readu64()))
                f.skip(0x10)

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'REDengine Archive':
            run(['wolvenkit.cli','extract',i,'-o',o,'-v','Quiet'])
            if listdir(o): return
        case 'REDengine W2ResourCe':
            run(['wolvenkit.cli','convert','s',i,'-o',o,'-v','Quiet'])
            if listdir(o): return
        case 'idTech 7 Resource':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'IDCL')

            v = f.readu32()
            unk = sum(f.read(4))
            f.skip(0x14)
            if v == 13 and unk: f.skip(4)
            c = f.readu32()
            f.skip(4)
            dc = f.readu32()
            f.skip(0x14)
            no = f.readu64()
            f.skip(8)
            to = f.readu64()
            f.skip(8)
            nio = f.readu64() + dc * 4

            f.seek(no)
            nc = f.readu64()
            ns = [f.readu64() for _ in range(nc)]
            p = f.pos
            for ix in range(nc):
                f.seek(p+ns[ix])
                ns[ix] = f.read0s()

            f.seek(to)
            fs = []
            for _ in range(c):
                f.skip(0x20)
                fe = [f.readu64() + 1]
                f.skip(0x10)
                fe.extend([f.readu64(),f.readu64(),f.readu64()])
                f.skip(0x20)
                fe.append(f.readu8())
                f.skip(7)
                if fe[4] == 4:
                    fe[1] += 12
                    fe[2] -= 12
                f.skip(0x18)
                fs.append(fe)

            for fe in fs:
                f.seek(nio + fe[0]*8)
                fn = ns[f.readu64()].decode('utf-8').replace('\\','/').split('/')
                fn = o + '/' + sub_path(('/'.join((fn[ix] + '_dir') if exists(o + '/' + '/'.join(fn[:ix+1])) and isfile(o + '/' + '/'.join(fn[:ix+1])) else fn[ix] for ix in range(len(fn)-1)) + '/' + fn[-1]).lstrip('/').replace(':','/'))
                if exists(fn) and isdir(fn): move(fn,fn + '_dir')
                if fe[3] == 0: d = b''
                else:
                    f.seek(fe[1])
                    d = f.decompress(fe[2],('none','zlib','oodle_kraken',0,'oodle_kraken','oodle_leviathan'),usize=fe[3],db=db)
                writefile(fn,d)

            f.close()
            if fs: return
        case 'PlayStation BLS Update':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'SLB2')

            f.skip(8)
            c = f.readu32()
            cs = f.size // f.readu64()
            f.skip(8)
            fs = []
            for _ in range(c):
                fe = [f.readu32() * cs,f.readu32()]
                f.skip(8)
                fs.append(fe + [f.read(0x20).rstrip(b'\0').decode('utf-8')])
            for fe in fs:
                f.seek(fe[0])
                writefile(o + '/' + fe[2],f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Purple Moon Resource PRD+PRS':
            db.try_custom()
            from lib.file import File
            f = File(noext(i) +  '.prd',endian='<')
            fd = File(noext(i) +  '.prs',endian='<')
            f.seek(0xA8)

            while f:
                f.skip(8)
                of = f.readu32()
                if of == 0xFFFFFFFF:
                    f.skip(12)
                    continue
                fd.seek(of - 0x1C)
                f.skip(8)
                e = fd.read(4).rstrip(b'\0').decode('ascii')
                gid = fd.readu16()
                fn = f'{o}/{gid}{fd.read(0x12).rstrip(b"\0").decode("ascii")}.{e}'
                fd.skip(4)
                writefile(fn,fd.readc(f.readu32()))

            f.close()
            fd.close()
            if listdir(o): return
        case 'Sonic PAC':
            run(['hedgearcpack',i,o,'-E'])
            if listdir(o): return
        case 'Sonic BINA':
            db.try_custom()
            from lib.file import File
            f = File(i)

            if f.read(4) == b'BINA':
                f.skip(3)
                f._end = {b'L':'<',b'B':'>'}[f.read(1)]
                f.skip(8)
                asrt(f.read(4) == b'DATA')
                f.skip(4)
                de = f.readu32()
                to = de + f.readu32()
                te = f.readu32()
                f.skip(f.readu16() + 2)
                do = f.pos
                de += do
                to += do
                te += to
            else:
                f._end = '>'
                to = f.readu32()
                te = f.readu32()
                f.skip(8)
                asrt(f.read(8) == b'\x00\x001BBINA')
                f.skip(4)
                do = f.pos
                to += do
                de = to
                te += to

            f.seek(to)
            fs = []
            while f < te:
                b1 = f.readu8()
                fl,r = b1 >> 6,b1 & 0x3F
                if not fl: break
                if fl > 1:
                    r = f.readu8() + (r >> 8)
                    if fl > 2: r = f.readu16('>') + (r >> 16)
                fs.append((r << 2) + do)
            fs.append(de)
            fs = sorted(list(set(fs)))
            for ix in range(len(fs)-1):
                f.seek(fs[ix])
                writefile(f'{o}/{ix:02d}.bin',f.readc(fs[ix+1] - fs[ix]))

            f.close()
            return
        case 'Blitz Games PAK':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            f.skip(4)
            m = f.readu32()

            f.skip(4)
            c = f.readu32()
            to = f.readu32()*m
            tgo = f.readu32()*m
            f.skip(0x10)
            so = f.readu32()*m
            f.seek(to)

            fs = []
            for _ in range(c):
                fe = [f.readu32()*m]
                f.skip(4)
                fe.extend([f.readu32(),f.readu32() + so])
                htg = f.readu32()
                asrt(htg in {0,1},f.pos)
                if htg: fe.append(f.readu32() + tgo)
                else:
                    f.skip(4)
                    fe.append(None)
                f.skip(8)
                fs.append(fe)

            for fe in fs:
                if fe[3]:
                    f.seek(fe[3])
                    ex = '.' + f.read(4).decode('ascii')
                else: ex = ''
                f.seek(fe[2])
                fn = f.read0s().decode('utf-8') + ex
                f.seek(fe[0])
                writefile(o + '/' + (fn or 'StringTable.pak.sys'),f.readc(fe[1]))

            f.close()
            if fs: return
        case '-8 SysFile':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            f.skip(0x14)
            s1 = f.readu32()
            s2 = f.readu32()
            f.skip(8)
            writefile(o + '/0.png',f.readc(s1))
            writefile(o + '/1.png',f.readc(s2))

            f.close()
            return
        case 'Archer Maclean\'s Mercury PAQ':
            db.try_custom()
            from lib.file import File
            from lib.crypto import HashLib
            HL = HashLib.dl('archer_mac_mercury',db)
            f = File(i,endian='<')
            asrt(f.readu32() in {0x7D1,0xFEED})

            c = f.readu32()
            f.skip(8)
            fs = []
            for _ in range(c):
                fs.append((f.readu32(),f.readu32(),f.readu32()))
                asrt(f.readu32() == fs[-1][1],f.pos - 0x10)

            HL.wait()
            for fe in fs:
                f.seek(fe[2])
                d = f.readc(fe[1])
                if fe[0] in HL: fn = HL[fe[0]]
                else:
                    if d[:4] in {b'DEAD',b'COL0'}: ex = d[:4].decode('ascii')
                    elif b'MIG.00.1PSP\0' in d[0x20:0x50]: ex = 'pst'
                    elif d[:8] == b'********': ex = 'lvl.txt'
                    elif d[:13] == b'\r\nNEW_SURFACE': ex = 'srf.txt'
                    elif d[:9] == b'[Control]': ex = 'ctl.txt'
                    elif d[:10] == b'Obj Name: ': ex = 'obj.txt'
                    elif d[:10] == b'Thumbnail=': ex = 'tmb.txt'
                    elif d[:4] == b'\xED\xFE\0\0': ex = 'paq'
                    else: ex = guess_ext(d)
                    fn = f'{fe[0]:08X}.{ex}'
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'THQ PAK':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'kcap' and f.readu32() == 1)

            f.skip(8)
            so = f.readu32()
            c = f.readu32()
            fs = []
            for _ in range(c): fs.append((f.readu32() + so,f.readu32(),f.readu32()))
            for fe in fs:
                f.seek(fe[0])
                fn = f.read0s().decode('ascii')
                f.seek(fe[1])
                writefile(o + '/' + fn,f.readc(fe[2]))

            f.close()
            if fs: return
        case 'TotemTech Data':
            import glob
            run(['bff','extract','-e','binary',i,o])
            if exists(o + '/manifest.json') and exists(o + '/resources') and listdir(o + '/resources'):
                js = json.load(open(o + '/manifest.json',encoding='utf-8'))
                remove(o + '/manifest.json')
                td = TmpDir(mdir=False,path=o)
                mv(o + '/resources',td.p)

                writefile(o + '/$signature.txt',js['version'],'w')
                for x in js['blocks']:
                    asrt(len(x) == 1 and 'resources' in x)
                    for fn in x['resources']:
                        asrt(len(fn) == 1 and 'name' in fn)
                        fn = fn['name']
                        rfn = glob.glob(glob.escape(td.p + '/' + fn.replace(':','_').replace('>','_')) + '.*')
                        asrt(len(rfn) == 1)
                        mv(rfn[0],o + '/' + fn.replace(':','').replace('>','/'))

                td.destroy()
                return
        case 'L.A. Noire BIG':
            db.try_custom()
            from lib.file import File
            f = File(i)

            f.seek(-4)
            f.seek(-f.readu32('<'))
            f.skip(4)
            c = f.readu32('<')
            fs = []
            for _ in range(c):
                fe = [f.readu32('>'),f.readu32('>') << 4,f.readu32('>')]
                f.skip(4)
                fe.append(f.readu32('>'))
                fs.append(fe)

            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[3] or fe[2])
                if d[:4] in {b'segs',}: ex = d[:4].decode('ascii')
                else: ex = guess_ext(d)
                writefile(f'{o}/{fe[0]:08X}.{ex}',d)

            f.close()
            if fs: return
        case 'Nintendo ASH0':
            db.try_custom()
            from lib.file import decompress
            d = decompress(readfile(i),'ash0')
            writefile(o + '/' + tbasename(i),d)
            return
        case 'Super Mario Maker Level':
            db.try_custom()
            from lib.file import decompress
            d = readfile(i).split(b'ASH0')[1:]
            asrt(len(d) == 4)
            for ix,n in enumerate(('thumbnail0.tnl','course_data.cdt','course_data_sub.cdt','thumbnail1.tnl')):
                dd = decompress(b'ASH0' + d[ix],'ash0')
                writefile(o + '/' + n,dd)
            return
        case 'SDFTool SDF.bin':
            db.try_custom()
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='>')
            asrt(f.read(4) == b'SDF0')

            f.skip(4)
            c1 = f.readu32()
            asrt(f.reads8() < 0)
            c2 = f.readu24()
            f.skip(2 + 3 + 3 + 8)

            of = xopen(o + '/1.txt','w')
            of.write(f'{c1}\n\n')
            for ix in range(c1): of.write(f'{f.readu16()} {f.readu24()} {f.readu24()}\n{f.readc(0x28).hex()}\n\n')
            of.close()

            of = xopen(o + '/2.txt','w')
            of.write(f'{c2}\n\n')
            for ix in range(c2): of.write(f'{f.readc(0x10).hex()}\n')
            of.close()

            asrt(f.readu8() == 1 and f.readu16() == 0)
            writefile(o + '/hash.bin',f.readc(f.readu8() * 4))
            asrt(f.readu8() == 1 and f.readu16() == 0)
            d = f.readc(f.readu8() * 4)
            d = decrypt(d,'rsa_inv_le',0xd0c57d605d21c23b91000de888121741c3e2b8ba476b81b25123275b6b5c008b6b10abb59d357dd2fed5fea988940b94adc2136bb45c93d992b7102a5988033b73f6386ef9cce6bbc6dab03ba6e90a25976ef305a087302660475011c5ee50b8d44e1cc081d61273913664e1810abb97b93c1a6c0e6ebd8862d92ed88e62a450cd050dd4e212285128b453ef48711b0be4a0fc43bb8403efd57eda741644ee4cf64bc85187e0ee22fd3c61e4670eb19d47c99a3c9827219f0d4f6743f9fa27375deedf30dd2c17b5a6cd05339c399f2986e9c8919038a70c4f5fc2a760763e128818d1bb1c79a8d8a05d4401ac3004e5f64913a43c8cad637e94d478b63a27d2760105fdeadc8ff71914aaa9b9da29f35d294d4c23638f7f6170ba5358bc127f72c78b6bc4ce746cd350647c61f32dbdfc6135c1db2ec7c2ab9d914ed9a79b46c1ee57692b5fda14c1f0c0597a3c39414d7b8c519144c93dc72ab08b1c7a7b8e651cefcb1b3291128b4136d05abfe33af3568a163c7a839be864bc5abf3ac735fa33bb1ca45953f8431ed9fff2df07f0fbb5a071a462340463fcdfe79f9dee85e297115e1e5d077c414b2bf8523802fc7fd32a40e77cf8be6e0a115aa2709ba2c1fe04fadae81db12d0c71d5020c10f6a62f5e35f4a3d8ec0d3bf3dd914482cc39fd4e221e2feb39e23e0ef408954ef638b2d75e210ba0b6a473d526fc17588b,
                                       3,r=2)
            asrt(d[:1] == b'\1')
            d = d[1:].split(b'\0',1)[1][::-1]
            writefile(o + '/signature.bin',d)

            f.close()
            return
        case 'Marmalade Derbh DZIP':
            tf = TmpFile('.dz',path=o)
            tf.link(i)
            run(['derbh_dzip','-q','-d',tf])
            tf.destroy()
            if exists(tf.p[:-3]) and listdir(tf.p[:-3]):
                copydir(tf.p[:-3],o,True)
                return
        case 'Marmalade Resource Group':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu8() == 0x3D and f.readu8() == 3)

            v = f.readu16('>')
            if v > 0x0101: f.skip(2)
            while f:
                h = f.readu32()
                if not h: break
                d = f.readc(f.readu32() - 4)
                writefile(f'{o}/{h:08X}.{guess_ext(d)}',d)

            f.close()
            if listdir(o): return
        case '7th Level BIN'|'Access Software AP'|'Bureau 13 GL'|'Braid Dead 13 DAT'|'Beam Software GOB'|'Conquest Earth WAD'|'Cryo BigFile'|\
             'Escal Compressed'|'Gabriel Knight 3 Barn'|'Goosebumps CFS'|'Hell: A Cyberpunk Thriller Library'|\
             'SouthPeak Interactive Puzzle Archive'|'Hostile Waters MNG'|'Tsunami Media RLB'|'Coktel Vision STK'|'Coktel Vision STK2':
            MP = {
                '7th Level BIN':'7lev_bin','Access Software AP':'access_ap','Bureau 13 GL':'b13_gl','Braid Dead 13 DAT':'bd13_dat','Beam Software GOB':'beam_gob',
                'Conquest Earth WAD':'ce_wad','Cryo BigFile':'cryo_archive','Escal Compressed':'escal-z','Gabriel Knight 3 Barn':'gk3_barn','Goosebumps CFS':'goosebumps',
                'Hell: A Cyberpunk Thriller Library':'hell-lib','SouthPeak Interactive Puzzle Archive':'mco','Hostile Waters MNG':'mng','Tsunami Media RLB':'rlb',
                'Coktel Vision STK':'stk','Coktel Vision STK2':'stk2',
            }
            if t in MP: ty = MP[t]
            else: raise NotImplementedError('Type not mapped:',t)

            run(['na_game_tool','-extract','-ifmt',ty,i,o])
            if listdir(o): return
        case 'Bethesda BSA':
            for enc in ('utf7','utf8','utf32','unicode'):
                run(['bsab','-e','-o','--noheaders','--encoding',enc,i,o])
                if listdir(o): return
        case 'RE Engine PAK':
            lp = dirname(db.get('ree.unpacker')) + '/Projects'
            if len(listdir(lp)) != 1:
                remove(lp + '/all.list')
                lst = list(set(sum([readfile(lp + '/' + x,'r').split('\n') for x in listdir(lp)],[])))
                remove(*[lp + '/' + x for x in listdir(lp)])
                writefile(lp + '/all.list','\n'.join(lst),'w')

            run(['ree.unpacker','all',i,o],cwd=dirname(lp))
            if listdir(o): return
        case 'Capcom Encrypted MAME ROM':
            db.try_custom()
            from lib.pyob import PyOBinX
            key = PyOBinX.dl('keys',db)
            from lib.file import decompress
            from lib.crypto import decrypt

            if '_d.' in basename(i).lower(): iv = key['capcom_mame']['div'] + basename(i).replace('_d.','_D.')
            else: iv = key['capcom_mame']['iv'] + basename(i)

            if decompress(
                decompress(
                    decrypt(readfile(i),'capcom_mame',key['capcom_mame']['k'],iv),
                    'lz4',no_size=True),
                'zip',o=o
            ): return
        case 'Smoking Car Productions Disk Cache':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            fs = []
            for _ in range(c):
                fs.append((f.read(12).rstrip(b'\0').decode('ascii'),f.readu32()*0x800,f.readu32()*0x800))
                asrt(f.readu16() in {0,1})
            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Kamen Rider Atsume BIN':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')

            f.skip(4)
            c = f.readu16()
            bo = 6 + c*8
            fs = []
            for _ in range(c): fs.append((f.readu32()+bo,f.readu32()))
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.readc(fe[1])
                writefile(f'{o}/{ix:02d}.{guess_ext(d)}',d)

            f.close()
            if fs: return
        case 'Trinity OnePack':
            db.try_custom()
            asrt(exists(noext(i) + '.trpfs'))
            db.get('trpfs.fbs')
            from lib.file import File
            from lib.crypto import HashLib
            HL = HashLib.dl('pokemon',db)

            fd = File(noext(i) + '.trpfs',endian='<')
            asrt(fd.read(8) == b'ONEPACK\0')

            bo = fd.readu64()
            fd.seek(bo)
            fbuf = fd.read()

            from bin.PokeDocs.trpfs import TRPFS # type: ignore
            tfs = TRPFS.GetRootAs(fbuf)
            asrt(tfs.FileOffsetsLength() == tfs.FileHashesLength())
            fs = [(tfs.FileOffsets(ix),tfs.FileHashes(ix)) for ix in range(tfs.FileOffsetsLength())]
            del tfs
            fs.append((bo,0))

            HL.wait()
            if exists(noext(i) + '.trpfd'):
                db.get('trpfd.fbs')
                from bin.PokeDocs.trpfd import TRPFD # type: ignore
                tfd = TRPFD.GetRootAs(readfile(noext(i) + '.trpfd'))
                HL.add([tfd.PackStrings(ix).decode('utf-8') for ix in range(tfd.PackStringsLength())])
                del tfd
                HL.save()

            for ix,fe in enumerate(fs[:-1]):
                fd.seek(fe[0])
                writefile(o + '/' + HL.get(fe[1],f'$unk/{h:016X}.bin'),fd.readc(fs[ix + 1][0] - fe[0]))

            fd.close()
            if fs: return
        case 'Trinity PAK':
            db.try_custom()
            db.get('trpak.fbs')
            from lib.file import decompress
            from lib.crypto import HashLib
            HL = HashLib.dl('pokemon',db)

            from bin.PokeDocs.trpak import TRPAK # type: ignore
            tpk = TRPAK.GetRootAs(readfile(i))
            asrt(tpk.FileEntryLength() == tpk.FileHashesLength())

            HL.wait()
            for ix in range(tpk.FileEntryLength()):
                fl = tpk.FileEntry(ix)
                h = tpk.FileHashes(ix)
                fn = HL.get(h,f'$unk/{h:016X}.bin')
                d = bytes(fl.ByteBuffer(dix) for dix in range(fl.ByteBufferLength()))
                writefile(o + '/' + fn,decompress(d,(0,'zlib','lz4','oodle','none')[fl.CompressType()],usize=fl.FileSize(),db=db))

            del tpk
            if listdir(o): return
        case 'Trinity GFLXPack':
            db.try_custom()
            from lib.file import File
            from lib.crypto import HashLib
            HL = HashLib.dl('pokemon',db)

            f = File(i,endian='<')
            asrt(f.read(8) == b'GFLXPACK')

            f.skip(8)
            fc,dc = f.readu32(),f.readu32()
            fo = f.readu64()
            fho = f.readu64()
            dos = [f.readu64() for _ in range(dc)]

            f.seek(fho)
            hs = [f.readu64() for _ in range(fc)]
            f.seek(fo)
            fes = []
            for _ in range(fc):
                f.skip(2)
                fe = [f.readu16(),f.readu32(),f.readu32()]
                f.skip(4)
                fe.append(f.readu64())
                fes.append(fe)

            fs = []
            for do in dos:
                f.seek(do)
                dh = f.readu64()
                dc = f.readu32()
                f.skip(4)

                for _ in range(dc):
                    eh = f.readu64()
                    cix = f.readu32()
                    f.skip(4)
                    fs.append(fes[cix] + [cix,dh,eh,hs[cix]])

            HL.wait()
            ch = {}
            for fe in fs:
                if fe[5] in HL and fe[6] in HL: fn = HL[fe[5]] + HL[fe[6]]
                elif fe[7] in HL: fn = HL[fe[7]]
                else: fn = HL.get(fe[5],f'$unk/{fe[5]:016X}/') + HL.get(fe[6],f'{fe[6]:016X}.bin')

                if fe[4] in ch: cp(o + '/' + ch[fe[4]],o + '/' + fn)
                else:
                    f.seek(fe[3])
                    d = f.decompress(fe[2],('none','zlib','lz4','oodle')[fe[0]],usize=fe[1],db=db)
                    writefile(o + '/' + fn,d)
                    ch[fe[4]] = fn

            f.close()
            if fs: return
        case 'Open Media Toolkit Formatted Stream':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            v = {b'0MFS':1,b'0MF2':2,b'0MF3':3}[f.read(4)]
            asrt(v in {1,2,3})

            f.seek(f.readu32())
            dc = f.readu32()
            fs = []
            mcs = []
            for _ in range(dc):
                n = f.readc(4).decode('ascii')
                asrt(n.isprintable())
                c = f.readu32()
                for _ in range(c):
                    fe = [n,f.reads32(),f.readu32(),f.readu32()]
                    if v >= 2:
                        fe.append(f.reads(f.readu8(),'ascii'))
                        if v >= 3: fe.append(f.readu16())
                        else: fe.append(0)
                        fs.append(fe)
                    elif v == 0:
                        fs.append(fe)
                        if n == 'mCTy': mcs.append(fs[-1][2])
            xc = f.readu32()
            xfs = [(f.readu32(),f.readu32()) for _ in range(xc)]

            if v == 0:
                nm = {}
                for m in mcs:
                    f.seek(m)
                    dc = f.readu32()
                    for _ in range(dc):
                        n = f.readc(4).decode('ascii')
                        asrt(n.isprintable())
                        if not n in nm: nm[n] = {}
                        f.padc(2)
                        c = f.readu32()
                        for _ in range(c):
                            id = f.reads32()
                            nm[n][id] = f.readc(f.readu8()).decode('ascii')

            for fe in fs:
                f.seek(fe[2])
                if v == 1:
                    if fe[0] == '0HDR':
                        try:
                            fn = fe[1].to_bytes(4,'big',signed=True).decode('ascii')
                            asrt(fn.isprintable())
                        except: fn = str(fe[1])
                    elif fe[0] in nm and fe[1] in nm[fe[0]]: fn = fe[0] + '/' + nm[fe[0]][fe[1]]
                    else: fn = f'${fe[0]}/{fe[1]}'
                    d = f.readc(fe[3])
                else:
                    if fe[5]: us = f.readu32()
                    else: us = None
                    d = f.decompress(fe[3] - (4 if fe[5] else 0),{0:'none',6:'zlib'}[fe[5]],usize=us)

                    if fe[0] == '0HDR':
                        try:
                            fn = fe[1].to_bytes(4,'big',signed=True).decode('ascii')
                            asrt(fn.isprintable())
                        except: fn = str(fe[1])
                    else: fn = fe[0] + '/' + (fe[4] or str(fe[1]))
                fn += '.' + OMTFS_XMP.get(fe[0],fe[0])

                writefile(o + '/' + fn,d)
            for ix,fe in enumerate(xfs):
                f.seek(fe[0])
                writefile(f'{o}/$unk/{ix:02d}.bin',f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Barbie: Riding Club Cache':
            db.try_custom()
            from lib.file import File
            f = File(i)

            bn = tbasename(i)
            while f:
                s = int(f.readc(12).rstrip())
                if bn: fn,bn = bn,None
                else:
                    fn = f.readc(34).rstrip().decode('ascii')
                    x = f.readc(6).rstrip().decode('ascii')
                    asrt(fn.isprintable() and x.isprintable())
                    fn = f'{x}/{fn}.{OMTFS_XMP.get(x,x)}'
                writefile(o + '/' + fn,f.readc(s))

            f.close()
            if not bn: return
        case 'PlayStation Encrypted SFM':
            db.try_custom()
            from Cryptodome.Cipher import AES
            from lib.file import File
            from lib.crypto import decrypt

            dn = dirname(i)
            for _ in range(3):
                if exists(dn + '/npbind.dat'):
                    np = dn + '/npbind.dat'
                    break
                dn = dirname(dn)
            else:
                print('npbind.dat not found')
                return 1

            f = File(np,endian='>')
            asrt(f.read(4) == b'\xD2\x94\xA0\x18' and f.readu32() == 1)
            f.skip(8)
            es,ec = f.readu64(),f.readu64()
            f.skip(0x60)
            nps = []
            for _ in range(ec):
                ep = f.pos + es
                while f < ep:
                    ty = f.readu16()
                    if ty == 0x10:
                        nps.append(f.readc(f.readu16())[:0x10].ljust(0x10,b'\0'))
                        break
                    else: f.skip(f.readu16())
                f.seek(ep)
            f.close()

            d = open(i,'rb').read()
            div,d = d[:0x10],d[0x10:]

            for n in nps:
                for k in (b'!\xf4\x1ak\xad\x8a\x1d>\xcaz\xd5\x86\xc1\x01\xb7\xa9',
                          b'\x02\xcc\xd3F\xb4Y\xcb\x83P^\x8ev\nD\xd4W'):
                    derk = AES.new(k,AES.MODE_CBC,iv=b'\0'*16).encrypt(n)
                    dc = decrypt(d,'aes_cbc',derk,div)
                    if dc[-1] > 16: continue
                    dc = dc[:-dc[-1]]
                    try: asrt(dc.decode('utf-8').replace('\n','').replace('\r','').isprintable())
                    except: pass
                    else:
                        writefile(f'{o}/{tbasename(i)}.{extname(i)[2:]}',dc)
                        return
        case 'Starsky & Hutch WAD':
            db.try_custom()
            from lib.file import File,mask
            f = File(i,endian='<')
            f.padc(8)
            asrt(f.read(4) == b'WAD!' and f.readu32() == 4)

            f.skip(8)
            writefile(o + '/$description.txt',f.readc(0x80).rstrip(b'\0'))
            f.skip(8)
            fnc = f.readu32()
            fno = f.readu32()
            f.padc(4)
            fdic = f.readu32()
            fdio = f.readu32()
            pnc = f.readu32()
            pno = f.readu32()
            nmdlt,fddlt = f.readu16(),f.readu16()
            xno = f.readu32()
            xnc = f.readu32()
            pnno = f.readu32()
            pnnc = f.readu32()
            sto = f.readu32()
            f.skip(4)

            f.seek(xno)
            xs = [f.readc(4).rstrip(b'\0').decode('ascii') for _ in range(xnc)]

            f.seek(pno)
            pkns1 = [f.readu32() for _ in range(pnc)]
            pkns1 = [(pkn & mask(7),(pkn >> 7) & mask(8),pkn >> 15) for pkn in pkns1]
            f.seek(pnno)
            pkns2 = [f.readu32() for _ in range(pnnc)]
            pkns2 = [(pkn & mask(7),(pkn >> 7) & mask(8),pkn >> 15) for pkn in pkns2]

            pns = []
            for dix,pn in enumerate(pkns1):
                xi,nl,no = pn

                asrt(xi != 0x7E)
                if 0x77 <= xi <= 0x7D:
                    bxi,bnl,bno = pkns2[nl]
                    f.seek(sto + bno)
                    n = f.readc(bnl).decode('ascii')
                    if not n.isprintable() or (xi > 0x78 and '#' not in n): raise Exception(f'{n.encode("ascii")} ({bnl} @ {sto+bno}) @ {pnno+nl*4} ({dix} @ {pno+dix*4})')
                    if '#' in n: n = n.replace('#',f'{no:0{0x7E - xi}d}')
                    elif xi == 0x77: n += f'-{no}'
                    elif xi == 0x78: n += f'_{no}'
                    if bxi != 0x7F: n += '.' + xs[bxi]
                else:
                    f.seek(sto + no)
                    n = f.readc(nl).decode('ascii')
                    asrt(n.isprintable())
                    if xi != 0x7F: n += '.' + xs[xi]
                pns.append(n)

            f.seek(fdio)
            fds = [(f.readu32(),f.readu32()) for _ in range(fdic)]
            fds = [(0,0) if x[1] == 0xFFFFFFFF else x for x in fds]
            f.seek(fno)
            fis = [(f.readu16(),f.readu16(),f.readu16(),f.readu16()) for _ in range(fnc)]
            for fi in fis:
                dc,do,fc,fo = fi
                p = '/'.join(pns[do-nmdlt:do+dc-nmdlt])
                for ix in range(fc):
                    try:
                        fe = fds[fo+ix-fddlt]
                        asrt((fe[0]+fe[1]) < f.size)
                        f.seek(fe[1])
                    except:
                        print(f'{fo+ix-fddlt} ({fo}+{ix}-{fddlt}) / {len(fds)} @ {f.pos - 8}')
                        raise
                    writefile(f'{o}/{p}/{pns[fo+ix-nmdlt]}',f.readc(fe[0]))

            f.close()
            if fds: return
        case 'Torque HHA':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(8) == b'\x4F\xF3\x2F\xAC\0\0\1\0')

            ss = f.readu32()
            c = f.readu32()
            f.skip(ss)
            fs = []
            for _ in range(c):
                fe = (0x10 + f.readu32(),0x10 + f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32())
                asrt(fe[2] in {0,1},f.pos - 0x10)
                fs.append(fe)

            for fe in fs:
                f.seek(fe[0])
                fn = f.read0s().decode('utf-8') + '/'
                f.seek(fe[1])
                fn += f.read0s().decode('utf-8')
                f.seek(fe[3])
                writefile(o + '/' + fn,f.decompress(fe[5],('none','deflate')[fe[2]]))

            f.close()
            if fs: return
        case 'One Piece Battle Adventure FSM':
            db.try_custom()
            from lib.file import File
            f = File(i)

            f._end = '>' if f.readu8() == 1 else '<'
            f.skip(7)
            asrt(f.read(7) == b'FSM_v1.')
            v = f.read(1)[0]-0x30
            asrt(v in {1,2},v)
            f.back(14)

            if v == 1:
                f.skip(2)
                align = 0x20
                ces = 0xC
            elif v == 2:
                align = f.readu16()
                ces = 0x20
            tab_is = f.readu32()
            asrt(tab_is in {0,1})
            f.skip(8)
            c = f.readu32() + f.readu32()
            fes = f.readu32()
            uxs = f.readu32() * 4

            f.seek(align+-align%0x20)

            def readce():
                be = f._end

                f._end = '>' if f.readu8() == 1 else '<'
                ct = f.readu8()
                asrt(ct in {0,3,5,7},ct)
                asrt(ct != 5,f'{ct} not implemented (FUN_002ff030)')
                f.skip(2)
                us,zs = f.readu32(),f.readu32()
                f.skip(ces - 12)

                d = f.decompress(zs,('none',0,0,'lzss16c',0,1,0,'zlib')[ct],usize=us,big_endian=f._end == '>')
                f.align(align)

                f._end = be
                return d

            ft = File(readce(),endian=f._end)
            ft_readv = ft.readu32 if tab_is else ft.readu16
            ovs = [ft_readv() for _ in range(c)]
            ft.align(4)
            ftbp = ft.pos

            drs = ['/']*c
            fc = 0
            for ix in range(c):
                ft.seek(ftbp + fc * uxs + ix * 12 + ovs[ix])
                vs = (ft.readu32(),ft.readu32(),ft.readu32())

                if vs[0] & 0x10000000:
                    n = ft.read0s().decode('ascii')
                    ft.back(len(n)+1)
                    drs += [drs.pop() + '/' + n] * vs[2]
                else:
                    ft.skip(uxs)
                    fc += 1

                    fn = ft.read0s()
                    ft.back(len(fn)+1)
                    try:
                        fn = fn.decode('ascii')
                        asrt(fn.isprintable() and fn,fn)
                    except:
                        print(ft.pos)
                        raise
                    f.seek(align + fes + vs[1]*align)
                    f.align(align)
                    f.align(0x20)
                    d = readce() if uxs else f.readc(vs[2])
                    writefile(o + '/' + drs.pop() + '/' + fn,d)

            ft.close()
            f.close()
            if listdir(o): return
        case 'One Piece Battle Adventure NXD':
            db.try_custom()
            from lib.file import File
            db.set_temp_print()
            f = File(i)
            f._end = '>' if f.readu8() == 1 else '<'

            f.skip(1)
            aln = f.readu16()
            f.skip(4)
            asrt(f.read(7) == b'FSM_v1.')
            v = f.read(1)[0]-0x30
            asrt(v in {1,2},v)
            if v == 1: aln = 0x20

            fc = f.readu32()
            f.skip(4)
            fs = f.readu32()
            f.seek(aln + fs)
            f.align(aln)
            f.align(0x20)
            f.skip(fc*aln)

            while f:
                bp = f.pos
                if f.readu8() in {0,1}:
                    f.skip(1)
                    if not f.readu16()%0x10 and f.readu32() in {0,1} and f.read(7) == b'FSM_v1.' and f.read(1) in b'12': break
                f.seek(bp+0x10)
            else:
                f.close()
                db.reset_temp_print()
                return 1
            aln = bp

            rs = []
            for of in range(0,f.size,aln):
                f.seek(of)
                if f.readu8() not in {0,1}: continue
                f.skip(1)
                if f.readu16()%0x10 or not f.readu32() in {0,1} or f.read(7) != b'FSM_v1.' or not f.read(1) in b'12': continue
                f.seek(of)
                tf = TmpFile()
                writefile(tf,f.read())
                rs.append(extract4_3(tf.p,o,'One Piece Battle Adventure FSM'))
                tf.destroy()

            f.close()
            db.reset_temp_print()
            if not any(rs): return
        case 'RTX Remix Package':
            db.try_custom()
            from lib.file import File
            from lib.crypto import crc_hash
            f = File(i,endian='<')
            asrt(f.read(4) == b'\x0D\xD0\xAD\xBA' and f.readu32() == 1)

            f.seek(f.readu64())
            ac,bc = f.readu16(),f.readu16()
            asts = [[f.readu16() for _ in range(10)] for _ in range(ac)]
            blbs = []
            for _ in range(bc):
                fe = [f.readu40(),f.readu8()]
                asrt(fe[1] in {0,1})
                f.padc(1)
                asrt(f.readu8() == 0)
                blbs.append(fe + [f.readu32(),f.readu32()])
            stb = [x.decode('utf-8') for x in f.read()[:-1].split(b'\0')]

            for a in asts:
                bfn,xfn = splitext(stb[a[0]])
                bfn = o + '/' + bfn
                isn = not a[9]-a[8]
                for ix in range(a[8],a[9] + 1):
                    f.seek(blbs[ix][0])
                    # seems to be some variation https://github.com/microsoft/DirectStorage/tree/main/GDeflate isn't able to decompress
                    d = f.decompress(blbs[ix][2],('none','none'#'gdeflate'
                                                  )[blbs[ix][1]],usize=a[2] | a[3] << 16,db=db)
                    asrt(crc_hash(d,'crc32') == blbs[ix][3])
                    writefile(bfn + ('' if isn else f'_{ix}') + xfn + ('.gd' if blbs[ix][1] else ''),d)

            f.close()
            if asts: return
        case 'Cheat Engine Cheat Table':
            db.try_custom()
            import re
            RGS = re.compile(r' +')

            import xml.etree.ElementTree as ET
            tr = ET.parse(i).getroot()

            def fcs(iob,d):
                if iob.find('CheatEntries') is not None:
                    for x in iob.find('CheatEntries').findall('CheatEntry'):
                        n = x.find('ID').text
                        if x.find('Description') is not None: n = RGS.sub(' ',sub_path(x.find('Description').text.strip('"'),slash=True)).strip() + '_' + n
                        if x.find('AssemblerScript') is not None: writefile(d + '/' + n + '.asm',x.find('AssemblerScript').text,'w')
                        fcs(x,d + '/' + n)
            fcs(tr,o)

            if tr.find('CheatCodes') is not None:
                ob = []
                for x in tr.find('CheatCodes').findall('CodeEntry'):
                    n = x.find("Description").text.strip('"')
                    if x.attrib.get('GroupHeader') == '1': ob.append(f'=== {n} ===')
                    else:
                        if x.find('AddressString') is not None:
                            ob.append(f'{n} @ {x.find("AddressString").text}')
                            for pn in ('Before','Actual','After'):
                                if x.find(pn) is not None: ob.append(pn + ': ' + ' '.join([b.text for b in x.find(pn).findall('Byte')]))
                            ob.append('')
                if ob: writefile(o + '/codes.txt','\n'.join(ob),'w')
            if tr.find('UserdefinedSymbols') is not None:
                ob = [x.find('Name').text + ' @ ' + x.find('Address').text for x in tr.find('UserdefinedSymbols').findall('SymbolEntry')]
                if ob: writefile(o + '/symbols.txt','\n'.join(ob),'w')
            if tr.find('LuaScript') is not None: writefile(o + '/script.lua',tr.find('LuaScript').text,'w')
            if tr.find('DisassemblerComments') is not None:
                ob = [x.find('Address').text.strip() + '\n' + x.find('Comment').text.strip() for x in tr.find('DisassemblerComments').findall('DisassemblerComment')]
                if ob: writefile(o + '/disassembler_comments.txt','\n\n'.join(ob),'w')

            del tr
            if listdir(o): return
        case 'Wii Exported Save Data':
            sdk = db.bin_path + 'wii_sd.bdb'
            if exists(sdk):
                sdk = open(sdk,'rb').read()
                sdky,sdiv = sdk[:0x10],sdk[0x10:]
            else:
                import re
                rg = re.findall(r'<code>([a-f\dA-F]{32})</code>',db.c.get('https://wiki.wiidatabase.de/wiki/SD-Key').text)
                asrt(len(rg) == 2)
                sdky,sdiv = bytes.fromhex(rg[0]),bytes.fromhex(rg[1])
                writefile(sdk,sdky + sdiv)

            db.try_custom()
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='>')
            h = decrypt(f.readc(0xF0C0),'aes_cbc',sdky,sdiv)
            writefile(o + '/$SYS/header.bin',h)
            h = File(h,endian='>')

            h.skip(8)
            bnrs = h.readu32()
            h.skip(0x14)
            writefile(o + '/$SYS/banner.bnr',h.readc(bnrs))
            h.close()

            bks = f.readu32()
            asrt(bks == 0x70 and f.read(2) == b'Bk' and f.readu16() == 1)
            f.skip(4)
            c = f.readu32()
            f.skip(bks - 0x10)
            f.align(0x40)

            for _ in range(c):
                asrt(f.read(4) == b'\x03\xAD\xF1\x7E')
                s = f.readu32()
                f.skip(2)
                ty = f.readu8()
                asrt(ty in {1,2})
                fn = f.readc(0x45).split(b'\0')[0].decode('utf-8')
                iv = f.readc(0x10)
                f.align(0x40)
                if ty == 2 and s != 0: raise ValueError(f'Directory with size @ 0x{f.pos - 0x80:08X}')
                if ty == 2: mkdir(o + '/' + fn)
                elif ty == 1:
                    d = f.readc(s + -s%0x40)
                    writefile(o + '/' + fn,decrypt(d,'aes_cbc',sdky,iv)[:s])

            f.seek(-0x300)
            writefile(o + '/$SYS/device.crt',f.readc(0x180))
            writefile(o + '/$SYS/application.crt',f.readc(0x180))

            f.close()
            if c: return
        case 'Moe Cure Net FileList':
            db.try_custom()
            import json
            from lib.file import File
            f = File(i,endian='>')
            c = f.readu32()
            ob = {}

            fds = {}
            for _ in range(c):
                n = f.readc(f.readu32()).decode('utf-8')
                sn = f.readc(f.readu32()).decode('utf-8')
                if sn:
                    if not sn in fds:
                        fsn = dirname(i) + '/' + sn
                        if exists(fsn): fds[sn] = open(dirname(i) + '/' + sn,'rb')
                        elif exists(fsn + extname(n)): fds[sn] = open(fsn + extname(n),'rb')
                        else: print('Could not find',sn,'skipping')
                    if sn in fds:
                        fds[sn].seek(f.readu32())
                        writefile(o + '/' + n,fds[sn].read(f.readu32()))
                else:
                    f.skip(4)
                    ob[n] = f.readu32()
                f.skip(1)

            for x in fds.values(): x.close()
            f.close()
            if ob: json.dump(ob,open(o + '/$settings.json','w',encoding='utf-8'),indent=2,ensure_ascii=False)
            if listdir(o): return
        case 'The Indian In The Cupboard Data':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            f.seek(f.readu32())

            ac,c = f.readu16(),f.readu16()
            f.skip(ac*2+2)
            fs = [f.readu32() for _ in range(c+1)]
            for ix in range(c):
                f.seek(fs[ix])
                d = f.read(fs[ix+1]-fs[ix])
                if d[:2] == b'\x80\x01': ex = 'pal.image'
                elif d[:2] == b'\x80\x02': ex = 'image'
                elif d[:2] == b'\x80\x06': ex = 'anim'
                else:
                    ex = guess_ext(d)
                    if ex == 'bin' and int.from_bytes(d[:2],'big') <= 0x100 and len(d) <= 770: ex = 'pal'
                writefile(o + f'/{ix:04d}.{ex}',d)

            f.close()
            if c: return
        case 'Death End re:Quest 2 GDAT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'GDAT')

            c = f.readu32()
            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                ty = f.read(4)
                if ty[0] == 0:
                    try:
                        ty = ty[1:].decode('ascii')[::-1]
                        asrt(ty.isprintable())
                    except: ty = 'bin'
                else: ty = 'bin'

                d = None
                if fe[1] >= 0x96:
                    f.skip(0x7C)
                    if f.read(4) == b'BILZ':
                        f.skip(4)
                        if (0x90+f.readu32('>')) == fe[1]:
                            f.skip(4)
                            d = f.decompress(fe[1]-0x90,'zlib')
                if d is None:
                    f.seek(fe[0])
                    d = f.read(fe[1])

                writefile(o + f'/{ix:02d}.{ty}',d)

            f.close()
            if fs: return
        case 'Death End re:Quest 2 ZLIB':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')

            ty = f.read(4)
            if ty[0] == 0:
                try:
                    ty = ty[1:].decode('ascii')[::-1]
                    asrt(ty.isprintable())
                except: ty = extname(i)[1:]
            else: ty = extname(i)[1:]

            f.skip(0x7C)
            asrt(f.read(4) == b'BILZ')
            f.skip(4)
            zs = f.readu32()
            f.skip(4)
            d = f.decompress(zs,'zlib')
            writefile(o + f'/{tbasename(i)}.{ty}',d)

            f.close()
            if d: return
        case 'Sumo Digital XPAC':
            db.try_custom()
            from lib.file import File,decompress,iszl
            from lib.crypto import HashLib
            HL = HashLib.dl('sumo_xpac',db)

            bak = {
                0xC03C389F:'.\\Resource\\Racers\\Zobio.zif',0x71CA44A2:'.\\Resource\\Racers\\Zobio.zig',
                0x94AAD2E5:'.\\Resource\\Tracks\\Particle_TestTrack.zif',0x4638DEE8:'.\\Resource\\Tracks\\Particle_TestTrack.zig',
                0x09A915C5:'.\\Resource\\Tracks\\SeasideHill_Hard_Unused.zif',0x55F4D9E6:'.\\Resource\\Tracks\\SeasideHill_Hard_Unused.zig',
                0xFFE6BEC5:'.\\Resource\\TSOData\\ItemDefaults.txt',0x59C8DA80:'.\\Resource\\TSOData\\GroupNames.txt',
            }
            for h in {0x0090AE05,0x9D853559,0x7EFC3B8B}: bak[h] = f'.\\Resource\\TSOData\\{h:08X}.tso'

            f = File(i,endian='<')
            f.skip(12)
            c = f.readu32()
            f.skip(4)

            fs = []
            for _ in range(c):
                f.skip(4)
                fs.append((f.readu32(),f.readu32(),f.readu32(),f.readu32()))

            HL.wait()
            for fe in fs:
                if fe[0] in HL: fn = HL[fe[0]]
                elif fe[0] in bak: fn = '$unk/' + bak.get(fe[0])
                else: fn = f'$unk/{fe[0]:08X}.bin'

                f.seek(fe[1])
                d = f.readc(fe[2] or fe[3])
                if iszl(d): d = decompress(d,'zlib')
                writefile(o + '/' + fn,d)
            if fs: return
        case 'Dragon UnPACKer 5 Plugin':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            asrt(f.read(5) == b'DUPP\x1A')
            v = f.readu8()
            f.skip(2)

            inf = open(o + '/' + tbasename(i) + '.ini','w',encoding='utf-8')
            inf.write(f'[{tbasename(i)}]\nenabled=1\n')
            infsp = inf.tell()

            if v < 4:
                f.skip(12)
                ps = f.reads32()
                fc = f.reads32()

                for vn in ('name','url','author','comment'): inf.write(f'{vn}={f.read(f.readu8()).decode("utf-8")}\n')
                if ps > 0: open(o + '/picture.bmp').write(f.read(ps))

                for _ in range(fc):
                    s = f.reads32()
                    f.skip(0x10)
                    c = f.reads32()
                    f.skip(8)
                    fn = f.read(f.readu8()).decode('utf-8')
                    fn = o + '/' + os.path.join(f.read(f.readu8()).decode('utf-8'),fn)
                    d = f.decompress(s,('none','zlib')[c])
                    writefile(fn,d)
            elif v == 4:
                offc = f.reads32()
                offs = []
                for _ in range(offc):
                    oe = [f.readu8()]
                    fls = f.readu8()
                    if fls & 1: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x20: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x40: oe.append(f.reads32())
                    else:
                        f.skip(4)
                        oe.append(0)
                    oe += [f.reads64(),f.reads64()]
                    f.skip(0x28)
                    offs.append(oe)

                fs = []
                fnd = {}
                df = None
                for oe in offs:
                    f.seek(oe[4])
                    d = f.decompress(oe[5],('none','zlib','lzma_us32')[oe[1]])

                    b = File(d,endian='<')
                    if oe[0] == 1:
                        b.skip(12)
                        for vn in ('name','url','author'): inf.write(f'{vn}={b.read(b.readu8()).decode("utf-8")}\n')
                        inf.write(f'comment={b.read(b.readu32()).decode("utf-8")}\n')
                    elif oe[0] == 2:
                        for _ in range(oe[3]):
                            fe = [b.reads64(),b.reads64()]
                            b.skip(12)
                            fls = b.readu8()
                            if fls & 0x10: fe.append(b.readu8())
                            else:
                                b.skip(1)
                                fe.append(0)
                            b.skip(1)
                            fe.append(b.reads32())
                            b.skip(0x45)
                            if not fls & 0x40: fs.append(fe)
                    elif oe[0] == 10: writefile(o + '/' + tbasename(i) + '_banner.bmp',d)
                    elif oe[0] == 20:
                        for ix in range(oe[3]): fnd[ix] = b.read(b.readu8()).decode('utf-8')
                    elif oe[0] == 21: df = b
                    else: writefile(o + '/$' + str(oe[0]) + '.unkheader',d)

                if fs and not df: return 1

                for fe in fs:
                    df.seek(fe[0])
                    d = df.decompress(fe[1],('none','zlib','lzma_us32')[fe[2]])
                    writefile(o + '/' + fnd.get(fe[3],str(fe[3])),d)
            elif v == 5:
                f.skip(2)
                offc = f.readu32()
                offs = []
                for _ in range(offc):
                    oe = [f.readu8()]
                    fls = f.readu8()
                    if fls & 1: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x20: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x40: oe.append(f.readu32())
                    else:
                        f.skip(4)
                        oe.append(0)
                    oe += [f.reads64(),f.reads64()]
                    f.skip(0x48)
                    offs.append(oe)

                fs = []
                fnd = {}
                fld = {}
                df = None
                for oe in offs:
                    f.seek(oe[4])
                    d = f.decompress(oe[5],('none','zlib','lzma_us32')[oe[1]])

                    b = File(d,endian='<')
                    if oe[0] == 1:
                        b.skip(12)
                        for vn in ('name','url','author'): inf.write(f'{vn}={b.read(b.readu8()).decode("utf-8")}\n')
                        inf.write(f'comment={b.read(b.readu32()).decode("utf-8")}\n')
                    elif oe[0] == 2:
                        for _ in range(oe[3]):
                            fe = [b.reads64(),b.reads64()]
                            b.skip(12)
                            fls = b.readu32()
                            if fls & 0x10: fe.append(b.readu8())
                            else:
                                b.skip(1)
                                fe.append(0)
                            b.skip(5)
                            fe += [b.readu32(),b.readu32()]
                            b.skip(0x44)
                            if not fls & 0x40: fs.append(fe)
                    elif oe[0] == 10: writefile(o + '/' + tbasename(i) + '_banner.bmp',d)
                    elif oe[0] == 20:
                        for ix in range(oe[3]): fnd[ix] = b.read(b.readu8()).decode('utf-8')
                    elif oe[0] == 23:
                        for ix in range(oe[3]): fld[ix] = b.read(b.readu8()).decode('utf-8')
                    elif oe[0] == 21: df = b
                    else: writefile(o + '/$' + str(oe[0]) + '.unkheader',d)

            infp = inf.tell()
            inf.close()
            if len(listdir(o)) > 1 or infp != infsp: return
        case 'Candy Land Adventure RFS':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            def readb(p:list):
                bo = f.pos
                asrt(f.read(4) == b'Ce\x87\x09')
                pf = '/'.join([f'{x:02d}' for x in p])
                f.skip(4)
                c = f.readu16()
                f.skip(6)
                fs = [(f.readu32()+bo,f.readu32()) for _ in range(c)]

                for ix,fe in enumerate(fs):
                    f.seek(fe[0])
                    d = f.readc(fe[1])
                    if fe[1] > 0x18 and d[:4] == b'Ce\x87\x09': ex = 'rfs'
                    elif len(p) == 2 and p[0] == 1 and ix == 0: ex = 'bg'
                    elif len(p) == 2 and p[0] == 1 and ix == 2 and not fe[1]%4: ex = 'pal'
                    elif len(p) == 2 and p[0] == 1 and c >= 7 and ix == 5: ex = 'anim'
                    elif (len(p) == 2 and p[0] == 1 and ((c >= 7 and ix == 6) or (c >= 6 and ix == 5))) or (len(p) == 1 and p[0] == 2): ex = 'mono.11025hz.s8.pcm'
                    elif len(p) == 2 and p[0] == 0 and ix == 0: ex = 'anim'
                    else: ex = guess_ext(d)
                    writefile(f'{o}/{pf}/{ix:02d}.{ex}',d)
                    if ex == 'rfs':
                        f.seek(fe[0])
                        readb(p + [ix])

            readb([])
            f.close()
            if listdir(o): return
        case 'Opalium Engine PAK':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'PAK ')

            c = f.readu32()
            f.skip(8)
            fs = []
            for _ in range(c):
                fe = (f.readu32(),f.readu32())
                f.skip(4)
                es = f.readu32()
                f.skip(8)
                fs.append((fe[0],fe[1],f.readc(es - 0x18).rstrip(b'\0').decode('ascii')))

            for fe in fs:
                f.seek(fe[0])
                d = f.readc(fe[1])
                writefile(o + '/' + fe[2],d)

            f.close()
            if fs: return
        case 'Other Ocean Interactive ARC':
            db.try_custom()
            from lib.file import File
            fd = File(i,endian='<')
            fd.skip(4)

            cs = fd.readu32()
            f = File(fd.decompress(cs,'msf'),endian=fd._end)
            fs = []
            while f:
                try: fs.append((f.read0s().decode('ascii'),f.readu32() + cs + 8,f.readu32()))
                except (UnicodeDecodeError,EOFError):
                    f.close()
                    fd.close()
                    return 1
            f.close()
            fs.append((0,fd.size,0))

            for ix,fe in enumerate(fs[:-1]):
                s = fs[ix+1][1] - fe[1]
                if s < 0 or (s == 0 and fe[2] != 0):
                    fd.close()
                    return 1
                fd.seek(fe[1])
                d = fd.decompress(s,'msf' if s != fe[2] else 'none',usize=fe[2])
                if len(d) != fe[2]:
                    fd.close()
                    return 1
                writefile(o + '/' + fe[0],d)

            fd.close()
            if fs: return
        case 'Piper SAGE':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'RIFF')
            ep = f.readu32() + f.pos
            typ = f.read(4).decode('ascii')
            asrt(typ == 'SAGE')

            FNM = {}
            def readb(typ):
                n = f.read(4).decode('ascii')
                bs = f.readu32()
                ep = bs + f.pos

                match n:
                    case 'LIST':
                        typ = f.read(4).decode('ascii')
                        while f < ep: readb(typ)
                    case 'SWAV':
                        asrt(bs == 0x58)
                        fn = sub_path(f.read(0x50).rstrip(b'\0').decode('ascii'))
                        f.skip(4)
                        FNM[f.readu32()] = fn
                    case 'S256':
                        f.skip(0x21)
                        fn = sub_path(f.read(0x50).rstrip(b'\0').decode('ascii'))
                        f.skip(0x11)
                        of = f.readu32()
                        FNM[of] = (fn,f.read(ep - f.pos - 4))

                    case 'RIFF':
                        f.back(8)
                        asrt(f.pos in FNM)
                        writefile(o + '/' + FNM.pop(f.pos),f.read(bs + 8))
                    case 'DIB8':
                        fe = FNM.pop(f.pos - 8)
                        writefile(o + '/' + fe[0],b'BM' + (14 + len(fe[1]) + bs).to_bytes(4,'little') + b'\0'*4 + (14 + len(fe[1])).to_bytes(4,'little') + fe[1] + f.read(bs))

                    case 'SGDS'|'SSND'|'SDIB': pass
                    case _: raise NotImplementedError(f'{n} ({bs}) @ 0x{f.pos - 8:08X}')

                f.seek(ep)
                f.align(2)
            while f < ep: readb(typ)

            f.close()
            if listdir(o): return
        case 'DreamFactory 5 Resource':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            f.padc(2)
            asrt(f.readu16() == 1)

            f.skip(0x10)
            c = f.readu32()
            f.padc(8);f.skip(8)
            f.align(0x200)
            f.skip(0x200)

            ofs = [f.readu32() for _ in range(c)]
            for of in ofs:
                f.seek(of)
                id,s = f.readu32(),f.readu32()
                f.skip(4)
                ty = f.read(4)[::-1].decode('ascii')
                if ty == '\0\0\0\0': ty = 'text'
                asrt(ty.isprintable())
                writefile(f'{o}/{id:03d}.{ty.lower()}',f.read(s))

            f.close()
            if ofs: return
        case 'Sunday vs. Magazine FARC':
            db.try_custom()
            from lib.file import File
            from lib.crypto import HashLib

            HL = HashLib.dl('sxm',db)
            f = File(i,endian='<')
            asrt(f.read(4) == b'FARC' and f.readu32() == 0x100)

            c = f.readu32()
            so = f.readu32()
            fs = [(f.readu32(),f.readu32(),f.readu64()) for _ in range(c)]
            if so == 0:
                f.close()
                fd = open(noext(i) + '.fac','rb')
            else: fd = f

            HL.wait()
            for fe in fs:
                fd.seek(fe[0])
                d = fd.read(fe[1])
                if fe[2] in HL: fn = HL[fe[2]]
                else:
                    if d[:4] == b'FARC': ex = 'fab'
                    elif d[:4] == b'TARC': ex = 'tpk'
                    elif d[:4] == b'FTEX': ex = 'tex'
                    elif d[:4] == b'PPHD': ex = 'phd'
                    elif d[:4] == b'aeDT': ex = 'dat'
                    elif d[:4] == b'CHNK' and d[0x10:0x14] == b'BACK': ex = 'bpk'
                    elif d[:4] == b'CHNK' and d[0x10:0x14] == b'CHAR': ex = 'cpk'
                    elif d[:4] == b'CHNK': ex = 'chnk'
                    elif d[:4] == b'EMIT': ex = 'emit'
                    elif d[:4] == b'SEQH': ex = 'spk'
                    elif d[:5] == b'_enum': ex = 'mess.bin'
                    else:
                        ex = guess_ext_alvion(d)
                        if ex == 'luac': ex = 'so'
                        elif ex == 'psadpcm': ex = 'pbd'
                    fn = f'{fe[2]:016X}.{ex}'
                writefile(o + '/' + fn,d)

            fd.close()
            if fs: return
        case 'Sunday vs. Magazine TARC'|'Sunday vs. Magazine EMIT':
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.peek(4).decode('ascii') == t[-4:])
            r = sxm_block(f,o)
            f.close()
            if r: return
        case 'Sunday vs. Magazine BACKground PacK'|'Sunday vs. Magazine CHARacter PacK':
            from lib.file import File
            f = File(i,endian='<')

            bks = {}
            while f:
                n = f.read(4).decode('ascii')
                if not n in bks: bks[n] = 0
                else: bks[n] += 1
                f.skip(4)
                s = f.readu32()
                asrt(s == f.readu32())
                ep = f.pos + s

                match n:
                    case 'CHNK'|'BACK'|'UVAM'|'CHAR':
                        if s > 0: writefile(f'{o}/{n}{bks[n]:02d}.bin',f.readc(s))
                    case 'TEXR'|'MODL'|'MOTN': sxm_block(f,f'{o}/{n}{bks[n]:02d}',hint=n)
                    case _: raise NotImplementedError(f'{n} ({s}) @ {f.pos-0x10:08X}')
                f.seek(ep)

            f.close()
            if bks: return
        case 'Sunday vs. Magazine aeDAT':
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'aeDT')

            f.padc(2)
            c = f.readu16()
            f.skip(4);f.padc(4)
            offs = [f.readu32() for _ in range(c+1)]
            fs = [f.read(0x20).rstrip(b'\0').decode('ascii') for _ in range(c)]
            for ix in range(c):
                f.seek(offs[ix])
                writefile(o + '/' + fs[ix],f.readc(offs[ix+1]-offs[ix]))

            f.close()
            if fs: return
        case 'ChainDive FLD':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu8() == 0xD0)

            c = f.readu24()
            writefile(o + '/$filename.txt',f.readc(0x14).rstrip(b'\0'))
            ofs = [f.readu32() for _ in range(c+1)]

            for ix in range(c):
                f.seek(ofs[ix] & 0xFFFFF800)
                d = f.readc((ofs[ix+1] & 0xFFFFF800) - ofs[ix])
                writefile(o + f'/{ix:03d}.{guess_ext_alvion(d)}',d)

            f.close()
            if c: return
        case 'Alvion INS Resource':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'ins\0')

            f.seek(0x20)
            tof = f.readu32()
            f.seek(0x30)
            teof = f.readu32()
            asrt(teof == f.readu32())
            f.seek(0x40)
            dof = f.readu32()

            f.seek(tof)
            fs = []
            while f < teof:
                fs.append((f.readu32() + dof,f.readu32()))
                f.skip(8)

            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.readc(fe[1])
                writefile(o + f'/{ix:03d}.{guess_ext_alvion(d)}',d)

            f.close()
            if fs: return
        case 'Alvion TIM2 Collection':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            f.padc(4)

            c = f.readu32()
            f.padc(8)
            ofs = [f.readu32() for _ in range(c)]
            ofs.sort()
            ofs.append(f.size)

            for ix in range(c):
                f.seek(ofs[ix])
                d = f.readc(ofs[ix+1]-ofs[ix])
                writefile(o + f'/{ix:02d}.{guess_ext_alvion(d)}',d)

            f.close()
            if c: return

    return 1

def dnasoft_lzss_decrypt(i:bytes,pyo):
    from lib.crypto import decrypt
    asrt(i[:4] == b'LZSS')
    rs = int.from_bytes(i[4:8],'little')
    return decrypt(i[8:8+rs+-rs%8],'blowfish_le',pyo['dnasoft'])[:rs]
def guess_ext_alvion(d:bytes):
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    ex = None
    if d[:8] == b'I3D_I3M\0': ex = 'i3m'
    elif d[:8] == b'I3D_I3R\0': ex = 'i3r'
    elif d[:8] == b'I3D_BIN\0': ex = 'i3d'
    elif d[:4] == b'ins\0': ex = 'res'
    elif d[:4] == b'alk\0': ex = 'alk'
    elif d[:4] == b'demo': ex = 'demo'
    else:
        if s > 0x60 and not sum(d[:4]) and sum(d[4:8]) and not sum(d[8:16]):
            c = 0x10 + int.from_bytes(d[4:8],'little')*4
            o = int.from_bytes(d[0x10:0x14],'little')
            if (c+-c%0x10) == o and d[o:o+4] == b'TIM2': ex = 'tm2col'
    ex = ex or guess_ext_ps2(d)

    return ex
def sxm_block(inp,o:str,hint=None):
    from lib.file import File
    f:File = inp
    p = f.pos

    match f.read(4).decode('ascii'):
        case 'TARC':
            asrt(f.readu32() == 0x100)
            c = f.readu32()
            asrt(f.readu32() != 0)
            fs = [(f.read(0x38).rstrip(b'\0').decode('ascii'),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(p + fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))
            return bool(fs)
        case 'EMIT':
            asrt(f.readu32() == 0x101)
            c = f.readu32()
            f.seek(p + int.from_bytes(f.read(4),'little'))
            d = []
            fns = {}
            for _ in range(c):
                f.skip(0x20)
                fn = f.read(0x20).rstrip(b'\0')
                if fn:
                    if not fn in fns: fns[fn] = 0
                    if d: writefile(o + '/' + d[0] + (f'.{fns[fn]}' if fns[fn] else ''),b''.join(d[1:]))
                    fns[fn] += 1
                    d = [fn.decode('ascii')]
                d.append(f.readc(0xE0))
            if d: writefile(o + '/' + d[0] + (f'.{fns[fn]}' if fns[fn] else ''),b''.join(d[1:]))
            return bool(c)
        case _:
            f.back(4)
            if hint in {'MODL','MOTN'}:
                fof = f.peek('u32',poffset=0x2C)
                fs = [(f.read(0x20).rstrip(b'\0').decode('ascii'),f.skip(8),f.readu32(),f.readu32()) for _ in range(fof//0x30)]
                for fe in fs:
                    f.seek(p + fe[3])
                    writefile(o + '/' + fe[0],f.readc(fe[2]))
                return bool(fs)
