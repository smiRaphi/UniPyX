from lib.main import *

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
            for ix in range(c):
                fn = f'{o}\\{ix:03d}.bin'
                fd.seek(f.readu32()*0x800)
                d = fd.read(f.readu32())
                us = f.readu32()
                if us and us != len(d):
                    assert d[:8] == b'\x00\xE9UCL\xFF\x01\x1A',ix
                    tf = TmpFile('.ucl')
                    open(tf.p,'wb').write(d[:0x1A] + d[0x1E:] + b'\0'*4) # strip unflagged crc and add EOF (?)
                    run(['uclpack','-d',tf,fn],print_try=False,print_out=True)
                    tf.destroy()
                    assert exists(fn) and getsize(fn) == us,ix
                else: open(fn,'wb').write(d)
                f.skip(4)

            f.close()
            fd.close()
            if c: return
        case 'Xenoblade Chronicles X DE ARH2':
            scr = db.get('xbxdetool')
            fl = dirname(scr) + '/Filelists'
            if exists(fl + '/hash_list.txt'):
                hl = [x.split('|',1)[1] for x in open(fl + '/hash_list.txt').read().strip('\r\n').split('\n') if x]
                remove(fl + '/hash_list.txt')
                for hf in listdir(fl):
                    hf = fl + '/' + hf
                    if isfile(hf) and hf.lower().endswith('.txt'):
                        hl += open(hf).read().strip('\r\n').split('\n')
                        remove(hf)
                hl.extend([
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
                open(fl + '/list.txt','w').write('\n'.join(sorted(list(set(hl)))))
                del hl

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
            from lib.file import File,crc_hash
            MP = {crc_hash(x[:1022].encode('ascii'),'tarzan'):x.replace(':','') for x in open('bin/tarzan.hsh').read().split('\n')}

            if db.print_try: print('Trying with custom extractor')
            f = File(i,endian='<')

            ep = f.size
            fs = []
            while f.pos < ep:
                fe = (f.readu32(),f.readu32(),f.readu32())
                if not fe[0]: break
                fs.append(fe)
                ep = min(ep,fe[1])

            for fe in fs:
                f.seek(fe[1])
                d = f.read(fe[2])
                if fe[0] in MP: fn = MP[fe[0]]
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
        case 'Nexar New PAC':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,inv,decompress
            f = File(i,endian='<')
            assert f.read(4) == b'PACu'

            c = f.readu32()
            fmtv = f.readu32()
            fmt = ('none','lzss','huffman','zlib','zlib_or_none','unknown 1','unknown 2','zstd_or_none')[fmtv]
            f.seek(f.size - 4)
            idxs = f.readu32()
            f.seek(f.size - 4 - idxs)
            inf = File(decompress(inv(f.read(idxs)),'huffman',usize=0x4C*c),endian=f._end)

            for _ in range(c):
                fn = inf.read(0x40).rstrip(b'\0').decode('shift-jis' if fmtv < 7 else 'utf-8')
                f.seek(inf.readu32())
                us,s = inf.readu32(),inf.readu32()
                if fmt == 'zlib_or_none': d = f.decompress(s,'zlib' if s != us else 'none')
                elif fmt == 'zstd_or_none': d = f.decompress(s,'zstd' if s != us else 'none')
                elif fmt in ('lzss','huffman'): d = f.decompress(s,fmt,usize=us)
                else: d = f.decompress(s,fmt)
                xopen(o + '/' + fn,'wb').write(d)

            f.close()
            del inf
            if c: return
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

    return 1
