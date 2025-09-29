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

    def run(self,cmd:list,stdin:bytes|str=None,text=True,getexe=True,timeout=0,useos=False,print_try=True,**kwargs) -> tuple[int,str|bytes,str|bytes]:
        if print_try and self.print_try: print('Trying with',cmd[0])
        if type(cmd) == list and getexe: cmd[0] = self.get(cmd[0])
        if type(stdin) == str and not text: stdin = stdin.encode()
        if useos:
            r = os.system((subprocess.list2cmdline(cmd) if type(cmd) == list else cmd) + ' >NUL')
            o = e = None
        else:
            p = subprocess.Popen([str(x) for x in cmd] if type(cmd) == list else cmd,text=text,encoding=('cp437' if text else None),stdout=-1,stderr=-1,stdin=-1 if stdin != None else None,**kwargs)
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
                        p = gtmp(ex)

                    self.dl(e['u'],p)
                    if 'x' in e:
                        bk = self.print_try
                        self.print_try = False
                        if ex == '.zip':
                            with zipfile.ZipFile(p,'r') as z:
                                for tx in e['x']:
                                    if tx == '*':
                                        os.makedirs('bin/' + e['x'][tx],exist_ok=True)
                                        z.extractall('bin/' + e['x'][tx])
                                    else: xopen('bin/' + e['x'][tx],'wb').write(z.read(tx))
                        elif ex in ['.tgz','.tar.gz']:
                            with tarfile.open(p,'r:gz') as z:
                                for tx in e['x']: xopen('bin/' + e['x'][tx],'wb').write(z.extractfile(tx).read())
                        elif ex in ['.txz','.tar.xz']:
                            with tarfile.open(p,'r:xz') as z:
                                for tx in e['x']: xopen('bin/' + e['x'][tx],'wb').write(z.extractfile(tx).read())
                        elif ex in ['.tzt','.tar.zst']:
                            td = gtmp()
                            self.run(['7z','x','-y','-o' + td,p])
                            with tarfile.open(td + '/' + os.listdir(td)[0],'r') as z:
                                for tx in e['x']: xopen('bin/' + e['x'][tx],'wb').write(z.extractfile(tx).read())
                            rmtree(td)
                        elif ex == '.7z':
                            td = gtmp()
                            self.run(['7z','x','-y','-o' + td,p])
                            for tx in e['x']: copy(td + '/' + tx,'bin/' + e['x'][tx])
                            rmtree(td)
                        elif ex == '.rar':
                            td = gtmp()
                            self.run(['unrar','x','-or','-op' + td,p])
                            for tx in e['x']: copy(td + '/' + tx,'bin/' + e['x'][tx])
                            rmtree(td)
                        elif ex == '.msi':
                            td = gtmp()
                            os.makedirs(td,exist_ok=True)
                            self.run(['lessmsi','x',p,td + '\\'],getexe=False)
                            for tx in e['x']: copy(td + '/SourceDir/' + tx,'bin/' + e['x'][tx])
                            rmtree(td)
                        elif ex == '.deb':
                            td = gtmp()
                            os.makedirs(td,exist_ok=True)
                            self.run(['7z','x','-y','-o' + td,p])
                            with tarfile.open(td + '/data.tar','r') as z:
                                for tx in e['x']: xopen('bin/' + e['x'][tx],'wb').write(z.extractfile('./' + tx).read())
                            rmtree(td)
                        else: raise NotImplementedError(p + f' [{ex}]')
                        self.print_try = bk
                        os.remove(p)
            exei = os.path.abspath('bin/' + exi['p'])
            self.udb[exe] = t
            self.save()
            os.chdir(cd)
        return exei,up
    def dl(self,url:str,out:str):
        start = 0
        try:
            with xopen(out,'wb') as f:
                for _ in range(10):
                    try:
                        with self.c.stream("GET",url,headers={'Range':f'bytes={start}-'},follow_redirects=True) as r:
                            if r.headers.get('Content-Length') and not int(r.headers['Content-Length']): continue
                            for c in r.iter_bytes(4096): f.write(c)
                        break
                    except httpx.ConnectError: pass
                    except httpx.ReadTimeout: start = f.tell()
                else: f.write(self.c.get(url,follow_redirects=True).content)
        except:
            if os.path.exists(out): os.remove(out)
            raise

    def save(self):
        open((BDIR or '.') + '/' + self.udbp,'w',encoding='utf-8').write(json.dumps(self.udb,ensure_ascii=False,separators=(',',':')))

from io import open
