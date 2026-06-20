import sys
if sys.version_info < (3,13):
    raise RuntimeError("Python 3.13+ is required")

import re,json,ast,os,errno,subprocess,hashlib,ctypes,types,typing,shutil
from time import sleep
from ctypes import wintypes
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

if typing.TYPE_CHECKING:
    from lib.file import File
    u8=s8=u16=s16=u24=s24=u32=s32=u40=s40=u48=s48=u64=s64=u128=s128=int
    f16=f32=f64=float
    utf8,utf16=str
    padding=skip=align=types.NoneType

def asrt(c:bool,*r,err:Exception=ValueError):
    if not c:
        if len(r) == 1 and isinstance(r[0],types.FunctionType): r = r[0]()
        elif r: r = ' '.join(str(x) for x in r)
        else: r = ''
        raise err(r)
def namespace(_func=None,include=[],keep_init=True):
    def f1(func):
        class Wrapper(object):
            def __init__(self):
                self.__initialized = False
                self.__body = {}
            def __call__(self,*args,**kwargs):
                d = super().__getattribute__('__dict__')
                if d['_Wrapper__initialized'] and keep_init: return self
                r = func(*args,**kwargs)
                b = d['_Wrapper__body']
                b.clear()
                for k,v in r.items():
                    if include:
                        if k not in include: continue
                    elif not isinstance(v,types.FunctionType): continue
                    b[k] = v
                d['_Wrapper__initialized'] = True
                return self
            def __getattribute__(self,name):
                d = super().__getattribute__('__dict__')
                if not d['_Wrapper__initialized']: self()
                return d['_Wrapper__body'][name]
        Wrapper.__name__ = func.__name__

        return Wrapper()
    if _func is None: return f1
    return f1(_func)

isfile,isdir,exists = os.path.isfile,os.path.isdir,os.path.exists
basename,dirname,abspath = os.path.basename,os.path.dirname,os.path.abspath
rename = os.rename
getsize,listdir = os.path.getsize,os.listdir
def splitext(i:str):
    bn = basename(i)
    if bn[0] == '.': return i[:-len(bn)],bn
    return os.path.splitext(i)
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
    if abspath(i)[0].lower() == abspath(o)[0].lower():
        mkdir(dirname(o))
        rename(i,o)
    else:
        copy(i,o)
        remove(i)
mv = move
def copydir(i:str,o:str,delete=False,reni=False):
    i = str(i)
    o = str(o)
    if reni:
        asrt(delete)
        ni = dirname(i) + '\\tmp' + os.urandom(8).hex()
        mv(i,ni)
        i = ni
    mkdir(o)
    cfnc = cp
    if delete and abspath(i)[0].lower() == abspath(o)[0].lower(): cfnc = move
    for x in listdir(str(i)): cfnc(i + '/' + x,o + '/' + x)
    if delete: rmdir(i)
def remove(*inp:str): [os.remove(i) if isfile(i) or os.path.islink(i) else rmdir(i) for i in inp if exists(i)]
def symlink(i:str,o:str):
    mkdir(dirname(o))
    os.symlink(i,o)
def xopen(f:str,m='r',encoding='utf-8',newline=None,**kwargs):
    f = abspath(str(f))
    mkdir(dirname(f))
    if 'b' in m: return open(f,m,**kwargs)
    return open(f,m,encoding=encoding,newline=newline,**kwargs)
def readfile(f:str,m='rb',off=0,size=None,encoding='utf-8',newline=None,**kwargs) -> bytes|str:
    asrt('r' in m or '+' in m)
    if 'b' in m: o = xopen(f,m,**kwargs)
    else: o = xopen(f,m,encoding=encoding,newline=newline,**kwargs)
    o.seek(off)
    r = o.read(size)
    o.close()
    return r
def writefile(f:str,d:bytes|str,m='wb',encoding='utf-8',newline=None,**kwargs):
    if 'b' in m: o = xopen(f,m,**kwargs)
    else: o = xopen(f,m,encoding=encoding,newline=newline,**kwargs)
    r = o.write(d)
    o.close()
    return r
def rldir(i:str,files=True) -> list[str]:
    i = str(i)
    o = []
    for x in listdir(i):
        x = i + '\\' + x
        if isfile(x): o.append(x)
        else:
            if not files: o.append(x)
            o += rldir(x,files=files)
    return o
def isvalid(p:str,reject_dirs=False):
    if not isinstance(p,str) or not p: return False
    if reject_dirs and os.path.sep in p: return False

    _,path = os.path.splitdrive(p)
    root = os.environ.get('HOMEDRIVE','C:') if sys.platform == 'win32' else os.path.sep
    asrt(exists(root),err=FileNotFoundError)

    root = root.rstrip('\\/') + os.path.sep
    for pp in path.split(os.path.sep):
        try: os.lstat(root + pp)
        except OSError as e:
            if hasattr(e,'winerror'):
                if e.winerror == 123: return False
            elif e.errno in {errno.ENAMETOOLONG,errno.ERANGE}: return False
        except (TypeError,ValueError): return False
    return True
SUB_PATH = str.maketrans({
    ':':'：',
    '?':'？',
    '*':'﹡',
    '|':'｜',
    '"':'＂',
    '<':'＜',
    '>':'＞',
    '\n':' ',
    '\t':' ',
})
SUB_PATHX = str.maketrans({
    '/':'／',
    '\\':'＼',
})
def sub_path(p:str,home=False,slash=False):
    if home and len(p) > 3 and p[0].isalpha() and p[1] == ':' and p[2] in '\\/': h,p = p[:3],p[3:]
    else: h = ''
    r = p.translate(SUB_PATH).replace('\r','')
    if slash: r = r.translate(SUB_PATHX)
    return h + r
