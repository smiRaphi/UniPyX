import json,httpx,os,subprocess,zipfile
from shutil import copyfile,rmtree

def gtmp(suf=''): return os.getenv('TEMP').strip('\\') + '\\tmp' + os.urandom(8).hex() + suf
def xopen(f:str,m='wb',enc='utf-8'):
    f = os.path.abspath(f)
    os.makedirs(os.path.dirname(f),exist_ok=True)
    if 'b' in m: return open(f,m)
    return open(f,m,encoding=enc)
class DLDB:
    def __init__(self):
        self.dbp = 'bin/dldb.json'
        self.c = httpx.Client()
        if not os.path.exists(self.dbp):
            pass
        self.db = json.load(open(self.dbp,encoding='utf-8'))

    def run(self,cmd:list) -> tuple[int,bytes,bytes]:
        cmd[0] = self.get(cmd[0])
        p = subprocess.Popen(cmd,stdout=-1,stderr=-1)
        p.wait()
        return p.returncode,p.stdout.read(),p.stderr.read()
    def get(self,exei:str):
        exe = exei
        if exe.lower().endswith('.exe'): exe = exe[:-4]
        if exe in self.db:
            if not os.path.exists('bin/' + self.db[exe]['p']):
                print('Downloading',exe)
                for e in self.db[exe]['fs']:
                    if 'p' in e: p = 'bin/' + e['p']
                    else:
                        ex = e.get('ex','.' + e['u'].split('?')[0].split('.')[-1]).lower()
                        p = gtmp(ex)
                    self.dl(e['u'],p)
                    if 'x' in e:
                        if ex == '.zip':
                            with zipfile.ZipFile(p,'r') as z:
                                for tx in e['x']: xopen('bin/' + e['x'][tx],'wb').write(z.read(tx))
                        elif ex == '.msi':
                            td = gtmp()
                            os.makedirs(td,exist_ok=True)
                            subprocess.run(['msiexec','/a',p,'/qb','TARGETDIR=' + td],stdout=-1,stderr=-1)
                            for tx in e['x']: copyfile(td + '/Files/' + tx,'bin/' + e['x'][tx])
                            rmtree(td)
                        else: raise NotImplementedError(p + f' [{ex}]')
                        os.remove(p)
            return 'bin/' + self.db[exe]['p']
        return exei
    def dl(self,url:str,out:str):
        with xopen(out,'wb') as f:
            with self.c.stream("GET",url) as r:
                for c in r.iter_bytes(4096): f.write(c)
