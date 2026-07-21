import sys,os,subprocess

BDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(BDIR + '\\bin\\pip',exist_ok=True)
sys.path.insert(0,BDIR + '\\bin\\pip')
def pip(*pkgs,error=False):
    r = subprocess.run([sys.executable,'-m','pip','install',*pkgs,'-U','-t',BDIR + '\\bin\\pip'],stdout=-1,stderr=-2)
    if error and r.returncode: raise RuntimeError(r.stdout.decode('cp437'))
    return r.stdout.decode('cp437')

try: import httpx
except (ImportError,ModuleNotFoundError):
    pip('httpx')
    import httpx

import json,zipfile,tarfile,importlib.util
from shutil import copyfile,copytree,rmtree
from time import sleep,time
from multiprocessing.pool import ThreadPool

def gtmp(suf=''): return os.getenv('TEMP').strip('\\') + '\\tmp' + os.urandom(8).hex() + suf
def xopen(f:str,m='r',encoding='utf-8'):
    f = os.path.abspath(f)
    os.makedirs(os.path.dirname(f),exist_ok=True)
    if 'b' in m: return open(f,m)
    return open(f,m,encoding=encoding)
def copy(i:str,o:str):
    o = os.path.abspath(o)
    os.makedirs(os.path.dirname(o),exist_ok=True)
    if os.path.isdir(i): copytree(i,o)
    else: copyfile(i,o)
