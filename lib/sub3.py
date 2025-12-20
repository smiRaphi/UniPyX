from .main import *

def extract3(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def quickbms(scr,inf=i,oup=o):
        if db.print_try: print('Trying with',scr)
        run(['quickbms','-Y',db.get(scr),inf,oup],print_try=False)
        if os.listdir(oup): return
        return 1
    def jsbeautifier(scr,inf=i,oup=o):
        t = scr
        scr = 'jsbeautifier_' + scr

        jfp = db.get(scr)
        jf = open(jfp).read()
        if 'from jsbeautifier.unpackers import UnpackingError' in jf: open(jfp,'w').write(jf.replace('from jsbeautifier.unpackers import UnpackingError','class UnpackingError(Exception): pass'))

        if db.print_try: print('Trying with',scr)
        jsm = getattr(__import__(f'bin.{scr}'),scr)
        if t == 'myobfuscate': jsm.CAVEAT = ''
        elif t == 'jsobfuscator':
            jsm._smartsplit = jsm.smartsplit
            jsm.smartsplit = lambda x: [ast.literal_eval('"' + x.replace('"','\\"') + '"') for x in jsm._smartsplit(x)]

        d = open(i,encoding='utf-8').read()
        jsm.detect(d)
        try: d = jsm.unpack(d)
        except Exception as e:
            if e.__class__.__name__ == 'UnpackingError': return 1
            else: raise

        if t == 'packer':
            sds = sorted([0,len(d)] + list(set(sum([[x.start(),x.end()] for x in re.finditer(r'((?<!\\)\'.*?\'|(?<!\\)\".*?\"|(?<!\w)/.*?/)',d)],[]))))
            sd = []
            for ix in range(len(sds)-1): sd.append(d[sds[ix]:sds[ix+1]])

            for ix in range(len(sd)):
                if ix % 2: continue
                for rg,rp in (
                    (r';',r';\n'),
                    (r',',r', '),
                    (r'([\{\}])',r'\n\1\n'),
                    (r'\n+(;)?\n+',r'\1\n'),
                    (r'\n{\n\}\n',r' {}\n'),
                    (r'(?<=\w)=\n\{\n',r' = {\n' + '\0'),
                    (r'(?<=, )\n\{\n',r'{\n' + '\0'),
                    (r'}\n\)\n',r'})\n'),
                    (r'(?:^|(?<=[\w\)\]]))([\?\:<>=&^\|\*\+\-~%]|&&|\|\||[=!]==|(?:[\+\-&\|\^~\*/%<>!=]|<<|>>)=)(?:$|(?=[\w\(\[!]))',r' \1 '),
                    (r'(?s)for(\([^;]*;)\n([^;]*;)\n(\))',r'for \1 \2\3 '),
                    (r'(?s)for(\([^;]*;)\n([^;]*;)\n([^;]*?\))',r'for \1 \2 \3 '),
                    (r'if(\([^;]*?\))',r'if \1 '),
                    (r'return(!|$)',r'return \1'),
                ): sd[ix] = re.sub(rg,rp,sd[ix])
            d = ''.join(sd).split('\n')

            tabs = 0
            old = -1
            add = ''
            for ix in range(len(d)):
                if d[ix] and d[ix][0] == '\x00':
                    d[ix] = d[ix][1:]
                    tabs += 1
                if '{' in d[ix]: tabs += 1
                if '}' in d[ix]: tabs -= 1
                if old != tabs:
                    add = "\t"*tabs
                    old = tabs
                d[ix] = add[1 if d[ix] == '{' else 0:] + d[ix].rstrip(' \t')
            d = '\n'.join(d)

        open(o + '/' + tbasename(i) + '.js','w',encoding='utf-8').write(d)
        if d: return
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
             '-c','MOUNT I "' + dirname(inf) + '"','-c','MOUNT C "' + dirname(custs or s) + '"','-c','MOUNT O "' + oup + '"','-c','O:'] + xcmds + [
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
    def vamos(cmd:list,inf=i,oup=o):
        raise NotImplementedError
        if db.print_try: print('Trying with',cmd[0])

        db.get('vamos')
        import importlib,importlib.util
        class RedSpec:
            @classmethod
            def find_spec(cls,fullname,path,target=None):
                rename = None
                if fullname.startswith('amitools.vamos') or fullname == 'amitools': rename = fullname
                elif fullname == 'machine68k': rename = 'amitools.machine68k'
                if rename:
                    rename = 'bin.' + rename
                    spec = importlib.util.find_spec(rename)
                    spec.name = fullname
                    spec.fake = rename
                    spec.loader = cls
                    return spec
            @staticmethod
            def create_module(spec):return importlib.import_module(spec.fake) if hasattr(spec,'fake') else None
            @staticmethod
            def exec_module(spec):pass
        sys.meta_path.append(RedSpec)

        import warnings
        warnings.filterwarnings('ignore',category=RuntimeWarning)

        remove(TMP + '/.vamosVols')
        from bin.amitools.vamos import main # type: ignore
        scr = db.get(cmd[0])
        ncmd = [x.replace(oup.replace('\\','/'),'Output:').replace(dirname(inf).replace('\\','/'),'Input:').replace('\\','/') for x in cmd[1:]]
        main.main(args=['System:c/' + basename(scr)] + ncmd,cfg_dict={
        'path':{
            'vols_base_dir':TMP + '/.vamosVols'
        },'machine':{
            'cpu':'68020',
            'ram_size':8192
        },'volumes':[
            "System:" + dirname(dirname(scr)),
            "Input:" + dirname(inf),
            "Output:" + oup
        ],'iffparse':{'library':{'mode':'amiga'}},
          'locale'  :{'library':{'mode':'amiga'}}})
        remove(TMP + '/.vamosVols')

    match t:
        case 'Qt IFW':
            run(['qtifw-devtool','dump',i,o])
            if os.listdir(o): return
        case 'MSCAB SFX':
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o) and not exists(o + '/.rsrc'): return
            remove(o)
            mkdir(o)

            env = os.environ.copy()
            env['__COMPAT_LAYER'] = 'RUNASINVOKER'

            if db.print_try: print('Trying with input (/X)')
            prc = subprocess.Popen([i,'/X:' + o,'/Q','/C'],stdout=-1,stderr=-1,env=env)
            for _ in range(20):
                if prc.poll() != None:
                    for _ in range(50):
                        if os.listdir(o): return
                        sleep(0.1)
                    break
                sleep(0.1)
            else: prc.kill()

            if db.print_try: print('Trying with input (/T)')
            prc = subprocess.Popen([i,'/T:' + o,'/Q'],stdout=-1,stderr=-1,env=env)
            for _ in range(10):
                if prc.poll() != None:
                    for _ in range(50):
                        if os.listdir(o): return
                        sleep(0.1)
                    break
                sleep(0.1)
            else: prc.kill()

            if db.print_try: print('Trying with input (-extract)')
            prc = subprocess.Popen([i,'-silent','-extract'],stdout=-1,stderr=-1,env=env,cwd=o)
            for _ in range(10):
                if prc.poll() != None:
                    for _ in range(50):
                        if os.listdir(o):
                            for f in os.listdir(o):
                                if f.endswith('.msi'): extract(o + '/' + f,o,'MSI')
                            return
                        sleep(0.1)
                    break
                sleep(0.1)
            else: prc.kill()
        case 'NSIS Installer':
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o): return

            if quickbms('instexpl'):
                tm = []
                for x in os.listdir(o):
                    if isfile(o + '/' + x): tm.append(o + '/' + x)
                if tm:
                    mkdir(o + '/$INSFILES')
                    for x in tm: mv(x,o + '/$INSFILES')
                if exists(o + '/$INSTDIR'): copydir(o + '/$INSTDIR',o,True)
                return
        case 'Wise Installer':
            run(['e_wise',i,o])
            if os.path.exists(o + '/00000000.BAT'):
                osj = OSJump()
                osj.jump(o)
                e,_,r = run(['00000000.BAT'],getexe=False)
                osj.back()
                if e: print('BAT returned',e,r)
                else: remove(o + '/00000000.BAT')
                return
            if os.listdir(o): raise NotImplementedError('Unhandled Wise Installer output')
        case 'Inno Installer':
            f = open(i,'rb')
            f.seek(-0x1C76,2)
            gog = f.read(15) == b'00#GOGCRCSTRING'
            f.close()

            if not gog:
                _,e,_ = run(['innounp-2','-o','-q',i],print_try=False)
                e = e.replace('\r','').replace(' ','').replace('\t','')
                if 'Encrytedfiles:' in e and not 'Encrytedfiles:0\n' in e:
                    _,e,_ = run(['innoextract','--crack','-q',i])
                    e = e.replace('\r','').lstrip().rstrip('\n')
                    if not e.startswith('Password found:'): return 1
                    pwd = ['-p' + e.split(': ',1)[1]]
                else: pwd = []

                run(['innounp-2','-x','-b','-m','-d' + o,'-u','-h','-o','-y'] + pwd + [i])
                if not os.listdir(o): run(['innounp','-x','-m','-d' + o,'-y'] + pwd + [i])
                for x in os.listdir(o):
                    if x != '{app}':
                        try: mv(o + '/' + x,o + '/$INSFILES/')
                        except PermissionError: copy(o + '/' + x,o + '/$INSFILES/')
                if exists(o + '/{app}'):
                    while True:
                        try:copydir(o + '/{app}',o,True)
                        except:pass
                        else:break
                    fix_innoinstext(o,i)
                    return
                if fix_innoinstext(o,i): return
            else: pwd = []

            if pwd: pwd = ['-P',pwd[2:]]
            run(['innoextract','-e','-q','--iss-file','-g'] + pwd + ['-d',o,i])
            if os.listdir(o):
                for x in os.listdir(o):
                    if x != 'app': mv(o + '/' + x,o + '/$INSFILES/' + x)
                if exists(o + '/app'): copydir(o + '/app',o,True)
                return
        case 'VISE Installer'|'Inno Archive': return quickbms('instexpl')
        case 'MSI':
            run(['lessmsi','x',i,o + '\\'])
            if exists(o + '/SourceDir') and os.listdir(o + '/SourceDir'):
                for _ in range(10):
                    try:copydir(o + '/SourceDir',o,True)
                    except PermissionError:pass
                    except shutil.Error:pass
                    else:break
                return

            td = TmpDir()
            run(['msiexec','/a',i,'/qn','/norestart','TARGETDIR=' + td],getexe=False)
            copydir(td,o)
            td.destroy()
            if os.listdir(o): return
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o): return
        case 'MSP':
            run(['msix',i,'/out',o,'/ext'])
            if os.listdir(o): return
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o): return
        case 'Setup Factory Installer':
            if not quickbms('totalobserver'):
                if os.listdir(o + '/%AppDir%'):
                    for x in os.listdir(o):
                        if isfile(o + '/' + x): remove(o + '/' + x)
                    copydir(o + '/%AppDir%',o,True)
                if exists(o + '/%SysDir%'): mv(o + '/%SysDir%',o + '/$SYS')
                return
            quickbms('instexpl')
        case 'InstallShield Setup':
            f = open(i,'rb')
            f.seek(943)
            if f.read(42) == b'InstallShield Self-Extracting Stub Program':
                if db.print_try: print('Trying with custom extractor')
                ofs = []
                while True:
                    x = f.read(1)
                    if not x: break
                    if x == b'\x50':
                        if f.read(3) == b'\x4B\3\4':
                            of = open(o + f'\\FILE{len(ofs)+1}.zip','wb')
                            of.write(b'PK\3\4')
                            of.write(f.read(14))
                            cs = f.read(4)
                            of.write(cs)
                            cs = int.from_bytes(cs,'little')
                            of.write(f.read(4))
                            fnl = f.read(2)
                            of.write(fnl)
                            fnl = int.from_bytes(fnl,'little')
                            of.write(f.read(2))
                            fn = f.read(fnl)
                            of.write(fn)
                            ofs.append((of.name,fn.decode()))
                            of.write(f.read(cs))

                            chhd = f.read(4)
                            assert chhd == b'PK\1\2'
                            of.write(chhd)
                            of.write(f.read(42+fnl))

                            chhd = f.read(4)
                            assert chhd == b'PK\5\6'
                            of.write(chhd)
                            of.write(f.read(12))
                            of.write((int.from_bytes(f.read(4),'little')).to_bytes(4,'little'))
                            of.write(b'\0\0')
                            of.close()
                        else: f.seek(-3,1)
                f.close()
                if ofs:
                    import zipfile
                    for x in ofs:
                        with zipfile.ZipFile(x[0]) as z: xopen(o + '/' + x[1],'wb').write(z.read(x[1]))
                        remove(x[0])
                    if os.path.exists(o + '/_INST32I.EX_') or os.path.exists(o + '/_inst16.ex_'):
                        if fix_isinstext(o): return
                    else: return
            else: f.close()

            run(['isx',i,o])
            if exists(o + '/' + tbasename(i) + '_sfx.exe'): remove(o + '/' + tbasename(i) + '_sfx.exe')
            if exists(o + '/' + tbasename(i) + '_ext.bin'):
                remove(o)
                mkdir(o)
            elif os.listdir(o):
                if exists(o + '/Disk1/setup.exe'):
                    if fix_isinstext(o,o + '\\Disk1'): return
                return

            td = TmpDir()
            tf = td + '\\' + basename(i)
            symlink(i,tf)
            osj = OSJump()
            osj.jump(td)
            _,po,_ = run(['isxunpack',tf],'\n')
            remove(tf)
            osj.back()
            if 'All Files are Successfuly Extracted!' in po and len(os.listdir(td.p)) == 1:
                copydir(td + '/' + os.listdir(td.p)[0],o,True)
                if os.path.exists(o + '/_inst32i.ex_'):
                    if fix_isinstext(o): return
                else: return

            quickbms('instexpl')
            fs = os.listdir(o)
            if fs == ['install.exe','uninst.exe'] and (os.path.getsize(o + '/install.exe') + os.path.getsize(o + '/uninst.exe')) == 0:
                remove(o + '/install.exe',o + '/uninst.exe')
                fs = []
            if fs:
                if not 'SETUP.EXE' in fs and not 'Setup.ini' in fs and not 'MSIEng.isc' in fs: return
                if 'MSIEng.isc' in fs:
                    ret = False
                    for x in fs:
                        if not x.lower().endswith('.msi'): continue
                        r = extract(o + '/' + x,o + '/' + noext(x),'MSI')
                        if x[0] != '{' and not '}.' in x: ret = ret or r
                    if not ret: return
                elif fix_isinstext(o): return
        case 'InstallShield Z':
            td = TmpDir()
            osj = OSJump()
            osj.jump(td)
            symlink(i,'archive.z')
            run(['icomp','archive.z','*.*','-d','-i'],timeout=2)
            remove('archive.z')
            osj.back()
            if not os.listdir(td.p): td.destroy()
            else:
                copydir(td.p,o)
                td.destroy()
                return
        case 'InstallShield Archive':
            td = TmpDir()
            osj = OSJump()
            osj.jump(td)
            e,_,_ = run(['i6comp','x','-rof',i])
            osj.back()
            if not e and os.listdir(td.p):
                copydir(td,o)
                td.destroy()
                return
            td.destroy()

            td = TmpDir()
            osj = OSJump()
            osj.jump(td)
            e,_,_ = run(['i5comp','x','-rof',i])
            osj.back()
            if not e and os.listdir(td.p):
                copydir(td,o)
                td.destroy()
                return
            td.destroy()

            bk = os.environ.get('__COMPAT_LAYER')
            os.environ['__COMPAT_LAYER'] = 'RUNASINVOKER'
            ti = TmpFile('.ini')
            e,_,_ = run(['iscab',i,'-i"' + ti + '"','-lx'])
            if bk != None: os.environ['__COMPAT_LAYER'] = bk
            else: del os.environ['__COMPAT_LAYER']
            if not e:
                print('INI:\n' + xopen(ti).read())
                ti.destroy()
                raise NotImplementedError("iscab returned:\n" + e)
            ti.destroy()
        case 'FreeArc':
            run(['unarc','x','-o+','-dp' + o,i])
            if os.listdir(o): return
        case 'Big EXE':
            ts = os.path.getsize(i)
            f = open(i,'rb')
            f.seek(64)
            c = 0
            while True:
                b = f.read(16)
                if not b: break
                if b == b'\x4D\x5A\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00':
                    sp = f.tell()-16
                    f.seek(48 + 24 + 56,1)
                    siz = int.from_bytes(f.read(4),'little')
                    f.seek(sp)
                    open(o + f'/{c}.exe','wb').write(f.read(siz))
                    f.seek(-f.tell() % 16,1)
                    if f.tell() >= ts: f.seek(sp + 64)
                    c += 1
            if c:
                for ix in range(c):
                    try: xr = main_extract(o + f'/{ix}.exe',o + f'/{ix}')
                    except AssertionError: xr = False
                    if exists(o + f'/{ix}') and not os.listdir(o + f'/{ix}'): remove(o + f'/{ix}')
                    elif xr: remove(o + f'/{ix}.exe')
                return
        case 'Resource DLL':
            run(['7z','x',i,'-o' + o,'-aou'])
            if exists(o + '/.rsrc'):
                copydir(o + '/.rsrc',o,True)
                return
        case 'Netopsystems FEAD':
            bk = os.environ.get('__COMPAT_LAYER')
            os.environ['__COMPAT_LAYER'] = 'RUNASINVOKER'
            if db.print_try: print('Trying with input (/nos_ne)')
            run([i,'/s','/nos_ne','/nos_o' + o],print_try=False)
            if bk != None: os.environ['__COMPAT_LAYER'] = bk
            else: del os.environ['__COMPAT_LAYER']
            if os.listdir(o): return
        case 'Advanced Installer':
            if db.print_try: print('Trying with input (/extract)')
            td = TmpDir()

            p = subprocess.Popen([i,'/extract',td.p],stdout=-1,stderr=-1)
            for _ in range(25):
                if p.poll() != None: break
                sleep(0.1)
            else: p.kill()

            if os.listdir(td.p):
                bp = td.p + '\\' + os.listdir(td.p)[0]
                for f in os.listdir(bp):
                    if not f.endswith('.msi') or extract(bp + '\\' + f,o,'MSI'): mv(bp + '\\' + f,o + '\\$INSFILES\\' + f)
                td.destroy()
                if os.listdir(o): return
        case 'CExe':
            err,e,_ = run(['resourceextractor','list',i])
            if err: return 1
            for x in e.strip().replace('\r','').split('\n'):
                if x.split('/')[0] == '99':
                    tf = TmpFile()
                    run(['resourceextractor','extract',i,x.split()[0],tf.p],print_try=False)
                    ar,_ = analyze(tf.p,True)

                    td = TmpDir()
                    if ('SZDD' in ar and not extract(tf.p,td.p,'SZDD')) or ('ZLIB' in ar and not extract(tf.p,td.p,'ZLIB')):
                        otf = td.p + '\\' + os.listdir(td.p)[0]
                        if open(otf,'rb').read(8) == b'MZ\x90\0\3\0\0\0': mv(otf,o + '/' + x.split('/')[1] + '.exe')
                        else: mv(otf,o + '/' + x.split('/')[1])
                    else: mv(tf.p,o + '/' + x.split('/')[1])
                    tf.destroy()
                    td.destroy()

            for f in os.listdir(o):
                f = o + '\\' + f
                if not f.endswith('.exe') or os.path.getsize(f) < 16384:continue
                main_extract(f,f[:-4])

            if os.listdir(o): return
        case 'PyInstaller':
            run(['pyinstxtractor-ng',i],cwd=o)
            if exists(o + '/' + basename(i) + '_extracted'):
                copydir(o + '/' + basename(i) + '_extracted',o,True)
                return
        case 'Steam DRM':
            tf = o + '\\' + basename(i)
            symlink(i,tf)
            run(['steamless','--quiet','--dumppayload','--dumpdrmp','--realign','--recalcchecksum','--exp',tf])
            remove(tf)
            if exists(tf + '.unpacked.exe'):
                rename(tf + '.unpacked.exe',tf)
                return
        case 'Denuvo': raise NotImplementedError
        case 'Crinkler': raise NotImplementedError
        case 'com2txt':
            dosbox(['com2txt','-r',i,'OUT.COM'])
            if exists(o + '/OUT.COM'):
                mv(o + '/OUT.COM',o + '/' + tbasename(i) + ('.com' if i[-3:].islower() else '.COM'))
                return
        case 'bytepress':
            run(['bytepressdecompressor',i],stdin='No\n\n',cwd=o)
            of = o + '/' + tbasename(i) + '-decompressed.exe'
            if exists(of):
                mv(of,o + '/' + basename(i))
                return
        case 'Bat2Exe':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            f = File(i,endian='<')
            f.seek(0x178)
            assert f.read(8) == b'.text\0\0\0'
            f.skip(8)
            s,of = f.readu32(),f.readu32()
            eo = of + s - 8

            f.seek(of + 8)
            tmpl = 0
            src = b'@echo off && title '
            while f.tell() < eo:
                t = f.readu16()
                if t == src[tmpl]:
                    tmpl += 1
                    if tmpl == len(src): break
                else: tmpl = 0
            else: assert tmpl == len(src)

            f.skip(-39)
            sl = f.readu8()
            f.skip(38)
            fn = f.read(sl-38)[:-1].decode('utf-16le')
            fn += f.read(f.readu8())[:-1].decode('utf-16le')

            assert f.readu8() == 0x7D
            f.skip(0x7D)

            bs = f.readu8()
            if   bs & (0b100 << 5) == (0b000 << 5): bs =  bs & 0x7F
            elif bs & (0b110 << 5) == (0b100 << 5): bs = (bs & 0x3F) << 8 | f.readu8()
            elif bs & (0b111 << 5) == (0b110 << 5): bs = (bs & 0x1F) << 24 | (f.readu8() << 16) | (f.readu8() << 8) | f.readu8()
            bs -= 1
            assert bs > 0

            bat = f.read(bs)
            assert f.readu8() in (0,1)
            f.close()

            if len(bat.replace(b'\r',b'')) > 3519 and bat.startswith(b'set '):
                st = re.search(rb'^set [a-z]{10}=s\r?\n%[a-z]{10}%et [a-z]{10}=e\r?\n%[a-z]{10}%%[a-z]{10}%t [a-z]{10}=t\r?\n',bat)
                if st:
                    cr = st.end() > 87
                    assert st.end() == (87 + (3 if cr else 0))
                    bat = bat[87 + (3 if cr else 0):]

                    mp = re.findall(rb'(?:%[a-z]{10}%){3} ([a-z]{10})=([a-z])\r?\ngoto [A-Z]{10}\r?\n(?:%[a-z]{10}%){3} [a-z]{10}=[a-z]\r?\n:[A-Z]{10}\r?\n',
                                    bat[:3432 + (104 if cr else 0)])
                    assert len(mp) == 26
                    bat = bat[3432 + (104 if cr else 0):]
                    for x in mp:
                        bat = bat.replace(b'%' + x[0] + b'%',x[1])
                        if bat.strip().endswith(b'%' + x[0]): bat = bat.replace(b'%' + x[0],x[1])
            else:
                sub10 = re.compile(rb'%[a-z]{10}%')

                nrp = [sub10.sub(b'',x) for x in re.findall(rb'(%[a-z]{10}%|^)?[sS]%[a-z]{10}%[eE]%a[a-z]{10}%[tT]%[a-z]{10}%(?:[ \t]%[a-z]{10}%){1,} ((?:[a-z]%[a-z]{10}%){10})[ \t=][a-z]{10}',bat)] # find all real variables with a length of 10
                bat = sub10.sub(lambda m: m[0] if m[0] in nrp else b'',bat)
            open(o + '/' + fn,'wb').write(bat)

            return
        case '624'|'4kZIP'|'Amisetup'|'aPACK'|'AVPACK'|'COM RLE Packer'|'Cruncher'|'DexEXE'|'Dn.COM Cruncher'|'Envelope'|'ExeLITE'|'JAM'|'LGLZ'|'Pack Packed'|\
             'PMWLite'|'RDT Compressor'|'RJCrush'|'Shrinker Packed'|'SpaceMaker'|'T-PACK'|'Tenth Planet Soft'|'TSCRUNCH'|'XPACK/LZCOM':
            dosbox(['cup386',i,'OUT.BIN','/1h' + ('x' if open(i,'rb').read(2) == b'MZ' else '')])
            chks = os.path.getsize(i)-768
            if chks < 0x10: chks = 0x10
            if exists(o + '/OUT.BIN') and os.path.getsize(o + '/OUT.BIN') >= chks:
                on = basename(i)
                if on.lower().endswith('.exe') and open(o + '/OUT.BIN','rb').read(2) != b'MZ': on = on[:-3] + ('com' if on.endswith('.exe') else 'COM')
                elif on.lower().endswith('.com') and open(o + '/OUT.BIN','rb').read(2) == b'MZ': on = on[:-3] + ('exe' if on.endswith('.com') else 'EXE')
                mv(o + '/OUT.BIN',o + '/' + on)
                return
        case 'COMPACK'|'Compress-EXE'|'ICE'|'Optlink'|'PGMPAK'|'TinyProg':
            dosbox(['unp','e',i,'OUT.BIN'])
            chks = os.path.getsize(i)-768
            if chks < 0x10: chks = 0x10
            if exists(o + '/OUT.BIN') and os.path.getsize(o + '/OUT.BIN') >= chks:
                on = basename(i)
                if on.lower().endswith('.exe') and open(o + '/OUT.BIN','rb').read(2) != b'MZ': on = on[:-3] + ('com' if on.endswith('.exe') else 'COM')
                elif on.lower().endswith('.com') and open(o + '/OUT.BIN','rb').read(2) == b'MZ': on = on[:-3] + ('exe' if on.endswith('.com') else 'EXE')
                mv(o + '/OUT.BIN',o + '/' + on)
                return
        case 'AXE'|'CEBE'|'Cheat Packer'|'Diet Packed'|'EXECUTRIX-COMPRESSOR'|'LM-T2E'|'Neobook Executable'|'PACKWIN'|'Pro-Pack'|'SCRNCH'|'UCEXE'|'WWPACK'|\
             'PKTINY':
            r = extract(i,o,'624')
            if not r: return r
            remove(o)
            mkdir(i)

            r = extract(i,o,'COMPACK')
            if not r: return r
        case 'PKLITE'|'LZEXE'|'EXEPACK':
            od = rldir(o)
            run(["deark","-opt","execomp","-od",o,i])
            for x in rldir(o):
                if not x in od:
                    mv(x,o + '/' + basename(i))
                    return
        case 'Godot Game'|'Godot Pack':
            run(['gdre_tools','--headless','--extract=' + i,'--output=' + o,'--ignore-checksum-errors'])
            if exists(o): remove(o + '/gdre_export.log')
            if os.listdir(o): return
        case 'IRIX IDB':
            if db.print_try: print('Trying with custom extractor')

            cps = {}
            pr7z = db.print_try
            lerr = False
            errp = ''
            for x in open(i,encoding='utf-8').read().strip().split('\n'):
                x = x.strip() + ' '
                t,x = x.split(' ',1)
                assert t in 'fdl',t
                t = t
                mode,x = x.split(' ',1)
                mode = int(mode,8)
                user,x = x.split(' ',1)
                group,x = x.split(' ',1)
                path,x = x.split(' ',1)
                if errp:
                    if errp != path: continue
                    else: errp = ''
                path2,x = x.split(' ',1)

                od,x = x.split(' ',1)
                d = od
                for _ in range(2):
                    if exists(dirname(i) + '/' + d): d = dirname(i) + '/' + d;break
                    elif exists(d): d = abspath(d);break
                    else: d = noext(d)
                else:
                    x = od + ' ' + x
                    if exists(noext(i) + '.dev'): d = noext(i) + '.dev'
                    elif exists(noext(i) + '.sw'): d = noext(i) + '.sw'
                    elif exists(noext(i) + '.sw64'): d = noext(i) + '.sw64'
                    else: raise FileNotFoundError(od)
                if not d in cps:
                    cps[d] = open(d,'rb')
                    cps[d].seek(13)
                d = cps[d]

                ne = {}
                while x.strip():
                    xv,x = x.split(' ',1)
                    if '(' in xv:
                        xn,xv = xv.split('(',1)
                        xv,x = (xv + ' ' + x).split(') ',1)
                    else: xn,xv = xv,True
                    if xn in ('sum','size','cmpsize','f'): xv = int(xv)
                    ne[xn] = xv
                if t == 'f':
                    fpos = ffpos = d.tell()
                    p1 = d.read(int.from_bytes(d.read(2),'big')).decode(errors='ignore')
                    lerr = lerr or p1.strip() != path.strip()
                    if lerr:
                        while p1.strip() != path.strip():
                            fpos += 1
                            d.seek(fpos)
                            p1 = d.read(int.from_bytes(d.read(2),'big')).decode(errors='ignore')
                            if not p1: break
                        else:
                            print('Recovered to',p1)
                            lerr = False
                        if lerr:
                            fpos = ffpos - 1
                            while p1.strip() != lpath.strip():
                                fpos += 1
                                d.seek(fpos)
                                p1 = d.read(int.from_bytes(d.read(2),'big')).decode(errors='ignore')
                                if not p1: break
                            else:
                                print('Recovered to',p1)
                                lerr = False
                        if lerr:
                            fpos = ffpos - 1
                            lng = 0
                            while True:
                                fpos += 1
                                d.seek(fpos)
                                lng = int.from_bytes(d.read(2),'big')
                                if lng <= 8 or lng > 0xFF: continue
                                try: p1 = d.read(lng).decode()
                                except: continue
                                if not p1: raise EOFError
                                if '\r' in p1.strip() or '\n' in p1.strip() or ' ' in p1 or '\t' in p1 or '\\' in p1 or '"' in p1 or "'" in p1 or '?' in p1 or '*' in p1: continue
                                if '/' in p1 and p1.startswith(path.split('/')[0] + '/'): break
                            lerr = False
                            d.seek(-(len(p1) + 2),1)

                            errp = p1.strip()
                            print('Recovered to',errp)

                            continue

                    fpos = d.tell()
                    p2 = d.read(int.from_bytes(d.read(2),'big'))
                    try: p2 = p2.decode()
                    except: d.seek(fpos)
                    else:
                        if p2.strip() != path2.strip(): d.seek(fpos)
                    rs = ne['cmpsize'] if ne.get('cmpsize',0) > 0 else ne['size']
                    dat = d.read(rs)
                    assert len(dat) == rs,d.name

                    if ne.get('cmpsize',0) > 0:
                        assert dat[:2] == b'\x1F\x9D'
                        tf = TmpFile('.z')
                        open(tf.p,'wb').write(dat)
                        _,dat,err = run(['7z','e','-so','-tZ',tf],text=False,print_try=pr7z)
                        if pr7z: pr7z = False
                        tf.destroy()

                        if len(dat) != ne['size']:
                            print(err.decode().strip(),path,f'[{d.name}@{d.tell():2X}]')
                            lerr = pr7z = True

                    xopen(o + '/' + path,'wb').write(dat)
                    try: xopen(o + '/' + path2,'wb').write(dat)
                    except FileExistsError as e:
                        op = e.filename
                        while os.path.lexists(op): op = e.filename + f'${c}';c += 1
                        xopen((o + '/' + path2).replace('/','\\').replace(e.filename,op,1),'wb').write(dat)
                    lpath = path
                elif t == 'd':
                    mkdir(o + '/' + path)
                    mkdir(o + '/' + path2)
                elif t == 'l':
                    mkdir(dirname(o + '/' + path))
                    mkdir(dirname(o + '/' + path2))
                    sym = ne['symval']
                    if sym.startswith('../'): sym = (path.split('/')[0] if '/' in path else '') + sym[2:]
                    sym = o + '/' + sym

                    op = o + '/' + path
                    c = 0
                    while os.path.lexists(op): op = o + '/' + path + f'${c}';c += 1
                    symlink(sym,op)

                    op = o + '/' + path2
                    if exists(op):
                        if os.path.realpath(op) == os.path.realpath(sym): continue
                        c = 0
                        while os.path.lexists(op): op = o + '/' + path2 + f'${c}';c += 1
                    symlink(sym,op)
            for f in cps: cps[f].close()
            if cps: return
        case 'Compressed Nintendo Switch Executable':
            of = o + '/' + tbasename(i) + '.nso'
            run(['nsnsotool',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'GameCube DOLXZ'|'Wii DOLXZ':
            if db.print_try: print('Trying with custom extractor')
            import lzma

            f = open(i,'rb')
            f.seek(0x20)
            off = int.from_bytes(f.read(4),'big')
            f.seek(0x124)
            siz = int.from_bytes(f.read(4),'big')
            f.seek(off)
            open(o + '/' + basename(i),'wb').write(lzma.decompress(f.read(siz)))
            f.close()
            return
        case 'DOLPAK':
            ti = o + '/' + tbasename(i) + '.dol'
            tf = o + '/' + tbasename(i) + '.7z'
            symlink(i,ti)
            run(['dolpak',ti])
            remove(ti)
            assert exists(tf)
            extract(tf,o,'7z')
            remove(tf)
            if os.listdir(o): return
        case 'd0lLZ 1'|'d0lLZ 2':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            f.seek(0x1C)
            data0 = f.readu32()
            f.seek(0xAC)
            data0_size = f.readu32()
            f.seek(data0)
            assert f.read(3) == b'DLZ'
            ver = f.readu8()

            of = open(o + '/' + basename(i),'wb')
            if ver == 2:
                def dlz_dec_block():
                    size = f.readu32()
                    assert size > 6
                    epos = f.pos + size
                    f.skip(4)

                    dec = bytearray()
                    while f.pos < epos:
                        flags = f.readu16('<')
                        bitc = 16
                        if (f.pos + bitc) > epos: bitc = epos - f.pos
                        for bit in range(bitc):
                            if (flags >> bit) & 1:
                                tok0,tok1 = f.readu8(),f.readu8()
                                oflags,leng,off = tok0 >> 4,(tok0 & 0x0F)+3,tok1
                                err = f'0b{oflags:04b},{leng},{off} = 0x{tok0:02X}{tok1:02X} @ 0x{f.pos-2:04X}'
                                assert off > 0,err
                                off = len(dec) - off + 1
                                if off < 0:
                                    assert off >= -16,err
                                    dec += bytes(-off)
                                    off = 0
                                for i in range(leng): dec.append(dec[off + i])
                            else: dec.append(f.readu8())
                    of.write(dec)
            while f.pos < (data0 + data0_size): dlz_dec_block()
            return
        case 'd0lLZ 3': raise NotImplementedError
        case 'Xamarin Compressed':
            if db.print_try: print('Trying with custom extractor')
            import lz4.block # type: ignore
            open(o + '/' + basename(i),'wb').write(lz4.block.decompress(open(i,'rb').read()[8:]))
            return
        case 'JS P.A.C.K.E.R.': return jsbeautifier('packer')
        case 'JS MyObfuscate.com': return jsbeautifier('myobfuscate')
        case 'JavaScriptObfuscator': return jsbeautifier('jsobfuscator')
        case 'Javascript Obfuscator.com':
            if db.print_try: print('Trying with custom extractor')
            d = open(i,encoding='utf-8').read()

            def jsstr(i:str) -> str: return ast.literal_eval(i.replace(r'\/','/'))

            dec1n,*vals1 = re.search(r'function ([a-zA-Z]{3})\([a-z]\)\{var [a-z]=(\d+);var [a-z]=[a-z]\.length;var [a-z]=\[\];for\(var [a-z]=0;[a-z]<[a-z];[a-z]\+\+\)\{[a-z]\[[a-z]\]=[a-z]\.charAt\([a-z]\)\};for\(var [a-z]=0;[a-z]<[a-z];[a-z]\+\+\)\{var [a-z]=[a-z]\*\([a-z]\+(\d+)\)\+\([a-z]%(\d+)\);var [a-z]=[a-z]\*\([a-z]\+(\d+)\)\+\([a-z]%(\d+)\);var [a-z]=[a-z]%[a-z];var [a-z]=[a-z]%[a-z];var [a-z]=[a-z]\[[a-z]\];[a-z]\[[a-z]\]=[a-z]\[[a-z]\];[a-z]\[[a-z]\]=[a-z];[a-z]=\([a-z]\+[a-z]\)%(\d+);\}',d).groups()
            vals1 = [int(x) for x in vals1]
            def decjs1(i:str):
                t = vals1[0]
                o = list(i)
                for ix in range(len(i)):
                    a = t * (ix + vals1[1]) + (t % vals1[2])
                    b = t * (ix + vals1[3]) + (t % vals1[4])
                    c = a % len(i)
                    d = b % len(i)
                    o[c],o[d] = o[d],o[c]
                    t = (a + b) % vals1[5]
                return ''.join(o)

            dec1 = decjs1(jsstr(re.search(r';var [a-zA-Z]{3}=(\'.+?\');',d)[1]))

            vals2 = list(re.search(r'var [a-z]=(\d+),[a-z]=(\d+),[a-z]=(\d+);var [a-z]="abcdefghijklmnopqrstuvwxyz";var [a-z]=\[([\d,]+)\];[^;]+;for\([^;]+;[^;]+;[^;]+;var [a-z]=\[\];[a-z]\+=(\d+);[a-z]\+=(\d+);[a-z]\+=(\d+);for\(var [a-z]=0;[a-z]<arguments\.length;[a-z]\+\+\).+?\.join\(""\);var [a-z]=\[([\d,]+)\]',dec1).groups())
            vals2[3] = [int(x) for x in vals2[3].split(',')]
            for ix in range(3): vals2[ix] = int(vals2[ix]) + int(vals2.pop(4))
            vals2[4] = [int(x) for x in vals2[4].split(',')] + vals2[3]
            def decjs2(i:str):
                a = {}
                for ix,x in enumerate(vals2[3]): a[x] = ix + 1

                l = i.split(' ')
                for ix in range(len(l)-1,-1,-1):
                    z = b = 0
                    r = None
                    while b < len(l[ix]):
                        c = ord(l[ix][b])
                        if c in a:
                            u = (a[c] - 1) * vals2[1] + ord(l[ix][b+1]) - vals2[0]
                            v = b
                            b += 1
                        elif c == vals2[2]:
                            u = vals2[1] * (len(vals2[3]) - vals2[0] + ord(l[ix][b+1])) + ord(l[ix][b+2]) - vals2[0]
                            v = b
                            b += 2
                        else:
                            b += 1
                            continue

                        if r is None: r = []
                        if v > z: r.append(l[ix][z:v])
                        r.append(l[u+1])
                        z = b + 1

                        b += 1
                    if r is not None:
                        if z < len(l[ix]): r.append(l[ix][z:])
                        l[ix] = "".join(r)
                o1 = [l[0]]

                o = "".join(o1)
                for ix in range(len(vals2[4])): o = chr(vals2[4][ix]).join(o.split('.' + "abcdefghijklmnopqrstuvwxyz"[ix]))
                return '.'.join(o.split('.!'))

            dec2 = jsstr(re.search(r'\([a-zA-Z]{3}\((\'.+\')\)\);',d)[1])
            dec2 = decjs1(dec2)
            dec2 = decjs2(dec2)

            dec3n,*vals3 = re.search(r'function (_\$af\d{6})\([a-z],jso\$setrpl\$[a-z]\)\{var (?:[a-z]=\{\},){6}[a-z]=\{\};[a-z]\._= ?jso\$setrpl\$[a-z];.+?;[a-z]\+\+\)\{[a-z]\._= ?jso\$ft\$boe\$_\d+\([a-z]\._\* \(jso\$ft\$boe\$_\d+\([a-z],(\d+)\)\),\(jso\$ft\$boe\$_\d+\([a-z]\._,(\d+)\)\)\);;?[a-z]\._= ?jso\$ft\$boe\$_\d+\(n\._\* \(jso\$ft\$boe\$_\d+\([a-z],(\d+)\)\),\(jso\$ft\$boe\$_\d+\([a-z]\._,(\d+)\)\)\);;?.+\([a-z],[a-z],[a-z]\)\{[a-z]\._= ?jso\$ft\$boe\$_\d+\(\(jso\$ft\$boe\$_\d+\([a-z]\._,[a-z]\._\)\),(\d+)\)\}',dec2).groups()
            vals3 = [int(x) for x in vals3]
            def decjs3(i1:str,i2:int):
                t = i2
                o = list(i1)
                for ix in range(len(i1)):
                    a = t * (ix + vals3[0]) + (t % vals3[1])
                    b = t * (ix + vals3[2]) + (t % vals3[3])
                    c = a % len(i1)
                    d = b % len(i1)
                    o[c],o[d] = o[d],o[c]
                    t = (a + b) % vals3[4]
                return '#'.join('%'.join('\x7F'.join(''.join(o).split('%')).split('#1')).split('#0')).split('\x7F')

            dec3 = re.findall(r'var (_\$_[a-f\d]{4})=\(' + re.escape(dec3n) + r'\)\((".+"),(\d+)\);',dec2)
            dec3_1 = {x[0]:decjs3(jsstr(x[1]),int(x[2])) for x in dec3}
            dec3f = dec2.split('function ' + dec3n)[0].split('var ')[0]
            dec = re.split(r'var [a-z]=\'#\';return [a-z]\._(?:\.join\([a-z]\)\.split\([a-z]\)){4}\}',dec2,maxsplit=1)[1]
            dec = re.sub(r'function jso\$spliter_\$af\d{6}\([a-z],[a-z],[a-z]\)\{.+?\}','',dec)
            dec = re.sub(r'if\(!_\$(?:_[a-f\d]{4}|af\d{6})\)\{_\$af\d{6}\([^\)]*\);.*?return\};','',dec)

            dec3_2 = {x[0]:x[1] for x in re.findall(r'function (jso\$ft\$giden\$[^\(]+)\(\)\{return ([^\}]+)\}',dec3f)}
            dec3_3 = {x[0]:x[1] for x in re.findall(r'function (jso\$ft\$[^\(]+)\(a,b\)\{return a(.) b\}',dec3f)}

            for bs,rp in dec3_1.items():
                for ix in range(len(rp)): dec = dec.replace(f'{bs}[{ix}]',repr(rp[ix]).replace('/',r'\/'))
            for bs,rp in dec3_2.items(): dec = dec.replace(bs,rp)
            for bs,rp in dec3_3.items(): dec = re.sub(rf'{bs}\((.+?),(.+?)\)',fr'\1 {rp} \2',dec)

            if d.startswith('var '): ivar = d.split(';')[0][4:].split(',')
            else: ivar = []

            for var in ivar.copy():
                rg = re.compile(re.escape(var) + r'= ?(_\$af\d{6});')
                rn = rg.search(dec)
                if not rn:continue
                dec = rg.sub('',dec)
                dec = dec.replace(rn[1],var)
                ivar.remove(var)

            for x in re.findall(r'jso\$setrpl\$[a-zA-Z_][a-zA-Z_\$\d_]*',dec):
                rn = x.split('$',2)[2]

                dec = re.sub('var ' + re.escape(rn) + r' ?= ?\{\};','',dec)
                dec = re.sub('var ' + re.escape(rn) + r' ?= ?\{\},',r'var ',dec)
                dec = re.sub(',' + re.escape(rn) + r' ?= ?\{\}([;,])',r'\1',dec)

                dec = re.sub(re.escape(rn) + r'\._ ?= ?' + re.escape(x) + ';','',dec)

                dec = dec.replace(x,rn)

            if ivar: dec = 'var ' + ','.join(ivar) + ';' + dec
            d = dec

            sds = sorted([0,len(d)] + list(set(sum([[x.start(),x.end()] for x in re.finditer(r'((?<!\\)\'.*?\'|(?<!\\)\".*?\"|(?<![\w_\\])/.*?/)',d)],[]))))
            sd = []
            for ix in range(len(sds)-1): sd.append(d[sds[ix]:sds[ix+1]])

            for ix in range(len(sd)):
                if ix % 2: continue
                for rg,rp in (
                    (r'([=<>]) ',r'\1'),
                    (';',r';\n'),
                    (',',', '),
                    (r'([\{\}])',r'\n\1\n'),
                    (r'\n+(;)?\n+',r'\1\n'),
                    (r'\n?{\n\}(;?)\n',r' {}\1\n'),
                    (r'\}\n,',r'},'),
                    (r'(?<=\w)=\n\{\n',r' = {\n' + '\0'),
                    (r'(?<=, )\n\{\n',r'{\n' + '\0'),
                    (r'}\n\)\n',r'})\n'),
                    (r'([=<>]) ',r'\1'),
                    (r'(?:^|(?<=[\w\)\]\}]))([\?\:<>=&^\|\*\+\-~%]|&&|\|\||[=!]==|(?:[\+\-&\|\^~\*/%<>!=]|<<|>>)=)(?:$|(?=[\w\(\[\{!]))',r' \1 '),
                    (r'(?s)for(\([^;]*;)\n([^;]*;)\n(\))',r'for \1 \2\3 '),
                    (r'(?s)for(\([^;]*;)\n([^;]*;)\n([^;]*?\))',r'for \1 \2 \3 '),
                    (r'if(\([^;]*?\))',r'if \1 '),
                    (r'return(!|$)',r'return \1'),
                ): sd[ix] = re.sub(rg,rp,sd[ix])
            d = ''.join(sd).split('\n')

            tabs = 0
            old = -1
            add = ''
            for ix in range(len(d)):
                if d[ix] and d[ix][0] == '\x00':
                    d[ix] = d[ix][1:]
                    tabs += 1
                if '{' in d[ix]: tabs += 1
                if '}' in d[ix]: tabs -= 1
                if old != tabs:
                    add = "\t"*tabs
                    old = tabs
                d[ix] = add[1 if d[ix] == '{' else 0:] + d[ix].rstrip(' \t')
            d = '\n'.join(d)

            open(o + '/' + tbasename(i) + '.js','w',encoding='utf-8').write(d)
            if d: return
        case 'C64 TBC MultiCompactor'|'C64 CruelCrunch'|'C64 Time Cruncher'|'C64 Super Compressor'|'C64 MegaByte Cruncher'|'C64 1001 CardCruncher'|\
             'C64 ECA Compactor':
            tf = o + '\\' + basename(i)
            symlink(i,tf)
            run(['unp64',tf])
            remove(tf)
            if os.listdir(o): return
        case 'VMProtect': raise NotImplementedError
        case 'Encrypted EAC Payload':
            hookshot(['decrypteacpayload','-e',i],{'C:\\EAC_Dumps':o})

            for f in os.listdir(o):
                p = o + '\\' + f
                if f.startswith('Dump_') and isdir(p) and exists(p + '/EAC_Launcher_decrypted.dll'): break
            else: return 1

            remove(p + '/original_eac.bin',p + '/eac_.bin')
            copydir(p,o,True)
            if open(o + '/EAC_Launcher_decrypted.dll','rb').read(4) in (b'MZ\x90\x00',b'\x7FELF'): return
        case 'Chromium Delta Update':
            run(['android-ota-extract',i],cwd=o)
            if os.listdir(o): return
        case 'Excel DNA XLL':
            run(["exceldna-unpack",'--xllFile=' + i,'--outFolder=' + o,'--overwrite'])
            if os.listdir(o): return
        case 'Nuitka Compiled':
            run(['nuitka-extractor',i],cwd=o)
            if os.listdir(o): return
        case 'Python Compiled Module':
            err,r,_ = run(['pycdc',i],text=False)
            assert not err
            open(o + '/' + tbasename(i) + '.py','wb').write(r.split(b'\r\n',3)[3])
            return
        case 'Install Creator Pro':
            run(['cicdec','-db',i,o])
            if os.listdir(o):
                for f in os.listdir(o):
                    if f.startswith('Block 0x') and f.endswith('.bin'):
                        mkdir(o + '/$INSFILES')
                        mv(o + '/' + f,o + '/$INSFILES/' + f.rsplit(None,1)[1].replace('UNINSTALLER.bin','UNINSTALLER.exe'))
                return
        case 'UPX':
            run(['upx','-d','-f','-o',o + '/' + basename(i),i])
            if exists(o + '/' + basename(i)): return
        case 'Z-Code':
            e,r,_ = run(['txd',i],text=False)
            if e: return 1
            open(o + '/' + tbasename(i) + '.asm','wb').write(r)
            return
        case 'Atomik Cruncher':
            of = o + '/' + basename(i)
            vamos(['xfddecrunch',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'Netcrypt':
            if db.print_try: print('Trying with custom extractor')
            import base64
            try: from Cryptodome.Cipher import AES # type: ignore
            except ImportError: from Crypto.Cipher import AES # type: ignore
            from lib.file import EXE

            x = EXE(i)
            x.seek(x.secs['.text'][0])
            while x.pos < x.secs['.text'][2]:
                d = x.read(0x1000)
                try:idx = d.index(b'System.Security.Cryptography\0')
                except:pass
                else:break
            else: return 1

            x.seek(x.pos - 0x1000 + idx)
            while x.pos < x.secs['.text'][2]:
                b = x.reads()
                if b == b'\0':break
                while b != b'\0': b = x.read(1)
            else: return 1

            key = x.read(x.readu16('>')-1)
            iv = x.read(x.readu16('>')-1)
            x.skip(2)
            dat = x.read(x.readu24('>')-1)
            x.close()
            key,iv,dat = [base64.b64decode(x.decode('utf-16le')) for x in (key,iv,dat)]

            dat = AES.new(key,AES.MODE_CBC,iv).decrypt(dat)
            if dat[:2] == b'MZ':
                open(o + '/' + basename(i),'wb').write(dat[:-dat[-1]])
                return
        case 'Shell Archive':
            if db.print_try: print('Trying with custom extractor')
            d = open(i,newline='',encoding='utf-8').read()
            for fs in ('# This is a shell archive.  Remove anything before this line,',
                       '# This is a shell archive, meaning:',
                       '# This is a shell archive (produced by GNU sharutils',
                       '# This is a shell archive (shar',
                       '# This is a shell archive.  To extract the files,',
                       ': "This is a shell archive, meaning:',
                       ': This is a shar archive.  Extract with sh, not csh.',
                       '#  execute this shell (sh) script on a clean directory to',
                       '# shar:\tShell Archiver',
                       ':  SHAR archive format.  Archive created '):
                if fs in d:
                    d = d[d.index(fs):]
                    break

            for rge in (
                (r"(?sm)^ *sed +(?:-e +)?(?P<q1>['\"])s/\^([^\n]+)//(?P=q1) +> *(?P<q2>['\"]?)([^\n\"]+?)(?P=q2) +<< *(?P<q3>['\"]?)(?P<fend>[^\n]+?)(?P=q3) *\n(.+?)(?P=fend)"          ,3,6,1),
                (r"(?sm)^ *sed +(?:-e +)?(?P<q1>['\"])s/\^([^\n]+?)//(?P=q1) +<< *(?P<q2>['\"]?)(?P<fend>[^\n]+?)(?P=q2) *> *(?P<q3>['\"]?)([^\n\"]+?)(?P=q3)(?: *&&)? *\n(.+?)(?P=fend)",5,6,1),
                (r"(?sm)^ *cat +(?:- +)?> *(?P<q1>['\"]?)([^\n\"]+?)(?P=q1) +<< *(?P<q2>['\"]?)(?P<fend>[^\n]+?)(?P=q2) *\n(.+?)(?P=fend)",1,4),
                (r"(?sm)^ *cat +(?:- +)?<< *\\(?P<fend>[^\n\"]+?) *> *(?P<q1>['\"]?)([^\n\"]+)(?P=q1) *\n(.+?)(?P=fend)"                  ,2,3),
                (r"(?sm)^ *cat +(?:- +)?<< *(?P<q1>['\"])(?P<fend>[^\n]+?)(?P=q1) *> *(?P<q2>['\"]?)([^\n\"]+)(?P=q2) *\n(.+?)(?P=fend)"  ,3,4),
                ):
                r = re.compile(rge[0])
                for fe in r.findall(d):
                    dt = fe[rge[2]]
                    if len(rge) > 3: dt = '\n'.join([x[1 if x.startswith(fe[rge[3]]) else 0:] for x in dt.split('\n')])
                    xopen(o + '/' + fe[rge[1]].lstrip('./'),'w',newline='',encoding='utf-8').write(dt)
                d = r.sub('',d)
            pr = db.print_try
            db.print_try = False
            for fe in re.findall(r"(?sm)^ *sed +(?P<q1>['\"])s/\^([^\n]+?)//(?P=q1) +<< *(?P<q2>['\"]?)(?P<fend>[^\n]+?)(?P=q2) *\| *uudecode +&&\n(.+?)(?P=fend)",d):
                tf = TmpFile('.uu')
                xopen(tf,'w',newline='',encoding='utf-8').write('\n'.join([x[1 if x.startswith(fe[1]) else 0:] for x in fe[4].split('\n')]))
                extract(tf.p,o,'UUencoded')
                tf.destroy()
            db.print_try = pr
            for de in re.findall(r"(?m)^ *mkdir +(?P<q1>['\"]?)(.+)(?P=q1)\n",d): mkdir(o + '/' + de[1])

            if os.listdir(o): return
        case 'Casio BE-300 Package':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            bo = f.readu16()
            fc = f.readu16()
            f.seek(bo)
            for _ in range(fc):
                f.skip(7)
                fn = f.read(f.readu8()).decode()
                f.skip(1)
                xopen(o + '/' + fn,'wb').write(f.read(f.readu32()))
            if fc: return
        case 'GPEComp':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            for pos in (0xAA48,0xAA70):
                f.seek(pos)
                if f.read(8) == b"\x00\xE9\x55\x43\x4C\xFF\x01\x1A": break
            else: return 1
            f.seek(-8,1)
            tf = TmpFile('.ucl')
            open(tf.p,'wb').write(f.read())

            of = o + '\\' + basename(i) + '.elf'
            run(['uclpack','-d',tf.p,of])
            tf.destroy()
            if exists(of) and os.path.getsize(of): return
        case 'EDI Install Archive':
            dosbox(['ediextract','/U:.',i])
            if os.listdir(o): return
        case 'EDI Install LZSS': return extract(i,o,'ARX') # deark
        case '.NET Packer 1':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            ps = f.seek(-0x5000,2)
            d = f.read(0x5000)
            f.seek(ps + d.index(b'\6\0\0\0\0\0\0\0') + 8)
            fc = f.readu32()
            f.skip(f.readu8() + 8*2*2 + 8)

            fs = []
            for _ in range(fc):
                fe = (f.readu64(),f.readu64())
                f.skip(8+1)
                fs.append((fe[0],fe[1],f.read(f.readu8()).decode()))
            for fe in fs:
                f.seek(fe[0])
                xopen(o + '/' + fe[2],'wb').write(f.read(fe[1]))
            if fc: return

    return 1
