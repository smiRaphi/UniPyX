import os,sys,sysconfig,subprocess,re,httpx
from hashlib import sha256

SRCD = os.path.dirname(os.path.abspath(__file__))
def get_src(p:str): return os.path.join(SRCD,p)
LIBD = os.path.join(SRCD,'.lib')
os.makedirs(LIBD,exist_ok=True)
FS = [get_src(x) for x in ('unipyxx.c','util.h','comp.c','crypt.c','ext.c')]
XEXR = re.compile(r'(?m)^XEXPORT [^\(]+ ([\w_]+)\('.encode())
IMPR = re.compile(r'(?m)^XIMPORT\(([^\)]+)\)'.encode())
DLLP = SRCD + ('.dll' if sys.platform == 'win32' else '.so')

DLDB = {
    'kernel32':('kernel32.lib',None),
    'xcompress':('xcompress64.lib','https://raw.githubusercontent.com/NativeFunction/SC-CL/refs/heads/master/lib/xcompress64.lib'),
    'unimplode6a':('unimplode6a.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/unimplode6a.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'ozunreduce':('ozunreduce.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/ozunreduce.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'ozunshrink':('ozunshrink.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/ozunshrink.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
}
def get_lib(n:str):
    p = os.path.join(LIBD,DLDB[n][0])
    if not os.path.exists(p):
        if DLDB[n][1] is None: return DLDB[n][0]
        d = httpx.get(DLDB[n][1],follow_redirects=True).content
        if len(DLDB[n]) > 2:
            d = d.replace(b'\r',b'')
            for x in DLDB[n][2:]:
                if isinstance(x[0],int): d = d[:x[0]] + x[1] + d[x[0]:]
                else: d = d.replace(x[0],x[1])
        open(p,'wb').write(d)
    return p
def compile(quiet=False):
    cc = None
    env = os.environ.copy()
    ch = sha256()
    libs = set()
    xfncs = set()
    for x in sorted(FS):
        d = open(x,'rb').read().replace(b'\r',b'').strip(b'\n')
        ch.update(d)
        for fn in XEXR.findall(d): xfncs.add(fn.decode('utf-8'))
        for lns in IMPR.findall(d):
            for ln in lns.decode('utf-8').split(','): libs.add(ln.replace(' ','').replace('"',''))
    libs = [get_lib(x) for x in libs]
    ch = ch.digest()

    if sysconfig.get_config_var('CC'):
        print('WARNING: GCC is untested')
        cc = sysconfig.get_config_var('CC')
        cmd = ['-O3','-shared','-o',DLLP,*FS]
    elif sys.platform == 'win32':
        from setuptools import msvc
        env |= {x.upper():v for x,v in msvc.EnvironmentInfo('x64' if sys.maxsize > 2**32 else 'x86').return_env().items()}
        cmd  = ['/Ox','/GS-','/GR-','/Gs999999','/LD','/I',LIBD,'/TC',*FS,f'/Fe:{DLLP}','/link','/MANIFEST:NO','/MERGE:.rdata=.text','/OPT:REF','/OPT:ICF','/ALIGN:128','/ENTRY:DllMain',
               'vcruntime.lib','ucrt.lib'] + ['/EXPORT:' + x for x in xfncs]
        for p in env['PATH'].split(';'):
            if os.path.exists(p + '/cl.exe') and os.path.isfile(p + '/cl.exe'): cc = os.path.join(p,'cl.exe');break
    if cc is None: raise ValueError('No C compiler found')

    if os.path.exists(DLLP):
        if os.path.exists(DLLP + '.bak'): os.remove(DLLP + '.bak')
        os.rename(DLLP,DLLP + '.bak')
    pls = os.listdir()
    r = subprocess.call([cc] + cmd + [l for l in libs if l.endswith(('.a','.lib'))],env=env,stdout=-3 if quiet else None,stderr=-2 if quiet else None)
    ex = ('exp','lib','a','pdb','obj')
    for ex in ex:
        dnf = os.path.splitext(DLLP)[0] + '.' + ex
        if os.path.exists(dnf): os.remove(dnf)
    for p in os.listdir():
        if p.endswith(ex) and p not in pls: os.remove(p)
    if r:
        if os.path.exists(DLLP + '.bak'): os.rename(DLLP + '.bak',DLLP)
    elif os.path.exists(DLLP + '.bak'): os.remove(DLLP + '.bak')
    if not r: open(DLLP,'ab').write(ch)
    return r

if __name__ == '__main__':
    sys.exit(compile())
