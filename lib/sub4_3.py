from lib.main import *

def extract4_3(inp:str,out:str,t:str):
    run = db.run
    i = inp
    o = out

    match t:
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
            import zlib
            from lib.file import File
            f = File(i)
            assert f.read(4) == b'GRF\x05'

            v = (b'\x01FRG',b'GRF\x01').index(f.read(4))
            if v == 0: f._end = '>'
            elif v == 1: f._end = '<'

            f.seek(f.readu32())
            ft = File(zlib.decompress(f.read()),endian=f._end)
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
                d = f.read(max(fs[ix+1][1]-fe[1],fe[2])) # don't trust file size fe[2]
                assert fe[3] == 1,f'{fe[3]}: {d[:8].hex()}'
                xopen(o + '/' + fe[0],'wb').write(zlib.decompress(d))

            f.close()
            if fs: return
        case 'Artech DAT':
            if db.print_try: print('Trying with custom extractor')
            import zlib
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
                d = f.read(fe[2] or fe[1])
                if fe[2] and fe[2] != fe[1]: d = zlib.decompress(d)
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

    return 1
