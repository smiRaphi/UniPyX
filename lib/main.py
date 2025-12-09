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
basename,dirname,splitext,abspath = os.path.basename,os.path.dirname,os.path.splitext,os.path.abspath
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
    if abspath(i)[0].lower() == abspath(o)[0].lower(): rename(i,o)
    else:
        copy(i,o)
        remove(i)
mv = move
def copydir(i:str,o:str,delete=False):
    mkdir(o)
    cfnc = cp
    if delete and abspath(i)[0].lower() == abspath(o)[0].lower(): cfnc = move
    for x in os.listdir(str(i)): cfnc(i + '/' + x,o + '/' + x)
    if delete: rmdir(i)
def remove(*inp:str): [os.remove(i) if isfile(i) or os.path.islink(i) else rmdir(i) for i in inp if exists(i)]
def xopen(f:str,m='r',encoding='utf-8',newline=None):
    f = os.path.abspath(str(f))
    mkdir(dirname(f))
    if 'b' in m: return open(f,m)
    return open(f,m,encoding=encoding,newline=newline)
def rldir(i:str,files=True) -> list[str]:
    i = str(i)
    o = []
    for x in os.listdir(i):
        x = i + '\\' + x
        if isfile(x): o.append(x)
        else:
            if not files: o.append(x)
            o += rldir(x,files=files)
    return o

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
TRDB = None
db = DLDB()

def cleanp(i:str):
    i = i.replace('/','\\').rstrip('\\')
    while i.endswith('\\.'): i = i[:-1].rstrip('\\')
    while i.startswith('.\\'): i = i[1:].lstrip('\\')
    i = i.replace('\\.\\','\\')
    return os.path.abspath(i)
def checktdb(i:list[str]) -> list[str]:
    o = []
    for x in i:
        if not x.lower() in TDBF: continue
        for t in TDB:
            if x.lower() in TDB[t]: o.append(t)
    return o
def analyze(inp:str,raw=False):
    global TRDB

    opt = db.print_try
    db.print_try = False
    inp = cleanp(inp)

    ts = []
    if isfile(inp):
        db.get('trid')
        import bin.trid.trid as trid # type: ignore
        trid.print = lambda *_,**__:None
        if not TRDB: TRDB = trid.trdpkg2defs(dirname(db.get('trid')) + '\\triddefs.trd',usecache=True)
        ts += [x.triddef.filetype for x in trid.tridAnalyze(inp,TRDB,True) if x.perc >= 10]
        _,o,_ = db.run(['die','-p','-D',dirname(db.get('die')) + '\\db',inp])
        ts += [x.split('[')[0].split('(')[0].strip() for x in DIER.findall(o.replace('\r','')) if x != 'Unknown']
    _,o,_ = db.run(['file','-bsnNkm',os.path.dirname(db.get('file')) + '\\magic.mgc',inp])
    ts += [x.split(',')[0].split(' created: ')[0].split('\\012-')[0].strip(' \t\n\r\'') for x in o.split('\n') if x.strip()]

    for wt in ('plain text','Plain text','ASCII text','XBase DataBase (generic)','HomeLab/BraiLab Tape image','VXD Driver','Sybase iAnywhere database files',
               'DICOM medical imaging bitmap (w/o header)','Enter a useful filetype description','Z-Code V8 adventure for Infocom Z-Machine','LTAC compressed audio (v1.61)',
               'Adobe Photoshop Color swatch','Gazebo model Configuration'):
        if wt in ts: ts.remove(wt)
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
                    for x in msplit(lg.split('\n')[0].split(' - ',1)[1],[' - [ ',' ] [ ',' ] - ',' [ ',' ] ',' stub : ',' Ovl like : ',' - ',' , ']):
                        if x == '( RESOURCES ONLY ! no CODE )': ts.append('Resources Only')
                        elif not x.startswith(('Buffer size : ','Size from sections : ','File corrupted or Buffer Error','x64 *Unknown ','*Unknown ','Stub : *Unknown ','EP Token : ','File is corrupted ','EP : ')):
                            for sp in (' -> OVL Offset : ',' > section : ',' , size : ','Warning : ',' ( ','*ACM'): x = x.split(sp)[0]
                            for sp in ('Structure : ','use : ','stub : ','EP Generic : '): x = x.split(sp)[-1]
                            x = x.strip(' ,!:;-()[]')
                            if x and x.lower() not in ('genuine','unknown','more than necessary','sections','x64 *unknown exe','<- from file.','no sec. cab.7z.zip') and not x.lower().endswith(' sections') and not x.replace('-','').replace('.','').isdigit() and\
                               x != 'Deb' and not (x[0].lower() == 'v' and x[1:].replace('.','').isdigit()): ts.append(x)

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
    if not ts and isfile(inp):
        _,o,_ = db.run(['gamearch',inp,'-l'])
        ts = re.findall(r'File .+ a .+ \[(.+)\]\n',o.replace('\r',''))
        for dts in re.findall(r', archive is (?:probably|definitely) not (.+)\n',o.replace('\r','')): ts.remove(dts)
        if ts: ts = [ts[0]]
        else: ts = []

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
            elif x[0] == 'ext': ret = inp.lower().endswith(tuple(x[1]) if type(x[1]) == list else x[1])
            elif x[0] == 'name': ret = basename(inp) == x[1]
            elif x[0] == 'print': print(*x[1:]);continue
            elif type(x[0]) == bool and x[0] == False: tret = ret = False
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
                elif x[0] == 'isin':
                    f = open(inp,'rb')
                    cvs = [ast.literal_eval('"' + cv.replace('"','\\"') + '"').encode('latin1') for cv in x[1]]
                    sp = x[2]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = f.read(len(cvs[0])) in cvs
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
                    else: mn,mx = 0,f.seek(0,2)

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
                elif x[0] == 'str0nv':
                    f = open(inp,'rb')
                    sp = x[1]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    scnt = 0
                    b = b''
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=/': scnt += 1
                        elif b != b'\0': ret = False;break
                    else: ret = scnt >= x[3]
                    f.close()
                elif x[0] == 'str0e':
                    f = open(inp,'rb')
                    sp = x[1]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    scnt = 0
                    b = b''
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=/': scnt += 1
                        elif b == b'\0': ret = scnt >= x[3];break
                    else: ret = scnt >= x[3]
                    f.close()
                elif x[0] == 'str0':
                    f = open(inp,'rb')
                    sp = x[1]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    scnt = 0
                    b = b''
                    end = False
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if b == b'\0': end = True
                        elif not end and b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=/': scnt += 1
                        else: ret = False;break
                    else: ret = scnt >= x[3]
                    f.close()
                elif x[0] == 'str':
                    f = open(inp,'rb')
                    sp = x[1]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    b = b''
                    for _ in range(x[2]):
                        b = f.read(1)
                        if not b: ret = False;break
                        if not b in b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$.#+% -_^({[]})&;@\',~=/': ret = False;break
                    else: ret = True
                    f.close()
                elif x[0] == 'n0':
                    f = open(inp,'rb')
                    sp = x[2]
                    if sp < 0: sp = f.seek(0,2) + sp
                    if sp < 0: sp = 0
                    f.seek(sp)
                    ret = sum(f.read(x[1])) != 0
                    f.close()
                elif x[0] == 'reg':
                    reg = re.compile(x[1].encode())
                    f = open(inp,'rb')
                    if len(x) > 3: mn,mx = x[2],x[3]
                    elif len(x) > 2: mn,mx = x[2],f.seek(0,2)
                    else: mn,mx = 0,f.seek(0,2)

                    f.seek(mn)
                    ret = reg.match(f.read(mx-mn)) != None
                    f.close()
                else: raise ValueError('Unknown detection instruction: ' + str(x))
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
    nts = list(set(nts))
    if not raw and not nts: print(ts)

    db.print_try = opt
    if raw: return nts,ts
    return nts

