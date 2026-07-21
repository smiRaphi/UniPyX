from .main import *

def extract1(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def msdos(cmd,mscmd=[],tmpi=False,inf=i,**kwargs):
        if tmpi:
            mkdir(o)
            tf = o + '/' + 'TMP' + extname(inf)
            symlink(inf,tf)

        if db.print_try: print('Trying with',cmd[0])
        run(['msdos'] + mscmd + [db.get(cmd[0])] + [(('TMP' + extname(inf)) if tmpi and x == inf else x) for x in cmd[1:]],print_try=False,**kwargs)

        if tmpi: remove(tf)

        if listdir(o): return
        return 1
    def dosbox(cmd:list,inf=i,oup=o,print_try=True,nowin=True,max=True,custs:str=None,tmpi=True,xcmds=[],stdin=None):
        scr = cmd[0]
        s = db.get(scr)
        if not exists(s): s = custs

        mkdir(oup)
        oinf = inf
        if tmpi:
            td = TmpDir()
            inf = td + '\\TMP' + extname(inf)
            symlink(oinf,inf)

        if stdin: open(oup + '/_IN.TXT','w',encoding='cp437').write(inp)

        if print_try and db.print_try: print('Trying with',scr)
        p = subprocess.Popen([db.get('dosbox'),'-nolog','-nopromptfolder','-savedir','NUL','-defaultconf','-fastlaunch','-nogui',('-silent' if nowin else ''),
             '-c','MOUNT I "' + dirname(inf) + '"','-c','MOUNT C "' + dirname(custs or s) + '"','-c','MOUNT O "' + oup + '"','-c','O:'] + xcmds + [
             '-c',subprocess.list2cmdline(['C:\\' + basename(s)] + [('I:\\' + basename(inf) if x == oinf else x) for x in cmd[1:]]) + (' > _OUT.TXT' if nowin else '') + (' < _IN.TXT' if stdin else '')] + (sum([['-set',f'{x}={DOSMAX[x]}'] for x in DOSMAX],[]) if max else []),stdout=-3,stderr=-2)

        while not exists(oup + '/_OUT.TXT'): sleep(0.1)
        while True:
            try: open(oup + '/_OUT.TXT','ab').close()
            except PermissionError: sleep(0.1)
            else: break

        for _ in range(10):
            if getsize(oup + '/_OUT.TXT') > 0: break
            sleep(0.1)

        while True:
            r = readfile(oup + '/_OUT.TXT')
            if len(r) == getsize(oup + '/_OUT.TXT'):
                r = r.decode('utf-8')
                break
            sleep(0.1)
        while True:
            try:
                remove(oup + '/_OUT.TXT')
                if stdin: remove(oup + '/_IN.TXT')
            except PermissionError: sleep(0.1)
            else: break
        p.kill()
        if tmpi: td.destroy()

        return r

    match t:
        case '7z'|'MSCAB'|'Windows Help File'|'ARJ'|'JFD IMG'|'TAR'|'yEnc'|'xz'|'BZip2'|'LZIP'|'CPIO'|'Asar'|'ARJZ'|\
             'DiskDupe IMG'|'XAR'|'Z'|'EXT'|'SquashFS'|'VHD'|'Compressed ISO'|'CramFS'|'Google Update Installer'|'RPM Package'|\
             'Microsoft Compound Document':
            _,_,e = zip7(i,o,t)
            if 'ERROR: Unsupported Method : ' in e and readfile(i,size=2) == b'MZ':
                rmtree(o,True)
                mkdir(o)
                if db.print_try: print('Trying with input')
                run([i,'x','-o' + o,'-y'],print_try=False)
            if listdir(o) and not exists(o + '/.rsrc'):
                if t == 'MSCAB': fix_cab(o);return
                elif t in {'Z','xz','BZip2','LZIP'}: return fix_tar(o)
                else: return
        case 'ZSTD':
            db.try_custom()
            from lib.file import decompress
            of = o + '\\' + tbasename(i)
            d = decompress(readfile(i),'zstd',db=db)
            writefile(of,d)

            xm = {b'RARC':'RARC',b'SARC':'SARC',b'NARC':'NitroARC',b'darc':'Nintendo Data ARChive'}
            tg = d[:4]
            if tg in xm:
                tp = o + f'\\tmp{os.urandom(6).hex()}.{tg.decode().lower()}'
                rename(of,tp)
                r = extract(tp,o,xm[tg])
                if r: rename(tp,of)
                else:
                    while True:
                        try: remove(tp)
                        except PermissionError: sleep(0.1)
                        else: break
                return
            return fix_tar(o)
        case 'LZMA':
            if db.print_try: print('Trying with lzma')
            from lib.file import decompress
            writefile(o + '/' + tbasename(i),decompress(readfile(i),'lzma'))
            if d: return
        case 'LZ4':
            if db.print_try: print('Trying with lz4')
            from lib.file import decompress
            try: d = decompress(readfile(i),'lz4')
            except: return 1
            writefile(o + '/' + tbasename(i),d)
            return
        case 'FastLZ':
            of = o + '\\' + tbasename(i)
            run(['fastlz','d',i,of])
            if exists(of) and getsize(of): return
        case 'Stripped TAR':
            db.try_custom()
            f = xopen(i,'rb')

            while True:
                fn = f.read(100)
                if len(fn) != 100: break
                if fn[0] == 0:
                    f.seek(-99,1)
                    b = b''
                    while True:
                        b = f.read(1)
                        if not b:
                            fn = b''
                            break
                        if b[0] != 0:
                            fn = b + f.read(99)
                            break

                if len(fn) != 100: break
                fn = fn.rstrip(b'\0').decode('utf-8')

                asrt(f.read(8*3) == (b'0000000\0'*3))
                fs = int(f.read(11).decode('utf-8'),8)

                asrt(f.read(22) == (b'\0' + b'0'*11 + b'\0' + b'0'*7 + b'\0 '))
                f.seek(0xAC,1)
                #asrt(sum(f.read(0xAC)) == 0,f.tell())
                asrt(f.read(0x10) == (b'0000000\0'*2))
                asrt(sum(f.read(0xA7)) == 0)

                writefile(o + '/' + fn,f.read(fs))

            f.close()
            return
        case 'LHARC':
            run(['lha','xf','--extract-broken-archive','-w=' + o,i])
            if listdir(o): return
            zip7(i,o,t)
            if listdir(o): return
        case 'PDF':
            run(['pdfdetach','-saveall','-o',o + '\\out',i])
            run(['pdfimages','-j',i,o + '\\img'])
            run(['pdftohtml','-embedbackground','-meta','-overwrite','-q',i,o + '\\html'])
            if listdir(o + '/html'): return
            remove(o + '/html')
        case 'Nero CD IMG':
            zip7(i,o,t)
            for ix,f in enumerate(listdir(o)):
                tf = o + f'/{ix:02d}' + extname(f).lower()
                to = o + f'\\{ix:02d}'
                os.rename(o + '/' + f,tf)
                if extname(tf) == '.iso':
                    mkdir(to)
                    if extract1(tf,to,'ISO'): remove(to)
                    else: remove(tf)
            if listdir(o): return
        case 'Aaru'|'CDI'|'ACT Apricot IMG'|'Unix Fast Filesystem':
            td = TmpDir(path=o,mdir=False)
            run(['aaru','filesystem','extract',i,basename(td.p)],cwd=o)
            if exists(td.p) and listdir(td.p):
                ret = False
                for td1 in listdir(td.p):
                    td1 = td + '/' + td1
                    if listdir(td1):
                        copydir(td1 + '/' + listdir(td1)[0],o)
                        ret = True
                td.destroy()
                if ret: return
            td.destroy()
        case 'ISO'|'IMG'|'Floppy Image'|'UDF'|'DOS IMG'|'NTFS'|'Master Boot Record':
            _,e,_ = run(['aaru','filesystem','info',i],print_try=False)
            iso_udf = t in {'ISO','UDF'} and 'As identified by ISO9660 Filesystem.' in e and 'Identified by 2 plugins' in e

            if not iso_udf and not extract1(i,o,'Aaru'): return

            bd = listdir(o)
            zip7(i,o,t)
            if exists(o):
                for f in listdir(o):
                    if f not in bd: return
        case 'CUE+BIN'|'CDI CUE+BIN':
            osj = OSJump()
            osj.jump(dirname(i))
            td = 'tmp' + os.urandom(8).hex()
            run(['aaru','filesystem','extract',i,td])
            osj.back()
            td = dirname(i) + '\\' + td
            if exists(td) and listdir(td):
                td1 = td + '/' + listdir(td)[0]
                copydir(td1 + '/' + listdir(td1)[0],o)
                remove(td)
                return
            remove(o,td)
            mkdir(o)

            run(['bin2iso',i,o,'-a'])[1]
            if listdir(o):
                for f in listdir(o):
                    if f.endswith('.iso'):
                        nt = None
                        f = o + '\\' + f
                        fo = xopen(f,'rb')
                        fs = fo.seek(0,2)

                        for off in (0x10000,0xFDA0000,0x18310000):
                            if off > fs: break
                            fo.seek(off)
                            if fo.read(20) == b'MICROSOFT*XBOX*MEDIA': nt = 'XISO';break
                        if not nt:
                            for off,chk,typ in (
                                                (0x0000,b'\xAE\x0F\x38\xA2','GameCube TGC ISO'),
                                                (0x0018,b'\x5D\x1C\x9E\xA3','Wii ISO'),
                                                (0x001C,b'\xC2\x33\x9F\x3D','GameCube ISO'),
                                                (0x0800,b'PlayStation3\0\0\0\0','PS3 ISO'),
                                                (0x8000,b'\1CD001\1\0','ISO'),):
                                if off > fs: break
                                fo.seek(off)
                                if fo.read(len(chk)) == chk: nt = typ; break

                        fo.close()
                        if nt and not extract(f,o,nt): remove(f)
                return
        case 'Shifted ISO':
            db.try_custom()
            f = xopen(i,'rb')
            f.seek(0x8000)
            dat = f.read(0x1000)
            if not b'\x01CD001\x01\x00' in dat: return 1
            tf = o + '\\TMP' + os.urandom(8).hex() + '.iso'
            f.seek(dat.index(b'\x01CD001\x01\x00'))
            writefile(tf,f.read())
            f.close()

            if extract1(tf,o,'ISO'): rename(tf,o + '/' + tbasename(i) + '_fixed.iso')
            else: remove(tf)
            return
        case 'Cloop IMG':
            tf = TmpFile('.img',path=o)
            run(['qemu-img','convert','--salvage','-O','raw','-m',os.cpu_count(),'-q',i,tf])
            r = extract1(tf.p,o,'IMG')
            tf.destroy()
            return r
        case 'Apple Partition Map':
            _,e,_ = run(['7z','l','-tAPM',i],print_try=False)
            if 'ERRORS:\nUnexpected end of archive' in e and '0.Apple_partition_map' in e:
                zip7(i,o,t)
                fs = listdir(o)
                if len(fs) > 1:
                    for f in fs:
                        f = o + '\\' + f.lower()
                        od = noext(f)
                        if f.endswith('.iso'):
                            mkdir(od)
                            if not extract(f,od,'ISO'):
                                remove(f,od)
                                asrt(not exists(od))
                        elif f.endswith('.hfs'):
                            mkdir(od)
                            if not extract(f,od,'Apple Disk Image'):
                                remove(f,od)
                                asrt(not exists(od))
                    if listdir(o) != fs: return
                remove(o)
                mkdir(o)
            return extract(i,o,'Apple Disk Image')
        case 'Apple Disk Image'|'Roxio Toast IMG':
            _,e,_ = run(['aaru','filesystem','info',i],print_try=False)
            try: ps = int(re.search(r'(\d+) partitions found\.',e)[1])
            except: ps = 1

            ce = os.environ.copy()
            ce['PATH'] += ';' + dirname(db.get('hfsexplorer'))
            oo = listdir(o)
            for p in range(ps):
                if db.print_try: print('Trying with hfsexplorer/unhfs')
                cop = o + (f'\\{p}' if ps > 1 else '')
                mkdir(cop)
                _,_,e = run(['java','--enable-native-access=ALL-UNNAMED','-cp',db.get('hfsexplorer'),'org.catacombae.hfsexplorer.tools.UnHFS','-o',cop,'-resforks','APPLEDOUBLE','-sfm-substitutions','-partition',p,'--',i],print_try=False,env=ce)
                if 'Failed to create directory ' in e: return 1
                if exists(cop) and not listdir(cop): rmdir(cop)
            if not exists(o): mkdir(o)
            if listdir(o) and listdir(o) != oo: return

            return extract(i,o,'ISO')
        case 'Apple DiskCopy':
            db.try_custom()
            tf = TmpFile('.img',path=o)
            writefile(tf,readfile(i)[0x84:])
            for ty in ('IMG','Apple Disk Image'):
                if not extract1(tf.p,o,ty): break
            else: mv(tf.p,o + '/' + tbasename(i) + '.img')
            tf.destroy()
            return
        case 'Error Code Modeler':
            tf = TmpFile('.iso',path=o)
            run(['unecm',i,tf])
            if not exists(tf.p) or not getsize(tf.p): return 1
            if extract1(tf.p,o,'ISO'): mv(tf.p,o + '/' + tbasename(i))
            tf.destroy()
            return
        case 'CHD':
            _,inf,_ = run(['chdman','info','-i',i],print_try=False)

            if "Tag='CHGD'" in inf:
                td = TmpDir()
                run(['chdman','extractcd','-o',td + '/tmp.cue','-f','-i',i])
                if not exists(td + '/tmp.cue'):
                    td.destroy()
                    return 1

                if extract(td + '/tmp.cue',o,'GD-ROM CUE+BIN'):
                    for f in listdir(td.p): mv(td + '/' + f,o + '/' + tbasename(i) + extname(f))
                td.destroy()
            else:
                tf = TmpFile('.img')
                run(['chdman','extracthd','-o',tf,'-f','-i',i])
                if not exists(tf.p): return 1

                if extract(tf.p,o,'IMG'): mv(tf.p,o + '/' + basename(o) + '.img')
                tf.destroy()
            return
        case 'ZIP'|'InstallShield Setup ForTheWeb'|'RESOF':
            ZFMTM = {
                0:'none',
                1:'shrink',
                2:'reduce1',
                3:'reduce2',
                4:'reduce3',
                5:'reduce4',
                6:'pkzip_implode',
                7:'tokenize', # reserved, no implementation, unsupported
                8:'deflate',
                9:'deflate64',
                10:'pkware_implode',
                12:'bzip2',
                14:'lzma_zip',
                15:'oodle', # unofficial, used by "New World: Aeternum", untested
                16:'cmpsc', # unsupported, https://github.com/Fish-Git/cmpsctst
                18:'terse', # unsupported, https://github.com/openmainframeproject/tersedecompress/tree/master/cpp/src
              # 18:'xceed_bwt', # unofficial
                19:'lz77z', # unsupported
                20:'zstd', # deprecated
              # 20:'lpaq8', # unofficial
                22:'forza_encrypted', # unofficial, custom encryption + deflate, untested
                92:'reference', # WinZip
                93:'zstd',
                94:'packmp3', # WinZip
              # 94:'lz4', # unofficial, OTEr ZIP, untested
                95:'xz',
                96:'zipx_jpeg', # unsupported, WinZip, not packjpg
                97:'wavpack', # WinZip
              # 97:'brotli', # unofficial, OTEr ZIP, untested
                98:'ppmd8',
                99:'aes',
              # 99:'lzfse', # unofficial, Apple
               100:'lzfse', # unofficial, OTEr ZIP, untested, https://github.com/trufae/otezip
            }
            BUNFMTM = ( # https://github.com/r-lyeh-archived/bundle
                'none', # RAW
                'shoco', # unsupported
                'lz4f', # unsupported
                'zlib', # MINIZ
                'lzip', # unsupported
                'lzma', # LZMA20
                'zpaq', # unsupported
                'lz4', # error
                'brotli', # BROTLI9, error
                'zstd', # error
                'lzma', # LZMA25
                'bsc', # unsupported
                'brotli', # BROTLI11, error
                'shrinker', # unsupported
                'csc20', # unsupported
                'zstdf', # unsupported
                'bcm', # unsupported
                'zling', # unsupported
                'mcm', # unsupported
                'tangelo', # unsupported
                'zmolly', # unsupported
                'crush', # unsupported
                'lzjb', # unsupported
                'bzip2',
            )

            FRZK = None
            FRH3NK = {
                'l':'a',
                '`':'b',
                '^':'c',
                '6':'d',
                'q':'e',
                'v':'f',
                '{':'g',
                '@':'h',
                '$':'i',
                '7':'j',
                's':'k',
                'b':'l',
                'g':'m',
                '8':'n',
                'h':'o',
                'u':'p',
                'f':'q',
                '4':'r',
                '~':'s',
                '1':'t',
                '=':'u',
                "'":"v",
                'm':'w',
                ']':'x',
                '!':'y',
                ',':'z',
                'y':'_',
                '_':'-',
                '[':'0',
                '0':'1',
                'w':'2',
                'k':'3',
                '(':'4',
                '2':'5',
                'j':'6',
                '}':'7',
                ';':'8',
                '+':'9',
            }
            db.try_custom()
            import json
            from lib.file import File,decompress,pdosdate,by2bi
            from lib.crypto import decrypt,encrypt,crc_hash
            fh3ne = i.endswith('.,$u')
            f = File(i,endian='<')

            SIG66 = b'PK\6\6'
            SIG56 = b'PK\5\6'
            if t == 'RESOF':
                SIG12 = b'PK\1\4'
                SIG34 = b'PK\3\6'
            else:
                SIG12 = b'PK\1\2'
                SIG34 = b'PK\3\4'

            TESTDS = 0x10061 # max EOCD32 + EOCD64
            f.seek(-TESTDS)
            d = f.read(TESTDS)
            if not sum(d):
                while True:
                    f.back(TESTDS*2)
                    d = f.read(TESTDS)
                    if sum(d):
                        f.back((TESTDS - len(d.rstrip(b'\0'))) + TESTDS)
                        d = f.read(TESTDS)
                        break

            trrntzip = None
            bp = f.pos - len(d)
            po = len(d)
            if SIG66 in d:
                while True:
                    p = d.rfind(SIG66 + b'\x2C\0\0\0\0\0\0\0',None,po)
                    if p == -1: return 1
                    po = p
                    f.seek(bp + p + 4 + 8 + 4 + 8)
                    if f.read(8) != f.read(8): continue
                    sz,of = f.readu64(),f.readu64()
                    if (of + sz) <= (bp + p): break

                f.seek(bp + p + 4 + 8 + 4)
                if sum(f.read(8)): raise NotImplementedError('Multi file zip')
                c = f.readu64()
                f.skip(8)
                cds,cdo = f.readu64(),f.readu64()
            else:
                while True:
                    p = d.rfind(SIG56,0x4C,po)
                    if p == -1: return 1
                    po = p
                    f.seek(bp + p + 4)
                    mult = sum(f.read(4))
                    cdc,tcdc = f.readu16(),f.readu16()
                    if not (cdc == tcdc or (not mult and cdc == 0 and tcdc != 0)): continue
                    sz,of = f.readu32(),f.readu32()
                    if t == 'RESOF': sz ^= 0xFFFFFFFF
                    if (of + sz) <= (bp + p): break
                    if not SIG56 in d[:p] and (of + sz - 0x40) <= (bp + p): break

                f.seek(bp + p + 4)
                if sum(f.read(4)): raise NotImplementedError('Multi file zip')
                c = f.readu16()
                if c == 0: c = f.readu16()
                else: f.skip(2)
                cds,cdo = f.readu32(),f.readu32()
                cmt = f.readc(f.readu16()).rstrip(b'\0')
                if len(cmt) == 0x16 and cmt.startswith(b'TORRENTZIPPED-'): trrntzip = int(cmt[14:0x16],16)
                elif cmt: writefile(o + '/$comment.txt',cmt)

            # fe: file entry
            # - cv: create version
            # - xv: extract version
            # - fl: flags
            # - ct: compression type
            # - ts: timestamp, tuple = FILETIME, int = unix
            #   - m: modified
            #   - a: accessed
            #   - c: created
            # - zs: compressed size
            # - us: uncompressed size
            # - crc: crc32
            # - dsk: disk/file number
            # - ia: internal attributes
            # - xa: external attributes
            # - of: offset
            # - n: name
            # - cm: comment

            f.seek(cdo)
            reb = 0
            if c > 0 and not f.peek(4) == SIG12:
                f.seek(bp + p - cds)
                reb = f.pos - cdo

            if not trrntzip is None:
                asrt(crc_hash(f.peek(cds),'crc32') == trrntzip)
                trrntzip = True

            fs = []
            for _ in range(c):
                blkn = f.read(4)
                if blkn in {SIG56,SIG66}: break
                asrt(blkn == SIG12)
                fe = {
                    'cv':f.readu16(),
                    'xv':f.readu16(),
                    'fl':f.readu16(),
                    'ct':f.readu16(),
                    'ts':{},
                }
                asrt(not fe['fl'] & 0x1780)
                if fe['xv'] & 0xFF >= 62: asrt(not fe['fl'] & 0x2000,'Encrypted CD',err=NotImplementedError)
                if fe['ct'] == 22 and FRZK is None:
                    from lib.pyob import PyOBinX
                    FRZK = PyOBinX.dl('forza_keys',db)

                ct,cd = f.readu16(),f.readu16()
                if not trrntzip:
                    try: fe['ts']['m'] = unix2filetime(pdosdate(cd,ct))
                    except ValueError: pass
                fe['crc'] = f.readu32()
                fe['chk'] = (cd >> 8) if fe['fl'] & 8 else (fe['crc'] >> 24)
                fe['zs'],fe['us'] = f.readu32(),f.readu32()
                nl,xl,cml = f.readu16(),f.readu16(),f.readu16()
                fe['dsk'] = f.readu16()
                fe['ia'] = f.readu16()
                fe['xa'] = f.readu32()
                fe['of'] = f.readu32() + reb
                fnb = f.readc(nl)
                fe['n'] = fnb.rstrip(b'\0').decode('utf-8' if fe['fl'] & 0x800 else 'cp437')
                if fh3ne: fe['n'] = decrypt(fe['n'],'fh3name',FRH3NK)

                ep = f.pos + xl
                if xl == 10 and fe['cv'] == fe['xv'] == 10 and f.peek('u16',poffset=2) >= 0x3030 and all(x in '0123456789abcdefABCDEF' for x in f.reads(xl,'latin-1')):
                    f.seek(ep) # JAR shit
                while (f.pos + 4) < ep:
                    tg,s = f.readc(2),f.readu16()
                    xep = f.pos + s
                    match tg:
                        case b'\0\0': pass # empty
                        case b'\1\0': # Zip64
                            asrt(s >= 8)
                            fe['us'] = f.readu64()
                            if s > 8:
                                asrt(s >= 0x10)
                                fe['zs'] = f.readu64()
                            if s > 0x10:
                                asrt(s >= 0x18)
                                fe['of'] = f.readu64()
                            if s > 0x18:
                                asrt(s >= 0x1C)
                                fe['dsk'] = f.readu32()
                        case b'\x07\0': # AV Info
                            fe['avinf'] = f.read(s)
                        case b'\x09\0': # OS/2
                            fe['os2x'] = True
                        case b'\x0A\0': # NTFS
                            asrt(s >= 0x20)
                            f.padc(4)
                            asrt(f.readu16() == 1 and f.readu16() == 0x18,f.pos)
                            ts = f.readu64() # FILETIME
                            if ts: fe['ts']['m'] = ts
                            ts = f.readu64()
                            if ts: fe['ts']['a'] = ts
                            ts = f.readu64()
                            if ts: fe['ts']['c'] = ts
                        case b'\x0C\0': # OpenVMS
                            asrt(s >= 4)
                            f.skip(4)
                            while (f.pos + 4) < xep:
                                vtg,vs = f.readu16(),f.readu16()
                                vep = f.pos + vs
                                asrt(vep <= xep)
                                match vtg:
                                    case 4|19|20|13|21|22|23|29: pass # RECATTR, EXPDATE, BAKDATE, ASCDATES, UIC, FPRO, RPRO, JOURNAL
                                    case 3: # UCHAR
                                        asrt(vs >= 4)
                                        fe['vms'] = f.readu32()
                                    case 17: # CREDATE
                                        asrt(vs >= 8)
                                        ts = f.readu64()
                                        if ts: fe['ts']['c'] = vms2filetime(ts)
                                    case 18: # REVDATE
                                        asrt(vs >= 8)
                                        ts = f.readu64()
                                        if ts: fe['ts']['m'] = vms2filetime(ts)
                                    case _: raise NotImplementedError(f'Unknown OpenVMS tag {vtg} @ 0x{f.pos - 4:08X}')
                                f.seek(vep)
                        case b'\1\x99': # AE-x
                            asrt(fe['ct'] == 99,'AE-x entry without AE-x compression type')
                            asrt(s == 7)
                            fe['aes'] = {
                                'vv':f.readu16(),
                                'v':f.read(2),
                                'm':f.readu8(),
                            }
                            asrt(fe['aes']['v'] == b'AE' and fe['aes']['vv'] in {1,2},f'Unsupported AE-x vendor {repr(fe['aes']['v'])[2:-1]}-{fe["aes"]["vv"]}')
                            asrt(fe['aes']['m'] in {1,2,3},f'Unsupported AE-x mode {fe["aes"]["m"]}')
                            fe['ct'] = f.readu16()
                        case b'\x03\x99': # WinZip Reference
                            pass
                        case b'\x1E\xA1': # Data Stream Alignment
                            pass # u16 ?
                        case b'\x20\xA2': # Microsoft Open Packaging Growth Hint
                            pass # u64 growth hint, 0x10 padding
                        case b'\x23\x11': # ?, seen in Forza Horizon 6
                            pass # u32 data offset
                        case b'AC': # Acorn
                            asrt(s >= 4)
                            asrt(f.read(4) == b'ARC0')
                        case b'KV': # KeyValuePairs
                            asrt(s >= 14)
                            asrt(f.read(13)[:9] == b'KeyValuePairs'[:9]) # only verify first couple bytes
                            kvc = f.readu8()
                            fe['kv'] = dict((f.reads(f.readu16(),'utf-8'),f.reads(f.readu16(),'utf-8')) for _ in range(kvc))
                        case b'NU': # Xcess unicode
                            asrt(s >= 10 and f.read(4) == b'NUCX')
                            ns = f.readu32()
                            asrt((ns*2+8) <= s)
                            fe['n'] = f.readutf16(ns)
                            fe['xcess'] = True
                        case b'Q\x1A': # minizip hash
                            asrt(s > 4)
                            ht,hs = f.readu16(),f.readu16()
                            asrt((hs + 4) <= s)
                            fe[{10:'md5',20:'sha1',23:'sha256'}[ht]] = f.read(hs)
                        case b'SD': # windows ACL
                            pass
                        case b'UT':
                            asrt(s >= 1)
                            utfl = f.readu8()
                            asrt(not utfl >> 3)
                            for ix,mn in enumerate('mac'):
                                if (f.pos + 4) > xep: break
                                if utfl & (1 << ix):
                                    ts = f.readu32()
                                    if ts: fe['ts'][mn] = unix2filetime(ts)
                        case b'UX': # Unix
                            asrt(s >= 8)
                            ts = f.readu32()
                            if ts: fe['ts']['a'] = unix2filetime(ts)
                            ts = f.readu32()
                            if ts: fe['ts']['m'] = unix2filetime(ts)
                            # optional u16 UID & u16 GID
                        case b'Ux': # Previous new Unix
                            pass # optional u16 UID & u16 GID
                        case b'e\0': # IBM S/390 attributes uncompressed
                            pass
                        case b'nu': # ASi unix
                            pass
                        case b'up': # Info-ZIP unicode
                            asrt(s > 5)
                            asrt(f.readu8() == 1)
                            if crc_hash(fnb,'crc32') == f.readu32(): fe['n'] = f.readc(s - 5).decode('utf-8')
                        case b'ux': # New Unix
                            pass # u16 tag (?), u16 len (?), u8 v, u8 UIDlen, u8 UID[UIDlen], u8 GIDlen, u8 GID[GIDlen]
                        case b'\xC5\x10': # minizip CMS signature
                            pass # eh, no
                        case b'\xCD\xCD': # minizip central directory
                            asrt(s >= 8)
                            fe['mzc'] = f.readu64()
                            raise NotImplementedError('minizip central directory')
                        case _: raise NotImplementedError(f'{repr(tg)[1:]} @ 0x{f.pos - 4:08X}')
                    f.seek(xep)
                f.seek(ep)
                fe['cm'] = f.readc(cml)
                if fe['xa'] & 0x10 or (fe['n'].endswith('/') and fe['us'] == 0) or ('vms' in fe and fe['vms'] & 0x1000): mkdir(o + '/' + sanitize_relative(fe['n']))
                else: fs.append(fe)

            if any(fe['fl'] & 1 for fe in fs):
                # TODO: add key db
                KEY = None
                raise ValueError('No key for zip file')
            if FRZK:
                FRZK.wait()
                FRMK = [x for x in FRZK['c'] if x['n'].startswith('fm') and x['t'] == 'file']
                FRHK = [x for x in FRZK['c'] if x['n'].startswith('fh') and x['t'] == 'file']

            BUNDLE = []
            hrefs = any(fe['ct'] == 92 for fe in fs)
            refs = []
            drefs = {}
            for fe in fs:
                f.seek(fe['of'])
                asrt(f.read(4) == SIG34,lambda:f.fmt('§@§'))
                v = f.readu16()
                if 'aes' in fe: ct = 99
                else: ct = fe['ct']
                asrt(f.readu16() & 0x087F == fe['fl'] & 0x087F)
                ct2 = f.readu16()
                f.skip(0x10) # f.skip(4);crc2,zs2,us2 = f.readu32(),f.readu32(),f.readu32()
                fnl2,xfl2 = f.readu16(),f.readu16()
                fnb2 = f.reads(fnl2,'cp437')
                if ct == 18 and ct2 == 8 and not fe['fl'] & 0x800 and fnb2.isprintable() and all(x & 0x80 for x in fe['n'].encode('cp437')):
                    fe['n'] = fnb2
                    ct = fe['ct'] = ct2
                asrt(ct == ct2)

                ep = f.pos + xfl2
                if fe.get('os2x'):
                    while (f.pos + 4) < ep:
                        tg,s = f.readc(2),f.readu16()
                        xep = f.pos + s
                        if xep > ep: break
                        match tg:
                            case b'\x09\0':
                                asrt(s >= 10)
                                xus,xct,xcrc = f.readu32(),f.readu16(),f.readu32()
                                os2 = decompress(f.readc(s - 10),ZFMTM[xct],usize=xus)
                                if xcrc: asrt(crc_hash(os2,'crc32') == xcrc)
                                fe['os2x'] = os2
                                
                        f.seek(xep)
                f.seek(ep)

                d = f.readc(fe['zs'])
                if ct == 99 and 'aes' in fe:
                    sml,kml = (0,8,12,16)[fe['aes']['m']],(0,16,24,32)[fe['aes']['m']]
                    salt,kvr,auth,d = d[:sml],d[sml:sml+2],d[-10:],d[sml+2:-10]
                    k = encrypt(KEY,'pbkdf2',salt,1000,size=kml*2 + 2)
                    asrt(k[-2:] == kvr,'Password verification failed')
                    asrt(crc_hash(d,'hmac_sha1',key=k[kml:-2])[:10] == auth,'Authentication failed')
                    d = decrypt(d,'aes_ctr_le',k[:kml],bits=0x80)
                elif ct == 22: # Forza
                    asrt(len(d) >= 0x230) # min observed block size + fm6apex header
                    if len(d) & 7 == 4:
                        v = 1
                        iv,pad,hmac,d = d[:0x10],int.from_bytes(d[0x10:0x14],'little'),d[0x14:0x24],d[0x24:]
                        ds = len(d) - 0x24
                        bhd = iv + pad.to_bytes(4,'little')
                    else:
                        v = 0
                        iv,hmac,d = d[:0x10],d[0x10:0x20],d[0x20:]
                        ds = len(d) - 0x20
                        bhd = iv
                    for ctx in (FRMK,FRHK)[v]:
                        if ds % (ctx['b'] + 0x10): continue
                        hd = (ds // (ctx['b'] + 0x10) * ctx['b']).to_bytes(4,'little') + bhd
                        if crc_hash(hd,'cmac_tfit',key=ctx['mk'],table=ctx['mt']) == hmac: break
                    else: return 1
                    d = decrypt(d,'transformit',ctx['dk'],iv,table=ctx['dt'],block_size=ctx['b'])
                    if v == 1: d = d[:-pad]
                    fe['ct'] = 8 # deflate
                elif fe['fl'] & 1:
                    d = decrypt(d,'zipcrypto',KEY)
                    asrt(d[11] == fe['chk'])
                    d = d[12:]

                fn = o + '/' + sanitize_relative(fe['n'])
                c = 0
                while exists(fn):
                    fn = o + '/' + fe['n'] + '_' + str(c)
                    c += 1
                fe['ffn'] = fn

                if fe['ct'] == 92:
                    fe['sha1'] = d
                    refs.append(fe)
                    continue

                if fe['ct'] == 18 and d[:1].isdigit() and d[1:2] == b'1' and by2bi(d[-2:]).rstrip('0').endswith('00010111'):
                    d = decompress(d,'xceed_bwt',usize=fe['us'],check=lambda x: crc_hash(x,'crc32') == fe['crc'])
                elif fe['ct'] == 99 and d[:4] in {b'bvx$',b'bvx-',b'bvx1',b'bvx2',b'bvxn'}:
                    d = decompress(d,'lzfse',usize=fe['us'])
                elif fe['ct'] == 20 and d[:4] != b'\x28\xB5\x2F\xFD':
                    d = decompress(d,'lpaq8',usize=fe['us'])
                elif fe['ct'] == 6: d = decompress(d,ZFMTM[fe['ct']],usize=fe['us'],flags=fe['fl'])
                elif fe['ct'] == 97 and d[:4] != b'wvpk': d = decompress(d,'brotli',usize=fe['us'])
                elif fe['ct'] in {94,97}: d = decompress(d,ZFMTM[fe['ct']],usize=fe['us'],db=db)
                else: d = decompress(d,ZFMTM[fe['ct']],usize=fe['us'])
                for pht in ('sha256','sha1','md5'):
                    if pht in fe:
                        asrt(crc_hash(d,pht,bytes=True) == fe[pht],f'Hash mismatch ({pht})')
                        break
                else:
                    if fe['crc']: asrt(crc_hash(d,'crc32') == fe['crc'],'Checksum mismatch (crc32)')

                if hrefs: drefs[crc_hash(d,'sha1',bytes=True)] = fn
                if 9 >= ct >= 1: pass
                elif ct == 0 and len(d) >= 0x1E and d[0] == 0x70 and len(BUNFMTM) > d[1] > 0:
                    tf = File(d[:0x20])
                    tf.skip(2)
                    try: bus,bzs = tf.readleb128u(),tf.readleb128u() + 0x1A
                    except EOFError: BUNDLE.append(False)
                    else:
                        BUNDLE.append(bzs == (len(d) - tf.pos))
                        if BUNDLE[-1]: fe['bun'] = {'zs':bzs,'us':bus,'ct':d[1]}
                    del tf
                else: BUNDLE.append(False)

                writefile(fn,d)
                ts = [0,0,0]
                if 'c' in fe['ts']: ts[0] = fe['ts']['c']
                if 'a' in fe['ts']: ts[1] = fe['ts']['a']
                if 'm' in fe['ts']: ts[2] = fe['ts']['m']
                set_ftime(fn,*ts,unix=False)

                if fe.get('cm'): writefile(fn + '.$comment.txt',fe['cm'])
                if 'kv' in fe: writefile(fn + '.$kvpairs.json',json.dumps(fe['kv'],indent=2),'wt')
                if 'avinf' in fe: writefile(fn + '.$avinfo.bin',fe['avinf'])
                if 'os2x' in fe: writefile(fn + '.$os2.ea',fe['os2x'])
            f.close()

            if BUNDLE and not any(x is False for x in BUNDLE):
                ex = None
                for fe in fs:
                    if not 'bun' in fe: continue
                    ct = BUNFMTM[fe['bun']['ct']]
                    kw = {'usize':fe['bun']['us']}
                    if ct == 'lzma': kw['null_usize'] = True
                    elif ct == 'zstd': kw['db'] = db

                    try: writefile(fe['ffn'],decompress(readfile(fe['ffn'])[-fe['bun']['zs']:],ct,**kw))
                    except NotImplementedError as e:
                        mv(fe['ffn'],fe['ffn'] + '.$uns.' + ct)
                        ex = e
                    except Exception as e:
                        if not ct in {'zstd','brotli','lz4'}: raise
                        mv(fe['ffn'],fe['ffn'] + '.$err.' + ct)
                        ex = e
                if not ex is None: raise ex

            for fe in refs:
                fn = fe['ffn']
                copyfile(drefs[fe['sha1']],fn)
                ts = [0,0,0]
                if 'c' in fe['ts']: ts[0] = fe['ts']['c']
                if 'a' in fe['ts']: ts[1] = fe['ts']['a']
                if 'm' in fe['ts']: ts[2] = fe['ts']['m']
                set_ftime(fn,*ts,unix=False)
                if fe.get('cm'): writefile(fn + '.$comment.txt',fe['cm'])
                if 'kv' in fe: writefile(fn + '.$kvpairs.json',json.dumps(fe['kv'],indent=2),'wt')
                if 'avinf' in fe: writefile(fn + '.$avinfo.bin',fe['avinf'])
                if 'os2x' in fe: writefile(fn + '.$os2.ea',fe['os2x'])
            if fs: return

            if readfile(i,size=2) == b'MZ':
                zip7(i,o,'ZIP',True)
                if os.path.exists(o + '/_INST32I.EX_'):
                    if fix_isinstext(o): return
                elif os.path.exists(o + '/Disk1/ikernel.ex_'):
                    if fix_isinstext(o,o + '/Disk1'): return
                elif listdir(o): return
                run(['garbro','-x',i],cwd=o)
                if listdir(o): return
                return 1

            run(['unzip','-q','-o',i,'-d',o])
            if listdir(o): return
            zip7(i,o,'ZIP',True)
            if listdir(o): return
            import zipfile
            if db.print_try: print('Trying with zipfile')
            try:
                with zipfile.ZipFile(i,'r') as z: z.extractall(o)
            except: pass
            else: return
        case 'ZLIB':
            if db.print_try: print('Trying with zlib')
            import zlib

            try:d = zlib.decompress(readfile(i))
            except zlib.error:return 1

            writefile(o + '/' + tbasename(i),d)
            return
        case 'GZIP':
            db.try_custom()
            from lib.file import File
            from lib.crypto import crc_hash
            f = File(i,endian='<')
            asrt(f.read(2) == b'\x1F\x8B' and f.readu8() == 8)
            fl = f.readu8()
            asrt(not fl >> 5)
            mt = f.readu32()
            f.skip(2)

            bs = None
            if fl & 4:
                xl = f.readu16()
                ep = f.pos + xl
                while (f.pos + 4) < ep:
                    tg,sz = f.read(2),f.readu16()
                    xep = f.pos + sz
                    match tg:
                        case b'\0\0': pass # padding
                        case b'BC': # BGZF
                            bs = f.readu16() + 1
                        case _: raise NotImplementedError(f'Unknown extra field {repr(tg)[1:]}')
                    f.seek(xep)
                f.seek(ep)

            fn = None
            if fl & 8: fn = f.read0s().decode('utf-8')
            if not fn:
                fn = tbasename(i)
                if i.lower().endswith('.tgz'): fn += '.tar'
                elif not '.' in fn and fl & 1: fn += '.txt'
            if fl & 0x10: writefile(o + '/$comment.txt',f.read0s())
            if fl & 2:
                hd = f.peek(f.pos,poffset=-f.pos)
                asrt(crc_hash(hd,'crc32_16') == f.readu16())

            if bs:
                f.seek(0)
                of = xopen(o + '/' + fn,'wb')
                while f:
                    p = f.pos
                    asrt(f.read(2) == b'\x1F\x8B' and f.readu8() == 8)
                    fl = f.readu8()
                    f.skip(6)

                    bs = None
                    if fl & 4:
                        xl = f.readu16()
                        ep = f.pos + xl
                        while (f.pos + 4) < ep:
                            tg,sz = f.read(2),f.readu16()
                            xep = f.pos + sz
                            if tg == b'BC': bs = f.readu16() + 1
                            f.seek(xep)
                        f.seek(ep)
                    if fl & 8: f.read0s()
                    if fl & 0x10: f.read0s()
                    if fl & 2: f.skip(2)

                    zs = (bs or f.size) - (f.pos - p) - 8
                    f.skip(zs)
                    crc,us = f.readu32(),f.readu32()
                    f.back(zs + 8)
                    d = f.decompress(zs,'deflate',usize=us)
                    asrt(crc == crc_hash(d,'crc32'))
                    of.write(d)
                    if not bs: break
                    f.skip(8)

                of.close()
                f.close()
                if mt: set_ftime(o + '/' + fn,mt=mt)
                return fix_tar(o)

            p = f.pos
            f.seek(-8)
            crc,us = f.readu32(),f.readu32()
            f.seek(p)
            d = f.decompress(f.left - 8,'deflate',usize=us)
            f.close()
            if crc: asrt(crc == crc_hash(d,'crc32'))

            bfl = len(d) >= 0x1C and d[:4] == b'CMPR' and int.from_bytes(d[4:8],'little') + 8 == len(d)
            if bfl and not '.' in fn and i.lower().endswith('.bfl'): fn += extname(i)
            nbt = len(d) >= 8 and i.lower().endswith(('.nbt','.dat','.dat_old')) and d[:3] == b'\x0A\0\0' and d[-1] == 0
            if nbt:
                snbt = d[6:6 + int.from_bytes(d[4:6],'big')]
                nbt = snbt.isascii() and snbt.decode('ascii').isprintable()
            if nbt: fn += extname(i)

            writefile(o + '/' + fn,d)
            if mt: set_ftime(o + '/' + fn,mt=mt)

            if bfl: return extract(o + '/' + fn,o,'Colin McRae Rally 2 BFL')
            elif nbt: return extract(o + '/' + fn,o,'Minecraft NBT')
            return fix_tar(o)
        case 'ZPAQ':
            run(['zpaq','x',i,'-f','-to',o])
            if listdir(o): return
        case 'BZip':
            _,f,_ = run(['bzip','-dkc',basename(i)],cwd=dirname(i),text=False)
            if f:
                writefile(o + '/' + tbasename(i),f)
                return
        case 'VirtualBox Disk Image':
            td = TmpDir(path=o)
            zip7(i,td,t,True)
            if os.path.exists(td + '/1.img'):
                zip7(td + '/1.img','-o' + o,None,True)
                td.destroy()
                if listdir(o): return
            td.destroy()
        case 'RAR':
            cmd = ['unrar','x','-or','-op' + o]
            if i.lower().endswith('-m4ckd0ge_repack.rar'): cmd += ['-pM4CKD0GE']
            run(cmd + [i])
            if listdir(o): return
            zip7(i,o,t)
            if listdir(o): return
        case 'StuffIt'|'AmiPack':
           e,_,_ = run(['unar','-f','-o',o,i])
           if not e: return
        case 'KryoFlux'|'SCP Flux'|'HxC Floppy IMG':
            bcmd = ['hxcfe','-finput:' + i]
            _,op,_ = run(bcmd + ['-list'])

            op = op.replace('\r','')
            if '------- Disk Tree --------' in op:
                op = op.split('------- Disk Tree --------\n')[1].split('--------------------------\n')[0]
                cp = []
                fs = []
                for t in re.findall(r"( *)([> ])([^<\n]+) <\d+>\n",op):
                    while len(cp)*4 > len(t[0]): cp.pop()
                    if t[1] == '>':
                        cp.append(t[2])
                        mkdir(o + '/' + '/'.join(cp))
                    else:
                        f = '/'.join(cp + [t[2]])
                        run(bcmd + ['-getfile:/' + f],cwd=dirname(o + '/' + f),print_try=False)

                if fs and rldir(o): return
        case 'BBC Micro SSD':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            dn = f.reads(8,'latin-1').rstrip('\0 ')
            if dn: writefile(o + '/$diskname.txt',dn,'wt')
            f.seek(0)
            ns = [(f.reads(7,'latin-1').rstrip('\0 '),f.reads(1,'latin-1')) for _ in range(0x20)]
            fs = []
            for ix in range(0x20):
                f.skip(4)
                sz = f.readu16() | (((f.readu8() >> 4) & 3) << 16)
                fs.append((f.readu8() * 0x100,sz,*ns[ix]))

            for fe in fs[1:]: # skip disk name
                if len(fe[2]) == 0:
                    asrt(fe[1] == 0)
                    continue
                f.seek(fe[0])
                writefile(o + '/' + fe[3].rstrip('\0 $') + '/' + fe[2],f.readc(fe[1]))

            f.close()
            if fs: return
        case 'ACE':
            db.get('acefile')
            if db.print_try: print('Trying with acefile')
            from bin.acefile import open as aceopen # type: ignore

            try:
                with aceopen(i) as f: f.extractall(path=o)
            except: pass
            else: return
        case 'AIN':
            dosbox(['ain','x',i],stdin='\n')
            if listdir(o): return
        case 'HA': return msdos(['ha','xqy',i],cwd=o)
        case 'AKT': return msdos(['akt','x',i],cwd=o)
        case 'AMGC': return msdos(['amgc','x',i],cwd=o)
        case 'CPC IMG':
            if db.print_try: print('Trying with amstradcpcexplorer')
            run([sys.executable,db.get('amstradcpcexplorer'),i,'-dir','-ex'],print_try=False,cwd=o)
            if listdir(o): return
        case '2MG'|'Apple DOS IMG':
            td = 'tmp' + os.urandom(8).hex()
            run(['cadius','EXTRACTVOLUME',i,td])
            if listdir(td):
                copydir(td,o,True)
                for f in rldir(o):
                    if f.endswith('\\_FileInformation.txt'): remove(f)
                    else: rename(f,f[:-7])
                return
            remove(td)

            if db.print_try: print('Trying with acx')
            run(['java','-jar',db.get('acx'),'x','--suggested','-d',i,'-o',o],print_try=False)
            if listdir(o): return
        case 'AR':
            run(['ar','x',i],cwd=o)
            if listdir(o): return
            zip7(i,o,t,True)
            if listdir(o): return
        case 'ARQ': return msdos(['arq','-x',i,'*',o])
        case 'XX34': return msdos(['xx34','D',i],tmpi=True,cwd=o)
        case 'UHARC':
            dosbox(['uharcd','x',i])
            if listdir(o): return
        case 'Stirling Compressed'|'The Compressor'|'CP Shrink'|'DIET'|'Acorn Spark'|'Aldus LZW'|'Aldus Zip'|'ARX'|'CAZIP'|'DOS Backup'|\
             'EPOC App Info'|'EPOC Install Package'|'GEM Resource'|'OS/2 Installation Package'|'Microsoft Comic Chat Character':
            od = rldir(o)
            run(["deark","-od",o,'-a',i])
            for x in rldir(o):
                if x in od: continue
                xb = basename(x)
                if xb.startswith('output.') and len(xb.split('.')) > 2 and len(xb.split('.')[1]) in {3,4,5} and xb.split('.')[1].isdigit():
                    rn = xb.split('.',2)[2]
                    if rn == 'bin':
                        if '.' in i[-4:] and i[-1] == '_': mv(o + '/' + fs[0],o + '/' + basename(i[:-1]))
                        else: mv(o + '/' + fs[0],o + '/' + tbasename(i))
                    elif len(rn.split('.')) > 1: mv(x,dirname(x) + '\\' + rn)
                    else: mv(x,o + '\\' + xb[7:])
            fs = listdir(o)
            if fs: return
        case 'ZOO':
            if readfile(i,size=2) == b'MZ':
                run(['deark','-od',o,i])
                tf = o + '\\output.000.zoo'
                if not exists(tf): return 1
                r = extract(tf,o,'ZOO')
                if r: mv(tf,o + '\\' + tbasename(i) + '.zoo')
                else: remove(tf)
                return r

            r = extract(i,o,'Stirling Compressed') # deark
            if r:
                remove(o)
                mkdir(o)
            else: return

            run(['unzoo','-x','-o','-j',o + '\\',i])
            if listdir(o): return
        case 'YAC': return msdos(['yac','x',i],cwd=o)
        case 'Yamazaki Zipper':
            run(['yzdec','-d' + o,'-y',i])
            if listdir(o): return
        case '777'|'BIX'|'UFA':
            # merge 7z predecessors
            run([t.lower(),'x','-y','-o' + o,i])
            if listdir(o): return
        case 'Brotli':
            db.try_custom()
            from lib.file import decompress
            d = decompress(readfile(i),'brotli')
            if d:
                writefile(o + '/' + tbasename(i),d)
                return fix_tar(o)
        case 'BZip3':
            tf = o + '/' + basename(i)
            symlink(i,tf)
            run(['bzip3','-d','-f','-k',tf])
            remove(tf)
            if listdir(o): return fix_tar(o)
        case 'Turbo Range Coder':
            of = o + '/' + tbasename(i)
            run(['turborc','-d',i,of])
            if exists(of) and getsize(of): return
        case 'ACB':
            dosbox(['acb','r',i])
            if listdir(o): return
        case 'ALZip'|'EGG':
            run(['alzipcon','-x','-oa',i,o])
            if listdir(o): return
        case 'AR7':
            _,_,r = run(['msdos',db.get('ar7'),'l',i])
            r = re.sub('\n+','\n',r.replace('\r','')).split('----------- ------------- ---- ------\n')[-1].strip().rsplit('\n',1)[0].replace('\n ',' ')
            for f in r.split('\n'): mkdir(o + '/' + dirname(f.rsplit(None,3)[0].replace(':','\\')))

            return msdos(['ar7','x',i],cwd=o)
        case 'ARG': return msdos(['arg','e',i],cwd=o)
        case 'ASD':
            tf = i
            f = xopen(i,'rb')
            if f.read(2) == b'MZ':
                tf = TmpFile('.asd')
                f.seek(0x9000)
                tf.write(f.read())
            f.close()
            run(['asd','x','-y',tf],cwd=o)
            if hasattr(tf,'destroy'): tf.destroy()
            if listdir(o): return
        case 'BlakHole':
            run(['izarccl','-e','-o','-p' + o,i])
            if listdir(o): return
        case 'Compact Pro'|'MacBinary'|'Disk Doubler':
            cmd = ['unar','-f','-D','-k','visible']
            try: i.encode('ascii')
            except UnicodeEncodeError:
                try: i.encode('x-mac-japanese')
                except UnicodeEncodeError: pass
                else:
                    try: inf = json.loads(run(['lsar','-json',i])[1].replace('\t',' ').replace('}\n  "lsarInnerFormatName"','},"lsarInnerFormatName"'))
                    except json.JSONDecodeError: pass
                    else:
                        if inf['lsarEncoding'] not in {'macintosh','UTF-8'}: cmd += ['-e','x-mac-japanese']

            run(cmd + ['-o',o,i])
            if listdir(o): return
        case 'DAR':
            run(['dar','-x','/cygdrive/' + i.replace('\\','/').replace(':',''),'-q','-qcrypto','-R','/cygdrive/' + o.replace('\\','/').replace(':','')])
            if listdir(o): return
        case 'DietDisk':
            ins = getsize(i)
            copy(i,o + '/TMP.EXT')
            dosbox(['fatten','O:\\TMP.EXT'],custs=dirname(db.get('dietdisk')) + '\\FATTEN.EXE',tmpi=False,xcmds=['-c','C:','-c','DIETDISK.COM','-c','O:'])
            if getsize(o + '/TMP.EXT') != ins:
                mv(o + '/TMP.EXT',o + '/' + basename(i))
                return
        case 'DWC':
            tf = i
            f = xopen(i,'rb')
            if f.read(2) == b'MZ':
                siz = f.seek(0,2)
                f.seek(0)
                tf = TmpFile('.dwc')
                d = f.read(siz-0x10)
                tf.write(d + f.read(0x10).rsplit(b'DWC')[0] + b'DWC')
                del d
            f.close()
            r = msdos(['dwc','x',tf],cwd=o)
            if hasattr(tf,'destroy'): tf.destroy()
            return r
        case 'Rob Northen Compression'|'Amiga XPK'|'File Imploder'|'Compact'|'Crunch-Mania'|'Freeze Compressed'|'FVL0 Compressed':
            of = o + '/' + tbasename(i)
            run(['ancient','decompress',i,of])
            if exists(of) and getsize(of): return
        case 'ABE': return msdos(['dabe','-v','+i',i],cwd=o)
        case 'CarComp': return msdos(['car','x',i],cwd=o)
        case 'PeaZip':
            td = o + '\\tmp' + os.urandom(4).hex()
            run(['pea','UNPEA',i,td,'RESETDATE','SETATTR','EXTRACT2DIR','HIDDEN'])
            if exists(td):
                if listdir(td):
                    copydir(td,o,True)
                    return
                remove(td)
        case 'Intel HEX':
            db.try_custom()
            f = xopen(i,encoding='utf-8')

            fs = [[]]
            for l in f.readlines():
                if l[0] != ':': continue
                datal = int(l[1:1+2],16)
                addr = int(l[3:3+4],16)
                typ = int(l[7:7+2],16)
                asrt(typ in {0,1},hex(typ))

                if datal:
                    data = bytes.fromhex(l[9:9+2*datal])
                    fs[-1].append((addr,data))
                if typ == 1: fs.append([])
            f.close()
            if not fs[-1]: fs.pop(-1)

            mf = len(fs) > 1
            for ix,fe in enumerate(fs):
                of = o + '/' + tbasename(i)
                if mf: of += f'_{ix}'
                of = xopen(of + '.bin','wb')
                for addr,data in fe:
                    if addr > of.seek(0,2): of.write(b'\xFF'*(addr-of.tell()))
                    else: of.seek(addr)
                    of.write(data)
                of.close()
            if fs: return
        case 'AppleSingle'|'CrLZH'|'Crunch':
            if not extract1(i,o,'StuffIt'): return # unar
            if not extract1(i,o,'DIET'): return # deark
        case 'PowerPacker':
            if not extract1(i,o,'StuffIt'): return # unar
            if not extract1(i,o,'Amiga XPK'): return # ancient
        case 'BinHex':
            if not extract1(i,o,'AppleSingle'): return # unar & deark
            if not extract1(i,o,'7z'): return # 7z
        case 'BinSCII':
            tf = TmpFile('.bsc')
            writefile(tf.p,b'\n'.join([x.lstrip(b' ') for x in (b'FiLeStArTfIlEsTaRt' + readfile(i).split(b'FiLeStArTfIlEsTaRt',1)[1]).split(b'\n')]))
            r = extract1(tf.p,o,'DIET') # deark
            tf.destroy()
            return r
        case 'Compaq QRST IMG'|'CopyQM IMG'|'FDCOPY CFI IMG':
            tf = TmpFile('.img',path=o)
            run(['dskconv','-otype','raw',i,tf])
            if not exists(tf.p) or not getsize(tf.p): return 1
            if extract1(tf.p,o,'IMG'): mv(tf.p,o + '/' + tbasename(i) + '.img')
            tf.destroy()
            return
        case 'UUencoded':
            db.try_custom()
            from lib.crypto import decrypt
            d = readfile(i,'r')
            if 'begin ' in d: d = [x for x in re.findall(r'(?ms)begin \d+ ([^\n]+)\n(.+?)\nend\n',d)]
            else: d = [(tbasename(i),d)]

            for en,ed in d: writefile(o + '/' + en,decrypt(ed,'uue'))
            if d: return
        case 'HTTP Response':
            db.try_custom()
            from urllib.parse import unquote_to_bytes
            hd,d = readfile(i).split(b'\r\n\r\n',1)
            hd = {x.split(b': ',1)[0].decode('latin1'):x.split(b': ',1)[1] for x in hd.split(b'\r\n')[1:]}
            hds = {'$header':hd.split(b'\r\n')[0].decode('latin1')} | {x:hd[x].decode('latin1') for x in hd}
            hd = {x.lower():hd[x] for x in hd}

            of = o + '/'
            if 'content-disposition' in hd and\
               b'attachment' in hd['content-disposition'].lower() and\
               b'filename'   in hd['content-disposition'].lower():
                fn = hd['content-disposition'].split(b'; ',1)[1]
                fn = fn[8:].strip()
                if fn[:1] == b'*':
                    enc,fn = fn[2:].strip().split(b"''",1)
                    fn = fn.strip().split()[0]
                    of += unquote_to_bytes(fn).decode(enc.decode('latin1'))
                else:
                    fn = fn[1:].strip()
                    if fn[:1] == b'"':
                        rfn,fn = fn[1:].split(b'"')[0]
                        if b'; ' in fn and b'filename' in fn.lower() and b"''" in fn:
                            enc,fn = fn[2:].strip().split(b"''",1)
                            fn = fn.strip().split()[0]
                            of += unquote_to_bytes(fn).decode(enc.decode('latin1'))
                        else: of += unquote_to_bytes(rfn).decode('latin1')
            elif 'content-type' in hd: of += tbasename(i) + '.' + mime2ext(hd['content-type'])
            else: of += basename(i)

            writefile(of,d)
            json.dump(hds,open(of + '_headers.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
            return
        case 'Motorola S-Record':
            db.try_custom()
            f = xopen(i)

            fs = [[]]
            for l in f.readlines():
                if l[0] != 'S': continue
                l = l[1:].rstrip()
                t = int(l[0])
                if t in {4,5,6}: continue

                if t in {0,7,8,9}: fs.append([])
                if t in {0,1,2,3}:
                    l = l[1:3+int(l[1:3],16)*2]
                    c,l = l[-2:],l[:-2]
                    if (0xFF - (sum(bytes.fromhex(l)) & 0xFF)) != int(c,16): print('Checksum error',l)
                    l = l[2:]

                    if t in {0,1}: a,l = l[:4],l[4:]
                    elif t == 2: a,l = l[:6],l[6:]
                    elif t == 3: a,l = l[:8],l[8:]

                    d = bytes.fromhex(l)
                    if t == 0:
                        try: n = d.rstrip(b'\0').decode('ascii')
                        except: pass
                        else: fs[-1].append(n)
                    fs[-1].append((int(a,16),d))
            f.close()

            for ix,fe in enumerate(fs):
                if not fe: continue
                of = o + f'/{ix}'
                if type(fe[0]) == str: of += '_' + fe.pop(0)
                of = xopen(of + '.bin','wb')
                for a,d in fe:
                    if a > of.seek(0,2): of.write(b'\xFF'*(a-of.tell()))
                    of.seek(a)
                    of.write(d)
                of.close()
            if fs: return
        case 'Bootable FAT16 IMG':
            db.try_custom()
            from lib.file import File,pdosdate
            f = File(i,endian='<')

            f.seek(0xA0B)
            asrt(f.readu8() == 8)
            f.skip(0x14)

            fs = []
            while f:
                fn = f.read(8)
                if not fn[0]: break
                if fn[0] in {5,0xE5}: fn = fn[1:]
                fn = fn.decode('ascii').rstrip()
                ex = f.read(3).decode('ascii').rstrip()
                if ex: fn += '.' + ex

                atr = f.readu8()
                if not fn.strip('.'):
                    if atr & 0x10:
                        f.skip(0x14)
                        continue
                    else: fn = f'_{fn}_'
                if atr & 0x10: raise NotImplementedError(f'Directory @ 0x{f.pos-12:4X}')
                elif atr & 0x40: raise NotImplementedError(f'Device @ 0x{f.pos-12:4X}')
                f.skip(1)

                rcd = f.read(5)
                f.skip(4)
                if sum(rcd):
                    f.skip(4)
                    ct = int.from_bytes(rcd[1:3],'little')
                    cd = int.from_bytes(rcd[3:5],'little')
                else:
                    ct = f.readu16()
                    cd = f.readu16()

                fs.append((fn,f.readu16(),f.readu32(),pdosdate(cd,ct,rcd[0] if sum(rcd) else 0)))

            csf = []
            for fe in fs:
                if fe[2]: csf.append(fe)
            sorted(csf,key=lambda x:x[1])
            if len(csf) < 2: cs = 0x200
            else: cs = 1 << (csf[0][2] // (csf[1][1] - csf[0][1])).bit_length()

            for fe in fs:
                f.seek((fe[1]+1) * cs)
                writefile(o + '/' + fe[0],f.read(fe[2]))
                if fe[3]: set_ftime(o + '/' + fe[0],fe[3])
            if fs: return
        case 'Base64':
            if db.print_try: print('Trying with custom extractor')
            from lib.crypto import decrypt
            d = decrypt(readfile(i),'b64',fix=True)
            try: asrt('\0' not in d.decode('utf-8'))
            except: ext = guess_ext(d)
            else:
                if d.strip().startswith(b'{"') and d.strip().endswith(b'}'): ext = 'json'
                else: ext = 'txt'
            writefile(f'{o}/{tbasename(i)}.{ext}',d)
            return
        case 'Web ARchive':
            db.try_custom()
            from lib.crypto import decrypt
            import json
            f = xopen(i,'rb')

            tr = {}
            while True:
                if f.readline().rstrip(b'\r\n') != b'WARC/1.0': break
                hd = read_http_head(f.readline)
                hds = hd.copy()
                hd = {k.lower():v for k,v in hd.items()}
                asrt('warc-type' in hd and 'content-length' in hd)
                if not hd['warc-type'] in tr: tr[hd['warc-type']] = 0

                bfn = f'{o}/{hd["warc-type"]}/{tr[hd['warc-type']]}_'
                if hd['warc-type'] == 'warcinfo':
                    json.dump(read_http_head(f.readline,int(hd['content-length']),idn=True),xopen(bfn + 'info.json','w',encoding='utf-8'),indent=2,ensure_ascii=False)
                elif hd['warc-type'] in {'request','response'}:
                    p = int(hd['content-length'])
                    bp = f.tell()
                    gv = f.readline(p)
                    rhd = read_http_head(f.readline,p - len(gv))
                    hds['$http'] = {'$header':gv.strip().decode('utf-8')} | rhd.copy()
                    rhd = {k.lower():v for k,v in rhd.items()}

                    if 'content-disposition' in rhd and\
                       'attachment' in rhd['content-disposition'].lower() and\
                       'filename'   in rhd['content-disposition'].lower():
                        rfn = rhd['content-disposition'].split('; ',1)[1]
                        rfn = rfn[8:].strip()
                        if rfn[:1] == '*':
                            enc,rfn = rfn[2:].strip().split("''",1)
                            rfn = rfn.strip().split()[0]
                            fn = decrypt(rfn,'url').decode(enc)
                        else:
                            rfn = rfn[1:].strip()
                            if rfn[:1] == '"':
                                rfn,rfn = rfn[1:].split('"')[0]
                                if '; ' in rfn and 'filename' in rfn.lower() and "''" in rfn:
                                    enc,rfn = rfn[2:].strip().split("''",1)
                                    rfn = rfn.strip().split()[0]
                                    fn = decrypt(rfn,'url').decode(enc.decode('latin1'))
                                else: fn = decrypt(rfn,'url').decode('latin1')
                    elif 'content-type' in rhd: fn = 'content.' + mime2ext(rhd['content-type'])
                    else: fn = 'content.bin'

                    ll = min(int(rhd.get('content-length',bp + p)),p-(f.tell()-bp))
                    if ll: writefile(bfn + fn,f.read(ll))
                    f.seek(bp + p)
                else: raise NotImplementedError(hd['warc-type'])
                json.dump(hds,xopen(bfn + 'header.json','w',encoding='utf-8'),indent=2,ensure_ascii=False)
                tr[hd['warc-type']] += 1
                f.readline();f.readline()

            f.close()
            if tr: return
        case 'Git Bundle':
            run(['git','clone',i,o])
            if listdir(o): return
        case 'Bencode':
            db.try_custom()
            import json
            f = xopen(i,'rb')
            s = f.seek(0,2);f.seek(0)
            fc = 0

            def reads(n=1):return f.read(n).decode('ascii')
            def readv(ty=None):
                nonlocal fc
                if ty is None: ty = reads()
                match ty:
                    case 'd':
                        b = {}
                        while 1:
                            ty = reads()
                            if ty == 'e':break
                            k = readv(ty)
                            b[k] = readv()
                        return b
                    case 'l':
                        b = []
                        while 1:
                            ty = reads()
                            if ty == 'e':break
                            b.append(readv(ty))
                        return b
                    case 'i':
                        b = 0
                        while 1:
                            c = reads()
                            if c.isdigit(): b = b*10 + int(c)
                            else: break
                        return b
                    case '0'|'1'|'2'|'3'|'4'|'5'|'6'|'7'|'8'|'9':
                        f.seek(-1,1)
                        l = readv('i')
                        d = f.read(l)
                        try:
                            b = d.decode('utf-8')
                            asrt(b.isprintable())
                        except:
                            b = f'${fc}.bin'
                            writefile(o + '/' + b,d)
                            fc += 1
                        return b
                    case _: raise NotImplementedError(ty)

            ob = []
            while f.tell() < s: ob.append(readv())
            f.close()
            if ob:
                json.dump(ob,xopen(f'{o}/{tbasename(i)}.json','w',encoding='utf-8'),indent=2,ensure_ascii=False)
                return
        case 'TTComp':
            of = o + '/' + ext_expand(basename(i))
            run(['ttdecomp',i,of])
            if exists(of) and getsize(of): return
        case 'Diff Patch':
            db.try_custom()
            f = open(i,encoding='utf-8')

            ix = 0
            fs = {}
            l = f.readline()
            while True:
                cc = ''
                while True:
                    if not l: break
                    if l.startswith('--- '): break
                    cc += l
                    l = f.readline()
                if not l: break
                writefile(f'{o}/$comments/{ix:03d}.txt',cc,'w')
                ix += 1

                mip = l[4:-1]
                l = f.readline()
                asrt(l.startswith('+++ '))
                plp = l[4:-1]
                if not mip in fs: fs[mip] = []
                if not plp in fs: fs[plp] = []

                l = f.readline()
                while True:
                    if not l.startswith('@@ '): break
                    ml,pl = l[3:-1].split('@@',1)[0].strip().split()
                    asrt(ml[0] == '-' and pl[0] == '+')
                    mlo = int(ml[1:].split(',',1)[0])
                    plo = int(pl[1:].split(',',1)[0])
                    mb = []
                    pb = []
                    while True:
                        l = f.readline()
                        if not l: break
                        if l[0] == ' ':
                            mb.append(l[1:-1])
                            pb.append(l[1:-1])
                        elif l[0] == '-': mb.append(l[1:-1])
                        elif l[0] == '+': pb.append(l[1:-1])
                        else: break
                    if l == "\\ No newline at end of file\n": l = f.readline()
                    else:
                        mb.append('')
                        pb.append('')

                    fs[mip].append((mlo,mb))
                    fs[plp].append((plo,pb))
            f.close()

            if '/dev/null' in fs: fs.pop('/dev/null')
            for x in fs:
                ls = []
                for yo,yd in fs[x]:
                    if (yo+len(yd)) > len(ls): ls.extend(['']*(yo+len(yd)-len(ls)))
                    for ix,l in enumerate(yd): ls[yo+ix] = l
                writefile(o + '/' + x,'\n'.join(ls),'w')

            if fs: return
        case 'Google Authenticator Migration URL':
            ALGM = {1:'SHA1',2:'SHA256',3:'SHA512',4:'MD5'}
            DIGM = {1:6,2:8}
            TYPM = {1:'hotp',2:'totp'}

            db.try_custom()
            from lib.file import File
            from lib.crypto import decrypt,encrypt
            from urllib.parse import urlparse,parse_qs
            u = urlparse(i)
            asrt(u.scheme == 'otpauth-migration' and u.hostname == 'offline')
            u = parse_qs(u.query)
            asrt('data' in u)
            f = File(decrypt(u['data'][0],'b64url'),endian='>')

            ob = []
            while f:
                tg = f.readleb128u()
                fn,wt = tg >> 3,tg & 7
                if fn == 1 and wt == 2:
                    ep = f.readleb128u() + f.pos
                    otp = {'s':b'','n':'','i':'','a':1,'d':1,'t':2,'c':0}
                    while f < ep:
                        tg = f.readleb128u()
                        fn,wt = tg >> 3,tg & 7
                        if fn == 1 and wt == 2: otp['s'] = f.readc(f.readleb128u())
                        elif fn == 2 and wt == 2: otp['n'] = f.reads(f.readleb128u(),'utf-8')
                        elif fn == 3 and wt == 2: otp['i'] = f.reads(f.readleb128u(),'utf-8')
                        elif fn == 4 and wt == 0: otp['a'] = f.readleb128u()
                        elif fn == 5 and wt == 0: otp['d'] = f.readleb128u()
                        elif fn == 6 and wt == 0: otp['t'] = f.readleb128u()
                        elif fn == 7 and wt == 0: otp['c'] = f.readleb128u()
                        elif wt == 0: f.readleb128u()
                        elif wt == 2: f.skip(f.readleb128u())
                        else: raise NotImplementedError(wt)
                    ob.append(otp)
                elif wt == 0: f.readleb128u()
                elif wt == 2: f.skip(f.readleb128u())
                else: raise NotImplementedError(wt)

            f.close()
            if ob:
                rob = []
                for b in ob:
                    par = ['secret=' + encrypt(b['s'],'b32',bytes=False).rstrip('=')]
                    if b['i']: par.append('issuer=' + b['i'])
                    par.append(f'algorithm={ALGM[b["a"]]}')
                    par.append(f'digits={DIGM[b["d"]]}')
                    rob.append(f'otpauth://{TYPM[b["t"]]}/{b["n"]}?' + '&'.join(par))
                writefile(o + '/otpauth.txt','\n'.join(rob),'w')
                return
        case 'FreeArc':
            run(['unarc','x','-o+','-dp' + o,i])
            if listdir(o): return
        case 'Microsoft SZDD':
            db.try_custom()
            from lib.file import decompress
            writefile(o + '/' + ext_expand(basename(i)),decompress(readfile(i),'szdd'))
            return

    return 1

def read_http_head(readline,max:int=None,idn=False):
    o = {}
    p = 0
    while not max or p < max:
        l = readline(max-p if max else None)
        p += len(l)
        l = l.rstrip(b'\r\n')
        if not l: break
        if idn and l[0] == 0x20:
            try: lr = l.decode('utf-8');asrt(lr.isprintable())
            except: lr = l.decode('latin1')
            o[list(o)[-1]] += lr
            continue
        l = l.lstrip()
        if not l: break
        try: lr = l.decode('utf-8');asrt(lr.isprintable())
        except: lr = l.decode('latin1')
        o[lr.split(': ',1)[0]] = lr.split(': ',1)[1]
    return o
