from .main import *

CTTR = {
    'application/octet-stream':'bin',
    'application/epub+zip':'epub',
    'application/javascript':'js',
    'application/java-archive':'jar',
    'audio/mpeg':'mp3',
    'audio/vorbis':'ogg',
    'image/jpeg':'jpg',
    'image/svg+xml':'svg',
    'image/vnd.adobe.photoshop':'psd',
    'image/vnd.microsoft.icon':'ico',
    'image/dicom-rle':'dcm',
    'image/heic-sequence':'heic',
    'image/heif-sequence':'heif',
    'image/tiff-fx':'tif',
    'image/tiff':'tif',
    'model/gltf-binary':'gltf',
    'model/gltf+json':'gltf',
    'model/step+xml':'step',
    'model/step+zip':'step',
    'model/step-xml+zip':'step',
    'model/vnd.gs-gdl':'gdl',
    'model/vnd.moml+xml':'moml',
    'model/vnd.usdz+zip':'usdz',
    'model/vnd.valve.source.compiled-map':'bsp',
    'model/x3d-vrml':'x3d',
    'model/x3d+xml':'x3d',
    'model/x3d+fastinfoset':'x3d',
    'multipart/alternative':'bin',
    'multipart/appledouble':'_',
    'multipart/byteranges':'bin',
    'multipart/digest':'bin',
    'multipart/encrypted':'bin',
    'multipart/form-data':'bin',
    'multipart/header-set':'txt',
    'multipart/mixed':'bin',
    'multipart/multilingual':'txt',
    'multipart/related':'bin',
    'multipart/report':'bin',
    'multipart/signed':'bin',
    'multipart/x-mixed-replace':'bin',
    'multipart/parallel':'bin',
    'multipart/voice-message':'vpm',
    'multipart/vnd.bint.med-plus':'bmed',
    'text/plain':'txt',
    'text/javascript':'js',
    'text/ecmascript':'js',
    'text/tab-separated-values':'tsv',
    'video/3gpp':'3gp',
    'video/matroska':'mkv',
    'video/matroska-3d':'mkv',
    'video/mpeg':'mpg',
    'video/mpeg4-generic':'mp4',
}

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
            r = open(oup + '/_OUT.TXT','rb').read()
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
        case '7z'|'MSCAB'|'Windows Help File'|'ARJ'|'ZSTD'|'JFD IMG'|'TAR'|'yEnc'|'xz'|'BZip2'|'SZDD'|'LZIP'|'CPIO'|'Asar'|'SWF'|'ARJZ'|\
             'DiskDupe IMG'|'XAR'|'Z'|'EXT'|'SquashFS'|'VHD'|'Compressed ISO'|'CramFS'|'Google Update Installer':
            _,_,e = run(['7z','x',i,'-o' + o,'-aou'])
            if 'ERROR: Unsupported Method : ' in e and open(i,'rb').read(2) == b'MZ':
                rmtree(o,True)
                mkdir(o)
                opt = db.print_try
                db.print_try = False
                if opt: print('Trying with input')
                run([i,'x','-o' + o,'-y'])
                db.print_try = opt
            if listdir(o) and not exists(o + '/.rsrc'):
                if t == 'MSCAB': fix_cab(o);return
                elif t in ('ZSTD','xz','BZip2','LZIP'): return fix_tar(o)
                else: return
        case 'Stripped TAR':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')

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
                fn = fn.rstrip(b'\0').decode()

                assert f.read(8*3) == (b'0000000\0'*3)
                fs = int(f.read(11).decode(),8)

                assert f.read(22) == (b'\0' + b'0'*11 + b'\0' + b'0'*7 + b'\0 ')
                f.seek(0xAC,1)
                #assert sum(f.read(0xAC)) == 0,f.tell()
                assert f.read(0x10) == (b'0000000\0'*2)
                assert sum(f.read(0xA7)) == 0

                open(o + '/' + fn,'wb').write(f.read(fs))
            return
        case 'LHARC':
            run(['lha','xf','--extract-broken-archive','-w=' + o,i])
            if listdir(o): return
            run(['7z','x',i,'-o' + o,'-aou'])
            if listdir(o): return
        case 'PDF':
            run(['pdfdetach','-saveall','-o',o + '\\out',i])
            run(['pdfimages','-j',i,o + '\\img'])
            run(['pdftohtml','-embedbackground','-meta','-overwrite','-q',i,o + '\\html'])
            if listdir(o + '/html'): return
            remove(o + '/html')
        case 'Nero CD IMG':
            run(['7z','x','-tnrg',i,'-o' + o,'-aou'])
            for ix,f in enumerate(listdir(o)):
                tf = o + f'/{ix:02d}' + extname(f).lower()
                to = o + f'\\{ix:02d}'
                os.rename(o + '/' + f,tf)
                if extname(tf) == '.iso':
                    mkdir(to)
                    if extract1(tf,to,'ISO'): remove(to)
                    else: remove(tf)
            if listdir(o): return
        case 'CDI'|'Aaru'|'ACT Apricot IMG':
            osj = OSJump()
            osj.jump(dirname(i))
            td = 'tmp' + os.urandom(8).hex()
            run(['aaru','filesystem','extract',i,td])
            osj.back()
            td = dirname(i) + '\\' + td
            if exists(td) and listdir(td):
                ret = False
                for td1 in listdir(td):
                    td1 = td + '/' + td1
                    if listdir(td1):
                        copydir(td1 + '/' + listdir(td1)[0],o)
                        ret = True
                remove(td)
                if ret: return
            remove(td)
        case 'ISO'|'IMG'|'Floppy Image'|'UDF'|'DOS IMG':
            _,e,_ = run(['aaru','filesystem','info',i],print_try=False)
            iso_udf = t in ('ISO','UDF') and 'As identified by ISO9660 Filesystem.' in e and 'Identified by 2 plugins' in e

            if not iso_udf and not extract1(i,o,'Aaru'): return

            bd = listdir(o)
            run(['7z','x',i,'-o' + o,'-aou'])
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
                        fo = open(f,'rb')
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
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            f.seek(0x8000)
            dat = f.read(0x1000)
            if not b'\x01CD001\x01\x00' in dat: return 1
            tf = o + '\\TMP' + os.urandom(8).hex() + '.iso'
            f.seek(dat.index(b'\x01CD001\x01\x00'))
            open(tf,'wb').write(f.read())

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
                run(['7z','x','-tAPM',i,'-o' + o,'-aou'])
                fs = listdir(o)
                if len(fs) > 1:
                    for f in fs:
                        f = o + '\\' + f.lower()
                        od = noext(f)
                        if f.endswith('.iso'):
                            mkdir(od)
                            if not extract(f,od,'ISO'):
                                remove(f,od)
                                assert not exists(od)
                        elif f.endswith('.hfs'):
                            mkdir(od)
                            if not extract(f,od,'Apple Disk Image'):
                                remove(f,od)
                                assert not exists(od)
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
            for p in range(ps):
                if db.print_try: print('Trying with hfsexplorer/unhfs')
                cop = o + (f'\\{p}' if ps > 1 else '')
                mkdir(cop)
                _,_,e = run(['java','--enable-native-access=ALL-UNNAMED','-cp',db.get('hfsexplorer'),'org.catacombae.hfsexplorer.tools.UnHFS','-o',cop,'-resforks','APPLEDOUBLE','-sfm-substitutions','-partition',p,'--',i],print_try=False,env=ce)
                if 'Failed to create directory ' in e: return 1
                if exists(cop) and not listdir(cop): rmdir(cop)
            if not exists(o): mkdir(o)
            if listdir(o): return

            return extract(i,o,'ISO')
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
        case 'ZIP'|'InstallShield Setup ForTheWeb':
            if open(i,'rb').read(2) == b'MZ':
                run(['7z','x',i,'-o' + o,'-aoa'])
                if os.path.exists(o + '/_INST32I.EX_'):
                    if fix_isinstext(o): return
                elif os.path.exists(o + '/Disk1/ikernel.ex_'):
                    if fix_isinstext(o,o + '/Disk1'): return
                elif listdir(o): return
                run(['garbro','x','-o',o,i])
                if listdir(o): return
            else:
                run(['unzip','-q','-o',i,'-d',o])
                if listdir(o): return
                run(['7z','x',i,'-o' + o,'-aoa'])
                if listdir(o): return
                import zipfile
                try:
                    with zipfile.ZipFile(i,'r') as z: z.extractall(o)
                except: pass
                else: return
        case 'ZLIB':
            if db.print_try: print('Trying with zlib')
            import zlib

            id = open(i,'rb').read()
            try:d = zlib.decompress(id)
            except zlib.error:return 1

            open(o + '/' + tbasename(i),'wb').write(d)
        case 'GZIP':
            f = open(i,'rb')
            assert f.read(2) == b'\x1F\x8B'
            if f.read(1) == b'\x08':
                flgs = f.read(1)[0]

                fs = f.seek(-8,2)
                if not sum(f.read(8)):
                    f.seek(10)
                    if flgs & 4: f.seek(int.from_bytes(f.read(2),'little'),1)
                    if flgs & 8:
                        fn = b''
                        s = b''
                        while True:
                            s = f.read(1)
                            if not s: return 1
                            if s == b'\0': break
                            fn += s
                        fn = fn.decode('utf-8')
                    else: fn = tbasename(i)
                    if flgs & 0x10:
                        s = b''
                        while True:
                            s = f.read(1)
                            if not s: return 1
                            if s == b'\0': break
                    if flgs & 2: f.seek(2,1)

                    if (fs-f.tell()) > 2:
                        if db.print_try: print('Trying with gzip')
                        import gzip
                        f.seek(0)
                        open(o + '/' + fn,'wb').write(gzip.decompress(f.read()))
                        f.close()
                        return
            f.close()

            run(['7z','x',i,'-o' + o,'-aoa'])
            if listdir(o): return fix_tar(o)
        case 'ZPAQ':
            run(['zpaq','x',i,'-f','-to',o])
            if listdir(o): return
        case 'BZip':
            _,f,_ = run(['bzip','-dkc',basename(i)],cwd=dirname(i),text=False)
            if f:
                open(o + '/' + tbasename(i),'wb').write(f)
                return
        case 'VirtualBox Disk Image':
            td = TmpDir(path=o)
            run(['7z','x',i,'-o' + td,'-aoa'])
            if os.path.exists(td + '/1.img'):
                run(['7z','x',td + '/1.img','-o' + o,'-aoa'])
                td.destroy()
                if listdir(o): return
            td.destroy()
        case 'RAR':
            cmd = ['unrar','x','-or','-op' + o]
            if i.lower().endswith('-m4ckd0ge_repack.rar'): cmd += ['-pM4CKD0GE']
            run(cmd + [i])
            if listdir(o): return
            run(['7z','x',i,'-o' + o,'-aou'])
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
            run(['bbccp','-i',i,'.',o + '\\'])
            if listdir(o): return
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
        case 'ARQ': return msdos(['arq','-x',i,'*',o])
        case 'XX34': return msdos(['xx34','D',i],tmpi=True,cwd=o)
        case 'UHARC':
            dosbox(['uharcd','x',i])
            if listdir(o): return
        case 'Stirling Compressed'|'The Compressor'|'CP Shrink'|'DIET'|'Acorn Spark'|'Aldus LZW'|'Aldus Zip'|'ARX'|'CAZIP'|'DOS Backup'|\
             'EPOC App Info'|'EPOC Install Package'|'GEM Resource':
            od = rldir(o)
            run(["deark","-od",o,'-a',i])
            for x in rldir(o):
                if x in od: continue
                xb = basename(x)
                if xb.startswith('output.') and len(xb.split('.')) > 2 and len(xb.split('.')[1]) in (3,4,5) and xb.split('.')[1].isdigit():
                    rn = xb.split('.',2)[2]
                    if rn == 'bin':
                        if '.' in i and i[-1] == '_': mv(o + '/' + fs[0],o + '/' + basename(i[:-1]))
                        else: mv(o + '/' + fs[0],o + '/' + tbasename(i))
                    elif len(rn) > 3: move(x,dirname(x) + '\\' + rn)
            fs = listdir(o)
            if fs: return
        case 'ZOO':
            if open(i,'rb').read(2) == b'MZ':
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
            of = o + '/' + tbasename(i)
            run(['brotli','-d','-o',of,i])
            if exists(of) and getsize(of): return fix_tar(o)
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
            f = open(i,'rb')
            if f.read(2) == b'MZ':
                tf = TmpFile('.asd')
                f.seek(0x9000)
                open(tf.p,'wb').write(f.read())
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
                        if inf['lsarEncoding'] not in ('macintosh','UTF-8'): cmd += ['-e','x-mac-japanese']

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
            f = open(i,'rb')
            if f.read(2) == b'MZ':
                siz = f.seek(0,2)
                f.seek(0)
                tf = TmpFile('.dwc')
                d = f.read(siz-0x10)
                open(tf.p,'wb').write(d + f.read(0x10).rsplit(b'DWC')[0] + b'DWC')
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
            if db.print_try: print('Trying with custom extractor')
            f = open(i,encoding='utf-8')

            fs = [[]]
            for l in f.readlines():
                if l[0] != ':': continue
                datal = int(l[1:1+2],16)
                addr = int(l[3:3+4],16)
                typ = int(l[7:7+2],16)
                assert typ in (0,1),hex(datal)[2:].upper()

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
                of = open(of + '.bin','wb')
                for addr,data in fe:
                    if addr > of.seek(0,2): of.write(b'\xFF'*(addr-of.tell()))
                    of.write(data)
                of.close()
            if fs: return
        case 'AppleSingle'|'CrLZH'|'Crunch':
            if not extract1(i,o,'StuffIt'): return # unar
            if not extract1(i,o,'DIET'): return # deark
        case 'BinHex':
            if not extract1(i,o,'AppleSingle'): return # unar & deark
            if not extract1(i,o,'7z'): return # 7z
        case 'BinSCII':
            tf = TmpFile('.bsc')
            open(tf.p,'wb').write(b'\n'.join([x.lstrip(b' ') for x in (b'FiLeStArTfIlEsTaRt' + open(i,'rb').read().split(b'FiLeStArTfIlEsTaRt',1)[1]).split(b'\n')]))
            r = extract1(tf.p,o,'DIET')
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
            if db.print_try: print('Trying with custom extractor')
            import binascii
            d = open(i,encoding='utf-8').read()
            if 'begin ' in d: d = [x for x in re.findall(r'(?ms)begin \d+ ([^\n]+)\n(.+?)\nend\n',d)]
            else: d = [(tbasename(i),d)]

            for en,ed in d:
                f = xopen(o + '/' + en.lstrip('./'),'wb')
                for l in ed.splitlines():
                    try: dl = binascii.a2b_uu(l)
                    except binascii.Error:
                        n = (((ord(l[0])-32) & 63) * 4 + 5) // 3
                        dl = binascii.a2b_uu(l[:n])
                    f.write(dl)
                f.close()
            if d: return
        case 'HTTP Response':
            if db.print_try: print('Trying with custom extractor')
            from urllib.parse import unquote_to_bytes
            hd,d = open(i,'rb').read().split(b'\r\n\r\n',1)
            hd = {x.split(b': ',1)[0].decode('latin-1').lower():x.split(b': ',1)[1] for x in hd.split(b'\r\n')[1:]}

            of = o + '/'
            if 'content-disposition' in hd and\
               b'attachment' in hd['content-disposition'].lower() and\
               b'filename'   in hd['content-disposition'].lower():
                fn = hd['content-disposition'].split(b'; ',1)[1]
                fn = fn[8:].strip()
                if fn[:1] == b'*':
                    enc,fn = fn[2:].strip().split(b"''",1)
                    fn = fn.strip().split()[0]
                    of += unquote_to_bytes(fn).decode(enc.decode('latin-1'))
                else:
                    fn = fn[1:].strip()
                    if fn[:1] == b'"':
                        rfn,fn = fn[1:].split(b'"')[0]
                        if b'; ' in fn and b'filename' in fn.lower() and b"''" in fn:
                            enc,fn = fn[2:].strip().split(b"''",1)
                            fn = fn.strip().split()[0]
                            of += unquote_to_bytes(fn).decode(enc.decode('latin-1'))
                        else: of += unquote_to_bytes(rfn).decode('latin-1')
            elif 'content-type' in hd:
                of += tbasename(i) + '.'
                ct = hd['content-type'].decode('latin-1').split(';')[0].lower()
                if ct in CTTR: ct = CTTR[ct]
                else:
                    ct = ct.split('/')[1].split('+')[-1]
                    if ct.startswith('x-'): ct = ct[2:]
                    if ct.startswith('vnd.'): ct = ct[4:]
                of += ct
            else: of += basename(i)

            open(of,'wb').write(d)
            return
        case 'Base64':
            if db.print_try: print('Trying with custom extractor')
            import base64
            open(o + '/' + tbasename(i) + '.bin','wb').write(base64.b64decode(open(i,'rb').read()))
            return
        case 'Motorola S-Record':
            if db.print_try: print('Trying with custom extractor')
            f = open(i)

            fs = [[]]
            for l in f.readlines():
                if l[0] != 'S': continue
                l = l[1:].rstrip()
                t = int(l[0])
                if t in (4,5,6): continue

                if t in (0,7,8,9): fs.append([])
                if t in (0,1,2,3):
                    l = l[1:3+int(l[1:3],16)*2]
                    c,l = l[-2:],l[:-2]
                    if (0xFF - (sum(bytes.fromhex(l)) & 0xFF)) != int(c,16): print('Checksum error',l)
                    l = l[2:]

                    if t in (0,1): a,l = l[:4],l[4:]
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
                of = open(of + '.bin','wb')
                for a,d in fe:
                    if a > of.seek(0,2): of.write(b'\xFF'*(a-of.tell()))
                    of.write(d)
                of.close()
            if fs: return

    return 1
