import os
from lib.dldb import DLDB
from shutil import rmtree,copytree,copyfile

isfile,isdir,exists = os.path.isfile,os.path.isdir,os.path.exists
basename,dirname,splitext = os.path.basename,os.path.dirname,os.path.splitext
symlink,rename = os.symlink,os.rename
def tbasename(i:str): return splitext(basename(str(i)))[0]
def extname(i:str): return splitext(str(i))[1]
def noext(i:str): return splitext(str(i))[0]
def mkdir(i:str): os.makedirs(i,exist_ok=True)
def rmdir(i:str,r=True): rmtree(str(i)) if r else os.rmdir(str(i))
def copy(i:str,o:str):
    if o.endswith(('/','\\')):
        o = o.strip('\\/')
        mkdir(o)
    if isfile(i):
        if isdir(o): copyfile(i,o + '/' + basename(i))
        else:
            mkdir(dirname(o))
            copyfile(i,o)
    elif isdir(i):
        if o.endswith(('/','\\')):
            mkdir(o)
            copytree(i,o + basename(i),dirs_exist_ok=True)
        else: copytree(i,o,dirs_exist_ok=True)
cp = copy
def move(i:str,o:str):
    copy(i,o)
    remove(i)
mv = move
def copydir(i:str,o:str,delete=False):
    mkdir(o)
    for x in os.listdir(str(i)): cp(i + '/' + x,o + '/' + x)
    if delete: rmdir(i)
def remove(*inp:str): [os.remove(i) if isfile(i) or os.path.islink(i) else rmdir(i) for i in inp if exists(i)]
def xopen(f:str,m='r',encoding='utf-8'):
    f = os.path.abspath(str(f))
    mkdir(dirname(f))
    if 'b' in m: return open(f,m)
    return open(f,m,encoding=encoding)

TMP = os.getenv('TEMP').strip('\\') + '\\'
def gtmp(suf=''): return TMP + 'tmp' + os.urandom(8).hex() + suf
class TmpDir:
    def __init__(self,mdir=True):
        self.p = gtmp()
        if mdir: self.mkdir()
    def mkdir(self): mkdir(self.p)
    def destroy(self):
        try: rmdir(self.p)
        except FileNotFoundError: pass
    def __str__(self): return self.p
    def __add__(self,i): return self.p + i
    def __radd__(self,i): return i + self.p
    def __del__(self): self.destroy()
class TmpFile:
    def __init__(self,suf=''): self.p = gtmp(suf)
    def link(self,i): symlink(i,self.p)
    def copy(self,i): cp(i,self.p)
    def destroy(self):
        try: os.remove(self.p)
        except FileNotFoundError: pass
    def __str__(self): return self.p
    def __add__(self,i): return self.p + i
    def __radd__(self,i): return i + self.p
    def __del__(self): self.destroy()
class OSJump:
    def __init__(self): self.p = os.getcwd()
    def jump(self,i): os.chdir(str(i))
    def back(self): os.chdir(self.p)

