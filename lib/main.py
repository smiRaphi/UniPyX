import re,json,ast,os,sys,subprocess
from time import sleep
from shutil import rmtree,copytree,copyfile
from lib.dldb import DLDB

TRIDR = re.compile(r'(\d{1,3}\.\d)% \(.*\) (.+) \(\d+(?:/\d+){1,2}\)')
EIPER1 = re.compile(r'Overlay : +(.+) > Offset : [\da-f]+h')

isfile,isdir,exists = os.path.isfile,os.path.isdir,os.path.exists
basename,dirname,splitext,realpath = os.path.basename,os.path.dirname,os.path.splitext,os.path.realpath
abspath = realpath
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
    f = os.path.realpath(str(f))
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
    def __init__(self,suf='',name=''): self.p = TMP + (name or (os.urandom(8).hex() + suf))
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

TDB:dict = json.load(xopen('lib/tdb.json'))
DDB:list[dict] = json.load(xopen('lib/ddb.json'))
TDBF = set(sum(TDB.values(),[]))
db = DLDB()

def cleanp(i:str):
    i = i.replace('/','\\').rstrip('\\')
    while i.endswith('\\.'): i = i[:-1].rstrip('\\')
    while i.startswith('.\\'): i = i[1:].lstrip('\\')
    i = i.replace('\\.\\','\\')
    return os.path.realpath(i)
def checktdb(i:list):
    o = []
    for x in i:
        if not x.lower() in TDBF: continue
        for t in TDB:
            if x.lower() in TDB[t]: o.append(t)
    return o
