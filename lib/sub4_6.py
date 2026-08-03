from .main import *

def extract4_6(inp:str,out:str,t:str):
    run = db.run
    i,o = inp,out

    match t:
        case 'Torus Hunk File':
            raise NotImplementedError
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            hs = f.readu32()
            asrt(f.readu16() == 0x70 and f.readu16() == 4)
            f.skip(8)
            c = f.readu32()
            asrt(f.readu32() == 2)
            dn = f.reads(0x40,'ascii').rstrip('\0')
            if dn == 'Temp': dn = o
            else: dn = o + '/' + dn
            f.skip(8)
            dn += '/' + f.reads(0x40,'ascii').rstrip('\0')
            tds = f.readu32()

            f.seek(hs + 8)
            cds = 0
            for _ in range(c):
                hs = f.readu32()
                asrt(f.readu16() == 0x71 and f.readu16() == 4)
                ep = f.pos + hs

                f.skip(6)
                exl,nl = f.readu16(),f.readu16()
                ex = f.reads(exl,'ascii').rstrip('\0')
                fn = dn + '/' + f.reads(nl,'ascii').rstrip('\0') + '.' + ex
                f.seek(ep)

                s = f.readu32()
                cds += s
                f.skip(0x18)
                writefile(fn,f.readc(s))
                asrt(f.readu32() == 0 and f.readu16() == 0x72 and f.readu16() == 4)

            f.close()
            if c and cds == tds: return
        case 'Onyx Engine FAT+data':
            TMAP = {
                0x044081CE:'fnt',
                0x10091979:'swf',
                0x24097ED9:'tex',
            }

            db.try_custom()
            from lib.file import File
            f = File(File(i).decompress(None,'zlib'),endian='<')
            fd = File(noext(i),endian=f._end)

            c = f.readu32()
            fs = [(f.readu32(),f.readu64()) for _ in range(c)]
            del f
            fs.append((0,fd.size))

            for ix,fe in enumerate(fs[:-1]):
                fd.seek(fe[1])
                f = File(fd.decompress(fs[ix + 1][1] - fe[1],'zlib'),endian=fd._end)
                dn = f'{o}/{fe[0]:08X}'
                mkdir(dn)
                c = f.readu32()
                for ix in range(c):
                    s = f.peek('u32')
                    asrt(s >= 8)
                    if s >= 12: n = f'{f.peek("u32",poffset=8):08X}'
                    else: n = f'{ix:03d}'
                    tid = f.peek("u32",poffset=4)
                    if not tid in TMAP: ex = f'{tid:08X}'
                    else: ex = TMAP[tid]
                    writefile(f'{dn}/{n}.{ex}',f.readc(s))

            fd.close()
            if fs: return
        case 'ZPackage':
            db.try_custom()
            from lib.file import File,pdosdate
            f = File(i,endian='<')
            asrt(f.read(10) == b'ZPackage1\0')

            while f:
                xo = f.readu32()
                n = o + '/' + f.read0s('ascii')
                ts = (f.readu16(),f.readu16())
                writefile(n,f.decompress(xo - f.pos,'zlib'))
                set_ftime(n,pdosdate(ts[1],ts[0]))

            f.close()
            if listdir(o): return
        case 'XelaSoft Archive':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'PCK2')

            to = f.readu32()
            f.skip(4) # tsz
            c = f.readu32()
            f.seek(to)

            fs = []
            for _ in range(c):
                f.skip(4) # file type id
                fs.append((f.readu32(),f.readu32(),f.read0s('ascii')))
                f.skip(3)

            for fe in fs:
                f.seek(fe[0])
                writefile(o + '/' + fe[2],f.readc(fe[1]))

            f.close()
            if fs: return
        case 'WarpIN Archive':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'w\4\2\xBE' and f.readu16() == 3)
            f.padc(0x100)

            writefile(o + '/$info.txt',b'Title: ' + f.readc(0x40).split(b'\0')[0] + b'\nAuthor: '+ f.readc(0x40).split(b'\0')[0] + b'\nURL: ' + f.readc(0x80).split(b'\0')[0] + b'\n')
            f.skip(4)
            pc = f.readu16()
            pus,pzs = f.readu16(),f.readu16()
            f.padc(4)
            writefile(o + '/$page.htm',f.decompress(pzs,'bzip2',usize=pus))
            ps = []
            for _ in range(pc):
                f.skip(2) # index/id
                c,of = f.readu16(),f.readu32()
                f.skip(8) # total data us/zs
                ps.append((c,of,f.readc(0x20).split(b'\0')[0].decode('ascii')))

            for pe in ps:
                f.seek(pe[1])
                dn = o + '/' + pe[2]
                mkdir(dn)
                for _ in range(pe[0]):
                    f.skip(8) # u32: ?, u16: ?, u16: pid
                    us,zs = f.readu32(),f.readu32()
                    f.skip(4) # crc? unknown, 0 if us == zs
                    n = f.readc(0x100).split(b'\0')[0].decode('ascii')
                    ts = (f.readu32(),f.readu32())
                    f.padc(1)
                    writefile(dn + '/' + n,f.decompress(zs,'bzip2' if us != zs else 'none',usize=us))
                    set_ftime(dn + '/' + n,ct=ts[0],mt=ts[1])

            f.close()
            if ps: return

    return 1
