import os,sys,sysconfig,subprocess,re,httpx
from time import sleep
from hashlib import sha256

SRCD = os.path.dirname(os.path.abspath(__file__))
def get_src(p:str): return os.path.join(SRCD,p)
LIBD = os.path.join(SRCD,'.lib')
os.makedirs(LIBD,exist_ok=True)
FS = [get_src(x) for x in ('unipyxx.c','util.h','comp.c','crypt.c','ext.c')]
XEXR = re.compile(r'(?m)^XEXPORT [^\(]+ ([\w_]+)\('.encode())
IMPR = re.compile(r'(?m)^XIMPORT\(([^\)]+)\)'.encode())
DLLP = SRCD + ('.dll' if sys.platform == 'win32' else '.so')

def remove(f:str):
    for _ in range(5):
        try: os.remove(f)
        except PermissionError: sleep(0.1)
        else: break

DLDB = {
    'kernel32':('kernel32.lib',None),
    'xcompress':('xcompress64.lib','https://raw.githubusercontent.com/NativeFunction/SC-CL/refs/heads/master/lib/xcompress64.lib'),
    # cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -Wno-author "-DCMAKE_POLICY_VERSION_MINIMUM=3.5" -DBUILD_SHARED_LIBS=OFF -A x64
    # cmake --build build -j <cores> --config Release
    'lzfse':('lzfse.lib',0), # static https://github.com/lzfse/lzfse
    # cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -Wno-author -A x64 -DZSTD_BUILD_STATIC=ON -DZSTD_BUILD_SHARED=OFF -DZSTD_BUILD_COMPRESSION=OFF -DZSTD_BUILD_DICTBUILDER=OFF -DZSTD_LEGACY_SUPPORT=1
    # cmake --build build -j <cores> --config Release
    'zstd':('zstd_static.lib',0), # static https://github.com/facebook/zstd
    'unimplode6a':('unimplode6a.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/unimplode6a.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'ozunreduce':('ozunreduce.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/ozunreduce.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'ozunshrink':('ozunshrink.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/ozunshrink.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'lpaq8_zzz':('lpaq8_zzz.h','https://raw.githubusercontent.com/WangXuan95/TinyZZZ/refs/heads/main/src/lpaq8CD.c'),
}
def get_lib(n:str):
    if DLDB[n][1] == 0: return os.path.join(LIBD + 'x',DLDB[n][0])
    elif DLDB[n][1] is None: return DLDB[n][0]
    p = os.path.join(LIBD,DLDB[n][0])
    if not os.path.exists(p):
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
        cmd  = ['/Ox','/GS-','/GR-','/Gs999999','/LD','/I',LIBD,'/TC',*FS,f'/Fe:{DLLP}','/link','/MANIFEST:NO','/MERGE:.rdata=.text','/OPT:REF','/OPT:ICF','/ALIGN:128',
                '/NODEFAULTLIB:MSVCRT','/IGNORE:4108','/IGNORE:4217','/IGNORE:4286'] + ['/EXPORT:' + x for x in xfncs]
        for p in env['PATH'].split(';'):
            if os.path.exists(p + '/cl.exe') and os.path.isfile(p + '/cl.exe'): cc = os.path.join(p,'cl.exe');break
    if cc is None: raise ValueError('No C compiler found')

    if os.path.exists(DLLP):
        if os.path.exists(DLLP + '.bak'): remove(DLLP + '.bak')
        os.rename(DLLP,DLLP + '.bak')
    pls = os.listdir()
    r = subprocess.call([cc] + cmd + [l for l in libs if l.endswith(('.a','.lib'))],env=env,stdout=-3 if quiet else None,stderr=-2 if quiet else None)
    ex = ('exp','lib','a','pdb','obj')
    for ex in ex:
        dnf = os.path.splitext(DLLP)[0] + '.' + ex
        if os.path.exists(dnf): remove(dnf)
    for p in os.listdir():
        if p.endswith(ex) and p not in pls: remove(p)
    if r:
        if os.path.exists(DLLP + '.bak'): os.rename(DLLP + '.bak',DLLP)
    elif os.path.exists(DLLP + '.bak'): remove(DLLP + '.bak')
    if not r: open(DLLP,'ab').write(ch)
    return r

if __name__ == '__main__':
    sys.exit(compile())