def analyze(inp:str,raw=False):
    opt = db.print_try
    db.print_try = False
    inp = cleanp(inp)
    _,o,_ = db.run(['trid','-n:5',inp])
    ts = [x[1] for x in TRIDR.findall(o) if float(x[0]) >= 10]
    _,o,_ = db.run(['file','-bnNkm',os.path.dirname(db.get('file')) + '\\magic.mgc',inp])
    ts += [x.split(',')[0].split(' created: ')[0].strip() for x in o.strip().split('\n') if x.strip() not in ['data']]

    if os.path.isfile(inp):
        f = open(inp,'rb')
        if f.read(2) == b'MZ':
            f.seek(0x3C)
            f.seek(int.from_bytes(f.read(4),'little'))
            if f.read(4) == b'PE\0\0':
                f.close()
                log = gtmp('.log')
                db.run(['exeinfope',inp + '*','/s','/log:' + log])
                for _ in range(15):
                    if os.path.exists(log) and os.path.getsize(log): break
                    sleep(0.1)
                if os.path.exists(log):
                    lg = open(log,encoding='utf-8').read().strip()
                    os.remove(log)
                    m = EIPER1.search(lg)
                    if m: ts.append(m[1])
                    for x in lg.split('\n')[0].split(' - ')[1:]: ts.append(x.split('(')[0].split('[')[0].strip(' ,!:;'))
            else: f.close()
        else: f.close()

    nts = checktdb(ts)
    nts = list(set(nts))
    for x in DDB:
        if 'rq'  in x and not (x['rq']  in nts or (x['rq']  == None and not nts)): continue
        if 'rqr' in x and not (x['rqr'] in ts  or (x['rqr'] == None and not ts )): continue
        ret = False
        if x['d'] == 'py':
            lc = {}
            try:
                exec('def check(inp):\n\t' + x['py'].replace('\n','\n\t'),globals={'os':os,'dirname':dirname,'basename':basename},locals=lc)
                if lc['check'](inp):
                    if x.get('s'): nts = [x['rs']]
                    else: nts.append(x['rs'])
            except:
                print(x)
                raise
        elif x['d'] == 'ps':
            env = os.environ.copy()
            env['input'] = inp
            p = subprocess.Popen(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',x['ps']],env=env,stdout=-1)
            p.wait()
            ret = p.stdout.read().decode(errors='ignore').strip() == 'True'
        elif x['d']['c'] == 'ext': ret = inp.lower().endswith(x['d']['v'])
        elif x['d']['c'] == 'name': ret = basename(inp) == x['d']['v']
        elif os.path.isfile(inp):
            if x['d']['c'] == 'contain':
                cv = ast.literal_eval('"' + x['d']['v'].replace('"','\\"') + '"').encode('latin1')
                f = open(inp,'rb')
                sp = x['d']['r'][0]
                if sp < 0: sp = f.seek(0,2) + sp
                if sp < 0: sp = 0
                f.seek(sp)
                ret = cv in f.read(x['d']['r'][1])
                f.close()
            elif x['d']['c'] == 'isat':
                f = open(inp,'rb')
                ret = True
                for ix in range(len(x['d']['v'])//2):
                    cv = ast.literal_eval('"' + x['d']['v'][ix*2].replace('"','\\"') + '"').encode('latin1')
                    sp = x['d']['v'][ix*2 + 1]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = ret and f.read(len(cv)) == cv
                f.close()
        if ret:
            if x.get('s'):
                nts = [x['rs']]
                break
            else: nts.append(x['rs'])
    if not raw and not nts: print(ts)

    db.print_try = opt
    if raw: return nts,ts
    return nts

def extract(inp:str,out:str,t:str) -> bool:
    db.print_try = True
    run = db.run
    i = inp
    o = out

    def quickbms(scr,inp=None):
        inf = inp or i
        if db.print_try: print('Trying with',scr)
        run(['quickbms',db.get(scr),inf,o],print_try=False)
        if os.listdir(o): return
        return 1

    match t:
        case '7z'|'LHARC'|'MSCAB'|'BinHex'|'Windows Help File'|'ARJ'|'ZSTD':
            _,_,e = run(['7z','x',i,'-o' + o,'-aou'])
            if 'ERROR: Unsupported Method : ' in e and open(i,'rb').read(2) == b'MZ':
                rmtree(o,True)
                mkdir(o)
                opt = db.print_try
                db.print_try = False
                if opt: print('Trying with input')
                run([i,'x','-o' + o,'-y'])
                db.print_try = opt
            if os.listdir(o): return
        case 'PDF':
            run(['pdfdetach','-saveall','-o',o + '\\out',i])
            run(['pdfimages','-j',i,o + '\\img'])
            run(['pdftohtml','-embedbackground','-meta','-overwrite','-q',i,o + '\\html'])
            if os.listdir(o + '/html'): return
            remove(o + '/html')
        case 'ISO'|'IMG'|'Floppy Image'|'CDI CUE+BIN'|'CDI'|'UDF':
            td = 'tmp' + os.urandom(8).hex()
            osj = OSJump()
            osj.jump(dirname(i))
            run(['aaru','filesystem','extract',i,td])
            td = os.path.realpath(td)
            osj.back()
            if os.listdir(td):
                td1 = td + '/' + os.listdir(td)[0]
                copydir(td1 + '/' + os.listdir(td1)[0],o)
                remove(td)
                return
            remove(td)

            run(['7z','x',i,'-o' + o,'-aou'])
            if os.listdir(o): return
        case 'CUE+BIN':
            if not extract(i,o,'ISO'): return
            tf = TmpFile('.iso')
            run(['bin2iso',i,tf,'-a'])
            if exists(tf.p):
                main_extract(i,o)
                tf.destroy()
                if os.listdir(o): return
        case 'Apple Disk Image'|'Mac HFS Image':
            from threading import Thread
            from queue import Queue,Empty

            def readl(out,queue):
                for l in iter(out.readline,b''): queue.put(l)
                out.close()

            if db.print_try: print('Trying with hfsexplorer')
            ce = os.environ.copy()
            ce['PATH'] += ';' + dirname(db.get('hfsexplorer'))
            td = TmpDir()
            p = subprocess.Popen(['java','--enable-native-access=ALL-UNNAMED','-cp',db.get('hfsexplorer'),'org.catacombae.hfsexplorer.HFSExplorer','-apm','browse',i],cwd=td.p,env=ce,stdout=-1,stderr=-3,stdin=-1,bufsize=1,close_fds=False)
            qo = Queue()
            t = Thread(target=readl,args=(p.stdout,qo))
            t.daemon = True
            t.start()
            def sin(i:bytes):
                p.stdin.write(i)
                try: p.stdin.flush()
                except OSError: pass

            ps = []
            while p.poll() is None:
                for _ in range(3):
                    try: l = qo.get_nowait().decode().rstrip();break
                    except Empty:sleep(0.1)
                else:break
                print(l)
                if l.startswith('Partition ') and 'HFS' in l: ps.append((int(l.split()[1][:-1]),l.split('"')[1]))
                elif ps: break

            for sp in ps:
                def xfold():
                    fs = []
                    while p.poll() is None:
                        for _ in range(3):
                            try: l = qo.get_nowait().decode().rstrip();break
                            except Empty:sleep(0.1)
                        else:break
                        print(l)
                        if l.startswith('  [org.catacombae.'): fs.append((int(l.split('@')[1].split(']')[0],16),l[-2] == '/'))
                        elif l.startswith('  [Folder Thread: '): base = str(int(l.split('@')[1].split(']')[0],16)).encode()
                        elif l.startswith('Listing files in "'): basen = l.split('"')[1].strip('/\\')
                        elif fs: break
                    while p.poll() is None:
                        for f in fs:
                            while p.poll() is None:
                                try:l = qo.get_nowait()
                                except Empty:break
                                print(l)
                            if f[1]:
                                sin(b'cdn ' + str(f[0]).encode() + b'\r\n')
                                xfold()
                                while p.poll() is None:
                                    try:l = qo.get_nowait()
                                    except Empty:break
                                    print(l)
                                sin(b'cdn ' + base + b'\r\n')
                            else:
                                sin(b'info ' + str(f[0]).encode() + b'\r\n')
                                while p.poll() is None:
                                    try:l = qo.get_nowait()
                                    except Empty:break
                                    print(l)
                                sin(b'extract ' + str(f[0]).encode() + b'\r\n')
                                while p.poll() is None:
                                    try:l = qo.get_nowait()
                                    except Empty:break
                                    print(l)
                                while not os.listdir(td.p): sleep(0.1)
                                move(td.p + '/' + os.listdir(td.p)[0],o + '/' + sp[1] + '/' + basen + '/')

                while p.poll() is None:
                    try:l = qo.get_nowait()
                    except Empty:break
                    print(l)
                sin(str(sp[0]).encode() + b'\r\n')
                xfold()
                while p.poll() is None:
                    try:l = qo.get_nowait()
                    except Empty:break
                    print(l)
                sin(b'q\r\n')

            p.kill()
            p.stdin.close()
            t.join()
            qo.shutdown(True)
            td.destroy()
        case 'CHD':
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
        case 'StuffIt':
           e,_,_ = run(['unar','-f','-o',o,i])
           if not e: return
        case 'UPX':
            run(['upx','-d','-o',o + '/' + basename(i),i])
            if exists(o + '/' + basename(i)): return
        case 'RVZ':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if os.listdir(o):
                if exists(o + '/DATA'):
                    for sd in os.listdir(o):
                        rename(o + '/' + sd + '/sys',o + '/' + sd + '/$SYS')
                        for sf in os.listdir(o + '/' + sd):
                            if sf in ['$SYS','files']: continue
                            remove(o + '/' + sd + '/' + sf)
                        copydir(o + '/' + sd + '/files',o + '/' + sd,True)
                        if sd == 'DATA': copydir(o + '/DATA',o,True)
                        else: rename(o + '/' + sd,o + '/$' + sd)
                else:
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
        case 'Wii ISO'|'GameCube ISO':
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
        case 'NSP':
            bcd = ['hac2l','-t','pfs','--disablekeywarns','-k',db.get('prodkeys'),'--titlekeys=' + db.get('titlekeys')]
            _,e,_ = run(bcd + [i],print_try=False)
            bcd += ['--exefsdir=' + o + '\\ExeFS','--romfsdir=' + o + '\\RomFS']
            if ' MetaType=Patch ' in e:
                pinf = re.search(r'ProgramId=([\dA-F]+), Version=0x([\dA-F]+),',e)
                pid,pv = pinf[1],int(pinf[2],16)
                for x in os.listdir(dirname(i)):
                    if pid in x and x.endswith('.nsp'):
                        try: v = int(re.search(r'v(\d+)(?:\b|_)(?!\.)',x)[1])
                        except: v = 0
                        if v < pv: bf = dirname(i) + '\\' + x;break
                else: return 1
                bcd += ['--basepfs',bf]
            run(bcd + [i])
            if os.listdir(o) and os.listdir(o + '/ExeFS') and os.listdir(o + '/RomFS'): return
        case 'NDS':
            run(['mdnds','e',i,o])
            if os.listdir(o): return
        case 'PS4 PKG':
            td = TmpDir()
            rtd = TmpDir()
            run(['ps4pkg','img_extract','--passcode','00000000000000000000000000000000','--tmp_path',rtd,i,td])
            rtd.destroy()
            if os.path.exists(td + '/Image0') and os.listdir(td + '/Image0'):
                copydir(td + '/Image0',o)
                mv(td + '/Sc0',o + '/sce_sys')
                td.destroy()
                return
            td.destroy()
        case 'PS3 ISO':
            from bin.ps3key import PS3Keys
            k = PS3Keys().get(i)
            tf = TmpFile('.iso')
            tf.link(i)
            run(['ps3dec','--iso',tf,'--dk',k,'--tc','16','--skip'])
            rmdir('log')
            tf.destroy()
            if os.path.exists(tf.p + '_decrypted.iso'):
                if not extract(tf.p + '_decrypted.iso',o,'ISO'):
                    remove(tf.p + '_decrypted.iso')
                    return
                remove(tf.p + '_decrypted.iso')
            if not extract(i,o,'ISO'): return
        case 'PSVita PKG':
            import zlib,base64
            if exists(dirname(i) + '/work.bin'):
                ZRIF_DICT = zlib.decompress(base64.b64decode(b"eNpjYBgFo2AU0AsYAIElGt8MRJiDCAsw3xhEmIAIU4N4AwNdRxcXZ3+/EJCAkW6Ac7C7ARwYgviuQAaIdoPSzlDaBUo7QmknIM3ACIZM78+u7kx3VWYEAGJ9HV0="))
                rif = open(dirname(i) + '/work.bin','rb').read()
                c = zlib.compressobj(level=9,wbits=10,memLevel=8,zdict=ZRIF_DICT)
                bn = c.compress(rif)
                bn += c.flush()
                if len(bn) % 3: bn += bytes(3 - len(bn) % 3)
                zrif = base64.b64encode(bn).decode()
            else: return 1

            osj = OSJump()
            osj.jump(o)
            run(['pkg2zip','-x',i,zrif])
            if exists('app') and os.listdir('app') and os.listdir('app/' + os.listdir('app')[0]):
                td = o + '/app/' + os.listdir('app')[0]
                osj.back()

                run(['psvpfsparser','-i',td,'-o',o,'-z',zrif])
                rmtree(o + '/app')

                if os.listdir(o): return
        case 'WUX':
            from bin.wiiudk import DKeys
            cmd = ['java','-jar',db.get('jwudtool'),'-commonkey','d7b00402659ba2abd2cb0db27fa2b656','-decrypt','-in',i,'-out',o]
            k = DKeys().get(i)
            if not k: cmd.append('-dev')
            else: cmd += ['-titleKey',k]
            if db.print_try: print('Trying with jwudtool')
            run(cmd,print_try=False)
            if os.listdir(o):
                for x in os.listdir(o):
                    try:
                        if not x.startswith('GM'): remove(o + '/' + x);continue
                        if not exists(o + '/' + x + '/content'): remove(o + '/' + x);continue
                        copydir(o + '/' + x,o,True)
                    except PermissionError: pass
                return
        case 'XISO':
            run(['xdvdfs','unpack',i,o])
            if os.listdir(o): return
        case 'U8'|'RARC':
            run(['wszst','X',i,'--max-file-size=2g','-o','-R','-E$','-d',o])
            if len(os.listdir(o)) > 1 or (os.listdir(o) and not exists(o + '/wszst-setup.txt')):
                if exists(o + '/wszst-setup.txt'): remove(o + '/wszst-setup.txt')
                return
        case 'Yaz0':
            run(['wszst','DEC',i,'-o','-E$','-d',o + '\\' + tbasename(i)])
            if exists(o + '\\' + tbasename(i)): return
        case 'LZSS'|'LZ77':
            run(['gbalzss','d',i,o + '\\' + tbasename(i)])
            if exists(o + '\\' + tbasename(i)): return
        case 'AFS':
            run(['afspacker','-e',i,o])
            if os.path.exists(noext(i) + '.json'): remove(noext(i) + '.json')
            if os.listdir(o): return
        case 'GD-ROM CUE+BIN':
            run(['buildgdi','-extract','-cue',i,'-output',o,'-ip',o + '/IP.BIN'])
            if os.listdir(o): return
        case 'NDS Sound Data':
            td = TmpDir()
            tf = td + '\\' + 'tmp' + os.urandom(8).hex() + '.sdat'
            symlink(i,tf)
            run(['ndssndext','-x',tf])
            remove(tf)
            if os.listdir(td.p):
                copydir(td + '/' + os.listdir(td.p)[0],o)
                td.destroy()
                return
            td.destroy()

        case 'Qt IFW':
            from signal import SIGTERM
            from winpty import PtyProcess
            bk = os.environ.get('__COMPAT_LAYER')
            os.environ['__COMPAT_LAYER'] = 'RUNASINVOKER'
            if db.print_try: print('Trying with input')

            p = PtyProcess.spawn(subprocess.list2cmdline([db.get('winpty'),i,'--nf','--ns','--am','--al','--lang','en','--cp',o + '\\$CACHE','-t',o,'-g','ifw.installer.installlog=true','in']))
            p.write('Yes\r\n')
            while p.isalive():
                try: l = p.readline()
                except EOFError: break
                if l.split(b']',1)[-1].strip().startswith(b'Installing component'): p.kill(SIGTERM)

            if bk != None: os.environ['__COMPAT_LAYER'] = bk
            else: del os.environ['__COMPAT_LAYER']
            fs = os.listdir(o)
            if fs:
                if 'InstallationLog.txt' in fs:
                    remove(o + '/InstallationLog.txt')
                    fs.remove('InstallationLog.txt')
                if '$CACHE' in fs: fs.remove('$CACHE')
                if fs: return
                remove(o)
                mkdir(o)
        case 'MSCAB SFX':
            run(['7z','x',i,'-o' + o,'-aoa'])
            if os.listdir(o): return

            bk = os.environ.get('__COMPAT_LAYER')
            os.environ['__COMPAT_LAYER'] = 'RUNASINVOKER'
            if db.print_try: print('Trying with input (/X)')
            run([i,'/X:' + o,'/Q','/C'],print_try=False)
            if bk != None: os.environ['__COMPAT_LAYER'] = bk
            else: del os.environ['__COMPAT_LAYER']
            for _ in range(50):
                if os.listdir(o): return
                sleep(0.1)

            bk = os.environ.get('__COMPAT_LAYER')
            os.environ['__COMPAT_LAYER'] = 'RUNASINVOKER'
            if db.print_try: print('Trying with input (/T)')
            run([i,'/T:' + o,'/Q'],print_try=False)
            if bk != None: os.environ['__COMPAT_LAYER'] = bk
            else: del os.environ['__COMPAT_LAYER']
            for _ in range(50):
                if os.listdir(o): return
                sleep(0.1)
        case 'VISE Installer': return quickbms('instexpl')
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
            run(['innoextract','-e','-q','--iss-file','-g','-d',o,i])
            if os.listdir(o):
                for x in os.listdir(o):
                    if x != 'app': mv(o + '/' + x,o + '/$INSFILES/' + x)
                if exists(o + '/app'): copydir(o + '/app',o,True)
                return
            run(['innounp','-x','-d' + o,'-y',i])
            if exists(o + '/{app}'):
                for x in os.listdir(o):
                    if x != '{app}': mv(o + '/' + x,o + '/$INSFILES/')
                copydir(o + '/{app}',o,True)
                return
        case 'FitGirl Installer':
            for x in os.listdir(dirname(i)):
                if x.startswith('fg-') and x.endswith('.bin'):
                    try: n = int(x[3:-4])
                    except: n = None
                    if n == 1: mf = x;break
            else: return 1

            td = TmpDir()
            run(['innoextract','-e','-q','-d',td,i])
            remove(td + '/tmp/cls-srep.dll',td + '/tmp/cls-srep_x64.exe',td + '/tmp/cls-srep_x86.exe')
            copydir(dirname(db.get('cls-srep')),td + '/tmp')
            run(['unarc-cpp',td + '\\tmp\\unarc.dll','x','-o+','-dp' + o,'-w' + td + '\\tmp','-cfgarc.ini',dirname(i) + '\\' + mf],cwd=td.p + '\\tmp')
            td.destroy()

            def find_file(o):
                for x in os.listdir(o):
                    x = o + '/' + x
                    if isfile(x) or find_file(x): return 1
            if find_file(o): return
            remove(o)
            mkdir(o)
        case 'MSI':
            td = TmpDir()
            run(['msiexec','/a',i,'/qn','/norestart','TARGETDIR=' + td],getexe=False)
            copydir(td,o)
            td.destroy()
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
                if ofs:
                    f.close()
                    import zipfile
                    for x in ofs:
                        with zipfile.ZipFile(x[0]) as z: xopen(o + '/' + x[1],'wb').write(z.read(x[1]))
                        remove(x[0])
                    if os.path.exists(o + '/_INST32I.EX_'):
                        if fix_isinstext(o): return
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
                    if fix_isinstext(o): return
                else: return

            quickbms('instexpl')
            fs = os.listdir(o)
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
                    open(o + '/' + str(c) + '.exe','wb').write(f.read(siz))
                    f.seek(-f.tell() % 16,1)
                    if f.tell() >= ts: f.seek(sp + 64)
                    c += 1
            if c:
                for ix in range(c):
                    if main_extract(o + f'/{ix}.exe',o + f'/{ix}') and not os.listdir(o + f'/{ix}'): remove(o + f'/{ix}')
                    else: remove(o + f'/{ix}.exe')
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
        case 'BRSAR':
            run(['mrst','extract','-o',o,i])
            if os.listdir(o): return
        case 'ROFS Volume':
            tf = TmpFile('.iso')
            run(['cvm_tool','split',i,tf])
            extract(tf,o,'ISO')
            tf.destroy()
        case 'RetroStudio PAK':
            run(['paktool','-x',i,'-o',o])
            if os.listdir(o): return
        case 'CPK':
            run(['cpkextract',i,o])
            if os.listdir(o): return
        case 'CRI CPK': return quickbms('cpk')
        case 'Sonic AMB': return quickbms('sonic4')
        case 'Level5 ARC'|'Level5 XPCK':
            run(['3ds-xfsatool','-i',i,'-o',o,'-q'])
            if os.listdir(o): return
        case 'NDS SWAR':
            raise NotImplementedError
        case 'Iron Sky GPK':
            fs = []
            for x in re.findall(r'<File((?: \w+="\w{3}: [^"]*")+)\s*/>',open(i,encoding='utf-8').read()):
                tfs = {}
                for y in re.findall(r'(\w+)="(\w{3}): ([^"]*)"',x):
                    if y[1] in ['U16','U32','U64']: tfs[y[0]] = int(y[2])
                    elif y[1] == 'BOL': tfs[y[0]] = bool(int(y[2]))
                    else: tfs[y[0]] = y[2]
                fs.append(tfs)
            ofl = {}
            bid = dirname(i) + '/'
            for x in fs:
                if not x['source'] in ofl: ofl[x['source']] = open(bid + x['source'],'rb')
                ofl[x['source']].seek(x['offset'])
                xopen(o + '/' + x['alias'],'wb').write(ofl[x['source']].read(x['size']))
                if x['compression'] != 'CM_STORE' or x['size'] != x['originalSize']: print('Unknown compression',x)
            for x in ofl: ofl[x].close()
            return
        case 'NUB2': return quickbms('nus3_nub2')
        case 'CTPK':
            run(['ctpktool','-efd',i,o])
            if os.listdir(o): return
        case 'Rob Northen Compression':
            run(['ancient','decompress',i,o + '/' + basename(i)])
            if os.path.exists(o + '/' + basename(i)) and os.path.getsize(o + '/' + basename(i)): return
        case 'XBP': return quickbms('xbp')
        case 'Bezel Archive': return quickbms('bea')
        case 'PlayStation Archive':
            run(['psarc','extract','--input='+i,'--to='+o])
            if os.listdir(o): return
        case 'Unity Bundle':
            if db.print_try: print('Trying with assetripper')
            run([sys.executable,dirname(db.get('assetripper')) + '\\client.py',i,o],print_try=False)
            if os.listdir(o): return
        case 'Unity Assets':
            b = basename(i).lower()
            if b.startswith('sharedassets') and '.assets.split' in b and b[-1].isdigit():
                bn = b.rstrip('0123456789')
                fs = []
                for x in os.listdir(dirname(i)):
                    if x.startswith(bn): fs.append((dirname(i) + '/' + x,int(x[len(bn):])))
                tf = dirname(i) + '\\' + os.urandom(8).hex() + '.assets'
                with open(tf,'wb') as f:
                    for x in sorted(fs,key=lambda x:x[1]): f.write(open(x[0],'rb').read())
                r = extract(tf,o,'Unity Bundle')
                remove(tf)
            else: r = extract(i,o,'Unity Bundle')
            if not r: return
        case 'Rayman DCZ': return quickbms('rayman_dcz')
        case 'iQiyi PAK':
            run(['iqipack',i,o])
            if os.listdir(o): return
        case 'LEGO JAM': return quickbms('legoracer_jam')
        case 'Metroid Samus Returns PKG': return quickbms('metroid_sr_3ds')
        case 'DDR DAT':
            MODS = ['SLUS_213.77','SLES_551.97','SLUS_217.67','SLUS_219.17']

            for x in os.listdir(dirname(i)):
                if x.upper() in MODS: ex = dirname(i) + '\\' + x;break
            else:
                for x in os.listdir(dirname(dirname(i))):
                    if x.upper() in MODS: ex = dirname(dirname(i)) + '\\' + x;break
                else: return 1

            osj = OSJump()
            tf1,tf2 = TmpFile(name=basename(i).upper()),TmpFile(name=basename(ex).upper())
            tf1.link(i),tf2.link(ex)
            osj.jump(TMP)
            r = quickbms('ddr_dat',tf2)
            osj.back()
            tf1.destroy(),tf2.destroy()
            return r
        case 'Allegro DAT':
            run(['allegro_dat','-e','-o',o + '\\',i,'*\\'])
            if os.listdir(o): return

        case 'Ridge Racer V A':
            tf = dirname(i) + '\\rrv3vera.ic002'
            if os.path.exists(tf): remove(tf)
            symlink(db.get('rrv3va'),tf)

            cfp = dirname(db.get('rrvatool')) + '/RidgeRacerVArchiveTool.exe.config'
            d = open(cfp).read().replace('<value>True</value>','<value>False</value>')
            open(cfp,'w').write(d.replace('<setting name="ACV3Achecked" serializeAs="String">\n                <value>False</value>','<setting name="ACV3Achecked" serializeAs="String">\n                <value>True</value>'))
            if db.print_try: print('Trying with rrvatool')
            p = subprocess.Popen([db.get('rrvatool'),i],stdout=-1,stderr=-1)
            sleep(1)
            
            while not os.listdir(i + '_extract'): sleep(0.1)
            while True:
                try:copydir(i + '_extract',o,True)
                except:sleep(0.1)
                else:break
            p.kill()
            remove(tf)

            for x in os.listdir(o):
                if not os.path.getsize(o + '/' + x): remove(o + '/' + x)

            if os.listdir(o): return
    return 1
def fix_isinstext(o:str):
    ret = True
    fs = os.listdir(o)
    if exists(o + '/_INST32I.EX_'):
        mkdir(o + '/_INST32I_EX_')
        extract(o + '/_INST32I.EX_',o + '/_INST32I_EX_','Stirling Compressed')

    for x in fs:
        x = x.upper()
        if x in ['_SETUP.LIB','DATA.Z'] or (x.startswith('_SETUP.') and x.endswith(('0','1','2','3','4','5','6','7','8','9'))):
            mkdir(o + '/' + x.replace('.','_'))
            r = not extract(o + '\\' + x,o + '\\' + x.replace('.','_'),'InstallShield Z')
            if not r: print("Could not extract",x)
            ret = ret and r
        elif x.startswith(('_SYS','_USER','DATA')) and x.endswith('.CAB'):
            mkdir(o + '/' + tbasename(x))
            r = not extract(o + '\\' + x,o + '\\' + tbasename(x),'InstallShield Archive')
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

def main_extract(inp:str,out:str,ts:list[str]=None,quiet=True,rs=False):
    out = cleanp(out)
    assert not exists(out),'Output directory already exists'
    inp = cleanp(inp)
    if ts == None: ts = analyze(inp)
    assert ts,'Unknown file type'

    for x in ts:
        if not quiet: print('Trying format',x)
        mkdir(out)
        try:
            if not extract(inp,out,x):break
        except:
            if not os.listdir(out): os.rmdir(out)
            raise
        rmtree(out)
    else:
        if rs: raise Exception("Could not extract")
        return
    if not quiet: print('Extracted successfully to',out)