class DLDB:
    def __init__(self):
        self.bin_path = BDIR + '\\bin\\'

        self.dbp = BDIR + '/lib/dldb.json'
        self.udbp = self.bin_path + 'updb.json'
        self.c = httpx.Client()
        self.print_try = False
        self._old_print_try = []

        self.db = json.load(xopen(self.dbp))
        self.pdb = {x:self.db[x] for x in self.db if 'pip' in self.db[x]}
        for x in self.pdb: self.db.pop(x)

        if os.path.exists(self.udbp):
            try: self.udb = json.load(xopen(self.udbp))
            except json.decoder.JSONDecodeError:
                print('WARNING: download cache is invalid, deleting')
                os.remove(self.udbp)
                self.udb = {}
        else: self.udb = {}
        if not 'httpx' in self.udb: self.udb['httpx'] = int(time())

        self.piptries = {}
        self.pipinstalled = {}
        class DLDBPip:
            @classmethod
            def find_spec(cls,fullname,path,target=None):
                n = fullname.split('.')[0]
                if n in self.pdb:
                    self.pipinstalled[n] -= 1
                    if self.pipinstalled[n] != 0: return
                    if n in self.piptries:
                        print(self.piptries[n])
                        raise Exception('pip Import Error')
                    return importlib.util.find_spec(self.pip(n,True).get('name',n))
        class DLDBPipUpdate:
            @classmethod
            def find_spec(cls,fullname,path,target=None):
                n = fullname.split('.')[0]
                if n in self.pdb:
                    if n not in self.pipinstalled: self.pipinstalled[n] = 0
                    self.pipinstalled[n] += 1
                    if n in self.udb and self.udb[n] < self.pdb[n].get('ts',0): self.pip(n)

        sys.meta_path.insert(1,DLDBPipUpdate)
        sys.meta_path.append(DLDBPip)

    def run(self,cmd:list,stdin:bytes|str=None,text=True,getexe=True,timeout=0,useos=False,print_try=True,print_out=False,**kwargs) -> tuple[int,str|bytes,str|bytes]:
        if print_try and self.print_try: print('Trying with',cmd[0])
        if type(cmd) == list and getexe: cmd[0] = self.get(cmd[0])
        if type(stdin) == str and not text: stdin = stdin.encode()
        if useos:
            if stdin:
                tfi = gtmp('.i')
                if type(stdin) == str: stdin = stdin.encode()
                xopen(tfi,'wb').write(stdin)
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
            p = subprocess.Popen([str(x) for x in cmd] if type(cmd) == list else cmd,text=text,encoding=('cp437' if text else None),stdout=None if print_out else -1,stderr=None if print_out else -1,stdin=-1 if stdin is not None else None,**kwargs)
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
            if exe in self.udb and self.udb[exe] < exi.get('ts',0) and os.path.exists(self.bin_path + exi['p']):
                if os.path.isdir(self.bin_path + exi['p']): rmtree(self.bin_path + exi['p'])
                else: os.remove(self.bin_path + exi['p'])
            if exi.get('fs',1) == None: os.makedirs(self.bin_path + exi['p'],exist_ok=True)
            if not os.path.exists(self.bin_path + exi['p']):
                if not 'fs' in exi: return None,False
                t = int(time())
                up = True
                print('Downloading',exe)
                for e in exi['fs']:
                    if type(e) == str: e = {'u':e,'p':e.split('?')[0].split('/')[-1]}
                    elif type(e) == list: e = {'u':e[0],'p':e[1]}
                    if 'p' in e: p = self.bin_path + e['p']
                    elif e['u'] is not None:
                        if e.get('ex'): ex = e['ex']
                        else:
                            ex = e['u'].split('?')[0].split('/')[-1].lower()
                            if not '.' in ex: ex = ''
                            elif ex.split('.')[-2] == 'tar': ex = '.tar.' + ex.split('.')[-1]
                            else: ex = '.' + ex.split('.')[-1]
                        p = gtmp('.exe' if ex in {'run','inno','nsis'} else ex)

                    if e['u'] == '.': p,ex = self.bin_path + 'bin.7z','.7z'
                    elif 'github' in e: self.gh_dir(e['u'],self.bin_path + e['github'])
                    elif e['u'] is not None: self.dl(e['u'],p,verify=e.get('v',True))
                    if 'x' in e:
                        bk = self.print_try
                        self.print_try = False

                        self.ext(p,ex,e['x'])

                        self.print_try = bk
                        if e['u'] != '.': os.remove(p)
                    if 'cmd' in e: self.run(e['cmd'],print_try=False,cwd=self.bin_path[:-1])
                    if 'del' in e:
                        for d in e['del']:
                            if os.path.exists(self.bin_path + d):
                                if os.path.isdir(self.bin_path + d): rmtree(self.bin_path + d)
                                else:
                                    for _ in range(50):
                                        try: os.remove(self.bin_path + d)
                                        except PermissionError: sleep(0.1)
                                        else: break
                self.udb[exe] = t
            exei = os.path.abspath(self.bin_path + exi['p'])
            self.save()
            os.chdir(cd)
        return exei,up
    def ext(self,p:str,ex:str,xl:dict):
        if ex in {'.zip','.nupkg'}:
            xall = False
            td = gtmp()
            with zipfile.ZipFile(p,'r') as z:
                for tx in xl:
                    if tx == '*':
                        os.makedirs(self.bin_path + xl[tx],exist_ok=True)
                        z.extractall(self.bin_path + xl[tx])
                    elif type(xl[tx]) == dict:
                        if '?ex' in xl[tx]: ex = xl[tx].pop('?ex')
                        else: ex = os.path.splitext(tx)[1].lower()
                        tf = gtmp(ex)
                        xopen(tf,'wb').write(z.read(tx))
                        self.ext(tf,ex,xl[tx])
                        os.remove(tf)
                    elif tx[-1] == '/':
                        if not xall:
                            os.makedirs(td,exist_ok=True)
                            z.extractall(td)
                            xall = True
                        copy(td + '/' + tx,self.bin_path + xl[tx])
                    else:
                        d = z.read(tx)
                        xopen(self.bin_path + xl[tx],'wb').write(d)
            if xall: rmtree(td)
        elif ex in {'.tgz','.tar.gz'}:
            with tarfile.open(p,'r:gz') as z:
                for tx in xl: xopen(self.bin_path + xl[tx],'wb').write(z.extractfile(tx).read())
        elif ex in {'.txz','.tar.xz'}:
            with tarfile.open(p,'r:xz') as z:
                for tx in xl: xopen(self.bin_path + xl[tx],'wb').write(z.extractfile(tx).read())
        elif ex in {'.tzt','.tar.zst'}:
            td = gtmp()
            self.run(['7z','x','-y','-o' + td,p])
            with tarfile.open(td + '/' + os.listdir(td)[0],'r') as z:
                for tx in xl: xopen(self.bin_path + xl[tx],'wb').write(z.extractfile(tx).read())
            rmtree(td)
        elif ex in {'.7z','.arj','.zipx','nsis','.lha'}:
            td = gtmp()
            self.run(['7z','x','-y','-o' + td,'-aoa',p])
            for tx in xl: copy(td + '/' + tx,self.bin_path + xl[tx])
            for _ in range(5):
                try: rmtree(td)
                except PermissionError: sleep(0.1)
                else: break
        elif ex == '.rar':
            td = gtmp()
            self.run(['unrar','x','-or','-op' + td,p])
            for tx in xl: copy(td + '/' + tx,self.bin_path + xl[tx])
            for _ in range(5):
                try: rmtree(td)
                except PermissionError: sleep(0.1)
                else: break
        elif ex == '.msi':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run(['lessmsi','x',p,td + '\\'])
            for tx in xl: copy(td + '/SourceDir/' + tx,self.bin_path + xl[tx])
            rmtree(td)
        elif ex == '.deb':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run(['7z','x','-y','-o' + td,p])
            with tarfile.open(td + '/data.tar','r') as z:
                for tx in xl: xopen(self.bin_path + xl[tx],'wb').write(z.extractfile('./' + tx).read())
            rmtree(td)
        elif ex == 'inno':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run(['innounp-2','-x','-b','-m','-d' + td,'-u','-h','-o','-y',p])
            for tx in xl: copy(td + '/' + ('{app}/' if not tx.startswith(('{app}/','{tmp}/')) else '') + tx,self.bin_path + xl[tx])
            rmtree(td)
        elif ex == 'run':
            td = gtmp()
            os.makedirs(td,exist_ok=True)
            self.run([p,'-y'],stdin='\n',getexe=False,cwd=td)
            for tx in xl: copy(td + '/' + tx,self.bin_path + xl[tx])
            rmtree(td)
        else: raise NotImplementedError(p + f' [{ex}]')
    def dl(self,url:str,out:str,verify=True):
        start = 0
        kwargs = {}
        if not verify:
            cl = httpx
            kwargs['verify'] = False
        else: cl = self.c
        clfr = False
        try:
            with xopen(out,'wb') as f:
                for _ in range(10):
                    try:
                        with cl.stream("GET",url,headers={'Range':f'bytes={start}-'},follow_redirects=True,**kwargs) as r:
                            if r.headers.get('Content-Length') and not int(r.headers['Content-Length']): continue
                            for c in r.iter_bytes(4096):
                                if not clfr:
                                    if b'<title>Just a moment...</title>' in c and b'://challenges.cloudflare.com' in c: raise ValueError(f'Cloudflare ({url})')
                                    clfr = True
                                f.write(c)
                        break
                    except (httpx.ConnectError,httpx.ConnectTimeout): pass
                    except httpx.ReadTimeout: start = f.tell()
                else: f.write(cl.get(url,follow_redirects=True,**kwargs).content)
        except:
            if os.path.exists(out): os.remove(out)
            raise
    def gh_dir(self,url,out,_first=True):
        if _first:
            self.ghthp = ThreadPool()
            self.ghq = []

        d = self.c.get(url,headers={'accept':'application/json','x-requested-with':'XMLHttpRequest'}).json()
        if 'meta' in d and 'title' in d['meta']: tit = d['meta']['title']
        d = d['payload']
        out = out.strip('/')
        os.makedirs(out,exist_ok=True)
        if not 'refInfo' in d:
            if not 'codeViewTreeRoute' in d: raise ValueError
            d = d['codeViewTreeRoute']
        if not 'repo' in d:
            if not ' · ' in tit: raise ValueError
            tit = tit.rsplit(' · ',1)[1]
            d['repo'] = {'ownerLogin':tit.split('/')[0],'name':tit.split('/')[1]}
        b = f'https://github.com/{d["repo"]["ownerLogin"]}/{d["repo"]["name"]}/tree/{d["refInfo"]["name"]}/'
        for x in d['tree']['items']:
            if x['contentType'] == 'directory':
                self.ghq.append(self.ghthp.apply_async(self.gh_dir,(b + x['path'],out + '/' + x['name'],False)))
            elif x['contentType'] == 'file':
                self.dl(f'https://raw.githubusercontent.com/{d["repo"]["ownerLogin"]}/{d["repo"]["name"]}/refs/heads/{d["refInfo"]["name"]}/{x["path"]}',out + '/' + x['name'])

        if _first:
            for x in self.ghq: x.get()
            self.ghthp.close()
            self.ghthp.join()
    def pip(self,n:str,install=False) -> dict:
        e = self.pdb[n]
        if n in self.udb and self.udb[n] > e.get('ts',0) and not install: return e
        print('Downloading',n)
        t = int(time())
        self.piptries[n] = pip(e['pip'])
        self.udb[n] = t
        self.save()
        return e

    def try_custom(self):
        if self.print_try: print('Trying with custom extractor')
    def set_temp_print(self,v:bool):
        self._old_print_try.append(self.print_try)        
        self.print_try = v
    def reset_temp_print(self):
        if not self._old_print_try: return
        self.print_try = self._old_print_try.pop()

    def save(self):
        open(self.udbp,'w',encoding='utf-8').write(json.dumps(self.udb,ensure_ascii=False,separators=(',',':')))

from io import open
