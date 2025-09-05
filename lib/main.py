import re,json,ast,os,sys,subprocess,hashlib
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
    ts += [x.split(',')[0].split(' created: ')[0].split('\\012-')[0].strip() for x in o.split('\n') if x.strip()]

    if isdir(inp): typ = 'directory'
    else:
        idt = open(inp,'rb').read(0x4000)
        isz = sum(idt) != 0
        try: idt = idt.decode('utf-8')
        except: typ = 'binary'
        else:
            if isz: typ = 'text'
            else: typ = 'binary'
        if ('null data' in ts or 'null bytes' in ts) and typ == 'binary' and not isz: typ = 'null'

    if 'data' in ts: ts.remove('data')
    if 'null data' in ts: ts.remove('null data')
    if 'null bytes' in ts: ts.remove('null bytes')
    if 'directory' in ts: ts.remove('directory')

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
                    for x in lg.split('\n')[0].split(' - ')[1:]:
                        if x == '( RESOURCES ONLY ! no CODE )': ts.append('Resources Only')
                        else:
                            x = x.split('(')[0].split('[')[0].split(' -> OVL Offset : ')[0].split(' > section : ')[0].split(' , size : ')[0].strip(' ,!:;')
                            if x: ts.append(x)

                yrep = db.update('yara')
                yp = os.path.dirname(yrep[0])
                if yrep[1]:
                    db.run([yp + '/yarac.exe','-w',yp + '/packers_peid.yar',yp + '/packers_peid.yarc'])
                    remove(yp + '/yarac.exe','-C',yp + '/packers_peid.yar')
                err,o,_ = db.run(['yara','-C',yp + '/packers_peid.yarc',inp])
                if not err: ts += [x.split()[0].replace('_',' ').strip() for x in o.split('\n') if x.strip()]
            else: f.close()
        else: f.close()

    ts = [x.strip() for x in ts if x.strip()]

    nts = checktdb(ts)
    nts = list(set(nts))
    for xv in DDB:
        if 't' in xv and xv['t'] != typ: continue
        if 'rq' in xv:
            if xv['rq'] == None:
                if nts: continue
            else:
                rq = xv['rq'] if type(xv['rq']) == list else [xv['rq']]
                chf = all if type(rq[-1]) == bool and rq[-1] else any
                if not chf(y in nts for y in rq if type(y) == str): continue
        if 'rqr' in xv:
            if xv['rqr'] == None:
                if ts: continue
            else:
                rqr = xv['rqr'] if type(xv['rqr']) == list else [xv['rqr']]
                chf = all if type(rqr[-1]) == bool and rqr[-1] else any
                if not chf(y in ts for y in rqr if type(y) == str): continue

        tret = 0
        if not 'd' in xv or not xv['d']:
            dl = []
            tret = True
        else:
            dl = xv['d']
            if type(dl[0]) != list: dl = [dl]
        for x in dl:
            if x[0] == 'py':
                lc = {}
                try:
                    exec('def check(inp):\n\t' + x[1].replace('\n','\n\t'),globals={'os':os,'dirname':dirname,'basename':basename},locals=lc)
                    ret = lc['check'](inp)
                except:
                    print(x[1])
                    raise
            elif x[0] == 'ps':
                env = os.environ.copy()
                env['input'] = inp
                p = subprocess.Popen(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',x[1]],env=env,stdout=-1)
                p.wait()
                ret = p.stdout.read().decode(errors='ignore').strip() == 'True'
            elif x[0] == 'ext': ret = inp.lower().endswith(x[1])
            elif x[0] == 'name': ret = basename(inp) == x[1]
            elif os.path.isfile(inp):
                if x[0] == 'contain':
                    cv = ast.literal_eval('"' + x[1].replace('"','\\"') + '"').encode('latin1')
                    f = open(inp,'rb')
                    sp = x[2][0]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = cv in f.read(x[2][1])
                    f.close()
                elif x[0] == 'isat':
                    f = open(inp,'rb')
                    cv = ast.literal_eval('"' + x[1].replace('"','\\"') + '"').encode('latin1')
                    sp = x[2]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = f.read(len(cv)) == cv
                    f.close()
                elif x[0] == 'size':
                    sz = os.path.getsize(inp)
                    if type(x[1]) == int: ret = sz == x[1]
                    else: ret = (x[1][0] == None or sz >= x[1][0]) and (x[1][1] == None or sz <= x[1][1])
                elif x[0] == 'hash':
                    hs = x[1].lower()
                    if len(hs) == 40: h = hashlib.sha1
                    elif len(hs) == 32: h = hashlib.md5
                    elif len(hs) == 64: h = hashlib.sha256
                    h = h()

                    f = open(inp,'rb')
                    while True:
                        cv = f.read(0x1000)
                        if not cv: break
                        h.update(cv)
                    f.close()
                    ret = h.hexdigest() == hs
                elif x[0] == 'str0':
                    f = open(inp,'rb')
                    f.seek(x[1])
                    scnt = 0
                    b = b''
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=': scnt += 1
                        elif b != b'\0': ret = False;break
                    else: ret = scnt >= x[3]
                    f.close()
            if type(x[-1]) == bool and x[-1]: tret = tret or ret
            else: tret = (tret or type(tret) != bool) and ret
            if not xv.get('noq') and not tret: break
        if tret:
            if xv.get('s'):
                nts = [xv['rs']]
                break
            else: nts.append(xv['rs'])
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
            if os.listdir(o) and not exists(o + '/.rsrc'): return
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
        case 'Apple Disk Image'|'Mac HFS Image'|'Roxio Toast IMG':
            _,e,_ = run(['aaru','filesystem','info',i],print_try=False)
            try: ps = int(re.search(r'(\d+) partitions found\.',e)[1])
            except: ps = 1

            ce = os.environ.copy()
            ce['PATH'] += ';' + dirname(db.get('hfsexplorer'))
            for p in range(ps):
                if db.print_try: print('Trying with hfsexplorer/unhfs')
                cop = o + (f'\\{p}' if ps > 1 else '')
                mkdir(cop)
                _,_,e = run(['java','--enable-native-access=ALL-UNNAMED','-cp',db.get('hfsexplorer'),'org.catacombae.hfsexplorer.tools.UnHFS','-o',cop,'-resforks','NONE','-partition',p,'--',i],print_try=False,env=ce)
                if 'Failed to create directory ' in e: return 1
                if not os.listdir(cop): rmdir(cop)
            if os.listdir(o): return
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
        case 'KryoFlux':
            tf = TmpFile('.script')
            xopen(tf,'w').write('set FLUXSTREAM_PLL_INITIAL_BITRATE 250000\n')
            _,o,_ = run(['hxcfe','-finput:' + i,'-script:' + tf,'-list'])
            tf.destroy()

            if '------- Disk Tree --------' in o:
                o = o.split('------- Disk Tree --------\n')[1].split('--------------------------\n')[0]
                if not 'ERROR -> Sector not found' in o:
                    print(o)
                    raise NotImplementedError()
        case 'BBC Micro SSD':
            run(['bbccp','-i',i,'.',o + '\\'])
            if os.listdir(o): return

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
            rtd = TmpDir()
            run(['ps4pkg','img_extract','--passcode','00000000000000000000000000000000','--tmp_path',rtd,i,o])
            rtd.destroy()
            if os.path.exists(o + '/Image0') and os.listdir(o + '/Image0'):
                fs = os.listdir(o)
                copydir(o + '/Image0',o)
                mv(o + '/Sc0',o + '/sce_sys')
                for x in fs: remove(o + '/' + x)
                return
        case 'PS5 PKG':
            rtd = TmpDir()
            run(['ps5pkg','img_extract','--passcode','00000000000000000000000000000000','--tmp_path',rtd,i,o])
            rtd.destroy()
            if os.listdir(o): raise NotImplementedError()
            if os.path.exists(o + '/Image0') and os.listdir(o + '/Image0'):
                fs = os.listdir(o)
                copydir(o + '/Image0',o)
                mv(o + '/Sc0',o + '/sce_sys')
                for x in fs: remove(o + '/' + x)
                return
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
            if exists(dirname(i) + '/work.bin'): work = dirname(i) + '/work.bin'
            elif exists(noext(i) + '.work.bin'): work = noext(i) + '.work.bin'
            else: return 1

            ZRIF_DICT = zlib.decompress(base64.b64decode(b"eNpjYBgFo2AU0AsYAIElGt8MRJiDCAsw3xhEmIAIU4N4AwNdRxcXZ3+/EJCAkW6Ac7C7ARwYgviuQAaIdoPSzlDaBUo7QmknIM3ACIZM78+u7kx3VWYEAGJ9HV0="))
            rif = open(work,'rb').read()
            c = zlib.compressobj(level=9,wbits=10,memLevel=8,zdict=ZRIF_DICT)
            bn = c.compress(rif)
            bn += c.flush()
            if len(bn) % 3: bn += bytes(3 - len(bn) % 3)
            zrif = base64.b64encode(bn).decode()

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
        case 'Xbox LIVE ROM': raise NotImplementedError()
        case 'GD-ROM CUE+BIN':
            run(['buildgdi','-extract','-cue',i,'-output',o + '\\','-ip',o + '\\IP.BIN'])
            if os.listdir(o): return
        case 'Wii TMD':
            ckey = dirname(db.get('tmd_wii')) + '/'

            if not exists(ckey + 'common.key'):
                s = db.c.get('https://wiki.wiidatabase.de/wiki/Common-Key').text
                for r,k in [('Normal','common'),
                            ('Korea' ,'korea' ),
                            ('Debug' ,'debug' )]:
                    open(ckey + k + '.key','wb').write(bytes.fromhex(re.search(f'<b>{r}:</b> *<code>([^<]+)</code>',s)[1]))

            if db.print_try: print('Trying with tmd_wii')
            from bin.tmd import TMD,derive_key,check_sha1,decrypt_content

            dr = dirname(i)
            dls = [x for x in os.listdir(dr) if os.path.isfile(dr + '/' + x)]
            if 'tmd' in dls: tmd = 'tmd'
            else: tmd = max([x for x in dls if x.startswith('tmd.')],key=lambda x:int(x.split('.')[-1]))
            tmd = TMD(dr + '/' + tmd)

            for c in tmd.contents:
                fn = hex(c.cid)[2:].zfill(8)
                odr = o + '/' + fn
                ifl = dr + '/' + fn

                if not check_sha1(ifl,c.sha1):
                    tf = TmpFile()
                    decrypt_content(ifl,tf,derive_key(tmd.titleid,1),c)
                    assert check_sha1(tf, c.sha1)
                    ifl = str(tf)

                if c.type == 2: copy(ifl,o + '/CAFEDEAD.bin')
                elif c.type == 0x8001:
                    if extract(ifl,o + '/$SHARED','U8'): copy(ifl,o + '/$SHARED/' + fn + '.bin')
                elif c.index == 0 and tmd.titleid == b'\0\0\0\1\0\0\0\2': copy(ifl,o + '/build_tag.bin')
                elif c.index == 0: copy(ifl,o + '/banner.bnr')
                elif c.index == 1: copy(ifl,o + '/launch.dol')
                elif tmd.bootindex == c.index: copy(ifl,o + '/boot.dol')
                else:
                    if open(ifl,'rb').read(4) == b'U\xAA8\x2D':
                        if extract(ifl,odr,'U8'): copy(ifl,odr + '.bin')
                    else: copy(ifl,odr + '.bin')
            return

        case 'U8'|'RARC':
            run(['wszst','X',i,'--max-file-size=2g','-o','-R','-E$','-d',o])
            if len(os.listdir(o)) > 1 or (os.listdir(o) and not exists(o + '/wszst-setup.txt')):
                if exists(o + '/wszst-setup.txt'): remove(o + '/wszst-setup.txt')
                return
        case 'SARC':
            class Stub:
                def __init__(self,*args,**kwargs):pass
                def __call__(self,*args,**kwargs): return Stub()
                def __getattribute__(self,name): return Stub()
            class OsStub:
                def __init__(self):pass
                def __add__(self,v): return os.devnull

            if db.print_try: print('Trying with sarc')
            db.get('sarc')
            sys.modules['oead'] = Stub()
            sys.modules['rstb'] = Stub()
            sys.modules['json'] = Stub()
            os.path.dirname = lambda x: OsStub() if x.endswith('\\sarc.py') else dirname(x)
            sys.modules['os'] = os

            try:
                from bin.sarc import SARC # type: ignore
                sarc = SARC(open(i,'rb').read())
                sarc.extract_to_dir(o)
                del sarc
            except ImportError: raise
            except: pass

            sys.modules.pop('oead')
            sys.modules.pop('rstb')
            sys.modules.pop('json')
            sys.modules.pop('os')
            os.path.dirname = dirname

            if os.listdir(o): return
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
            from winpty import PtyProcess # type: ignore
            bk = os.environ.get('__COMPAT_LAYER')
            os.environ['__COMPAT_LAYER'] = 'RUNASINVOKER'
            if db.print_try: print('Trying with input')

            p = PtyProcess.spawn(subprocess.list2cmdline([i,'--nf','--ns','--am','--al','--lang','en','--cp',o + '\\$CACHE','-t',o,'-g','ifw.installer.installlog=true','in']))
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
            run(['innounp-2','-x','-b','-m','-d' + o,'-u','-h','-o','-y',i])
            if not exists(o + '/{app}'): run(['innounp','-x','-m','-d' + o,'-y',i])
            if exists(o + '/{app}'):
                for x in os.listdir(o):
                    if x != '{app}': mv(o + '/' + x,o + '/$INSFILES/')
                while True:
                    try:copydir(o + '/{app}',o,True)
                    except:pass
                    else:break
                if exists(o + '/$INSFILES/unarc.dll'):
                    td = TmpDir()
                    copydir(o + '/$INSFILES',td.p)
                    remove(td + '/cls-srep.dll',td + '/cls-srep_x64.exe',td + '/cls-srep_x86.exe')
                    copydir(dirname(db.get('cls-srep')),td.p)
                    bcmd = ['unarc-cpp',td + '\\unarc.dll','x','-o+','-dp' + o,'-w' + td,'-cfgarc.ini']
                    for f in os.listdir(dirname(i)):
                        f = dirname(i) + '\\' + f
                        if not isfile(f) or open(f,'rb').read(4) != b'ArC\1': continue
                        print(run(bcmd + [f],cwd=td.p))
                        td.destroy()
                return
            run(['innoextract','-e','-q','--iss-file','-g','-d',o,i])
            if os.listdir(o):
                for x in os.listdir(o):
                    if x != 'app': mv(o + '/' + x,o + '/$INSFILES/' + x)
                if exists(o + '/app'): copydir(o + '/app',o,True)
                return
        case 'VISE Installer'|'Inno Archive': return quickbms('instexpl')
        case 'MSI':
            run(['lessmsi','x',i,o + '\\'])
            if exists(o + '/SourceDir') and os.listdir(o + '/SourceDir'):
                copydir(o + '/SourceDir',o,True)
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
                if ofs:
                    f.close()
                    import zipfile
                    for x in ofs:
                        with zipfile.ZipFile(x[0]) as z: xopen(o + '/' + x[1],'wb').write(z.read(x[1]))
                        remove(x[0])
                    if os.path.exists(o + '/_INST32I.EX_') or os.path.exists(o + '/_inst16.ex_'):
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
            run(['unpsarc',i,o])
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
        case 'Doom WAD':
            osj = OSJump()
            osj.jump(o)
            run(['wadext',i,'-nogfxconvert','-nosndconvert'])
            osj.back()
            if os.listdir(o) and os.listdir(o + '/' + os.listdir(o)[0]):
                td = o + '/' + os.listdir(o)[0]
                while exists(td):
                    try: copydir(td,o,True)
                    except PermissionError:pass
                return
        case 'Glacier RPKG':
            run(['rpkg','-extract_from_rpkg',i,'-output_path',o])
            if os.listdir(o) and os.listdir(o + '/' + os.listdir(o)[0]):
                td = o + '/' + os.listdir(o)[0]
                while exists(td):
                    try: copydir(td,o,True)
                    except PermissionError:pass
                return
        case 'Glacier PKG Def':
            run(['rpkg','-decrypt_packagedefinition_thumbs',i,'-output_path',o])
            if os.listdir(o): return
        case 'Blur PAK': return quickbms('blur')
        case 'Konami DPG':
            if db.print_try: print('Trying with custom extractor')

            inf = open(i,'rb')
            def readstr():
                t = b''
                while True:
                    b = inf.read(1)
                    if b == b'\x00': break
                    t += b
                return t.decode()
            assert inf.read(8) == b'DP2\x1A0001'
            inf.seek(4,1)
            nfs = int.from_bytes(inf.read(4),byteorder='little')
            offs = [int.from_bytes(inf.read(4),byteorder='little') for _ in range(nfs+1)]
            fnms = [readstr() for _ in range(nfs)]

            for idx in range(nfs):
                tof = open(o + '/' + fnms[idx],'wb')
                inf.seek(offs[idx])
                print(hex(inf.tell()),fnms[idx])
                siz = int.from_bytes(inf.read(4),byteorder='little') - 5
                skp = 4

                inf.seek(skp + siz,1)
                while inf.read(1) != b'\x11':
                    skp += 1

                inf.seek(offs[idx] + 4 + skp)
                tof.write(inf.read(siz))
                tof.close()
            if os.listdir(o): return
        case 'Teardown Encrypted File':
            of = o + '\\' + basename(o) + '_'
            run(['tdedecrypt',i + '_',of])
            if exists(of[:-1]) and (os.path.getsize(of[:-1]) or not os.path.getsize(i)): return
        case 'Unreal Engine Package':
            if 0:
                key = ['-a']
            else: key = []
            run(['repak'] + key + ['unpack','-o',o,'-q','-f',i])
            if os.listdir(o): return
        case 'Danganronpa WAD':
            if db.print_try: print('Trying with wad_archiver')
            db.get('wad_archiver')
            from bin.wad_archiver import Commands # type: ignore
            class Args:
                input = i
                output = o
                silent = True
            Commands.extract_files(Args)
            if os.listdir(o): return
        case 'Valve Package':
            run(['vpkedit','-o',o,'--no-progress','-e','/',i])
            if os.listdir(o): return
        case 'Direct Storage Archive':
            run(['unpsarc',i,o])
            if os.listdir(o): return
        case 'NSMBW Coin World ARC':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File
            f = File(i,endian='<')
            f.skip(6)

            fc = f.readu16()
            fs = []
            for _ in range(fc):
                fm = [f.read(0x40).strip(b'\0').decode()]
                f.skip(4)
                fm.append(f.readu32())
                f.skip(4)
                fm.append(f.readu32())
                fs.append(fm)
            for of in fs:
                tof = xopen(o + '/' + of[0],'wb')
                f.seek(of[2])
                tof.write(f.read(of[1]))
                tof.close()
            f.close()
            if fs: return
        case 'Arc System Works PAC': return quickbms('arcsys')

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
def fix_isinstext(o:str,oi:str=None):
    ret = True
    oi = oi or o
    fs = os.listdir(oi)
    if exists(oi + '/_INST32I.EX_'):
        mkdir(o + '/_INST32I_EX_')
        extract(oi + '/_INST32I.EX_',o + '/_INST32I_EX_','Stirling Compressed')
    elif exists(oi + '/_inst16.ex_'):
        mkdir(o + '/_inst16_ex_')
        extract(oi + '/_inst16.ex_',o + '/_inst16_ex_','Stirling Compressed')

    for x in fs:
        x = x.upper()
        if x in ['_SETUP.LIB'] or (x.startswith('_SETUP.') and x.endswith(('0','1','2','3','4','5','6','7','8','9'))) or x.endswith('.Z'):
            mkdir(o + '/' + x.replace('.','_'))
            r = not extract(oi + '\\' + x,o + '\\' + x.replace('.','_'),'InstallShield Z')
            if not r: print("Could not extract",x)
            ret = ret and r
        elif x.startswith(('_SYS','_USER','DATA')) and x.endswith('.CAB'):
            mkdir(o + '/' + tbasename(x))
            r = not extract(oi + '\\' + x,o + '\\' + tbasename(x),'InstallShield Archive')
            if not r: print("Could not extract",x)
            ret = ret and r

    if ret:
        if oi == o:
            for x in fs: remove(oi + '/' + x)
        else: remove(oi)
        for x in os.listdir(o):
            if not isdir(o + '/' + x) or x.upper() in ['_INST32I_EX_','_INST16_EX_']: continue
            while True:
                try: copydir(o + '/' + x,o,True);break
                except PermissionError: pass
    return ret

def main_extract(inp:str,out:str,ts:list[str]=None,quiet=True,rs=False) -> bool:
    out = cleanp(out)
    #assert not exists(out),'Output directory already exists'
    inp = cleanp(inp)
    if ts == None: ts = analyze(inp)
    if not ts:
        if rs: assert ts,'Unknown file type'
        return

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
        if rs: assert not rs,"Could not extract"
        return
    if not quiet: print('Extracted successfully to',out)
    return True
