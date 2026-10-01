from .main import *

def extract4_6(inp:str,out:str,t:str) -> bool:
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
            fd = File(noext(i),endian=f.endian)

            c = f.readu32()
            fs = [(f.readu32(),f.readu64()) for _ in range(c)]
            del f
            fs.append((0,fd.size))

            for ix,fe in enumerate(fs[:-1]):
                fd.seek(fe[1])
                f = File(fd.decompress(fs[ix + 1][1] - fe[1],'zlib'),endian=fd.endian)
                dn = f'{o}/{fe[0]:08X}'
                mkdir(dn)
                c = f.readu32()
                for ix in range(c):
                    s = f.peek('u32')
                    asrt(s >= 8)
                    if s >= 12: n = f'{f.peek("u32",offset=8):08X}'
                    else: n = f'{ix:03d}'
                    tid = f.peek("u32",offset=4)
                    if not tid in TMAP: ex = f'{tid:08X}'
                    else: ex = TMAP[tid]
                    writefile(f'{dn}/{n}.{ex}',f.readc(s))

            fd.close()
            if fs: return
        case 'ZPackage':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(10) == b'ZPackage1\0')

            while f:
                xo = f.readu32()
                n = o + '/' + f.read0s('ascii')
                ts = dos2unix(f.readu16(),f.readu16())
                writefile(n,f.decompress(xo - f.pos,'zlib'))
                set_ftime(n,ts)

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
        case 'AIRNovel Package':
            db.try_custom()
            import zipfile
            z = zipfile.ZipFile(i,'r',strict_timestamps=False,metadata_encoding='utf-8')
            nl = z.namelist()
            z.close()

            db.set_temp_print(False)
            r = extract(i,o,'ZIP')
            db.reset_temp_print()
            if r: return r

            import xml.etree.ElementTree as ET
            app = ET.fromstring(XMLNSRG.sub('',readfile(o + '/META-INF/AIR/application.xml','rt')))
            swf = app.find('initialWindow').find('content').text
            del app

            osw = os.path.join(o,'$' + os.path.basename(swf))
            r = extract(os.path.join(o,swf),osw,'Shockwave Flash')
            if r: return r

            if any(x.endswith('_') for x in nl):
                prj = ET.parse(o + '/config.anprj').getroot()
                cl = prj.find('coder').get('len')
                if cl.startswith('0x'): cl = int(cl[2:],16)
                else: cl = int(cl)
                del prj

                import re,ast
                from lib.crypto import decrypt

                mng = readfile(osw + '/scripts/com/fc2/blog38/famibee/AIRNovel/LoadMng.as','rt')
                k = re.search(r'new CriptRC4\((".+?")\);',mng)
                if k: k = k[1]
                else: k = re.search(r'private static const (?P<n>[\w_]+):String = (".+?");\s*private static var [_\w]+:CriptRC4 = new CriptRC4\((?P=n)\);',mng)[2]
                key = ast.literal_eval(k).encode('utf-8')
                fullr = re.compile(re.search(r'private static const REG_EXT_FULL_CODE:RegExp = /(.+)/;',mng)[1])
                for x in nl:
                    if x.endswith('_') and isfile(o + '/' + x):
                        d = readfile(o + '/' + x)
                        if fullr.match(x): ed = len(d)
                        else: ed = min(len(d),cl)
                        writefile(o + '/' + x[:-1],decrypt(d[:ed],'airrc4',key) + d[ed:])
                        remove(o + '/' + x)
            return
        case 'MSKN 2 Archive':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(9) == b'_MCT\0KSLZ')
            f = f.decompress(File,'zlib',_close=True)

            writefile(o + '/$info.txt',f"""Name: {f.reads(f.readu32())}
Version: {f.reads(f.readu32())}
Author: {f.reads(f.readu32())}
Unknown 1: {f.reads(f.readu32())}
Unknown 2: {f.reads(f.readu32())}""")
            c = f.readu8()
            f.skip(1)
            for _ in range(c):
                f.skip(2)
                n = f.reads(f.readu32())
                w,h = f.readu32(),f.readu32()
                writefile(f'{o}/Images/{n}.{w}x{h}.rgba8',f.readc(w*h*4))

            f.skip(2)
            c = f.readu16()
            f.skip(2)
            for ix in range(c):
                n = f.reads(f.readu32())
                writefile(f'{o}/Layouts/{ix}.{n}',f.readc(f.readu32()))

            kv = {}
            c = f.readu8() + 1
            for _ in range(c):
                k = f.reads(f.readu32())
                asrt(f.reads(f.readu32()) == ':',f.pos)
                kv[k] = f.reads(f.readu32())
            writefile(o + '/config0.json',kv,'j',indent=4)
            kv = {}
            c = f.readu32()
            for _ in range(c):
                k = f.reads(f.readu32())
                asrt(f.reads(f.readu32()) == ':',f.pos)
                kv[k] = f.reads(f.readu32())
            writefile(o + '/config1.json',kv,'j',indent=4)
            kv = {}
            c = f.readu8() + 1
            for _ in range(c):
                k = f.reads(f.readu32())
                asrt(f.reads(f.readu32()) == ':',f.pos)
                kv[k] = f.reads(f.readu32())
            writefile(o + '/config2.json',kv,'j',indent=4)
            return
        case 'Origin Systems Setup Archive':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(0x1C) == b'(C) 1994 Origin Systems Inc.')
            f.padc(0x34)

            f.skip(4)
            c = f.readu32()
            f.seek(0x80)
            fs = [(f.readu32(),f.readu32(),f.reads(13).rstrip('\0')) for _ in range(c)]
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                fn = fe[2] or f'${ix:02d}.bin'
                writefile(o + '/' + fn,f.readc(fe[1]))

            f.close()
            if fs: return
        case 'ProtectIt/2 Encrypted':
            db.try_custom()
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='<')
            asrt(f.read(4) == b'PIT2')

            # key = crc_hash(key, 'protectit2')
            # original program just uses this as verification for the processed key but it's just the actual key so yay
            k = decrypt(f.readc(0x10),'xor',b'ProtectIt/2 OS/2')
            fn = f.reads(0x104,'ascii').rstrip('\0')
            d = f.read()
            f.close()
            writefile(o + '/' + fn,decrypt(d,'xor',k))
            return
        case 'Nexon PKN':
            from lib.file import File,decompress
            from lib.crypto import decrypt,crc_hash

            d = readfile(i)
            for k in (basename(i),basename(i).lower()):
                k = crc_hash(k,'snow2_nexon',size=16)
                for p in range(0x3DA): # block size - min entry size
                    d1 = decrypt(d[p:p + 0x30],'snow2_nexon',k)
                    nl = int.from_bytes(d1[:4],'little')
                    if nl > 0x1FFF or nl == 0: continue
                    if not istext(d1[4:4 + nl*2],'utf-16le',filename=True): continue
                    break
                else:continue
                break
            else: return 1

            if len(d) > p + 0x2000000: fss = 0x2000000
            else: fss = len(d) - p - (-p % 4)
            f = File(decrypt(d[p:p + fss],'snow2_nexon',k),endian='<')
            hchk = bool(f.peek('u32',offset=4 + f.peek('u32')*2) >> 3)

            fs = []
            while f:
                nl = f.readu32()
                if nl > 0x1FFF or nl == 0: break
                try: n = f.readutf16(nl)
                except UnicodeDecodeError: break
                if hchk: chk = f.readu32()
                fe = (f.readu32(),f.readu32(),f.readu32(),f.readu32())
                k = f.readc(0x10)
                if hchk: asrt(chk == crc_hash((*fe,*k),'sum32'))
                fs.append((n,*fe,k))
            bp = p + f.pos + -f.pos % 4
            bp += -bp % 0x400
            del f

            if not hchk: bn = tbasename(i).rstrip('0123456789_')
            for fe in fs:
                if fe[1] & 6:
                    hn = fe[0].replace('\\','/')
                    if not hchk: hn = bn + '/' + hn
                    k = crc_hash(hn,'snow2_nexon',size=16,key=fe[5])

                of = bp + fe[2] * 0x400
                fd = d[of:of + fe[4] + (-fe[4] % 4)]
                if fe[1] & 2: fd = decrypt(fd,'snow2_nexon',k)[:fe[4]]
                if fe[1] & 4:
                    sz = min(0x400,fe[4]) - (-fe[4] % 4)
                    fd = decrypt(fd[:sz],'snow2_nexon',k) + fd[sz:]
                if fe[1] & 1: fd = decompress(fd,'zlib',usize=fe[3])
                writefile(o + '/' + fe[0],fd)

            del d
            if fs: return
        case 'Rage Software MNG':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'ZGWH')

            c = f.readu32()
            fs = [(f.read0s('ascii'),f.readu32(),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[3])
                writefile(o + '/' + fe[0],f.decompress(fe[1],'zlib' if fe[1] != fe[2] else 'none',usize=fe[2]))

            f.close()
            if fs: return
        case 'Deep Silver Volition VPP':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu32() == 0x51890ACE and f.readu32() in {1,3})

            c = f.readu32()
            f.skip(4)
            a = f.readu32()
            f.align(a)
            fs = [(f.reads(0x18,'ascii').rstrip('\0'),f.readu32(),f.readu32()) for _ in range(c)]
            f.align(a)

            for fe in fs:
                writefile(o + '/' + fe[0],f.decompress(fe[2],'zlib',usize=fe[1]))
                f.align(a)
            f.close()
            if fs: return
        case 'Slayer Engine DAT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            c = f.readu32()
            asrt(c <= 0xB4) # max file entries in fixed size 0x4000 header
            f.padc(0x21C)
            fs = [(f.readu32(),f.readu32(),f.reads(0x50,'ascii').rstrip('\0')) for _ in range(c)]

            f.seek(0x4000)
            for fe in fs:
                ep = f.pos + fe[1]
                writefile(o + '/' + fe[2],f.readc(fe[0]))
                f.seek(ep)

            f.close()
            if fs: return
        case 'Red Faction II TOC Group+Packfile':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            f.read0s('ascii') # name
            dr = f.read0s('ascii')

            ty = f.readu32()
            bc = f.readu32()
            if ty & 2:
                asrt(bc == 1,'more than one packfile')
                fd = File(dirname(i) + '/' + os.path.relpath(f.read0s('ascii'),dr))
                c = f.readu32()
                for _ in range(c):
                    n,s = f.read0s('ascii'),f.readu32()
                    fd.seek(f.readu32())
                    writefile(o + '/' + n,fd.readc(s))

                f.close()
                fdp = fd.pos
                fd.close()
                if fdp != 0: return
            else:
                f.close()
                raise NotImplementedError('unsupported TOC type')
        case 'Etrange Overlord Encrypted Unity Bundle':
            db.try_custom()
            from lib.pyob import PyOBinX
            keys = PyOBinX.dl('keys',db)
            from lib.crypto import decrypt,crc_hash
            d = readfile(i)
            k = crc_hash(keys.wait()['etrange'],'pbkdf2_sha1',key=tbasename(i)[:0x10].ljust(0x10,'_').encode('utf-8'),c=1000,size=0x10)
            of = o + '/' + basename(i)
            dd = decrypt(d[:0x80],'aes_ctr_le',k)
            asrt(dd[:8] == b'UnityFS\0')
            writefile(of,dd + d[0x80:])
            extract(of,o,'Unity Bundle')
            return
        case 'Synetic SYN':
            db.try_custom()
            from lib.file import File,decompress
            f = File(i,endian='<')
            asrt(f.read(4) == b'FNYS')

            c = f.readu32()
            f.padc(8)
            fs = [(f.reads(0x18,'latin-1').split('\0')[0],f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                asrt(fe[2] > 4)
                d = f.readc(fe[2])
                if d[:4] == b'!SSM':
                    raise NotImplementedError('MSS! encrypted')
                    us = int.from_bytes(d[4:8],'little')
                    d = d[0x10:]
                else:
                    us = int.from_bytes(d[:4],'little')
                    d = d[4:]
                d = decompress(d,'lzss0_msb',usize=us)
                writefile(o + '/' + fe[0],d)

            f.close()
            if fs: return
        case 'MediaStation CXT':
            db.try_custom()
            from lib.file import File
            fnm = {}
            if exists(dirname(i) + '/PROFILE._ST'):
               for fn in readfile(dirname(i) + '/PROFILE._ST','rt').split('\n!\n',2)[1].split('\n'):
                   if not fn: continue
                   fn,id,*_ = fn.split()
                   if fn == '*': continue
                   fnm[int(id)] = fn

            f = File(i,endian='<')
            asrt(f.readu32() == 0x4949 and f.readu32() == 0xEEEE)
            c = f.readu32()
            f.seek(f.readu32())
            fs = [(f.readu16(),f.readu32(),f.readu32(),f.padc(4)) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                fn = fnm.get(fe[0],str(fe[0])) + '.'
                if d[:4] == b'RIFF' and d[8:12] == b'IMTS': fn += 'stm'
                else: fn += guess_ext(d)
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'Marvel Ultimate Alliance 2 PAK':
            db.try_custom()
            from lib.file import File
            from lib.crypto import crc_hash
            f = File(i,endian='>')
            asrt(f.read(4) == b'\x1AAGI' and f.readu32() == 4)

            inf = {}
            if exists(noext(i) + '.igx'):
                import xml.etree.ElementTree as ET
                xml = ET.parse(noext(i) + '.igx').getroot()
                asrt(xml.tag == 'igx')
                for fe in xml.findall('object[@buildInfo]'):
                    n = fe.get('buildInfo').lower().split('.')
                    asrt(len(n) == 2 and n[0] == n[1])
                    si = {}
                    fn = fe.find('var[@name="_fileName"]')
                    if not fn is None: si['fn'] = fn.get('value')
                    dt = fe.find('comment[@name="creation_time"]')
                    if not dt is None: si['dt'] = dt.get('value')
                    if si: inf[n[0]] = si
                del xml

            f.skip(4)
            c = f.readu32()
            f.skip(8)
            so = f.seek(f.readu32())
            ss = [f.seekc(so + x).read0s('utf-8') for x in f.readil(4,c,end='<')]
            ss = {crc_hash(x.encode('utf-8'),'fnv1a_32'):sub_path(x) for x in ss}

            f.seek(0x30)
            hshs = f.readil(4,c)
            fs = []
            for ix in range(c):
                fs.append((ss[hshs[ix]],f.readu32(),f.readu32()))
                asrt(f.reads32() == -1,f.pos)

            for fe in fs:
                f.seek(fe[1])
                bn = basename(fe[0]).lower()
                if bn in inf and 'fn' in inf[bn]: fn = inf[bn]['fn']
                else: fn = fe[0]
                writefile(o + '/' + fn,f.readc(fe[2]))
                if bn in inf and 'dt' in inf[bn]: set_ftime(o + '/' + fn,str2unix(inf[bn]['dt']))

            f.close()
            if fs: return
        case 'Sandustry Save':
            db.try_custom()
            import json
            from lib.file import decompress
            inf,d = readfile(i).split(b'\n',1)

            h = json.loads(inf.decode('utf-8'))
            ts = str2unix(h['timestamp'])
            ts = (ts - h['playTime'] / 1000,ts)
            console()
            writefile(o + '/info.json',inf)
            set_ftime(o + '/info.json',*ts)
            if d.startswith(b'\x1F\x8B'): d = decompress(d,'gzip')
            writefile(o + '/data.json',d)
            set_ftime(o + '/data.json',*ts)
            return
        case 'Zip-Archive':
            db.try_custom()
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='<')
            f.seek(-3)
            asrt(f.read(3) == b'PT&')

            f.back(7)
            flg = f.peek('u16')
            tabs = f.peek('u16',offset=2)
            pws = flg >> 3
            # files aren't encrypted, password just get's checked by application
            if pws:
                f.back(pws)
                writefile(o + '/$password.txt',decrypt(f.peek(pws),'croll',flg & 3).decode('cp850'))

            ep = f.back(tabs) + tabs
            if flg & 4:
                asrt(f.readu8() == 0)
                bn = sub_path(f.reads(f.readu8(),'cp850'))
                mkdir(o + '/' + bn)
            fs = []
            while f < ep:
                if flg & 4:
                    if not fs: dr = bn
                    else: dr = bn[:f.readu8()] + f.reads(f.readu8(),'cp850')
                else: dr = ''
                fnl = f.readu8()
                # asrt(fnl & 0x80,lambda:f.fmt('§@§')) # changing this does not seem to do anything (tested with hex edited sample)
                fs.append((dr + f.reads(fnl & 0x7F,'cp850'),f.readu32()))

            f.seek(0)
            for fe in fs:
                writefile(o + '/' + sanitize_relative(fe[0]),f.decompress(fe[1],'implode',db=db))

            f.close()
            if fs: return
        case 'Compart Character Set':
            REPL = {
                'SP':'\x20',
                'NBSP':'\xA0',
                'ST':'\x9C',
                'SSA':'\x86',
                'EPA':'\x97',
                'RI':'\x8D',
                'SS2':'\x8E',
                'OSC':'\x9D',
                'NEL':'\x85',
                'ESA':'\x87',
                'EOM':'EM',
                'PU2':'\x92',
                'SS3':'\x8F',
                'PAD':'\x80',
                'HOP':'\x81',
                'BPH':'\x82',
                'NBH':'\x83',
                'IND':'\x84',
                'HTS':'\x88',
                'HTJ':'\x89',
                'VTS':'\x8A',
                'PLD':'\x8B',
                'PLU':'\x8C',
                'DCS':'\x90',
                'PU1':'\x91',
                'STS':'\x93',
                'CCH':'\x94',
                'MW':'\x95',
                'SPA':'\x96',
                'SOS':'\x98',
                'SGC':'\x99',
                'SCI':'\x9A',
                'CSI':'\x9B',
                'PM':'\x9E',
                'SHY':'\xAD',
                'APC':'\x9F',
            }

            db.try_custom()
            import re
            from lib.crypto import decrypt
            d = decrypt(readfile(i,'rt'),'html')
            n = re.search(r'<title>[^“„<]*[“„]([^”“]+)[”“]</title>',d)[1]
            chrs = re.findall(r'(<span class="text">(.+?)</span>|<div class="item blank"></div>)',d)
            asrt(len(chrs) == 0x100)

            ob = [f'{ix:02X}' if x[0].startswith('<div') else f'{ix:02X}={REPL.get(x[1],x[1])}' for ix,x in enumerate(chrs)]
            writefile(o + '/' + sub_path(n,slash=True) + '.tbl','\n'.join(ob) + '\n')
            return
        case 'IBM XMIT Transmit':
            if db.print_try: print('Trying with xmi-reader')
            oj = OSJump()
            oj.jump(dirname(db.get('libmagic'))) # xmi needs libmagic.dll
            import xmi
            oj.back()
            f = xmi.open_file(i,outputfolder=o,quiet=True)
            asrt(not f.has_message(),err=NotImplementedError,debug=True)

            ob = f._get_clean_json_no_text()
            ob.pop('CONFIG',None)
            ob.pop('file',None)
            writefile(o + '/$db.json',ob,indent=4)

            suc = False
            for dn in f.get_files():
                if f.is_pds(dn):
                    de = f.get_file_info_simple(dn) | f.get_file_info_detailed(dn)
                    ts = {}
                    if 'created' in de: ts['ct'] = str2unix(de['created'])
                    if 'modified' in de: ts['mt'] = str2unix(de['modified'])
                    bn = o + '/' + sub_path(dn,slash=True)
                    mkdir(bn)
                    for fn in f.get_members(dn):
                        try: fe = f.get_member_info(dn,fn)
                        except KeyError:
                            if fn.startswith('DELETED??'):
                                p = f'{bn}/$deleted{fn[9:]}.null'
                                xopen(p,'x').close()
                                set_ftime(p,**ts)
                                continue
                            raise
                        fts = {}
                        if 'modified' in fe: fts['mt'] = str2unix(fe['modified'])
                        p = bn + '/' + sub_path(fn,slash=True) + fe['extension']
                        try: writefile(p,f.get_member_decoded(dn,fn))
                        except KeyError:
                            if 'alias' in fe: symlink(sub_path(fe['alias'],slash=True) + fe['extension'],p)
                            else: raise FileNotFoundError(f'{dn}/{fn}')
                        set_ftime(p,**(ts | fts))
                        suc = True
                else: raise NotImplementedError(dn)

            if suc: return
        case 'IBM EBCDIC DOC JCL':
            db.try_custom()
            f = xopen(i,'rt',encoding='cp500')

            fs = {}
            while True:
                l = f.read(0x46)
                if not l: break
                d = ''
                while len(d) != 8:
                    c = f.read(1)
                    if not c: break
                    if d or c != ' ': d += c
                if d:
                    for _ in range(2):
                        if f.read(1) not in {'','/'}:
                            f.seek(f.tell() - 1)
                            break
                else:
                    fs['$truncated'] = [l]
                    break
                if not d in fs: fs[d] = []
                fs[d].append(l)
            f.close()

            for k,v in fs.items():
                writefile(o + '/' + sub_path(k,slash=True) + '.txt','\n'.join(v) + '\n')

            if fs: return
        case 'DeFrosTPAC Archive':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(f.readu8()) == b'TPAC' and f.read(f.readu8()) == b'1.6')

            while f:
                n = f.reads(f.readu8(),'ascii')
                if len(n) < 12: f.skip(12 - len(n))
                writefile(o + '/' + n,f.readc(f.readu32()))

            f.close()
            if listdir(o): return
        case 'Android Boot Image':
            db.try_custom()
            from lib.file import File,decompress
            f = File(i,endian='<')
            asrt(f.read(8) == b'ANDROID!')

            v = f.peek('u32',offset=0x20)
            inf = [f'Version: {v}']
            fs = []
            if v >= 3:
                sz = f.readu32()
                if sz: fs.append(('kernel',sz))
                sz = f.readu32()
                if sz: fs.append(('ramdisk',sz))
                osv = f.readu32()
                f.skip(0x18)
                pgs = 0x1000
                writefile(o + '/cmd.txt',f.readc(0x600).split(b'\0',1)[0])
            else:
                sz,adr = f.readu32(),f.readu32()
                if sz:
                    fs.append(('kernel',sz))
                    inf.append(f'Kernel Address: 0x{adr:08X}')
                sz,adr = f.readu32(),f.readu32()
                if sz:
                    fs.append(('ramdisk',sz))
                    inf.append(f'Ramdisk Address: 0x{adr:08X}')
                sz,adr = f.readu32(),f.readu32()
                if sz:
                    fs.append(('second',sz))
                    inf.append(f'Second Address: 0x{adr:08X}')
                inf.append(f'Tags Address: 0x{f.readu32():08X}')
                pgs = f.readu32()
                f.skip(4)
                osv = f.readu32()

            inf.append(f'Page Size: 0x{pgs:08X}')
            osvv = osv >> 11
            if osvv:
                inf.append(f'OS Version: {osv >> 14}.{(osv >> 7) & 0x7F}.{osv & 0x7F}')
            ospv = osv & 0x7FF
            if ospv:
                y,m = 2000 + (ospv >> 4),ospv & 0xF
                inf.append(f'OS Patch: {y:04d}-{m:02d}')
                ts = ymd2unix(y,m)
            else: ts = None

            if v < 3:
                prn = f.readc(0x10).split(b'\0',1)[0]
                if prn: inf.append(f'Product Name: {prn.decode("utf-8")}')
                cmd = f.readc(0x200).split(b'\0',1)[0]
                id = f.readc(0x20)
                if sum(id):
                    if not sum(id[0x14:]): inf.append(f'SHA-1: {id[:0x14].hex().upper()}')
                    else: inf.append(f'ID: {id.hex().upper()}')
                cmd += f.readc(0x400).split(b'\0',1)[0]
                writefile(o + '/cmd.txt',cmd)

                if v > 0:
                    sz,off = f.readu32(),f.readu64()
                    if sz: fs.append(('recovery_dtbo',sz,off))
                    inf.append(f'Boot Header Size: {f.readu32():08X}')
                if v == 2:
                    sz,adr = f.readu32(),f.readu64()
                    if sz:
                        fs.append(('dtb',sz))
                        inf.append(f'DTB Address: 0x{adr:08X}')
            if ts and exists(o + '/cmd.txt'): set_ftime(o + '/cmd.txt',ts)

            if v >= 4:
                sz = f.readu32()
                if sz: fs.append(('boot_signature',sz))

            writefile(o + '/info.txt','\n'.join(inf))
            if ts: set_ftime(o + '/info.txt',ts)

            f.align(pgs)
            for fe in fs:
                if len(fe) == 2:
                    d = f.readc(fe[1])
                    f.align(pgs)
                else: d = f.peek(fe[1],offset=[fe[2]])
                writefile(o + '/' + fe[0],d)
                if ts: set_ftime(o + '/' + fe[0],ts)

                if fe[0] == 'kernel':
                    asrt(sum(d[-12:]) == 0)
                    off = int.from_bytes(d[-0x1C:-0x18],'little')
                    if len(d) - 0x30 > off > 0x1000:
                        chk = (d[off:off+4],len(d) - off - 0x18)
                        d = decompress(d[off:],'guess',noerror=True)
                        if chk[0] != d[:4] and len(d) > chk[1]:
                            writefile(o + '/' + fe[0] + '.dec',d)
                            if ts: set_ftime(o + '/' + fe[0] + '.dec',ts)
                elif fe[0] == 'ramdisk':
                    chk = (d[:4],len(d))
                    d = decompress(d,'guess')
                    if chk != (d[:4],len(d)):
                        writefile(o + '/' + fe[0] + '.dec',d)
                        if ts: set_ftime(o + '/' + fe[0] + '.dec',ts)
                    if d.startswith(b'0707'): extract(o + '/' + fe[0] + '.dec',o + '/' + fe[0] + '_ext','CPIO')

            f.close()
            if fs: return
        case 'LG Encrypted EPK':
            raise NotImplementedError
            KEYS = (1786572797,'https://github.com/openlgtv/epk2extract/raw/refs/heads/master/keys/AES.key')
            DBP = db.bin_path + 'epk_keys.pyob'

            db.try_custom()
            from lib.pyob import PyOBinX
            if exists(DBP):
                keys = PyOBinX(DBP)
                ts = keys.wait()['ts']
            else: ts = 0
            if ts < KEYS[0]:
                import httpx,time
                keys = PyOBinX.new(DBP,{'ts':int(time.time()),'k':[]})
                for l in httpx.get(KEYS[1]).text.replace('\r','').split('\n'):
                    l = l.split('#',1)[0].strip()
                    if not l: continue
                    l = bytes.fromhex(l)
                    if not l in keys['k']: keys['k'].append()
                keys.save()

            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='<')

            if f.peek(4) != b'EPK3':
                tst = f.peek(0x10)
                for k in keys['k']:
                    tst = decrypt(tst,'aes_ecb',k)
                    if tst[:4] == b'EPK3': break
                else:
                    f.close()
                    return 1
                h = File(decrypt(f.read(0x6B0),'aes_ecb',k),endian=f.endian)
            else: h = f
            asrt(h.read(4) == b'EPK3')
        case 'LZX Archive':
            ol = listdir(o)
            run(['lzx','x',i,o])
            if listdir(o) != ol: return
        case 'Great Adventures by Fisher Price Resource':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu32() == 4)
            f.padc(8)

            f.skip(8)
            of,c = f.readu32(),f.readu32() // 8
            f.seek(of)
            fs = [(f.readu32(),f.readu32()) for _ in range(c)]
            for ix,fe in enumerate(fs):
                f.seek(fe[0])
                d = f.readc(fe[1])
                writefile(f'{o}/{ix:02d}.{guess_ext(d)}',d)

            f.close()
            if fs: return
        case 'SouthPeak Interactive AGG':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu32() == 3 and f.reads(0x104,'latin-1').rstrip('\0') == 'Copyright (c) 1998 Southpeak Interactive LLC, Cary, North Carolina, USA.  All Rights Reserved.')

            sl,c = f.readu32(),f.readu32()
            asrt(sl >= c)
            fs = []
            for _ in range(c):
                fe = f.readu32(),f.readu32()
                f.skip(4) # u32: ?, the same for all entries
                f.readbool32() # ?, only seen as 1 in .mpj entries
                fs.append((*fe,o + '/' + sanitize_relative(sub_path(f.readc(0x104).split(b'\0')[0].decode('ascii')))))

            for fe in fs:
                f.seek(fe[0])
                fn,ex = splitext(fe[2])
                c = ''
                while exists(fn + c + ex):
                    c = '.$' + str(int(c[2:] or '0') + 1)
                writefile(fn + c + ex,f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Marvel Ultimate Alliance BIN':
            db.try_custom()
            from lib.pyob import PyOBinX
            keys = PyOBinX.dl('keys',db)
            from lib.crypto import decrypt
            from lib.file import File,decompress
            f = File(i,endian='<')
            asrt(f.read(4) == b'\x6E\xCA\x9A\xB1' and f.readu16() == 1)

            fl = f.readu8()
            f.padc(1)
            c = f.readu32()
            s = f.readu32()
            us = f.readu32()
            zs = f.readu32()
            f.skip(4)
            td = f.readc(s)
            kcnf = keys.wait()['mua']
            if fl & 0x10: td = decrypt(td,'mua',s,**kcnf)
            if fl & 1: td = decompress(td,'zlib',usize=c * 0x28)
            tf = File(td,endian=f.endian)

            sd = f.readc(zs)
            if fl & 0x10: sd = decrypt(sd,'mua',zs,**kcnf)
            if fl & 1: sd = decompress(sd,'zlib',usize=us)

            bp = f.pos
            for _ in range(c):
                tf.skip(8)
                n = sd[tf.readu64():].split(b'\0')[0].decode('ascii')
                f.seek(bp + tf.readu64())
                d = f.readc(tf.readu64())
                if fl & 0x10: d = decrypt(d,'mua',len(d),**kcnf)
                us = tf.readu64()
                if fl & 1:
                    try: d = decompress(d,'zlib',usize=us)
                    except:
                        print(f.pos - len(d),tf.pos - 0x28,n,len(d),us)
                        raise
                asrt(len(d) == us)
                writefile(o + '/' + n,d)

            f.close()
            del tf
            del sd
            if c: return
        case 'Knowledge Adventure Resource':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(6) == b'BWRF10')

            c = f.readu32()
            fs = [(f.reads(12,'ascii').rstrip('\0'),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[1])
                writefile(o + '/' + fe[0],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Electronic Arts BIGF':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            asrt(f.read(4) == b'BIGF')
            f.skip(4) # file size LE

            c = f.readu32()
            f.skip(4) # min header size?
            fs = [(f.readu32(),f.readu32(),f.read0s('ascii')) for _ in range(c)]
            for fe in fs:
                f.seek(fe[0])
                writefile(o + '/' + fe[2],f.readc(fe[1]))

            f.close()
            if fs: return
        case 'Electronic Arts BIN Text':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.readu16() == 1)

            c = f.readu16()
            ob = [(f.readu32(),f.readu32()) for _ in range(c)]
            ob = [f'{e[0]}: {f.seekc(e[1]).read0s16()}' for e in ob]
            f.close()
            if ob:
                writefile(f'{o}/{tbasename(i)}.txt','\n'.join(ob))
                return
        case 'Who Wants to Be a Millionaire DAT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            asrt(f.readu16() == 1 and f.readu16() == 0)

            ds,dss,fss,dc,fc = f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32()
            f.skip(ds)
            ep = f.pos + dss
            dstr = [f.reads(f.readu8(),'ascii') for _ in whilelc(lambda:f < ep)]
            f.seek(ep)
            ep = f.pos + fss
            fstr = [f.reads(f.readu8(),'ascii') for _ in whilelc(lambda:f < ep)]
            f.seek(ep)

            ds = [(dstr[ix],f.readu32(),f.readu32()) for ix in range(dc)]
            ds = [(range(x[1],x[1] + x[2]),x[0]) for x in ds]
            fs = [(f.readu32(),f.readu32(),f.readu32()) for _ in range(fc)]

            for x in ds:
                mkdir(o + '/' + x[1])
            for ix,fe in enumerate(fs):
                dn = [x[1] for x in ds if ix in x[0]]
                asrt(len(dn) == 1)
                f.seek(fe[1])
                writefile(o + '/' + dn[0] + '/' + fstr[fe[0]],f.readc(fe[2]))

            f.close()
            if fs: return
        case 'Who Wants to Be a Millionaire Sound DAT':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')
            asrt(f.readu16() == 2)
            f.skip(2)

            ds,dss,dts,fss,uts,fts = [f.readu32() for _ in range(6)]
            f.padc(4)
            ep = f.skip(ds) + dss
            dss = [(f.reads(f.readu8(),'ascii'),f.readu16()) for _ in whilelc(lambda:f < ep)]
            dss = {x[1]:x[0] for x in dss}
            ep = f.pos + dts
            ds = [(f.readu32(),f.readu16() + f.padc(2)) for _ in whilelc(lambda:f < ep)]
            ds = [(range(x[0],x[0] + x[1]),dss[ix]) for ix,x in enumerate(ds)]
            ep = f.skip(fss + uts) + fts
            fs = [(f.readu32(),f.readu32(),f.skip(0x14)) for _ in whilelc(lambda:f < ep)]

            for x in ds:
                mkdir(o + '/' + x[1])
            for ix,fe in enumerate(fs):
                dn = [x for x in ds if ix in x[0]]
                asrt(len(dn) == 1)
                dn = dn[0]
                f.seek(fe[0])
                writefile(f'{o}/{dn[1]}/{ix - dn[0].start}.snd',f.readc(fe[1]))

            f.close()
            if fs: return

    return 1
