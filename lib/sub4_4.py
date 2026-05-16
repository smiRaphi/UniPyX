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
                n = f.read(4).decode('ansi')
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
            from lib.file import File
            from lib.crypto import decode
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
            from lib.file import File
            from lib.crypto import HashLib
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
                assert t in {1,2}
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
            from lib.file import File
            from lib.crypto import decrypt
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
            from lib.file import File
            from lib.crypto import decrypt
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
        case 'Endless Interactive IN2+DBB'|'Endless Interactive IN1+DBB':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            def fix_mp4(f:File,gp:int,fn:str):
                stco = []
                def readb(p=None):
                    bp = f.pos
                    s = f.readu32()
                    n = ((p + '/') if p else '') + f.read(4).decode('ascii')
                    if s == 1: s = f.readu64()
                    elif s == 0: s = f.size - bp
                    ep = bp + s

                    if n in {'moov','moov/trak','moov/trak/mdia','moov/trak/mdia/minf','moov/trak/mdia/minf/stbl'}: # 'moov/trak/mdia/minf/dinf',
                        while f.pos < ep:
                            if readb(n): return True
                    # elif n == 'moov/trak/mdia/minf/dinf/dref':
                    #     assert f.readu8() == f.readu24() == 0
                    #     c = f.readu32()
                    #     for _ in range(c):
                    #         if readb(n): return True
                    # elif n == 'moov/trak/mdia/minf/dinf/dref/alis':
                    #     assert f.readu8() == 0
                    #     fl = f.readu24()
                    #     assert fl in {0,1}
                    #     return not fl
                    elif n == 'moov/trak/mdia/minf/stbl/stco':
                        assert f.readu8() == f.readu24() == 0
                        stco.append(f.pos)

                    f.seek(ep)

                while f: readb()
                if not stco: return
                for x in stco:
                    f.seek(x)
                    c = f.readu32()
                    for _ in range(c):
                        v = f.readu32()
                        f.back(4)
                        assert v >= gp,f"0x{v:08X} < 0x{gp:08X} {fn}"
                        f.writeu32(v-gp)

                writefile(f'{noext(fn)}.fixed{extname(fn)}',f.readall())
                del f

            f = File(noext(i) + '.in' + t[21])
            f._end = {0x101:'>',0x202:'<'}[f.readu16()]
            fd = File(noext(i) + '.dbb',endian='>')
            assert f.readu16() == 5 and f.readu16() == 1
            f.padc(4)

            fd.seek(0x30)
            fd.skip(fd.readu8())
            c = fd.readu8()
            fd.skip(1+c*0x12)
            fd.padc(0x10)
            fd.skip(4+4)
            bo = fd.readu32()

            tc = f.readu16()
            fc = f.readu16()
            ssz = f.readu16()
            ts = {f.readu16():(f.readu32(),f.readu32()) for _ in range(tc)}
            assert 7 in ts and 9 in ts
            assert ts[7][1] == (fc*(4+ssz))

            if 8 in ts:
                f.seek(ts[8][0])
                writefile(o + '/$unknown.txt',f.readc(ts[8][1]))

            f.seek(ts[9][0])
            fs = []
            for _ in range(ts[9][1]//11):
                f.skip(2)
                fs.append((f.readu32(),f.readu32()))
                f.skip(1)

            f.seek(ts[7][0])
            ids = set()
            for _ in range(fc):
                fn = f.read(ssz).rstrip(b'\0').decode('ascii')
                assert fn and fn.isprintable()
                id = f.readu16()
                f.skip(2)
                fn = o + '/' + fn
                if exists(fn): fn = f'{noext(fn)}.{id:04d}{extname(fn)}'

                fe = fs[id-1]
                fd.seek(bo + fe[0])
                d = fd.readc(fe[1])
                writefile(fn,d)
                ids.add(id-1)
                if d[4:8] == b'mdat': fix_mp4(File(d,endian='>'),fe[0],fn)

            c = 0
            for ix,x in enumerate(fs):
                if ix in ids: continue
                fd.seek(bo + x[0])
                d = fd.readc(x[1])
                fn = f'{o}/$left/{ix:03d}.{guess_ext(d)}'
                writefile(fn,d)
                if d[4:8] == b'mdat': fix_mp4(File(d,endian='>'),x[0],fn)
                c += 1

            f.close()
            fd.close()
            if fc: return
        case 'Blood Will Tell Osamu Tezuka\'s Dororo LBI':
            raise NotImplementedError
            from lib.file import File
            f = File(i,endian='<')

            def reado(assrt=True):
                of = f.readu32()
                if assrt: assert of
                if of: of -= 1
                else: of = None
                return of
            def readv(fnc=f.readu32,assrt=True,**kwargs) -> int:
                v = reado(assrt)
                cp = f.pos
                if v is None: return None
                f.seek(v)
                r = fnc(**kwargs)
                f.seek(cp)
                return r

            f.skip(8)
            o1,o2 = reado(),reado()
            f.seek(o1)
            assert f.read(4) == b'SSCN'
            f.skip(12)
            c = f.readu32()
            f.seek(o2)

            f.seek(reado() + 4)
            ty = f.readu32()
            assert ty in {4,0x1F}

            if ty == 4:
                f.seek(o2 + (c+3)*4)
                ofs = [(f'{ix:02d}',readv()) for ix in range(c)]

            for dn,of in ofs:
                f.seek(of)
                assert f.readu32() == 0x1000
                f.skip(0x28)
                c = f.readu32()
                fs = []
                for _ in range(c):
                    fs.append((f.readu16()*0x10,f.readu16(),of+f.readu32()))
                    f.padc(3)
                    f.skip(5)

                for fe in fs:
                    f.seek(fe[2])
                    writefile(f'{o}/{dn}/{fe[1]:05d}.bin',f.readc(fe[0]))

            f.close()
            if ofs: return
        case 'DDLC+ Encrypted Unity Bundle':
            KEY = 0x28

            if db.print_try: print('Trying with custom extractor')
            from lib.crypto import decrypt
            of = f'{o}/{tbasename(i)}.bundle'
            writefile(of,decrypt(readfile(i),'xor',KEY))
            r = extract(of,o,'Unity Bundle')
            return
        case 'Selene Pack':
            KEYS = (b'Selene.Default.Password',b'PackPass')

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            from lib.crypto import decrypt
            from multiprocessing.pool import ThreadPool
            f = File(i,endian='<')
            assert f.read(4) == b'KCAP'

            c = f.readu32()
            fs = []
            for _ in range(c):
                fn = f.read(0x40).rstrip(b'\0').decode('shift-jis')
                assert fn,f.pos-0x40
                f.skip(8)
                fs.append((fn,f.readu32(),f.readu32(),f.readu32()))
                assert fs[-1][3] in {0,1}

            if any(fe[3] for fe in fs):
                wav = [fe for fe in fs if fe[3] == 1 and fe[0].lower().endswith('.wav') and fe[2] >= 4]
                assert wav,"Can't guess key"
                wav = wav[0]
                f.seek(wav[1])
                d = f.readc(4)
                for k in KEYS: # this also initializes all key tables!!! which would otherwise cause Threading issues
                    if decrypt(d,'selene',k) == b'RIFF':
                        key = k
                        break
                else: raise RuntimeError('Unknown key')

            def writed(d,fn,flg):
                if flg: d = decrypt(d,'selene',key)
                writefile(o + '/' + fn,d)
            p = ThreadPool()
            pcs = []
            for fe in fs:
                f.seek(fe[1])
                pcs.append(p.apply_async(writed,(f.readc(fe[2]),fe[0],fe[3])))
            for pc in pcs: pc.get()
            p.close()
            p.join()

            f.close()
            if fs: return
        case 'Konami NKP':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'NKP\x1A'

            eo = f.readu32()
            f.padc(4)
            c = f.readu32()
            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            fs.append((0,eo))

            for ix,fe in enumerate(fs[:-1]):
                f.seek(fe[0])
                fn = f.read0s('ascii')
                f.seek(fe[1])
                writefile(o + '/' + fn,f.readc(fs[ix+1][1]-fe[1]))

            f.close()
            if fs: return
        case 'Neox Package':
            CAL = (0,'zlib','lz4','zstd')
            EAL = ('none','xor','rc4','aes','cxor')
            HAL = (0,0,'murmur3_32')

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decompress
            from lib.crypto import decrypt,maskb
            f = File(i,endian='<')
            assert f.read(4) == b'NXPK'

            c = f.readu32()
            f.padc(4)
            tea = f.readu32()
            if tea != 0: raise NotImplementedError(f'Encrypted TOC {EAL[tea] if tea < len(EAL) else "?"} (0x{tea:02X})')
            f.skip(4)
            f.seek(f.readu32())

            fs = []
            for _ in range(c):
                # 0       |1  |2 |3 |4    |5    |6  |7
                # name_crc|off|zs|us|crc_z|crc_u|cal|eal
                fs.append([f.readu32() for _ in range(6)] + [f.readu16(),f.readu16()])
                assert fs[-1][6] in {0,1,2,3} and fs[-1][7] in {0,4},f.pos - 0x1C

            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                if fe[7] == 5:
                    r,c = fe[3],fe[5]
                    if fe[1] <= 0x80: off,pks = 0,fe[1]
                    else:
                        off = (r >> 1) % (fe[1] - 0x80)
                        pks = (((c << 1) & maskb(4)) % 0x60) + 0x20
                    d = d[:off] + decrypt(d[off:off+pks],'cxor',(r ^ c) & 0xFF,off) + d[off+pks:]
                elif fe[7] != 0: raise NotImplementedError(f'Unimplemented encryption {EAL[fe[7]] if fe[7] < len(EAL) else "?"} (0x{fe[7]:02X})')

                if fe[6] == 0: d = decompress(d,'zlib' if fe[2] != fe[3] else 'none',usize=fe[3])
                else: d = decompress(d,CAL[fe[6]],usize=fe[3])
                writefile(f'{o}/{fe[0]:08X}.{guess_ext_163(d)}',d)

            f.close()
            if fs: return
        case 'Digital Illusions PDT':
            KEY = b'THEEVENTHORIZONS'

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File,decompress
            from lib.crypto import decrypt
            from multiprocessing.pool import ThreadPool
            f = File(i,endian='<')
            assert f.read(4) == b'PDI1'

            c = max(f.readu32(),f.readu32())
            f.skip(4)
            do = f.readu32()
            bo = f.readu32()
            f.seek(do)
            fs = []
            dns = []
            for ix in range(c):
                ft = f.readu16()
                if not ft:
                    f.skip(0x42)
                    continue
                ids = [f.reads16() for _ in range(5)]
                fe = (f.readu32()+bo,f.readu32())
                fn = f.read(0x2C).rstrip(b'\0').decode('ansi')
                f.skip(4)

                if ft & 4:
                    assert ft == 4,f.pos - 0x44
                    lid = ids[1]
                    if lid == -1: lid = ids[2]
                    if lid == -1: lid = c
                    dns.append((lid,fn))
                else:
                    assert (ft >> 1) == 12,f.pos - 0x44
                    dn = [x[1] for x in dns if ix < x[0]]
                    fs.append(('/'.join(dn) + '/' + fn,fe[0],fe[1],ft))

            def writed(d,fe):
                # don't trust compressed flag
                if fe[3] & 1 or\
                   (d[:4] == b'CDI1' and not d[8] and not d[9] and not d[11] and not d[10] & 0b11101110):
                    assert d[:4] == b'CDI1'
                    assert not d[8] and not d[9]
                    assert not d[11] and not d[10] & 0b11101110
                    us = int.from_bytes(d[4:8],'little')
                    fl = d[10]
                    d = d[12:]
                    if fl & 0x10: d = decrypt(d,'tea_pad_le',KEY)
                    if fl & 1: d = decompress(d,'lzss8',usize=us)
                    d = d[:us]
                    assert len(d) == us,fe[0]
                writefile(o + '/' + fe[0],d)
            p = ThreadPool()
            pcs = []
            for fe in fs:
                f.seek(fe[1])
                pcs.append(p.apply_async(writed,(f.readc(fe[2]),fe)))
            for pc in pcs: pc.get()
            p.close()
            p.join()

            f.close()
            if fs: return
        case 'Camelot ARC': raise NotImplementedError
        case 'Natsume LZS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import decompress
            d = readfile(i)
            assert d[:4] == b'LZS\0' and d[4] == 5

            hs = int.from_bytes(d[8:12],'little')
            p = 0x1C + d[0x18]
            if not d[0x18] and not sum(d[0x1C:0x20]): p += 4
            if p >= hs: fn = basename(i)
            else: fn = d[p:hs].split(b'\0')[0].decode('ascii')
            writefile(o + '/' + fn,decompress(d,'natsume_lzs'))
            return
        case 'Delta Studio YSCE':
            TYPS = ('Geometry','Bone','Group','Plane','Instance','Empty','Armature','Light')

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.reads32()
            cvbo = 0
            for _ in range(c):
                on = f.read(0x40).split(b'\0')[0].decode('ansi')
                inf = [f.read(0x40).split(b'\0')[0].decode('ansi'),f.reads32(),f.reads32(),f.reads32(),f.reads32()]
                ty = f.reads32()
                assert ty >= 0,f.pos

                ob = []
                for ix,fln in enumerate(('Material','Model Index','Parent Index','Parent Instance Index','Skeleton Index')): ob.append(f'{fln}: {inf[ix]}')
                ob.append(f'Type: {TYPS[ty] if ty < len(TYPS) else "?"} ({ty})\n')
                ob.append(f'Position: {f.readf32()} {f.readf32()} {f.readf32()}')
                ob.append(f'Orientation Euler: {f.readf32()} {f.readf32()} {f.readf32()}')
                ob.append(f'Orientation Quaternion: {f.readf32()} {f.readf32()} {f.readf32()} {f.readf32()}')
                ob.append(f'Scale: {f.readf32()} {f.readf32()} {f.readf32()}')
                ob.append(f'Min Extreme: {f.readf32()} {f.readf32()} {f.readf32()}')
                ob.append(f'Max Extreme: {f.readf32()} {f.readf32()} {f.readf32()}\n')
                ob.append(f'UV Channels: {f.reads32()}')
                vc = f.reads32()
                ob.append(f'Vertex Count: {vc}')
                fc = f.reads32()
                ob.append(f'Face Count: {fc}')
                bc = f.reads32()
                ob.append(f'Bone Count: {bc}')
                ob.append(f'Max Bones Per Vertex: {f.reads32()}')
                fls = f.readu32()
                ob.append(f'Flags: {fls:05b}')
                vds = f.reads32()
                ob.append(f'Vertex Data Size: {vds}')

                fn = f'{o}/{inf[1]:03d}_{sub_path(on,slash=True)}.' + TYPS[ty] if ty < len(TYPS) else f'Undefined{ty:02d}'
                if vc:
                    strd = vds // vc
                    f.skip(-cvbo % strd)
                cvbo += vds
                bo = f.pos
                writefile(fn + '.bin',f.read(vds + 2*fc*3))
                writefile(fn + '_info.txt','\n'.join(ob),'w')
                if ty == 0:
                    obj = [f'o {on}']
                    for ix in range(vc):
                        f.seek(bo + ix*strd)
                        obj.append(f'v {f.readf32()} {f.readf32()} {f.readf32()}')
                        f.skip(4)
                        if fls & 8: obj.append(f'vt {f.readf32()} {f.readf32()}')
                        if fls & 2:
                            obj.append(f'vn {f.readf32()} {f.readf32()} {f.readf32()}')
                            f.skip(4)
                    f.seek(bo + vds)
                    for _ in range(fc):
                        vs = (f.readu16()+1,f.readu16()+1,f.readu16()+1)
                        obj.append(f'f {vs[0]}/{vs[0]}/{vs[0]} {vs[1]}/{vs[1]}/{vs[1]} {vs[2]}/{vs[2]}/{vs[2]}')
                    writefile(fn + '.obj','\n'.join(obj),'w')

            f.close()
            if c: return
        case 'Six Guns Encrypted Save':
            KEY = b'\x15\x24\x11\x1C\x6F\x31\xD4\x64\x61\x20\x02\x32\xC0\x44\x99\xB0'

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='<')

            hs = f.readu32()
            assert f.read(f.readu32()) == b'ENCRYPTED\0'
            enc = f.read(f.readu32()).rstrip(b'\0').decode('ascii')
            assert enc == 'TEA'
            f.seek(hs)
            assert f.readu32() == 1
            writefile(o + '/' + basename(i),decrypt(f.read(),'tea_le',KEY))
            f.close()
            return
        case 'Temple of Elemental Evil DAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,'rb',endian='<')
            f.seek(-12)
            assert f.read(4) == b'1TAD'

            f.skip(4)
            f.seek(-f.readu32())
            c = f.readu32()
            fs = []
            ds = {-1:o}
            for ix in range(c):
                fn = f.read(f.readu32()).rstrip(b'\0').decode('ascii')
                f.skip(4)
                ty = f.readu32()
                assert ty in {1,2,0x400},f.pos-4

                if ty == 0x400: f.skip(12)
                else: fe = [f.readu32(),f.readu32(),f.readu32()]

                pix = f.reads32()
                assert pix in ds,f.pos-4
                fn = ds[pix] + '/' + fn
                f.skip(8)

                if ty == 0x400: ds[ix] = fn
                else: fs.append(fe + [ty,fn])

            for fe in fs:
                f.seek(fe[2])
                writefile(fe[4],f.decompress(fe[0],(0,'none','zlib')[fe[3]],usize=fe[1]))

            f.close()
            if fs: return
        case 'ZUN GRZ':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,'rb',endian='<')
            assert f.read(4) == b'HGRZ'

            c = f.readu32()
            fs = [f.readu32() for _ in range(c+1)]
            for ix in range(c):
                f.seek(fs[ix])
                d = f.readc(fs[ix+1]-fs[ix])
                if d[:4] in {b'HGRX',b'HGRZ',b'HGRF',b'BFNT'}: ex = d[1:4].decode('ascii').lower()
                elif d[:7] == b'ZN\x1A\0\0\0\0': ex = 'grp'
                else: ex = guess_ext(d)
                writefile(f'{o}/{ix:02d}.{ex}',d)

            f.close()
            if c: return
        case 'Eutechnyx CDFILES.DAT+AR':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,'rb',endian='<')
            assert f.read(4) == b'file'

            v = f.readu32()
            if v >> 24:
                f.back(4)
                f._end = '>'
                v = f.readu32()
            assert v in {1,3}

            f.skip(4) # unk float (2)
            uc = f.readu32() + f.readu32() + f.readu32()*4 + f.readu32()
            fc = f.readu32()
            anl = f.readu32()
            bs = f.readu32()
            nc = f.readu32()
            f.skip(4 + uc)
            an = dirname(i) + '/' + basename(f.read(anl).rstrip(b'\0').decode('ascii'))
            assert exists(an),an

            offs = [f.readu32()*bs for _ in range(fc)]
            szs = [f.readu32() for _ in range(fc)]
            nof = [f.readu32() for _ in range(nc)]
            ids = {}
            for ix in range(nc):
                if f._end == '>': ty,id = f.readu8(),f.readu24()
                else: id,ty = f.readu24(),f.readu8()
                if ty in {0,0x20}: continue
                assert ty == 0x40,f'unknown type 0x{ty:02X} @ 0x{f.pos-4:06X}'
                if id in ids and ids[id][1] == 0x40:
                    assert ty != 0x40,'file overwrite'
                    continue
                ids[id] = (ix,ty)

            ns = []
            if v == 3:
                f.skip(4*nc) # null on PC
                rnc = f.readu32()
                nsz = f.readu32()
                rno = [f.readu32() for _ in range(rnc)]
                rns = []
                bo = f.pos
                for of in rno:
                    f.seek(bo + of)
                    rns.append(f.read0s('ascii'))

                bo = f.seek(bo + nsz)
                for of in nof:
                    f.seek(bo + of)
                    fn = ''
                    bs = f.read0s()
                    p = 0
                    while p < len(bs):
                        nix = bs[p];p+=1
                        if nix >= 0x80 and p < len(bs): nix = ((nix & 0x7F) << 8) | bs[p];p+=1
                        fn += rns[nix-1]
                    ns.append(fn)
            elif v == 1:
                bo = f.pos
                for of in nof:
                    f.seek(bo + of)
                    ns.append(f.read0s('ascii'))
            f.close()

            if an.lower().endswith('0.ar'):
                fds = []
                bn = an[:-4]
                for ix in range(10):
                    n = bn + f'{ix}.ar'
                    if not exists(n): break
                    fds.append(open(n,'rb'))
            else: fds = [open(an,'rb')]

            for ix in range(fc):
                dix = ids[ix]
                if dix[1] != 0x40: continue

                if ix > 0 and offs[ix] == 0: fds.pop(0).close()
                fds[0].seek(offs[ix])
                d = fds[0].read(szs[ix])
                assert len(d) == szs[ix],f'offset {offs[ix]} too big'
                writefile(o + '/' + ns[dix[0]],d)

            for fd in fds: fd.close()
            if fc: return
        case 'Eutechnyx ARC':
            TYM = {
                -1:'Directory',
                -3:'StringTable',
                1:'image',
                2:'material',
                7:'null',
                15:'faces',
                16:'verts',
            }

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,'rb',endian='<')
            assert f.read(3) == b'ARC'
            v = f.reads(1,'ascii')

            c = f.readu32('>' if v == 'N' else '<')
            fs = []
            if v == '0': bo = 0x40
            elif v in 'XPCN': bo = 0x80
            else: raise NotImplementedError(v)

            f.seek(bo)
            bo += c*0x10
            for _ in range(c):
                f.skip(4)
                fs.append((f.readu32(),f.reads32(),f.reads8(),f.readu24('>')))

            assert fs[-1][2] == -3
            sto = fs[-1][0] + bo
            drn = ''
            for ix,fe in enumerate(fs):
                if fe[1] == -1: fn = f'{ix:03d}'
                else:
                    f.seek(sto + fe[1])
                    fn = sub_path(f.read0s('ascii'))

                if fe[2] == -1:
                    drn += '/' + fn
                    mkdir(o + '/' + drn)
                if fe[2] != 0: fn += '.' + TYM.get(fe[2],f'{fe[2]:02X}')
                f.seek(bo + fe[0])
                writefile(o + '/' + drn + '/' + fn,f.readc(fe[3]))

            f.close()
            if fs: return
        case 'Eutechnyx Compressed ARC':
            raise NotImplementedError
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,'rb')
            assert f.read(3) == b'ARC'
            v = f.reads(1,'ascii')

            assert v == 'N'
            f.seek(0x74)
            assert f.read(4) == b'\xDE\xC0\xDE\xC0'
            zs,us = f.readu32('<'),f.readu32('<')
        case 'Messiah Image Resource':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.seek(0x26)
            c = f.readu16()
            for ix in range(c):
                s = f.readu32() - 0x14
                w,h = f.readu16(),f.readu16()
                f.skip(8)
                ct = f.read(4)
                if ct == b'ZZZ4': us = f.readu32();s -= 4
                else: us = 0
                writefile(f'{o}/{ix:02d}_{w}x{h}.rgba8',f.decompress(s,{b'NNNN':'none',b'ZZZ4':'lz4'}[ct],usize=us))

            f.close()
            if c: return
        case 'Bomberman Wars IDX+BIN':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(noext(i)+'.idx',endian='<')
            fd = File(noext(i)+'.bin')

            while f:
                fn = f.read(0x18).rstrip(b'\0').decode('ascii')
                fd.seek(f.readu32())
                writefile(o + '/' + fn,fd.readc(f.readu32()))

            f.close()
            fd.close()
            if listdir(o): return
        case 'K2 ConnectFile':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,'rb',endian='<')
            assert f.read(0x14) == b'ConnectFile Version '

            f.seek(0)
            k1 = (f.readu32() ^ 0xFFFFFFFF).to_bytes(4,'little')
            f.seek(0x18)
            do = f.readu32() ^ int.from_bytes(k1,'little')
            ft = File(decrypt(f.readc(do - 0x1C),'xor',k1),endian=f._end)
            c = ft.readu32()
            szs = [ft.readu32() for _ in range(c)]
            offs = [ft.readu32() for _ in range(c)]
            fns = [ft.readc(0x2C).rstrip(b'\0').decode('utf-8') for _ in range(c)]
            del ft
            assert offs[0] != 0 # bo = do if offs[0] == 0 else 0

            for ix in range(c):
                f.seek(offs[ix])
                d = f.readc(szs[ix])
                writefile(o + '/' + fns[ix],decrypt(d,'xor',(szs[ix] ^ 0xFFFFFFFF).to_bytes(4,'little')))

            f.close()
            if c: return
        case 'Cause of Death EXP':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')
            assert f.read(5) == b'CSPUD'

            c = f.readu32()
            fs = [(f.readu16(),f.readu32()) for _ in range(c)]

            for fe in fs:
                f.seek(fe[1])
                zs,us,cf = f.readu32(),f.readu32(),f.readu32()
                assert cf in {0,1},fe[1]
                d = f.decompress(zs,('none','lzma')[cf],usize=us)
                writefile(f'{o}/{fe[0]}.{guess_ext(d)}',d)

            f.close()
            if fs: return
        case 'Macross: Do You Remember Love? GKO':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            fs = [(f.read(0x10).rstrip(b'\0').decode('ascii'),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Macross: Do You Remember Love? PUD':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.skip(2)
            c = f.readu16()
            for ix in range(c):
                w,h = f.readu16(),f.readu16()
                f.skip(6)
                ty = f.readu16()
                assert ty in {0,1}
                if ty == 0: d = f.readc(f.readu32())
                else:
                    us,zs = f.readu32(),f.readu32()
                    d = f.decompress(zs,'lzss8',usize=us)
                writefile(f'{o}/{ix:03d}_{w}x{h}.pal{int((len(d)/(w*h))*8)}',d)

            f.close()
            if c: return
        case 'WWE Raw XPK+D.BIN+F.BIN':
            if db.print_try: print('Trying with custom extractor')
            bn = noext(i)
            if i.lower().endswith('.bin'): bn = bn[:-2]
            from lib.file import File
            f = File(bn + '_D.BIN',endian='<')

            fns = []
            def reade(p):
                while f:
                    ty = f.readu16()
                    if ty == 0: break
                    nl = f.readu16()
                    v = f.readu32()
                    n = p + '/' + f.reads(nl,'ascii')
                    f.padc(1)
                    if ty == 1: fns.append((v,n))
                    else:
                        mkdir(n)
                        cp = f.pos
                        f.seek(v)
                        reade(n)
                        f.seek(cp)

            f.seek(12)
            f.seek(f.readu32())
            reade(o)
            f.close()
            if not fns: return 1

            f = File(bn + '_F.BIN',endian=f._end)
            f.seek(12)
            fs = []
            while f:
                fs.append((f.readu32(),f.readu32()))
                f.skip(4) # something to do with images, sometimes WxH in u16 be, sometimes ???
            f.close()
            if not fs: return 1

            f = File(bn + '.XPK',endian=f._end)
            for fe in fns:
                f.seek(fs[fe[0]][0])
                writefile(fe[1],f.readc(fs[fe[0]][1]))

            f.close()
            if fns and fs: return
        case 'Wizards of a Waverly Place XPF':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.readu32() == 0xBADBEEF1

            vc = f.readu8()
            vs = {}
            for _ in range(vc):
                n = f.readutf16(f.readu16())
                vs[n] = f.readu32()
                assert f.readu32() in {0,1},f.pos - 4
            assert 'Engine' in vs

            of = open(f'{o}/$header.txt','w',encoding='utf-8')
            for k,v in vs.items(): of.write(f'{k}: {v}\n')
            of.close()

            v = vs['Engine']
            bp = f.pos
            if v >= 0x10: f.skip(4)
            nc = f.readu16()
            ns = {}
            if v >= 0x10:
                for _ in range(nc):
                    id = f.readu16()
                    assert f.readu32().bit_count() == 1,f.pos - 4
                    ns[id] = f.readutf16(f.readu16())

                if v >= 0x20:
                    fec = f.readu16()
                    feo = f.pos
                    f.skip(fec * 8)
                    oc = f.readu16()
                    oo = f.pos
                else:
                    fec = f.readu16()
                    oc = f.readu16()
                    oo = f.pos
                    xc = 6
                    feo = oo + oc * (4+xc)

                f.seek(feo)
                fes = [(ix,f.readu16(),f.reads16(),f.readu32() + bp) for ix in range(fec)]
                fo = min([x[3] for x in fes])

                f.seek(oo)
                if v >= 0x20:
                    xc = fo - f.pos
                    assert not xc % 2 and not xc % oc
                    xc = xc//oc - 4

                ordr = {}
                for _ in range(oc):
                    nid = f.readu16()
                    ordr[f.readu16()] = oc + 12 + nid
                    f.skip(xc)
            else:
                for _ in range(nc):
                    id = f.readu16()
                    ns[id] = f.readutf16(f.readu16())

                fc = f.readu16()
                ordr = [fc + f.readu16() for _ in range(fc)]
                fes = [(ix,f.readu16(),f.reads16(),f.readu32() + bp) for ix in range(fc)]

            fes.sort(key=lambda x:x[3])
            fes.append((0,0,0,f.size))
            for ix in range(len(fes)-1):
                fe = fes[ix]
                f.seek(fe[3])
                assert fe[2] <= 0,f'{fe} {f.read(4)}'
                d = f.decompress(fes[ix+1][3] - fe[3],'lz11' if fe[2] < 0 else 'none')
                writefile(f'{o}/{fe[0]:03d}.{guess_ext_nds(d)}',d)

            f.close()
            if fes: return
        case 'TREVA SDPC':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import decompress
            d = readfile(i)
            assert d[:4] == b'SDPC'
            us = int.from_bytes(d[4:8],'little')
            writefile(o + '/' + tbasename(i),decompress(d[8:],'lzo1x',usize=us))
            return
        case 'Konami FireBeat LZSS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import decompress
            d = readfile(i)
            us = int.from_bytes(d[:4],'little')
            writefile(o + '/' + basename(i)[:-1 if i[-1] in 'zZ' else None],decompress(d[4:],'lzss8',usize=us))
            return
        case 'JumpStart SpyMasters Resource':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.readu32() == 3

            f.padc(0x10)
            of1,sz1 = f.readu32(),f.readu32()
            f.padc(0x20)
            of2,sz2 = f.readu32(),f.readu32()
            f.seek(of1)
            fso = [(f.readu32(),f.readu32()) for _ in range(sz1//8)]
            f.seek(of2)
            ofs = [(f.readu32(),f.readu32()) for _ in range(sz2//8)]

            fs = []
            for of in ofs:
                f.seek(of[0])
                fse = fso[f.readu32()]
                usz = f.readu32()
                f.skip(4) # some float
                flgs = f.readu32()
                if flgs == 7: assert (usz - 2) == fse[1],f.pos
                else: assert usz == fse[1],f.pos
                fs.append((fse[0],fse[1],sub_path(f.read(f.readu32()).rstrip(b'\0').decode('ascii'))))

            for fe in fs:
                f.seek(fe[0])
                writefile(o + '/' + fe[2],f.readc(fe[1]))

            f.close()
            return
        case 'HAL XBIN YAML':
            if db.print_try: print('Trying with custom extractor')
            import yaml
            from lib.file import File
            f = File(i)
            assert f.read(4) == b'XBIN'
            f._end = {b'\x34\x12':'<',b'\x12\x34':'>'}[f.read(2)]
            v = f.readu8()
            f.padc(1)
            f.skip(8)
            if v >= 4: f.skip(4)

            assert f.read(4) == b'YAML'
            V = f.readu32()
            def reads():
                of = (f.pos if V >= 5 else 0) + f.readu32()
                p = f.pos
                f.seek(of)
                v = f.reads(f.readu32(),'utf-8')
                f.seek(p)
                return v
            def readn(root=False):
                if not root:
                    of = (f.pos if V >= 5 else 0) + f.readu32()
                    p = f.pos
                    f.seek(of)
                ty = f.readu32()
                assert ty in {1,2,3,4,5,6},ty

                match ty:
                    case 1: v = f.reads32()
                    case 2: v = f.readf32()
                    case 3: v = f.readu32() != 0
                    case 4: v = reads()
                    case 5:
                        c = f.readu32()
                        sp = f.pos
                        v = {}
                        if V >= 4:
                            f.skip(c * 8)
                            ordr = [f.readu32() for _ in range(c)]
                        else: ordr = list(range(c))

                        for x in ordr:
                            f.seek(sp + x * 8)
                            k = reads()
                            v[k] = readn()

                        f.seek(sp + c * 8)
                        if V >= 4: f.skip(c * 4)
                    case 6:
                        c = f.readu32()
                        v = [readn() for _ in range(c)]
                if not root: f.seek(p)
                return v

            ob = readn(True)
            if ob:
                yaml.dump(ob,xopen(o + '/' + tbasename(i) + '.yaml','w'),sort_keys=False,allow_unicode=True)
                return
        case 'Bandai PKG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'BPK0'

            dsz,do = f.readu32(),f.readu32()

            ds = []
            def readd(p):
                bp = f.pos
                xs = f.readu16()
                f.skip(2)
                es = f.readu16()
                f.skip(2)
                of,s = f.readu32(),f.readu32()
                f.padc(4)
                n = p + '/' + f.readc(es - 0x14).rstrip(b'\0').decode('shift-jis')
                if s: ds.append((of,n))
                else: mkdir(n)

                if xs:
                    ep = bp + xs
                    while f.pos < ep: readd(n)

            ep = f.seek(do) + dsz
            while f.pos < ep: readd(o)

            fs = []
            for de in ds:
                f.seek(de[0])
                c = f.readu32()//0x10
                f.back(4)
                for _ in range(c):
                    sp = f.pos + f.readu32()
                    f.skip(8)
                    fs.append((sp,f.readu32(),de[1]))

            for fe in fs:
                f.seek(fe[0])
                fn = fe[2] + '/' + f.read0s('shift-jis')
                f.seek(fe[1])
                assert f.read(4) == b'BDL0'
                us,zs = f.readu32(),f.readu32()
                f.padc(0x14)
                writefile(fn,f.decompress(zs or us,'zlib' if zs else 'none'))

            f.close()
            if fs: return
        case 'Bandai ARC':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'BARC' and f.readu16() == f.readu16() == 1

            hs = f.readu32()
            assert 0x20 >= hs >= 0x1C
            f.skip(4)
            c = f.readu32()
            assert f.readu32() == 12
            of = f.readu32()
            f.padc(hs - 0x20)
            f.seek(of)
            fs = [(f.readu32(),f.readu32(),f.readu32()) for _ in range(c)]

            for fe in fs:
                f.seek(fe[2])
                hs = f.readu16()
                fn = f.readc(hs - 2).rstrip(b'\0').decode('shift-jis')
                assert fe[1] and fe[0] != fe[1],fe
                writefile(o + '/' + fn,f.decompress(fe[1],'zlib' if fe[0] != fe[1] else 'none'))

            f.close()
            if fs: return
        case 'Metropolis Software ZAP':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            f.seek(-0x14)
            assert f.readu8() == 0x31 and f.readu8() == 0x10 and f.readu16() == 0x2003 and f.readu32() in {4,5}

            fs = []
            def reade(p:str):
                off = f.readu32()
                rp = f.pos
                f.seek(off)

                dc,fc = f.readu16(),f.readu16()
                foff = f.readu32()
                bp = f.pos
                ofs = [bp + f.readu32() for _ in range(dc)]
                for of in ofs:
                    f.seek(of)
                    n = p + '/' + f.reads(f.readu8(),'ascii')
                    reade(n)

                f.seek(foff)
                bp = f.pos
                ofs = [bp + f.readu32() for _ in range(fc)]
                for of in ofs:
                    f.seek(of)
                    n = p + '/' + f.reads(f.readu8(),'ascii')
                    fe = [n,f.readu32(),f.readu32(),f.readu32()]
                    f.skip(4) # ?
                    f.padc(4)
                    fe.append(f.readu32())
                    fs.append(fe)

                f.seek(rp)

            f.skip(4)
            reade(o)

            for fe in fs:
                f.seek(fe[1])
                writefile(fe[0],f.decompress(fe[3],'deflate' if fe[4] & 1 else 'none',usize=fe[2]))

            f.close()
            if fs: return
        case 'Pivotal Games DAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.crypto import HashLib
            hl = HashLib.dl('pivotal',db,encoding='ascii',fmt=lambda x:x.upper())
            from lib.file import File
            f = File(i)

            f.seek(4)
            vb = f.readu32('>')
            f.back(4)
            vl = f.readu32('<')
            f._end = '>' if vb < vl else '<'
            f.seek(4)
            fo = f.readu32()
            f.seek(0)

            fs = []
            while f.pos < fo:
                fe = (f.readu32(),f.readu32(),f.readu32())
                if not fe[0]: break
                fs.append(fe)

            hl.wait()
            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                if fe[0] in hl: fn = hl.get(fe[0])
                else:
                    fn = f'$unk/{fe[0]:08X}.'
                    if d[:4] == b'EOBJ': fn += 'evo'
                    elif d[:4] == b'SLOC': fn += 'loc'
                    elif d[:4] == b'imgf': fn += 'img'
                    elif d[:9] == b'Version 7' and d[10:13] == b'\r\n"': fn += 'env'
                    elif d[:11] == b'Version 4\r\n': fn += 'spl'
                    elif d[:14] == b'"Loading Bar" ': fn += 'fas'
                    elif b'// ' in d[:8] and b'REFX_' in d[:0x400]: fn += 'rfx'
                    elif d[:12] == b'\2\0\0\0\x33\0\0\0\1\0\0\0' and d[12] in {0,2} and d[13:0x10] == b'\0\0\0': fn += 'prb'
                    elif sum(d[:2]) and not sum(d[2:8]) and not sum(d[9:13]) and d[8] == 0x18: fn += 'oct'
                    elif sum(d[:2]) and not sum(d[2:6]) and d[6:8] == b'\xCD\xCD' and not sum(d[9:13]) and d[8] == 0x14: fn += 'qtd'
                    else: fn += guess_ext(d)
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'CRI ACS File':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'ACSF'

            f.skip(4) # file size
            c = f.readu32()
            f.skip(0x14) # u16 alignment + junk
            fs = []
            for _ in range(c):
                f.skip(4) # ftype
                fs.append((f.readc(0x10).rstrip(b'\0').decode('ascii'),f.readu32(),f.readu32()))

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'CRI DPF':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            bs = f.read(4).rstrip(b'\0')
            assert bs and bs.isdigit()
            bs = int(bs)

            f.skip(4)
            dc,fc = f.readu32(),f.readu32()
            if dc != 1: raise NotImplementedError
            do,fo = f.readu32(),f.readu32()

            f.seek(do)
            if f.read(1) != b'\\' or sum(f.readc(15)): raise NotImplementedError
            f.seek(fo)
            fs = []
            for _ in range(fc):
                fs.append((f.readc(0x10).rstrip(b'\0').decode('ascii'),f.readu32()*bs,f.readu32()))
                f.padc(8)

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Ludia GWTarget':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')
            assert f.read(4) == b'GWTg' and f.readu8() == 1

            v = f.reads(f.readu32(),'ascii')
            writefile(o + '/' + basename(i) + '.txt',f'{v}\n{f.readu32()}x{f.readu32()}','w')

            f.close()
            if not f: return
        case 'Microsoft .NET ResX':
            if db.print_try: print('Trying with custom extractor')
            import base64
            import xml.etree.ElementTree as ET

            tr = ET.parse(i)
            for r in tr.getroot().iter('data'):
                n,ty = r.get('name'),r.get('mimetype')
                d = r.find('value').text 
                if ty == 'application/x-microsoft.net.object.binary.base64': d,ex = base64.b64decode(d),'net.bin'
                else: d,ex = d.encode('utf-8'),mime2ext(ty)
                writefile(o + '/' + n + '.' + ex,d)

            del tr
            if listdir(o): return

    return 1
