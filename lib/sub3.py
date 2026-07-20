from .main import *

def extract3(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def quickbms(scr,inf=i,oup=o):
        if db.print_try: print('Trying with',scr)
        run(['quickbms','-Y',db.get(scr),inf,oup],print_try=False)
        if listdir(oup): return
        return 1
    def jsbeautifier(scr,inf=i,oup=o):
        t = scr
        scr = 'jsbeautifier_' + scr

        jfp = db.get(scr)
        jf = open(jfp).read()
        if 'from jsbeautifier.unpackers import UnpackingError' in jf: writefile(jfp,jf.replace('from jsbeautifier.unpackers import UnpackingError','class UnpackingError(Exception): pass'),'w')

        if db.print_try: print('Trying with',scr)
        jsm = getattr(__import__(f'bin.{scr}'),scr)
        if t == 'myobfuscate': jsm.CAVEAT = ''
        elif t == 'jsobfuscator':
            jsm._smartsplit = jsm.smartsplit
            jsm.smartsplit = lambda x: [ast.literal_eval('"' + x.replace('"','\\"') + '"') for x in jsm._smartsplit(x)]

        d = open(inf,encoding='utf-8').read()
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

        writefile(oup + '/' + tbasename(inf) + '.js',d,'w')
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
            if getsize(oup + '/_OUT.TXT') > 0: break
            sleep(0.1)

        while True:
            r = open(oup + '/_OUT.TXT','rb').read()
            if len(r) == getsize(oup + '/_OUT.TXT'):
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
        case 'Qt IFW':
            run(['qtifw-devtool','dump',i,o])
            if listdir(o): return

            zip7(i,o,None,True)
            if listdir(o) and not exists(o + '/.rsrc'): return
        case 'MSCAB SFX':
            zip7(i,o,t,True)
            if listdir(o) and not exists(o + '/.rsrc'): return
            remove(o)
            mkdir(o)

            env = os.environ.copy()
            env['__COMPAT_LAYER'] = 'RUNASINVOKER'

            if db.print_try: print('Trying with input (/X)')
            prc = subprocess.Popen([i,'/X:' + o,'/Q','/C'],stdout=-1,stderr=-1,env=env)
            for _ in range(20):
                if prc.poll() != None:
                    for _ in range(50):
                        if listdir(o): return
                        sleep(0.1)
                    break
                sleep(0.1)
            else: prc.kill()

            if db.print_try: print('Trying with input (/T)')
            prc = subprocess.Popen([i,'/T:' + o,'/Q'],stdout=-1,stderr=-1,env=env)
            for _ in range(10):
                if prc.poll() != None:
                    for _ in range(50):
                        if listdir(o): return
                        sleep(0.1)
                    break
                sleep(0.1)
            else: prc.kill()

            if db.print_try: print('Trying with input (-extract)')
            prc = subprocess.Popen([i,'-silent','-extract'],stdout=-1,stderr=-1,env=env,cwd=o)
            for _ in range(10):
                if prc.poll() != None:
                    for _ in range(50):
                        if listdir(o):
                            for f in listdir(o):
                                if f.endswith('.msi'): extract(o + '/' + f,o,'MSI')
                            return
                        sleep(0.1)
                    break
                sleep(0.1)
            else: prc.kill()
        case 'NSIS Installer':
            zip7(i,o,t,True)
            if listdir(o) and not exists(o + '/.rsrc'): return
            rmtree(o)
            mkdir(o)

            if quickbms('instexpl'):
                tm = []
                for x in listdir(o):
                    if isfile(o + '/' + x): tm.append(o + '/' + x)
                if tm:
                    mkdir(o + '/$INSFILES')
                    for x in tm: mv(x,o + '/$INSFILES')
                if exists(o + '/$INSTDIR'): copydir(o + '/$INSTDIR',o,True)
                return
        case 'Wise Installer':
            run(['e_wise',i,o])
            if os.path.exists(o + '/00000000.BAT'):
                e,_,r = run(['00000000.BAT'],getexe=False,print_try=False,cwd=o)
                if e: print('BAT returned',e,r)
                else: remove(o + '/00000000.BAT')
                return
            if listdir(o): raise NotImplementedError('Unhandled Wise Installer output')
        case 'Inno Installer':
            f = open(i,'rb')
            f.seek(-0x2000,2)
            gog = b'00#GOGCRCSTRING' in f.read()
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
                if not listdir(o): run(['innounp','-x','-m','-d' + o,'-y'] + pwd + [i])
                for x in listdir(o):
                    if x != '{app}':
                        try:
                            if isfile(o + '/' + x): mv(o + '/' + x,o + '/$INSFILES/' + x)
                            else:
                                if exists(o + '/$INSFILES'): copydir(o + '/' + x,o + '/$INSFILES',True)
                                else: mv(o + '/' + x,o + '/$INSFILES')
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
            if listdir(o):
                if gog:
                    for x in listdir(o):
                        p = o + '/' + x
                        if (isfile(p) and (x.startswith('goggame-') or x == 'install_script.iss')) or\
                           (isdir(p)  and x in {'tmp','embedded','__redist'}):
                               if exists(o + '/$INSFILES/' + x): x = noext(x) + '_2' + extname(x)
                               mv(p,o + '/$INSFILES/' + x)
                        elif isdir(p) and x in {'commonappdata','app'}: copydir(p,o + '/$INSFILES',True)
                        elif isdir(p) and x == '__support':
                            for xf in listdir(p):
                                if xf == 'app': copydir(p + '/' + xf,o,True)
                                else: mv(p + '/' + xf,o + '/$INSFILES/' + xf)
                            rmdir(p)
                else:
                    for x in listdir(o):
                        if not x in {'app','$INSFILES'}:
                            if x == 'install_script.iss' and exists(o + '/$INSFILES/install_script.iss'): mv(o + '/' + x,o + '/$INSFILES/' + x[:-4] + '_2.iss')
                            else: mv(o + '/' + x,o + '/$INSFILES/' + x)
                    if exists(o + '/app'): copydir(o + '/app',o,True)
                    if listdir(o) == ['$INSFILES']:
                        if fix_innoinstext(o,i): return
                        else: return 1
                return
        case 'VISE Installer': return quickbms('instexpl')
        case 'MSI':
            td = TmpDir(path=o)
            run(['lessmsi','x',i,td + '\\'])
            if exists(td + '/SourceDir') and listdir(td + '/SourceDir') and sum(map(getsize,rldir(td.p))) > (getsize(i) / 50):
                for _ in range(10):
                    try:copydir(td + '/SourceDir',o,True)
                    except PermissionError:pass
                    except shutil.Error:pass
                    else:break
                td.destroy()
                return
            td.destroy()

            td = TmpDir(path=o)
            run(['msiexec','/a',i,'/qn','/norestart','TARGETDIR=' + td],getexe=False)
            copydir(td,o,True)
            td.destroy()
            if listdir(o): return
            zip7(i,o,t,True)
            if listdir(o): return
        case 'MSP':
            run(['msix',i,'/out',o,'/ext'])
            if listdir(o): return
            zip7(i,o,t,True)
            if listdir(o): return
        case 'Setup Factory Installer':
            if not quickbms('totalobserver'):
                if listdir(o + '/%AppDir%'):
                    for x in listdir(o):
                        if isfile(o + '/' + x): remove(o + '/' + x)
                    copydir(o + '/%AppDir%',o,True)
                if exists(o + '/%SysDir%'): mv(o + '/%SysDir%',o + '/$SYS')
                return
            quickbms('instexpl')
        case 'InstallShield Setup':
            f = open(i,'rb')
            f.seek(943)
            if f.read(42) == b'InstallShield Self-Extracting Stub Program':
                from lib.file import decompress
                db.try_custom()
                while True:
                    x = f.read(1)
                    if not x: break
                    if x == b'P':
                        if f.read(3) == b'K\3\4':
                            d = [b'PK\3\4',f.read(14)]
                            cs = f.read(4)
                            d.append(cs)
                            cs = int.from_bytes(cs,'little')
                            d.append(f.read(4))
                            fnl = f.read(2)
                            d.append(fnl)
                            fnl = int.from_bytes(fnl,'little')
                            d.append(f.read(2))
                            fn = f.read(fnl)
                            d.append(fn)
                            fn = fn.decode('utf-8')
                            d.append(f.read(cs))

                            chhd = f.read(4)
                            asrt(chhd == b'PK\1\2')
                            d.append(chhd)
                            d.append(f.read(42+fnl))

                            chhd = f.read(4)
                            asrt(chhd == b'PK\5\6')
                            d.append(chhd)
                            d.append(f.read(12))
                            d.append((int.from_bytes(f.read(4),'little')).to_bytes(4,'little'))
                            d.append(b'\0\0')
                            writefile(o + '/' + fn,decompress(b''.join(d),'zip',out=1))
                        else: f.seek(-3,1)
                f.close()
                if listdir(o):
                    if exists(o + '/_INST32I.EX_') or exists(o + '/_inst16.ex_'):
                        if fix_isinstext(o): return
                    else: return
            else: f.close()

            run(['isx',i,o])
            if exists(o + '/' + tbasename(i) + '_sfx.exe'): remove(o + '/' + tbasename(i) + '_sfx.exe')
            if exists(o + '/' + tbasename(i) + '_ext.bin'):
                remove(o)
                mkdir(o)
            elif listdir(o):
                if exists(o + '/Disk1/setup.exe'):
                    if fix_isinstext(o,o + '\\Disk1'): return
                return

            td = TmpDir(path=o)
            tf = TmpFile(name=basename(i),path=td.p)
            _,po,_ = run(['isxunpack',tf],stdin='\n',cwd=td.p)
            tf.destroy()
            if 'All Files are Successfuly Extracted!' in po and len(listdir(td.p)) == 1:
                copydir(td + '/' + listdir(td.p)[0],o,True)
                td.destroy()
                if os.path.exists(o + '/_inst32i.ex_'):
                    if fix_isinstext(o): return
                else: return
            else: td.destroy()

            quickbms('instexpl')
            fs = listdir(o)
            if fs == ['install.exe','uninst.exe'] and (getsize(o + '/install.exe') + getsize(o + '/uninst.exe')) == 0:
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
            td = TmpDir(path=o)
            tf = TmpFile(suf='.z',path=td.p)
            tf.link(i)
            run(['icomp',basename(tf.p),'*.*','-d','-i'],cwd=td.p)
            tf.destroy()
            if not listdir(td.p): td.destroy()
            else:
                copydir(td,o,True)
                td.destroy()
                return
        case 'InstallShield Archive':
            if exists(noext(i) + '.hdr'):
                td = TmpDir(path=o)
                e,_,r = run(['i6comp','x','-rof',i],cwd=td.p)
                if not (e or 'Could not open ' in r) and listdir(td.p):
                    copydir(td,o,True)
                    td.destroy()
                    return
                td.destroy()

                td = TmpDir(path=o)
                e,_,_ = run(['i5comp','x','-rof',i],cwd=td.p)
                if not e and listdir(td.p):
                    copydir(td,o,True)
                    td.destroy()
                    return
                td.destroy()
            return 1

            ti = TmpFile('.ini')
            td = TmpDir()
            rd = {f'{os.environ["SYSTEMROOT"].lower()}\\temp':td.p}
            if 'c:\\windows\\temp' in rd: rd['c:\\windows\\temp'] = td.p
            e,_,_ = hookshot(['iscab',i,'-i"' + ti + '"','-lx'],rd,env=os.environ.copy() | {'__COMPAT_LAYER':'RUNASINVOKER'})
            td.destroy()
            if not e:
                print('INI:\n' + readfile(ti))
                ti.destroy()
                raise NotImplementedError("iscab returned:\n" + e)
            ti.destroy()
        case 'Big EXE':
            ts = getsize(i)
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
                    writefile(o + f'/{c}.exe',f.read(siz))
                    f.seek(-f.tell() % 16,1)
                    if f.tell() >= ts: f.seek(sp + 64)
                    c += 1
            if c:
                for ix in range(c):
                    try: xr = main_extract(o + f'/{ix}.exe',o + f'/{ix}')
                    except ValueError: xr = False
                    if exists(o + f'/{ix}') and not listdir(o + f'/{ix}'): remove(o + f'/{ix}')
                    elif xr: remove(o + f'/{ix}.exe')
                return
        case 'Resource DLL':
            zip7(i,o,t,True)
            if exists(o + '/.rsrc'):
                copydir(o + '/.rsrc',o,True)
                return
        case 'Netopsystems FEAD':
            if db.print_try: print('Trying with input (/nos_ne)')
            run([i,'/s','/nos_ne','/nos_o' + o],print_try=False,env=os.environ.copy() | {'__COMPAT_LAYER':'RUNASINVOKER'})
            if listdir(o): return
        case 'Advanced Installer':
            if db.print_try: print('Trying with input (/extract)')
            td = TmpDir()

            p = subprocess.Popen([i,'/extract',td.p],stdout=-1,stderr=-1)
            for _ in range(25):
                if p.poll() != None: break
                sleep(0.1)
            else: p.kill()

            if listdir(td.p):
                bp = td.p + '\\' + listdir(td.p)[0]
                for f in listdir(bp):
                    if not f.endswith('.msi') or extract(bp + '\\' + f,o,'MSI'): mv(bp + '\\' + f,o + '\\$INSFILES\\' + f)
                td.destroy()
                if listdir(o): return
        case 'CExe':
            db.try_custom()
            from lib.file import ext_exe,decompress,iszl
            e = ext_exe(i)

            for x in e.DIRECTORY_ENTRY_RESOURCE.entries[0].directory.entries:
                id = x.id
                x = x.directory.entries[0].data.struct
                d = e.get_data(x.OffsetToData,x.Size)
                if d[:10] == b'SZDD\x88\xF0\x27\x33\x41\x00':
                    d = decompress(d,'szdd')
                    fn = '$STUB/inflate.dll'
                elif iszl(d):
                    d = decompress(d,'zlib')
                    fn = basename(i)
                else: fn = f'$STUB/{id}.bin'
                writefile(o + '/' + fn,d)

            e.close()
            return
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
            db.try_custom()
            from lib.file import File

            f = File(i,endian='<')
            f.seek(0x178)
            asrt(f.read(8) == b'.text\0\0\0')
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
            else: asrt(tmpl == len(src))

            f.skip(-39)
            sl = f.readu8()
            f.skip(38)
            fn = f.read(sl-38)[:-1].decode('utf-16le')
            fn += f.read(f.readu8())[:-1].decode('utf-16le')

            asrt(f.readu8() == 0x7D)
            f.skip(0x7D)

            bs = f.readcompiu()
            bs -= 1
            asrt(bs > 0)

            bat = f.read(bs)
            asrt(f.readu8() in {0,1})
            f.close()

            if len(bat.replace(b'\r',b'')) > 3519 and bat.startswith(b'set '):
                st = re.search(rb'^set [a-z]{10}=s\r?\n%[a-z]{10}%et [a-z]{10}=e\r?\n%[a-z]{10}%%[a-z]{10}%t [a-z]{10}=t\r?\n',bat)
                if st:
                    cr = st.end() > 87
                    asrt(st.end() == (87 + (3 if cr else 0)))
                    bat = bat[87 + (3 if cr else 0):]

                    mp = re.findall(rb'(?:%[a-z]{10}%){3} ([a-z]{10})=([a-z])\r?\ngoto [A-Z]{10}\r?\n(?:%[a-z]{10}%){3} [a-z]{10}=[a-z]\r?\n:[A-Z]{10}\r?\n',
                                    bat[:3432 + (104 if cr else 0)])
                    asrt(len(mp) == 26)
                    bat = bat[3432 + (104 if cr else 0):]
                    for x in mp:
                        bat = bat.replace(b'%' + x[0] + b'%',x[1])
                        if bat.strip().endswith(b'%' + x[0]): bat = bat.replace(b'%' + x[0],x[1])
            else:
                sub10 = re.compile(rb'%[a-z]{10}%')

                nrp = [sub10.sub(b'',x) for x in re.findall(rb'(%[a-z]{10}%|^)?[sS]%[a-z]{10}%[eE]%a[a-z]{10}%[tT]%[a-z]{10}%(?:[ \t]%[a-z]{10}%){1,} ((?:[a-z]%[a-z]{10}%){10})[ \t=][a-z]{10}',bat)] # find all real variables with a length of 10
                bat = sub10.sub(lambda m: m[0] if m[0] in nrp else b'',bat)
            writefile(o + '/' + fn,bat)

            return
        case '624'|'4kZIP'|'Amisetup'|'aPACK'|'AVPACK'|'COM RLE Packer'|'Cruncher'|'DexEXE'|'Dn.COM Cruncher'|'Envelope'|'ExeLITE'|'JAM'|'LGLZ'|'Pack Packed'|\
             'PMWLite'|'RDT Compressor'|'RJCrush'|'Shrinker Packed'|'SpaceMaker'|'T-PACK'|'Tenth Planet Soft'|'TSCRUNCH'|'XPACK/LZCOM'|'Dave Dunfield Packer':
            dosbox(['cup386',i,'OUT.BIN','/1h' + ('x' if open(i,'rb').read(2) == b'MZ' else '')])
            chks = getsize(i)-768
            if chks < 0x10: chks = 0x10
            if exists(o + '/OUT.BIN') and getsize(o + '/OUT.BIN') >= chks:
                on = basename(i)
                if on.lower().endswith('.exe') and open(o + '/OUT.BIN','rb').read(2) != b'MZ': on = on[:-3] + ('com' if on.endswith('.exe') else 'COM')
                elif on.lower().endswith('.com') and open(o + '/OUT.BIN','rb').read(2) == b'MZ': on = on[:-3] + ('exe' if on.endswith('.com') else 'EXE')
                mv(o + '/OUT.BIN',o + '/' + on)
                return
        case 'COMPACK'|'Compress-EXE'|'ICE'|'Optlink'|'PGMPAK'|'TinyProg':
            dosbox(['unp','e',i,'OUT.BIN'])
            chks = getsize(i)-768
            if chks < 0x10: chks = 0x10
            if exists(o + '/OUT.BIN') and getsize(o + '/OUT.BIN') >= chks:
                on = basename(i)
                if on.lower().endswith('.exe') and open(o + '/OUT.BIN','rb').read(2) != b'MZ': on = on[:-3] + ('com' if on.endswith('.exe') else 'COM')
                elif on.lower().endswith('.com') and open(o + '/OUT.BIN','rb').read(2) == b'MZ': on = on[:-3] + ('exe' if on.endswith('.com') else 'EXE')
                mv(o + '/OUT.BIN',o + '/' + on)
                return
        case 'AXE'|'CEBE'|'Cheat Packer'|'Diet Packed'|'EXECUTRIX-COMPRESSOR'|'LM-T2E'|'Neobook Executable'|'PACKWIN'|'Pro-Pack'|'SCRNCH'|'UCEXE'|'WWPACK'|\
             'PKTINY':
            r = extract(i,o,'624') # cup386
            if not r: return r
            remove(o)
            mkdir(i)

            r = extract(i,o,'COMPACK') # unp
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
            if listdir(o): return
        case 'IRIX IDB':
            db.try_custom()

            cps = {}
            pr7z = db.print_try
            lerr = False
            errp = ''
            for x in readfile(i,'r').strip().split('\n'):
                x = x.strip() + ' '
                t,x = x.split(' ',1)
                asrt(t in 'fdl',t)
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
                    if xn in {'sum','size','cmpsize','f'}: xv = int(xv)
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
                                try: p1 = d.read(lng).decode('utf-8')
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
                    asrt(len(dat) == rs,d.name)

                    if ne.get('cmpsize',0) > 0:
                        asrt(dat[:2] == b'\x1F\x9D')
                        tf = TmpFile('.z')
                        writefile(tf.p,dat)
                        _,dat,err = run(['7z','e','-so','-tZ',tf],text=False,print_try=pr7z)
                        if pr7z: pr7z = False
                        tf.destroy()

                        if len(dat) != ne['size']:
                            print(err.decode().strip(),path,f'[{d.name}@{d.tell():2X}]')
                            lerr = pr7z = True

                    writefile(o + '/' + path,dat)
                    try: writefile(o + '/' + path2,dat)
                    except FileExistsError as e:
                        op = e.filename
                        while os.path.lexists(op): op = e.filename + f'${c}';c += 1
                        writefile((o + '/' + path2).replace('/','\\').replace(e.filename,op,1),dat)
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
            if exists(of) and getsize(of): return
        case 'GameCube DOLXZ'|'Wii DOLXZ':
            db.try_custom()
            from lib.file import decompress

            f = open(i,'rb')
            f.seek(0x20)
            off = int.from_bytes(f.read(4),'big')
            f.seek(0x124)
            siz = int.from_bytes(f.read(4),'big')
            f.seek(off)
            d = f.read(siz)
            f.close()
            writefile(o + '/' + basename(i),decompress(d,'xz'))
            return
        case 'DOLPAK':
            ti = o + '/' + tbasename(i) + '.dol'
            tf = o + '/' + tbasename(i) + '.7z'
            symlink(i,ti)
            run(['dolpak',ti])
            remove(ti)
            asrt(exists(tf),err=FileNotFoundError)
            extract(tf,o,'7z')
            remove(tf)
            if listdir(o): return
        case 'd0lLZ 1'|'d0lLZ 2':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')

            f.seek(0x1C)
            data0 = f.readu32()
            f.seek(0xAC)
            data0_size = f.readu32()
            f.seek(data0)
            asrt(f.read(3) == b'DLZ')
            ver = f.readu8()

            of = open(o + '/' + basename(i),'wb')
            if ver == 2:
                def dlz_dec_block():
                    size = f.readu32()
                    asrt(size > 6)
                    epos = f.pos + size
                    f.skip(4)

                    dec = bytearray()
                    while f < epos:
                        flags = f.readu16('<')
                        bitc = 16
                        if (f.pos + bitc) > epos: bitc = epos - f.pos
                        for bit in range(bitc):
                            if (flags >> bit) & 1:
                                tok0,tok1 = f.readu8(),f.readu8()
                                oflags,leng,off = tok0 >> 4,(tok0 & 0x0F)+3,tok1
                                err = f'0b{oflags:04b},{leng},{off} = 0x{tok0:02X}{tok1:02X} @ 0x{f.pos-2:04X}'
                                asrt(off > 0,err)
                                off = len(dec) - off + 1
                                if off < 0:
                                    asrt(off >= -16,err)
                                    dec += bytes(-off)
                                    off = 0
                                for i in range(leng): dec.append(dec[off + i])
                            else: dec.append(f.readu8())
                    of.write(dec)
            else: raise NotImplementedError(f'Version {ver}')
            while f < (data0 + data0_size): dlz_dec_block()
            return
        case 'd0lLZ 3':
            raise NotImplementedError
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')

            f.seek(4)
            d0o = f.readu32()
            f.seek(0x94)
            d0s = f.readu32()
            f.seek(d0o)
            writefile(o + '/' + basename(i),f.decompress(d0s,'d0llz3'))
            return
        case 'Xamarin Compressed':
            db.try_custom()
            from lib.file import decompress
            try: writefile(o + '/' + basename(i),decompress(readfile(i)[8:],'lz4'))
            except: return 1
            return
        case 'JS P.A.C.K.E.R.': return jsbeautifier('packer')
        case 'JS MyObfuscate.com': return jsbeautifier('myobfuscate')
        case 'JavaScriptObfuscator': return jsbeautifier('jsobfuscator')
        case 'Javascript Obfuscator.com':
            db.try_custom()
            d = readfile(i,'r')

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

            writefile(f'{o}/{tbasename(i)}.js',d,'w')
            if d: return
        case 'C64 TBC MultiCompactor'|'C64 CruelCrunch'|'C64 Time Cruncher'|'C64 Super Compressor'|'C64 MegaByte Cruncher'|'C64 1001 CardCruncher'|\
             'C64 ECA Compactor':
            tf = o + '\\' + basename(i)
            symlink(i,tf)
            run(['unp64',tf])
            remove(tf)
            if listdir(o): return
        case 'VMProtect': raise NotImplementedError
        case 'Encrypted EAC Payload':
            hookshot(['decrypteacpayload','-e',i],{'C:\\EAC_Dumps':o})

            for f in listdir(o):
                p = o + '\\' + f
                if f.startswith('Dump_') and isdir(p) and exists(p + '/EAC_Launcher_decrypted.dll'): break
            else: return 1

            remove(p + '/original_eac.bin',p + '/eac_.bin')
            copydir(p,o,True)
            if open(o + '/EAC_Launcher_decrypted.dll','rb').read(4) in {b'MZ\x90\x00',b'\x7FELF'}: return
        case 'Chromium Delta Update':
            run(['android-ota-extract',i],cwd=o)
            if listdir(o): return
        case 'Excel DNA XLL':
            run(["exceldna-unpack",'--xllFile=' + i,'--outFolder=' + o,'--overwrite'])
            if listdir(o): return
        case 'Nuitka Compiled':
            run(['nuitka-extractor',i],cwd=o)
            if listdir(o): return
        case 'Python Compiled Module':
            err,r,_ = run(['pycdc',i],text=False)
            asrt(not err)
            writefile(o + '/' + tbasename(i) + '.py',r.split(b'\r\n',3)[3])
            return
        case 'Install Creator Pro':
            run(['cicdec','-db',i,o])
            if listdir(o):
                for f in listdir(o):
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
            writefile(o + '/' + tbasename(i) + '.asm',r)
            return
        case 'Atomik Cruncher': raise NotImplementedError
        case 'Netcrypt':
            db.try_custom()
            from lib.file import EXE
            from lib.crypto import decrypt

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
                b = x.read(1)
                if b == b'\0':break
                while b != b'\0': b = x.read(1)
            else: return 1

            key = x.read(x.readu16('>')-1)
            iv = x.read(x.readu16('>')-1)
            x.skip(2)
            dat = x.read(x.readu24('>')-1)
            x.close()
            key,iv,dat = [decrypt(x.decode('utf-16le'),'b64') for x in (key,iv,dat)]

            dat = decrypt(dat,'aes_cbc',key,iv)
            if dat[:2] == b'MZ':
                writefile(o + '/' + basename(i),dat[:-dat[-1]])
                return
        case 'Shell Archive':
            db.try_custom()
            import re,shlex
            from lib.crypto import decrypt
            d = readfile(i,'rt',newline='')
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
                (r"(?sm)^ *sed +(?:-e +)?(?P<q1>['\"])s/\^([^\r\n]+)//(?P=q1) +> *(?P<q2>['\"]?)([^\r\n\"]+?)(?P=q2) +<< *(?P<q3>['\"]?)(?P<fend>[^\r\n]+?)(?P=q3) *\r?\n(.+?)(?P=fend)",3,6,1),
                (r"(?sm)^ *sed +(?:-e +)?(?P<q1>['\"])s/\^([^\r\n]+?)//(?P=q1) +<< *(?P<q2>['\"]?)(?P<fend>[^\r\n]+?)(?P=q2) *> *(?P<q3>['\"]?)([^\r\n\"]+?)(?P=q3)(?: *&&)? *\r?\n(.+?)(?P=fend)",5,6,1),
                (r"(?sm)^ *cat +(?:- +)?> *(?P<q1>['\"]?)([^\r\n\"]+?)(?P=q1) +<< *(?P<q2>['\"]?)\\?(?P<fend>[^\r\n]+?)(?P=q2) *\r?\n(.+?)(?P=fend)",1,4),
                (r"(?sm)^ *cat +(?:- +)?<< *\\(?P<fend>[^\r\n\"]+?) *> *(?P<q1>['\"]?)([^\n\"]+)(?P=q1) *\r?\n(.+?)(?P=fend)"                  ,2,3),
                (r"(?sm)^ *cat +(?:- +)?<< *(?P<q1>['\"])(?P<fend>[^\r\n]+?)(?P=q1) *> *(?P<q2>['\"]?)([^\r\n\"]+)(?P=q2) *\r?\n(.+?)(?P=fend)"  ,3,4),
                ):
                r = re.compile(rge[0])
                for fe in r.findall(d):
                    dt = fe[rge[2]]
                    if len(rge) > 3: dt = '\n'.join([x[1 if x.startswith(fe[rge[3]]) else 0:] for x in dt.split('\n')])
                    writefile(o + '/' + sanitize_relative(fe[rge[1]]),dt,'wt',newline='')
                d = r.sub('',d)
            UUR = re.compile(r'(?ms)begin \d+ ([^\n]+)\n(.+?)\nend\n')
            for fe in re.findall(r"(?sm)^ *sed +(?P<q1>['\"])s/\^([^\r\n]+?)//(?P=q1) +<< *(?P<q2>['\"]?)(?P<fend>[^\r\n]+?)(?P=q2) *\| *uudecode +&&\r?\n(.+?)(?P=fend)",d):
                dt = '\n'.join([x[1 if x.startswith(fe[1]) else 0:] for x in fe[4].replace('\r','').split('\n')])
                asrt('begin ' in dt)
                for ufe in UUR.findall(dt): writefile(o + '/' + sanitize_relative(ufe[0]),decrypt(ufe[1],'uu'))
            for de in re.findall(r"(?m)^ *mkdir +([^\r\n]+)\r?\n",d):
                for dn in shlex.split(de): mkdir(o + '/' + sanitize_relative(dn))

            if listdir(o): return
        case 'Casio BE-300 Package':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            bo = f.readu16()
            fc = f.readu16()
            f.seek(bo)
            for _ in range(fc):
                f.skip(7)
                fn = f.read(f.readu8()).decode('utf-8')
                f.skip(1)
                writefile(o + '/' + fn,f.read(f.readu32()))

            f.close()
            if fc: return
        case 'GPEComp':
            db.try_custom()
            from lib.file import decompress
            f = open(i,'rb')
            for pos in (0xAA48,0xAA70):
                f.seek(pos)
                if f.read(8) == b"\x00\xE9\x55\x43\x4C\xFF\x01\x1A": break
            else: return 1
            f.seek(-8,1)
            d = f.read()
            f.close()
            writefile(f'{o}/{basename(i)}.elf',decompress(d,'uclpack',db=db))
            return
        case 'EDI Install Archive':
            dosbox(['ediextract','/U:.',i])
            if listdir(o): return
        case 'EDI Install LZSS': return extract(i,o,'ARX') # deark
        case '.NET Packer 1':
            db.try_custom()
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
                fs.append((fe[0],fe[1],f.read(f.readu8()).decode('utf-8')))
            for fe in fs:
                f.seek(fe[0])
                writefile(o + '/' + fe[2],f.read(fe[1]))

            f.close()
            if fc: return
        case 'Xbox Executable':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            asrt(f.read(4) == b'XBEH')
            f.seek(0x104)
            boff = f.readu32()
            f.skip(0x14)
            secs = f.readu32()
            seco = f.readu32()
            f.seek(seco-boff)

            fs = []
            for _ in range(secs):
                flgs = f.readu32()
                f.skip(8)
                fs.append([f.readu32(),f.readu32(),f.readu32()-boff,flgs & 4])
                f.skip(0x20)

            for fe in fs:
                f.seek(fe[2])
                fn = f.read0s().decode('latin1')
                if fe[3]: fn = '$SYS/' + fn
                f.seek(fe[0])
                writefile(o + '/' + fn,f.read(fe[1]))
            if fs: return
        case 'Lua Bytecode':
            f = open(i,'rb')
            asrt(f.read(4) == b'\x1bLua')
            v = f.read(1)[0]
            fv = f.read(1)[0]
            f.close()
            mav,miv = v >> 4,v & 0xF

            of = o + '\\' + tbasename(i) + '.lua'
            if mav == 5:
                if db.print_try: print('Trying with unluac')
                run(['java','-jar',db.get('unluac'),'--output',of,i],print_try=False)
            if exists(of) and getsize(of): return

            if fv == 0 and mav == 5 and miv in {1,2,3}: writefile(of,run([f'luadec{mav}{miv}','--',i],text=False)[1])
            if exists(of) and getsize(of): return
        case 'Bink Video EXE':
            db.try_custom()
            from lib.file import EXE
            f = EXE(i)

            VS = list(b'fghi')

            if 'BINKDATA' in f.secs:
                f.seek(f.secs['BINKDATA'][0])
                for _ in range(0x20):
                    tg = f.read(4)
                    if tg[:3] == b'BIK' and tg[3] in VS:
                        s = f.readu32()+8
                        f.skip(-8)
                        writefile(o + f'/{tbasename(i)}_logo.bik',f.read(s))
                        break
                    f.skip(12)

            f.seek(max(f.secs.values(),key=lambda x:x[2])[2])
            if f.read(3) == b'BIK' and f.readu8() in VS:
                s = f.readu32()+8
                f.skip(-8)
                writefile(o + f'/{tbasename(i)}.bik',f.read(s))

            f.close()
            if listdir(o): return
        case 'Inno Archive':
            db.try_custom()
            import zlib
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(8) == b'idska32\x1A')
            f.skip(4)
            asrt(f.read(4) == b'zlb\x1A')
            f.skip(6)

            of = open(o + '/' + basename(i),'wb')
            z = zlib.decompressobj(wbits=-15)
            while f: of.write(z.decompress(f.read(0x800)))
            f.close()
            p = of.tell()
            of.close()
            if p: return
        case 'PlayStation 2 IOPRP IMG'|'PlayStation 2 BIOS':
            tf = TmpFile('.img',path=o)
            tf.link(i)
            run(['romman','-x',tf])
            tf.destroy()
            if exists(o + '/' + tbasename(tf.p) + '.csv') and listdir(o + '/ext_' + basename(tf.p)):
                mv(o + '/' + tbasename(tf.p) + '.csv',o + '/$' + tbasename(i) + '.csv')
                copydir(o + '/ext_' + basename(tf.p),o,True,reni=True)
                for f in listdir(o):
                    if isdir(o + '/' + f):
                        mv(o + '/' + f,o + '/' + f[4:] + '_ext')
                        mv(o + '/' + f[4:] + '.csv',o + '/$' + f[4:] + '.csv')
                return
        case 'Windows CE FW IMG'|'Windows CE Xip':
            run(['eimgfs',i,'-r','-d',o,'-extractall'])
            if listdir(o):
                if len(listdir(o)) == 1: copydir(o + '/' + listdir(o)[0],o,True,reni=True)
                else: return
                if listdir(o): return
        case 'PlayStation 3 SELF/SPRX':
            of = o + '\\' + tbasename(i) + '.elf'
            _,ro,rr = run(['ps3_unself',i,of],env={'PS3_KEYS':db.get('ps3oskeys')})
            if not ' (ERROR)' in ro and not ' (ERROR)' in rr and exists(of) and getsize(of): return
        case 'AMI Aptio Capsule':
            tf = TmpFile(suf=extname(i),path=o)
            tf.link(i)
            run(['uefiextract',tf,'all'])
            tf.destroy()
            if exists(tf.p + '.dump') and isdir(tf.p + '.dump') and listdir(tf.p + '.dump') and exists(tf.p + '.report.txt') and exists(tf.p + '.guids.csv'):
                mv(tf.p + '.report.txt',o + '/$report.txt')
                mv(tf.p + '.guids.csv',o + '/$GUIDs.csv')
                copydir(tf.p + '.dump',o,True,reni=True)
                return
        case 'Amiga Kickstart ROM':
            db.get('amitools')

            import importlib,importlib.util
            class RedSpec:
                @classmethod
                def find_spec(cls,fullname,path,target=None):
                    if fullname.startswith('amitools.') or fullname == 'amitools':
                        rename = 'bin.' + fullname
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

            if db.print_try: print('Trying with amitools')
            from bin.amitools.rom.romsplitter import RomSplitter # type: ignore
            from bin.amitools.binfmt.hunk.BinFmtHunk import BinFmtHunk # type: ignore
            rs = RomSplitter(db.get('ami_ks_rom_splitdata'))
            if not rs.find_rom(i):
                del rs
                return 1
            bfm = BinFmtHunk()

            for e in rs.get_all_entries():
                for opt in ((0,0,''),(1,0,'$FIX/'),(0,1,'$PTC/'),(1,1,'$FIX+PTC/')):
                    if opt[0] and not e.extra.fixes: continue
                    if opt[1] and not e.extra.patches: continue
                    mkdir(o + '/' + opt[2])
                    bfm.save_image(f'{o}/{opt[2]}{e.name}',rs.extract_bin_img(e,opt[0],opt[1]))

            del rs
            del bfm
            if listdir(o): return
        case '.NETZ':
            db.try_custom()
            from lib.file import File,ext_exe
            e = ext_exe(i,dotnet=True)
            asrt(len(e.net.resources) == 1 and e.net.resources[0].name == 'app.resources')

            ffn = e.FileInfo[0][1].StringTable[0].entries[b'OriginalFilename'].decode('utf-8')
            # dnfile's resource parser seems to be broken?
            f = File(e.net.resources[0].data._data,endian='<')
            e.close()

            asrt(f.read(4) == b'\xCE\xCA\xEF\xBE')
            f.skip(4)
            f.skip(f.readu32())
            f.skip(4)
            c = f.readu32()
            asrt(f.readu32() == 0)
            f.align(8)
            f.skip(4*c)
            nos = [f.readu32() for _ in range(c)]
            bo = f.readu32()
            sbo = f.pos

            fs = []
            for no in nos:
                f.seek(sbo + no)
                fs.append((f.read(f.readleb128u()).decode('utf-16le'),f.readu32()))

            for ix,fe in enumerate(fs):
                f.seek(bo + fe[1] + 1)
                xopen(o + '/' + (ffn if ix == 0 else fe[0].replace('!1',' ').replace('!2',',').replace('!3','.Resources').replace('!4','Culture').split(',')[0] + '.dll'),
                      'wb').write(f.decompress(f.readu32(),'zlib'))

            del f
            if listdir(o): return
        case 'Pascal Script Binary':
            td = TmpDir()
            mkdir(td + '/Desktop')
            opp = td + '/AppData/Roaming/vdisasm/isd/options.xml'
            writefile(opp,'<?xml version="1.0" encoding="utf-8"?><Options xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><LastScriptPath>' + i + '</LastScriptPath><LastMethodName></LastMethodName></Options>','w')
            if db.print_try: print('Trying with isd')
            p = subprocess.Popen([db.get('isd')],env=os.environ.copy() | {'APPDATA':td.p + '\\AppData\\Roaming','USERPROFILE':td.p})
            of = o + '\\' + tbasename(i) + '.pas'

            sleep(2)
            send_keys('%fe')
            sleep(0.5)
            send_keys(of,escape=True)
            send_keys('{ENTER}')
            sleep(0.75)
            while not exists(of) or not getsize(of): sleep(0.1)
            p.kill()
            td.destroy()
            return
        case 'WebAssembly':
            run(['wasm2c',i,'--enable-exceptions','--enable-tail-call','--enable-memory64','--enable-multi-memory','--enable-extended-const','--enable-custom-page-sizes','-o',o + '\\' + tbasename(i) + '.c'])
            run(['wasm2wat',i,'--enable-all','-o',o + '\\' + tbasename(i) + '.wat'])
            run(['wasm-decompile',i,'--enable-all','-o',o + '\\' + tbasename(i) + '.txt'])
            return
        case 'CryptPE BinTable.h':
            db.try_custom()
            import re,ast
            from lib.file import decompress
            from lib.crypto import decrypt

            inf = open(i).read()
            s = int(re.search(r'static size_t file_size *= *(\d+);',inf)[1])
            inf = {x[0]:bytes(ast.literal_eval(f'({x[1]})')) for x in re.findall(r'static uint8_t (\w+)\[\] *= *\{([^\}]+)\}',inf)}
            tree,bc = decrypt(inf['tree'],'salsa20',inf['key'],inf['nonce'],return_block_count=True)
            dat = decrypt(inf['binary'],'salsa20',inf['key'],inf['nonce'],block_count=bc)

            writefile(f'{o}/{tbasename(i)}.exe',decompress(tree + dat,'huffman',usize=s,padding=True))
            return
        case 'CryptPE':
            db.try_custom()
            import re
            from lib.file import decompress,EXE
            from lib.crypto import decrypt
            f = EXE(i)

            ds = f.secs['.data'][1] - 0x80 - 0x20 - 0x10 - 0x30
            f.seek(f.secs['.text'][0] + 0x800)
            cod = f.read(f.secs['.text'][1] - 0x800)

            cmps1 = re.findall(b'\x81[\xFF\xFD].{4}',cod)
            scmp = {}
            for c in cmps1:
                adr = int.from_bytes(c[2:6],'little')
                if adr > ds: continue
                if not adr in scmp: scmp[adr] = []
                scmp[adr].append(c[1])
            cmps1 = [x for x in scmp if len(scmp[x]) == 2 and 0xFF in scmp[x] and 0xFD in scmp[x]]
            asrt(len(cmps1) == 1)

            cmps2 = [int.from_bytes(x[2:4],'little') for x in re.findall(b'\x81\xFF.[\0\1]\0\0',cod)]
            cmps2 = [x for x in cmps2 if 0x140 >= x >= 0x30]
            asrt(len(cmps2) == 1)

            movs = [int.from_bytes(x[1:5],'little') for x in re.findall(b'\xB9.{4}',cod)]
            movs = [x for x in movs if cmps1[0]*1.75 > x > cmps1[0]/2.5]
            cmps3 = [int.from_bytes(x[3:7],'little') for x in re.findall(b'\x49\x81\xF9.{4}',cod)]
            cmps3 = [x for x in cmps3 if x in movs]
            asrt(len(cmps3) == 1)
            del cod

            f.seek(f.secs['.data'][0] + 0x80)
            key = f.read(0x20)
            nonce = f.read(0x10)
            tree = f.read(cmps2[0])
            dat = f.read(cmps1[0])

            tree,bc = decrypt(tree,'salsa20',key,nonce,return_block_count=True)
            dat = decrypt(dat,'salsa20',key,nonce,block_count=bc)

            writefile(f'{o}/{tbasename(i)}.exe',decompress(tree + dat,'huffman',usize=cmps3[0],padding=True))
            return
        case 'Fatpack':
            db.try_custom()
            from lib.file import ext_exe,decompress
            f = ext_exe(i)

            if '.fpack  ' in f.SECTIONS: d = f.SECTIONS['.fpack  '].get_data()
            else:
                inf = f.DIRECTORY_ENTRY_RESOURCE.entries[0].directory.entries[0].directory.entries[0].data.struct
                d = f.get_data(inf.OffsetToData,inf.Size)
            f.close()

            writefile(f'{o}/{tbasename(i)}.exe',decompress(d,'lzma',null_usize=True))
            return
        case 'zexe':
            db.try_custom()
            from lib.file import decompress
            d = decompress(readfile(i)[0x200:],'gzip')
            writefile(f'{o}/{tbasename(i)}.{"exe" if d[:2] == b"MZ" else "elf"}',d)
            return
        case 'MASM Installer':
            from lib.file import EXE

            f = EXE(i)
            f.seek(f.secs['.data'][0])
            tf = TmpFile(name='.data')
            writefile(tf.p,f.read(f.secs['.data'][1]))
            f.close()

            zip7(tf,o,None,True)
            tf.destroy()
            if listdir(o): return
        case 'Tixati Installer':
            db.try_custom()
            from lib.file import ext_exe,decompress
            f = ext_exe(i)

            nms = [x.decode('utf-8').strip('\\/') for x in f.SECTIONS['.rdata'].get_data().split('Copy program files...'.encode('utf-16le'))[1].split(b'\0') if x]
            fnd = bool(nms)
            nmsbz = [x for x in nms if x.endswith('.bz2')]
            nms = [x for x in nms if x not in nmsbz]

            for x in f.DIRECTORY_ENTRY_RESOURCE.entries[0].directory.entries:
                x = x.directory.entries[0].data.struct
                d = f.get_data(x.OffsetToData,x.Size)
                if d[:3] == b'BZh': writefile(o + '/' + nmsbz.pop(0)[:-3],decompress(d,'bzip2'))
                elif d[:23] == b'SCROLL THIS WINDOW DOWN': writefile(o + '/' + nms.pop(0),d)
                else: raise NotImplementedError('Unknown file')

            f.close()
            if fnd and not nmsbz and not nms: return
        case 'SecuROM': raise NotImplementedError
        case 'Multimedia Fusion 2.0':
            TMAP = {
                0x1122:'Preview'} | {
                0x2222+ix:x for ix,x in enumerate(('MiniHeader','AppHeader','AppName','Author','MenuBar','ExtensionsPath','ExtensionsMini','FrameItems','GlobalEvents',
                                          'FrameHandles','ExtensionData','ExtraExtensions','EditorFilename','TargetFilename','HelpFile','TransitionFile','GlobalValues',
                                          'GlobalStrings','Extensions','AppIcon','IsDemo','SerialNumber','BinaryFiles','MenuImages','About','Copyright','GlobalValueNames',
                                          'GlobalStringNames','MovementExtensions','FrameItems','ExeOnly','AppHeaderExtra','Protection','ShaderBank','BluRayAppOptions',
                                          'ExtendedHeader','AppCodePage','FrameOffset','AdMobID','2249','Html5Preloader','AndroidMenu','VirtualKeysToChar','CharEncoding',
                                          'PreloaderTouchMsg','EngineVer','2250','AppLanguage','WUAOOptions','ObjectHeaders','ObjectNames','ObjectShaders',
                                          'ObjectProperties','ObjectPropOffsets','TrueTypeFontInfo','TrueTypeFontBank','DX9ShaderBank','225B','225C','PlayerControls',
                                          'AppIcon','225F','2260','2261'))} | {
                0x3333+ix:x for ix,x in enumerate(('Frame','FrameHeader','FrameName','FramePassword','FramePalette','FrameInstances','FrameFadeInStuff','FrameFadeOutStuff',
                                          'FrameTransitionIn','FrameTransitionOut','FrameEvents','FramePlayHeader','FrameExtraItems','FrameExtraInstances',
                                          'FrameLayers','FrameRect','FrameDemoPath','FrameSeed','FrameLayerEffects','FrameBluRayOptions','FrameMoveTimer',
                                          'FrameMosaicTable','FrameEffects','FrameRuntimeOptions','FrameWuaOptions','FrameHandle'))} | {
                0x4444+ix:x for ix,x in enumerate(('ObjectInfoHeader','ObjectInfoName','ObjectCommon','4447','ObjectInfoShader','ObjectAnimations','ObjectShapes'))} | {
                0x5555:'ImageOffsets',0x5556:'FontOffsets',0x5557:'SoundOffsets',0x5558:'MusicOffsets',0x6665:'BankOffsets',
                0x6666:'ImageBank',0x6667:'FontBank',0x6668:'SoundBank',0x6669:'MusicBank',
                0x7EEE:'Fusion3Seed',0x7F7F:'Last',
            }

            db.try_custom()
            from lib.file import EXE,File,decompress,iszl
            from lib.crypto import decrypt
            from multiprocessing.pool import ThreadPool
            f = EXE(i)
            f.seek(f.ovl_off)

            h = f.read(4)
            unp = False # h == b'wwww' # only for non exe
            if h == b'wwww': v = 2
            elif h in {b'\x7F\x7F\0\0',b'\x2C\x22\0\0'}:
                if f.read(4) == b'I\x87G\x12': v = 2
                else: v = 1.5
            elif h[:2] == b'\1\0': v = 1.1
            else: raise NotImplementedError('Unknown version')
            if v != 2: raise NotImplementedError(f'Unsupported version v{v}')
            anc = 'anaconda_' if v == 1.5 else ''

            if v > 1.5:
                f.seek(f.ovl_off + 0x1C)
                c = f.readu32()
                for _ in range(c):
                    fn = f.readutf16(f.readu16())
                    f.skip(4)
                    s = f.readu32()
                    if s > 6: zl = iszl(f.peek(8))
                    else: zl = False
                    writefile(o + '/' + fn,f.decompress(s,anc + ('zlib' if zl else 'none')))

            hn = f.reads(4,'ascii')
            rtv,rtsv = f.readu16(),f.readu16()
            prv,prb = f.readu32(),f.readu32()
            if rtv != 169:
                if prb < 280: v = 2.1 if prv == 1 else 2
            else: v = 1.5
            enc = 'utf-16' if hn != 'PAME' else 'ascii'

            if v != 2: raise NotImplementedError(f'Unsupported version v{v}')
            anc = 'anaconda_' if v == 1.5 else ''

            c = 0
            kids = {}
            fs = []
            while (f.pos + 8) < f.size:
                id = f.readu16()
                fl = f.readu16()
                s = f.readu32()
                fs.append((c,f.pos,id,fl,s))
                if id in {0x2224,0x222E,0x223B,0x224F}:
                    asrt(not fl & 2)
                    d = f.readc(s)
                    if fl & 1:
                        d = d[8:]
                        asrt(d[0] == 0x78,hex(f.pos - s - 8))
                        d = decompress(d,anc + ('zlib' if iszl(d) else 'deflate'))
                    if fl >> 2: raise NotImplementedError(f'Unknown flag {bin(fl)} @ {f.pos - s - 8}')
                    kids[id] = d
                else: f.skip(s)
                c += 1

            if 0x224F in kids:
                d = kids.pop(0x224F)
                asrt(len(d) == 12)
                prb = int.from_bytes(d[:4],'little')
            if prb > 285 or unp: ko = (0x2224,0x223B,0x222E)
            else: ko = (0x222E,0x2224,0x223B)
            key = b''.join(kids.pop(x,b'') for x in ko)

            ofis = {}
            for ix,of,id,fl,s in fs:
                f.seek(of)
                d = f.readc(s)

                if s > 0:
                    if fl & 2:
                        if fl & 1:
                            d = d[4:]
                            if prb > 285 and id & 1: d = (d[0] ^ (id & 0xFF) ^ (id >> 8)).to_bytes(1) + d[1:]
                        d = decrypt(d,'mmfs',key)
                        if fl & 1: d = d[4:]
                    if fl & 1:
                        if not fl & 2: d = d[8:]
                        asrt(d[0] == 0x78,f'{d[:4]} @ 0x{of + 8:08X}')
                        d = decompress(d,anc + ('zlib' if iszl(d) else 'deflate'))
                    if fl >> 2: raise NotImplementedError(f'Unknown flag {bin(fl)} @ {of - 8}')
                fn = f'{o}/$Chunks/{ix:03d}.{TMAP.get(id,f"{id:04X}")}'
                writefile(fn,d)

                if id in {0x5555,0x5556,0x5557,0x5558,
                          0x6666,0x6667,0x6668,0x6669}:
                    ofis[id] = fn

            p = ThreadPool()
            prcs = []
            for bid in range(4):
                if not (bid + 0x5555) in ofis or not (bid + 0x6666) in ofis: continue
                od = File(ofis[bid + 0x5555],endian=f._end)
                dd = File(ofis[bid + 0x6666],endian=f._end)
                offs = sorted(set([od.readu32() - 0x104 for _ in range(od.size//4)]))
                del od
                while offs and offs[0] < 1: offs.pop(0)
                if not offs:
                    del dd
                    continue
                offs.append(dd.size)
                def dec(id,d,bfn,bid):
                    fn = ''
                    if bid in {0,1,3}:
                        d = d[8:]
                        d = decompress(d,('zlib' if iszl(d) else 'deflate') if len(d) > 6 else 'none')
                    elif bid == 2:
                        d = d[12:]
                        flg = d[0] & 0x20
                        d = d[8:]
                        nl = int.from_bytes(d[:4],'little')
                        d = d[4:]
                        if not flg:
                            s = int.from_bytes(d[:4],'little')
                            d = decompress(d[4:4+s],'zlib' if iszl(d[4:]) else 'deflate')
                        if enc == 'utf-16': nl *= 2
                        fn = d[:nl]
                        while fn[-2 if enc == 'utf-16' else -1:] == b'\0\0': fn = fn[:-2 if enc == 'utf-16' else -1]
                        fn,d = fn.decode('utf-16le' if enc == 'utf-16' else enc),d[nl:]
                        if fn: fn += '_'
                    writefile(f'{bfn}_ext/{fn}{id:03d}.{("image","font","wav","music")[bid]}',d)

                for ix in range(len(offs) - 1):
                    dd.seek(offs[ix])
                    id = dd.readu32()
                    if bid == 0 and prb >= 284: id -= 1
                    elif bid == 1 and v >= 2 and prb < 284: id += 1
                    elif bid in {2,3} and v >= 2.5: id -= 1
                    prcs.append(p.apply_async(dec,(id,dd.readc(offs[ix+1] - offs[ix] - 4),ofis[bid + 0x6666],bid)))
                del dd
            for pc in prcs: pc.get()
            p.close()
            p.join()

            f.close()
            if listdir(o): return
        case 'Shockwave Flash':
            if db.print_try: print('Trying with ffdec')
            from multiprocessing import cpu_count
            env,td = make_env()
            _,_,r = run(['java','-jar',db.get('ffdec'),'-config',f'loopMedia=false,parallelSpeedUpThreadCount={cpu_count()}','-format','frame:gif','-select','1-250','-exportTimeout','65','-export','all,xfl',o,i],print_try=False,env=env)
            td.destroy()
            if 'java.lang.Exception' in r:
                print(r)
                return 1
            for x in listdir(o):
                if not listdir(o + '/' + x): remove(o + '/' + x)
            if exists(o + '/xfl') and len(listdir(o + '/xfl')) == 1: copydir(o + '/xfl/' + listdir(o + '/xfl')[0],o + '/xfl',True,True)
            if listdir(o): return
        case 'NE Resource DLL':
            db.try_custom()
            from lib.file import ext_exe
            f = ext_exe(i)

            def getr(p,t):
                if type(t) == dict:
                    for k in t: getr(f'{p}/{k}',t[k])
                else:
                    d = t.data
                    if type(d) != bytes: d = d.read()
                    writefile(f'{p}.{guess_ext(d)}',d)
            getr(o,f.resource_table.resources)

            del f
            if listdir(o): return
        case '.NET Executable':
            if db.print_try: print('Trying with ilspycmd')
            run(['dotnet',db.get('ilspycmd'),'--disable-updatecheck','--nested-directories','-p','-o',o,i],getexe=False,print_try=False)
            if listdir(o): return
        case 'QuickBMS XML Script':
            db.try_custom()
            import re
            from html import unescape
            d = readfile(i,'r').strip()
            asrt(d.startswith('<bms') and d.endswith('</bms>'))
            d = d[:-6]
            hd = re.search(r'^<bms(\s+([\w_]+="[^"\n]*"\s*)+)?\s*>',d)
            asrt(hd)
            hd = hd[0]
            d = unescape(d[len(hd):].strip())

            atrs = [f'# {x[0]}={unescape(x[1])}' for x in re.findall(r'([\w_]+)="([^"\n]*)"',hd)]
            if atrs: d = '\n'.join(atrs) + '\n\n' + d
            writefile(f'{o}/{tbasename(i)}.bms',d,'w')
            if d: return
        case 'Gateshark2NTR Plugin':
            # https://gbatemp.net/threads/release-gateshark2ntr.436504/
            # https://github.com/phecdaDia/NTRClient/wiki/Gateshark
            # https://developer.arm.com/documentation/ddi0406/c/Application-Level-Architecture/Instruction-Details/Alphabetical-list-of-instructions
            # in: https://gbatemp.net/threads/release-gateshark2ntr.436504/post-8663350 out: https://gbatemp.net/threads/release-gateshark2ntr.436504/post-8664187
            raise NotImplementedError
            BA = 0x00100100
            BMP = {1 << ix:x for ix,x in enumerate(('A','B','SE','ST','DR','DL','DU','DD','R','L','X','Y'))} | {0x4000:'ZL',0x8000:'ZR'}

            def cut(i:int,s:int,o:int=0): return (i >> o) & ((1 << s) - 1)
            def imm12(i:int):
                v = cut(i,8)
                r = cut(i,4,8) * 2
                return cut((v >> r) | (v << (32 - r)),32)
            def procc(pc:int) -> bool:
                def pos(): return hex(of + pc*4 - 4 + BA)
                def get():
                    nonlocal pc
                    x = xc[pc];pc += 1
                    return x
                def getd(o):
                    o += pc * 4
                    o -= len(xc) * 4
                    return int.from_bytes(xd[o:o+4],'little')

                x = get()
                #print(hex(x))
                if len(xc) - pc > 3 and cut(x,16,16) == 0xe3a0:
                    v = imm12(x)
                    #print(hex(v),pos())
                    asrt(v and v.bit_count() < 4 and not v & 0x3000,pos())
                    asrt(cut(get(),8,24) == 0xEB and cut(get(),8,24) in {0xE2,0xE3})
                    ob.append(f'DD000000 {v:08X}')
                    bts.append(v)
                    x = get()
                    end = None
                    if x != 0x08BD8010:
                        asrt(cut(x,16,16) == 0x0A00,pos())
                        end = pc + cut(x,16) + 1

                    procc(pc)
                    ob.append('D0000000 00000000')
                    if end: return procc(end)
                    return 1
                elif len(xc) - pc > 4 and cut(x,20,12) == 0xe59f3 and cut(xc[pc],20,12) == 0xe59f2 and cut(xc[pc+1],16,16) == 0xe153:
                    v1 = getd(cut(x,8) + 4)
                    v2 = getd(cut(get(),8) + 4)
                    x = get()
                    v1 -= (cut(x,4,8) << 4) | cut(x,4)
                    ob.append(f'D9000000 {v1:08X}')
                    x = get()
                    if cut(x,16,16) == 0xE6FF: x = get()
                    asrt(cut(x,20,12) == 0xe1c23,pos())
                    v2 += cut(x,8,4)
                    ob.append(f'D6000000 {v2:08X}')
                elif len(xc) - pc > 3 and cut(x,20,12) == 0xe59f3 and cut(xc[pc],20,12) == 0xe59f1 and cut(xc[pc+1],16,16) == 0xe192:
                    v1 = getd(cut(x,8) + 4)
                    ob.append(f'D9000000 {v1:08X}')
                    v2 = getd(cut(get(),8) + 4)
                    ob.append(f'D6000000 {v2:08X}')
                    x = get()
                    while cut(x,16,16) != 0xe182: x = get()
                elif len(xc) - pc > 3 and cut(x,20,12) == 0xe59f3 and cut(xc[pc],20,12) == 0xe7921:
                    v = getd(cut(x,8) + 4)
                    ob.append(f'D9000000 {v:08X}')
                    pc += 1
                    x = get()
                    while cut(x,20,12) == 0xe2433:
                        v -= imm12(x)
                        x = get()
                    asrt(cut(x,20,12) == 0xe7821,pos())
                    ob.append(f'D6000000 {v:08X}')
                elif len(xc) - pc > 4 and cut(x,20,12) == 0xe59f3 and (cut(xc[pc],20,12) == 0xe59f3 or cut(xc[pc+1],20,12) == 0xe59f3):
                    v1 = getd(cut(x,8) + 4)
                    x = get()
                    if cut(x,20,12) == 0xe5132:
                        v1 -= cut(x,12)
                        x = get()
                    ob.append(f'D9000000 {v1:08X}')
                    asrt(cut(x,20,12) == 0xe59f3,pos())
                    v2 = getd(cut(x,8) + 4)
                    x = get()
                    asrt(cut(x,20,12) == 0xe5832,pos())
                    v2 += cut(x,12)
                    ob.append(f'D6000000 {v2:08X}')
                elif x == 0xE8BD8010: return 1

            db.try_custom()
            import re,struct
            d = readfile(i)

            bfp = re.search(b'(?s)[\x01-\xFF][\x10-\x1F]\x9F\xE5\x01\x00\xA0\xE3(...)\xEB',d)
            bfp = bfp.start(1)//4 + int.from_bytes(bfp[1],'little')
            fps = []
            for ps in re.finditer(b'(?s)[\x01-\xFF][\x10-\x1F]\x9F\xE5\x01\x00\xA0\xE3(...)\xEB',d):
                pfp = ps.start(1)//4 + int.from_bytes(ps[1],'little')
                if pfp == bfp: fps.append(ps.start())

            dss = []
            obs = []
            for ix,of in enumerate(fps):
                cs = (int.from_bytes(d[of:of+2],'little') & 0xFFF) + 8
                xc = d[of:of + cs]
                if ix == len(fps) - 1: xd = d[of + cs:of + cs + max(dss) + 0x10]
                else:
                    xd = d[of + cs:fps[ix + 1]]
                    dss.append(len(xd))

                no = int.from_bytes(xd[:4],'little') - BA
                n = d[no:].split(b'\0')[0]
                if not n.startswith(b'Execute: '): continue
                try: n = n[9:].decode('ascii');asrt(n.isprintable())
                except: continue

                ob = []
                xc:tuple[int] = struct.unpack(f'<{len(xc)//4}I',xc)
                bts = []
                try: procc(3)
                except: continue
                if ob and ob[-1] == 'D0000000 00000000': ob.pop()
                if bts:
                    pbts = []
                    dn = set()
                    for b in bts:
                        if b in dn: continue
                        dn.add(b)
                        pbts.append('+'.join([bn for pb,bn in BMP.items() if b & pb]))
                    bts = f'({"/".join(pbts)}) '
                else: bts = ''
                obs.append(f'[{bts}{n}]\n{"\n".join(ob)}\n')

            if obs:
                print(obs)
                #writefile(f'{o}/{tbasename(i)}.cht','\n'.join(obs),'w')
                #return
        case 'Concatinated C Code':
            db.try_custom()
            import re
            d = readfile(i,'rt')

            for r in ((r'(?s)_{69}\n\n([^\s]{3,})[^\n]*\n_{69}\n+(.+?)(?=\n_{69}\n\n|\x1A|$)',0,1),):
                pm = re.findall(r[0],d)
                if pm:
                    for m in pm: writefile(o + '/' + m[r[1]],m[r[2]],'wt')
                    break
            else: return 1
            return
        case 'Camelot Obfuscated NSO':
            db.try_custom()
            from lib.pyob import PyOBinX
            keys = PyOBinX.dl('keys',db)

            from lib.crypto import decrypt
            from lib.file import File,decompress
            f = File(i,endian='<')
            asrt(f.read(4) == b'NSO0')

            f.skip(4);f.padc(4)
            fl = f.readu32()
            f.skip(0x20)
            dsfo,dsmo,dss = f.readu32(),f.readu32(),f.readu32()
            f.skip(4)
            bid = f.readc(0x20)
            f.skip(8)
            cdss = f.readu32()
            f.seek(dsfo)
            if fl & 4: d = f.decompress(cdss,'zstd' if fl & 0x80 else 'lz4',usize=dss)
            else: d = f.readc(dss)

            keys.wait()
            # build id: base key, offset1, offset2, offset3, MT seed, MT drop
            bk,of1,of2,of3,seed,drop = keys['mario_golf_rush'][bid]
            of1 -= dsmo;of2 -= dsmo;of3 -= dsmo
            od = bytearray()

            td = decrypt(d[:of1],'camelot_xor',bk)
            td = decompress(td[:-4],'camelot_blz',usize=int.from_bytes(td[-4:],'little'))
            od.extend(td)

            td = decrypt(d[of1:of2],'camelot_xor',bk + 1)
            td = decompress(td[:-4],'camelot_blz',usize=int.from_bytes(td[-4:],'little'))
            od.extend(td)

            td = decrypt(d[of2:of3],'camelot_rand',bk + 2,seed,drop=drop)
            td = decompress(td[:-4],'camelot_blz',usize=int.from_bytes(td[-4:],'little'))
            od.extend(td)

            writefile(f'{o}/{tbasename(i)}.nro',od)
            return
        case 'AOLSetup':
            db.try_custom()
            from lib.file import File,ext_exe,decompress
            e = ext_exe(i)
            xn = e.DIRECTORY_ENTRY_EXPORT.name.decode('latin-1')
            asrt(xn in {'INSTALL.EXE','SETUP.EXE'},xn)

            f = File(e.get_overlay(),endian='<')
            e.close()
            asrt(f.readc(2) == b'RS')
            def reads(): return f.readc(f.readu16()).decode('latin-1')

            strs = [reads() for _ in whilelc(lambda:f.peek('u32'))]
            strs.append('')
            padl = len([f.skip(2) for _ in whilelc(lambda:not f.peek('u16'))]) * 2

            if xn == 'INSTALL.EXE' or padl == 12:
                strs.extend([reads() for _ in whilelc(lambda:f.peek('u32'))])
                while not f.peek('u16'): f.skip(2)
                f.skip(2)

            f.skip(2)
            f.skip(f.readu16()*4)
            xd = []
            for _ in range(2):
                c = f.readu16()
                d = {}
                for _ in range(c):
                    k = reads()
                    d[k] = reads()
                xd.append(d)
            while f.peek('u32'):
                c = f.readu16()
                xd.append([reads() for _ in range(c)])
            padl2 = len([f.skip(2) for _ in whilelc(lambda:not f.peek('u16'))]) * 2
            if padl2 == 6:
                f.skip(6)
                c = f.readu16()
                xd.append([reads() for _ in range(c)])
            elif xn == 'INSTALL.EXE' and padl == 0x14:
                c = f.readu16()
                xd.append([reads() for _ in range(c)])

            [f.skip(2) for _ in whilelc(lambda:not (f.peek('u16') > 1 and 20 >= f.peek('u16',poffset=2) >= 10 and f.peek(6,poffset=4).lower() == b'dunzip'))]

            c = f.readu16()
            fs = [(reads(),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                if fe[2] > f.left:
                    d = f.read(f.left)
                    if fe[2] != fe[1] and len(d) > 0x20:
                        asrt(d[:4] == b'PK\3\4' and d[8] in {8,0} and d[9] == 0)
                        nl = int.from_bytes(d[0x1A:0x1E],'little')
                        d = decompress(d[0x1E + nl:],'none' if d[8] == 0 else 'deflate_noerr')
                    writefile(o + '/' + sanitize_relative(fe[0]) + '.$eof',d)
                else:
                    writefile(o + '/' + sanitize_relative(fe[0]),f.decompress(fe[2],'zip' if fe[2] != fe[1] else 'none',usize=fe[1],out=1))

            del f
            if fs:
                writefile(o + '/$strings.txt','\n'.join(strs),'wt')
                json.dump(xd,xopen(o + '/$extra.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
                return
        case 'BitRock Installer':
            SST = (
                (8, 16,1, 32,2, 4 ),
                (4, 8, 1, 16,2, 0 ),
                (2, 4, 8, 1, 0, 16),
                (2, 4, 0, 8, 1, 0 ),
                (1, 2, 4, 0, 8, 0 ),
                (1, 2, 4, 0, 0, 8 ),
                (1, 2, 0, 4, 0, 0 ),
            )
            FSIG = b'bitrock-lzma-4.0mFC3acAOJrQinu5aEHu0uH7N5XSQ3Z14'

            db.try_custom()
            from lib.file import File,decompress,ext_exe,mask
            e = ext_exe(i)
            cert = None
            if len(e.OPTIONAL_HEADER.DATA_DIRECTORY) > 4:
                cert = e.OPTIONAL_HEADER.DATA_DIRECTORY[4].VirtualAddress
                if cert == 0: cert = None
            oo = e.get_overlay_data_start_offset()
            e.close()

            f = File(i,endian='>')

            if cert is None:
                f.seek(f.size)
                for _ in range(f.pos,oo,-8):
                    f.back(0x38)
                    tmp = f.read(0x38)
                    p = tmp.rfind(FSIG)
                    if p != -1: break
                    f.back(8)
                else: raise ValueError('Footer not found')
                f.back(len(tmp) - p)
            else:
                f.seek(cert - 0x37)
                tmp = f.read(0x37)
                p = tmp.rfind(FSIG)
                asrt(p != -1)
                f.back(len(tmp) - p)
            sp = f.back(0x10)
            f.skip(4)
            sz = f.readu32()
            f.skip(4) # toc size & 0x7FFFFFFF
            toco = f.readu32()
            sp -= sz

            if oo + 0x100 < sp:
                f.seek(oo)
                lnchd = f.peek(0x100)
                if lnchd.startswith(b'#!/bin/sh\n') and lnchd.endswith(b'#') and b'\x1A#' in lnchd and lnchd.rstrip(b'#').endswith(b'\x1A'):
                    writefile(o + '/$INSTFILES/$tclkit_launcher.sh',lnchd.split(b'\x1A')[0])
                oo += 0x100

            f.seek(sp - 7)
            cookfs = f.readc(7) == b'CFS0002'
            asrt(f.read(4) == b'JL\x1A\x00')
            f.seek(sp + toco)
            asrt(f.readbp() == 0)
            sch = f.reads(f.readbp())
            asrt(sch == 'dirs[name:S,parent:I,files[name:S,size:I,date:I,contents:B]]',sch)
            asrt(f.readbp() == 1)
            asrt(f.readbp() > 0) # dir size
            f.seek(sp + f.readbp())
            asrt(f.readbp() == 0)
            dc = f.readbp()

            def readi(s:int,c:int,signed=True) -> list[int]:
                if c == 0:
                    asrt(s == 0)
                    return []
                d = f.readc(s)

                if c < 8 and 0 < len(d) < 7: w = SST[c - 1][len(d) - 1]
                else: w = (len(d) * 8) // c
                asrt(w in {0,1,2,4,8,16,32,64})

                if w < 8:
                    asrt(not signed)
                    m = mask(w)
                    r = []
                    for ix in range(c): r.append((d[(ix * w) // 8] >> ((ix * w) & 7)) & m)
                    return r
                else: return f.readil(w // 8,d,signed,'<')
            def readd(c:int) -> list[bytes]:
                ds = f.readbp()
                if ds:
                    do = f.readbp()
                    ss = f.readbp()
                    if ss != 0: so = f.readbp()
                else: ss = 0
                cs = f.readbp()
                if cs != 0: co = f.readbp()
                rbp = f.pos

                if ss:
                    f.seek(sp + so)
                    s = readi(ss,c,False)
                else: s = [0] * c
                if ds:
                    f.seek(sp + do)
                    d = f.readc(ds)
                else: d = b''

                p = 0
                r = []
                for sz in s:
                    if sz == 0: r.append(None)
                    else:
                        r.append(d[p:p+sz])
                        p += sz

                if cs:
                    f.seek(sp + co)
                    xr = []
                    p = 0
                    while f.pos < sp + co + cs:
                        p += f.readbp()
                        asrt(c > p >= 0 and r[p] is None)
                        xs = f.readbp()
                        if xs:
                            xo = f.readbp()
                            if xo == 0: xr.append((p,xs))
                            else:
                                cp = f.pos
                                f.seek(sp + xo)
                                r[p] = f.readc(xs)
                                f.seek(cp)
                        else: r[p] = b''
                        p += 1

                    if xr:
                        f.seek(sp + co + cs)
                        for p,xs in xr: r[p] = f.readc(xs)
                f.seek(rbp)
                return [b'' if x is None else x for x in r]

            ns = [x[:-1].decode('utf-8') for x in readd(dc)]
            ps = f.readbp()
            if ps:
                po = f.readbp()
                cp = f.pos
                f.seek(sp + po)
                prs = readi(ps,dc,True)
                f.seek(cp)
            else: prs = []
            fes = f.readbp()
            if fes: feo = f.readbp()

            asrt(ns[0] == '<root>' and prs[0] == -1)
            ds = ['']
            for ix in range(1,dc): ds.append(sanitize_relative(ds[prs[ix]] + '/' + ns[ix]))

            f.seek(sp + feo)
            dist = None
            for dn in ds:
                asrt(f.readbp() == 0)
                c = f.readbp()
                dn = '$INSFILES/' + dn
                if c == 0:
                    mkdir(o + '/' + dn)
                    continue
                asrt(c > 0)
                fns = [x[:-1].decode('utf-8') for x in readd(c)]

                fss = f.readbp()
                fso = f.readbp()
                cp = f.pos
                f.seek(sp + fso)
                fs = readi(fss,c,True)
                f.seek(cp)

                fds = f.readbp()
                fdo = f.readbp()
                cp = f.pos
                f.seek(sp + fdo)
                fd = readi(fds,c,True)
                f.seek(cp)

                d = readd(c)
                for fix in range(c):
                    fn = o + '/' + dn + '/' + fns[fix]
                    sd = decompress(d[fix],'zlib' if len(d[fix]) != fs[fix] else 'none',usize=fs[fix])
                    if dn + '/' + fns[fix].lower() == '$INSFILES//origindist': dist = sd.decode('utf-8').lower()
                    writefile(fn,sd)
                    if fd[fix] != 0: set_ftime(fn,fd[fix])
            if not dist is None and exists(o + '/$INSFILES/' + dist): copydir(o + '/$INSFILES/' + dist,o,True)

            if cookfs:
                import json,re
                from lib.crypto import crc_hash,HASHTS
                BRG = re.compile(r'(.*)___bitrockBigFile([1-9]\d*)$')

                cmm = {0:'none',1:'deflate',255:'lzma'}
                ep = sp
                f.seek(ep - 0x10)
                idxs,pc,dalg = f.readu32(),f.readu32(),cmm[f.readu8()]
                sp = f.seek(ep - 0x10 - idxs - pc*0x14)
                asrt(sp >= oo)
                hshs = [f.readu128() for _ in range(pc)]
                szs = f.readil(4,pc)

                idx = File(f.decompress(idxs - 1,cmm[f.readu8()]),endian=f._end)
                asrt(idx.read(8) == b'CFS2.200')
                fs = []
                def readce(p):
                    c = idx.readu32()
                    for _ in range(c):
                        n = sanitize_relative(p + '/' + idx.reads(idx.readu8(),'utf-8'))
                        asrt(idx.readu8() == 0)
                        ts = idx.readu64()
                        bc = idx.reads32()
                        if bc == -1:
                            mkdir(o + '/' + n)
                            readce(n)
                        else: fs.append((n,ts,[(idx.readu32(),idx.readu32(),idx.readu32()) for _ in range(bc)]))
                readce('')

                if idx.left >= 4:
                    mc = idx.readu32()
                    m = {}
                    for _ in range(mc):
                        n = idx.reads(idx.readu32(),'utf-8').split('\0',1)
                        m[n[0]] = n[1]
                    json.dump(m,xopen(o + '/$INSFILES/$cookfs_metadata.json','wt'),ensure_ascii=False,indent=2)
                else: m = {}
                del idx

                hsh = m.get('cookfs.pagehash','md5')
                hmsk = mask(HASHTS[hsh]*8)
                f.seek(sp - sum(szs))
                pgs = []
                for ix in range(pc):
                    d = f.decompress(szs[ix] - 1,cmm[f.readu8()])
                    asrt(crc_hash(d,hsh) == hshs[ix] & hmsk,lambda:f'{hshs[ix] & hmsk:0{HASHTS[hsh]*2}X} != {crc_hash(d,hsh):0{HASHTS[hsh]*2}X} ({ix}, {szs[ix]} @ 0x{f.pos - szs[ix]:08X})')
                    pgs.append(d)
                f.close()

                bfs = {}
                tbfs = {}
                for fe in fs:
                    m = BRG.match(fe[0])
                    if m:
                        if m[1] not in bfs: bfs[m[1]] = []
                        bfs[m[1]].append((int(m[2]),fe[0]))

                    of = xopen(o + '/' + fe[0],'wb')
                    for be in fe[2]: of.write(pgs[be[0]][be[1]:be[1]+be[2]])
                    of.close()
                    set_ftime(o + '/' + fe[0],fe[1])
                    tbfs[fe[0]] = fe[1]

                for bf in bfs:
                    of = xopen(o + '/' + bf,'ab')
                    for x in sorted(bfs[bf],key=lambda x:x[0]):
                        of.write(readfile(o + '/' + x[1]))
                        remove(o + '/' + x[1])
                    of.close()
                    set_ftime(o + '/' + bf,tbfs[bf])

                if listdir(o) == ['$INSFILES','default']: copydir(o + '/default',o,True,True)
            else: f.close()

            if ds: return
        case 'Bytessence Install Maker':
            db.try_custom()
            from lib.crypto import crc_hash
            from lib.file import File,ext_exe,decompress
            e = ext_exe(i)
            oo = e.get_overlay_data_start_offset()
            e.close()
            f = File(i,endian='<')
            f.seek(oo)
            asrt(f.read(0x14) == b"$_BIM_CONFIG_START_$")

            f.skip(4)
            ms = f.readu32()
            if f.peek('u32') == 0 and f.peek(0x12,poffset=ms + 4) == b"$_BIM_CONFIG_END_$": v = 0
            else:
                ms = f.readu32()
                if f.peek('u32') == 0 and f.peek(0x12,poffset=ms + 4) == b"$_BIM_CONFIG_END_$": v = 1
                else: raise ValueError

            f.seek(oo + 0x18)
            if v == 0:
                ms = f.readu32()
                f.padc(4)
                md = f.readc(ms)
            elif v == 1:
                mc,ms = f.readu32(),f.readu32()
                f.padc(4)
                md = f.readc(ms)
                asrt(crc_hash(md,'crc32') == mc)
            asrt(f.read(0x12) == b"$_BIM_CONFIG_END_$")
            e = ext_exe(md)
            mn = e.DIRECTORY_ENTRY_EXPORT.name.decode('latin-1')
            del e
            writefile(o + '/$INSFILES/' + mn,md)

            if f.peek(5) == b'BLZMA':
                f.skip(5)
                v,ts = f.readu32(),f.readu32()
                asrt(v in {1,2})
                c = f.readu64()
                f.skip(0x10)
                prop = f.readc(5)

                for _ in range(c):
                    n = o + '/' + sanitize_relative(f.reads(f.readu32(),'cp1252').rstrip('\0'))
                    ts = f.readu32()
                    f.skip(4)
                    zs,us = f.readu64(),f.readu64()
                    ccrc = f.readu32()
                    if v == 1: enc = f.readu32()
                    else: enc = f.readu8()
                    asrt(enc == 0,'Encryption')

                    of = xopen(n,'wb')
                    crc = 0
                    while of.tell() < us:
                        bzs,bus = f.readu32(),f.readu32()
                        d = f.decompress(bzs,'lzma1_raw',props=prop,usize=bus + 4)[:bus]
                        crc = crc_hash(d,'crc32',value=crc)
                        of.write(d)
                    of.close()
                    asrt(crc == ccrc)
                    set_ftime(n,ts)
            elif f.peek(4) == b'PK\3\4':
                for fe in f.decompress(None,'zip',out={}):
                    fn = sanitize_relative(fe[0])
                    if fe[1] is None: mkdir(o + '/' + fn)
                    else:
                        writefile(o + '/' + fn,fe[1])
                        set_ftime(o + '/' + fn,fe[2])

            f.close()
            if listdir(o) != ['$INSFILES']:
                for de in listdir(o):
                    if de.startswith('_$_INSTALLER_Data_') and de.endswith('_$_') and de[18:-3].isdigit():
                        copydir(o + '/' + de,o + '/$INSFILES',True)
                if len(listdir(o)) == 2:
                    dig = [x for x in listdir(o) if x.isdigit()]
                    if dig: copydir(o + '/' + dig[0],o,True,True)
                return
        case 'DeployMaster':
            db.try_custom()
            from lib.crypto import crc_hash
            from lib.file import File,ext_exe,iszl
            e = ext_exe(i)
            oo = e.get_overlay_data_start_offset()
            for x in e.DIRECTORY_ENTRY_RESOURCE.entries:
                if x.id == 0x10:
                    ve = x.directory.entries[0].directory.entries[0].data.struct
                    vd = e.get_data(ve.OffsetToData,ve.Size)
                    break
            else: raise ValueError('No version offset')
            e.close()

            f = File(vd,endian='<')
            f.skip(6)
            f.read0s16()
            for _ in range(4):
                if f.peek('u8'): break
                f.skip(1)
            asrt(f.read(4) == b'\xBD\x04\xEF\xFE')
            v = tuple(f.readil(2,4)[::-1])
            del f

            f = File(i,endian='<')
            f.seek(oo)
            writefile(o + '/$INSFILES/$engine.exe',f.decompress(-1,'bz2'))
            asrt(f.reads32() == -1)
            writefile(o + '/$INSFILES/$lang.txt',f.decompress(f.readu32(),'zlib'))
            prj = f.decompress(f.readu32(),'zlib').split(b'\x0C')
            flg = prj[-1][-1] if prj[-1] else 0
            prj = [x.decode('cp1252').rstrip('\0') for x in prj[:-1]]
            writefile(o + '/$INSFILES/$project.txt','\n'.join(prj) + f'\n{flg:02X}','wt')

            if flg & 1:
                writefile(o + '/$INSFILES/$id_registry.bin',f.decompress(f.readu32(),'zlib'))
                writefile(o + '/$INSFILES/$id_validation.bin',f.decompress(f.readu32(),'zlib'))
                asrt(f.readu32() == 0)
            writefile(o + '/$INSFILES/$authentication.bin',f.readc(0x43))
            apph = f.readc(0x2B if v >= (2,7,0,0) else 4)
            writefile(o + '/$INSFILES/$appearance_header.bin',apph)
            if apph[-1]: writefile(o + '/$INSFILES/$appearance.bin',f.decompress(f.readu32(),'zlib'))

            fids = [7,8,9,10]
            if len(prj) >= 17: fids.append(14)
            res = {}
            for fi in fids:
                if prj[fi]: res[prj[fi]] = f.decompress(f.readu32(),'zlib')

            cc = f.readu8()
            for ix in range(cc):
                d = f.decompress(f.readu32(),'zlib')
                writefile(f'{o}/$INSFILES/$component_{ix}.{guess_ext(d)}',d)
            ns = f.decompress(f.readu32(),'zlib').decode('cp1252').replace('\r','').split('\n')
            if not ns[-1]: ns.pop()
            c = len(res) + len(ns)
            ofs = f.readil(4,c,signed=True)
            tss = f.readil(4,c)
            vss = f.readil(8,c,signed=True)
            szs = f.readil(4,c)
            crs = f.readil(4,c)

            for ix,(fn,d) in enumerate(res.items()):
                asrt(ofs[ix] == -1)
                asrt(szs[ix] == len(d) and crc_hash(d,'crc32') == crs[ix])
                fn = o + '/$INSFILES/' + fn
                writefile(fn,d)
                set_ftime(fn,tss[ix])

            eof = max(x + f.peek('u32',poffset=x - f.pos) for x in ofs[len(res):])
            ds = {}
            while f < eof:
                p = []
                while f < eof:
                    l = f.readu8()
                    if l == 0xFE: break
                    if l == 0xFF:
                        pk = f.peek('u32')
                        if pk == 0 or (pk >= 8 and f.pos + 4 + pk <= eof and iszl(f.peek(8,poffset=4))):
                            p = None
                            break
                    else: p.append(f.reads(l,'cp1252'))
                if p is None: break
                if p and p[0].upper() == '%APPFOLDER%': p.pop(0)
                p = sanitize_relative('/'.join(p))
                fids = f.decompress(f.readu32(),'zlib')
                fids = [int.from_bytes(fids[ix*3+1:ix*3+3],'little') for ix in range(len(fids)//3)]
                for ix in fids: ds[ix] = p

            oid = sorted(ds)[:c]
            for ix in range(len(res),c):
                f.seek(ofs[ix])
                d = f.decompress(f.readu32(),'zlib')
                asrt(szs[ix] == len(d) and crc_hash(d,'crc32') == crs[ix])
                if ix < len(oid): fn = o + '/' + ds[oid[ix]]
                else: fn = o
                fn += '/' + ns[ix - len(res)]
                writefile(fn,d)
                set_ftime(fn,tss[ix])

            f.close()
            if c > 0: return

    return 1
