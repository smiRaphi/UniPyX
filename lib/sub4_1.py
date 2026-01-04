from lib.main import *

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
            raise NotADirectoryError() # https://github.com/hoshsadiq/ps3theme-p3t-extract/blob/master/src/P3TExtractor/Extractor.php
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
                    try:
                        td = d.decode('cp1251')
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
