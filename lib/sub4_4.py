from lib.main import *

def extract4_4(inp:str,out:str,t:str):
    run = db.run
    i = inp
    o = out

    match t:
        case 'Pixar USD Crate': raise NotImplementedError
        case 'Quest3D ZICB':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            of = o + '/' + basename(i)
            while f:
                n = f.read(4).decode('latin-1')
                s = f.readu32()
                ep = f.pos + s

                match n:
                    case 'ACTF'|'ZINS'|'ZIOS': pass
                    case 'ZICB':
                        if exists(of): raise FileExistsError
                        writefile(of,f.decompress(s,'zlib'))
                    case _: raise NotImplementedError(f'{n} ({s}) @ 0x{f.pos:08X}')

                f.seek(ep)

            f.close()
            if exists(of): return
        case 'Surreal Software SRSC':
            TMAP = {
                0x200:'node',
                0x203:'mesh',
                0x204:'uv',
                0x207:'pos',
                0x208:'skl',
                0x211:'parent',
                0x214:'anim',
                0x216:'vert',
                0x302:'sndinf',
                0x303:'pcm',
                0x305:'sndfmt',
                0x402:'lvl',
                0x501:'mdlinf',
                0x502:'mdl',
            }

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'SRSC' and f.readu8() == f.readu8() == 1

            of = f.readu32()
            c = f.readu16()
            f.padc(4)
            f.seek(of)
            fs = [(f.readu16(),f.readu16(),f.readu16(),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[3])
                ex = TMAP.get(fe[0],f'{fe[0]:03X}')
                writefile(f'{o}/{fe[2]:02X}/{fe[1]:02X}.{ex}',f.readc(fe[4]))

            f.close()
            if fs: return
        case 'Silent Hill PAK':
            TMAP = (
                'MYS','SCT','MDL','MAT','SYT',
                'GIN','PIN','XWB','XSB','CSV',
                None ,'DDB','TXT','HKC',None ,
                'STR','PTM','PGP','CMF','PHP',
                'MTM','XML','GAT','CAP','FTS',
                'XML','STR','APK','HKS','HKA',
                'HCL','SES','XGS','XWS','HKP',
                'NVM',None ,None ,None ,#'BIK',
                'OGG','SAC','XMB','GAB','CAB','FTB',
            )

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'PAK_' and f.readu32() == 1

            c = f.readu32()
            f.skip(4)
            fs = []
            for _ in range(c):
                fe = [f.read(0x40).rstrip(b'\0').decode('ascii'),f.readu32(),f.readu32(),f.readu32(),f.reads32()]
                assert f.reads16() == -1
                fe.extend([f.readu16(),f.readu32()])
                if fe[4] == -1: assert fe[3] == fe[6] == 0,f.pos - 0x58
                fs.append(fe)

            for fe in fs:
                if fe[5] > len(TMAP) or TMAP[fe[5]] is None: ex = f'{fe[5]:02X}'
                else: ex = TMAP[fe[5]]
                if fe[4] == -1:
                    d = b''
                    ex += '.deleted'
                else:
                    f.seek(fe[3])
                    if fe[1] & 0x10:
                        assert fe[6] > 12 and f.read(4) == b'LZO\0'
                        us,zs = f.readu32('>'),f.readu32('>')
                        d = f.decompress(zs,'lzo1x',usize=us,db=db)
                    else: d = f.readc(fe[6])
                fn = f'{o}/{fe[0]}.{ex}'
                writefile(fn,d)
                if fe[2] > 0:
                    set_ctime(fn,fe[2])

            f.close()
            if fs: return
        case 'RTL Ski Jumping 2002 PAK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decode
            f = File(i,endian='<')

            f.seek(4)
            c = f.readu32()*0x800//0x50
            f.seek(0)
            fs = []
            for _ in range(c):
                zs,off = f.readu32(),f.readu32()
                if off == 0: break
                f.skip(4)
                fs.append((zs,off * 0x800,f.readu32(),decode(f.read(0x40).rstrip(b'\0'),'latin-1c')))

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[3],f.decompress(fe[0],'rtl_lz' if fe[0] != fe[2] else 'none'))

            f.close()
            if fs: return
        case 'mTropolis MPL':
            if db.print_try: print('Trying with custom extractor')
            from datetime import datetime
            from lib.file import File
            f = File(i,endian='<')
            assert f.readu16() == 1 and f.readu16() == 0xA5A5 and f.readu16() == 0xAA55
            f.padc(2)

            OFS = {}
            def get_fl(id) -> File:
                if id not in OFS:
                    dn = dirname(i)
                    bn = OFS[-1].replace('\0',str(id))
                    pcs = [dn + '/' + x for x in listdir(dn) if noext(x).upper() == bn and x.lower().endswith('.mpx')]
                    if pcs: OFS[id] = File(pcs[0],endian=f._end)
                    else:
                        print(f'WARNING: {dirname(i)}/{bn}.* not found! skipping entries')
                        OFS[id] = None
                return OFS[id]

            FS = []
            def readb(f:File):
                id = f.readu32()
                f.skip(6)
                s = f.readu32()
                ep = f.pos + s

                match id:
                    case 1000:
                        stc = f.readu32()
                        f.skip(2)
                        sgc = f.readu16()
                        for _ in range(stc):
                            n = f.readc(0x10).rstrip(b'\0').decode('ascii')
                            ct,cd = f.readu16('>'),f.readu16('>')
                            tm = datetime(1980 + ((cd >> 9) & 0x7F),(cd >> 5) & 0xF,cd & 0x1F,(ct >> 11) & 0x1F,(ct >> 5) & 0x3F,(ct & 0x1F) * 2)
                            assert f.readc(4) == b'eStr'
                            FS.append((n,f.readu16(),f.readu32(),f.readu32(),tm.timestamp()))
                            assert sgc >= FS[-1][1] > 0

                        cid = f.readu32()
                        assert str(cid) in tbasename(i)
                        OFS[-1] = tbasename(i).replace(str(cid),'\0')
                        OFS[cid] = f
                    case 1002:
                        while f.pos < ep: readpb(f)
                    case _: raise NotImplementedError(f'{id} ({s}) {f.name} @ 0x{f.pos - 14:08X}')

                if ep > f.pos: f.seek(ep)
            def readpb(f:File):
                f.padc(2)
                f.seek(f.readu32())
                readb(f)

            readpb(f)
            for ix,fe in enumerate(FS):
                cf = get_fl(fe[1])
                if not cf: continue
                cf.seek(fe[2])
                if fe[3] == 0: continue
                fn = f'{o}/{ix:03d}.{fe[0]}'
                writefile(fn,cf.readc(fe[3]))
                set_ctime(fn,fe[4])

            for x in OFS:
                if x != -1 and OFS[x]: OFS[x].close()
            if FS: return
        case 'mTropolis MDM':
            TMAP = {
                1:'spr',
                3:'anim',
                4:'snd',
                5:'pal',
            }

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'MDM!' and f.readu16() == f.readu16() == 0x100

            f.seek(f.readu32())
            f.padc(8)
            f.skip(4)
            c = f.readu32()
            while f:
                if f.reads32() == -1: break
            else:
                f.close()
                return 1

            fs = []
            for _ in range(c):
                fs.append((f.readu32(),f.readu32(),f.readu32()))
                f.padc(4)

            for ix,fe in enumerate(fs):
                f.seek(fe[2])
                writefile(f'{o}/{ix:02d}.{TMAP.get(fe[1],f"{fe[1]:02d}")}',f.readc(fe[0]))

            f.close()
            if fs: return
        case 'Lego Creator QUBE':
            rcbkv = sys.getrecursionlimit()
            sys.setrecursionlimit(20000)

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            DN = set()
            def readv(mx:int):
                ty = f.reads(1,'ascii')
                match ty:
                    case 'i': return f.readu32()
                    case 's': return f.readu16()
                    case '[':
                        l = f.readu32()
                        sty = f.reads(1,'ascii')
                        if not sty in 'B': raise NotImplementedError(f'{ty}.{sty} @ 0x{f.pos-6:08X}')
                        v = f.readc(l)
                        return v
                    case '@':
                        v = []
                        while f.pos < mx: v.append(readv(mx))
                        return v
                    case 'B':
                        l = f.readu8()
                        v = []
                        for _ in range(l):
                            if f.pos >= mx: break
                            v.append(readv(mx))
                        return v
                    case 'F': return f.readf32()
                    case 'D': return f.readf64()
                    case '\0': return None
                    case _: raise NotImplementedError(f'{ty} @ 0x{f.pos-1:08X}')
            def readb(p:list[str]):
                bp = f.pos
                ty = f.readu16() & 0x7FFF
                if ty != 15 and bp in DN: return
                DN.add(bp)
                f.skip(2)
                s = f.readu32()
                ep = bp + s
                if f.readu32(): return
                f.skip(4)
                r = []
                while f.pos < ep: r.append(readv(ep))

                match ty:
                    case 1:
                        assert len(r) == 1 and type(r[0]) == list
                        r = r[0]
                        assert r[3].to_bytes(4,'little') == b'QUBE'

                        f.seek(r[6])
                        ep = r[6]+r[7]
                        v = []
                        while f.pos < ep: v.append(readv(ep))
                        for ix,x in enumerate(v[2:]):
                            f.seek(x)
                            readb(p + [f'{ix:02d}'])
                    case 2:
                        if None in r:
                            n = r[-1]
                            assert type(n) == bytes,f'{ty} @ 0x{bp:08X}'
                            if len(p) > 1: p.pop()
                            p.append(n.rstrip(b'\0').decode('ascii'))
                            assert p[-1].isprintable()
                        mkdir('/'.join(p))
                        for ix,x in enumerate(r):
                            if x is None: break
                            if x < BP or x >= f.size: continue
                            f.seek(x)
                            readb(p + [f'{ix:02d}'])
                    case 15:
                        if len(r) == 3 and type(r[2]) == bytes and r[0] == len(r[2]): writefile('/'.join(p) + '.' + guess_ext(r[2]),r[2])
                        else: writefile('/'.join(p) + '.unk.txt',repr(r).replace('[','[\n').replace(']','\n]').encode('utf-8'))
                    case _: raise NotImplementedError(f'{ty} @ 0x{bp:08X}')

            f.seek(4)
            BP = f.readu32()
            f.seek(0)
            readb([o])

            sys.setrecursionlimit(rcbkv)
            f.close()
            if listdir(o): return
        case 'Xenoblade Chronicles X DE ARH2':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,HashLib
            hl = HashLib.dl('xbxde',db,fmt=lambda x:x.lower(),encoding='ascii')
            f = File(i,endian='<')
            assert f.read(4) == b'arh2'

            c = f.readu32()
            a = f.readu32()
            f.padc(4)
            fs = [(f.readu64(),f.readu32(),f.readu32()) for _ in range(c)]
            f.close()

            fd = File(noext(i) + '.ard',endian=f._end)
            hl.wait()
            for fe in fs:
                fn = hl.get(fe[0])
                if fe[1] != fe[2]:
                    bp = fd.pos
                    if fd.read(4) != b'xbc1' or fe[1] <= 0x30:
                        if fe[2] == 0:
                            fd.back(4)
                            d = fd.readc(fe[1])
                        else: raise ValueError(f'Invalid xbc1 header size={fe[1]} usize={fe[2]} @ 0x{bp:08X}')
                    else:
                        ct = fd.readu32()
                        us = fd.readu32() or fe[2]
                        assert fe[2] == 0 or fe[2] == us,f'{fe[2]} != {us} @ 0x{bp:08X}'
                        zs = fd.readu32()
                        fd.skip(0x20)
                        d = fd.decompress(zs,(0,'zlib',0,'zstd')[ct],usize=us)
                        assert len(d) == us,f'{us} != {len(d)} @ 0x{bp:08X}'
                        fd.seek(bp + fe[1])
                else: d = fd.readc(fe[1])
                if not fn:
                    fn = f'$unk/{fe[0]:016X}.'
                    if d[:4] in {b'xbc1','arh2',b'LAHD',b'LAFT',b'LAGP',b'CES\0',b'CEA\0',b'efb0',b'HCPS',b'DLGT'}: fn += d[:3].decode('ascii').lower()
                    elif d[:4] in {b'BC\0\0',b'SB  '}: fn += d[:2].decode('ascii').lower()
                    elif d[:4] == b'1RAS': fn += 'ras'
                    else: fn += guess_ext(d)
                writefile(o + '/' + fn,d)
                fd.align(a)

            fd.close()
            if fs: return
        case 'Harry Potter and the Deathly Hallows BIN':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            ss = f.readu32()
            c = f.readu32()
            sd = {f.readu32():f.read0s('ascii') for _ in range(c)}
            f.seek(4 + ss)
            f.skip(f.readu32()*4)

            c = f.readu32()
            fs = []
            uc = 0
            for _ in range(c):
                fe = [f.readu32()]
                f.skip(4)
                fe.append(f.readu32())
                f.skip(4)
                fe.append(f.readu32())
                sk = f.readu32()
                uc += f.readu32()
                f.padc(12)
                if not sk: fs.append(fe)

            f.skip(uc * 4)
            for fe in fs:
                ex,fn = sd[fe[0]].split(':',1)
                fn += '.' + ex
                if fe[2]: writefile(f'{o}/{fn}.header',f.readc(fe[2]))
                writefile(o + '/' + fn,f.readc(fe[1]))
                f.skip(-fe[1]%0x10)

            f.close()
            if fs: return
        case 'Project IGI Resource':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'ILFF'

            ep = f.readu32()
            f.skip(8)
            assert f.read(4) == b'IRES'
            fn = None
            while f.pos < ep:
                bn = f.read(4)
                bs = f.readu32()
                f.skip(4)
                s = f.readu32()
                if s == 0: s = bs
                else: s -= 0x10
                bp = f.pos

                if bn == b'NAME': fn = f.readc(bs).rstrip(b'\0').decode('ascii').replace(':','/')
                elif bn == b'BODY':
                    assert fn is not None
                    writefile(o + '/' + fn,f.readc(bs))
                    fn = None
                else: raise NotImplementedError(f'{bn.decode("ascii")} @ 0x{bp-0x10:08X}')
                f.seek(bp + s)

            f.close()
            if listdir(o): return
        case 'Golden Tee Fore! BIG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            while f:
                fn = f.read(f.readu16()).decode('utf-8').replace(':\\','\\',1)
                t = f.readu8()
                assert t in (1,2)
                if t == 1: mkdir(o + '/' + fn)
                elif t == 2: writefile(o + '/' + fn,f.read(f.readu32()))
            if listdir(o): return
        case 'UMD Data':
            if db.print_try: print('Trying with custom extractor')
            d = readfile(i).replace(b'\0',b' ').replace(b'|',b'\n')
            writefile(o + '/' + tbasename(i) + '.txt',d)
            return
        case 'SuperScape VRT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            msgs = [x for x in f.read(0xE0).split(b'\x1A')[0].split(b'\0') if x]
            for ix,x in enumerate(msgs): writefile(f'{o}/$message{ix}.txt',x)

            f.skip(0x10)
            assert f.readu32() == 0 and f.read(4) == b'.VRT'
            f.padc(2)
            c = f.readu32()
            f.skip(4)
            fs = []
            for _ in range(c+1):
                fn = f.read0s('ascii')
                f.align(2)
                fs.append((fn,f.readu32(),f.readu32()))

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Gizmo Studios BOLT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'BOLT'

            f.seek(0x18)
            fdo = f.readu32()
            f.seek(0x10)
            ds = []
            for _ in range(fdo//0x10-1):
                f.skip(1)
                c = f.readu24('>')
                f.skip(4)
                ds.append((c,f.readu32()))
                f.padc(4)

            for dix,de in enumerate(ds):
                f.seek(de[1])
                fs = []
                for _ in range(de[0]):
                    f.skip(4)
                    fs.append((f.readu32(),f.readu32(),f.readu32()))

                for fe in fs:
                    f.seek(fe[1])
                    d = f.read(fe[0]) # not f.readc!
                    writefile(f'{o}/{dix:02d}/{fe[2]:08X}.{guess_ext(d)}',d)

            f.close()
            if ds: return
        case 'Hornby BSF':
            KEY = 0xBB

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decrypt
            f = File(i,endian='<')
            assert f.read(4) == b'BSF\0'
            f.skip(0x14)

            c = 0
            while f:
                ep = f.pos
                assert f.read(4) == b'BLK\0'
                n = f.read(4).rstrip(b'\0').decode('ascii')
                s = f.readu32()
                ds = f.readu32()
                assert (s-0x48) == ds
                ep += s

                f.skip(15)
                fn = f.read(0x29)[:0x20]
                fn = fn[:1] + fn[1:].split(b'\0')[0]
                assert len(fn) >= 2 and fn[1] != KEY,f'Empty file name @ {ep-s}'
                fn = o + '/' + decrypt(fn,'hornby',KEY,0x7F).rstrip(b'\0').decode('ascii') + '.' + n

                writefile(fn,f.readc(ds))
                if n == 'STR':
                    f.seek(ep - ds + 0x10)
                    sc = f.readu32()
                    ofs = [f.readu32() for _ in range(sc)]
                    bp = f.pos
                    ob = []
                    for of in ofs:
                        f.seek(bp + of)
                        ob.append(f.read0s('ascii'))
                    if ob: writefile(fn + '.txt','\n'.join(ob),'w')

                f.seek(ep)
                c += 1
                if n == 'END': break

            f.close()
            if c: return
        case 'Detective Instinct: Farewell, My Beloved Encrypted DIP':
            KEY = readfile(db.get('difmb_dip_key')) # external file because 256KB

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decrypt
            f = File(decrypt(readfile(i),'xor',KEY),endian='>')
            del KEY

            c = f.readu32()
            fs = [(f.readu32(),f.readu32(),f.read(f.readu32()).rstrip(b'\0').decode('utf-8')) for _ in range(c)]
            for fe in fs:
                fn = o + '/' + fe[2]
                if fe[0] & 0x20: fn += '.external'
                if fe[0] & 2:
                    mkdir(fn)
                    continue
                else: d = f.readc(fe[1])
                writefile(fn,d)

            del f
            if fs: return
        case 'StarFlyers Bulk File Index':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            offs = [f.readu32() for _ in range(c)]

            ofs = {}
            fs = []
            for of in offs:
                f.seek(of)
                f.skip(2)
                to = f.readu32()
                sn = f.read0s('ascii')
                f.seek(to)
                c = f.readu32()
                offs2 = [f.readu32() for _ in range(c)]

                for of2 in offs2:
                    f.seek(of2)
                    if sn == '*bulkFiles':
                        id = f.readu32()
                        assert id not in ofs or ofs[id] is None
                        f.skip(14)
                        fn = dirname(i) + '/' + f.read0s('ascii')
                        #if not exists(fn): print('WARNING:',fn,'not found, skipping entries')
                        ofs[id] = open(fn,'rb') if exists(fn) else None
                    else:
                        fe = [f.readu32(),f.readu32(),f.readu32()]
                        f.padc(6)
                        fe.append(sn + '/' + f.read0s('ascii'))
                        fs.append(fe)
            f.close()
            if all(of is None for of in ofs.values()):
                print('0 referenced *.bul files found')
                return 1

            for fe in fs:
                if ofs[fe[0]] is None: continue
                ofs[fe[0]].seek(fe[1])
                writefile(o + '/' + fe[3],ofs[fe[0]].read(fe[2]).split(b'\0',1)[1])

            [f.close() for f in ofs.values() if f]
            if listdir(o): return
        case 'Endless Interactive IN2+DBB':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            def fix_mp4(f:File,gp:int,fn:str):
                stco = None
                def readb(p=None):
                    nonlocal stco
                    bp = f.pos
                    s = f.readu32()
                    n = ((p + '/') if p else '') + f.read(4).decode('ascii')
                    if s == 1: s = f.readu64()
                    elif s == 0: s = f.size - bp
                    ep = bp + s

                    if n in {'moov','moov/trak','moov/trak/mdia','moov/trak/mdia/minf','moov/trak/mdia/minf/dinf','moov/trak/mdia/minf/stbl'}:
                        while f.pos < ep:
                            if readb(n): return True
                    elif n == 'moov/trak/mdia/minf/dinf/dref':
                        assert f.readu8() == f.readu24() == 0
                        c = f.readu32()
                        for _ in range(c):
                            if readb(n): return True
                    elif n == 'moov/trak/mdia/minf/dinf/dref/alis':
                        assert f.readu8() == 0
                        fl = f.readu24()
                        assert fl in {0,1}
                        return not fl
                    elif n == 'moov/trak/mdia/minf/stbl/stco':
                        assert f.readu8() == f.readu24() == 0
                        stco = f.pos

                    f.seek(ep)

                while f:
                    if readb(): break
                else:
                    if stco is None: return
                    f.seek(stco)
                    c = f.readu32()
                    for _ in range(c):
                        v = f.readu32()
                        f.back(4)
                        assert v >= gp,f"0x{v:08X} < 0x{gp:08X} {fn}"
                        f.writeu32(v-gp)

                    writefile(f'{noext(fn)}.fixed{extname(fn)}',f.readall())
                    del f

            f = File(noext(i) + '.in2',endian='<')
            fd = File(noext(i) + '.dbb',endian='>')
            assert f.readu32() == 0x50202 and f.readu32() == 1
            f.padc(2)

            fd.seek(0x30)
            fd.skip(fd.readu8())
            c = fd.readu8()
            fd.skip(1+c*0x12)
            fd.padc(0x10)
            fd.skip(4+4)
            bo = fd.readu32()

            tc = f.readu16()
            fc = f.readu16()
            f.skip(2)
            ts = {f.readu16():(f.readu32(),f.readu32()) for _ in range(tc)}
            assert 7 in ts and 9 in ts
            assert ts[7][1] == (fc*0x10) and ts[9][1] == (fc*11)

            f.seek(ts[9][0])
            fs = []
            for _ in range(fc):
                f.skip(2)
                fs.append((f.readu32(),f.readu32()))
                f.skip(1)

            f.seek(ts[7][0])
            for _ in range(fc):
                fn = f.read(12).rstrip(b'\0').decode('ascii')
                assert fn and fn.isprintable()
                id = f.readu16()
                fn = o + '/' + fn
                if exists(fn): fn = f'{noext(fn)}.{id:04d}{extname(fn)}'

                fe = fs[id-1]
                assert f.readu16() == 1
                fd.seek(bo + fe[0])
                d = fd.readc(fe[1])
                writefile(fn,d)
                if d[4:8] == b'mdat': fix_mp4(File(d,endian='>'),fe[0],fn)

            f.close()
            fd.close()
            if c: return

    return 1
