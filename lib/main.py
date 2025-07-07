import os
from lib.dldb import DLDB
from shutil import move,rmtree,copytree,copyfile

isfile,isdir,exists = os.path.isfile,os.path.isdir,os.path.exists
basename,dirname,splitext = os.path.basename,os.path.dirname,os.path.splitext
symlink,rename = os.symlink,os.rename
mv = move
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
def copydir(i:str,o:str,delete=False):
    mkdir(o)
    for x in os.listdir(str(i)): cp(i + '/' + x,o + '/' + x)
    if delete: rmdir(i)
def remove(i:str): os.remove(i) if isfile(i) or os.path.islink(i) else rmdir(i)
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
        case '7z'|'ZIP'|'LHARC'|'MSCAB':
            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o): return
        case 'RAR':
            run(['unrar','x','-or','-op' + o,i])
            if os.listdir(o): return
            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o): return
        case 'StuffIt':
           e,_,_ = run(['unar','-f','-o',o,i])
           if not e: return

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
        case 'Stirling Compressed':
            run(["deark","-od",o,i])
            fs = os.listdir(o)
            for x in fs:
                if x.startswith('output.') and len(x.rsplit('.',1)[0]) > 10: move(o + '/' + x,o + '/' + x.split('.',2)[2])
            if fs: return

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