def extract(inp:str,out:str,t:str,db:DLDB) -> bool:
    db.print_try = True
    run = db.run
    i = inp
    o = out
    match t:
        case '7z'|'LHARC'|'MSCAB'|'BinHex'|'ISO':
            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o): return
        case 'CDI':
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o):
                for x in os.listdir(o):
                    if x.endswith('.iso'):
                        e,_,_ = run(['7z','x',o + '/' + x,'-o' + o + '/' + x.split('.')[-2],'-aoa'])
                        if not e: remove(o + '/' + x)
                return
        case 'ZIP'|'InstallShield Setup ForTheWeb':
            if open(i,'rb').read(2) == b'MZ':
                run(['7z','x',i,'-o' + o,'-aoa'])
                if os.path.exists(o + '/_INST32I.EX_'):
                    if fix_isinstext(o,db): return
                elif os.listdir(o): return
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
        case 'CUE+BIN':
            mkdir(o)
            run(['bin2iso',i,o,'-a'])
            for x in os.listdir(o):
                if x.endswith('.iso'):
                    e,_,_ = run(['7z','x',o + '/' + x,'-o' + o + '/' + x.split('-')[-1][:-4],'-aoa'])
                    if not e: remove(o + '/' + x)
            if os.listdir(o): return
        case 'VirtualBox Disk Image':
            td = TmpDir()
            run(['7z','x',i,'-o' + td,'-aoa'])
            if os.path.exists(td + '/1.img'):
                run(['7z','x',td + '/1.img','-o' + o,'-aoa'])
                td.destroy()
                if os.listdir(o): return
            td.destroy()
        case 'RAR':
            run(['unrar','x','-or','-op' + o,i])
            if os.listdir(o): return
            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o): return
        case 'StuffIt':
           e,_,_ = run(['unar','-f','-o',o,i])
           if not e: return
        case 'UPX':
            run(['upx','-d','-o',o + '/' + basename(i),i])
            if exists(o + '/' + basename(i)): return
        case 'RVZ':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if os.listdir(o):
                rename(o + '/sys',o + '/$SYS')
                copydir(o + '/files',o,True)
                return
            tf = TmpFile('.iso')
            run(['dolphintool','convert','-u',gtmp('user'),'-i',i,'-o',tf,'-f','iso'])
            if exists(tf.p):
                run(['wit','-q','X',tf,'-p','-o','-E$','-d',o])
                tf.destroy()
                fs = os.listdir(o)
                if len(fs) == 1:
                    try:
                        mv(o + '/' + fs[0] + '/sys',o + '/$SYS')
                        copydir(o + '/' + fs[0] + '/files',o,True)
                        remove(o + '/' + fs[0])
                    except:pass
                    else:return
            tf.destroy()
        case 'GameCube ISO':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if os.listdir(o):
                rename(o + '/sys',o + '/$SYS')
                copydir(o + '/files',o,True)
                return
        case 'Wii ISO':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if os.listdir(o):
                rename(o + '/sys',o + '/$SYS')
                copydir(o + '/files',o,True)
                return
            run(['wit','-q','X',i,'-p','-o','-E$','-d',o])
            fs = os.listdir(o)
            if len(fs) == 1:
                try:
                    mv(o + '/' + fs[0] + '/sys',o + '/$SYS')
                    copydir(o + '/' + fs[0] + '/files',o,True)
                    remove(o + '/' + fs[0])
                except:pass
                else:return
        case 'NCSD':
            e,_,_ = run(['3dstool','-xt01267f','cci',o + '\\DP0.bin',o + '\\DP1.bin',o + '\\DP2.bin',o + '\\DP6.bin',o + '\\DP7.bin',i,'--header',o + '\\HNCSD.bin'])
            if e: return 1

            e,_,_ = run(['3dstool','-xtf','cxi',o + '\\DP0.bin','--header',o + '\\HNCCH0.bin','--exh',o + '\\DecExH.bin','--exh-auto-key','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key','--logo',o + '\\LogoLZ.bin','--plain',o + '\\PlainRGN.bin'])
            if e: return 1
            run(['3dstool','-xtf','cfa',o + '\\DP1.bin','--header',o + '\\HNCCH1.bin','--romfs',o + '\\DecManual.bin','--romfs-auto-key'])
            run(['3dstool','-xtf','cfa',o + '\\DP2.bin','--header',o + '\\HNCCH2.bin','--romfs',o + '\\DecDLPlay.bin','--romfs-auto-key'])
            run(['3dstool','-xtf','cfa',o + '\\DP6.bin','--header',o + '\\HNCCH6.bin','--romfs',o + '\\DecN3DSU.bin','--romfs-auto-key'])
            run(['3dstool','-xtf','cfa',o + '\\DP7.bin','--header',o + '\\HNCCH7.bin','--romfs',o + '\\DecO3DSU.bin','--romfs-auto-key'])

            remove(o + '\\DP0.bin',o + '\\DP1.bin',o + '\\DP2.bin',o + '\\DP6.bin',o + '\\DP7.bin')
            e,_,_ = run(['3dstool','-xtfu','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            if e: return 1
            run(['3dstool','-xtf','romfs',o + '\\DecManual.bin','--romfs-dir',o + '\\Manual'])
            run(['3dstool','-xtf','romfs',o + '\\DecDLPlay.bin','--romfs-dir',o + '\\DownloadPlay'])
            run(['3dstool','-xtf','romfs',o + '\\DecN3DSU.bin','--romfs-dir',o + '\\N3DSUpdate'])
            run(['3dstool','-xtf','romfs',o + '\\DecO3DSU.bin','--romfs-dir',o + '\\O3DSUpdate'])

            for x in os.listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            return
        case 'U8'|'RARC':
            run(['wszst','X',i,'-o','-R','-E$','-d',o])
            if len(os.listdir(o)) > 1 or (os.listdir(o) and not exists(o + '/wszst-setup.txt')):
                if exists(o + '/wszst-setup.txt'): remove(o + '/wszst-setup.txt')
                return
        case 'Yaz0':
            run(['wszst','DEC',i,'-o','-E$','-d',o + '\\' + tbasename(i)])
            if exists(o + '\\' + tbasename(i)): return
        case 'LZSS':
            run(['gbalzss','d',i,o + '\\' + tbasename(i)])
            if exists(o + '\\' + tbasename(i)): return
        case 'AFS':
            run(['afspacker','-e',i,o])
            if os.path.exists(noext(i) + '.json'): remove(noext(i) + '.json')
            if os.listdir(o): return
        case 'GD-ROM CUE+BIN':
            run(['buildgdi','-extract','-cue',i,'-output',o,'-ip',o + '/IP.BIN'])
            if os.listdir(o): return

        case 'VISE Installer':
            run(['quickbms',db.get('instexpl'),i,o])[2]
            if os.listdir(o): return
        case 'NSIS Installer':
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o): return

            run(['quickbms',db.get('instexpl'),i,o])[2]
            if os.listdir(o):
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
            run(['innounp','-x','-d' + o,'-y',i])
            if exists(o + '/{app}'):
                for x in os.listdir(o):
                    if x != '{app}': mv(o + '/' + x,o + '/$INSFILES/')
                copydir(o + '/{app}',o,True)
                return
        case 'MSI':
            run(['msiexec','/a',i,'/qb','TARGETDIR=' + o],getexe=False)
            if os.listdir(o): return
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o): return
        case 'InstallShield Setup':
            f = open(i,'rb')
            f.seek(943)
            if f.read(42) == b'InstallShield Self-Extracting Stub Program':
                print('Trying with custom extractor')
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
                if ofs:
                    f.close()
                    import zipfile
                    for x in ofs:
                        with zipfile.ZipFile(x[0]) as z: xopen(o + '/' + x[1],'wb').write(z.read(x[1]))
                        remove(x[0])
                    if os.path.exists(o + '/_INST32I.EX_'):
                        if fix_isinstext(o,db): return
                    else: return
            f.close()

            run(['isx',i,o])
            if exists(o + '/' + tbasename(i) + '_ext.bin'):
                remove(o)
                mkdir(o)
            elif os.listdir(o): return

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
                    if fix_isinstext(o,db): return
                else: return

            db.run(['quickbms',db.get('instexpl'),i,o])
            fs = os.listdir(o)
            if fs:
                if not 'SETUP.EXE' in fs and not 'Setup.ini' in fs and not 'MSIEng.isc' in fs: return
                if 'MSIEng.isc' in fs:
                    ret = False
                    for x in fs:
                        if not x.lower().endswith('.msi'): continue
                        r = extract(o + '/' + x,o + '/' + noext(x),'MSI',db)
                        if x[0] != '{' and not '}.' in x: ret = ret or r
                    if not ret: return
                elif fix_isinstext(o,db): return
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
            osj.jump(td)
            e,_,_ = run(['i5comp','x','-rof',i])
            osj.back()
            if not e and os.listdir(td.p):
                copydir(td,o)
                td.destroy()
                return
            td.destroy()

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
        case 'Stirling Compressed':
            run(["deark","-od",o,i])
            fs = os.listdir(o)
            for x in fs:
                if x.startswith('output.') and len(x.rsplit('.',1)[0]) > 10: move(o + '/' + x,o + '/' + x.split('.',2)[2])
            if fs: return

        case 'Windows Help File':
            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o):
                for x in os.listdir(o):
                    xp = o + '/' + x
                    if x[0] in '$#': remove(xp)
                return

        case 'F-Zero G/AX .lz':
            td = TmpDir()
            tf = td + '/file.lz'
            symlink(i,tf)
            run(['gxpand','unpack',td,o])
            if os.path.exists(o + '/file,lz'):
                td.destroy()
                rename(o + '/file,lz',o + '/' + tbasename(i))
                return
            remove(tf)
            ouf = open(tf,'wb')
            inf = open(i,'rb')
            ouf.write((inf.read(1)[0] - 8).to_bytes(1,'little'))
            ouf.write(inf.read())
            ouf.close()
            inf.close()
            run(['gxpand','unpack',td,o])
            td.destroy()
            if os.path.exists(o + '/file,lz'):
                rename(o + '/file,lz',o + '/' + tbasename(i))
                return
        case 'GC opening.bnr':
            run(['bnrtool','decode','--bnr',i,'--image',o + '/' + tbasename(i) + '.png','--info',o + '/' + tbasename(i) + '.yaml','-f','-s'],useos=True)
            if os.path.exists(o + '/' + tbasename(i) + '.png') and os.path.exists(o + '/' + tbasename(i) + '.yaml'): return
        case 'Pokemon FSYS':
            td = TmpDir()
            osj = OSJump()
            osj.jump(td)
            run(['gcfsysd',i])
            osj.back()
            if os.listdir(td.p):
                copydir(td,o,True)
                return
            td.destroy()
        case 'RetroStudio PAK':
            run(['paktool','-x',i,'-o',o])
            if os.listdir(o): return
        case 'CPK':
            run(['cpkextract',i,o])
            if os.listdir(o): return
        case 'Sonic AMB':
            run(['quickbms',db.get('sonic4'),i,o])
            if os.listdir(o): return
        case 'Level5 ARC'|'Level5 XPCK':
            run(['3ds-xfsatool','-i',i,'-o',o,'-q'])
            if os.listdir(o): return
    return 1

