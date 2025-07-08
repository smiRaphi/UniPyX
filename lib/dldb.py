import json,httpx,os,subprocess,zipfile,tarfile
from shutil import copyfile,rmtree
from time import sleep

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
        self.c = httpx.Client()
        self.print_try = False
        if not os.path.exists(self.dbp):
            pass
        self.db = json.load(xopen(self.dbp))

    def run(self,cmd:list,stdin:bytes|str=None,text=True,getexe=True,timeout=0,useos=False) -> tuple[int,str|bytes,str|bytes]:
        if self.print_try: print('Trying with',cmd[0])
        if type(cmd) == list and getexe: cmd[0] = self.get(cmd[0])
        if type(stdin) == str and not text: stdin = stdin.encode()
        if useos:
            r = os.system((subprocess.list2cmdline(cmd) if type(cmd) == list else cmd) + ' >NUL')
            o = e = None
        else:
            p = subprocess.Popen([str(x) for x in cmd] if type(cmd) == list else cmd,text=text,encoding=('cp437' if text else None),stdout=-1,stderr=-1,stdin=-1 if stdin != None else None)
            if timeout:
                for _ in range(timeout*10):
                    if p.poll() != None: break
                    sleep(0.1)
                else: p.kill()
                o,e = p.stdout.read(),p.stderr.read()
            else: o,e = p.communicate(input=stdin)
            r = p.returncode
        return r,o,e
    def get(self,exei:str):
        cd = os.getcwd()
        os.chdir(BDIR)
        exe = exei.lower()
        if exe.endswith('.exe'): exe = exe[:-4]
        if exe in self.db:
            if not os.path.exists('bin/' + self.db[exe]['p']):
                print('Downloading',exe)
                for e in self.db[exe]['fs']:
                    if type(e) == str: e = {'u':e,'p':e.split('?')[0].split('/')[-1]}
                    elif type(e) == list: e = {'u':e[0],'p':e[1]}
                    if 'p' in e: p = 'bin/' + e['p']
                    else:
                        sux = e['u'].split('?')[0].split('/')[-1].lower()
                        if sux.split('.')[-2] == 'tar': sux = '.tar.' + sux.split('.')[-1]
                        else: sux = '.' + sux.split('.')[-1]
                        ex = e.get('ex',sux)
                        p = gtmp(ex)
                    self.dl(e['u'],p)
                    if 'x' in e:
                        bk = self.print_try
                        self.print_try = False
                        if ex == '.zip':
                            with zipfile.ZipFile(p,'r') as z:
                                for tx in e['x']: xopen('bin/' + e['x'][tx],'wb').write(z.read(tx))
                        elif ex in ['.tgz','.tar.gz']:
                            with tarfile.open(p,'r:gz') as z:
                                for tx in e['x']: xopen('bin/' + e['x'][tx],'wb').write(z.extractfile(tx).read())
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
                            self.run(['msiexec','/a',p,'/qb','TARGETDIR=' + td],getexe=False)
                            for tx in e['x']: copy(td + '/' + tx,'bin/' + e['x'][tx])
                            rmtree(td)
                        else: raise NotImplementedError(p + f' [{ex}]')
                        self.print_try = bk
                        os.remove(p)
            exei = os.path.abspath('bin/' + self.db[exe]['p'])
        os.chdir(cd)
        return exei
    def dl(self,url:str,out:str):
        with xopen(out,'wb') as f:
            while True:
                try:
                    with self.c.stream("GET",url,follow_redirects=True) as r:
                        for c in r.iter_bytes(4096): f.write(c)
                    break
                except httpx.ConnectError: pass