def sanitize_relative(p:str):
    rps = [len(x) for x in p.replace('\\','/').split('/')]
    ps = []
    cp = 0
    for x in rps:
        ps.append((p[cp:cp+x],p[cp+x:cp+x+1]))
        cp += x + 1
    ops = []
    for x in ps:
        if x[0] == '..':
            if ops: ops.pop()
            continue
        elif x[0] in {'.',''}: continue
        ops.append(x[0] + x[1])
    r = ''.join(ops)
    if p[-1] not in '\\/' and r[-1] in '\\/': r = r[:-1]
    elif p[-1] != r[-1]: r = r[:-1] + p[-1]
    return r
def unix2filetime(t:int): return t * 10000000 + 116444736000000000
def filetime2unix(t:int): return t / 10000000 - 116444736000000000
def set_ftime(p:str,ct:int=None,at:int=None,mt:int=None,unix=True):
    if ct is None: ct = 0
    if mt is None: mt = ct
    if at is None: at = mt

    try:
        h = ctypes.windll.kernel32.CreateFileW(p,256,0,None,3,128,None)
        if unix:
            wct = unix2filetime(ct)
            wat = unix2filetime(at)
            wmt = unix2filetime(mt)
        else: wct,wat,wmt = ct,at,mt
        fct = wintypes.FILETIME(wct & 0xFFFFFFFF,wct >> 32)
        fat = wintypes.FILETIME(wat & 0xFFFFFFFF,wat >> 32)
        fmt = wintypes.FILETIME(wmt & 0xFFFFFFFF,wmt >> 32)
        ctypes.windll.kernel32.SetFileTime(h,ctypes.byref(fct),ctypes.byref(fat),ctypes.byref(fmt))
        ctypes.windll.kernel32.CloseHandle(h)
    except: pass
    else: return

    if not unix:
        at = filetime2unix(at)
        mt = filetime2unix(mt)
    os.utime(p,(at,mt))

TMP = os.getenv('TEMP').strip('\\') + '\\'
def gtmp(suf=''): return TMP + 'tmp' + os.urandom(8).hex() + suf
class TmpDir:
    def __init__(self,mdir=True,path=TMP):
        self.p = path.strip('\\/') + '\\' + 'tmp' + os.urandom(8).hex()
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
    def __init__(self,suf='',name='',path=TMP): self.p = path.strip('\\/') + '\\' + (name or ('tmp' + os.urandom(8).hex() + suf))
    def link(self,i:str): symlink(i,self.p)
    def copy(self,i:str): cp(i,self.p)
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
def make_env():
    env = os.environ.copy()
    td = TmpDir()
    env['USERPROFILE'] = td.p
    env['HOMEDRIVE'] = td.p[:2]
    env['HOMEPATH'] = td.p[2:]
    env['APPDATA'] = td.p + '\\AppData\\Roaming'
    env['LOCALAPPDATA'] = td.p + '\\AppData\\Local'
    env['TEMP'] = td.p + '\\AppData\\Local\\Temp'
    env['TMP'] = env['TEMP']
    return env,td

def _neof(f):
    b = bool(f.read(1))
    if b: f.seek(-1,1)
    return b
def send_keys(i:str,escape=False):
    if escape:
        i = i.replace('{','\0').replace('}','\1')
        for c in '+^%~()[]': i = i.replace(c,'{' + c + '}')
        i = i.replace('\0','{{}').replace('\1','{}}')
    subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',f"(New-Object -ComObject WScript.Shell).SendKeys('{i}')"])

def msplit(i:str|list[str],seps:list[str]) -> list[str]:
    out = i if type(i) == list else [i]
    for s in seps: out = sum([x.split(s) for x in out],[])
    return out

TDB:dict = json.load(xopen('lib/tdb.json'))
TDBF = set(sum(TDB.values(),[]))
WEAK = set(json.load(xopen('lib/weak.json')))
DDB:list[dict] = json.load(xopen('lib/ddb.json'))
TRDB = None
db = DLDB()

def cleanp(i:str):
    i = i.replace('/','\\').rstrip('\\')
    while i.endswith('\\.'): i = i[:-1].rstrip('\\')
    while i.startswith('.\\'): i = i[1:].lstrip('\\')
    i = i.replace('\\.\\','\\')
    return abspath(i)
def checktdb(i:list[str]) -> list[str]:
    o = []
    for x in i:
        if not x.lower() in TDBF: continue
        for t in TDB:
            if x.lower() in TDB[t]: o.append(t)
    return o

class FileStubbed(Exception): pass
class FileStub:
    def __init__(self): pass
    def close(self,*_,**__): raise FileStubbed
    read = readi = readline = seek = skip = tell = flush = close
    @property
    def closed(self): raise FileStubbed
    @property
    def name(self): raise FileStubbed
    @property
    def mode(self): raise FileStubbed
    def __bool__(self): return False