def fix_isinstext(o:str,db:DLDB):
    ret = True
    fs = os.listdir(o)
    if exists(o + '/_INST32I.EX_'):
        mkdir(o + '/_INST32I_EX_')
        extract(o + '/_INST32I.EX_',o + '/_INST32I_EX_','Stirling Compressed',db)

    for x in fs:
        x = x.upper()
        if x in ['_SETUP.LIB','DATA.Z'] or (x.startswith('_SETUP.') and x.endswith(('0','1','2','3','4','5','6','7','8','9'))):
            mkdir(o + '/' + x.replace('.','_'))
            r = not extract(o + '\\' + x,o + '\\' + x.replace('.','_'),'InstallShield Z',db)
            if not r: print("Could not extract",x)
            ret = ret and r
        elif x.startswith(('_SYS','_USER','DATA')) and x.endswith('.CAB'):
            mkdir(o + '/' + tbasename(x))
            r = not extract(o + '\\' + x,o + '\\' + tbasename(x),'InstallShield Archive',db)
            if not r: print("Could not extract",x)
            ret = ret and r

    if ret:
        for x in fs: remove(o + '/' + x)
        for x in os.listdir(o):
            if not isdir(o + '/' + x) or x.upper() == '_INST32I_EX_': continue
            while True:
                try: copydir(o + '/' + x,o,True);break
                except PermissionError: pass
    return ret
