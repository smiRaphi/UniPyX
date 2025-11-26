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

        if os.listdir(o): return
        return 1
    def dosbox(cmd:list,inf=i,oup=o,print_try=True,nowin=True,max=True,custs:str=None,tmpi=True,xcmds=[]):
        scr = cmd[0]
        s = db.get(scr)
        if not exists(s): s = custs

        mkdir(oup)
        oinf = inf
        if tmpi:
            td = TmpDir()
            inf = td + '\\TMP' + extname(inf)
            symlink(oinf,inf)

        if print_try and db.print_try: print('Trying with',scr)
        p = subprocess.Popen([db.get('dosbox'),'-nolog','-nopromptfolder','-savedir','NUL','-defaultconf','-fastlaunch','-nogui',('-silent' if nowin else ''),
             '-c','MOUNT I "' + dirname(inf).replace('\\','\\\\') + '"','-c','MOUNT C "' + dirname(custs or s).replace('\\','\\\\') + '"','-c','MOUNT O "' + oup.replace('\\','\\\\') + '"','-c','O:'] + xcmds + [
             '-c',subprocess.list2cmdline(['C:\\' + basename(s)] + [('I:\\' + basename(inf) if x == oinf else x) for x in cmd[1:]]) + (' > _OUT.TXT' if nowin else '')] + (sum([['-set',f'{x}={DOSMAX[x]}'] for x in DOSMAX],[]) if max else []),stdout=-3,stderr=-2)

        while not exists(oup + '/_OUT.TXT'): sleep(0.1)
        while True:
            try: open(oup + '/_OUT.TXT','ab').close()
            except PermissionError: sleep(0.1)
            else: break

        for _ in range(10):
            if os.path.getsize(oup + '/_OUT.TXT') > 0: break
            sleep(0.1)

        while True:
            r = open(oup + '/_OUT.TXT','rb').read()
            if len(r) == os.path.getsize(oup + '/_OUT.TXT'):
                r = r.decode('utf-8')
                break
            sleep(0.1)
        while True:
            try: remove(oup + '/_OUT.TXT')
            except PermissionError: sleep(0.1)
            else: break
        p.kill()
        if tmpi: td.destroy()

        return r

    match t:
        case '7z'|'MSCAB'|'Windows Help File'|'ARJ'|'ZSTD'|'JFD IMG'|'TAR'|'yEnc'|'xz'|'BZip2'|'SZDD'|'LZIP'|'CPIO'|'Asar'|'SWF'|'ARJZ'|\
             'DiskDupe IMG'|'XAR'|'Z'|'EXT'|'SquashFS'|'VHD'|'Compressed ISO':
            _,_,e = run(['7z','x',i,'-o' + o,'-aou'])
            if 'ERROR: Unsupported Method : ' in e and open(i,'rb').read(2) == b'MZ':
                rmtree(o,True)
                mkdir(o)
                opt = db.print_try
                db.print_try = False
                if opt: print('Trying with input')
                run([i,'x','-o' + o,'-y'])
                db.print_try = opt
            if os.listdir(o) and not exists(o + '/.rsrc'):
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
            if os.listdir(o): return
            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o): return
        case 'PDF':
            run(['pdfdetach','-saveall','-o',o + '\\out',i])
            run(['pdfimages','-j',i,o + '\\img'])
            run(['pdftohtml','-embedbackground','-meta','-overwrite','-q',i,o + '\\html'])
            if os.listdir(o + '/html'): return
            remove(o + '/html')
        case 'Nero CD IMG':
            run(['7z','x','-tnrg',i,'-o' + o,'-aou'])
            for ix,f in enumerate(os.listdir(o)):
                tf = o + f'/{ix:02d}' + extname(f).lower()
                to = o + f'\\{ix:02d}'
                os.rename(o + '/' + f,tf)
                if extname(tf) == '.iso':
                    mkdir(to)
                    if extract1(tf,to,'ISO'): remove(to)
                    else: remove(tf)
            if os.listdir(o): return
        case 'CDI'|'Aaru'|'ACT Apricot IMG':
            osj = OSJump()
            osj.jump(dirname(i))
            td = 'tmp' + os.urandom(8).hex()
            run(['aaru','filesystem','extract',i,td])
            osj.back()
            td = dirname(i) + '\\' + td
            if exists(td) and os.listdir(td):
                ret = False
                for td1 in os.listdir(td):
                    td1 = td + '/' + td1
                    if os.listdir(td1):
                        copydir(td1 + '/' + os.listdir(td1)[0],o)
                        ret = True
                remove(td)
                if ret: return
            remove(td)
        case 'ISO'|'IMG'|'Floppy Image'|'UDF':
            _,e,_ = run(['aaru','filesystem','info',i],print_try=False)
            iso_udf = t in ('ISO','UDF') and 'As identified by ISO9660 Filesystem.' in e and 'Identified by 2 plugins' in e

            if not iso_udf and not extract1(i,o,'Aaru'): return

            bd = os.listdir(o)
            run(['7z','x',i,'-o' + o,'-aou'])
            if exists(o):
                for f in os.listdir(o):
                    if f not in bd: return
        case 'CUE+BIN'|'CDI CUE+BIN':
            osj = OSJump()
            osj.jump(dirname(i))
            td = 'tmp' + os.urandom(8).hex()
            run(['aaru','filesystem','extract',i,td])
            osj.back()
            td = dirname(i) + '\\' + td
            if exists(td) and os.listdir(td):
                td1 = td + '/' + os.listdir(td)[0]
                copydir(td1 + '/' + os.listdir(td1)[0],o)
                remove(td)
                return
            remove(o,td)
            mkdir(o)

            run(['bin2iso',i,o,'-a'])[1]
            if os.listdir(o):
                for f in os.listdir(o):
                    if f.endswith('.iso'):
                        f = o + '\\' + f
                        if not extract1(f,o,'ISO'): remove(f)
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
                fs = os.listdir(o)
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
                    if os.listdir(o) != fs: return
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
                if exists(cop) and not os.listdir(cop): rmdir(cop)
            if not exists(o): mkdir(o)
            if os.listdir(o): return

            return extract(i,o,'ISO')
        case 'CHD':
            _,inf,_ = run(['chdman','info','-i',i],print_try=False)

            if "Tag='CHGD'" in inf:
                td = TmpDir()
                run(['chdman','extractcd','-o',td + '/tmp.cue','-f','-i',i])
                if not exists(td + '/tmp.cue'):
                    td.destroy()
                    return 1

                if extract(td + '/tmp.cue',o,'GD-ROM CUE+BIN'):
                    for f in os.listdir(td.p): mv(td + '/' + f,o + '/' + tbasename(i) + extname(f))
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
                elif os.listdir(o): return
                run(['garbro','x','-o',o,i])
                if os.listdir(o): return
            else:
                run(['unzip','-q','-o',i,'-d',o])
                if os.listdir(o): return
                run(['7z','x',i,'-o' + o,'-aoa'])
                if os.listdir(o): return
                import zipfile
                try:
                    with zipfile.ZipFile(i,'r') as z: z.extractall(o)
                except: pass
                else: return
        case 'ZLIB':
            if db.print_try: print('Trying with zlib')
            import zlib
            try:open(o + '/' + tbasename(i),'wb').write(zlib.decompress(open(i,'rb').read()))
            except:pass
            else:return
        case 'GZIP':
            if db.print_try: print('Trying with gzip')
            import gzip
            try:open(o + '/' + tbasename(i),'wb').write(gzip.decompress(open(i,'rb').read()))
            except:pass
            else:return fix_tar(o)

            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o): return fix_tar(o)
        case 'ZPAQ':
            run(['zpaq','x',i,'-f','-to',o])
            if os.listdir(o): return
        case 'BZIP':
            _,f,_ = run(['bzip','-dkc',basename(i)],cwd=dirname(i),text=False)
            if f:
                open(o + '/' + tbasename(i),'wb').write(f)
                return
        case 'VirtualBox Disk Image':
            td = TmpDir()
            run(['7z','x',i,'-o' + td,'-aoa'])
            if os.path.exists(td + '/1.img'):
                run(['7z','x',td + '/1.img','-o' + o,'-aoa'])
                td.destroy()
                if os.listdir(o): return
            td.destroy()
        case 'RAR':
            cmd = ['unrar','x','-or','-op' + o]
            if i.lower().endswith('-m4ckd0ge_repack.rar'): cmd += ['-pM4CKD0GE']
            run(cmd + [i])
            if os.listdir(o): return
            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o): return
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
            if os.listdir(o): return
        case 'ACE':
            db.get('acefile')
            if db.print_try: print('Trying with acefile')
            from bin.acefile import open as aceopen # type: ignore

            try:
                with aceopen(i) as f: f.extractall(path=o)
            except: pass
            else: return
        case 'AIN':
            if db.print_try: print('Trying with ain')
            p = subprocess.Popen([db.get('msdos'),'-sc',db.get('ain'),'x',i],cwd=o,stdin=-1)

            for t,v in ((2,b'\n'),(1,b'AIN\n'),(1,b'q')):
                if p.poll() != None: break
                sleep(t)
                try: p.stdin.write(v)
                except: pass

            for _ in range(25):
                if os.listdir(o): break
                sleep(0.1)
            else: p.kill()
            while p.poll() == None: sleep(0.05)
            try:del p
            except:pass

            if os.listdir(o): return
        case 'HA': return msdos(['ha','xqy',i],cwd=o)
        case 'AKT': return msdos(['akt','x',i],cwd=o)
        case 'AMGC': return msdos(['amgc','x',i],cwd=o)
        case 'CPC IMG':
            if db.print_try: print('Trying with amstradcpcexplorer')
            run([sys.executable,db.get('amstradcpcexplorer'),i,'-dir','-ex'],print_try=False,cwd=o)
            if os.listdir(o): return
        case '2MG'|'Apple DOS IMG':
            td = 'tmp' + os.urandom(8).hex()
            run(['cadius','EXTRACTVOLUME',i,td])
            if os.listdir(td):
                copydir(td,o,True)
                for f in rldir(o):
                    if f.endswith('\\_FileInformation.txt'): remove(f)
                    else: rename(f,f[:-7])
                return
            remove(td)

            if db.print_try: print('Trying with acx')
            run(['java','-jar',db.get('acx'),'x','--suggested','-d',i,'-o',o],print_try=False)
            if os.listdir(o): return
        case 'AR':
            run(['ar','x',i],cwd=o)
            if os.listdir(o): return
        case 'ARQ': return msdos(['arq','-x',i,'*',o])
        case 'XX34': return msdos(['xx34','D',i],tmpi=True,cwd=o)
        case 'UHARC':
            dosbox(['uharcd','x',i])
            if os.listdir(o): return
        case 'Stirling Compressed'|'The Compressor'|'CP Shrink'|'DIET'|'Acorn Spark'|'Aldus LZW'|'Aldus Zip'|'ARX':
            od = rldir(o)
            run(["deark","-od",o,'-a',i])
            for x in rldir(o):
                if x in od: continue
                xb = basename(x)
                if xb.startswith('output.') and len(xb.split('.')) > 2 and len(xb.split('.')[1]) in (3,4,5) and xb.split('.')[1].isdigit(): move(x,dirname(x) + '\\' + xb.split('.',2)[2])
            if os.listdir(o): return
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
            if os.listdir(o): return
        case 'YAC': return msdos(['yac','x',i],cwd=o)
        case 'Yamazaki Zipper':
            run(['yzdec','-d' + o,'-y',i])
            if os.listdir(o): return
        case '777'|'BIX'|'UFA':
            # merge 7z predecessors
            run([t.lower(),'x','-y','-o' + o,i])
            if os.listdir(o): return
        case 'Brotli':
            of = o + '/' + tbasename(i)
            run(['brotli','-d','-o',of,i])
            if exists(of) and os.path.getsize(of): return fix_tar(o)
        case 'BZip3':
            tf = o + '/' + basename(i)
            symlink(i,tf)
            run(['bzip3','-d','-f','-k',tf])
            remove(tf)
            if os.listdir(o): return fix_tar(o)
        case 'Turbo Range Coder':
            of = o + '/' + tbasename(i)
            run(['turborc','-d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'ACB':
            dosbox(['acb','r',i])
            if os.listdir(o): return
        case 'ALZip'|'EGG':
            run(['alzipcon','-x','-oa',i,o])
            if os.listdir(o): return
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
            if os.listdir(o): return
        case 'BlakHole':
            run(['izarccl','-e','-o','-p' + o,i])
            if os.listdir(o): return
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
            if os.listdir(o): return
        case 'DAR':
            run(['dar','-x','/cygdrive/' + i.replace('\\','/').replace(':',''),'-q','-qcrypto','-R','/cygdrive/' + o.replace('\\','/').replace(':','')])
            if os.listdir(o): return
        case 'DietDisk':
            ins = os.path.getsize(i)
            copy(i,o + '/TMP.EXT')
            dosbox(['fatten','O:\\TMP.EXT'],custs=dirname(db.get('dietdisk')) + '\\FATTEN.EXE',tmpi=False,xcmds=['-c','C:','-c','DIETDISK.COM','-c','O:'])
            if os.path.getsize(o + '/TMP.EXT') != ins:
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
        case 'Rob Northen Compression'|'Amiga XPK'|'File Imploder'|'Compact':
            of = o + '/' + tbasename(i)
            run(['ancient','decompress',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'ABE': return msdos(['dabe','-v','+i',i],cwd=o)
        case 'CarComp': return msdos(['car','x',i],cwd=o)
        case 'PeaZip':
            td = o + '\\tmp' + os.urandom(4).hex()
            run(['pea','UNPEA',i,td,'RESETDATE','SETATTR','EXTRACT2DIR','HIDDEN'])
            if exists(td):
                if os.listdir(td):
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
        case 'AppleSingle':
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
        case 'Compaq QRST IMG':
            tf = TmpFile('.img',path=o)
            run(['dskconv','-otype','raw',i,tf])
            r = extract1(tf.p,o,'IMG')
            tf.destroy()
            return r

    return 1
