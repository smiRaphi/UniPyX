#define DUMMY /*

import os,sys,httpx,sysconfig,subprocess
if sys.maxsize <= 2**32: raise RuntimeError("64-bit Python required")

DLLP = os.path.splitext(__file__)[0] + ('.dll' if sys.platform == 'win32' else '.so')
XCF = os.path.join(os.path.dirname(__file__),'xcompress64.lib')
if not os.path.exists(XCF) or not os.path.getsize(XCF):
    with open(XCF,'wb') as xf:
        xf.write(httpx.get('https://raw.githubusercontent.com/NativeFunction/SC-CL/refs/heads/master/lib/xcompress64.lib',follow_redirects=True).content)

cc = None
env = os.environ.copy()
if sysconfig.get_config_var('CC'):
    cc = sysconfig.get_config_var('CC')
    cmd = ['-O3','-shared','-o',DLLP,__file__]
elif sys.platform == 'win32':
    from setuptools import msvc
    env |= {x.upper():v for x,v in msvc.EnvironmentInfo('x64' if sys.maxsize > 2**32 else 'x86').return_env().items()}
    cmd = ['/Ox','/GS-','/GR-','/Gs999999','/LD','/TC',__file__,f'/Fe:{DLLP}','/link','/MANIFEST:NO','/MERGE:.rdata=.text','/OPT:REF','/OPT:ICF','/ALIGN:128','/ENTRY:DllMain',
           'kernel32.lib','vcruntime.lib'] + ['/EXPORT:XMem' + x for x in ['CreateDecompressionContext','Decompress','DecompressSegmentTD','DestroyDecompressionContext']]
    for p in env['PATH'].split(';'):
        if os.path.exists(p + '/cl.exe') and os.path.isfile(p + '/cl.exe'): cc = p + '/cl.exe';break
if cc is None: raise ValueError('No C compiler found')
cmd.append(XCF)

if os.path.exists(DLLP):
    if os.path.exists(DLLP + '.bak'): os.remove(DLLP + '.bak')
    os.rename(DLLP,DLLP + '.bak')

r = subprocess.call([cc] + cmd,env=env)
for ex in {'exp','lib','a','pdb','obj'}:
    ex = os.path.splitext(DLLP)[0] + '.' + ex
    if os.path.exists(ex): os.remove(ex)
    ex = os.path.basename(ex)
    if os.path.exists(ex): os.remove(ex)
if r:
    if os.path.exists(DLLP + '.bak'): os.rename(DLLP + '.bak',DLLP)
elif os.path.exists(DLLP + '.bak'): os.remove(DLLP + '.bak')
sys.exit(r)

'''*/

#include <stdint.h>

#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif
typedef unsigned long DWORD;

EXPORT int __stdcall DllMain(void* a,unsigned long b,void* c) { return 1; }

#ifdef __cplusplus
extern "C" {
#endif

#pragma comment(linker, "/include:XMemCreateDecompressionContext")
EXPORT long __stdcall XMemCreateDecompressionContext(int CodecType, const void *pCodecParams, DWORD Flags, void **pContext);
#pragma comment(linker, "/include:XMemDestroyDecompressionContext")
EXPORT void __stdcall XMemDestroyDecompressionContext(void *pContext);
#pragma comment(linker, "/include:XMemDecompress")
EXPORT long __stdcall XMemDecompress(void *pContext, void *pDestination, size_t *pDestSize, const void *pSource, size_t SrcSize);
#pragma comment(linker, "/include:XMemDecompressSegmentTD")
EXPORT long __stdcall XMemDecompressSegmentTD(void *pContext, void *pDestination, size_t *pDestSize, const void *pSource,
                                           size_t SrcSize, size_t DestSize, size_t Offset);

#ifdef __cplusplus
}
#endif

/*'''#*/