def analyze(inp:str,raw=False,quiet=True) -> list[str]|tuple[list[str],list[str],str]:
    global TRDB

    db.set_temp_print(False)
    if '://' in inp[:0x20]: typ = 'url'
    else:
        inp = cleanp(inp)
        if isdir(inp): typ = 'directory'
        else:
            f = open(inp,'rb')
            idt = f.read(0x4000)
            f.close()
            isz = sum(idt) != 0
            try: assert idt.decode('utf-8').replace('\r','').replace('\n','').replace('\t','').isprintable()
            except: typ = 'binary'
            else:
                if isz: typ = 'text'
                else: typ = 'binary'
            if typ == 'binary' and not isz: typ = 'null'

    ts = []
    if typ != 'url':
        if typ != 'directory':
            db.get('trid')
            import bin.trid.trid as trid # type: ignore
            trid.print = lambda *_,**__:None
            if not TRDB: TRDB = trid.trdpkg2defs(dirname(db.get('trid')) + '\\triddefs.trd',usecache=True)
            ts += [x.triddef.filetype for x in trid.tridAnalyze(inp,TRDB,True) if x.perc >= 10]
            for wt in {'InstallShield setup',}:
                if wt in ts: ts.remove(wt)
        _,o,_ = db.run(['file','-bsnNkm',dirname(db.get('file')) + '\\magic.mgc',inp])
        ts += [x.split(',')[0].split(' created: ')[0].split('\u00BF\u0074\u2593\u256C\u2551\u2567\u00F1\u2219')[0].split('\\012-')[0].strip(' \t\n\r\'') for x in o.split('\n') if x.strip()]

    if typ == 'binary':
        f = open(inp,'rb')
        tg = f.read(4)
        if tg[:2] == b'MZ' or tg == b'\x7fELF':
            if tg[:2] == b'MZ':
                f.seek(0x3C)
                f.seek(int.from_bytes(f.read(4),'little'))
                pe = f.read(4) == b'PE\0\0'
            else: pe = False
            f.close()

            dpth = db.get('die')
            dprc = subprocess.Popen([dpth,'-p','-D',dirname(dpth) + '\\db',inp],stdout=-1,stderr=-3)

            if pe:
                log = gtmp('.log')
                db.run(['exeinfope',inp + '*','/s','/log:' + log])
                for _ in range(15):
                    if exists(log) and getsize(log): break
                    sleep(0.1)
                if exists(log):
                    lg = readfile(log,'r',errors='ignore').strip()
                    os.remove(log)
                    m = EIPER1.search(lg)
                    if m: ts.append(m[1])
                    for x in msplit(lg.split('\n')[0].split(' - ',1)[1],[' - [ ',' ] [ ',' ] - ',' [ ',' ] ',' stub : ',' Ovl like : ',' - ',' , ']):
                        if x == '( RESOURCES ONLY ! no CODE )': ts.append('Resources Only')
                        elif not x.startswith(('Buffer size : ','Size from sections : ','File corrupted or Buffer Error','x64 *Unknown ','*Unknown ','Stub : *Unknown ','EP Token : ','File is corrupted ','EP : ')):
                            for sp in {' -> OVL Offset : ',' > section : ',' , size : ','Warning : ',' ( ','*ACM'}: x = x.split(sp)[0]
                            for sp in {'Structure : ','use : ','stub : ','EP Generic : '}: x = x.split(sp)[-1]
                            x = x.strip(' ,!:;-()[]')
                            if x and x.lower() not in {'genuine','unknown','more than necessary','sections','x64 *unknown exe','<- from file.','no sec. cab.7z.zip','2010 (e8'} and not x.lower().endswith((' sections',' [deb. 02')) and not x.replace('-','').replace('.','').isdigit() and\
                               x != 'Deb' and not (x[0].lower() == 'v' and x[1:].replace('.','').isdigit()) and not (len(x) == 15 and x[:4] == 'exe ' and x[12] == '-' and x[13:].isdigit() and all(x in '0123456789ABCDEF' for x in x[4:12])): ts.append(x)

            yrep = db.update('yara')
            yp = dirname(yrep[0])
            if yrep[1]:
                db.run([yp + '/yarac.exe','-w',yp + '/packers_peid.yar',yp + '/packers_peid.yarc'])
                remove(yp + '/yarac.exe','-C',yp + '/packers_peid.yar')
            err,o,_ = db.run(['yara','-C',yp + '/packers_peid.yarc',inp])
            if not err: ts += [x.split()[0].replace('_',' ').strip() for x in o.split('\n') if x.strip()]

            dprc.wait()
            o = dprc.stdout.read().decode('cp437')
            die = [x.strip() for x in DIER.findall(o.replace('\r','')) if x != 'Unknown']
            ts += die + [x.split('[')[0].split('(')[0] for x in die]
        else: f.close()

    ts = [x for x in ts if not x in WEAK]
    tst = []
    for t in ts:
        if t.startswith('Nintendo 3DS SMDH file: "'): tst.append('Nintendo 3DS SMDH file')
        elif t.startswith(('NES ROM image (iNES): ','NES ROM image (iNES) ')): tst.append('NES ROM image (iNES)')
        elif t.startswith('doom patch PWAD data containing'): tst.append('doom patch PWAD data')
        elif t.startswith('Delphi compiled form \''): tst.append('Delphi compiled form')
        elif t.startswith('cannot open ') and t.endswith(' (No such file or directory)'): pass
        elif t.startswith('byte-swapped cpio archive; '): tst.append('byte-swapped cpio archive')
        elif t.startswith('ISO 9660 CD-ROM filesystem data \''): tst.append('ISO 9660 CD-ROM filesystem data')
        else: tst.append(t)
    ts = tst

    ts = [MSPCR.sub(' ',x.strip()) for x in ts if x.strip()]
    if any(x in ts for x in {'Commodore 64 BASIC V2 program','Commodore C64 program'}):
        _,o,_ = db.run(['unp64','-i',inp])
        ts.append(o.strip().split(' : ',1)[1].split(', unpacker=')[0].strip())
        if ts[-1] == '(Unknown)': ts.pop(-1)
    if not ts and isfile(inp):
        _,o,_ = db.run(['gamearch',inp,'-l'])
        ts = re.findall(r'File .+ a .+ \[(.+)\]\n',o.replace('\r',''))
        for dts in re.findall(r', archive is (?:probably|definitely) not (.+)\n',o.replace('\r','')): ts.remove(dts)
        if ts: ts = [ts[0]]
        else: ts = []

    nts = checktdb(ts)
    nts = list(set(nts))
    f = FileStub()
    if typ in {'text','binary','null'}:
        f = open(inp,'rb')
        f._close = f.close
        f.close = lambda *_,**__:None
        f.readi = lambda n,end='<',sign=False: int.from_bytes(f.read(n),byteorder={'<':'little','>':'big'}[end],signed=sign)
        f.skip = lambda n: f.seek(n,1)
        fsz = f.seek(0,2)
    elif typ == 'url': fsz = len(inp)
    elif typ == 'directory':
        f = rldir(inp,files=False)
        fll = [os.path.relpath(x,inp).lower().replace('\\','/') for x in f]
        fsz = len(f)
    opfs = {}
    def fkopen(p,m,*args,**kwargs):
        asrt('r' in m and not '+' in m,'Read only')
        if p == inp:
            if f:
                asrt(m == 'rb','Binary read only')
                f.seek(0)
            return f
        elif p in opfs and opfs[p].mode == m:
            opfs[p].seek(0)
            return opfs[p]
        else:
            if p in opfs: opfs[p].close()
            rf = open(p,m,*args,**kwargs)
            rf._close = rf.close
            rf.close = lambda *_,**__:None
            rf.readi = lambda n,end='<',sign=False: int.from_bytes(rf.read(n),byteorder={'<':'little','>':'big'}[end],signed=sign)
            rf.skip = lambda n: rf.seek(n,1)
            opfs[p] = rf
            return rf

    for xv in DDB:
        if 't' in xv and xv['t'] != typ: continue
        if 'rq' in xv:
            if xv['rq'] == None:
                if nts: continue
            else:
                rq = xv['rq'] if type(xv['rq']) == list else [xv['rq']]
                chf = all if type(rq[-1]) == bool and rq[-1] else any
                chf = chf(y in nts for y in rq if type(y) == str)
                if type(rq[-1]) == bool and not rq[-1]: chf = not chf
                if not chf: continue
        if 'rqr' in xv:
            if xv['rqr'] == None:
                if ts: continue
            else:
                rqr = xv['rqr'] if type(xv['rqr']) == list else [xv['rqr']]
                chf = all if type(rqr[-1]) == bool and rqr[-1] else any
                chf = chf(y in ts for y in rqr if type(y) == str)
                if type(rqr[-1]) == bool and not rqr[-1]: chf = not chf
                if not chf: continue

        tret = 0
        if not 'd' in xv or not xv['d']:
            dl = []
            tret = True
        else:
            dl = xv['d']
            if type(dl[0]) != list: dl = [dl]
        ret = False
        for x in dl:
            if x[0] == 'py':
                lc = {}
                if f: f.seek(0)
                try:
                    exec('def check(inp,fsz,f):\n\t' + x[1].replace('\n','\n\t'),globals={'open':fkopen,'os':os,'dirname':dirname,'basename':basename,'tbasename':tbasename,'splitext':splitext,'isfile':isfile,'exists':exists,'getsize':getsize,'neof':_neof,'readfile':readfile,'asrt':asrt},locals=lc)
                    ret = lc['check'](inp,fsz,f)
                except FileStubbed: ret = False
                except:
                    print(xv['rs'] + ':')
                    print(x[1])
                    if f: f._close()
                    for opf in opfs.values():
                        if not opf.closed: opf._close()
                    raise
            elif x[0] == 'ps':
                env = os.environ.copy()
                env['input'] = inp
                p = subprocess.Popen(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',x[1]],env=env,stdout=-1)
                p.wait()
                ret = p.stdout.read().decode(errors='ignore').strip() == 'True'
            elif x[0] == 'ext': ret = inp.lower().endswith(tuple(x[1]) if type(x[1]) == list else x[1])
            elif x[0] == 'name': ret = basename(inp) == x[1]
            elif x[0] == 'namei': ret = basename(inp).lower() == x[1]
            elif x[0] in {'print','echo'}: print(*x[1:]);continue
            elif type(x[0]) == bool and x[0] == False: tret = ret = False
            elif typ in {'binary','text','null'}:
                if x[0] == 'contain':
                    cv = ast.literal_eval('"' + x[1].replace('"','\\"') + '"').encode('latin1')
                    sp = x[2][0]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = cv in f.read(x[2][1])
                elif x[0] == 'isat':
                    cv = ast.literal_eval('"' + x[1].replace('"','\\"') + '"').encode('latin1')
                    sp = x[2]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = f.read(len(cv)) == cv
                elif x[0] == 'isatS':
                    cv = ast.literal_eval('"' + x[1].replace('"','\\"') + '"').encode('latin1')
                    sp = x[3]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = f.read(x[2]*len(cv)) == (cv*x[2])
                elif x[0] == 'isin':
                    cvs = [ast.literal_eval('"' + cv.replace('"','\\"') + '"').encode('latin1') for cv in x[1]]
                    sp = x[2]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = f.read(len(cvs[0])) in cvs
                elif x[0] == 'size':
                    if type(x[1]) == int: ret = fsz == x[1]
                    else: ret = (x[1][0] == None or fsz >= x[1][0]) and (x[1][1] == None or fsz <= x[1][1])
                elif x[0] == 's%': ret = fsz % x[1] == 0
                elif x[0] == 'hash':
                    hs = x[1].lower()
                    if len(hs) == 40: h = hashlib.sha1
                    elif len(hs) == 32: h = hashlib.md5
                    elif len(hs) == 64: h = hashlib.sha256
                    h = h()

                    if len(x) > 3: mn,mx = x[2],x[3]
                    elif len(x) > 2: mn,mx = 0,x[2]
                    else: mn,mx = 0,fsz

                    f.seek(mn)
                    c = mx - mn
                    cv = b''
                    while c > 0:
                        cv = f.read((c % 0x1000) or 0x1000)
                        if not cv: break
                        h.update(cv)
                        c -= len(cv)
                    ret = h.hexdigest() == hs
                elif x[0] == 'str0e':
                    sp = x[1]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    scnt = 0
                    b = b''
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=/\\:<>*': scnt += 1
                        elif b == b'\0': ret = scnt >= x[3];break
                        else: ret = False;break
                    else: ret = scnt >= x[3]
                elif x[0] == 'str0':
                    sp = x[1]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    scnt = 0
                    b = b''
                    end = False
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if b == b'\0': end = True
                        elif not end and b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=/\\:<>*': scnt += 1
                        else: ret = False;break
                    else: ret = scnt >= x[3]
                elif x[0] == 'str':
                    sp = x[1]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    b = b''
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if not b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=/\\:<>*': ret = False;break
                    else: ret = True
                elif x[0] == 'n0':
                    sp = x[2]
                    if sp < 0: sp = fsz + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = sum(f.read(x[1])) != 0
                elif x[0] == 'reg':
                    reg = re.compile(x[1].encode())
                    if len(x) > 3: mn,mx = x[2],x[3]
                    elif len(x) > 2: mn,mx = x[2],fsz
                    else: mn,mx = 0,fsz

                    f.seek(mn)
                    ret = reg.match(f.read(mx-mn)) != None
                elif x[0] == 'json':
                    f.seek(0)
                    try: js = json.loads(f.read().decode('utf-8'))
                    except: ret = False
                    else:
                        def chk(j,c):
                            if type(j) != type(c): return False
                            if type(j) == dict and len(j) != len(c): return False
                            elif type(j) == list and len(c) > len(j): return False

                            if type(j) == dict:
                                for k in c:
                                    if k not in j: return False
                                    v = j[k]
                                    if type(v) != type(c[k]): return False
                                    if type(v) == dict and c[k] and not chk(v,c[k]): return False
                                    elif type(v) == list and c[k] and not chk(v,c[k]): return False
                                    elif type(v) == str and c[k] == 'n0' and not v: return False
                            elif type(j) == list:
                                for ix,cv in enumerate(c):
                                    v = j[ix]
                                    if type(v) != type(cv): return False
                                    if type(v) == dict and cv and not chk(v,cv): return False
                                    elif type(v) == list and cv and not chk(v,cv): return False
                                    elif type(v) == str and cv == 'n0' and not v: return False
                            return True
                        ret = chk(js,x[1])
                else: raise ValueError('Unknown detection instruction: ' + str(x))
            elif typ == 'url':
                if x[0] == 'isat':
                    cv,sp = x[1],x[2]
                    ret = inp[sp:sp+len(cv)] == cv
                elif x[0] == 'contains':
                    cv,sp,lng = x[1],x[2],x[3]
                    ret = inp[sp:sp+lng].find(cv) != -1
                elif x[0] == 'isin':
                    cv,sp = x[1],x[2]
                    ret = inp[sp:sp+len(cv[0])] in cv
            elif typ == 'directory':
                if x[0] == 'contains':
                    fl = fll.copy()
                    ret = False
                    for fn in x[1]:
                        for pfn in fl:
                            if fn in pfn: fl.remove(pfn);break
                        else: break
                    else: ret = True
                elif x[0] == 'containsext':
                    fl = fll.copy()
                    ret = False
                    for xn in x[1]:
                        for pfn in fl:
                            if pfn.endswith(xn): fl.remove(pfn);break
                        else: break
                    else: ret = True
            if xv.get('qq') and (type(x[-1]) != bool or x[-1]):
                if ret:
                    tret = True
                    break
            else:
                tret = (tret or type(tret) != bool) and ret
                if not tret: break
        if tret:
            if xv.get('s'):
                nts = [xv['rs']]
                break
            else: nts.append(xv['rs'])
    if f and hasattr(f,'_close'): f._close()
    for opf in opfs:
        if not opf.closed: opf._close()
    nts = list(set(nts))
    if not quiet and not nts: print(ts)

    db.reset_temp_print()
    if raw: return nts,ts,typ
    return nts

def extract(inp:str,out:str,t:str) -> bool:
    from .sub1 import extract1
    from .sub2 import extract2
    from .sub3 import extract3
    from .sub4 import extract4
    from .sub4_1 import extract4_1
    from .sub4_2 import extract4_2
    from .sub4_3 import extract4_3
    from .sub4_4 import extract4_4
    from .sub4_5 import extract4_5
    from .sub5 import extract5

    for f in (extract1,extract2,extract3,extract4,extract4_1,extract4_2,extract4_3,extract4_4,extract4_5,extract5):
        r = f(inp,out,t)
        if not r: return r

    return 1
def hookshot(cmd:list,redirect:dict,**kwargs):
    scr = cmd[0]
    if kwargs.get('print_try',db.print_try): print('Trying with',scr)
    if 'print_try' in kwargs: kwargs.pop('print_try')
    scr = db.get(scr)
    hks = scr + '.hookshot'
    open(hks,'w').close()

    #hkc = dirname(hks) + '/Hookshot.ini'
    #writefile(hkc,b'LoadHookModulesFromHookshotDirectory = yes\n')
    pwc = dirname(hks) + '/Pathwinder.ini'
    pwf = open(pwc,'w',encoding='utf-8')
    for i,(k,v) in enumerate(redirect.items()):
        pwf.write(f'[FilesystemRule:Rule{i}]\nOriginDirectory = {k}\nTargetDirectory = {v}\n\n')
    pwf.close()

    pw3 = dirname(hks) + '/Pathwinder.HookModule.32.dll'
    pw6 = dirname(hks) + '/Pathwinder.HookModule.64.dll'
    symlink(dirname(db.get('hookshot')) + '/Pathwinder.HookModule.32.dll',pw3)
    symlink(dirname(db.get('hookshot')) + '/Pathwinder.HookModule.64.dll',pw6)

    r = db.run(['hookshot',scr] + cmd[1:],print_try=False,**kwargs)
    remove(hks,pwc,pw3,pw6)
    return r

def fix_isinstext(o:str,oi:str=None):
    ret = True
    oi = oi or o
    fs = listdir(oi)
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
        for x in listdir(o):
            if not isdir(o + '/' + x) or x.upper() in {'$_INST32I_EX_','$_INST16_EX_','$ENGINE32'}: continue
            while True:
                try: copydir(o + '/' + x,o,True);break
                except PermissionError: pass
    return ret
def fix_innoinstext(o:str,i:str):
    if not exists(o + '/$INSFILES'): return False
    if exists(o + '/$INSFILES/unarc.dll') or exists(o + '/$INSFILES/UnArcLib.dll'): uad = o + '\\$INSFILES'
    elif exists(o + '/$INSFILES/tmp/unarc.dll'): uad = o + '\\$INSFILES\\tmp'
    elif exists(o + '/$INSFILES/{tmp}/unarc.dll'): uad = o + '\\$INSFILES\\{tmp}'
    else: return False

    td = TmpDir()
    copydir(uad,td.p)
    open(td + '/.hookshot','x').close()

    bcmd = ['unarc-cpp',td + '\\' + ('UnArcLib' if exists(td + '/UnArcLib.dll') else 'unarc') + '.dll','x','-o+','-dp' + o,'-w' + td,'-cfgarc.ini']
    for f in os.listdir(dirname(i)):
        f = dirname(i) + '\\' + f
        if not isfile(f) or open(f,'rb').read(4) != b'ArC\1': continue
        mkdir(TMP + '\\INNOTMP1')
        mkdir(TMP + '\\INNOTMP2')
        hookshot(bcmd + [f],{f'{os.environ["SYSTEMROOT"]}\\Temp':TMP + '\\INNOTMP1','C:\\Windows\\Temp':TMP + '\\INNOTMP2'},cwd=td.p)
        remove(TMP + '\\INNOTMP1',TMP + '\\INNOTMP2')
    td.destroy()

    return True
def fix_tar(o:str,rem=True):
    if len(listdir(o)) == 1:
        f = o + '/' + listdir(o)[0]
        if open(f,'rb').read(2) == b'MZ': return
        nts = analyze(f,quiet=True)
        if nts == ['TAR'] or nts == ['Stripped TAR']:
            r = extract(f,o,nts[0])
            if not r and rem:
                try:remove(f)
                except PermissionError:pass
            return r
def fix_cab(o:str,rem=True):
    ids = {}
    for x in listdir(o):
        if len(extname(x)) != 4 or not extname(x)[1:].isdigit(): return fix_cab2(o)
        id = int(extname(x)[1:])
        if id in ids: return fix_cab2(o)
        ids[id] = x

    if not 0 in ids: return
    from lib.file import File
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
        else: mv(o + '/' + ids[id],o + '/' + n)
    i.close()

    if not err and rem: remove(o + '/' + ids[0])
def fix_cab2(o:str):
    gid = None
    for x in os.listdir(o):
        x = extname(x)[1:]
        if len(x) != 36 or len(x.split('_')) != 5: return
        id = extname(x)
        try: bytes.fromhex(x.replace('_',''))
        except: return
        if not id: gid = id
        elif id != gid: return

    for f in os.listdir(o):
        fn = f[:-37]
        if fn[1] == '_': fn = fn[2:]
        elif len(fn.split('.')[0]) > 5 and '_' in fn.split('.')[0] and len(fn.split('.')[0].split('_',1)[1]) == 3 and fn.split('.')[0].split('_',1)[1].isdigit(): fn = fn.split('.',1)[1]
        fn = fn.replace('_','.')
        if fn.lower().endswith(('.dll00','.exe00','.h00','.dll01','.exe01','.ini00')): fn = fn[:-2]
        if exists(o + '/' + fn):
            c = 0
            while exists(o + '/' + noext(fn) + '_' + str(c) + extname(fn)): c += 1
            fn = noext(fn) + '_' + str(c) + extname(fn)
        while True:
            try: mv(o + '/' + f,o + '/' + fn)
            except PermissionError: pass
            else: break

def guess_ext(d:bytes) -> str:
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    ext = 'bin'
    if d[:4] == b'\x89PNG': ext = 'png'
    elif d[:4] == b'RIFF' and d[8:12] == b'WAVE': ext = 'wav'
    elif d[:4] == b'OggS': ext = 'ogg'
    elif d[:4] == b'fLaC': ext = 'flac'
    elif d[:4] == b'MThd': ext = 'mid'
    elif d[:4] == b'DXBC': ext = 'cso'
    elif d[:4] == b'NES\x1A': ext = 'nes'
    elif d[:4] == b'\x7FELF': ext = 'elf'
    elif d[:4] == b'DDS ': ext = 'dds'
    elif d[:4] == b'\x1BLua': ext = 'luac'
    elif d[:4] == b'8BPS': ext = 'psd'
    elif d[:4] == b'FWS\x09': ext = 'swf'
    elif d[:0x14] == b'Creative Voice File\x1A': ext = 'voc'
    elif d[:0x17] == b'Kaydara FBX Binary  \0\x1A\0': ext = 'fbx'
    elif d[:4] == b'FORM' and d[8:12] == b'AIFF': ext = 'aif'
    elif d[:3] == b'\xFF\xD8\xFF' and ((d[3] == 0xE0 and d[6:11] == b'JFIF\0') or (d[3] == 0xE1 and d[6:11] == b'Exif\0')): ext = 'jpg'
    elif d[-0x12:] == b'TRUEVISION-XFILE.\0': ext = 'tga'
    elif d[4:8] == b'mdat' and d[int.from_bytes(d[0:4],'big')+4:int.from_bytes(d[0:4],'big')+8] == b'moov': ext = 'mp4'
    elif d[:4] == b'\0\0\1\xBA' and\
         d[4] >> 6 == 0b01 and d[4] & 4 and\
         d[6] & 4 and d[8] & 4 and d[9] & 1 and\
         d[12] & 3 == 0b11 and not d[13] >> 3: ext = 'mpeg2'
    elif d[:2] == b'BM' and (not sum(d[4:8]) or not d[3]): ext = 'bmp'
    elif d[:0x13] == b'<?xml version="1.0"': ext = 'xml'
    elif d[:10] == b'# Blender ' and d[15:0x1A] == b' MTL File: ' and (d[10:11]+d[12:13]+d[14:15]).isdigit() and d[11] == d[13] == 0x2E: ext = 'blend'
    elif int.from_bytes(d[:4],'little') == s and d[5] == 0xAF and d[4] in {0x11,0x12,0x30,0x31,0x44}: ext = 'flc'
    elif s > 0x100 and (d[:3] == b'ID3' or
                       (d[0] == 0xFF and d[1] & 0xE0 == 0xE0 and d[1] & 0x18 != 8 and d[1] & 0x06 != 0 and
                        d[2] & 0xF0 != 0xF0 and d[2] & 0x0C != 0x0C and d[3] & 0b11 != 0b10)): ext = 'mp3'
    elif s >= 8 and d[0] == 0x78 and d[1] in {0x01,0x5E,0x9C,0xDA} and\
                    d[2] & 6 != 6 and not (not d[2] & 6 and d[2] >> 3) and (
                   ((d[3] << 8 | d[4]) == (~(d[5] << 8 | d[6]) & 0xFFFF)) if not d[2] & 6 else (
                    (d[2] >> 3) < 286 and (d[4] & 31) < 30)): ext = 'zlib'

    return ext
def guess_ext_zeebo(d:bytes,hint:int=None):
    if not d: return 'null'

    if d[:4] == b'PLZP': ext = 'plzp'
    elif not hint is None and hint <= 3: ext = ('image','audio','txt','bin')[hint]
    else: ext = guess_ext(d)

    if not hint is None:
        if hint == 0 and ext not in {'png','jpg','bmp','tga','dds'}: ext = 'image'
        elif hint == 1 and ext not in {'wav','mid','ogg'}: ext = 'audio'
        elif hint == 2: ext = 'txt'

    return ext
def guess_ext_psx(d:bytes):
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    ext = None
    if d[:4] == b'pBAV': ext = 'vh'
    elif d[:4] == b'pQES': ext = 'sep'
    elif d[:4] in {b'VAG1',b'VAG2',b'VAGi',b'pGAV',b'VAGp'}: ext = 'vag'
    elif d[:4] == b'\x10\0\0\0' and int.from_bytes(d[4:8],'little') in {2,8,9} and\
         int.from_bytes(d[8:12],'little') == (int.from_bytes(d[0x10:0x12],'little')*int.from_bytes(d[0x12:0x14],'little')*2+12): ext = 'tim'
    elif not s%0x10 and not sum(d[:0x10]):
        for p in range(0x10,s,0x10):
            if d[p] >> 4 > 5 or d[p+1] > 7: break
        else: ext = 'vb'
    if not ext: ext = guess_ext(d)

    return ext
def guess_ext_ps2(d:bytes):
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    ext = None
    if d[:4] == b'TIM2': ext = 'tm2'
    elif d[:8] == b'IECSsreV': ext = 'hd'
    elif d[:0x18] == b'RESET\0\0\0\0\0\x08\0\0\0\0\0ROMDIR\0\0': ext = 'img'
    elif d[:0x10] == b'BOOT2 = cdrom0:\\': ext = 'cnf'
    elif not s%0x10 and not d[0] and not sum(d[2:0x10]):
        for p in range(0x10,s,0x10):
            if d[p] >> 4 > 5: break
        else: ext = 'psadpcm'
    if not ext:
        ext = guess_ext_psx(d)
        if ext == 'vb': ext = guess_ext(d)

    return ext
def guess_ext_nds(d:bytes):
    if not d: return 'null'

    if d[:4] in {b'RGCN',b'RLCN',b'RECN',b'RNAN',b'RCSN'}: ext = d[:4].decode('ascii').lower()[::-1]
    elif d[:4] in {b'BMD0',}: ext = d[:3].decode('ascii').lower()
    else: ext = guess_ext(d)

    return ext
def guess_ext_3ds(d:bytes):
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    if d[:4] == b'darc': ext = 'arc'
    elif d[0] == 0x11 and sum(d[1:8]) and int.from_bytes(d[1:4]) < (s-4): ext = 'lz11'
    elif d[0] == 0x40 and sum(d[1:8]) and int.from_bytes(d[1:4]) < (s-4): ext = 'lz40'
    else: ext = guess_ext(d)

    return ext
def guess_ext_wii(d:bytes):
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    if d[:4] == b'\0\x20\xAF\x30': ext = 'tpl'
    elif d[:4] == b'bres': ext = 'bres'
    elif d[:4] == b'\x55\xAA\x38\x2D': ext = 'u8'
    elif d[:4] == b'RLYT': ext = 'brlyt'
    else: ext = guess_ext(d)

    return ext
def guess_ext_xbox(d:bytes):
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    if d[:4] == b'RIFF' and d[8:12] == b'XWMA': ext = 'xwma'
    elif d[:4] == b'XPR2': ext = 'xprx'
    elif d[:4] == b'XPR\0': ext = 'xpr'
    elif d[:4] == b'XBEH': ext = 'xbe'
    elif d[:4] == b'XEX2': ext = 'xex'
    elif b'Microsoft (R) Xbox 360 Shader Compiler 2.' in d[:0x600]:
        p = d.find(b'Microsoft (R) Xbox 360 Shader Compiler 2.')
        st = d[p-7:p-1]
        if st == b'vs_3_0': ext = 'xvu'
        elif st == b'ps_3_0': ext = 'xpu'
        else: ext = 'xsh'
    else: ext = guess_ext(d)

    return ext
def guess_ext_163(d:bytes):
    if not d: return 'null'
    s = len(d)
    if s < 4: return 'bin'

    ext = None
    if d[:12] == b'CocosStudio-UI': ext = 'coc'
    elif d[1:5] == b'KTX ': ext = 'ktx'
    elif d[:4] in {b'VANT',b'MDMP',b'NTRK'}: ext = d[:4].decode('ascii').lower()
    elif d[:4] == b'RGIS': ext = 'gis'
    elif d[:4] == b'BKHD': ext = 'bnk'
    elif d[:3] in {b'hit',b'PKM',b'PVR'}: ext = d[:3].decode('ascii').lower()
    elif s < 0x100000 and not b'\0' in d:
        txt = None
        for ec in ('utf-8','gb2312'):
            try:
                tx = d.decode(ec).replace('\r','')
                asrt(tx.replace('\n','').replace('\t','').isprintable())
            except: pass
            else:
                txt = tx
                break
        if not txt is None:
            if txt[0] == '{': ext = 'json'
            elif txt[0] == '<': ext = 'xml'
            elif txt[:7] == 'float4 ' or any(x in txt[:0x1000] for x in {'uniform vec4 ','float ','return float4(','\tvec4 ','\tfloat4 ',' #define ',' attribute vec4 ','out vec4 ','};\nstruct ','precision mediump float;','};\nfloat4 ',') in vec4 ','void main()\n{\n','\tfloat3 '}): ext = 'glsl'
            else: ext = 'txt'
    if not ext: ext = guess_ext(d)

    return ext

MIMEMP = {
    'application/octet-stream':'bin',
    'application/epub+zip':'epub',
    'application/javascript':'js',
    'application/java-archive':'jar',
    'application/x-microsoft.net.object.binary.base64':'b64',
    'audio/mpeg':'mp3',
    'audio/vorbis':'ogg',
    'binary/octet-stream':'bin',
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
    'text/ecmascript':'ejs',
    'text/tab-separated-values':'tsv',
    'video/3gpp':'3gp',
    'video/matroska':'mkv',
    'video/matroska-3d':'mkv',
    'video/mpeg':'mpg',
    'video/mpeg4-generic':'mp4',
}
def mime2ext(m:str):
    if type(m) == bytes: m = m.decode('latin1')
    m = m.split(';')[0].lower()
    if m in MIMEMP: return MIMEMP[m]
    m = m.split('/')[1].split('+')[-1]
    if m.startswith('x-'): m = m[2:]
    if m.startswith('vnd.'): m = m[4:]
    return m

ZIP7MP = {
    '7z':'7z',
    'ARJ':'Arj',
    'Asar':'Asar',
    'Base64':'Base64',
    'BinHex':'BinHex',
    'MSCAB':'Cab',
    'Windows Help File':'Chm',
    'Microsoft Compound Document':'Compound',
    'CPIO':'Cpio',
    'CramFS':'CramFS',
    'EXT':'Ext',
    'ISO':'Iso',
    'MacBinary':'MacBinary',
    'RAR':'Rar',
    'RPM Package':'Rpm',
    'Shockwave Flash':'SWF',
    'SquashFS':'SquashFS',
    'UDF':'Udf',
    'BZip2':'bzip2',
    'XAR':'Xar',
    'VHD':'VHD',
    'yEnc':'YEnc',
    'Z':'Z',
    'GZIP':'gzip',
    'Error Code Modeler':'ecm',
    'Apple Partition Map':'APM',
    'UUencoded':'uue',
    'xz':'xz',
    'ZSTD':'zstd',
    'TAR':'tar',
    'ZIP':'zip',
    'LZIP':'lzip',
    'LZMA':'lzma',
    'Nero CD IMG':'nrg',
    'Apple Disk Image':'Dmg',
    'LHARC':'Lzh',
    'Microsoft SZDD':'MsLZ',
    'NTFS':'ntfs',
    'MSCAB SFX':'Cab',
    'NSIS Installer':'Nsis',
    'MSI':'Compound',
    'MSP':'Compound',
    'ARJZ':'Arj',
    'AR':'Ar',
    'VirtualBox Disk Image':'VDI',
    'Master Boot Record':'MBR',
    'DiskDupe IMG':'FAT',
    'Compressed ISO':'cso',
    'Resource DLL':'PE',
    'Floppy Image':None,
    'Google Update Installer':None,
    'JFD IMG':None,
    'IMG':None,
    None:None,
}
def zip7(i:str,o:str,t:str,overwrite=False):
    if t in ZIP7MP: t = ZIP7MP[t]
    else: raise ValueError(f'{t} is not mapped in ZIP7MP')
    return db.run(['7z','x',i,'-o' + o,'-ao' + ('a' if overwrite else 'u')] + (['-t' + t] if t else []))

def main_extract(inp:str,out:str,ts:list[str]=None,quiet=True,rs=False) -> bool:
    db.print_try = not quiet
    out = cleanp(out)
    #asrt(not exists(out),'Output directory already exists')
    if not '://' in inp: inp = cleanp(inp)
    if ts == None: ts = analyze(inp,quiet=quiet)
    if not ts:
        if rs: asrt(ts,'Unknown file type')
        return

    for x in ts:
        if not quiet: print('Trying format',x)
        mkdir(out)
        try:
            if not extract(inp,out,x):break
        except:
            if not listdir(out): os.rmdir(out)
            raise
        rmtree(out)
    else:
        if rs: raise Exception("Could not extract")
        return
    if not quiet: print('Extracted successfully to',out)
    return True
