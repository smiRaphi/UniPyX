from lib.main import *

BARBIE_XMP = {
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
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')
            fd = open(noext(i) + '.dat','rb')
            assert f.read(4) == b'BLDh' and f.readu32() == 0

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
                    assert fc and bs
                    for _ in range(fc):
                        fs.append([f.readu32()*bs,f.readu32(),f.readu32()])
                        f.skip(0x1C)
                elif n == b'tbl ':
                    assert fs
                    for fe in fs: fe.append(f.read0s().decode('utf-8').lstrip('/'))

                f.seek(ep)
            f.close()

            for fe in fs:
                fd.seek(fe[0])
                d = fd.read(fe[1])
                if fe[2]:
                    assert d[:4] == b'GARC',d[:4]
                    assert d[8:12] == b'zlib',d[8:12]
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
                    assert ob,fe[0]
                    d = b''.join(ob)
                xopen(o + '/' + fe[3],'wb').write(d)
            if fs: return
        case 'Import Tuner Challenge TOC+DAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')
            fd = open(noext(i) + '.dat','rb')

            c = f.readu32()
            f.skip(12)
            offs = []
            for ix in range(c):
                of,zs,us = f.readu32(),f.readu32(),f.readu32()
                f.skip(4)
                if of in offs: continue
                offs.append(of)

                fd.seek(of*0x800)
                fn = f'{o}\\{ix:04d}.bin'
                d = fd.read(zs)

                if d and zs == us: raise NotImplementedError(ix)
                elif not d: assert us == 0,ix
                elif us != zs and d[:8] == b'\x00\xE9UCL\xFF\x01\x1A':
                    tf = TmpFile('.ucl')
                    open(tf.p,'wb').write(d)
                    _,r,_ = run(['uclpack32','-d',tf,fn],print_try=False)
                    if exists(fn) and getsize(fn) == us: tf.destroy()
                    else:
                        mv(tf.p,f'{o}/F/{ix:04d}_{r.strip().rsplit("\n",1)[1].split(": ",1)[1]}.ucl')
                else:
                    assert us in (0,zs),ix
                    open(fn,'wb').write(d)

            f.close()
            fd.close()
            if c: return
        case 'Xenoblade Chronicles X DE ARH2':
            scr = db.get('xbxdetool')
            fl = dirname(scr) + '/Filelists'
            if exists(fl + '/hash_list.txt'):
                HL = [x.split('|',1)[1] for x in open(fl + '/hash_list.txt').read().strip('\r\n').split('\n') if x]
                remove(fl + '/hash_list.txt')
                for hf in listdir(fl):
                    hf = fl + '/' + hf
                    if isfile(hf) and hf.lower().endswith('.txt'):
                        HL += open(hf).read().strip('\r\n').split('\n')
                        remove(hf)
                HL.extend([
                    '/chr/oj/qsten010901.ces','/chr/oj/qsten011101.ces','/chr/oj/qsten011104.ces','/chr/oj/qsten011108.ces','/chr/oj/qsten011305.ces','/chr/oj/qsten011501.ces','/chr/oj/qsten011503.ces',

                    '/ev/motion/ptcs/xs00010100/xs00010100_c03_cm_xs00010100_c03.eva','/ev/motion/ptcs/xs00010100/xs00010100_c01_cm_xs00010100_c01.eva','/ev/motion/ptcs/xs00010100/xs00010100_c03_evr_oj010006.anm','/ev/motion/ptcs/xs11020100_1/xs11020100_1_c08_kee002_ev_cmn_500_019_pcefb.eva',
                    '/ev/motion/ptcs/xs11020100_1/xs11020100_1_c09_evr1_model_en013101.eva','/ev/motion/ptcs/xs00010100/xs00010100_c01_evr_oj010006.anm','/ev/motion/ptcs/xs00010100/xs00010100_c03_evr_oj010006.eva','/ev/motion/ptcs/xs08110100_1/xs08110100_1_c12_evr_oj210004.anm',
                    '/ev/motion/ptcs/xs11020100_1/xs11020100_1_c08_evr1_model_en013101.anm','/ev/motion/ptcs/xs00010100/xs00010100_c01_evr_oj010006.eva','/ev/motion/ptcs/xs11020100_1/xs11020100_1_c08_kee001_ev_cmn_500_020_pcefb.eva','/ev/motion/ptcs/xs11020100_1/xs11020100_1_c08_evr1_model_en013101.eva',
                    '/ev/motion/ptcs/xs08110100_1/xs08110100_1_c12_evr_oj210004.eva',

                    '/ev/title/title3_c01_evr8_model_np009001.anm','/ev/title/title2_c01_evr25_oj490036.anm',

                    '/chr/en/sound_dl779100.ces',
                    '/ev/motion/en/en010301/509008m_sp_7_anm.anm','/ev/motion/en/en010501/509008m_sp_7_ed_anm.anm','/ev/motion/dl/dl080100/509012m_sp_11_anm.anm','/ev/motion/en/en011101/509009m_sp_8_anm.anm','/ev/motion/en/en011101/509008m_sp_7_ed_anm.anm','/ev/motion/en/en010601/509002m_sp_2_lp_anm.anm',
                    '/ev/motion/en/en050201/509011m_sp_10_anm.anm',
                    '/ev/motion/oj/ws121101r/509001m_sp_2_st_anm.anm','/ev/motion/oj/ws121101r/509002m_sp_2_lp_anm.anm',
                ])
                open(fl + '/list.txt','w').write('\n'.join(sorted(list(set(HL)))))
                del HL

            run([scr,'extract-all','-i',i,'-o',o],cwd=dirname(scr))
            if listdir(o): return
        case 'CSI NY GRF':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i)
            assert f.read(4) == b'GRF\x05'

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
                assert fe[3] == 1,f'{fe[3]}: {d[:8].hex()}'
                xopen(o + '/' + fe[0],'wb').write(f.decompress(s,'zlib'))

            f.close()
            if fs: return
        case 'Artech DAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(8) == b'Artech\0\0' and f.readu16() == 2 and f.readu16() == 3 and f.readu64() == 1

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
                open(f'{o}/{ix:04d}.{guess_ext(d)}','wb').write(d)

            f.close()
            if fs: return
        case 'Quantum3 DIR+WAD':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(noext(i) + '.dir',endian='<')
            fd = open(noext(i) + '.wad','rb')

            c = f.readu32()
            for _ in range(c):
                n = f.read(0x40).rstrip(b'\0').decode('utf-8')
                s = f.readu32()
                fd.seek(f.readu32() * 0x800)
                xopen(o + '/' + n,'wb').write(fd.read(s))

            f.close()
            fd.close()
            if listdir(o): return
        case 'Harry Potter and Prisoner of Azkaban IDS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            fo = f.readu32()
            f.back(4)

            fs = []
            while f.pos < fo:
                fe = (f.readu32(),f.readu32())
                if not fe[0]: break
                fs.append(fe)

            ob = []
            for fe in fs:
                f.seek(fe[0])
                ob.append(f'{fe[1]:03d}: {f.read0s().decode()}')
            f.close()
            if ob:
                open(o + '/' + tbasename(i) + '.txt','w').write('\n'.join(ob))
                return
        case 'Harry Potter and Prisoner of Azkaban SDT':
            if db.print_try: print('Trying with custom extractor')
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
                tg = f.read(4)
                f.back(4)
                while (f.pos+8) < fs[ix+1]:
                    f.skip(4)
                    s = f.readu32()
                    if not s: break
                    f.back(8)
                    d.append(f.read(s))

                try: tg = tg.decode('ascii');assert tg.isprintable()
                except: ex = 'bin'
                else: ex = tg.lower()
                xopen(f'{o}/{ix:03d}.{ex}','wb').write(b''.join(d))

            f.close()
            if fs: return
        case 'Red Baron VOL':
            if not extract(i,o,'GE:Red Baron VOL'): return
            BMSK = 0x7FFFFFFF
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'VOL '
            ep = (f.readu32() & BMSK) + 8

            soff = 0
            fs = []
            while f.pos < ep:
                n = f.read(4).decode('ascii')
                bep = (f.readu32() & BMSK) + f.pos
                match n:
                    case 'vols':
                        if f.readu32(): soff = f.pos
                    case 'voli':
                        while f.pos < bep:
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
                assert f.read(4) == b'VBLK'
                xopen(o + '/' + fn,'wb').write(f.read(f.readu32() & BMSK))

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
            if db.print_try: print('Trying with custom extractor')
            import base64
            import xml.etree.ElementTree as ET

            tr = ET.parse(i)
            for r in tr.getroot().find('ResourceMap').iter('NamedResource'):
                cdt = r.find('Candidate')
                if cdt.get('type') == 'EmbeddedData': xopen(o + '/' + r.get('uri').split('://',1)[1],'wb').write(base64.b64decode(cdt.find('Base64Value').text))
            del tr
            if listdir(o): return
        case 'Team Ari Encrypted RGSSAD'|'RPG Maker Archive':
            KEYS = {
                b'\x9e\x83\x42\x0e\x4e\xbd\xdc\x6d':0x2b804be2,
                b'\x31\xac\x3e\x2d\x9b\x23\xda\x11':0xdeadcafe,
                b'RGSSAD\0\1':0xdeadcafe,
            }

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            sig = f.read(8)
            key = KEYS[sig]

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
                xopen(o + '/' + fn,'wb').write(read_data(readu32()))

            f.close()
            if listdir(o): return
        case '3D Ultra Cool TBVolume':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(9) == b'TBVolume\0'

            f.skip(2)
            c = f.readu16()
            f.skip(4)
            open(o + '/$description.txt','w',encoding='utf-8').write(f.read(0x18).rstrip(b'\0').decode('ascii'))

            fs = []
            for _ in range(c):
                f.skip(4)
                fs.append(f.readu32())
            for of in fs:
                f.seek(of)
                fn = f.read(0x18).rstrip(b'\0').decode('ascii')
                xopen(o + '/' + fn,'wb').write(f.read(f.readu32()))

            f.close()
            if fs: return
        case '3D Ultra Cool PKX':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decompress
            f = File(i,endian='<')
            assert f.read(4) == b'PKX:'

            f.skip(8)
            ct = f.readu32()
            s = f.readu32()
            ds = f.readu32()

            if ct in (0x101,0x102): d = decompress(f.read(s),{0x101:'lzo1x',0x102:'lzo1y'}[ct],usize=ds,db=db)
            else: raise NotImplementedError(hex(ct))
            f.close()

            xopen(o + '/' + basename(i),'wb').write(d)
            return
        case 'Disney\'s Tarzan FSD':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,HashLib
            HL = HashLib.dl('tarzan',db,fmt=lambda x:x[:1022],encoding='ascii')
            f = File(i,endian='<')

            ep = f.size
            fs = []
            while f.pos < ep:
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
                xopen(o + '/' + fn,'wb').write(d)

            f.close()
            if fs: return
        case 'Transformers: Devastation DAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'DAT\0'
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
                xopen(o + '/' + fe[2],'wb').write(f.read(fe[1]))

            f.close()
            if fs: return
        case 'Transformers: Devastation BXM': raise NotImplementedError
        case 'Nexas New PAC':
            run(['garbro','-x',i],cwd=o)
            if listdir(o): return
        case 'Asura Engine Resource':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(8) == b'Asura   '

            cs = {}
            while f:
                p = f.pos
                n = f.read(4).decode('latin-1')
                if n == '\0\0\0\0': break
                ep = f.readu32() + p
                f.skip(8)

                match n:
                    case 'RSCF':
                        f.skip(8)
                        s = f.readu32()
                        fn = f.read(ep - f.pos - s).split(b'\0',1)[0].decode('ascii').strip(' \\/')
                        f.seek(ep - s)
                        xopen(o + '/' + fn,'wb').write(f.read(s))
                    case 'FONT':
                        u1 = f.readf32()
                        u2 = f.read(4).split(b'\0',1)
                        w = f.readf32()
                        h = f.readf32()
                        fnr = f.read(0x100).split(b'\0',1)

                        fn = o + f'/${n}/' + fnr[0].decode('ascii').strip(' \\/')
                        xopen(fn,'wb').write(f.read(ep - f.pos))
                        try: u2[1] = u2[1].rstrip(b'\0').decode('ascii')
                        except: u2[1] = u2[1].rstrip(b'\0').hex(' ').upper()
                        try: fnr[1] = fnr[1].rstrip(b'\0').decode('ascii')
                        except: fnr[1] = fnr[1].rstrip(b'\0').hex(' ').upper()
                        xopen(fn + '.txt','w').write(f'Unknown 1: {u1}\nUnknown 2: {u2[0].decode('ascii')}\nUnknown 2 Leftover: {u2[1]}\nWidth: {w}\nHeight: {h}\nFilename Leftover: {fnr[1]}\n')
                    case 'HANM':
                        f.back(8)
                        unk = f.readu32()
                        f.skip(4)
                        if unk == 5:
                            fn1 = f.read(0x80).split(b'\0',1)
                            fn2 = f.read(0x80).split(b'\0',1)
                            fn = o + f'/${n}/' + fn2[0].decode('ascii').strip(' \\/')
                            xopen(fn,'wb').write(f.read(ep - f.pos))
                            try: fn1[1] = fn1[1].rstrip(b'\0').decode('ascii')
                            except: fn1[1] = fn1[1].rstrip(b'\0').hex(' ').upper()
                            try: fn2[1] = fn2[1].rstrip(b'\0').decode('ascii')
                            except: fn2[1] = fn2[1].rstrip(b'\0').hex(' ').upper()
                            xopen(fn + '.txt','w').write(f'Name 1: {fn1[0].decode("ascii")}\nName 1 Leftover: {fn1[1]}\nName 2: {fn2[0].decode("ascii")}\nName 2 Leftover: {fn2[1]}\n')
                        elif unk == 6:
                            f.skip(4)
                            sp = f.readf32()
                            fn = o + f'/${n}/' + f.read0s().decode('ascii').strip(' \\/')
                            f.align(4,p)
                            xopen(fn,'wb').write(f.read(ep - f.pos))
                            xopen(fn + '.txt','w').write(f'Speed(?): {sp}\n')
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
                        xopen(o + f'/${n}/{cs[n]}.bin','wb').write(f.read(ep - f.pos))
                        cs[n] += 1
                    case 'MSHV'|'NORM'|'MTXT'|'MSPF'|'EMOD'|'HMPT'|'CTTR':
                        f.skip(4)
                        fn = o + f'/${n}/' + f.read0s().decode('ascii').strip(' \\/')
                        f.align(4,p)
                        xopen(fn,'wb').write(f.read(ep - f.pos))
                    case 'MSHP'|'HSKN'|'CTAC':
                        f.skip(8)
                        fn = o + f'/${n}/' + f.read0s().decode('ascii').strip(' \\/')
                        f.align(4,p)
                        xopen(fn,'wb').write(f.read(ep - f.pos))
                    case 'SKYB':
                        if not n in cs: cs[n] = 0
                        xyz = (f.readf32(),f.readf32(),f.readf32())
                        f.skip(4)
                        skyfl = []
                        while f.pos < (ep-4):
                            skyfl.append(f.read0s().decode('ascii'))
                            f.align(4,p)
                        xopen(o + f'/${n}/{cs[n]}.txt','w').write(f'XYZ: {xyz[0]} {xyz[1]} {xyz[2]}\nUnknown: {f.readu32()}\nFile list:\n' + '\n'.join(skyfl))
                        cs[n] += 1
                    case 'FNFO':
                        if not n in cs: cs[n] = 0
                        xopen(o + f'/${n}/{cs[n]}.txt','w').write(f'File size: {f.readu32()}\n')
                        cs[n] += 1
                    case 'RSFL':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            sn = f.read0s().decode('ascii')
                            f.align(4,p)
                            ob.append(f'{sn}\n{f.readu32()}\n{f.readu32()}\n{f.readu32()}')
                        xopen(o + f'/${n}/{cs[n]}.txt','w').write('\n\n'.join(ob))
                        cs[n] += 1
                    case 'LTXT':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            ob.append(f.read(f.readu32()*2).rsplit(b'\0\0')[0].decode('utf-16le'))
                            f.align(4,p)
                        xopen(f'{o}/${n}/{cs[n]}.txt','w').write('\n\n'.join(ob))
                        cs[n] += 1
                    case 'HTXT':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            ob.append(f.read(4)[::-1].hex().upper() + ': ' + f.read(f.readu32()*2).rsplit(b'\0\0')[0].decode('utf-16le'))
                            f.align(4,p)
                        xopen(f'{o}/${n}/{cs[n]}.txt','w').write('\n\n'.join(ob))
                        cs[n] += 1
                    case 'TTXT':
                        if not n in cs: cs[n] = 0
                        c = f.readu32()
                        ob = []
                        for _ in range(c):
                            ob.append(f.read0s().decode('ascii'))
                            f.align(4,p)
                            ob[-1] += f': {f.readf32()} {f.readf32()} {f.readf32()} {f.readf32()} {f.readf32()}x{f.readf32()}'
                        xopen(f'{o}/${n}/{cs[n]}.txt','w').write('\n'.join(ob))
                        cs[n] += 1
                    case _: raise NotImplementedError(f'Unknown: {n} @ 0x{p:X}')

                f.seek(ep)

            f.close()
            if listdir(o): return
        case 'GameMaker Archive':
            run(['undertalemodcli','load',i,'-s',dirname(db.get('undertalemodcli')) + '\\ExportAll.csx'],cwd=o)
            if listdir(o): return
        case 'Contact File Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'LF 2'

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
                xopen(o + '/' + fn,'wb').write(d)

            f.close()
            if fs: return
        case 'Nemea File Archive':
            KEY = 0xEE ^ (0x1E6 & 0xFF)

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decrypt
            f = File(i,endian='<')
            assert f.read(4) == b'NFA0'

            f.skip(4)
            c = f.readu32()
            f.skip(4)
            fs = []
            for _ in range(c):
                inf = decrypt(f.read(0x94),'xor',KEY)
                fs.append((int.from_bytes(inf[8:12],'little'),int.from_bytes(inf[12:16],'little'),inf[20:].rsplit(b'\0\0')[0].decode('utf-16le'))) # fe[2] = ,int.from_bytes(inf[16:20],'little')
            for fe in fs:
                f.seek(fe[1])
                #if fe[2]: print(decrypt(f.read(4),'xor',KEY).hex(),fe[0],fe[1],hex(fe[2]));raise
                xopen(o + '/' + fe[2],'wb').write(decrypt(f.read(fe[0]),'xor',KEY))

            f.close()
            if fs: return
        case 'D.N.A. Softwares Pack':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'PACK'

            c = f.readu32()
            fs = []
            for _ in range(c):
                fn = f.read(0x40).rstrip(b'\0').decode('ascii')
                f.skip(8)
                fs.append((f.readu32(),f.readu32(),fn))
            for fe in fs:
                f.seek(fe[0])
                d = f.read(fe[1])
                xopen(o + '/' + fe[2] + ('.lzss' if d[:4] == b'LZSS' else ''),'wb').write(d)
                if d[:4] == b'LZSS': xopen(o + '/' + fe[2],'wb').write(dnasoft_lzss_decrypt(d))

            f.close()
            if fs: return
        case 'D.N.A. Softwares LZSS':
            if db.print_try: print('Trying with custom extractor')
            of = o + '/' + basename(i)
            if i.lower().endswith('.lzss'): of = of[:-5]
            d = dnasoft_lzss_decrypt(readfile(i))
            xopen(of,'wb').write(d)
            return
        case '@N-Factory DAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu32()

            fs = []
            for _ in range(c):
                fn = f.read(0x100).split(b'\0',1)[0].decode('ascii').replace('\\','/')
                while fn.startswith(('./','../')): fn = fn.split('/',1)[1]
                fs.append((f.readu32(),fn))
            for fe in fs: xopen(o + '/' + fe[1],'wb').write(f.read(fe[0]))

            f.close()
            if fs: return
        case 'UTG Software DDD':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'HTSW'

            c = f.readu32()
            assert f.readu64() == 0
            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.readc(fe[1] - fe[0])
                xopen(o + '/' + f'{ix:02d}.{guess_ext(d)}','wb').write(d)

            f.close()
            if fs: return
        case 'Braveheart BLB 2.0':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(8) == b'BLB2.0\0\0'

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
                xopen(o + '/' + fs[ix][0],'wb').write(f.readc(fs[ix+1][1] - fs[ix][1]))

            f.close()
            if fs: return
        case 'Looking Glass Resource':
            TMP = (
                "bin","string","image","font","anim","pall","shadtab","voc","shape","pict",
                "b2extern","b2reloc","b2code","b2header","b2resrvd","obj3d","stencil","movie",
                "rect",
                "palette512"
            )

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decompress
            from multiprocessing.pool import ThreadPool
            f = File(i,endian='<')
            assert f.read(0x10) == b'LG Res File v2\r\n'

            cm = f.read(0x60).split(b'\x1A')[0]
            if cm: open(f'{o}/$comment.txt','wb').write(cm)

            f.skip(12)
            f.seek(f.readu32())
            c = f.readu16()
            bo = f.readu32()
            fs = [(f.readu16(),f.readu24(),f.readu8(),f.readu24(),f.readu8()) for _ in range(c)]
            f.seek(bo)

            def dec(d,fn,fe):
                d = decompress(d,'lg_lzw' if fe[2] & 1 else ('implode' if fe[2] & 0x20 else 'none'))[:fe[1]]
                xopen(fn,'wb').write(d)
            def decc(d,ix1,ext,fsd,fe):
                d = decompress(d,'lg_lzw' if fe[2] & 1 else ('implode' if fe[2] & 0x20 else 'none'))[:fe[1]-fsd[0]]
                for ix in range(len(fsd)-1): xopen(f'{o}/{ix1}.{ext}/{ix:02d}.{ext}','wb').write(d[fsd[ix] - fsd[0]:fsd[ix+1] - fsd[0]])
            p = ThreadPool()
            prcs = []

            for fe in fs:
                fn = f'{fe[0]:03d}'
                if fe[4] < len(TMP): ext = TMP[fe[4]]
                elif fe[4] == 0x30: ext = 'map'
                elif 0x40 > fe[4] >= 0x30: ext = f'app{fe[4]-0x2F:02d}'
                else: ext = f'{fe[4]:02d}'

                if fe[2] & 0x20: db.get('pwexplode')
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
            if db.print_try: print('Trying with custom extractor')
            import re

            f = open(i,'rb')
            d = b''
            while not b'</script>' in d: d += f.read(0x1000)
            f.seek(len(d.split(b'</script>',1)[0]))
            d = f.read(0x100).decode('utf-8')
            assert 'let overhead' in d

            f.seek(int(re.search(r'let +overhead *= *parseInt\("(\d+)"\)',d)[1]))
            tf = TmpFile('.tar',path=o)
            xopen(tf.p,'wb').write(f.read())
            f.close()

            r = extract(tf.p,o,'TAR')
            tf.destroy()
            return r
        case 'PlayStation V2 Trophy File':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')
            assert f.read(4) == b'\xB2\x28\xC6\x0A' and f.readu32() == 1

            f.skip(8)
            c = f.readu32()
            f.seek(f.readu32() + 0x20)
            fs = []
            for _ in range(c):
                fs.append((f.read(0x20).rstrip(b'\0').decode('utf-8'),f.readu64(),f.readu64()))
                f.skip(0x10)

            for fe in fs:
                f.seek(fe[1])
                xopen(f'{o}/{fe[0]}','wb').write(f.readc(fe[2]))

            f.close()
            if fs: return
        case 'REDengine Archive':
            run(['wolvenkit.cli','extract',i,'-o',o,'-v','Quiet'])
            if listdir(o): return
        case 'REDengine W2ResourCe':
            run(['wolvenkit.cli','convert','s',i,'-o',o,'-v','Quiet'])
            if listdir(o): return
        case 'idTech 7 Resource':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'IDCL'

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
                xopen(fn,'wb').write(d)

            f.close()
            if fs: return
        case 'PlayStation BLS Update':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'SLB2'

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
                xopen(o + '/' + fe[2],'wb').write(f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Purple Moon Resource PRD+PRS':
            if db.print_try: print('Trying with custom extractor')
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
                xopen(fn,'wb').write(fd.readc(f.readu32()))

            f.close()
            fd.close()
            if listdir(o): return
        case 'Sonic PAC':
            run(['hedgearcpack',i,o,'-E'])
            if listdir(o): return
        case 'Sonic BINA':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i)

            if f.read(4) == b'BINA':
                f.skip(3)
                f._end = {b'L':'<',b'B':'>'}[f.read(1)]
                f.skip(8)
                assert f.read(4) == b'DATA'
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
                assert f.read(8) == b'\x00\x001BBINA'
                f.skip(4)
                do = f.pos
                to += do
                de = to
                te += to

            f.seek(to)
            fs = []
            while f.pos < te:
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
                xopen(f'{o}/{ix:02d}.bin','wb').write(f.readc(fs[ix+1] - fs[ix]))

            f.close()
            return
        case 'The Mummy Returns PAK':
            if db.print_try: print('Trying with custom extractor')
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
                assert htg in {0,1},f.pos
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
                xopen(o + '/' + (fn or 'StringTable.pak.sys'),'wb').write(f.readc(fe[1]))

            f.close()
            if fs: return
        case '-8 SysFile':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.skip(0x14)
            s1 = f.readu32()
            s2 = f.readu32()
            f.skip(8)
            open(o + '/0.png','wb').write(f.readc(s1))
            open(o + '/1.png','wb').write(f.readc(s2))

            f.close()
            return
        case 'Archer Maclean\'s Mercury PAQ':
            CRCC = b"________________________________________________0123456789_______ABCDEFGHIJKLMNOPQRSTUVWXYZ______ABCDEFGHIJKLMNOPQRSTUVWXYZ_____________________________________________________________________________________________________________________________________"
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,HashLib
            HL = HashLib.dl('archer_mac_mercury',db,fmt=lambda x:x.translate(CRCC),encoding='ascii')
            f = File(i,endian='<')
            assert f.readu32() in {0x7D1,0xFEED}

            c = f.readu32()
            f.skip(8)
            fs = []
            for _ in range(c):
                fs.append((f.readu32(),f.readu32(),f.readu32()))
                assert f.readu32() == fs[-1][1],f.pos - 0x10

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
                    fn = hex(fe[0])[2:].zfill(8).upper() + '.' + ex
                xopen(o + '/' + fn,'wb').write(d)

            f.close()
            if fs: return
        case 'THQ PAK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'kcap' and f.readu32() == 1

            f.skip(8)
            so = f.readu32()
            c = f.readu32()
            fs = []
            for _ in range(c): fs.append((f.readu32() + so,f.readu32(),f.readu32()))
            for fe in fs:
                f.seek(fe[0])
                fn = f.read0s().decode('ascii')
                f.seek(fe[1])
                xopen(o + '/' + fn,'wb').write(f.readc(fe[2]))

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

                open(o + '/$signature.txt','w',encoding='utf-8').write(js['version'])
                for x in js['blocks']:
                    assert len(x) == 1 and 'resources' in x
                    for fn in x['resources']:
                        assert len(fn) == 1 and 'name' in fn
                        fn = fn['name']
                        rfn = glob.glob(glob.escape(td.p + '/' + fn.replace(':','_').replace('>','_')) + '.*')
                        assert len(rfn) == 1
                        mv(rfn[0],o + '/' + fn.replace(':','').replace('>','/'))

                td.destroy()
                return
        case 'L.A. Noire BIG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i)

            f.seek(-4,2)
            f.seek(-f.readu32('<'),2)
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
                xopen(f'{o}/{fe[0]:08X}.{ex}','wb').write(d)

            f.close()
            if fs: return
        case 'Nintendo ASH0':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import decompress
            d = decompress(readfile(i),'ash0')
            xopen(o + '/' + tbasename(i),'wb').write(d)
            return
        case 'Super Mario Maker Level':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import decompress
            d = readfile(i).split(b'ASH0')[1:]
            assert len(d) == 4
            for ix,n in ((0,'thumbnail0.tnl'),(1,'course_data.cdt'),(2,'course_data_sub.cdt'),(3,'thumbnail1.tnl')):
                dd = decompress(b'ASH0' + d[ix],'ash0')
                xopen(o + '/' + n,'wb').write(dd)
            return
        case 'SDFTool SDF.bin':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decrypt
            f = File(i,endian='>')
            assert f.read(4) == b'SDF0'

            f.skip(4)
            c1 = f.readu32()
            assert f.reads8() < 0
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

            assert f.readu8() == 1 and f.readu16() == 0
            xopen(o + '/hash.bin','wb').write(f.readc(f.readu8() * 4))
            assert f.readu8() == 1 and f.readu16() == 0
            d = f.readc(f.readu8() * 4)
            d = decrypt(d,'rsa_inv_le',0xd0c57d605d21c23b91000de888121741c3e2b8ba476b81b25123275b6b5c008b6b10abb59d357dd2fed5fea988940b94adc2136bb45c93d992b7102a5988033b73f6386ef9cce6bbc6dab03ba6e90a25976ef305a087302660475011c5ee50b8d44e1cc081d61273913664e1810abb97b93c1a6c0e6ebd8862d92ed88e62a450cd050dd4e212285128b453ef48711b0be4a0fc43bb8403efd57eda741644ee4cf64bc85187e0ee22fd3c61e4670eb19d47c99a3c9827219f0d4f6743f9fa27375deedf30dd2c17b5a6cd05339c399f2986e9c8919038a70c4f5fc2a760763e128818d1bb1c79a8d8a05d4401ac3004e5f64913a43c8cad637e94d478b63a27d2760105fdeadc8ff71914aaa9b9da29f35d294d4c23638f7f6170ba5358bc127f72c78b6bc4ce746cd350647c61f32dbdfc6135c1db2ec7c2ab9d914ed9a79b46c1ee57692b5fda14c1f0c0597a3c39414d7b8c519144c93dc72ab08b1c7a7b8e651cefcb1b3291128b4136d05abfe33af3568a163c7a839be864bc5abf3ac735fa33bb1ca45953f8431ed9fff2df07f0fbb5a071a462340463fcdfe79f9dee85e297115e1e5d077c414b2bf8523802fc7fd32a40e77cf8be6e0a115aa2709ba2c1fe04fadae81db12d0c71d5020c10f6a62f5e35f4a3d8ec0d3bf3dd914482cc39fd4e221e2feb39e23e0ef408954ef638b2d75e210ba0b6a473d526fc17588b,
                                       3,r=2)
            assert d[:1] == b'\1'
            d = d[1:].split(b'\0',1)[1][::-1]
            xopen(o + '/signature.bin','wb').write(d)

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
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.readu8() == 0x3D and f.readu8() == 3

            v = f.readu16('>')
            if v > 0x0101: f.skip(2)
            while f:
                h = f.readu32()
                if not h: break
                d = f.readc(f.readu32() - 4)
                xopen(f'{o}/{h:08X}.{guess_ext(d)}','wb').write(d)

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
                lst = list(set(sum([open(lp + '/' + x,encoding='utf-8').read().split('\n') for x in listdir(lp)],[])))
                remove(*[lp + '/' + x for x in listdir(lp)])
                open(lp + '/all.list','w',encoding='utf-8').write('\n'.join(lst))

            run(['ree.unpacker','all',i,o],cwd=dirname(lp))
            if listdir(o): return
        case 'Capcom Encrypted MAME ROM':
            KEY = (0xB5,0x29,0x6C,0x96)

            if db.print_try: print('Trying with custom extractor')
            from lib.file import decrypt,decompress

            if '_d.' in basename(i).lower(): iv = 'natives/STM/streaming/Roms/DecryptionRom/' + basename(i).replace('_d','_D')
            else: iv = 'natives/STM/streaming/Roms/' + basename(i)

            if decompress(
                decompress(
                    decrypt(readfile(i),'capcom_mame',KEY,iv),
                    'lz4',no_size=True),
                'zip',o=o
            ): return
        case 'Smoking Car Productions Disk Cache':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            fs = []
            for _ in range(c):
                fs.append((f.read(12).rstrip(b'\0').decode('ascii'),f.readu32()*0x800,f.readu32()*0x800))
                assert f.readu16() in {0,1}
            for fe in fs:
                f.seek(fe[1])
                xopen(o + '/' + fe[0],'wb').write(f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Kamen Rider Atsume BIN':
            if db.print_try: print('Trying with custom extractor')
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
                xopen(f'{o}/{ix:02d}.{guess_ext(d)}','wb').write(d)

            f.close()
            if fs: return
        case 'Trinity OnePack':
            if db.print_try: print('Trying with custom extractor')
            assert exists(noext(i) + '.trpfs')
            db.get('trpfs.fbs')
            from lib.file import File,HashLib
            HL = HashLib.dl('pokemon',db)

            fd = File(noext(i) + '.trpfs',endian='<')
            assert fd.read(8) == b'ONEPACK\0'

            bo = fd.readu64()
            fd.seek(bo)
            fbuf = fd.read()

            from bin.PokeDocs.trpfs import TRPFS # type: ignore
            tfs = TRPFS.GetRootAs(fbuf)
            assert tfs.FileOffsetsLength() == tfs.FileHashesLength()
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
                xopen(o + '/' + HL.get(fe[1],f'$unk/{h:016X}.bin'),'wb').write(fd.readc(fs[ix + 1][0] - fe[0]))

            fd.close()
            if fs: return
        case 'Trinity PAK':
            if db.print_try: print('Trying with custom extractor')
            db.get('trpak.fbs')
            from lib.file import decompress,HashLib
            HL = HashLib.dl('pokemon',db)

            from bin.PokeDocs.trpak import TRPAK # type: ignore
            tpk = TRPAK.GetRootAs(readfile(i))
            assert tpk.FileEntryLength() == tpk.FileHashesLength()

            HL.wait()
            for ix in range(tpk.FileEntryLength()):
                fl = tpk.FileEntry(ix)
                h = tpk.FileHashes(ix)
                fn = HL.get(h,f'$unk/{h:016X}.bin')
                d = bytes(fl.ByteBuffer(dix) for dix in range(fl.ByteBufferLength()))
                xopen(o + '/' + fn,'wb').write(decompress(d,(0,'zlib','lz4','oodle','none')[fl.CompressType()],usize=fl.FileSize(),db=db))

            del tpk
            if listdir(o): return
        case 'Trinity GFLXPack':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,HashLib
            HL = HashLib.dl('pokemon',db)

            f = File(i,endian='<')
            assert f.read(8) == b'GFLXPACK'

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
                    xopen(o + '/' + fn,'wb').write(d)
                    ch[fe[4]] = fn

            f.close()
            if fs: return
        case 'Barbie: Riding Club OMF':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')
            assert f.read(4) == b'0MFS'

            f.seek(f.readu32())
            dc = f.readu32()
            fs = []
            mcs = []
            for _ in range(dc):
                n = f.readc(4).decode('ascii')
                assert n.isprintable()
                c = f.readu32()
                for _ in range(c):
                    fs.append((n,f.reads32(),f.readu32(),f.readu32()))
                    if n == 'mCTy': mcs.append(fs[-1][2])
            xc = f.readu32()
            xfs = [(f.readu32(),f.readu32()) for _ in range(xc)]

            nm = {}
            for m in mcs:
                f.seek(m)
                dc = f.readu32()
                for _ in range(dc):
                    n = f.readc(4).decode('ascii')
                    assert n.isprintable()
                    if not n in nm: nm[n] = {}
                    f.padc(2)
                    c = f.readu32()
                    for _ in range(c):
                        id = f.reads32()
                        nm[n][id] = f.readc(f.readu8()).decode('ascii')

            for fe in fs:
                if fe[0] == '0HDR':
                    try:
                        fn = fe[1].to_bytes(4,'big',signed=True).decode('ascii')
                        assert fn.isprintable()
                    except: fn = str(fe[1])
                elif fe[0] in nm and fe[1] in nm[fe[0]]: fn = fe[0] + '/' + nm[fe[0]][fe[1]]
                else: fn = f'${fe[0]}/{fe[1]}'
                fn += '.' + BARBIE_XMP.get(fe[0],fe[0])

                f.seek(fe[2])
                xopen(o + '/' + fn,'wb').write(f.readc(fe[3]))
            for ix,fe in enumerate(xfs):
                f.seek(fe[0])
                xopen(f'{o}/$unk/{ix:02d}.bin','wb').write(f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Barbie: Riding Club Cache':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i)

            bn = tbasename(i)
            while f:
                s = int(f.readc(12).rstrip())
                if bn: fn,bn = bn,None
                else:
                    fn = f.readc(34).rstrip().decode('ascii')
                    x = f.readc(6).rstrip().decode('ascii')
                    assert fn.isprintable() and x.isprintable()
                    fn = f'{x}/{fn}.{BARBIE_XMP.get(x,x)}'
                xopen(o + '/' + fn,'wb').write(f.readc(s))

            f.close()
            if not bn: return
        case 'PlayStation Encrypted SFM':
            if db.print_try: print('Trying with custom extractor')
            from Cryptodome.Cipher import AES
            from lib.file import File,decrypt

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
            assert f.read(4) == b'\xD2\x94\xA0\x18' and f.readu32() == 1
            f.skip(8)
            es,ec = f.readu64(),f.readu64()
            f.skip(0x60)
            nps = []
            for _ in range(ec):
                ep = f.pos + es
                while f.pos < ep:
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
                    try: assert dc.decode('utf-8').replace('\n','').replace('\r','').isprintable()
                    except: pass
                    else:
                        xopen(f'{o}/{tbasename(i)}.{extname(i)[2:]}','wb').write(dc)
                        return
        case 'Starsky & Hutch WAD':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,mask
            f = File(i,endian='<')
            f.padc(8)
            assert f.read(4) == b'WAD!' and f.readu32() == 4

            f.skip(8)
            xopen(o + '/$description.txt','wb').write(f.readc(0x80).rstrip(b'\0'))
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

                assert xi != 0x7E
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
                    assert n.isprintable()
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
                        assert (fe[0]+fe[1]) < f.size
                        f.seek(fe[1])
                    except:
                        print(f'{fo+ix-fddlt} ({fo}+{ix}-{fddlt}) / {len(fds)} @ {f.pos - 8}')
                        raise
                    xopen(f'{o}/{p}/{pns[fo+ix-nmdlt]}','wb').write(f.readc(fe[0]))

            f.close()
            if fds: return
        case 'Torque HHA':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(8) == b'\x4F\xF3\x2F\xAC\0\0\1\0'

            ss = f.readu32()
            c = f.readu32()
            f.skip(ss)
            fs = []
            for _ in range(c):
                fe = (0x10 + f.readu32(),0x10 + f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32())
                assert fe[2] in {0,1},f.pos - 0x10
                fs.append(fe)

            for fe in fs:
                f.seek(fe[0])
                fn = f.read0s().decode('utf-8') + '/'
                f.seek(fe[1])
                fn += f.read0s().decode('utf-8')
                f.seek(fe[3])
                xopen(o + '/' + fn,'wb').write(f.decompress(fe[5],('none','deflate')[fe[2]]))

            f.close()
            if fs: return

    return 1

def dnasoft_lzss_decrypt(i:bytes):
    from lib.file import decrypt
    KEY = b'\xe4\x81\xd4\xed\x17\xd4\x41\x62\xfa\x5c\xe9\x95\xae\x25\x2f\xd0\x98\xc0\x14\xce\xd9\xa7\x42\xf9\x9f\xfa\x8d\x38\x2b\x2a\x13\x6a\x26\xe0\xd9\x70\x8e\xab\xb5\xf1\x8e\x77\xed\x80\x9b\x1c\xaf\x51\x91\x8d\x68\x00\x61\xb2\x46\x3d'

    assert i[:4] == b'LZSS'
    rs = int.from_bytes(i[4:8],'little')
    return decrypt(i[8:8+rs+-rs%8],'blowfish_le',KEY)[:rs]