def extract(inp:str,out:str,t:str) -> bool:
    from .sub1 import extract1
    from .sub2 import extract2
    from .sub3 import extract3
    from .sub4 import extract4
    from .sub5 import extract5

    for f in (extract1,extract2,extract3,extract4,extract5):
        r = f(inp,out,t)
        if not r: return r

    return 1
def hookshot(cmd:list,redirect:dict,**kwargs):
    scr = cmd[0]
    if not 'print_try' in kwargs or kwargs.pop('print_try'): print('Trying with',scr)
    scr = db.get(scr)
    hks = scr + '.hookshot'
    open(hks,'x').close()

    #hkc = dirname(hks) + '/Hookshot.ini'
    #open(hkc,'wb').write(b'LoadHookModulesFromHookshotDirectory = yes\n')
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
    open(td + '/.hookshot','x').close()

    bcmd = ['unarc-cpp',td + '\\unarc.dll','x','-o+','-dp' + o,'-w' + td,'-cfgarc.ini']
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
    if len(os.listdir(o)) == 1:
        f = o + '/' + os.listdir(o)[0]
        if open(f,'rb').read(2) == b'MZ': return
        nts,_ = analyze(f,True)
        if nts == ['TAR'] or nts == ['Stripped TAR']:
            r = extract(f,o,nts[0])
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
        else: os.rename(o + '/' + ids[id],o + '/' + n)
    i.close()

    if not err and rem: remove(o + '/' + ids[0])
def fix_zeebo(f,hint:int=None):
    import io
    if type(f) == bytes: f = io.BytesIO(f)

    tag = f.read(4)

    if tag == b'\x89PNG': ext = 'png'
    elif tag == b'RIFF': ext = 'wav'
    elif tag == b'MThd': ext = 'mid'
    elif tag == b'PLZP': ext = 'plzp'
    else:
        f.skip(2)
        if f.read(4) == b'JFIF': ext = 'jpg'
        elif tag[:3] == b'ID3' or\
            (tag[0] == 0xFF and tag[1] & 0xE0 == 0xE0 and tag[1] & 0x18 != 8 and tag[1] & 0x06 != 0 and tag[2] & 0xF0 != 0xF0 and tag[2] & 0x0C != 0x0C and tag[3] & 3 != 2):
                ext = 'mp3'
        elif tag[0] == 0x78: ext = 'zlib'
        elif not hint is None and hint <= 3: ext = ('image','audio','txt','bin')[hint]
        else: ext = None

    if not hint is None:
        if hint == 0 and ext not in ('png','jpg'): ext = 'image'
        elif hint == 1 and ext not in ('wav','mid'): ext = 'audio'
        elif hint == 2: ext = 'txt'

    return ext

def main_extract(inp:str,out:str,ts:list[str]=None,quiet=True,rs=False) -> bool:
    db.print_try = not quiet
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
