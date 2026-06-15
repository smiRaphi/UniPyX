from lib.main import *

def extract4_5(inp:str,out:str,t:str):
    i,o = inp,out

    match t:
        case 'Retro Engine RSDKv3':
            K1,K2 = b"4RaS9D7KaEbxcp2o5r6t",b"3tRaUxLmEaSn"
            db.try_custom()
            from lib.crypto import decrypt
            from lib.file import File
            f = File(i,endian='<')

            hs = f.readu32()
            dc = f.readu16()
            ds = [(decrypt(f.read(f.readu8()),'inv_len').decode('utf-8'),hs + f.readu32()) for _ in range(dc)]
            ds.append((0,f.size))
            for ix,de in enumerate(ds[:-1]):
                f.seek(de[1])
                xof = ds[ix+1][1]
                while f < xof:
                    fn = decrypt(f.read(f.readu8()),'inv').decode('utf-8')
                    writefile(o + '/' + de[0] + fn,decrypt(f.readc(f.readu32()),'rsdk3',K1,K2))

            f.close()
            if de: return
        case 'Retro Engine RSDKv4':
            KEY = (0xAAAAAAAB,0x24924925)

            db.try_custom()
            from lib.crypto import decrypt,HashLib
            hl = HashLib.dl('rsdk',db)
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(6) == b'RSDKvB')

            c = f.readu16()
            fs = []
            for _ in range(c):
                fe = [f.readu128(),f.readu32()]
                sz = f.readu32()
                fs.append((*fe,sz & 0x7FFFFFFF,sz & 0x80000000))

            hl.wait()
            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                if fe[3]: d = decrypt(d,'rsdk4',*KEY)
                if fe[0] in hl: fn = hl[fe[0]]
                else:
                    ex = guess_ext(d)
                    fn = f'$unk/{fe[0]:032X}.{ex}'
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'Retro Engine RSDKv5':
            db.try_custom()
            from lib.crypto import decrypt,HashLib
            hl = HashLib.dl('rsdk',db)
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(5) == b'RSDKv' and f.read(1) in b'345')

            c = f.readu16()
            fs = []
            for _ in range(c):
                fe = [f.readu128(),f.readu32()]
                sz = f.readu32()
                fs.append((*fe,sz & 0x7FFFFFFF,sz & 0x80000000))

            hl.wait()
            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                if fe[0] in hl:
                    fn = hl[fe[0]]
                    if fe[3]: d = decrypt(d,'rsdk5',fn)
                else:
                    fn = f'$unk/{fe[0]:032X}.'
                    if fe[3]: fn += 'enc'
                    else: fn += guess_ext(d)
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'Europe Racer IND+IMG':
            db.try_custom()
            from lib.file import File,decompress,iszl
            f = File(i,endian='<')
            fd = File(noext(i) + '.img')

            c = f.readu16()
            if (c*0x18) == f.left: fs = [(f.readc(0x14).rstrip(b'\0').decode('ascii'),f.readu32()) for _ in range(c)]
            elif (c*4) == f.left: fs = [(0,f.readu32()) for _ in range(c)]
            else: raise ValueError('Unknown format')
            fs.sort(key=lambda x:x[1])
            fs.append((0,fd.size))

            for ix,fe in enumerate(fs[:-1]):
                fd.seek(fe[1])
                d = fd.readc(fs[ix+1][1]-fe[1])
                if iszl(d[4:]): d = decompress(d[4:],'zlib',usize=int.from_bytes(d[:4],'little'))
                if fe[0]: fn = fe[0]
                else: fn = f'{ix:03d}.{guess_ext(d)}'
                writefile(o + '/' + fn,d)

            f.close()
            fd.close()
            if fs: return
        case 'LucasArts APak':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            asrt(f.read(4) == b'APak')

            f.skip(4)
            c = f.readu32()
            f.seek(0x18)
            sof = 0x50 + f.readu32()
            to1 = sof + f.readu32()
            to2 = f.readu32()
            dof = f.readu32()
            f.skip(4)
            oc = f.readu32()

            f.seek(to2)
            ofs = {}
            for _ in range(oc):
                id = f.readu32()
                ofs[id] = dof + f.readu32()
                f.padc(8)

            f.seek(to1)
            fs = []
            for _ in range(c):
                f.skip(0x14)
                so = sof + f.readu32()
                f.skip(0x10)
                fs.append((so,f.readu32(),f.readu32()))
                f.skip(0x10)

            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                fn = f.read0s('utf-8')
                if ix in ofs:
                    f.seek(ofs[ix])
                    asrt(fe[1] == fe[2])
                    d = f.readc(fe[2])
                else:
                    asrt(fe[1] == fe[2] == 0,f'{to1+ix*0x40}')
                    d = b''
                    fn = '$deleted/' + fn
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'LucasArts R2D2 Pack':
            db.try_custom()
            from lib.file import File
            f = File(i)
            asrt(f.read(8) in {b'R2D2pack',b'2D2Rkcap'})

            f.seek(0x30)
            f._end = {b'R2D2':'<',b'2D2R':'>'}[f.read(4)]
            f.skip(8)
            s = f.readu32()
            f.seek(0x30 + 0x10 + s - 1)
            fts = f.readu8()
            f.seek(0x30 + 0x10 + s - fts - 2)
            fn = f.read(fts).rstrip(b'\0').decode('utf-8')
            f.seek(0x30)
            writefile(o + '/' + fn,f.readc(s))
            f.close()
            return
        case 'Minecraft Console ARC':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')

            c = f.readu32()
            fs = [(f.reads(f.readu16(),'utf-8'),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Minecraft Console MCS':
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu32() == 0)

            d = f.decompress(None,'zlib',usize=f.readu32())
            f.close()
            f = File(d,endian=f._end)

            of,c = f.readu32(),f.readu32()
            f.seek(of)
            fs = []
            for _ in range(c):
                fs.append((f.readutf16(0x40).rstrip('\0'),f.readu32(),f.readu32()))
                f.padc(8)

            for fe in fs:
                f.seek(fe[2])
                writefile(o + '/' + fe[0],f.readc(fe[1]))

            del f
            if fs: return
        case 'Minecraft Console PCK':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu32() in {1,3})

            strs = []
            nc = f.readu32()
            xml = False
            for _ in range(nc):
                id,n = f.readu32(),f.readutf16(f.readu32())
                if n == "XMLVERSION": xml = True
                strs.append(f'{id}: {n}')
                f.padc(4)
            strs.append('')

            if xml: f.skip(4) # ???
            c = f.readu32()
            fs = []
            for _ in range(c):
                s = f.readu32()
                id = f.readu32()
                n = f.readutf16(f.readu32())
                strs.append(f'{id}: {n}')
                f.padc(4)
                fs.append((n,s))
            strs.append('')

            for fe in fs:
                nc = f.readu32()
                for _ in range(nc):
                    strs.append(f'{f.readu32()}: {f.readutf16(f.readu32())}')
                    f.padc(4)
                if nc: strs.append('')
                if not fe[0]:
                    asrt(fe[1] == 0)
                    continue
                if fe[0] == '0' and fe[1] == 0: continue
                writefile(o + '/' + fe[0],f.readc(fe[1]))

            f.close()
            writefile(o + '/$strings.txt','\n'.join(strs),'wt')
            if fs: return
        case 'Minecraft Console Game Rule File':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            asrt(f.readu24() == 0x103)

            f.seek(15)
            d = f.decompress(f.readu32(),'zlib')
            writefile(f'{o}/{tbasename(i)}.grf',d)
            f.close()
            return
        case 'Sonic Shuffle Message Data':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            d = []
            while f: d.append(f.reads(f.readu32() - 4,'utf-8').rstrip('\0'))

            f.close()
            if d:
                writefile(f'{o}/{tbasename(i)}.txt','\n\n'.join(d),'wt')
                return

    return 1
