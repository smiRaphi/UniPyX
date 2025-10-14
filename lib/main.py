import re,json,ast,os,sys,subprocess,hashlib,shutil
from time import sleep
from shutil import rmtree,copytree,copyfile
from lib.dldb import DLDB

TRIDR = re.compile(r'(\d{1,3}\.\d)% \(.*\) (.+) \(\d+(?:/\d+){1,2}\)')
EIPER1 = re.compile(r'Overlay : +(.+) > Offset : [\da-f]+h')
DIER = re.compile(r'    [A-Za-z]{4,12}: (.+)\n')
MSPCR = re.compile(r' +')
DOSMAX = {
    "waitonerror":"false",
    "priority":"normal,normal",
    "autolock":"false",
    "memsize":"63",
    "scaler":"none",
    "cycles":"max 100% limit 9999999999999999999999999999999999999999999999999999999999",
    "core":"dynamic",
    "ipx":"false"
}

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
def rldir(i:str,files=True):
    o = []
    for x in os.listdir(str(i)):
        x = str(i) + '\\' + x
        if isfile(x): o.append(x)
        else:
            if not files: o.append(x)
            o += rldir(x)
    return o

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

def msplit(i:str|list[str],seps:list[str]) -> list[str]:
    out = i if type(i) == list else [i]
    for s in seps: out = sum([x.split(s) for x in out],[])
    return out

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
def checktdb(i:list[str]) -> list[str]:
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
    _,o,_ = db.run(['trid','-d',dirname(db.get('trid')) + '\\triddefs.trd','-n','5',inp])
    ts = [x[1] for x in TRIDR.findall(o) if float(x[0]) >= 10]
    _,o,_ = db.run(['file','-bnNkm',os.path.dirname(db.get('file')) + '\\magic.mgc',inp])
    ts += [x.split(',')[0].split(' created: ')[0].split('\\012-')[0].strip() for x in o.split('\n') if x.strip()]
    _,o,_ = db.run(['die','-p','-D',dirname(db.get('die')) + '\\db',inp])
    ts += [x.split('[')[0].split('(')[0].strip() for x in DIER.findall(o.replace('\r','')) if x != 'Unknown']

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
                    lg = open(log,encoding='utf-8',errors='ignore').read().strip()
                    os.remove(log)
                    m = EIPER1.search(lg)
                    if m: ts.append(m[1])
                    for x in msplit(' - ' + lg.split('\n')[0].split(' - ',1)[1],[' - [ ',' ] [ ',' ] - ',' ]   ',' stub : ',' Ovl like : ',' - ']):
                        if x == '( RESOURCES ONLY ! no CODE )': ts.append('Resources Only')
                        elif not x.startswith(('Buffer size : ','Size from sections : ','File corrupted or Buffer Error','x64 *Unknown exe ','*Unknown exe ','Stub : *Unknown exe ','EP Token : ','File is corrupted ')):
                            x = x.split('(')[0].split('[')[0].split(' -> OVL Offset : ')[0].split(' > section : ')[0].split(' , size : ')[0].strip(' ,!:;-')
                            if x and x.lower() not in ('genuine','unknown','more than necessary )') and not (len(x) == 4 and x.isdigit()): ts.append(x)

                yrep = db.update('yara')
                yp = os.path.dirname(yrep[0])
                if yrep[1]:
                    db.run([yp + '/yarac.exe','-w',yp + '/packers_peid.yar',yp + '/packers_peid.yarc'])
                    remove(yp + '/yarac.exe','-C',yp + '/packers_peid.yar')
                err,o,_ = db.run(['yara','-C',yp + '/packers_peid.yarc',inp])
                if not err: ts += [x.split()[0].replace('_',' ').strip() for x in o.split('\n') if x.strip()]
            else: f.close()
        else: f.close()

    ts = [MSPCR.sub(' ',x.strip()) for x in ts if x.strip()]
    if any(x in ts for x in ('Commodore 64 BASIC V2 program',)):
        _,o,_ = db.run(['unp64','-i',inp])
        ts.append(o.strip().split(' : ',1)[1].split(', unpacker=')[0])

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
                    exec('def check(inp):\n\t' + x[1].replace('\n','\n\t'),globals={'os':os,'dirname':dirname,'basename':basename,'exists':exists},locals=lc)
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
                elif x[0] == 'isatS':
                    f = open(inp,'rb')
                    cv = ast.literal_eval('"' + x[1].replace('"','\\"') + '"').encode('latin1')
                    sp = x[3]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = f.read(x[2]*len(cv)) == (cv*x[2])
                    f.close()
                elif x[0] == 'size':
                    sz = os.path.getsize(inp)
                    if type(x[1]) == int: ret = sz == x[1]
                    else: ret = (x[1][0] == None or sz >= x[1][0]) and (x[1][1] == None or sz <= x[1][1])
                elif x[0] == 's%': ret = os.path.getsize(inp) % x[1] == 0
                elif x[0] == 'hash':
                    hs = x[1].lower()
                    if len(hs) == 40: h = hashlib.sha1
                    elif len(hs) == 32: h = hashlib.md5
                    elif len(hs) == 64: h = hashlib.sha256
                    h = h()

                    f = open(inp,'rb')
                    if len(x) > 3: mn,mx = x[2],x[3]
                    elif len(x) > 2: mn,mx = 0,x[2]
                    else:
                        mn = 0
                        mx = f.seek(0,2)
                        f.seek(0)

                    f.seek(mn)
                    c = mx - mn
                    cv = b''
                    while c > 0:
                        cv = f.read((c % 0x1000) or 0x1000)
                        if not cv: break
                        h.update(cv)
                        c -= len(cv)
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
                elif x[0] == 'str':
                    f = open(inp,'rb')
                    f.seek(x[1])
                    b = b''
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if not b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=': ret = False;break
                    else: ret = True
                    f.close()
                elif x[0] == 'n0':
                    f = open(inp,'rb')
                    f.seek(x[2])
                    ret = sum(f.read(x[1])) != 0
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

    def quickbms(scr,inf=i,ouf=o):
        if db.print_try: print('Trying with',scr)
        run(['quickbms',db.get(scr),inf,ouf],print_try=False)
        if os.listdir(ouf): return
        return 1
    def dosbox(cmd:list,inf=i,oup=o,print_try=True,nowin=True,max=True,tmps=False):
        scr = cmd[0]
        s = db.get(scr)

        mkdir(oup)
        ts = oup + '/'
        if tmps: ts += 'TMP' + os.urandom(2).hex() + extname(s)
        else: ts += basename(s)
        symlink(s,ts)
        symlink(inf,oup + '/' + basename(inf))

        if print_try and db.print_try: print('Trying with',scr)
        p = subprocess.Popen([db.get('dosbox'),'-nolog','-nopromptfolder','-savedir','NUL','-defaultconf','-fastlaunch','-nogui',('-silent' if nowin else '-exit'),
             '-c','MOUNT C "' + oup.replace('\\','\\\\') + '"','-c','C:',
             '-c',subprocess.list2cmdline([basename(ts)] + [(basename(x) if x == i else x) for x in cmd[1:]]) + (' > _OUT.TXT' if nowin else '')] + (sum([['-set',f'{x}={DOSMAX[x]}'] for x in DOSMAX],[]) if max else []),stdout=-3,stderr=-2)

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
            try: remove(oup + '/_OUT.TXT',ts,oup + '/' + basename(inf))
            except PermissionError: sleep(0.1)
            else: break
        p.kill()

        return r
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

    match t:
        case '7z'|'LHARC'|'MSCAB'|'BinHex'|'Windows Help File'|'ARJ'|'ZSTD'|'JFD IMG'|'TAR'|'yEnc'|'xz'|'BZip2'|'SZDD'|'LZIP'|'CPIO'|'Asar'|'SWF':
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
        case 'PDF':
            run(['pdfdetach','-saveall','-o',o + '\\out',i])
            run(['pdfimages','-j',i,o + '\\img'])
            run(['pdftohtml','-embedbackground','-meta','-overwrite','-q',i,o + '\\html'])
            if os.listdir(o + '/html'): return
            remove(o + '/html')
        case 'ISO'|'IMG'|'Floppy Image'|'CDI'|'UDF'|'Aaru':
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
            remove(td)

            run(['7z','x',i,'-o' + o,'-aou'])
            if exists(o) and os.listdir(o): return
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
                        if not extract(f,o,'ISO'): remove(f)
                return
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
        case 'StuffIt'|'AMPK':
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
        case 'Stirling Compressed':
            od = rldir(o)
            run(["deark","-od",o,i])
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
            dosbox(['acb','r',i],tmps=True)
            if os.listdir(o): return
        case 'ALZip'|'EGG':
            run(['alzipcon','-x','-oa',i,o])
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
        case 'NCCH CXI':
            e,_,_ = run(['3dstool','-xtf','cxi',i,'--header',o + '\\HNCCH.bin','--exh',o + '\\DecExH.bin','--exh-auto-key','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key','--logo',o + '\\LogoLZ.bin','--plain',o + '\\PlainRGN.bin'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            if e: return 1

            for x in os.listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            return
        case 'NCCH CFA':
            e,_,_ = run(['3dstool','-xtf','cfa',i,'--header',o + '\\HNCCH.bin','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            if e: return 1

            for x in os.listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            return
        case 'Switch NSP'|'Switch NCA'|'Switch XCI':
            for k in ('prod','dev'):
                bcd = ['hac2l','-t',{'Switch NSP':'pfs','Switch NCA':'nca','Switch XCI':'xci'}[t],'--disablekeywarns','-k',db.get(k+'keys'),'--titlekeys=' + db.get('titlekeys')]
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
                rmdir(o)
                mkdir(o)
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
            kys = DKeys()
            cmd = ['java','-jar',db.get('jwudtool'),'-commonkey',kys.get('common'),'-decrypt','-in',i,'-out',o]
            k = kys.get(i)
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
        case 'Xbox LIVE ROM': raise NotImplementedError
        case 'GD-ROM CUE+BIN':
            run(['buildgdi','-extract','-cue',i,'-output',o + '\\','-ip',o + '\\IP.BIN'])
            if os.listdir(o):
                from bin.chkey import CHKeys
                if exists(o + '/IP.BIN') and CHKeys().get(o): return extract(o + '\\IP.BIN',o,'Chihiro Extracted GD-ROM')
                return
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
        case '3DO IMG':
            run(['3dt','unpack','-o',o,i])
            if os.listdir(o) and os.listdir(o + '/' + basename(i) + '.unpacked'):
                copydir(o + '/' + basename(i) + '.unpacked',o,True)
                return
        case 'Amiga IMG':
            run(['uaeunp','-x',i,'**'],cwd=o)
            if os.listdir(o): return
        case 'Atari ATR':
            run(['atr',i,'x','-a'],cwd=o)
            if os.listdir(o): return
        case 'ZArchive':
            run(['zarchive',i,o])
            if os.listdir(o): return
        case 'C64 Tape'|'C64 LiBRary':
            run(['dirmaster','/e',i],cwd=o)
            if os.listdir(o): return
        case 'C64 TBC MultiCompactor'|'C64 CruelCrunch'|'C64 Time Cruncher'|'C64 Super Compressor'|'C64 MegaByte Cruncher'|'C64 1001 CardCruncher'|\
             'C64 ECA Compactor':
            tf = o + '\\' + basename(i)
            symlink(i,tf)
            run(['unp64',tf])
            remove(tf)
            if os.listdir(o): return
        case 'Chihiro Extracted GD-ROM':
            from bin.chkey import CHKeys

            id = dirname(i)
            key = CHKeys().get(i)
            if not key: return 1

            fats = []
            for f in os.listdir(id):
                if len(f) != 7: continue
                ld = id + '\\' + f
                if isdir(ld) or os.path.getsize(ld) != 0x100: continue

                lf = open(ld,'rb')
                if sum(lf.read(8)) == 0 and sum(lf.read(8)) != 0 and sum(lf.read(3)) == 0 and lf.read(1)[0] == 0xFF and sum(lf.read(0x8C)) == 0:
                    lf.seek(0xC0)
                    fatx = lf.read(0x20).strip(b'\0')
                    if fatx:
                        try:fatx = id + '\\' + fatx.decode()
                        except:pass
                        else:
                            if exists(fatx): fats.append(fatx)
                lf.close()

            if not fats: return 1

            for f in fats:
                tf = f + '.dec'
                run(['chdecrypt',f,tf,key.hex().upper()])
                assert exists(tf) and open(tf,'rb').read(4) == b'FATX',basename(tf)
                od = f + '_ext'
                run(['chextract-fatx',tf,od])
                if exists(od) and not os.listdir(od): rmdir(od)
            return

        case 'U8'|'RARC':
            run(['wszst','X',i,'--max-file-size=2g','-o','-R','-E$','-d',o])
            remove(o + '/wszst-setup.txt')
            if os.listdir(o): return
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
                    if x != '{app}': mv(o + '/' + x,o + '/$INSFILES/')
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
            from bin.tmd import File

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
        case 'PKLITE':
            od = rldir(o)
            run(["deark","-opt","execomp","-od",o,i])
            for x in rldir(o):
                if not x in od:
                    mv(x,o + '/' + basename(i))
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
            r = extract(tf,o,'ISO')
            tf.destroy()
            return r
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
        case 'Rob Northen Compression'|'Amiga XPK':
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
            if db.print_try: print('Trying with custom extractor')

            d = dirname(i)
            for _ in range(3):
                if exists(d + '/SYSTEM.CNF'): break
                d = dirname(d)
            else: return 1
            mf = d + '/' + re.search(r'cdrom0:\\(.+);\d+\n',open(d + '/SYSTEM.CNF').read())[1]
            if not exists(mf): return 1

            f = open(mf,'rb')
            size = f.seek(0,2)
            f.seek(0)
            if f.read(4) != b'\x7FELF': return 1

            def read32(): return int.from_bytes(f.read(4),'little')
            def skip(n): f.seek(n,1)
            def cs(): return size-f.tell()
            def reads(max=0xFF):
                t = b''
                for _ in range(max):
                    t += f.read(1)
                    if t[-1] == 0: break
                return t
            def testb():
                b = f.read(1)
                if b: f.seek(-1,1)
                return bool(b)

            f.seek(0x38)
            hsize = read32()
            load = read32()
            f.seek(load)

            ENTRY_SIZE = 4 * 11
            def read_table(ver=0) -> float:
                fs = read32()
                if fs == 0 or (fs*(ENTRY_SIZE + (4 if ver == 0 else 0))) > cs(): return -1

                tab = []
                for i in range(fs):
                    if read32() != i: return -2 # ID
                    t = read32()
                    if t > 0xFF: return -3
                    if t > 0x10: return -3.1 # type
                    if i == 0 and t != 1: return -3.2
                    if ver == 1: skip(4)

                    s = read32()
                    if s == 0: return -4 # size
                    o = read32() * 0x800

                    no = read32()
                    if no == 0: return -6.1 # name offset
                    no = no - load + hsize
                    if no < 0 or no > size: return -6 # name offset

                    skip(4) # hash
                    if read32() not in (0x7D6,0x7D5): return -8 # ?
                    for _ in range(4):
                        if read32() > 0xFF: return -9 # small values

                    pos = f.tell()
                    f.seek(no)
                    n = reads()
                    if n[-1] != 0: return -10
                    try: n = n[:-1].decode('ascii')
                    except: return -10
                    f.seek(pos)

                    tab.append({
                        'o':o,
                        's':s,
                        'n':n or f'0x{i:x}.bin'
                    })

                return tab

            tabs = []
            while testb():
                cp = f.tell()
                r = read_table()
                if type(r) == list:
                    #print(f'Found table at 0x{cp:X} to 0x{f.tell():X}')
                    tabs.append(r)
                else:
                    #if r <= -8: print(f'0x{cp:X} 0x{f.tell()-4:X}',r)
                    f.seek(cp+4)

            f.seek(load)
            while testb():
                cp = f.tell()
                r = read_table(1)
                if type(r) == list:
                    #print(f'Found v1 table at 0x{cp:X} to 0x{f.tell():X}')
                    tabs.append(r)
                else:
                    #if r <= -8: print('v1',f'0x{cp:X}',f'0x{f.tell()-4:X}',r)
                    f.seek(cp+4)

            ds = os.path.getsize(i)
            for t in tabs:
                lt = max([x['o'] + x['s'] for x in t])
                if lt == ds:
                    for xf in t:
                        f.seek(xf['o'])
                        os.makedirs(o + '/' + os.path.dirname(xf['n']),exist_ok=True)
                        open(o + '/' + xf['n'],'wb').write(f.read(xf['s']))
                    f.close()
                    return
            f.close()
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
            if '/Content/' in i.split()[-1].replace('\\','/'): prgf = dirname(i.replace('\\','/').rsplit('/Content/',1)[0]) + '/Engine/Programs'
            else: prgf = None
            run(['unrealpak',i,'-Extract',o])
            if prgf and exists(prgf): remove(prgf)
            if os.listdir(o): return

            run(['repak','unpack','-o',o,'-q','-f',i])
            if os.listdir(o): return
        case 'Unreal ZenLoader':
            if '/Content/' in i.split()[-1].replace('\\','/'): prgf = dirname(i.replace('\\','/').rsplit('/Content/',1)[0]) + '/Engine/Programs'
            else: prgf = None
            run(['unrealpak',i,'-Extract',o])
            if prgf and exists(prgf): remove(prgf)
            if os.listdir(o): return

            run(['zentools','ExtractPackages',dirname(i),o,'-PackageFilter=' + i])[1]
            remove(o + '/PackageStoreManifest.json')
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
        case 'Chrome PAK':
            run(['chrome-pak','-u',i,o])
            if os.listdir(o): return
        case 'PS3/PSV PUP':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File

            PUPMAP = {
            1:{
                0x100: 'version.txt',
                0x101: 'license.xml',
                0x102: 'promo_flags.txt',
                0x103: 'update_flags.txt',
                0x104: 'patch_build.txt',

                0x200: 'ps3swu.self',
                0x201: 'vsh.tar',
                0x202: 'dots.txt',
                0x203: 'patch_data.pkg',

                0x501: 'spkg_hdr.tar',

                0x601: 'ps3swu2.self',
            },
            2:{
                0x100: 'version.txt',
                0x101: 'license.xml',

                0x200: 'psp2swu.self',
                0x204: 'cui_setupper.self',
                0x221: 'vs0_patch_tar_info.txt',
                0x231: 'vs0_patch_tar_2_info.txt',

                0x300: 'update_files.tar',
                0x302: 'SLB2',
                0x303: 'os0',
                0x304: 'vs0',
                0x305: 'unk_305',
                0x306: 'unk_306',
                0x307: 'unk_307',
                0x308: 'unk_308',
                0x309: 'unk_309',
                0x30A: 'unk_30A',
                0x30B: 'unk_30B',
                0x30C: 'unk_30C',
                0x30D: 'unk_30D',
                0x30E: 'unk_30E',
                0x30F: 'unk_30F',
                0x310: 'unk_310',
                0x311: 'vs0_patch_tar',
                0x312: 'vs0_patch_tar_2',
                0x313: 'sysscon_type_0',
                0x314: 'sysscon_type_1',
                0x315: 'sysscon_type_2',
                0x316: 'sysscon_type_3',
                0x317: 'sysscon_type_4',
                0x318: 'sysscon_type_5',
                0x319: 'sysscon_type_6',
                0x31A: 'sysscon_type_7',
                0x31B: 'sysscon_type_8',
                0x31C: 'sysscon_type_9',

                0x400: 'package_scewm.wm',
                0x401: 'package_sceas.as',

                0x2005: 'cp_es1_fw',
                0x2006: 'cp_es2_fw',
            }}

            f = File(i,endian='<')
            assert f.read(7) == b'SCEUF\0\0'
            f.skip(1)
            fv = f.readu64()
            if fv > 0xFFFFFFFFFFF:
                f.skip(-8)
                f._end = '>'
                fv = f.readu64()

            assert fv in (1,2) # PS3,PSV

            if fv in (1,2): f.skip(8)
            segs = f.readu64()
            assert 0xFFFFFFFFFFF >= segs
            if fv == 1: f.skip(16)
            elif fv == 2: f.skip(96)

            fs = []
            for _ in range(segs):
                fs.append((f.readu64(),f.readu64(),f.readu64()))
                f.skip(8)
            for of in fs:
                f.seek(of[1])
                if of[0] == 0x101:
                    xml = f.read(5)
                    f.skip(-5)
                    if xml in (b'<xml ',b'<?xml'): n = 'license.xml'
                    else: n = 'resource.txt'
                else: n = PUPMAP[fv].get(of[0],hex(of[0]))
                tof = xopen(o + '/' + n,'wb')
                tof.write(f.read(of[2]))
                tof.close()
            if fs: return
        case 'RPG Maker Archive (XP/VX/VX Ace)':
            run(['rpgmakerdecrypter',i,'-w','-o',o])
            if os.listdir(o): return
        case 'RDB':
            run(['cethleann','--rdb','-k','-p','-y','-z',o,dirname(i),'--filelist',basename(i)])
            if os.listdir(o): return
        case 'Konami GAME.DAT':
            db.get('ddrutil')
            if db.print_try: print('Trying with ddrutil')
            from bin.ddrutil import FileTable,FILE_TABLE_OFFSET,decompress # type: ignore

            f = open(i,'rb')
            f.seek(FILE_TABLE_OFFSET)
            ft = FileTable(f)
            d = b''
            for fe in ft.entries:
                if not fe.is_valid(): continue
                of = open(o + '/' + hex(fe.filename_hash),'wb')
                f.seek(fe.offset)
                d = f.read(fe.length)
                if fe.is_compressed(): d = decompress(d)
                of.write(d)
                of.close()
            f.close()
            if os.listdir(o): return
        case 'Hollow Knight Save':
            if db.print_try: print('Trying with custom extractor')
            try: from Cryptodome.Cipher import AES # type: ignore
            except ImportError: from Crypto.Cipher import AES # type: ignore
            from base64 import b64decode

            f = open(i,'rb')
            f.seek(0x19)
            dat = f.read().split(b'=')[0]
            f.close()
            dat = AES.new(b'UKu52ePUBwetZ9wNX88o54dnfKRu0T1l',AES.MODE_ECB).decrypt(b64decode(dat + b'===='))

            open(o + '/' + tbasename(i) + '.json','wb').write(dat[:-dat[-1]])
            return
        case 'Initial D XAF':
            run(['assamunpack',i],cwd=o)
            if os.listdir(o): return
        case 'Safari WebArchive':
            db.get('pywebarchive')
            if db.print_try: print('Trying with pywebarchive')
            import bin.webarchive # type: ignore

            try:
                with bin.webarchive.open(i) as f: f.extract(o + '/' + tbasename(i) + '.html',False)
            except bin.webarchive.WebArchiveError: pass
            else: return
        case 'WIM':
            run(['wimlib','apply',i,o])
            if os.listdir(o): return

            return extract(i,o,'7z')
        case 'WATCOM Archive':
            if db.print_try: print('Trying with wpack')
            run(['msdos',db.get('wpack'),i],print_try=False,cwd=o)
            if os.listdir(o): return
        case 'RPACK':
            if db.print_try: print('Trying with custom extractor') # https://github.com/Qivex/rpack-extract/blob/main/rpack-extract.lua
            raise NotImplementedError
            from bin.tmd import File

            f = File(i,endian='<')
            assert f.read(4) == b'RP6L','Invalid RPACK file'
            if f.readu32() == 4: offm = 16
            else: assert False,"Unknown offset multiplier"

            cmp = f.readu32()
            assert cmp in (0,),'Unknown compression method'

            pc,sc,fc,fncl,fnc,bs = f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32()
            secis = {}
            for _ in range(sc):
                s = {'type':f.readu8()}
        case 'Konami LZSS':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File

            f = File(i,endian='<')
            l = f.readu32()
            if not l: return 1
            of = open(o + '/' + basename(i)[:(-1 if i[-1] in 'zZ' else None)],'wb')

            ring = [b'\0'] * 0x1000
            rpos = 0x0FEE
            ctrlw = 1

            c1 = c2 = co = cl = 0
            b = b''
            while l > 0:
                if ctrlw == 1: ctrlw = 0x100 | f.readu8()

                if ctrlw & 1:
                    b = f.read(1)
                    of.write(b)
                    ring[rpos] = b
                    rpos = (rpos + 1) % 0x1000
                    l -= 1
                else:
                    c1,c2 = f.readu8(),f.readu8()
                    cl = (c2 & 0x0F) + 3
                    co = ((c2 & 0xF0) << 4) | c1

                    for _ in range(cl):
                        of.write(ring[co])
                        ring[rpos] = ring[co]
                        co = (co + 1) % 0x1000
                        rpos = (rpos + 1) % 0x1000
                        l -= 1

                ctrlw >>= 1

            of.close()
            return
        case 'Minecraft PCK': return quickbms('minecraft_pck')
        case 'Mo\'PaQ':
            run(['mpqextractor','-e','*','-o',o,i])
            if os.listdir(o): return
        case 'IPS Patch'|'IPS32 Patch':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File

            f = File(i)
            i32 = f.read(5) == b'IPS32'

            rof = f.readu32 if i32 else f.readu24
            eof = int.from_bytes(b'EEOF' if i32 else b'EOF')
            off = s = 0
            d = b''
            while True:
                off = rof()
                if off == eof:break
                s = f.readu16()
                if s == 0: d = f.readu16()*f.read(1)
                else: d = f.read(s)
                open(o + '/' + hex(off)[2:].upper().zfill(8 if i32 else 6) + '.bin','wb').write(d)
            if os.listdir(o): return
        case 'ABE': return msdos(['dabe','-v','+i',i],cwd=o)
        case 'CarComp': return msdos(['car','x',i],cwd=o)
        case 'Bunny Pro. Das2 DPK':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File

            f = File(i,endian='<')
            assert f.read(2) == b'PA'
            fc = f.readu16()
            assert fc > 0 and f.readu32() > 0
            fs = [(f.read(0x10).rstrip(b'\0').decode('ascii'),f.readu32()) for _ in range(fc)]

            for n,s in fs: open(o + '/' + n,'wb').write(f.read(s))
            f.close()

            if fs: return
        case 'The Sims FAR':
            if db.print_try: print('Trying with gameextractor')
            run(['java','-jar',db.get('gameextractor'),'-extract','-input',i,'-output',o],print_try=False,cwd=dirname(db.get('gameextractor')))
            remove(dirname(db.get('gameextractor')) + '/logs')
            if os.listdir(o): return
        case 'Build Engine Group':
            run(['gamearch',i,'-X'],cwd=o)
            if os.listdir(o): return
        case 'HMM Packfile':
            if db.print_try: print('Trying with hmmunpack')
            db.get('hmmunpack')
            import bin.hmmunpack as hmmunpack # type: ignore

            hmmunpack.print = lambda *_,file=None:None
            hmmunpack.__Path = hmmunpack.Path
            hmmunpack.Path = lambda *args,**kwargs:hmmunpack.__Path(*((o,) if args == (f'output-{i}',) else args),**kwargs)
            hmmunpack.open = lambda *args,**kwargs:open('NUL' if args[0] == f'extract-report-{i.replace("\\","-").replace("/","-")}.txt' else args[0],*args[1:],**kwargs)

            hmmunpack.extract(i)
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
        case 'Donkey Kong Banana Kingdom':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File

            f = File(i,endian='<')
            f.seek(0x14)
            c = f.readu32()
            f.seek(0x20)
            fs = []
            for _ in range(c):
                fs.append((f.read(0x10).rstrip(b'\0').decode(),f.readu32(),f.readu32() * 0x200))
                f.skip(8)
            for fe in fs:
                f.seek(fe[2])
                open(o + '/' + fe[0],'wb').write(f.read(fe[1]))

            lo = max(fe[2] + fe[1] for fe in fs)
            xo = lo + (-lo % 0x200)
            if not xo >= f._size:
                f.seek(xo)
                open(o + '/_extra.bin','wb').write(f.read(f._size - xo - 0x200 - 0xB8B200 - 0x14C))

            f.close()
            if fs: return

        case 'qbp'|'TANGELO'|'CSC'|'NLZM'|'GRZipII'|'BALZ'|'SR3'|'SQUID'|'CRUSH'|'LZPX'|'LZPXJ'|'THOR'|'ULZ'|'LZPM':
            # merge some small compressors
            of = o + '/' + tbasename(i)
            run([t.lower(),'d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'ZCM':
            run(['zcm','x','-t0',i,o],timeout=300)
            if exists('master.tmp'): remove('master.tmp')
            if os.listdir(o): return
        case 'BCM':
            of = o + '/' + tbasename(i)
            run(['bcm','-d','-f',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'RAZOR':
            run(['rz','-y','-o',o,'x',i,'*'])
            if os.listdir(o): return
        case 'NanoZip':
            run(['nz','x','-o' + o,i,'*'])
            if os.listdir(o): return
        case 'bsc':
            of = o + '/' + tbasename(i)
            run(['bsc','d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'LZHAM':
            of = o + '/' + tbasename(i)
            run(['lzham','-c','-u','d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'YBS':
            YBSR = re.compile(r': Error opening ([^\n]+)')
            if db.print_try: print('Trying with ybs')
            while True:
                _,_,r = run(['ybs','-d','-y',i],print_try=False,cwd=o)
                fs = YBSR.findall(r)
                if not fs: break
                for f in fs: mkdir(o + '/' + dirname(f))
            if os.listdir(o): return
        case 'CSArc':
            run(['csarc','x','-t8','-o',o,i])
            if os.listdir(o): return
        case 'RK':
            run(['rk','-x','-y','-O','-D' + o,i])
            if os.listdir(o): return
        case 'GRZip':
            run(['grzip','e',i],cwd=o)
            if os.listdir(o): return
        case 'BOA Constrictor':
            dosbox(['boa','-x',i])
            if os.listdir(o): return
        case 'Flashzip':
            run(['flashzip','x','-t0',i,o])
            if os.listdir(o): return
        case 'Dark':
            run(['dark','u',i],cwd=o)
            if os.listdir(o): return
        case 'SBC':
            run(['sbc','x','-hn','-y','-t' + o,i])
            if os.listdir(o): return
        case 'SZIP':
            of = o + '/' + tbasename(i)
            run(['szip','-d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'Zzip':
            run(['zzip','x','-q',i],cwd=o)
            if os.listdir(o): return
        case 'Squeez':
            f = open(i,'rb')
            if f.read(2) == b'MZ':
                for of in (0x19600,0x1ce00,0x55c00,0x1c400,0x20200,0x65a00,0x19400,0x1ca00,0x55000):
                    f.seek(of)
                    if f.read(5) == b'SCSFX':break
                else:
                    f.close()
                    return 1

                f.seek(9,1)
                f.seek(int.from_bytes(f.read(4),'little'),1)
                f.seek(0x2C,1)
                for _ in range(3): f.seek(int.from_bytes(f.read(4),'little')*2,1)
                f.seek(7,1)
                assert f.read(5) == b'-sqx-'
                f.seek(-12,1)
            else: f.seek(-2,1)

            tf = o + '/tmp' + os.urandom(8).hex() + '.exe'
            t = open(tf,'wb')

            t.write(open(db.get('sqx'),'rb').read())
            # SCSFX
            import zlib,base64
            t.write(zlib.decompress(base64.b85decode('c-oy-&2Aev5LVDjp+ff_nE;X!G?uMDOHTR&N0u9-i5+;;ra;sKwM$8?cgZcum7=~;Z@u?WpfAuz=_~Xb?yj_U5}>F7+uWJq@SB-$h72ab`H!`~f4^7zv{tLlKdaUL`Qy(<{cR*{Xk_Z7RzEfBjrtM$icQrrmUcy-ZzJybPH}b9sCV)IQa9>7{GV_YinvklV|^{sn1_P#7=i%=tw6XeZPbUfp1yO2hptgS#@9tlEi~hEok1`n^>Y!!a*SoC(`nRCD!v=_r-9=t;wEAU0RRX|>uN2`#z-gFLdL?fjdUycW2w;zqESm264W;<p;)AqU?PVA6>FJHv3Aq8VMK8>?Gx6FGw<r5eRR0caU={@<t7mwI$`k-;JOs;B$nX~)9_M6)@DwZ)|7(+)&g*tTS+@p+=MH+7G&pEg4tArav?>;^3%xk;Qx4Lh2su8-6=N`%emOYCm-!|e^9$KQ?F@Xe(ugTG=h_*Trla7GPqIN!G*N0<LhuHd90TfK&hq^trpTGW#J*E+EzXD7%rnN3$=1wDj@annBob}X*auV3YrM;MrU!vwmM_6yzwbA1)V5W9s<>kc4G(egzBA#kJ^3%A#tYJzaQOa&$g)5OvT(fmgp!?a<luGHG81#(a!F>XCE~p=DhMuLM(>8;?{1oiJ<BE7<1OK2Tl8c0YX~niG5B`zB}wyEVu=B<&X)ABGkq}w=+iUy?)^>lBCjR%k;t<mt<*L@-I|qw&{O!>j76??0nOK#IQ;<RL4uPVQ13bppd_0uq8QFvN#EK69#-Bi)MyT7MTJW4$5(Grr;#yZbfH|_M5GU2^+yF*|ri!+`?y9zW7zPk{2p+kZ(UHPD6B3@~hms;aJB&fZAb1REah>`i44RE~Vo!vvR4p%Z#``Q&*`_hedM{)w$Yk_!b=M9~I@OWWVBa&0`t8@3Hefrm~gL#c;tL{he?98YszvI;%jQ_ZFKPqYa|$6Za<9lLIe+vQLyd4MSlqi-eMXN58-8H6r4!TdfcYwGXmc0xrh`Hc|C2l+6|k8A_CnB_hd*(I4K;?JjVsiokIbkmd1R%MUjIEQtu`u};%1QN=Te0B3Pb+VO74BU8vuX8jQC`{C~?K>?MM8k&K>n<y*nVKaL~RBYNJd*2Er45yo?>tjR{B%CfaNO~n;TptIgA1ITbB|$1gG|@?d5&_6e%~Zt=mGZU)g~Hcd#(a(fpvJUg=2p(7_Q~PlX0z#7+JKDwjEr<bog9+MM5kLLmn-+zZ>)QA(m&`Op$&sKQx>d2*lX#)ikYHW?#(PlAu_Y}DIHMRTlpM+g3rNw!BQRb+jKyMx`P=RU<b$=v{an4g3Ce4Wyq;47deqE`jqG03nIWU&U3LU2s{@6ypRfS1ra@FTj7wl={xE2!F+4auE|iXmqKMY>BPt4NBZ!n@<^Dui8JvRQ;542F>4_wg)Ughh4U7@+(P0dG4#oqMt(imkB`c}Q)q@2O`sD|s9r)v8EajrH4VJn#3yy=-zYywvB8@1(|W<pQm_m32vRxpfdmQN&4uXL$MXW$7S=w9Gl6c3NkxbQjT2h)Ej~TyOWcT9`)AYZZAxqZYzpMBv_8(ytXx$PdQhj%89C1!&BtR8?V9q94-X2JPeC6`8%9UIv06!j&c|nWPbGZy_Rp}9hx8n&N%<1Tj|O>K$~W5wNaf2);pRyi`Fq93H1aI;VT=fI9^Htb-U(<#h^z68bHMuu#ss;DZ`{k3c`##wT*fjcyiLpxybcpQ;vgB`mK67r_j&B!f9&D@AiM?rCV!8Sh<!P=Ay38EG+9GGvWlliilIXsL2HgFr0>;@(i>GgRPfNQeS+W5hqaIX+$(;oKmP(&ql(S')))

            t.write(f.read())
            f.close()
            t.close()
            if db.print_try: print('Trying with sqx sfx')
            run([tf],print_try=False)
            remove(tf)
            if os.listdir(o): return
        case 'IMP':
            run(['imp','e','-o' + o,'-y',i])
            if os.listdir(o): return
        case 'ARHANGEL':
            dosbox(['arhangel','x','-oq-',i])
            if os.listdir(o): return
        case 'JAR':
            run(['jar','x','-y',i],cwd=o)
            if os.listdir(o): return
        case 'Lizard':
            of = o + '/' + tbasename(i)
            run(['lizard','-d','-f','-q',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'Zhuff':
            of = o + '/' + tbasename(i)
            run(['zhuff','-d','-s',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'BriefLZ'|'QUAD':
            of = o + '/' + tbasename(i)
            run([t.lower(),'-d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'UltraCompressor 2': raise NotImplementedError
        case 'LZFSE':
            of = o + '/' + tbasename(i)
            run(['lzfse','-decode','-i',i,'-o',of])
            if exists(of) and os.path.getsize(of): return
        case 'LIMIT':
            dosbox(['limit','e','-y','-p',i],tmps=True)
            if os.listdir(o): return
        case 'Squeeze It': return msdos(['sqz','x',i],cwd=o)
        case 'QuARK': return msdos(['quark','x','/y',i],cwd=o,text=False)
        case 'LZOP':
            run(['lzop','-x','-qf',i],cwd=o)
            if os.listdir(o): return
        case 'OpenZL':
            of = o + '/' + tbasename(i)
            run(['zli','d','-o',of,'-f',i])
            if exists(of) and os.path.getsize(of): return
        case 'Flash': return msdos(['flash','-E',i,'*.*'],cwd=o)
        case 'Ai':
            run(['ai','e',i],cwd=o)
            if os.listdir(o): return

    return 1
def fix_isinstext(o:str,oi:str=None):
    ret = True
    oi = oi or o
    fs = os.listdir(oi)
    if exists(oi + '/_INST32I.EX_'):
        mkdir(o + '/$_INST32I_EX_')
        extract(oi + '/_INST32I.EX_',o + '/$_INST32I_EX_','Stirling Compressed')
    elif exists(oi + '/_inst16.ex_'):
        mkdir(o + '/$_inst16_ex_')
        extract(oi + '/_inst16.ex_',o + '/$_inst16_ex_','Stirling Compressed')

    for x in fs:
        x = x.upper()
        if x in ('_SETUP.LIB',) or (x.startswith('_SETUP.') and x.endswith(('0','1','2','3','4','5','6','7','8','9'))) or x.endswith('.Z'):
            mkdir(o + '/' + x.replace('.','_'))
            r = not extract(oi + '\\' + x,o + '\\' + x.replace('.','_'),'InstallShield Z')
            if not r: print("Could not extract",x)
            ret = ret and r
        elif x.startswith(('_SYS','_USER','DATA')) and x.endswith('.CAB'):
            mkdir(o + '/' + tbasename(x))
            r = not extract(oi + '\\' + x,o + '\\' + tbasename(x),'InstallShield Archive')
            if not r: print("Could not extract",x)
            ret = ret and r
        elif x == 'ENGINE32.CAB':
            mkdir(o + '/$' + tbasename(x))
            r = not extract(oi + '\\' + x,o + '\\$' + tbasename(x),'MSCAB')
            if not r: print("Could not extract",x)

    if ret:
        if oi == o:
            for x in fs: remove(oi + '/' + x)
        else: remove(oi)
        for x in os.listdir(o):
            if not isdir(o + '/' + x) or x.upper() in ('$_INST32I_EX_','$_INST16_EX_','$ENGINE32'): continue
            while True:
                try: copydir(o + '/' + x,o,True);break
                except PermissionError: pass
    return ret
def fix_innoinstext(o:str,i:str):
    if not exists(o + '/$INSFILES'): return False
    if exists(o + '/$INSFILES/unarc.dll'): uad = o + '\\$INSFILES'
    elif exists(o + '/$INSFILES/tmp/unarc.dll'): uad = o + '\\$INSFILES\\tmp'
    elif exists(o + '/$INSFILES/{tmp}/unarc.dll'): uad = o + '\\$INSFILES\\{tmp}'
    else: return False

    td = TmpDir()
    copydir(uad,td.p)

    wfd64 = dirname(db.get('wfrrx64'))
    wfd86 = dirname(db.get('wfrrx86'))
    json.dump({'Mapping':[{'Source':f'{os.environ["SYSTEMROOT"]}\\Temp','Target':TMP},{'Source':r'C:\\Windows\\Temp','Target':TMP}]},open(wfd64 + '/V_FS.json','w'),separators=(',',':'))
    json.dump({'Mapping':[{'Source':f'{os.environ["SYSTEMROOT"]}\\Temp','Target':TMP},{'Source':r'C:\\Windows\\Temp','Target':TMP}]},open(wfd86 + '/V_FS.json','w'),separators=(',',':'))
    prcs = []
    for f in os.listdir(td.p):
        if f.startswith('cls-') and f.endswith('_x64.exe'): prcs.append(subprocess.Popen([db.get('wfrrx64'),'-n',f[:-4],'--file'],stdout=-1,stderr=-1))
        elif f.startswith('cls-') and f.endswith('_x86.exe'): prcs.append(subprocess.Popen([db.get('wfrrx86'),'-n',f[:-4],'--file'],stdout=-1,stderr=-1))

    bcmd = ['unarc-cpp',td + '\\unarc.dll','x','-o+','-dp' + o,'-w' + td,'-cfgarc.ini']
    for f in os.listdir(dirname(i)):
        f = dirname(i) + '\\' + f
        if not isfile(f) or open(f,'rb').read(4) != b'ArC\1': continue
        db.run(bcmd + [f],cwd=td.p)
    td.destroy()

    for p in prcs: p.kill()
    remove(wfd64 + '/WFRR.log',wfd64 + '/V_FS.json',wfd86 + '/WFRR.log',wfd86 + '/V_FS.json')
    return True
def fix_tar(o:str,rem=True):
    if len(os.listdir(o)) == 1:
        f = o + '/' + os.listdir(o)[0]
        if open(f,'rb').read(2) == b'MZ': return
        nts,_ = analyze(f,True)
        if nts == ['TAR']:
            r = extract(f,o,'TAR')
            if not r and rem:
                try:remove(f)
                except PermissionError:pass
            return r
def fix_cab(o:str,rem=True):
    ids = {}
    for x in os.listdir(o):
        if len(extname(x)) != 4 or not extname(x)[1:].isdigit(): return
        id = int(extname(x)[1:])
        if id in ids: return
        ids[id] = x

    if not 0 in ids: return
    from bin.tmd import File
    i = File(o + '/' + ids[0],endian='<')
    if i.read(4) != b'MSCE': return
    i.skip(0x30)

    fc = i.readu16()
    i.skip(14)
    fso = i.readu32()

    err = False
    i.seek(fso)
    for _ in range(fc):
        id = i.readu16()
        i.skip(8)
        n = i.read(i.readu16())[:-1].decode('ascii')
        if id not in ids: err = True
        else: os.rename(o + '/' + ids[id],o + '/' + n)
    i.close()

    if not err and rem: remove(o + '/' + ids[0])

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
