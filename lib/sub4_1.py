from lib.main import *
from lib.dldb import BDIR
from lib.sub4 import auracomp

def extract4_1(inp:str,out:str,t:str):
    run = db.run
    i = inp
    o = out

    def quickbms(scr,inf=i,ouf=o,print_try=True):
        scp = db.get(scr)
        if db.print_try and print_try: print('Trying with',scr)
        run(['quickbms','-Y',scp,inf,ouf],print_try=False)
        if listdir(ouf): return
        return 1

    match t:
        case '1941 Frozen Front Lang':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.skip(1)
            unk = f.readu16()
            c = f.readu16()
            fs = []
            for _ in range(c): fs.append(f.readu16()-(c*2+5))
            fs.append(None)
            f.skip(2)

            d = f.read()
            f.close()
            ob = []
            for ix in range(c): ob.append(d[fs[ix]:fs[ix+1]].decode({17:'latin-1',527:'utf-8',14:'ascii'}[unk]))

            open(o + '/' + tbasename(i) + '.txt','w',encoding='utf-8').write('\n\n'.join(ob))
            if fs: return
        case '1941 Frozen Front Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'STY0'
            offs = []
            for _ in range(2):
                for _ in range(f.readu8()): offs.append(f.readu32())

            f.seek(0)
            d = f.read()
            f.close()

            offs.append(None)
            for ix in range(len(offs)-1): open(o + f'/{ix}.bin','wb').write(d[offs[ix]:offs[ix+1]])

            if offs: return
        case 'PS3 Theme':
            raise NotImplementedError # https://github.com/hoshsadiq/ps3theme-p3t-extract/blob/master/src/P3TExtractor/Extractor.php
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            assert f.read(4) == b'P3TF'

            f.skip(4)
        case 'Peggle Data':
            if db.print_try: print('Trying with custom extractor')

            bn = basename(i)
            if (len(bn) == 2 and bn[0].isalpha() and bn[1].isdigit()) or (len(bn) == 1 and bn[0].isalpha() and getsize(i) == 0 and exists(bn + '0')):
                fi = dirname(i) + '/' + bn[0]
                assert exists(fi + '0'),"Missing first file"
                d = b''
                for ix in range(10):
                    if not exists(fi + str(ix)): break
                    d += open(fi + str(ix),'rb').read()
            else: d = open(i,'rb').read()

            from lib.file import File
            f = File(d,endian='>')

            if f.readu8(): f.skip(1)
            f.skip(1)

            c = 0
            while f:
                u1 = f.readu16()
                if u1:
                    f.skip(-2)
                    assert u1 in (1,2,4,6,9),f'{u1} @ {f.pos//32768}.{f.pos % 32768}'
                    open(f'{o}/{c}_extra.bin','wb').write(f.read(2+[None,0x10,0x1C,None,0x34,None,0x4C,None,None,0x70][u1]))
                    f.skip(2)

                f.skip(6)
                if not f: break
                da = f.read(f.readu16())
                open(f'{o}/{c}.{guess_ext(da)}','wb').write(da)
                c += 1

            if c: return
        case 'Air Adrenaline Data 1'|'Air Adrenaline Data 2':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            if t == 'Air Adrenaline Data 1':
                c = f.readu16()//2
                f.seek(0)
            elif t == 'Air Adrenaline Data 2': c = f.readu8()
            fs = [f.readu16()+f.tell() for _ in range(c+1)]

            for ix in range(c):
                d = f.read(fs[ix+1]-fs[ix])
                open(o + f'/{ix}.{guess_ext(d)}','wb').write(d)

            f.close()
            if fs: return
        case 'Karma Studios Lang':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            f.skip(8)
            ob = []
            while f: ob.append(f.read(f.readu8())[:-1].decode())
            f.close()

            if ob:
                open(o + '/' + tbasename(i) + '.txt','w',encoding='utf-8').write('\n\n'.join(ob))
                return
        case 'Cannons Tournament PAK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            hs = f.readu32()
            es = f.readu32()
            f.seek(hs)
            fs = [(f.read(0x18).rstrip(b'\0').decode('utf-8'),f.readu32(),f.readu32()) for _ in range(es//0x20)]

            for fe in fs:
                f.seek(fe[1])
                open(o + '/' + fe[0],'wb').write(f.read(fe[2]))
            f.close()

            if fs: return
        case 'Doom Database':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu16()
            ob = []
            for _ in range(c): ob.append(f'{f.readu16():03}: {f.read(6).hex(' ').upper()}')
            f.close()

            if ob:
                open(o + '/' + tbasename(i) + '.txt','w').write('\n\n'.join(ob))
                return
        case 'Doom Palettes':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()//0x20
            for ix in range(c): open(o + f'/{ix}.pal','wb').write(f.read(0x20))
            f.close()

            if c: return
        case 'MediaMobile PAK':
            if db.print_try: print('Trying with custom extractor')
            txt = re.compile(r'^[А-Яа-яЁё0-9\s.,!?"\'-—()]*$')
            from lib.file import File
            f = File(i,endian='>')

            c = f.readu32()
            fs = [f.readu32() for _ in range(c)]

            for ix in range(c):
                d = bytes(x ^ 0x53 for x in f.read(fs[ix]))
                if fs[ix] < 0xB0000:
                    try: td = d.decode('cp1251')
                    except: pass
                    else:
                        if td.isprintable() and txt.fullmatch(td):
                            open(o + f'/{ix}.txt','w',encoding='utf-8').write(td)
                            continue
                open(o + f'/{ix}.{guess_ext(d)}','wb').write(d)
            f.close()

            if c: return
        case 'Taiko no Tatsujin Data 1':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            c = f.readu32()//4
            f.seek(0)
            fs = [f.readu32() for _ in range(c)]

            for ix in range(c-1):
                d = f.read(fs[ix+1]-fs[ix])
                if not d: continue
                open(o + f'/{ix}.{guess_ext(d)}','wb').write(d)
            f.close()

            if c: return
        case 'Taiko no Tatsujin Data 2'|'Taiko no Tatsujin Data 3':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            if t == 'Taiko no Tatsujin Data 2': readf = f.readu32
            elif t == 'Taiko no Tatsujin Data 3': readf = f.readu16

            c = 0
            while f:
                d = f.read(readf())
                open(o + f'/{c}.{guess_ext(d)}','wb').write(d)
                c += 1
            f.close()

            if c: return
        case 'THQ Worms Resources':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu16()//2
            f.seek(0)
            fs = [f.readu16() for _ in range(c)]

            txt = False
            if f.size < 0xA000:
                try: td = f.read().decode('cp1252')
                except UnicodeDecodeError: pass
                else: txt = td.replace('\n','').replace('\r','').replace('\xA0','').isprintable()
            f.seek(fs[0])

            if txt:
                ob = []
                for ix in range(c-1): ob.append(f.read(fs[ix+1]-fs[ix]).decode('cp1252'))
                if ob: open(o + '/' + tbasename(i) + '.txt','w',encoding='utf-8').write('\n\n'.join(ob))
            else:
                for ix in range(c-1):
                    d = f.read(fs[ix+1]-fs[ix])[1:]
                    if 3 < len(d) < 0x1000:
                        try: td = d.decode('cp1252')
                        except UnicodeDecodeError: pass
                        else:
                            if td.replace('\n','').isprintable():
                                open(o + f'/{ix}.txt','w',encoding='utf-8').write(td)
                                continue
                    open(o + f'/{ix}.{guess_ext(d)}','wb').write(d)
            f.close()

            if c: return
        case 'THQ Worms UTF Strings':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            ob = []
            c = 0
            while f:
                c = f.readu16()
                if not c:
                    f.skip(-2)
                    break
                for _ in range(c): ob.append(f.read(f.readu16()).decode('utf-8'))
            while f:
                c1 = f.readu16()
                if c1:
                    f.skip(-2)
                    break
                c = f.readu16()
                for _ in range(c): ob.append(f.read(f.readu16()).decode('utf-8'))
            while f:
                c = f.readu16()
                f.skip(2)
                for _ in range(c-1): ob.append(f.read(f.readu16()).decode('utf-8'))
            f.close()

            if ob:
                open(o + '/' + tbasename(i) + '.txt','w',encoding='utf-8').write('\n\n'.join(ob))
                return
        case 'X-Files Resources':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')
            f.skip(4)

            c = f.readu8()
            fs = [(f.readu16('<'),f.readu32() + 5 + 10 * c,f.readu32()) for _ in range(c)]

            for fe in fs:
                f.seek(fe[1])
                d = f.read(fe[2])
                open(o + f'/{fe[0]:02}.{guess_ext(d)}','wb').write(d)
            f.close()

            if fs: return
        case 'Atari Masterpieces Resources':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')

            of = f.readu32()
            c = f.readu16()
            f.seek(of)
            fs = [(f.readu32(),f.readu32(),f.read(4).hex().upper()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[0]+4)
                d = f.read(fe[1]-4)
                e = guess_ext(d)
                open(o + f'/{fe[2]}.{e}','wb').write(d)
                if e == 'zlib':
                    d = zlib.decompress(d)
                    open(o + f'/{fe[2]}_ext.{guess_ext(d)}','wb').write(d)
            f.close()

            if fs: return
        case 'Atari Masterpieces Strings':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            fs = [f.readu32() for _ in range(c)]
            ob = []
            for fe in fs:
                f.seek(fe+4)
                ob.append(f.read0s().decode('cp1252'))
            f.close()

            if ob:
                open(o + '/' + tbasename(i) + '.txt','w',encoding='utf-8').write('\n\n'.join(ob))
                return
        case 'Atari Masterpieces VPXH': raise NotImplementedError
        case 'Torus Ashen PackFile':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'PMAN'
            c = f.readu32()
            f.seek(0x40)
            fs = []
            for _ in range(c):
                f.skip(4)
                fs.append((f.readu32(),f.readu32()))
                f.skip(4)

            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.read(fe[1])
                if d[:2] == b'ZL' and d[5] == 0x78 and not (d[5]<<8|d[6])%31: ext = 'zl'
                else: ext = 'bin'
                open(o + f'/{ix}.{ext}','wb').write(d)
                if ext == 'zl': open(o + f'/{ix}_ext.bin','wb').write(zlib.decompress(d[5:]))
            f.close()

            if fs: return
        case 'Torus Ashen ZLib':
            if db.print_try: print('Trying with custom extractor')
            import zlib

            f = open(i,'rb')
            assert f.read(2) == b'ZL'
            f.seek(5)
            open(o + '/' + tbasename(i),'wb').write(zlib.decompress(f.read()))
            f.close()
            return
        case 'Torus Ashen Strings':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            f.seek(4)
            d = f.read()[:-2]
            f.close()

            ob = [x.decode('utf-16le') for x in d.rsplit(b'\0\0')]

            if ob:
                open(o + '/' + tbasename(i) + '.txt','w',encoding='utf-8').write('\n\n'.join(ob))
                return
        case 'uBlock Origin Config Backup':
            if db.print_try: print('Trying with custom extractor')
            import json
            j = json.load(open(i,encoding='utf-8'))

            open(o + '/externalLists.txt','w',encoding='utf-8').write(j['userSettings']['externalLists'])
            open(o + '/importedLists.txt','w',encoding='utf-8').write('\n'.join(j['userSettings']['importedLists']))
            open(o + '/selectedFilterLists.txt','w',encoding='utf-8').write('\n'.join(j['selectedFilterLists']))
            open(o + '/whitelist.txt','w',encoding='utf-8').write('\n'.join(j['whitelist']))
            open(o + '/dynamicFiltering.txt','w',encoding='utf-8').write(j['dynamicFilteringString'])
            open(o + '/urlFiltering.txt','w',encoding='utf-8').write(j['urlFilteringString'])
            open(o + '/hostnameSwitches.txt','w',encoding='utf-8').write(j['hostnameSwitchesString'])
            open(o + '/userFilters.txt','w',encoding='utf-8').write(j['userFilters'])
            return
        case 'Stylus Config Export':
            if db.print_try: print('Trying with custom extractor')
            import json
            j = json.load(open(i,encoding='utf-8'))

            json.dump(j[0]['settings'],open(o + '/settings.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)

            for jo in j[1:]:
                n = f'{jo.get("customName",jo["name"])} v{jo["usercssData"]["version"].lstrip("v")}'
                if 'author' in jo and not '?' in jo['author']: n = f'{jo["author"]} - {n}'
                open(o + f'/{n}.css','w',encoding='utf-8').write(jo['sourceCode'])
                if 'vars' in jo['usercssData']: json.dump(jo['usercssData']['vars'],open(o + f'/{n}_vars.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
                if 'exclusions' in jo: open(o + f'/{n}_exclusions.txt','w',encoding='utf-8').write('\n'.join(jo['exclusions']))
            return
        case 'Violentmonkey Config Export':
            if db.print_try: print('Trying with custom extractor')
            import json
            j = json.load(open(i,encoding='utf-8'))

            open(o + '/customCSS.css','w',encoding='utf-8').write(j['settings']['customCSS'])
            open(o + f'/{j["settings"]["editorThemeName"]}.css','w',encoding='utf-8').write(j['settings']['editorTheme'])
            open(o + '/template.js','w',encoding='utf-8').write(j['settings']['scriptTemplate'])

            if 'values' in j:
                for bk,bv in j['values'].items():
                    for k,v in bv.items():
                        if v[0] == 's' and v[1] == '{' and v[-1] == '}': ext = 'json'
                        else: ext = 'txt'
                        xopen(o + f'/{bk.replace("-20"," ").replace("-0a"," ").strip()}/{k}.{ext}','w').write(v[1:])
        case 'StormCE Library VFS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.skip(0x18)
            fs = []
            while True:
                n = f.read(0x14)
                if not n[0]: break
                fs.append((n.rstrip(b'\0').decode('cp1252'),f.readu32(),f.readu32()))

            for fe in fs:
                f.seek(fe[2])
                open(o + '/' + fe[0],'wb').write(f.read(fe[1]))
            if fs: return
        case 'StormCE IIII':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')

            t = f.read(1).decode('ascii')
            assert f.read(3) == b'iii' and t in 'Yip'

            if t == 'Y':
                f.skip(8)
                open(o + '/' + tbasename(i),'wb').write(zlib.decompress(f.read()))
            elif t == 'p':
                f.skip(8)
                c = 0
                while f:
                    s = f.readu32()
                    if not s: break
                    open(o + f'/{c}.bin','wb').write(zlib.decompress(f.read(s)));c += 1
            elif t == 'i':
                s = f.readu32()
                f.skip(12)
                open(o + '/' + tbasename(i),'wb').write(zlib.decompress(f.read(s)))
                d = f.read()
                if d: open(o + '/trailer.bin','wb').write(d)
            return
        case 'HMM Encrypted Snapshot':
            raise NotImplementedError
            if db.print_try: print('Trying with custom extractor')
            import zipfile
            from lib.file import File
            try:
                from Cryptodome.PublicKey import RSA # type: ignore
                from Cryptodome.Cipher import PKCS1_v1_5 # type: ignore
            except ImportError:
                from Crypto.PublicKey import RSA # type: ignore
                from Crypto.Cipher import PKCS1_v1_5 # type: ignore

            rsa = RSA.construct((0xd597f61ca364a25af50832a5e18e855a426532ee9210729cd6555394736da2dd52269c2a096f622a4dedf3498e1a1b2fe107366445f6234c8a9912e6727092017a019dec984e5136c935a3d67238889bf5c7c3d358f88c6439db9635e3eab0088b36c6a08803c7fc6699f20e0a221a4b973b0360869c81eefb22c39731b98015,
                                 0x10001))

            f = File(i,endian='<')
            key = PKCS1_v1_5.new()
        case 'JDownloader2 Encrypted Subconfig'|'JDownloader2 Encrypted Accounts':
            if db.print_try: print('Trying with custom extractor')
            try: from Cryptodome.Cipher import AES # type: ignore
            except ImportError: from Crypto.Cipher import AES # type: ignore

            if t == 'JDownloader2 Encrypted Subconfig':k = b'\x01\x02\x11\x01\x01T\x01\x01\x01\x01\x12\x01\x01\x01"\x01'
            elif t == 'JDownloader2 Encrypted Accounts':k = b'\x01\x06\x04\x05\x02\x07\x04\x03\x0c=\x0eK\xfe\xf9\xd4!'

            d = open(i,'rb').read()
            d = AES.new(k,AES.MODE_CBC,iv=k).decrypt(d)
            if d.strip()[:1] != b'{': return 1
            open(o + '/' + tbasename(i) + '.json','wb').write(d[:-d[-1]])
            return
        case 'Azito 3D Pack File':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(0x10) == b'PACK_FILE\0\0\0\0\0\0\0'
            c = f.readu32()
            for ix in range(c):
                d = f.read(f.readu32())

                if d[0] in (0x11,0x40):
                    tf = TmpFile()
                    open(tf.p,'wb').write(d)
                    of = o + f'\\{ix}.bin'
                    run(['lzx','-d',tf.p,of],print_try=False)
                    if exists(of) and getsize(of):
                        tg = open(of,'rb').read(4)
                        try: tg = tg.decode('ascii')
                        except: pass
                        else:
                            if tg.isalpha(): mv(of,o + f'/{ix}.{tg}')
                    else: mv(tf.p,of)
                    tf.destroy()
                else: open(o + f'/{ix}.bin','wb').write(d)
            if c: return
        case 'Azito 3D Pack Message':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(0x10) == b'PACK_MESSAGE\0\0\0\0'
            ob = []
            c = f.readu32()
            for _ in range(c): ob.append(f.read(f.readu32()).rstrip(b'\0').decode('shift-jis'))

            if ob:
                open(o + '/' + tbasename(i) + '.txt','w',encoding='utf-8').write('\n\n'.join(ob))
                return
        case 'Nintendo Data ARChive':
            db.get('darc')
            class COpen:
                def __init__(self): pass
                def __call__(self,p,m):
                    if m != 'rb': return open(p,m)
                    self.f = open(p,m)
                    self.seek = self.f.seek
                    self.tell = self.f.tell
                    return self
                def read(self,n=None):
                    p = self.tell()
                    d = self.f.read(n)
                    if (n == 4 and p == 0) or (n == 2 and p == 4): d = d.decode('latin-1')
                    return d
                def close(self): self.f.close()

            if db.print_try: print('Trying with darc')
            import bin.darc as darc # type: ignore
            darc.xrange = range
            darc.print = lambda *a: None
            darc.open = COpen()

            d = darc.Darc.load(i)
            d.extract(o)
            darc.open.close()

            if listdir(o): return
        case 'Azada Wizard':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')

            assert f.read(4) == b'WZD '
            f.seek(12)
            open(o + '/' + tbasename(i) + '.txt','wb').write(f.read())
            return
        case 'Noita Wizard pAK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.skip(4)
            c = f.readu32()
            f.skip(8)
            fs = [(f.readu32(),f.readu32(),f.read(f.readu32()).decode()) for _ in range(c)]

            for fe in fs:
                f.seek(fe[0])
                xopen(o + '/' + fe[2],'wb').write(f.read(fe[1]))
            if fs: return
        case 'Fox Engine QAR'|'Fox Engine FPK'|'Fox Engine PFTXS':
            if t == 'Fox Engine QAR': ext = 'dat'
            elif t == 'Fox Engine FPK':
                f = open(i,'rb')
                f.seek(6)
                if f.read(1) == b'd': ext = 'fpkd'
                else: ext = 'fpk'
                f.close()
            elif t == 'Fox Engine PFTXS': ext = 'pftxs'

            tf = TmpFile(suf='.' + ext,path=o)
            tf.link(i)
            run(['gzstool',tf])
            tf.destroy()
            tfp = tf.p.rsplit('.',1)[0] + '_' + ext
            if exists(tfp) and isdir(tfp) and listdir(tfp) and exists(tf.p + '.xml') and getsize(tf.p + '.xml'):
                remove(tf.p + '.xml')
                while True:
                    try: copydir(tfp,o,True)
                    except PermissionError: sleep(0.1)
                    else: break
                return
        case 'Fox Engine Console QAR':
            tf = TmpFile(suf='.dat',path=o)
            tf.link(i)
            run(['mgsv_qar_tool',tf,'-e2'])
            tf.destroy()
            if exists(tf.p[:-4]) and isdir(tf.p[:-4]) and listdir(tf.p[:-4]) and exists(tf.p[:-3] + 'inf'):
                remove(tf.p[:-3] + 'inf')
                while True:
                    try: copydir(tf.p[:-4],o,True)
                    except PermissionError: sleep(0.1)
                    else: break
                return
        case 'Deathloop Resource':
            from lib.file import File
            f = File(i,endian='>')
            ft = f.readu8()
            assert f.read(3) == b'SER'

            if ft == 4:
                if f.readu16() == 3: mi = i
                else:
                    inf = dirname(i) + '\\master_resources.index'
                    mi = dirname(i) + '/master.index'
            elif ft == 5:
                inf = i
                mi = dirname(i) + '/master.index'
            else: raise NotImplementedError(ft)
            f.close()

            rst = []
            if exists(mi):
                f = File(mi,endian='<')
                if f.read(6) == b'\x04SER\0\x03':
                    inf = dirname(i) + '\\' + f.read(f.readu32()).decode('ascii')
                    c = f.readu16('>')
                    for ix in range(c): rst.append((ix,f.read(f.readu32()).decode('ascii')))
                f.close()
            if not exists(inf): return 1

            sd,xt = open(db.get('deathloop'),encoding='utf-8').read().split('\nstartfunction BUILD_ARCHIVE_NUM\n')
            if not rst: rst = re.findall(r'putarray 0 +(\d+) +([^\n]+)',xt)

            if db.print_try: print('Trying with deathloop')
            tf = TmpFile('.bms')
            open(tf.p,'w',encoding='utf-8').write(sd.replace('\n    get ARCHIVENUM short\n','\n    get DUMMY2 long\n    get ARCHIVENUM short\n') + '\nstartfunction BUILD_ARCHIVE_NUM\n' + '\n'.join(f'putarray 0 {x[0]} {x[1]}' for x in rst) + '\nendfunction\n')
            tfi = TmpFile('.index',path=dirname(i))
            tfi.link(inf)
            run(['quickbms','-Y',tf,tfi,o],print_try=False)
            tfi.destroy()
            tf.destroy()

            if listdir(o): return
        case 'LMPK':
            if db.print_try: print('Trying with custom extractor')
            import zlib

            f = open(i,'rb')
            assert f.read(4) == b'LMPK'
            f.seek(8)
            d = zlib.decompress(f.read())
            f.close()

            try: e = d[:4].decode('ascii').lower()
            except UnicodeDecodeError: e = 'bin'
            else:
                if not isvalid(e):
                    if d[:5] == b'<?xml': e = 'xml'
                    else: e = 'bin'
            open(o + '/' + tbasename(i) + '.' + e,'wb').write(d)
            return
        case 'BCH':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            T0S = 8 + 4*5 + 4*7 + 4
            T1S = 8 + 4*6 + 4*8 + 4
            FMTS = (
                ("rgba8888",32),
                ("rgb888",24),
                ("rgba5551",16),
                ("rgb565",16),
                ("rgba4444",16),
                ("la88",16),
                ("hl88",16),
                ("l8",8),
                ("a8",8),
                ("la44",8),
                ("l4",4),
                ("a4",4),
                ("etc1",4),
                ("etc1_a4",8),
            )

            assert f.read(4) == b'BCH\0'
            f.skip(4)

            soff0 = f.readu32()
            f.skip(-4)
            if soff0 in (T0S,T0S-4): typ = 0
            elif soff0 == T1S: typ = 1

            seco = [f.readu32() for _ in range(4 if typ == 0 else 5)]
            f.skip(4)
            sec = [(seco[ix],f.readu32()) for ix in range(len(seco))]

            f.seek(sec[0][0])
            maps = [(f.readu32()+sec[0][0],f.readu32(),f.readu32()+sec[0][0]) for _ in range(15)]

            xall = True
            for ix,m in enumerate(maps):
                if not m[1]: continue

                f.seek(m[0])
                offs = [f.readu32()+sec[0][0] for _ in range(m[1])]
                f.seek(m[2]+12)
                nmso = {}
                for nix in range(m[1]):
                    f.skip(8)
                    nmso[offs[nix]] = f.readu32()+sec[1][0]

                if ix == 1:
                    xall = False
                    for off in offs:
                        f.seek(nmso[off])
                        n = f.read0s().decode()
                        f.seek(off)
                        xopen(f'{o}/material/{n}.bin','wb').write(f.read(0x174))
                elif ix == 2:
                    fs = []
                    for off in offs:
                        f.seek(off)
                        fe = [f.readu32()+sec[0][0],f.readu32()]
                        f.skip(0x20)
                        fs.append(fe + [f.readu32()+sec[1][0]])
                    for fe in fs:
                        f.seek(fe[2])
                        n = f.read0s().decode()
                        f.seek(fe[0])
                        xopen(o + f'/shader/{n}.shbin','wb').write(f.read(fe[1]))
                elif ix == 3:
                    for off in offs:
                        f.seek(off)
                        ucmds = [(f.readu32()+sec[2][0],f.readu32()) for _ in range(3)]
                        fmt = f.readu8()
                        mips = f.readu8()
                        f.skip(2)
                        noff = f.readu32()
                        f.seek(sec[1][0]+noff)
                        nb1 = f'{o}/texture/{f.read0s().decode()}'

                        w = h = 0
                        texs = set()
                        for csoff,csc in ucmds:
                            f.seek(csoff)
                            cmds = [f.readu32() for _ in range(csc)]

                            k = 0
                            while k + 1 < csc:
                                cmd = cmds[k+1]
                                addr = cmd & 0xFFFF
                                size = ((cmd >> 20) & 0xFF) + 2
                                size += -size % 2
                                assert (k+size) <= csc

                                v = cmds[k]
                                if addr in (0x82,0x92,0x9a): w,h = v >> 16,v & 0xFFFF
                                elif addr in (0x8e,0x96,0x9e): assert v == fmt
                                elif addr in (0x85,0x86,0x87,0x88,0x89,0x8a,0x95,0x9d): texs.add(v)

                                k += size
                        assert texs and w and h
                        nb2 = f'_{w}x{h}.{FMTS[fmt][0]}'
                        siz = 0
                        for _ in range(mips):
                            siz += (w * h * FMTS[fmt][1]) // 8
                            w >>= 1
                            h >>= 1
                            if w < 1: w = 1
                            if h < 1: h = 1

                        for tix,ro in enumerate(sorted(list(texs))):
                            if typ == 1 and fmt in (10,11) and ro < sec[4][1]: ro += sec[4][0]
                            else: ro += sec[3][0]

                            f.seek(ro)
                            xopen(nb1 + (f'_{tix}' if len(texs) > 1 else '') + nb2,'wb').write(f.read(siz))
                elif ix == 6:
                    xall = False
                    for off in offs:
                        f.seek(nmso[off])
                        n = f.read0s().decode()
                        f.seek(off)
                        xopen(f'{o}/camera/{n}.bin','wb').write(f.read(0x58))
                else: xall = False

            fs = rldir(o)
            if not xall:
                if sec[3][1]:
                    f.seek(sec[3][0])
                    open(o + '/RAW.bin','wb').write(f.read(sec[3][1]))
                if typ == 1 and sec[3] != sec[4] and sec[4][1]:
                    f.seek(sec[4][0])
                    open(o + '/RAW_EXT.bin','wb').write(f.read(sec[4][1]))
            f.close()

            if fs: return
        case 'Nintendo 3DS SMDH':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'SMDH' and f.readu32() == 0

            for l in ('JP','EN','FR','DE','IT','ES','CN','KR','NL','PT','RU','TW','U1','U2','U3','U4'):
                n,d,p = f.read(0x80).rsplit(b'\0\0')[0],f.read(0x100).rsplit(b'\0\0')[0],f.read(0x80).rsplit(b'\0\0')[0]
                if not (n+d+p): continue
                open(o + f'/name_{l}.txt','w',encoding='utf-8').write(f'Name: {n.decode('utf-16le')}\nDescription: {d.decode("utf-16le")}\nPublisher: {p.decode("utf-16le")}\n')

            s = open(o + '/settings.txt','w',encoding='utf-8')
            s.write('Age Ratings:\n')
            for p in ('CERO','ESRB','UNK1','USK','PEGI GEN','UNK2','PEGI PRT','PEGI BBFC','COB','GRB','CGSRR','UNK3','UNK4','UNK5','UNK6','UNK7'):
                v = f.readu8()
                if p[:3] != 'UNK' or v: s.write(f'{p:4}: {v}\n')
            s.write('\nRegions:\n')
            rf = f.readu32()
            if rf == 0x7fffffff: s.write('Region Free\n')
            else:
                if rf & 1: s.write('Japan\n')
                if rf & 2: s.write('North America\n')
                if rf & 4 and rf & 8: s.write('Europe (EU+AU)\n')
                elif rf & 4: s.write('Europe (Exclusive)\n')
                elif rf & 8: s.write('Australia (Exclusive)\n')
                if rf & 0x10: s.write('China\n')
                if rf & 0x20: s.write('Korea\n')
                if rf & 0x40: s.write('Taiwan\n')
            s.write(f'\nMatch Maker ID: {f.read(4).hex(' ').upper()}\nMatch Maker BIT ID: {f.read(8).hex(" ").upper()}\n\nFlags:\n')
            fv = f.readu32()
            for ix,n in enumerate(('Visible','Auto-Boot','3D','Require CTR EULA','Autosave','Extended Banner','Region Rating Required','Uses Savedata','Record Usage','Disable SD Savedata','New 3DS Exclusive','Parental Control Restriction')):
                s.write(f'{n}: {bool(fv & (1 << ix))}\n')
            evm = f.readu8()
            s.write(f'\nEULA Version: {f.readu8()}.{evm}\nOptimal Animation Default Frame: {f.readfloat()}\nCEC ID: {f.read(4).hex(" ").upper()}\n')
            s.close()

            f.skip(8)
            open(o + '/small_24x24.rgb565','wb').write(f.read(0x480))
            open(o + '/large_48x48.rgb565','wb').write(f.read(0x1200))
            f.close()
            return
        case 'Nintendo CTR Banner':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'CBMD'
            f.skip(4)

            coffs = [(ix,off) for ix,off in enumerate([f.readu32() for _ in range(14)]) if off]
            f.seek(0x84)
            bwo = f.readu32()
            if bwo: coffs.append((0,bwo))
            else: coffs.append((0,f.size))

            for ix,fe in enumerate(coffs[:-1]):
                iix,off = fe
                f.seek(off)
                d = auracomp(f.read(coffs[ix+1][1]-off),None,'nintendo-lz11')
                assert d
                open(o + '/' + ('common','eur-en','eur-fr','eur-de','eur-it','eur-es','eur-nl','eur-pt','eur-ru','jpn-jp','usa-en','usa-es','usa-pt')[iix] + '.bcmdl','wb').write(d)

            if bwo:
                f.seek(bwo)
                assert f.read(4) == b'CWAV'
                f.skip(8)
                s = f.readu32()
                f.seek(bwo)
                open(o + '/sound.bcwav','wb').write(f.read(s))

            if listdir(o): return
        case 'DBS Database':
            if db.print_try: print('Trying with custom extractor')
            import json
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'DBS\0'
            hds = tuple(list(f.read(4)))

            c = f.readu64()
            f.skip(4)
            sigo = f.readu32()
            do = f.readu32()
            so = f.readu32()

            f.seek(sigo)
            sig = tuple([f.readu16() for _ in range((do-sigo)//2)])
            SIGS = {
                (1,4,1,1):{
                    (1,4, 0, 0, 0, 0, 0, 0):('x','s','i',1),
                },
                (1,5,1,1):{
                    (1,4, 0, 0, 0, 0, 0, 0):('x','s'),
                },
                (1,6,1,1):{
                    (2,4, 8, 0, 0, 0, 0, 0):('x','s','s',1),
                    (3,8,12,16, 0, 0, 0, 0):('x','x','s','s','s','t8'),
                    (4,4, 8,12,16, 0, 0, 0):('x','s','s','s','s','i'),
                    (5,0, 4, 8,12,16, 0, 0):('s','s','s','s','s'),
                    (7,4, 8,12,16,20,24,28):('s','s','s','s','s'),
                },
                (1,6,1,2):{
                    (4,4, 8,12,16, 0, 0, 0):('x','s','s','s','s','x','i','i','x'),
                    (4,0, 4, 8,12, 0, 0, 0):('s','s','s','s','i','i','i','h','h'),
                },
            }
            if hds in SIGS and sig in SIGS[hds]:
                fmt = SIGS[hds][sig]
                if fmt[-1] == 1:
                    fmt = fmt[:-1]
                    b = {}
                else: b = []
            else: raise NotImplementedError(' '.join(str(h).zfill(2) for h in hds) + '|' + ' '.join(str(s).zfill(2) for s in sig))

            ln = sum([int(x[1:]) if x[0] == 't' else (2 if x == 'h' else 4) for x in fmt])*c
            assert (so-do) == ln

            def reads():
                p = f.pos+4
                f.seek(f.readu32())

                s = []
                utf16 = False
                while True:
                    b = f.read(2 if utf16 else 1)
                    if b in b'\0\0': break
                    if not utf16 and not (32 <= b[0] <= 126):
                        utf16 = True
                        b += f.read(1)
                    s.append(b)
                f.seek(p)

                s = b''.join(s)
                if utf16 and len(s) % 2: s += b'\0'
                return s.decode('utf-16-le' if utf16 else 'ascii')

            f.seek(do)
            for _ in range(c):
                v = []
                for fm in fmt:
                    if   fm == 'x': f.skip(4)
                    elif fm == 's': v.append(reads())
                    elif fm == 'i': v.append(f.readu32())
                    elif fm == 'h': v.append(f.readu16())
                    elif fm[0] == 't': v.append(list(f.read(int(fm[1:]))))
                if type(b) == dict: b[v[0]] = v[1]
                else: b.append(v)

            if b:
                json.dump(b,open(o + f'/{tbasename(i)}.json','w',encoding='utf-8'),indent=4,ensure_ascii=False)
                return
        case 'Dance Layout Script':
            if db.print_try: print('Trying with custom extractor')
            import json
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'DMR\0'
            f.skip(8)

            ob = {}
            while f:
                f.skip(8)
                k = f.read(0x20).rstrip(b'\0').decode('utf-8')
                tp = f.read(0x10).rstrip(b'\0').decode('utf-8')
                c = f.readu32()
                ob[k] = []
                for _ in range(c):
                    if tp == 'int': ob[k].append(f.reads32())
                    elif tp == 'float': ob[k].append(f.readfloat())
                    elif tp == 'string': ob[k].append(f.read(0x80).rstrip(b'\0').decode('utf-8'))
                    elif tp == 'wstring': ob[k].append(f.read(0x80).rsplit(b'\0\0')[0].decode('utf-16-le'))

            if ob:
                json.dump(ob,open(o + f'/{tbasename(i)}.json','w',encoding='utf-8'),indent=4,ensure_ascii=False)
                return
        case 'ID String0 Count8 Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu8()
            ob = []
            for _ in range(c): ob.append(f'{f.readu8()}: ' + f.read0s().decode('ascii'))
            if ob:
                open(o + f'/{tbasename(i)}.txt','w').write('\n'.join(ob))
                return
        case 'EBAB Animation Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            c = f.readu16()

            fs = []
            for _ in range(c):
                n = f.read0s().decode()
                if f.pos%2: f.skip(1)
                fs.append((n,f.readu16()*0x20))
            for fe in fs: open(o + f'/{fe[0]}.bin','wb').write(f.read(fe[1]))
            if fs: return
        case 'STXT Language Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'STXT'

            f.skip(6)
            sc = f.readu16()
            f.skip(8)
            c = f.readu32()
            f.seek(f.readu32())

            fs = [(f.read(4),[f.readu32() for _ in range(sc)]) for _ in range(c)]
            of = open(o + f'/{tbasename(i)}.txt','w',encoding='utf-8')
            for fe in fs:
                of.write(f'{fe[0].hex(' ').upper()}:\n')
                for off in fe[1]:
                    f.seek(off)
                    of.write(f.read0s().decode('utf-8') + '\n')
                of.write('\n')

            of.close()
            if fs: return
        case 'Adventure Time VOLume':
            if db.print_try: print("Trying with custom extractor")
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'\xCB\x32\x3D\xB5'
            f.skip(0x10)

            c = f.readu32()
            f.seek(f.readu32())
            fs = [(f.read(4),f.readu32(),f.readu64(),f.readu32()) for _ in range(c)]
            for fe in fs:
                if fe[1]:
                    f.seek(fe[1])
                    n = f.read0s().decode()
                else: n = ''
                if not n: n = fe[0].hex().upper() + '.bin'
                f.seek(fe[2])
                open(o + '/' + n,'wb').write(f.read(fe[3]))
            if fs: return
        case '0Size24 Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            f.seek(1)
            open(o + '/' + basename(i),'wb').write(f.read(f.readu24()))
            return
        case 'WayForward PAK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            d = f.readu32()+0x40
            c = f.readu32()
            fs = []
            for _ in range(c):
                f.skip(0x10)
                fs.append((f.readu32()+d,f.readu32(),f.read0s().decode().replace(':','/')))
                f.skip(-f.pos%8)
            for fe in fs:
                f.seek(fe[0])
                xopen(o + '/' + fe[2],'wb').write(f.read(fe[1]))
            if fs: return
        case 'Reverse Computer Screen':
            of = o + '/' + tbasename(i)
            if not of.endswith('.scr'): of += '.scr'
            run(['rcs','-f','-d',i,of])
            if exists(of) and getsize(of): return
        case 'Encrypted Arsenal MTC+MDF':
            DBP = BDIR + '/bin/mtcmdf.bdb'
            if not exists(DBP):
                import zipfile,json
                from io import BytesIO

                dbf = open(DBP,'wb')
                zf = zipfile.ZipFile(BytesIO(db.c.get('https://github.com/Infinest/Gimmick-ROM-extractor/releases/download/1.21/Gimmick_ROM_extractor.zip',follow_redirects=True).content))
                for h,p in (('C90971742F35300A94797EC76208462C024FE0C938356B216463FB61ACF6FB4F','config.json'),
                            ('1D3CE6FCD673E0349C07494687796ADDDF08A30A53B78672C884907B980F47A2','alternate_configs/Streets of Kamurocho (Streets of Rage 2)/config.json'),
                            ('FE8314DF62A13B63990995722F6F9A083AA5B30A4971E3297B49C241A44241F5','alternate_configs/Abarenbo Tengu & Zombie Nation/config.json'),
                            ('0'*64,'alternate_configs/F-117A Stealth Fighter/config.json')):
                    dbf.write(bytes.fromhex(h))
                    dbf.write(json.loads(zf.read(p).replace(b',\n}',b'}'))['AES_KEY'].encode('ascii').ljust(16,b'\0'))
                dbf.close()
            dbf = open(DBP,'rb')
            bdb = {dbf.read(32):dbf.read(16) for _ in range(4)}
            dbf.close()

            if db.print_try: print('Trying with custom extractor')
            import hashlib
            fd = open(noext(i) + '.mdf','rb')
            hsh = hashlib.sha256(fd.read(0x1000)).digest()
            assert hsh in bdb
            key = bdb[hsh]

            try: from Crypto.Cipher import AES # type: ignore
            except ImportError: from Cryptodome.Cipher import AES # type: ignore
            from lib.file import File
            f = File(i,endian='<')

            f.skip(8)
            c = f.readu64()
            f.skip(c*4)
            fs = []
            for _ in range(c):
                f.skip(8)
                fs.append(f.read(4).hex().upper())
                f.skip(4)

            aes = AES.new(key,AES.MODE_CBC,b'\0'*16)
            for ix in range(c):
                f.skip(8)
                fd.seek(f.readu32())
                es = f.readu32()
                s = f.readu64()
                f.skip(8)
                d = aes.decrypt(fd.read(es))[:s]

                open(o + f'/{ix}_{fs[ix]}.{"gen" if len(d)>0x200 and d[0x100:0x113] == b"SEGA GENESIS    (C)" else guess_ext(d)}','wb').write(d)
            if fs: return
        case 'Dotemu INF+BIN':
            run(['infbinrepacker','-e','-if',i,'-bf',noext(i) + '.bin','-od',o])
            if exists(o + '/uncompressed') and listdir(o + '/uncompressed'):
                copydir(o + '/uncompressed',o,True,reni=True)
                return

    return 1
