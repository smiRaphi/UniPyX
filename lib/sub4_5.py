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
            asrt(f.read(4) == b'APak' and f.readu32() == 5)

            c = f.readu32()
            f.seek(0x18)
            sof = 0x50 + f.readu32()
            to1 = sof + f.readu32()

            oto1,odo1,ods1,oc1 = f.readu32(),f.readu32(),f.readu32(),f.readu32()
            oto2,odo2,ods2,oc2 = f.readu32(),f.readu32(),f.readu32(),f.readu32()
            xtc,xto,xtdo,xtds = f.readu32(),f.readu32(),f.readu32(),f.readu32()

            f.seek(oto1)
            ofs1 = {}
            for _ in range(oc1):
                id = f.readu32()
                ofs1[id] = odo1 + f.readu32()
                f.padc(8)
            f.seek(oto2)
            ofs2 = {}
            for _ in range(oc2):
                id = f.readu32()
                ofs2[id] = odo2 + f.readu32()
                f.padc(8)
            f.seek(xto)
            oft3 = []
            for _ in range(xtc):
                f.skip(4) # ds
                oft3.append((f.readu32(),xtdo + f.readu32()))
                f.skip(0x114)
            ofs3 = {}
            for xc,xdo in oft3:
                for _ in range(xc):
                    id = f.readu32()
                    asrt(id not in ofs3,f.pos)
                    ofs3[id] = xdo + f.readu32()
                    f.padc(8)

            f.seek(to1)
            fs = []
            for _ in range(c):
                f.skip(0x14)
                so = sof + f.readu32()
                f.skip(0x10)
                fs.append((so,f.readu32(),f.readu32(),f.readu32()))
                asrt(fs[-1][1] == fs[-1][2],f.pos)
                f.skip(12)

            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                fn = f.read0s('utf-8')

                inc = [(oix,x[ix]) for oix,x in enumerate((ofs1,ofs2,ofs3)) if ix in x]
                if len(inc) == 1:
                    f.seek(inc[0][1])
                    writefile(o + '/' + fn,f.readc(fe[1 if inc[0][0] == 0 else 3]))
                elif len(inc) == 2 and inc[0][0] == 0:
                    bfn = splitext(fn)
                    f.seek(inc[0][1])
                    writefile(o + '/' + fn,f.readc(fe[1]))
                    f.seek(inc[1][1])
                    writefile(o + '/' + bfn[0] + '.data' + bfn[1],f.readc(fe[3]))
                else:
                    print(ix,fe,inc,fn)
                    raise NotImplementedError

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
        case 'Flipper Zero NFC Data':
            db.try_custom()
            import re
            d = readfile(i,'rt')

            pc = int(re.search(r'(?m)^Pages total: (\d+)$',d)[1])
            pgs = sorted(re.findall(r'(?m)^Page (\d+): ([A-F0-9 ]{2,})$',d),key=lambda x:int(x[0]))[:pc]
            ob = []
            DN = set()
            for x in pgs:
                if x[0] in DN: continue
                DN.add(x[0])
                ob.append(x[1])
            if ob:
                writefile(f'{o}/{tbasename(i)}.bin',bytes.fromhex(''.join(ob)),'wb')
                return
        case 'Nintendo Amiibo NFC Raw':
            db.try_custom()
            from .sub2 import Nintendo
            from lib.file import File,datetime
            f = File(Nintendo(db).amiibo_raw_decrypt(Nintendo.AmiiboRaw(i)),endian='>')

            f.seek(4)
            cd,md = f.readu16(),f.readu16()
            cd = datetime(2000 + ((cd >> 9) & 0x7F),(cd >> 5) & 0xF,cd & 0x1F).timestamp()
            md = datetime(2000 + ((md >> 9) & 0x7F),(md >> 5) & 0xF,md & 0x1F).timestamp()
            f.skip(4)
            n = f.readutf16(10).rstrip('\0') or tbasename(i)
            writefile(f'{o}/{n}_mii.bin',f.readc(0x60))
            f.seek(0xB0)
            writefile(f'{o}/{n}_area.bin',f.readc(0xD8))
            writefile(f'{o}/{n}_dec.bin',f.readall())
            del f

            for f in ('mii','area','dec'):
                set_ftime(f'{o}/{n}_{f}.bin',cd,mt=md)

            return
        case 'Dynamix VOL':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            f.seek(f.readu32())
            c = f.readu32()
            asrt(f.readu32() == 0x10)
            fs = []
            for _ in range(c):
                ty = f.readu32()
                if ty == 0:
                    f.skip(0x10)
                    mkdir(o + '/' + f.reads(f.readu16(),'ascii'))
                elif ty in {1,0x1001}:
                    fe = (f.readu32(),f.readu32() + 4)
                    f.skip(8)
                    fs.append((*fe,f.reads(f.readu16(),'ascii')))
                else: raise NotImplementedError(f.fmt(f'{ty:02X}§@',back=4))
                f.skip(4)

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[2],f.readc(fe[0]))

            f.close()
            if fs: return
        case 'Disney POD':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'Pod\0' and f.read(4) in {b'file',b'\0\0\0\0'} and f.readu32() == 0)

            c = f.readu32()
            fs = [(f.reads(12,'ascii').rstrip('\0'),f.readu32()) for _ in range(c)]
            for fe in fs: writefile(o + '/' + fe[0],f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Koei Tecmo LINKDATA':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            asrt(f.readu32() == 491001)

            c,b = f.readu32(),f.readu32()
            f.padc(4)
            fs = []
            for _ in range(c):
                f.padc(4)
                fs.append((f.readu32()*b,f.readu32()))
                f.padc(4)

            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.readc(fe[1])
                if d[:4] in {b'G1TG',b'KSHL',b'KTFK',b'WBD_',b'WBH_',b'G1EM'} and d[4:8].isdigit(): ex = d[:3].decode('ascii').lower()
                elif d[:0x1A] == b'\t// Generated by JustLook ': ex = 'txt'
                else: ex = guess_ext_ps2(d)
                writefile(f'{o}/{ix:02d}.{ex}',d)

            f.close()
            if fs: return
        case 'Sierra BAG':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            fs = [(f.readu32(),f.reads(13,'ascii').rstrip('\0')) for _ in range(c)]
            asrt(not fs[-1][1])

            for ix,fe in enumerate(fs[:-1]):
                f.seek(fe[0])
                writefile(o + '/' + fe[1],f.readc(fs[ix+1][0] - fe[0]))

            f.close()
            if fs: return
        case 'Sierra PRF':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            f.skip(4)
            asrt(f.read(4) == b'PRF\0' and f.readu32() == 1)

            f.skip(8)
            f.seek(f.readu32())
            c = f.readu16()
            f.skip(2)
            fs = []
            for _ in range(c):
                ty = f.reads(4,'ascii').strip()
                id = f.readu16()
                f.skip(2)
                fe = (f'{id:03d}.{ty}',f.readu32(),f.readu32())
                if ty == '\0\0\0\0':
                    asrt(fe[2] == 0)
                    continue
                fs.append(fe)

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Bomberman PAK':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                if not fe[0]: continue
                f.seek(fe[0])
                d = f.readc(fe[1])
                if d[:0x10] == b'NDS_COMPRESS\0\0\0\0': ex = 'ndsc'
                else: ex = guess_ext_nds(d)
                writefile(f'{o}/{ix:02d}.{ex}',d)

            f.close()
            if fs: return
        case 'Konami NDS Compress':
            db.try_custom()
            from lib.file import decompress
            d = readfile(i)
            asrt(d[:0x10] == b'NDS_COMPRESS\0\0\0\0')

            writefile(o + '/' + basename(i),decompress(d[0x10:],f'lz{d[0x10]:02x}',verify=False))
            return
        case 'Bomberman 2 FPCK':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                if not fe[0]: continue
                f.seek(fe[0])
                d = f.readc(fe[1])
                if d[:0x10] == b'NDS_COMPRESS\0\0\0\0': ex = 'ndsc'
                elif sum(d[:4]) and sum(d[4:8]) and (4+int.from_bytes(d[:4],'little')*8) == int.from_bytes(d[4:8],'little'): ex = 'fpck'
                elif d[:4] == b'BLDT': ex = 'bldt'
                else: ex = guess_ext_nds(d)
                writefile(f'{o}/{ix:02d}.{ex}',d)

            f.close()
            if fs: return
        case 'Championship Manager 17 DCFile':
            db.try_custom()
            from lib.crypto import decrypt
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(2) == b'D0')

            of,c = f.readu32(),f.readu16()
            fs = [(f.read0s('ascii'),f.readu32(),f.readu32()) for _ in range(c)]
            f.seek(of)
            for fe in fs:
                asrt(fe[1] & 0x80000000,lambda:f.read(8).hex(" ").upper(),err=NotImplementedError)
                d = f.decompress(fe[1] & 0x7fffffff,'none' if fe[1] & 0x80000000 else 'none',usize=fe[2])
                writefile(o + '/' + fe[0],d)

            f.close()
            if fs: return

    return 1
