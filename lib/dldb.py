import json,httpx,os,subprocess,zipfile,tarfile
from shutil import copyfile,rmtree
from time import sleep,time

BDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def gtmp(suf=''): return os.getenv('TEMP').strip('\\') + '\\tmp' + os.urandom(8).hex() + suf
def xopen(f:str,m='r',encoding='utf-8'):
    f = os.path.abspath(f)
    os.makedirs(os.path.dirname(f),exist_ok=True)
    if 'b' in m: return open(f,m)
    return open(f,m,encoding=encoding)
def copy(i:str,o:str):
    o = os.path.abspath(o)
    os.makedirs(os.path.dirname(o),exist_ok=True)
    copyfile(i,o)
class DLDB:
    def __init__(self):
        self.dbp = 'lib/dldb.json'
        self.udbp = 'bin/updb.json'
        self.c = httpx.Client()
        self.print_try = False
        self.db = json.load(xopen(self.dbp))
        if os.path.exists(self.udbp): self.udb = json.load(xopen(self.udbp))
        else: self.udb = {}

    def run(self,cmd:list,stdin:bytes|str=None,text=True,getexe=True,timeout=0,useos=False,print_try=True,print_out=False,**kwargs) -> tuple[int,str|bytes,str|bytes]:
        if print_try and self.print_try: print('Trying with',cmd[0])
        if type(cmd) == list and getexe: cmd[0] = self.get(cmd[0])
        if type(stdin) == str and not text: stdin = stdin.encode()
        if useos:
            if stdin:
                tfi = gtmp('.i')
                if type(stdin) == str: stdin = stdin.encode()
                open(tfi,'wb').write(stdin)
            tfo,tfe = gtmp('.o'),gtmp('.e')

            if 'cwd' in kwargs:
                cd = os.getcwd()
                os.chdir(kwargs['cwd'])
            r = os.system((subprocess.list2cmdline(cmd) if type(cmd) == list else cmd) + (f' <{tfi}' if stdin else '') + f' >{tfo} 2>{tfe}')
            if 'cwd' in kwargs: os.chdir(cd)

            o,e = open(tfo,'rb').read(),open(tfe,'rb').read()
            os.remove(tfo)
            os.remove(tfe)
            if stdin: os.remove(tfi)
            if text: o,e = o.decode('cp437'),e.decode('cp437')
        else:
            p = subprocess.Popen([str(x) for x in cmd] if type(cmd) == list else cmd,text=text,encoding=('cp437' if text else None),stdout=None if print_out else -1,stderr=None if print_out else -1,stdin=-1 if stdin != None else None,**kwargs)
            if timeout:
                for _ in range(int(timeout*10)):
                    if p.poll() != None: break
                    sleep(0.1)
                else: p.kill()
                o,e = p.stdout.read(),p.stderr.read()
            else: o,e = p.communicate(input=stdin)
            r = p.returncode
        return r,o,e
    def get(self,exei:str): return self.update(exei)[0]
    def update(self,exei:str):
        exe = exei.lower()
        up = False
        if exe.endswith('.exe'): exe = exe[:-4]
        if exe in self.db:
            cd = os.getcwd()
            os.chdir(BDIR)
            exi = self.db[exe]
            t = int(time())
            if exe in self.udb and self.udb[exe] < exi.get('ts',0): os.remove('bin/' + exi['p'])
            if not os.path.exists('bin/' + exi['p']):
                up = True
                print('Downloading',exe)
                for e in exi['fs']:
                    if type(e) == str: e = {'u':e,'p':e.split('?')[0].split('/')[-1]}
                    elif type(e) == list: e = {'u':e[0],'p':e[1]}
                    if 'p' in e: p = 'bin/' + e['p']
                    else:
                        if e.get('ex'): ex = e['ex']
                        else:
                            ex = e['u'].split('?')[0].split('/')[-1].lower()
                            if ex.split('.')[-2] == 'tar': ex = '.tar.' + ex.split('.')[-1]
                            else: ex = '.' + ex.split('.')[-1]
                        p = gtmp('.exe' if ex in ('run','inno','nsis') else ex)

                    if e['u'] == '.': p,ex = 'bin/bin.7z','.7z'
                    else: self.dl(e['u'],p,verify=e.get('v',True))
                    if 'x' in e:
                        bk = self.print_try
                        self.print_try = False

                        self.ext(p,ex,e['x'])

                        self.print_try = bk
                        if e['u'] != '.': os.remove(p)
            exei = os.path.abspath('bin/' + exi['p'])
            self.udb[exe] = t
            self.save()
            os.chdir(cd)
        return exei,up
    def ext(self,p:str,ex:str,xl:dict):
        if ex in ('.zip','.nupkg'):
            with zipfile.ZipFile(p,'r') as z:
                for tx in xl:
                    if tx == '*':
                        os.makedirs('bin/' + xl[tx],exist_ok=True)
                        z.extractall('bin/' + xl[tx])
                    elif type(xl[tx]) == dict:
                        if '?ex' in xl[tx]: ex = xl[tx].pop('?ex')
                        else: ex = os.path.splitext(tx)[1].lower()
                        tf = gtmp(ex)
                        xopen(tf,'wb').write(z.read(tx))
                        self.ext(tf,ex,xl[tx])
                        os.remove(tf)
                    else: xopen('bin/' + xl[tx],'wb').write(z.read(tx))
        elif ex in ('.tgz','.tar.gz'):
            with tarfile.open(p,'r:gz') as z:
                for tx in xl: xopen('bin/' + xl[tx],'wb').write(z.extractfile(tx).read())
        elif ex in ['.txz','.tar.xz']:
            with tarfile.open(p,'r:xz') as z:
                for tx in xl: xopen('bin/' + xl[tx],'wb').write(z.extractfile(tx).read())
        elif ex in ('.tzt','.tar.zst'):
            td = gtmp()
            self.run(['7z','x','-y','-o' + td,p])
            with tarfile.open(td + '/' + os.listdir(td)[0],'r') as z:
                for tx in xl: xopen('bin/' + xl[tx],'wb').write(z.extractfile(tx).read())
            rmtree(td)
        elif ex in ('.7z','.arj','.zipx','nsis','.lha'):
            td = gtmp()
            self.run(['7z','x','-y','-o' + td,'-aoa',p])
            for tx in xl: copy(td + '/' + tx,'bin/' + xl[tx])
            try: rmtree(td)
            except PermissionError: pass
        elif ex == '.rar':
            td = gtmp()
            self.run(['unrar','x','-or','-op' + td,p])
            for tx in xl: copy(td + '/' + tx,'bin/' + xl[tx])
            rmtree(td)
        elif ex == '.msi':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run(['lessmsi','x',p,td + '\\'])
            for tx in xl: copy(td + '/SourceDir/' + tx,'bin/' + xl[tx])
            rmtree(td)
        elif ex == '.deb':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run(['7z','x','-y','-o' + td,p])
            with tarfile.open(td + '/data.tar','r') as z:
                for tx in xl: xopen('bin/' + xl[tx],'wb').write(z.extractfile('./' + tx).read())
            rmtree(td)
        elif ex == 'inno':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run(['innounp-2','-x','-b','-m','-d' + td,'-u','-h','-o','-y',p])
            for tx in xl: copy(td + '/' + ('{app}/' if not tx.startswith(('{app}/','{tmp}/')) else '') + tx,'bin/' + xl[tx])
            rmtree(td)
        elif ex == 'run':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run([p,'-y'],stdin='\n',getexe=False,cwd=td)
            for tx in xl: copy(td + '/' + tx,'bin/' + xl[tx])
            rmtree(td)
        else: raise NotImplementedError(p + f' [{ex}]')
    def dl(self,url:str,out:str,verify=True):
        start = 0
        kwargs = {}
        if not verify:
            cl = httpx
            kwargs['verify'] = False
        else: cl = self.c
        try:
            with xopen(out,'wb') as f:
                for _ in range(10):
                    try:
                        with cl.stream("GET",url,headers={'Range':f'bytes={start}-'},follow_redirects=True,**kwargs) as r:
                            if r.headers.get('Content-Length') and not int(r.headers['Content-Length']): continue
                            for c in r.iter_bytes(4096): f.write(c)
                        break
                    except (httpx.ConnectError,httpx.ConnectTimeout): pass
                    except httpx.ReadTimeout: start = f.tell()
                else: f.write(cl.get(url,follow_redirects=True,**kwargs).content)
        except:
            if os.path.exists(out): os.remove(out)
            raise

    def save(self):
        open((BDIR or '.') + '/' + self.udbp,'w',encoding='utf-8').write(json.dumps(self.udb,ensure_ascii=False,separators=(',',':')))

from io import open
