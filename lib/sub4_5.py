from lib.main import *

def extract4_5(inp:str,out:str,t:str):
    run = db.run
    i,o = inp,out

    match t:
        case 'Retro Engine RSDKv3':
            db.try_custom()
            from lib.pyob import PyOBinX
            key = PyOBinX.dl('keys',db)
            from lib.crypto import decrypt
            from lib.file import File
            f = File(i,endian='<')

            hs = f.readu32()
            dc = f.readu16()
            ds = [(decrypt(f.read(f.readu8()),'inv_len').decode('utf-8'),hs + f.readu32()) for _ in range(dc)]
            ds.append((0,f.size))
            K1,K2 = key.wait()['rsdk3']
            for ix,de in enumerate(ds[:-1]):
                f.seek(de[1])
                xof = ds[ix+1][1]
                while f < xof:
                    fn = decrypt(f.read(f.readu8()),'inv').decode('utf-8')
                    writefile(o + '/' + de[0] + fn,decrypt(f.readc(f.readu32()),'rsdk3',K1,K2))

            f.close()
            if de: return
        case 'Retro Engine RSDKv4':
            db.try_custom()
            from lib.crypto import decrypt,HashLib
            hl = HashLib.dl('rsdk',db)
            from lib.pyob import PyOBinX
            key = PyOBinX.dl('keys',db)
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(6) == b'RSDKvB')

            c = f.readu16()
            fs = []
            for _ in range(c):
                fe = [f.readu128(),f.readu32()]
                sz = f.readu32()
                fs.append((*fe,sz & 0x7FFFFFFF,sz & 0x80000000))

            KEY = key.wait()['rsdk4']
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
                writefile(f'{o}/{tbasename(i)}.bin',bytes.fromhex(''.join(ob)))
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
        case 'The Learning Company MECC':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')

            hs = f.readu16()
            f.skip(4)
            asrt(f.read(4) == b'MECC')
            f.padc(2)
            writefile(o + '/$comment.txt',f.readc(0x40).rstrip(b'\0') + b' ' + f.readc(8).rstrip(b'\0'))
            fc = f.readu32()
            #f.skip(4)
            f.seek(hs)

            fls = [(f.reads(8,'ascii').rstrip('\0'),f.readu32(),f.readu32()) for _ in range(fc)]
            hs = f.pos
            fs = []
            for fle in fls:
                f.seek(hs + fle[2]*0x14)
                for _ in range(fle[1]):
                    tn = f.reads(8,'ascii').rstrip('\0')
                    fs.append((f'{fle[0]}/{f.readu32()}.{tn}',f.readu32(),f.readu32()))

            for fe in fs:
                f.seek(fe[2])
                writefile(o + '/' + fe[0],f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Mitsurugi KPK':
            db.try_custom()
            import zlib
            from lib.crypto import HashLib
            hl = HashLib.dl('mitsurugi',db)
            from lib.file import File,iszl
            fd = File(i)

            ps = []
            for ix in range(fd.size // 0x20):
                fd.seek(ix * 0x20)
                td = fd.read(8)
                if td[1] != 1 and iszl(td):
                    ps.append(fd.pos - 8)
                    if len(ps) == 2: break
            if len(ps) != 2:
                fd.close()
                return 1

            fd.seek(ps[0])
            td = fd.read(ps[1] - ps[0])
            zob = zlib.decompressobj()
            dd = zob.decompress(td)
            pfed = len(dd).to_bytes(4,'little') + (len(td) - len(zob.unused_data)).to_bytes(4,'little') + ps[0].to_bytes(4,'little')

            id = dirname(i)
            for pex in [id + '/' + x for x in listdir(id) if x.lower().endswith('.exe')]:
                pd = readfile(pex)
                pp = pd.find(pfed)
                if pp == -1 or not pd[pp+0x10] & 1 or pd[pp+0x11:pp+0x14] != b'\0\0\0': continue
                psp = pd.rfind(b'\0'*0x10,0,pp - 4)
                if psp == -1: continue
                f = File(pd[psp+0x10:],endian='<')
                break
            else:
                fd.close()
                return 1

            cv = 0
            fs = []
            while cv < fd.size:
                fe = (f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32())
                if fe[5] & 4: fe = (fe[0],0,0,fe[3],fe[4],fe[5])
                s = fe[2] if fe[5] & 1 else fe[1]
                s += -s%0x20
                if (fe[3] + s) > fd.size or fe[3] % 0x20 or (fe[2] and not fe[5] & 1): break
                fs.append(fe)
                cv += s
            del f

            hl.wait()
            for fe in fs:
                fd.seek(fe[3])
                d = fd.decompress(fe[2] if fe[5] & 1 else fe[1],'zlib' if fe[5] & 1 else 'none',usize=fe[1])
                if fe[0] in hl: fn = hl[fe[0]]
                else:
                    if d[:4] == b'E3\x0E\0': ex = 'e3'
                    elif d[:4] in {b'CMA2',b'W9A2'}: ex = d[:3].decode('ascii').lower()
                    else: ex = guess_ext(d)
                    fn = f'$unk/{fe[0]:08X}.{ex}'
                writefile(o + '/' + ("$deleted/" if fe[5] & 4 else "") + fn,d)

            fd.close()
            if fs: return
        case 'Sengoku Basara 2 Compressed'|'Capcom YZ2 Compressed':
            db.try_custom()
            from lib.file import decompress
            d = readfile(i)

            h,d = d[:0x20].split(b'\n')[0],d[0x20:]
            zs,us = int(h.split(b'\t')[0],16),int(h.split(b'\t')[1],16)
            if t == 'Sengoku Basara YZ2 Compressed': d = decompress(d[:zs + 4],'capcom_yz2',usize=us)
            else: d = decompress(d[:zs],'lzo1x',usize=us,db=db)
            asrt(len(d) == us)
            writefile(o + '/' + basename(i),d)
            return
        case 'Bandai PIDX':
            db.try_custom()
            from lib.crypto import decrypt
            from lib.file import File,decompress
            f = File(i,endian='<')
            asrt(f.read(4) == b'PIDX')

            dno,dnc = f.readu32(),f.readu32()
            tof,ttc,trc = f.readu32(),f.readu32(),f.readu32()
            t2o = f.readu32();f.skip(4)
            sof = f.readu32()

            f.seek(dno)
            dns = []
            for _ in range(dnc):
                dns.append(f.readu32())
                f.padc(12);f.skip(0x10)

            dns = {x:f.seekc(x + sof).read0s('ascii').lower() for x in dns}
            fds = {}
            id = dirname(i)
            for k,v in dns.items():
                if exists(id + '/' + v): fds[k] = f if v == basename(i).lower() else File(id + '/' + v,endian=f._end)
                else: fds[k] = None
            if all(x is None for x in fds.values()):
                asrt(len(fds) == 1,"Couldn't find any data files and data file count is over 1, so won't use base file")
                fds[list(fds)[0]] = f
            if any(x is None for x in fds.values()): print('WARNING: Some data files not found')

            f.seek(tof)
            tfs = [(f.readu32(),f.readu32() + sof,f.readu32(),f.readu32(),f.readu32(),f.readu32()) for _ in range(ttc)]

            fs = []
            def readd(of:int,c:int,p:str):
                mkdir(p)
                for ix in range(c):
                    fe = tfs[of + ix]
                    f.seek(fe[1])
                    n = f.read0s('ascii')
                    if fe[0] == 1: readd(fe[3],fe[2],p + '/' + n)
                    elif fe[0] == 0: fs.append((p + '/' + n,fe[3],fe[4],fe[5]))
                    else: raise NotImplementedError(f'{fe} @ 0x{tof+(of+ix)*0x18:08X}')
            readd(0,trc,o)

            f.seek(t2o)
            t2c = f.readu32()
            tos = [f.readu32() + t2o for _ in range(t2c)]
            tfs = []
            for of in tos:
                f.seek(of)
                tfs.append((f.readu32() + sof,f.readu32(),f.readu32())) # name off, data name off, fsts off
                # u32: fsts size, u32: ?

            hfst = False
            for fe in tfs:
                if fds[fe[1]] is None: continue
                p = f.seekc(fe[0]).read0s('ascii')
                hfst = True
                fd = fds[fe[1]]
                fd.seek(fe[2])

                asrt(fd.read(4) == b'FSTS')
                c,to,so = fd.readu32(),fd.readu32() + fe[2],fd.readu32() + fe[2]
                # u32: strings size
                fd.seek(to)
                fsts = [(fd.readu32() + so,fd.readu32() + fe[2],fd.readu32(),fd.readu32()) for _ in range(c)]

                for fse in fsts:
                    n = o + '/' + fd.seekc(fse[0]).read0s('ascii')
                    n = dirname(n) + '/' + p + '/' + basename(n)
                    fd.seek(fse[1])
                    asrt(fse[3] > 8)

                    key = fd.readu8() ^ 0x52;fd.back(1)
                    asrt(decrypt(fd.read(3),'xor',key) == b'RAI')
                    isnz = fd.readu8() ^ key
                    asrt((isnz & 0xFFFFFFFE) == 0x42)
                    asrt(fd.readu32() == fse[2])
                    if not isnz & 1: asrt(fse[2] == (fse[3] - 8))
                    writefile(n,decompress(decrypt(fd.readc(fse[3] - 8),'xor',key),'lzss0' if isnz & 1 else 'none',usize=fse[2]))

            for fe in fs:
                if fds[fe[1]] is None: continue
                fd = fds[fe[3]]
                fd.seek(fe[1])
                writefile(fe[0],fd.readc(fe[2]))

            for v in fds.values():
                if v is not None: v.close()
            if not f.closed: f.close()
            if fs or hfst: return
        case 'Remedy Archive System':
            db.try_custom()
            from lib.crypto import decrypt
            from lib.file import File
            fd = File(i,endian='<')
            asrt(fd.read(4) == b'RAS\0')

            key = fd.readu32()
            f = File(decrypt(fd.readc(0x20),'remedy_ras',key),endian=fd._end)
            fc,dc,isz,fsz = f.readu32(),f.readu32(),f.readu32(),f.readu32()
            v = f.readf32()
            f.skip(12)
            del f
            if v >= 1.2: fd.skip(4)

            id = decrypt(fd.readc(isz),'remedy_ras',key)
            fdd = decrypt(fd.readc(fsz),'remedy_ras',key)
            if v >= 1.3:
                asrt(fdd[-1] == 0)
                fds = fdd[:-1].decode('ascii').split('\0')
                asrt(len(fds) == dc)
            else:
                f = File(fdd,endian=fd._end)
                fds = []
                for _ in range(dc):
                    fds.append(f.read0s('ascii'))
                    f.skip(0x10)
                del f
            del fdd
            fds = [o + '/' + x.strip('/\\') for x in fds]
            for p in fds: mkdir(p)

            f = File(id,endian=fd._end)
            for _ in range(fc):
                n = f.read0s('ascii')
                s = f.readu32()
                if v >= 1.3:
                    fd.seek(f.readu32())
                    writefile(fds[f.readu32()] + '/' + n,fd.readc(s))
                else:
                    zs = f.readu32()
                    f.skip(4)
                    n = fds[f.readu32()] + '/' + n
                    f.skip(0x18)
                    if zs == s: writefile(n,fd.readc(s))
                    else:
                        asrt(fd.read(4) == b'RA->')
                        s2,zs2 = f.readu32(),f.readu32()
                        asrt(s == s2 and zs == (zs + 12))
                        asrt(writefile(n,fd.decompress(zs2,'lzss0',usize=s2)) == s2,n)
            del f,id

            fd.close()
            if fc: return
        case 'N-Space Zlib Compressed':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'\x7A\x26\xC8\x02')
            zs,us = f.readu32(),f.readu32()
            f.padc(4)
            writefile(o + '/' + basename(i),f.decompress(zs,'zlib',usize=us))
            f.close()
            return
        case 'Empire of Magic DAT':
            db.try_custom()
            from lib.crypto import decrypt
            from lib.file import File

            k = basename(i).lower().encode('ascii')
            d = decrypt(readfile(i,size=4),'empire_magic',k)
            asrt(d == b'DATA')
            f = File(decrypt(readfile(i),'empire_magic',k),endian='<')
            f.seek(4)

            c = f.readu32()
            f.padc(8)
            fs = [(0x10 + c*0x28 + f.readu32(),f.readu32(),f.reads(0x20,'ascii').rstrip('\0')) for _ in range(c)]
            for fe in fs:
                f.seek(fe[0])
                writefile(o + '/' + fe[2],f.readc(fe[1]))

            del f
            if fs: return
        case 'Destroy All Humans! DIR+PKG PS2'|'Destroy All Humans! DIR+PKG Xbox':
            raise NotImplementedError
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(8) == b'\xFA\xC7\xBB\x48\x02\x00\x00\x00')

            f.skip(0x10)
            pno,pdo,feo = f.readu32(),f.readu32(),f.readu32()
            f.seek(pno)
            pns = [f.reads(0x104,'ascii').rstrip('\0') for _ in range(f.readu32())]

            id = dirname(i)
            pes = []
            fd = {}
            f.seek(pdo)
            for _ in range(f.readu32()):
                n = pns[f.readu32()]
                if not n in fd:
                    pk = id + '/' + n + '.pkg'
                    if exists(pk): fd[n] = File(pk,endian='<')
                    else: fd[n] = None
                pes.append((n,f.readu32(),fd[n]))
                f.skip(0x28)
            if all(v is None for v in fd.values()): return 1

            f.seek(feo)
        case 'PlayStation 3 Theme':
            db.try_custom()
            from xml.dom import minidom
            import xml.etree.ElementTree as ET
            from lib.file import File,decompress
            f = File(i,endian='>')
            sig = f.read(4)
            asrt(sig in {b'P3TF',b'RAF0'})

            f.skip(4)
            tro,trs,idto,idts,sto,sts,iao,ias,fao,fas,fto,fts = [f.readu32() for _ in range(12)]
            f.seek(tro)
            tr = {}
            while f < (tro + trs):
                trep = f.pos - tro
                tre = (f.readu32() + sto,f.readu32(),f.reads32())
                f.skip(0x10)
                ats = []
                for _ in range(tre[1]):
                    no,ty = f.readu32() + sto,f.readu32()
                    if ty == 1: v = f.reads32();f.padc(4)
                    elif ty == 2: v = f.readf32();f.padc(4)
                    elif ty == 3: v = (f.readu32() + sto,f.readu32())
                    elif ty == 6: v = (f.readu32() + fto,f.readu32())
                    elif ty == 7: v = f.readu32() + idto;f.padc(4)
                    else: raise NotImplementedError(f'Attribute type {ty}')
                    ats.append((no,ty,v))
                tr[trep] = (tre[0],tre[2],ats)

            for tro,trv in tr.items():
                ats = {}
                for ae in trv[2]:
                    if ae[1] == 3:
                        f.seek(ae[2][0])
                        v = f.reads(ae[2][1],'utf-8').rstrip('\0')
                    elif ae[1] == 6: v = ae[2]
                    elif ae[1] == 7:
                        f.seek(ae[2] + 4) # skip s32 id
                        v = f.read0s('utf-8')
                    else: v = str(ae[2])
                    f.seek(ae[0])
                    ats[f.read0s('utf-8')] = v
                f.seek(trv[0])
                tr[tro] = (f.read0s('utf-8'),trv[1],ats,[])

            r = None
            for treo,tre in tr.items():
                if tre[1] == -1: r = treo
                elif tre[1] in tr and treo != tre[1]: tr[tre[1]][3].append(tre)

            asrt(not r is None)
            r = tr[r]

            def conv(e,p,par=None):
                ats = {}
                for k,v in e[2].items():
                    if isinstance(v,tuple):
                        f.seek(v[0])
                        d = f.readc(v[1])

                        if (k + 'size') in e[2]: s = e[2][k + 'size']
                        elif 'size' in e[2]: s = e[2]['size']
                        else: s = None
                        if not s is None and len(d) != int(s): d = decompress(d,'zlib')
                        if e[0] == 'bgimage':
                            if 'anim' in e[2]: ex = '.raf'
                            else: ex = '.jpg'
                        elif e[0] == 'se': ex = '.vag'
                        elif sig == b'RAF0': ex = ''
                        else: ex = '.' + guess_ext_ps2(d)

                        if ex == '.vag': fn = e[2]['id'] + '_' + k
                        elif 'id' in e[2]: fn = e[2]['id']
                        elif e[0] in {'notification',}: fn = e[0]
                        else: fn = k

                        c = 0
                        bfn = fn
                        fn += ex
                        while exists(o + '/' + p + '/' + fn):
                            fn = f'{bfn}_{c}{ex}'
                            c += 1

                        writefile(o + '/' + p + '/' + fn,d)
                        ats[k] = p + '/' + fn
                    else: ats[k] = v
                if par is not None: x = ET.SubElement(par,e[0],ats)
                else: x = ET.Element(e[0],ats)
                for ch in e[3]: conv(ch,p + '/' + e[0],x)
                return x

            r = conv(r,'')
            f.close()
            d = minidom.parseString(ET.tostring(r,'utf-8')).toprettyxml(indent='  ')
            writefile(f'{o}/${tbasename(i)}.{sig[:3].decode("ascii").lower()}.xml',d,'wt')
            return
        case 'Deadly Premonition Serial':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            while f:
                fn = f.readc(0x100).split(b'\0')[0].decode('ascii')
                s = f.readu32()
                writefile(o + '/' + sub_path(fn),f.readc(s))
                f.padc(-(s + 1)%0x10 + 1)

            f.close()
            if listdir(o): return
        case 'Sound Source Interactive IMX':
            db.try_custom()
            import re
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'\x3D\x55\x86\xED')

            # NRG = re.compile(rb'(?:\x03\x02\x01\x02[\x00-\x1F]?|\x01\x02\x06)([A-Za-z0-9\. ]{5,32})\x00') # doesn't line up with wav files :/
            WRG = re.compile(rb'RIFF(....)WAVEfmt \x10\x00{3}')
            BRG = re.compile(rb'BM(....)\x00{4}..\x00{2}\x28\x00{3}...\x00...\x00\x01\x00[\x01\x04\x08]\x00')

            f.seek(0xC4)
            o1,s1,o2,eof = f.readu32(),f.readu32(),f.readu32(),f.readu32()
            f.seek(o1)
            asrt(f.readu32() == 0x10001)
            fn = f.read0s('ascii')
            writefile(o + '/' + fn,f.readc(s1))
            f.seek(o2)
            d = f.readc(eof - o2)
            f.close()

            for ix,bp in enumerate(BRG.finditer(d)):
                writefile(f'{o}/{ix}.bmp',d[bp.start():bp.start() + int.from_bytes(bp[1],'little')])
            for ix,bp in enumerate(WRG.finditer(d)):
                writefile(f'{o}/{ix}.wav',d[bp.start():bp.start() + int.from_bytes(bp[1],'little') + 8])

            return
        case 'Hokuto No Ken IDX+BIN':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'FARC' and f.readu32() == 1)

            c = f.readu32()
            f.skip(4)
            ofs = [f.readu32() for _ in range(c)]
            fd = File(dirname(i) + '/' + f.read0s('ascii'))
            ds = []
            for of in ofs:
                f.seek(of)
                ds.append((f.readc(4),f.readu32(),f.readu32()))

            for de in ds:
                f.seek(de[1])
                asrt(f.read(4) == de[0])
                c = f.readu32()
                n = de[0].decode('ascii')
                mkdir(o + '/' + n)
                for ix in range(c):
                    fd.seek(f.readu32())
                    d = fd.readc(f.readu32())
                    if d[:4] == b'PALH': ex = 'pal'
                    elif d[:4] == b'TEXH': ex = 'tex'
                    elif d[:8] == b'FARC\1\0\0\0': ex = 'far'
                    else: ex = guess_ext_ps2(d)
                    writefile(f'{o}/{n}/{ix}.{ex}',d)

            f.close()
            fd.close()
            if ds: return
        case 'ZIPD Encrypted':
            db.try_custom()
            from lib.crypto import decrypt
            of = o + '/' + tbasename(i)
            if i.lower().endswith('.piz'): of += '.' + i[-3:][::-1]
            writefile(of,decrypt(readfile(i),'zipd'))
            return
        case 'Colin McRae Rally 2 BFL':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'CMPR')

            ep = f.seek(f.readu32() + 4)
            f.seek(f.readu32() + 8)
            fs = []
            while f < ep:
                fs.append((f.readu32(),f.readu32() + 8,f.reads(f.readu32(),'ascii')))
                f.align(4)

            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[2],f.readc(fe[0]))

            f.close()
            if fs: return
        case 'Minecraft NBT':
            import json
            ns = readfile(i,off=4,size=2)
            of = o + '/' + tbasename(i) + '.json'
            run(['nbt2json','-i',i,'-o',of] + (['-b'] if int.from_bytes(ns,'little') >= int.from_bytes(ns,'big') else []))

            try:
                nbt = json.load(open(of))['nbt']
                json.dump(nbt,open(of,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
            except: return 1
            else: return
        case 'Westwood Encrypted MIX':
            db.try_custom()
            from lib.crypto import decrypt,HashLib
            hlc,hl3 = HashLib.dl('westwood_mixc',db),HashLib.dl('westwood_mix3',db)
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu16() == 0)

            fl = f.readu16()
            asrt(fl >> 2 == 0)
            if fl & 2:
                from lib.pyob import PyOBinX
                keys = PyOBinX.dl('keys',db)
                mk = f.readc(0x50)
                mk = decrypt(mk,'rsa_le',int.from_bytes(keys.wait()['westwood_mix'],'big'))[:0x38]
                hd = f.peek(8)
                hd = decrypt(hd,'blowfish_ecb',mk)
                hs = 6 + int.from_bytes(hd[:2],'little') * 12
                hd = decrypt(f.readc(hs + (-hs % 8)),'blowfish_ecb',mk)
            else:
                hs = 6 + f.peek('u16') * 12
                hd = f.readc(hs + (-hs % 8))

            hd = File(hd,endian=f._end)
            c = hd.readu16()
            hd.skip(4) # data size
            fs = []
            hlc.wait(),hl3.wait()
            hlcc,hl3c = 0,0
            for _ in range(c):
                h = hd.readu32()
                if h in hlc: hlcc += 1
                if h in hl3: hl3c += 1
                fs.append((h,hd.readu32(),hd.readu32()))
            asrt(all(x[1] + x[2] <= f.size for x in fs))
            del hd

            if hl3c > hlcc: hl = hl3
            else: hl = hlc

            hl.wait()
            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                if fe[0] in hl: fn = hl[fe[0]]
                else: fn = f'$unk/{fe[0]:08X}.{guess_ext(d)}'
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'Slayer Engine RPE':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu32() == 1)

            c = f.readu32()
            f.padc(0x18)
            fs = []
            for _ in range(c):
                fn = f.reads(8,'ascii').rstrip('\0')
                f.skip(0x18)
                fs.append((fn,f.readu32(),f.readu32()))
                f.skip(4)

            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                writefile(o + '/' + fe[0] + '.' + guess_ext(d),d)

            f.close()
            if fs: return
        case 'Construct 2 Array':
            db.try_custom()
            import json
            d = json.load(xopen(i,'rt'))
            asrt(d['c2array'] is True and len(d['size']) == 3)

            ob = d['data']
            if d['size'][2] == 1:
                for x in range(d['size'][0]):
                    for y in range(d['size'][1]): ob[x][y] = ob[x][y][0]
                if d['size'][1] == 1:
                    for x in range(d['size'][0]): ob[x] = ob[x][0]

            if ob:
                json.dump(ob,xopen(f'{o}/{tbasename(i)}.json','wt'),ensure_ascii=False,separators=(',',':'))
                return
        case 'NIS America VFS':
            db.try_custom()
            from lib.file import File,decompress
            f = File(i,endian='<')
            asrt(f.read(4) == b'VFS3')

            fl,v,dc = f.readu32(),f.readu32(),f.readu32()
            asrt(v == 1,v)
            f.skip(dc * 0x1C)
            fc = f.readu32()
            feo = f.pos
            f.skip(fc * 0x28)

            tos = [f.readu64() for _ in range(3)]
            if fl & 0x10:
                chnko = tos.pop(0)
                if chnko == 0: f.back(8) # ???
            if fl & 0x20: ddco = tos.pop(0)
            so = tos.pop(0)
            do = f.pos

            if fl & 0x10 and chnko != 0:
                f.seek(chnko)
                ep = f.pos + f.readu32()
                chnks = []
                while f < ep:
                    chnks.append([f.reads32() for _ in range(f.readu32() // 4)])
            else: chnks = []

            if fl & 0x20:
                f.seek(ddco)
                ddcc = f.readu32()
                f.skip(4)
                ddcs = [f.readc(f.readu32()) for _ in range(ddcc)]
            else: ddcs = []

            f.seek(so)
            fsc = f.readu32()
            asrt(fsc >= fc)
            fss = [f.reads(f.readu32(),'utf-8') for _ in range(fsc)]
            dsc = f.readu32()
            asrt(dsc >= dc)
            dss = [f.reads(f.readu32(),'utf-8') for _ in range(dsc)]

            f.seek(0x10)
            ds = {}
            for _ in range(dc):
                f.skip(4)
                id = f.reads32()
                pid = f.reads32()
                f.skip(0x10)
                n = dss[id]
                if pid != -1: n = ds[pid] + '/' + n
                ds[id] = n

            f.seek(feo)
            fs = [(f.readu64() + do,f.readu64(),f.readu64(),f.readu32(),f.readu32(),f.readu32(),f.readu32()) for _ in range(fc)]

            def dec(d,fe):
                if fe[5] & 2:
                    if fe[5] & 1:
                        dci = fe[5] >> 16
                        dd = ddcs[dci] if fl & 0x20 and dci != 0xFFFF else None
                        if chnks:
                            chnk = chnks[fe[4]]
                            d = decompress(d,'nis_zstd',chunks=chnk,usize=fe[2],dict=dd)
                        else: d = decompress(d,'zstd',usize=fe[2],dict=dd)
                    else: d = decompress(d,'zlib')
                writefile(o + '/' + ds[fe[6]] + '/' + fss[fe[4]],d)
            p = LimitedPool()
            for fe in fs:
                f.seek(fe[0])
                d = f.readc(fe[1])
                p.put(dec,d,fe)
            f.close()
            p.close()
            for dn in ds.values(): mkdir(o + '/' + dn)
            if fs: return
        case 'HAL VPK0':
            db.try_custom()
            from lib.file import decompress
            of = o + '/' + basename(i)
            if of.lower().endswith(('.vpk','.vpk0')): of = noext(of)
            writefile(of,decompress(readfile(i),'vpk0'))
            return
        case 'L.A. Rush DIR+RES':
            db.try_custom()
            from lib.file import File
            f = File(noext(i) + '.dir',endian='<')

            c = f.readu32()
            asrt(c & 0x80000000)
            fd = File(noext(i) + '.res')
            for _ in range(c & 0x7FFFFFFF):
                fn = f.reads(0x20,'ascii').rstrip('\0')
                for ix in range(3):
                    fd.seek(f.readu32())
                    writefile(f'{o}/{fn}.{ix}',fd.readc(f.readu32()))

            f.close()
            fd.close()
            if listdir(o): return
        case 'L.A. Rush Compressed':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'k9CP')

            us = f.readu32()
            f.skip(4)
            writefile(o + '/' + tbasename(i),f.decompress(None,'zlib',usize=us))
            f.close()
            return
        case 'L.A. Rush AClump':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu64() == 0)

            fs = []
            off = f.size
            while f < off:
                fe = (f.readu32(),f.readu32())
                if fe[0] == 0: break
                off = min(off,fe[0])
                fs.append(fe)

            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                writefile(f'{o}/{ix}.bin',f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Pitbull Syndciate BigFile IDX+BIN':
            db.try_custom()
            from lib.file import File
            f = File(noext(i) + '.idx',endian='<')
            fd = File(noext(i) + '.bin',endian='<')
            asrt(fd.read(0x1B) == b'BigFileHeader for BigFile V')

            fd.seek(0)
            writefile(o + '/$comment.txt',fd.read(0x800).split(b'\0')[0])

            fs = [(f.reads(0x18,'ascii_mask').rstrip('\0'),f.readu32(),f.readu32()) for _ in range(f.size // 0x20)]
            f.close()
            ds = [x for x in fs if x[1] == 0]
            ds.append((0,0,len(fs)))
            for ix,de in enumerate(ds[:-1]):
                for fix in range(de[2],ds[ix+1][2]):
                    fe = fs[fix]
                    fd.seek(fe[1] * 0x800)
                    writefile(f'{o}/{de[0]}/{fe[0]}',fd.readc(fe[2]))

            fd.close()
            if fs: return
        case 'Black Lantern Studios DB':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu64() == 0)

            c = f.readu32()
            do = 12 + c*15
            fs = [(f.readu16(),f.readu32() + do,f.readu32(),f.seekc(4,1).readbool()) for _ in range(c)]

            fs.sort(key=lambda x:x[1])
            fs.append((0,f.size,0))
            for ix,fe in enumerate(fs[:-1]):
                f.seek(fe[1])
                d = f.decompress(fs[ix+1][1] - fe[1],'lz11' if fe[3] else 'none',usize=fe[2])
                writefile(f'{o}/{fe[0]}.{guess_ext_nds(d)}',d)

            f.close()
            if fs: return
        case 'Snail Mail DAW':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            f.seek(8)
            c = f.readu32()
            f.align(0x20)
            fs = []
            for _ in range(c):
                fs.append((f.readu32(),f.readu32(),f.readu32(),f.readu32()))
                f.align(0x20)

            for fe in fs:
                f.seek(fe[0])
                fn = o + '/' + f.read0s('ascii')
                if fn[-1] in '/\\' and fe[3] == fe[2] == 0: mkdir(fn)
                else:
                    f.seek(fe[1])
                    if fe[3]: d = f.decompress(fe[3],'lz11',usize=fe[2])
                    else: d = f.readc(fe[2])
                    writefile(fn,d)

            f.close()
            if fs: return
        case 'Legaia 2 DIR+BIN':
            db.try_custom()
            from lib.pyob import PyOBinX
            keys = PyOBinX.dl('keys',db)
            from lib.crypto import decrypt
            from lib.file import File

            bn = noext(i)
            asrt(exists(bn + '.bin'))
            fds = [xopen(bn + '.bin','rb')]
            for ix in range(1,10):
                if not exists(f'{bn}{ix}.bin'): break
                fds.append(xopen(f'{bn}{ix}.bin','rb'))
            fds = [(fd,fd.seek(0,2)) for fd in fds]
            f = File(decrypt(readfile(i),'legaia2',keys.wait()['legaia2']),endian='<')

            exts = [f.reads(4,'ascii').lstrip('\0')[::-1] for _ in range(0x40)]
            def readd(p:str=None):
                n = f.reads(8,'ascii').lstrip('\0')[::-1]
                dc,fc = f.readu16(),f.readu16()
                ep = f.readu32() * 0x10 + f.pos

                if p is None and n == 'ROOT': p = o
                else: p = p + '/' + n
                mkdir(p)

                for _ in range(fc):
                    n = f.reads(8,'ascii').lstrip('\0')[::-1]
                    ex = exts[f.readu16()]
                    if ex: n += '.' + ex
                    sz = f.readu16() * 0x800
                    off = f.readu32() * 0x800

                    for ix,fd in enumerate(fds):
                        if off <= fd[1]:
                            fdp = ix
                            break
                        else: off -= fd[1]
                    else: raise ValueError(f'Offset too big for all files ({len(fds)}, 0x{off:08X})')

                    fds[fdp][0].seek(off)
                    d = fds[fdp][0].read(sz)
                    if len(d) != sz:
                        fds[fdp + 1][0].seek(0)
                        d += fds[fdp + 1][0].read(sz - len(d))
                    writefile(p + '/' + n,d)
                for _ in range(dc): readd(p)
                f.seek(ep)

            readd()
            f.close()
            for fd in fds: fd[0].close()
            if listdir(o): return
        case 'IBM AIX Backup':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.peek('u16') == 9 and f.peek('u8',poffset=3) == 0xEA)

            xinf = []
            sc = 0
            gts = None
            fs = {}
            byn = None
            while f.pos + 4 < f.size:
                if (byn is False and f.peek('u32') == 0) or (byn is True and f.peek('u32') == 0xF6F6F6F6): break
                rt,rst = f.readu8(),f.readu8()
                f.skip(1) # chksum, idk what algo
                asrt(f.readu8() == 0xEA,lambda:f.fmt('§@§'))

                if rt == 9 and rst == 0:
                    if f.left < 0x44: break
                    f.skip(4)
                    gts = f.readu32()
                    f.skip(8)
                    dev1 = f.reads(0x10,'latin-1').split('\0')[0]
                    byn = not dev1.startswith('/dev/')
                    xinf.append(f"Device 1: {dev1}\nDevice 2: {f.reads(0x10,'latin-1').split('\0')[0]}\nUser: {f.reads(0x10,'latin-1').split('\0')[0]}")
                    f.skip(4)
                elif byn and rt == 1:
                    if f.left < 4: break
                    f.skip(4)
                    bp = f.pos
                    while f.pos + 4 < f.size:
                        if f.peek('u8') <= 15 and f.peek('u8',poffset=3) == 0xEA: break
                        f.skip(8)

                    sz = f.pos - bp
                    f.seek(bp)
                    d = f.readc(sz)
                    fn = f'{o}/$special{sc}.{"txt" if istext(d) else guess_ext(d)}'
                    writefile(fn,d)
                    if gts: set_ftime(fn,gts)
                    sc += 1
                elif byn and rst == 9:
                    if f.left < 0x38: break
                    f.skip(4)
                    m = f.readu16() & 0o170000
                    asrt(m in {0o040000,0o100000,0o120000},f.pos - 12,err=NotImplementedError)
                    f.skip(6)
                    s = f.readu32()
                    ts = (f.readu32(),f.readu32(),f.readu32())
                    f.skip(0x10)
                    fn = f.read0s('latin-1')
                    f.align(8)
                    fn = o + '/' + sanitize_relative(fn)
                    if s > f.left: s = max(f.left,0)
                    if m == 0o040000:
                        asrt(s == 0)
                        mkdir(fn)
                    elif m == 0o120000:
                        tfn = f.readc(s).split(b'\0')[0].decode('latin-1')
                        f.align(8)
                        tfn = o + '/' + sanitize_relative(tfn)
                        symlink(tfn,fn)
                    else:
                        writefile(fn,f.readc(s))
                        f.align(8)
                        set_ftime(fn,ts[2],ts[1],ts[0])
                elif byn and rst == 11:
                    if f.left < 0x44: break
                    f.skip(8)
                    m = f.readu32() & 0o170000
                    asrt(m in {0o040000,0o100000,0o120000},f.pos - 0x10,err=NotImplementedError)
                    f.skip(8)
                    s = f.readu32()
                    ts = (f.readu32(),f.readu32(),f.readu32())
                    f.skip(0x18)
                    fn = f.read0s('latin-1')
                    f.align(8)
                    if m != 0o120000 and f.peek('u32') == 2: f.skip(0x28)
                    fn = o + '/' + sanitize_relative(fn)
                    if s > f.left: s = max(f.left,0)
                    if m == 0o040000:
                        asrt(s == 0)
                        mkdir(fn)
                    elif m == 0o120000:
                        tfn = f.readc(s).split(b'\0')[0].decode('latin-1')
                        f.align(8)
                        tfn = o + '/' + sanitize_relative(tfn)
                        symlink(tfn,fn)
                    else:
                        writefile(fn,f.readc(s))
                        f.align(8)
                        set_ftime(fn,ts[2],ts[0],ts[1])
                elif byn and rst == 12:
                    if f.left < 0x4C: break
                    f.skip(8)
                    m = f.readu32() & 0o170000
                    asrt(m in {0o040000,0o100000,0o120000},f.pos - 0x10,err=NotImplementedError)
                    f.skip(8)
                    s = f.readu32()
                    ts = (f.readu32(),f.readu32(),f.readu32())
                    f.skip(0x20)
                    fn = f.read0s('latin-1')
                    f.align(8)
                    fn = o + '/' + sanitize_relative(fn)
                    if s > f.left: s = max(f.left,0)
                    if m == 0o040000:
                        asrt(s == 0)
                        mkdir(fn)
                    elif m == 0o120000:
                        tfn = f.readc(s).split(b'\0')[0].decode('latin-1')
                        f.align(8)
                        tfn = o + '/' + sanitize_relative(tfn)
                        symlink(tfn,fn)
                    else:
                        writefile(fn,f.readc(s))
                        f.align(8)
                        set_ftime(fn,ts[2],ts[0],ts[1])
                elif not byn and rt == 1 and rst == 3:
                    if f.left < 4: break
                    f.skip(4)
                    bp = f.pos
                    while f.pos + 4 < f.size:
                        if f.peek('u8') != 1 and f.peek('u8',poffset=3) == 0xEA: break
                        f.skip(8)

                    sz = f.pos - bp
                    f.seek(bp)
                    d = f.readc(sz)
                    fn = f'{o}/$bitmap{sc}.bin'
                    writefile(fn,d)
                    if gts: set_ftime(fn,gts)
                    sc += 1
                elif byn is False and rt == 0x3E and rst == 1:
                    if f.left < 0x1E4: break
                    f.skip(4)
                    writefile(f'{o}/$inode{sc}.tbl',f.readc(0x1E0))
                    while f.pos + 4 < f.size:
                        if f.peek('u16') == 0x0806 and f.peek('u8',poffset=3) == 0xEA: break
                        f.skip(8)
                elif byn is False and rt == 6 and rst == 8:
                    if f.left < 0x2C: break
                    f.skip(2)
                    id = f.readu16()
                    m = f.readu16() & 0o170000
                    asrt(m in {0o040000,0o100000,0o120000},f.pos - 10,err=NotImplementedError)
                    f.skip(6)
                    s = f.readu32()
                    ts = (f.readu32(),f.readu32(),f.readu32())
                    f.skip(0x10)
                    if s > f.left: s = max(f.left,0)

                    if m == 0o040000:
                        es = [(f.readu16(),sub_path(f.reads(14,'latin-1').split('\0')[0])) for _ in range(s//0x10)]
                        fs[id] = es
                    else:
                        fs[id] = {'o':f.pos,'m':m,'s':s,'t':ts}
                        f.skip(s)
                        f.align(8)
                else: raise NotImplementedError(f.fmt(byn,rt,rst,'§@',back=4))

            if fs:
                for id,fe in fs.items():
                    if isinstance(fe,list):
                        i1 = i2 = None
                        for cid,cn in fe:
                            if cn == '.': i1 = cid
                            elif cn == '..': i2 = cid
                        if i1 == i2 == id: r = id;break
                else: raise ValueError('No root found')

                l = [r]
                ps = {r:''}
                dn = set()
                while l:
                    pid = l.pop(0)
                    if pid in dn: continue
                    dn.add(pid)
                    if isinstance(fs[pid],dict): continue
                    pp = ps[pid]
                    for cid,cn in fs[pid]:
                        ps[cid] = sanitize_relative(pp + '/' + cn)
                        if cid in fs and isinstance(fs[cid],list):
                            mkdir(o + '/' + ps[cid])
                            l.append(cid)

                for id,fe in fs.items():
                    if not isinstance(fe,dict): continue
                    f.seek(fe['o'])
                    fn = o + '/' + ps[id]
                    if fe['m'] == 0o120000:
                        tfn = f.readc(fe['s']).split(b'\0')[0].decode('latin-1')
                        tfn = o + '/' + sanitize_relative(tfn)
                        symlink(tfn,fn)
                    else:
                        writefile(fn,f.readc(fe['s']))
                        set_ftime(fn,fe['t'][2],fe['t'][1],fe['t'][0])

            f.close()
            if xinf:
                writefile(o + '/$info.txt','\n\n'.join(xinf),'wt')
                if gts: set_ftime(o + '/$info.txt',gts)
                return
        case 'CP/M HUF':
            db.try_custom()
            from lib.file import File,BitReader
            f = File(inp,endian='<')
            asrt(f.readu16() == 0x1BD)

            c = f.readu16()
            xs = f.readu16()
            do = f.readu32()
            x = f.readc(xs)

            br = BitReader(f)
            huf = [None] * 0x200
            stck = []
            rt = 0
            nc = 1
            xp = 0
            while f < do or br.p != 8:
                if br.get_bit_l():
                    if nc + 1 >= 0x200: raise ValueError
                    huf[rt] = (nc,nc + 1)
                    stck.append(nc + 1)
                    rt = nc
                    nc += 2
                else:
                    try: huf[rt] = (x[xp],-1)
                    except Exception as e:
                        print(f'{e.__class__.__name__}: {e}')
                        console()
                        raise
                    xp += 1
                    if not stck: break
                    rt = stck.pop()
            else: raise ValueError

            def get_huf():
                n = 0
                while huf[n][1] != -1:
                    n = huf[n][0 if br.get_bit_l() else 1]
                return huf[n][0]

            f.seek(do)
            fs = [(f.readu32(),f.readu32(),f.readu32(),f.readu8()) for _ in range(c)]
            for fe in fs:
                br.seek(fe[0])
                fn = bytearray()
                for _ in range(0x1000):
                    b = get_huf()
                    if b == 0: break
                    fn.append(b)
                else: raise ValueError(fn[:0x10])
                fn = sanitize_relative(fn.decode('ascii'))

                br.seek(fe[2])
                d = bytes([get_huf() for _ in range(fe[1])])
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return

    return 1
