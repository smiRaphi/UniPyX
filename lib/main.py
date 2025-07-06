import os
from lib.dldb import DLDB
from shutil import move,rmtree,copytree,copyfile

isfile,isdir,exists = os.path.isfile,os.path.isdir,os.path.exists
basename,dirname,splitext = os.path.basename,os.path.dirname,os.path.splitext
symlink = os.symlink
mv = move
def tbasename(i:str): return splitext(basename(str(i)))[0]
def extname(i:str): return splitext(str(i))[1]
def noext(i:str): return splitext(str(i))[0]
def mkdir(i:str): os.makedirs(i,exist_ok=True)
def rmdir(i:str,r=True): rmtree(i) if r else os.rmdir(i)
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
    for x in os.listdir(i): cp(i + '/' + x,o + '/' + x)
    if delete: rmdir(i)
def remove(i:str): os.remove(i) if isfile(i) or os.path.islink(i) else rmdir(i)
def xopen(f:str,m='r',encoding='utf-8'):
    f = os.path.abspath(f)
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
    def __del__(self): self.destroy()
class TmpFile:
    def __init__(self,suf=''): self.p = gtmp(suf)
    def link(self,i): symlink(i,self.p)
    def copy(self,i): cp(i,self.p)
    def destroy(self):
        try: os.remove(self.p)
        except FileNotFoundError: pass
    def __str__(self): return self.p
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
        case '7z'|'zip'|'rar':
            run(['7z','x',i,'-o' + o])
            if os.listdir(o): return

        case 'VISE Installer':
            run(['quickbms',db.get('instexpl'),i,o])[2]
            if os.listdir(o): return
        case 'InstallShield Setup':
            tf = TmpFile(extname(i))
            tf.link(i)
            run(['isx',tf])
            if exists(noext(tf) + '_u/' + tbasename(tf) + '_ext.bin'): remove(noext(tf) + '_u')
            else:
                tf.destroy()
                copydir(noext(tf) + '_u',o,True)
                return

            _,po,_ = run(['isxunpack',tf],'\n')
            if not 'Not Valid All-in-One Modification of IS File' in po or not 'CAB-file NOT found in That EXE!' in po:
                raise NotImplementedError("isxunpack returned:\n" + po)
            tf.destroy()

            db.run_cmd(['quickbms',db.get('instexpl'),i,o])
            fs = os.listdir(o)
            if fs:
                if not 'SETUP.EXE' in fs: return
                ret = False
                if '_INST32I.EX_' in fs:
                    mkdir(o + '/_INST32I_EX_')
                    extract(o + '/_INST32I.EX_',o + '/_INST32I_EX_','Stirling Compressed',db)
                for x in fs:
                    if x == '_SETUP.LIB' or (x.startswith('_SETUP.') and x.endswith(('0','1','2','3','4','5','6','7','8','9'))):
                        mkdir(o + '/' + x.replace('.','_'))
                        ret = ret or extract(o + '/' + x,o + '/' + x.replace('.','_'),'InstallShield Z',db)
                if not ret:
                    for x in fs: remove(o + '/' + x)
                    for x in os.listdir(o):
                        while True:
                            try: copydir(o + '/' + x,o,True);break
                            except PermissionError: pass
                    return
        case 'InstallShield Z':
            td = TmpDir()
            osj = OSJump()
            osj.jump(td)
            symlink(i,'archive.z')
            run(['icomp','archive.z','*.*','-d','-i'])
            remove('archive.z')
            osj.back()
            if not os.listdir(td.p): td.destroy()
            else:
                copydir(td.p,o)
                td.destroy()
                return
        case 'Stirling Compressed':
            run(["deark","-od",o,i])
            fs = os.listdir(o)
            for x in fs:
                if x.startswith('output.') and len(x.rsplit('.',1)[0]) > 10: move(o + '/' + x,o + '/' + x.split('.',2)[2])
            if fs: return

    return 1
