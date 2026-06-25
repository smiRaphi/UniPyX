#define DUMMY /*

import os,sys
from hashlib import sha256
DLLP = os.path.splitext(__file__)[0] + ('.dll' if sys.platform == 'win32' else '.so')
CH = sha256(open(__file__,'rb').read().split(b"'''*" b"/",1)[1]).digest()
def asrt(c):
    if not c: raise ValueError

def compile(quiet=False):
    import sysconfig,subprocess
    cc = None
    env = os.environ.copy()
    if sysconfig.get_config_var('CC'):
        cc = sysconfig.get_config_var('CC')
        cmd = ['-O3','-shared','-o',DLLP,__file__]
    elif sys.platform == 'win32':
        from setuptools import msvc
        env |= {x.upper():v for x,v in msvc.EnvironmentInfo('x64' if sys.maxsize > 2**32 else 'x86').return_env().items()}
        cmd = ['/Ox','/GS-','/GR-','/Gs999999','/LD','/TC',__file__,f'/Fe:{DLLP}','/link','/MANIFEST:NO','/MERGE:.rdata=.text','/OPT:REF','/OPT:ICF','/ALIGN:16','/ENTRY:DllMain',
               'vcruntime.lib','ucrt.lib']
        for p in env['PATH'].split(';'):
            if os.path.exists(p + '/cl.exe') and os.path.isfile(p + '/cl.exe'): cc = p + '/cl.exe';break
    if cc is None: raise ValueError('No C compiler found')

    if os.path.exists(DLLP):
        if os.path.exists(DLLP + '.bak'): os.remove(DLLP + '.bak')
        os.rename(DLLP,DLLP + '.bak')
    r = subprocess.call([cc] + cmd,env=env,stdout=-3 if quiet else None,stderr=-2 if quiet else None)
    for ex in {'exp','lib','a','pdb','obj'}:
        ex = os.path.splitext(DLLP)[0] + '.' + ex
        if os.path.exists(ex): os.remove(ex)
        ex = os.path.basename(ex)
        if os.path.exists(ex): os.remove(ex)
    if r:
        if os.path.exists(DLLP + '.bak'): os.rename(DLLP + '.bak',DLLP)
    elif os.path.exists(DLLP + '.bak'): os.remove(DLLP + '.bak')
    if not r: open(DLLP,'ab').write(CH)
    return r

if __name__ == '__main__': sys.exit(compile())

import ctypes
u8 = ctypes.c_uint8
s8 = ctypes.c_int8
u32 = ctypes.c_uint32
u16 = ctypes.c_uint16
u64 = ctypes.c_uint64
szt = ctypes.c_size_t
sszt = ctypes.c_ssize_t
void = ctypes.c_void_p
P = ctypes.POINTER

def _1base_func(fnc,src,usize):
    i = (u8 * len(src)).from_buffer_copy(src)
    o = (u8 * ((len(src)*10) if usize == -1 else usize))()
    r = fnc(i,len(src),o,usize)
    if r < 0: raise RuntimeError(f'Decompression failed ({r})')
    return bytes(o)[:r]
def _2base_func(fnc,src,key):
    i = (u8 * len(src)).from_buffer_copy(src)
    o = (u8 * len(src))()
    k = (u8 * len(key)).from_buffer_copy(key)
    fnc(i,len(src),o,k,len(key))
    return bytes(o)
def _21base_func(fnc,src,key):
    b = (u8 * len(src)).from_buffer_copy(src)
    k = (u8 * len(key)).from_buffer_copy(key)
    fnc(b,len(src),k,len(key))
    return bytes(b)
def _3base_func(fnc,src):
    i = (u8 * len(src)).from_buffer_copy(src)
    o = (u8 * len(src))()
    fnc(i,len(src),o)
    return bytes(o)
def _4base_func(fnc,src):
    i = (u8 * len(src)).from_buffer_copy(src)
    return int(fnc(i,len(src)))
def _5base_func(fnc,src,seed):
    i = (u8 * len(src)).from_buffer_copy(src)
    return int(fnc(i,len(src),seed))

import struct
from hashlib import md5
from zlib import crc32

class X:
    MMFS = {};SELENE = {};EMPIRE_MAGIC = None
    def __init__(self):
        if not os.path.exists(DLLP): raise FileNotFoundError
        d = open(DLLP,'rb')
        d.seek(d.seek(0,2) - len(CH))
        ch = d.read(len(CH))
        d.close()
        if ch != CH:
            os.remove(DLLP)
            raise ValueError('DLL is out of date, deleted')

        self.dll = ctypes.CDLL(DLLP)
        for e in (
            ('decompress_lz10_raw', (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_lz11_raw', (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_lz40_raw', (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_blz_raw',  (P(u8),szt,P(u8),sszt),   sszt,0),
            ('decompress_lz4_fast', (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_lzss0_lsb',(P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_lzss0_msb',(P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_rtl_lz',   (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_vicious_lz',(P(u8),szt,P(u8),sszt),  sszt,1),
            ('decompress_huffman',  (P(u8),szt,P(u8),sszt,s8),sszt,0),
            ('decompress_ash0',     (P(u8),szt,P(u8)),        sszt,0),
            ('decompress_graw_bpe', (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_lzrw1kh',  (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_capcom_yz2',(P(u8),szt,P(u8),sszt),  sszt,1),
            ('decompress_d0llz3',   (P(u8),szt,P(u8),sszt),   sszt,1),

            ('decrypt_inv'  ,(P(u8),szt,P(u8)),void,3),
            ('decrypt_swp4' ,(P(u8),szt,P(u8)),void,3),
            ('decrypt_roll' ,(P(u8),szt,P(u8),P(u8),szt),void,2),
            ('decrypt_rolr' ,(P(u8),szt,P(u8),P(u8),szt),void,2),
            ('decrypt_xor'  ,(P(u8),szt,P(u8),P(u8),szt),void,2),
            ('decrypt_rxor' ,(P(u8),szt,P(u8),u8),void,0),
            ('decrypt_cxor' ,(P(u8),szt,P(u8),P(u8),szt),void,0),
            ('decrypt_dxor' ,(P(u8),szt,P(u8),P(u8),szt,P(u8),szt),void,0),
            ('decrypt_tea'  ,(P(u8),szt,P(u8),P(u8),s8),void,0),
            ('decrypt_rsdk3',(P(u8),szt,P(u8),P(u8)),void,0),
            ('decrypt_rsdk4',(P(u8),szt,u32,u32,P(u8),P(u8)),void,0),
            ('decrypt_rsdk5',(P(u8),szt,P(u8),P(u8)),void,0),
            ('decrypt_hornby',(P(u8),szt,u8,u8),void,0),
            ('init_mmfs',(P(u8),P(u8)),void,0),
            ('decrypt_mmfs',(P(u8),szt,P(u8)),void,0),
            ('init_selene',(P(u8),P(u8),szt,u32),void,0),
            ('decrypt_rc4_playpond',(P(u8),szt,P(u8),szt,szt),void,0),
            ('decrypt_zipcrypto',(P(u8),szt,P(u8),szt),void,2.1),
            ('decrypt_remedy_ras',(P(u8),szt,u32),void,0),
            ('init_empire_magic',(P(u8),),void,0),
            ('decrypt_empire_magic',(P(u8),szt,P(u8),szt,P(u8),u32),void,0),
            ('decrypt_tfit',(P(u8),szt,P(u8),P(u8),P(u8),P(u8),szt),void,0),

            ('hash_pivotal',(P(u8),szt),u32,4),
            ('hash_super_fast_le',(P(u8),szt),u32,4),
            ('hash_super_fast_be',(P(u8),szt),u32,4),
            ('hash_elf',(P(u8),szt),u32,4),
            ('hash_ap',(P(u8),szt),u32,4),
            ('hash_murmur2_le',(P(u8),szt,u32),u32,5),
            ('hash_murmur2_be',(P(u8),szt,u32),u32,5),
            ('hash_murmur2A_le',(P(u8),szt,u32),u32,5),
            ('hash_murmur2A_be',(P(u8),szt,u32),u32,5),
            ('hash_murmur2_64A_le',(P(u8),szt,u32),u64,5),
            ('hash_murmur2_64A_be',(P(u8),szt,u32),u64,5),
            ('hash_murmur2_64B_le',(P(u8),szt,u32),u64,5),
            ('hash_murmur2_64B_be',(P(u8),szt,u32),u64,5),
            ('hash_empire_magic',(P(u8),szt,s8),u32,0),
            ('mac_cmac_tfit',(P(u8),szt,P(u8),P(u8),P(u8),P(u8)),void,0),
        ):
            fnc = self.dll[e[0]]
            fnc.argtypes = e[1]
            fnc.restype = e[2]

            if e[3]:
                if e[3] == 1:
                    def wrapper(src,usize,_f=fnc): return _1base_func(_f,src,usize)
                elif e[3] == 2:
                    def wrapper(src,key,_f=fnc): return _2base_func(_f,src,key)
                elif e[3] == 2.1:
                    def wrapper(src,key,_f=fnc): return _21base_func(_f,src,key)
                elif e[3] == 3:
                    def wrapper(src,_f=fnc): return _3base_func(_f,src)
                elif e[3] == 4:
                    def wrapper(src,_f=fnc): return _4base_func(_f,src)
                elif e[3] == 5:
                    def wrapper(src,seed,_f=fnc): return _5base_func(_f,src,seed)
                setattr(self,e[0],wrapper)

    def decompress_lz10_raw(src:bytes,usize:int) -> bytes: ...
    def decompress_lz11_raw(src:bytes,usize:int) -> bytes: ...
    def decompress_lz4_fast(src:bytes,usize:int) -> bytes: ...
    def decompress_lzss0_lsb(src:bytes,usize:int) -> bytes: ...
    def decompress_lzss0_msb(src:bytes,usize:int) -> bytes: ...
    def decompress_rtl_lz(src:bytes,usize:int) -> bytes: ...
    def decompress_vicious_lz(src:bytes,usize:int) -> bytes: ...
    def decompress_graw_bpe(src:bytes,usize:int) -> bytes: ...
    def decompress_capcom_yz2(src:bytes,usize:int) -> bytes: ...
    
    def decompress_blz_raw(self,src:bytes,usize:int) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_blz_raw(i,len(src),o,usize)
        return bytes(o)[r:]
    def decompress_huffman(self,src:bytes,usize:int,padding:bool=False) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_huffman(i,len(src),o,usize,1 if padding else 0)
        if r == -1: raise RuntimeError('Decompression failed')
        return bytes(o)[:r]
    def decompress_ash0(self,src:bytes) -> bytes:
        if len(src) <= 12 or src[:4] != b'ASH0': raise ValueError('Invalid data')
        us = int.from_bytes(src[5:8],'big')
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * us)()
        r = self.dll.decompress_ash0(i,len(src),o)
        if r == -1: raise RuntimeError('Decompression failed')
        return bytes(o)[:r]

    def decrypt_inv(src:bytes) -> bytes: ...
    def decrypt_swp4(src:bytes) -> bytes: ...
    def decrypt_roll(src:bytes,key:bytes) -> bytes: ...
    def decrypt_rolr(src:bytes,key:bytes) -> bytes: ...
    def decrypt_xor(src:bytes,key:bytes) -> bytes: ...
    def decrypt_zipcrypto(src:bytes,key:bytes) -> bytes: ...

    def decrypt_rxor(self,src:bytes,key:bytes|int) -> bytes:
        if isinstance(key,bytes): key = key[0]
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * len(src))()
        self.dll.decrypt_rxor(i,len(src),o,key)
        return bytes(o)
    def decrypt_cxor(self,src:bytes,key:bytes,iv:int=0) -> bytes:
        if iv: key = bytes((x + iv) & 0xFF for x in key)
        i = (u8 * len(src)).from_buffer_copy(src)
        k = (u8 * len(key)).from_buffer_copy(key)
        o = (u8 * len(src))()
        self.dll.decrypt_cxor(i,len(src),o,k,len(key))
        return bytes(o)
    def decrypt_dxor(self,src:bytes,key1:bytes,key2:bytes) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        k1 = (u8 * len(key1)).from_buffer_copy(key1)
        k2 = (u8 * len(key2)).from_buffer_copy(key2)
        o = (u8 * len(src))()
        if len(key1) == len(key2):
            mk = (u8 * len(key1))()
            self.dll.decrypt_xor(k1,len(key1),mk,k2,len(key2))
            self.dll.decrypt_xor(i,len(src),o,mk,len(key1))
        else: self.dll.decrypt_dxor(i,len(src),o,k1,len(key1),k2,len(key2))
        return bytes(o)
    def decrypt_tea(self,src:bytes,key:bytes,le:bool=False) -> bytes:
        asrt(len(key) == 0x10 and not len(src) % 8)
        i = (u8 * len(src)).from_buffer_copy(src)
        k = (u8 * 0x10).from_buffer_copy(key)
        o = (u8 * len(src))()
        self.dll.decrypt_tea(i,len(src),o,k,1 if le else 0)
        return bytes(o)
    def decrypt_rsdk3(self,src:bytes,key1:bytes,key2:bytes) -> bytes:
        asrt(len(key1) == 20 and len(key2) == 12)
        d = (u8 * len(src)).from_buffer_copy(src)
        k1 = (u8 * 20).from_buffer_copy(key1)
        k2 = (u8 * 12).from_buffer_copy(key2)
        self.dll.decrypt_rsdk3(d,len(src),k1,k2)
        return bytes(d)
    def decrypt_rsdk4(self,src:bytes,key1:int,key2:int) -> bytes:
        d = (u8 * len(src)).from_buffer_copy(src)
        keyx1 = struct.unpack('<4I',md5(str(len(src)).encode()).digest())
        keyx2 = struct.unpack('<4I',md5(str((len(src) >> 1) + 1).encode()).digest())
        kx1 = (u8 * 0x10).from_buffer_copy(struct.pack('>4I',*keyx1))
        kx2 = (u8 * 0x10).from_buffer_copy(struct.pack('>4I',*keyx2))
        self.dll.decrypt_rsdk4(d,len(src),key1,key2,kx1,kx2)
        return bytes(d)
    def decrypt_rsdk5(self,src:bytes,key:bytes) -> bytes:
        asrt(len(key) == 0x10)
        key2 = struct.unpack('<4I',md5(str(len(src)).encode()).digest())
        d = (u8 * len(src)).from_buffer_copy(src)
        k1 = (u8 * 0x10).from_buffer_copy(key)
        k2 = (u8 * 0x10).from_buffer_copy(struct.pack('>4I',*key2))
        self.dll.decrypt_rsdk5(d,len(src),k1,k2)
        return bytes(d)
    def decrypt_hatch(self,src:bytes,key:bytes) -> bytes:
        asrt(len(key) == 0x10)
        key2 = crc32(len(src).to_bytes(8,'little')).to_bytes(4,'little')*4
        d = (u8 * len(src)).from_buffer_copy(src)
        k1 = (u8 * 0x10).from_buffer_copy(key)
        k2 = (u8 * 0x10).from_buffer_copy(key2)
        self.dll.decrypt_rsdk5(d,len(src),k1,k2)
        return bytes(d)
    def decrypt_hornby(self,src:bytes,key:bytes|int,msk:int=0xFF) -> bytes:
        if isinstance(key,bytes): key = key[0]
        d = (u8 * len(src)).from_buffer_copy(src)
        self.dll.decrypt_hornby(d,len(src),key,msk)
        return bytes(d)[1:]
    def init_mmfs(self,key:bytes):
        if key not in self.MMFS:
            key = key.replace(b'\0',b'')
            k = bytearray(key)[:0x80] + b'\0'*0x80
            if len(key) < 0xFF: k[len(key) + 1] = (sum(key) * 2) & 0xFF
            ik = (u8 * len(k)).from_buffer_copy(k)
            mk = (u8 * 0x100).from_buffer_copy(bytes(range(0x100)))
            self.dll.init_mmfs(mk,ik)
            self.MMFS[key] = mk
        return self.MMFS[key]
    def decrypt_mmfs(self,src:bytes,key:bytes) -> bytes:
        mk = self.init_mmfs(key)
        d = (u8 * len(src)).from_buffer_copy(src)
        self.dll.decrypt_mmfs(d,len(src),mk)
        return bytes(d)
    def init_selene(self,key:bytes):
        seed = crc32(key)
        if seed not in self.SELENE:
            k = (u8 * len(key)).from_buffer_copy(key)
            mk = (u8 * 0x10000)()
            self.dll.init_selene(mk,k,len(key),seed)
            self.SELENE[seed] = mk
        return self.SELENE[seed]
    def decrypt_selene(self,src:bytes,key:bytes) -> bytes:
        mk = self.init_selene(key)
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * len(src))()
        self.dll.decrypt_xor(i,len(src),o,mk,len(mk))
        return bytes(o)
    def decrypt_rc4_playpond(self,src:bytes,key:bytes,drop:int=0) -> bytes:
        b = (u8 * len(src)).from_buffer_copy(src)
        k = (u8 * len(key)).from_buffer_copy(key)
        self.dll.decrypt_rc4_playpond(b,len(src),k,len(key),drop)
        return bytes(b)
    def decrypt_remedy_ras(self,src:bytes,key:int) -> bytes:
        b = (u8 * len(src)).from_buffer_copy(src)
        self.dll.decrypt_remedy_ras(b,len(src),key)
        return bytes(b)
    def decrypt_empire_magic(self,src:bytes,key:bytes,key_end:bool=False) -> bytes:
        if self.EMPIRE_MAGIC is None:
            tb = (u8 * 0x400)()
            self.dll.init_empire_magic(tb)
            self.EMPIRE_MAGIC = tb
        b = (u8 * len(src)).from_buffer_copy(src)
        k = (u8 * len(key)).from_buffer_copy(key)
        self.dll.decrypt_empire_magic(b,len(src),k,len(key),self.EMPIRE_MAGIC,self.hash_empire_magic(key,key_end))
        return bytes(b)
        
    def decrypt_tfit(self,src:bytes,key:bytes,table:bytes,iv:bytes,block_size:int) -> bytes:
        asrt(len(key) == 4*4*17 and len(table) == 4*0x100*0x10*17 and len(iv) == 0x10 and len(src) % (block_size + 0x10) == 0)
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * (len(src) // (block_size + 0x10) * block_size))()
        k = (u8 * len(key)).from_buffer_copy(key)
        t = (u8 * len(table)).from_buffer_copy(table)
        iv = (u8 * 0x10).from_buffer_copy(iv)
        self.dll.decrypt_tfit(i,len(src),o,iv,k,t,block_size)
        return bytes(o)

    def hash_pivotal(self,src:bytes) -> int: ...
    def hash_super_fast_le(self,src:bytes) -> int: ...
    def hash_super_fast_be(self,src:bytes) -> int: ...
    def hash_elf(self,src:bytes) -> int: ...
    def hash_ap(self,src:bytes) -> int: ...
    def hash_murmur2_le(self,src:bytes,seed:int) -> int: ...
    def hash_murmur2_be(self,src:bytes,seed:int) -> int: ...
    def hash_murmur2A_le(self,src:bytes,seed:int) -> int: ...
    def hash_murmur2A_be(self,src:bytes,seed:int) -> int: ...
    def hash_murmur2_64A_le(self,src:bytes,seed:int) -> int: ...
    def hash_murmur2_64A_be(self,src:bytes,seed:int) -> int: ...
    def hash_murmur2_64B_le(self,src:bytes,seed:int) -> int: ...
    def hash_murmur2_64B_be(self,src:bytes,seed:int) -> int: ...
    def hash_empire_magic(self,src:bytes,end:bool=False) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_empire_magic(b,len(src),1 if end else 0)
    def mac_cmac_tfit(self,src:bytes,key:bytes,table:bytes) -> bytes:
        asrt(len(key) == 4*4*13 and len(table) == 4*0x100*0x10*13)
        s = (u8 * len(src)).from_buffer_copy(src)
        d = (u8 * 0x10)()
        k = (u8 * len(key)).from_buffer_copy(key)
        t = (u8 * len(table)).from_buffer_copy(table)
        self.dll.mac_cmac_tfit(s,len(src),d,k,t)
        return bytes(d)

'''*/

#include <stdint.h>
#include <stdlib.h>

#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif
#if defined(_MSC_VER) && defined(_WIN64)
    typedef long long ssize_t;
#elif defined(_MSC_VER) && defined(_WIN32)
    typedef long ssize_t;
#elif defined(INTPTR_MAX)
    typedef intptr_t ssize_t;
#else
    typedef long ssize_t;
#endif
EXPORT int __stdcall DllMain(void* a,unsigned long b,void* c) { return 1; }

#ifdef __cplusplus
extern "C" {
#endif

#define CONCAT(a,b) a##b
#define CONCATX(a,b) CONCAT(a,b)

#if defined(__GNUC__) || defined(__clang__)
    #define SWAP32(x) __builtin_bswap32(x)
#elif defined(_MSC_VER)
    unsigned long __cdecl _byteswap_ulong(unsigned long);
    #pragma intrinsic(_byteswap_ulong)
    #define SWAP32(x) _byteswap_ulong(x)
#else
    static inline uint32_t SWAP32(uint32_t x) {
        return ((x & 0xFF) << 24 | (x & 0xFF00) << 8 | (x & 0xFF0000) >> 8 | (x & 0xFF000000) >> 24);
    }
#endif
static inline uint8_t SWAP8(uint8_t x) {
    return ((uint8_t)x << 4) | (x >> 4);
}
static inline uint32_t HIMUL64(uint32_t a, uint32_t b) {
    return ((uint64_t)a) * ((uint64_t)b) >> 32;
}
static inline void DBLGF(uint8_t *src, uint8_t *dst) {
    uint8_t a = 0;
    if (src[0] & 0x80) a = 0x87;
    dst[15] = a ^ (src[15] << 1);
    for (int i=14;i >= 0;i--)
        dst[i] = (src[i + 1] >> 7) | (src[i] << 1);
}

static inline uint16_t read16le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8);
}
static inline uint16_t read16be(const uint8_t *restrict ptr) {
    return ptr[1] | (ptr[0] << 8);
}
static inline uint32_t read24le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8) | (ptr[2] << 16);
}
static inline uint32_t read24be(const uint8_t *restrict ptr) {
    return ptr[2] | (ptr[1] << 8) | (ptr[0] << 16);
}
static inline uint32_t read32le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8) | (ptr[2] << 16) | ((uint32_t)ptr[3] << 24);
}
static inline uint32_t read32be(const uint8_t *restrict ptr) {
    return ptr[3] | (ptr[2] << 8) | (ptr[1] << 16) | ((uint32_t)ptr[0] << 24);
}
static inline uint64_t read64le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8) | (ptr[2] << 16) | ((uint64_t)ptr[3] << 24) | ((uint64_t)ptr[4] << 32) | ((uint64_t)ptr[5] << 40) | ((uint64_t)ptr[6] << 48) | ((uint64_t)ptr[7] << 56);
}
static inline uint64_t read64be(const uint8_t *restrict ptr) {
    return ptr[7] | (ptr[6] << 8) | (ptr[5] << 16) | ((uint64_t)ptr[4] << 24) | ((uint64_t)ptr[3] << 32) | ((uint64_t)ptr[2] << 40) | ((uint64_t)ptr[1] << 48) | ((uint64_t)ptr[0] << 56);
}

typedef struct {
    const uint8_t* ptr;
    const uint8_t* end;
    uint8_t buf;
    uint8_t bits;
} BitReader;
static inline void init_BitReader(BitReader *br, const uint8_t *ptr, const size_t size) {
    br->ptr = ptr;
    br->end = ptr + size;
    br->buf = 0;
    br->bits = 0;
}
static inline uint8_t get_bit(BitReader *br) {
    if (!br->bits) {
        if (br->ptr >= br->end) return 0;
        br->buf = *(br->ptr++);
        br->bits = 8;
    }
    br->bits--;
    return (br->buf >> br->bits) & 1;
}
static inline uint32_t get_bits(BitReader *br, size_t n) {
    uint32_t v = 0;
    while (n > 0) {
        if (!br->bits) {
            if (br->ptr >= br->end) return v << n;
            br->buf = *(br->ptr++);
            br->bits = 8;
        }

        int s = (n < br->bits) ? n : br->bits;
        v = (v << s) | ((br->buf >> (br->bits - s)) & ((1 << s) - 1));
        br->bits -= s;
        n -= s;
    }
    return v;
}
static inline uint32_t get_bits_l(BitReader *br, size_t n) {
    uint32_t v = 0;
    size_t p = 0;
    while (n > 0) {
        if (!br->bits) {
            if (br->ptr >= br->end) return v;
            br->buf = *(br->ptr++);
            br->bits = 8;
        }

        int s = (n < br->bits) ? n : br->bits;
        v |= (br->buf & ((1 << s) - 1)) << p;
        br->bits -= s;
        br->buf >>= s;
        n -= s;
        p += s;
    }
    return v;
}

typedef struct {
    int16_t l;
    int16_t r; // -1 = leaf
} HuffNode;
static inline int read_hufftree(BitReader *br, int width, int max, HuffNode *tree) {
    int root = 0;
    int nodec = 1;
    int16_t stack[0x800];
    int stacki = 0;

    while (1) {
        if (get_bit(br)) {
            if (nodec + 1 >= max * 2) return 0;
            tree[root].l = nodec;
            tree[root].r = nodec + 1;
            stack[stacki++] = nodec + 1;
            root = nodec;
            nodec += 2;
        } else {
            tree[root].l = get_bits(br, width);
            tree[root].r = -1;
            if (!stacki) break;
            root = stack[--stacki];
        }
    }
    return 1;
}
static inline int get_huffcode(BitReader *br, HuffNode *tree) {
    int node = 0;
    while (tree[node].r != -1) {
        node = (get_bit(br)) ? tree[node].r : tree[node].l;
    }
    return tree[node].l;
}

#define MT_N 624
#define MT_M 397
#define MT_MSK_U (int32_t)0x80000000
#define MT_MSK_L (int32_t)0x7FFFFFFF
typedef struct {
    int32_t MATRIX_A;
    uint32_t TEMPERING_MASK_B;
    uint32_t TEMPERING_MASK_C;
    uint32_t INIT_MULT;

    int32_t mt[624];
    int32_t mti;
} MT19937;
#define INIT_MT19937(X) MT19937 X = { .MATRIX_A = (int32_t)0x9908B0DF, .TEMPERING_MASK_B = 0x9D2C5680,\
                                      .TEMPERING_MASK_C = 0xEFC60000, .INIT_MULT = 0x6C078965,\
                                      .mt = { 0 }, .mti = MT_N + 1 }
void MT19937_seed(MT19937 *restrict ctx, int32_t seed) {
    ctx->mt[0] = seed;
    for (ctx->mti=1;ctx->mti < MT_N;ctx->mti++) {
        int32_t last = ctx->mt[ctx->mti - 1];
        ctx->mt[ctx->mti] = (int32_t)(ctx->INIT_MULT * (uint32_t)(last ^ (last >> 30)) + (uint32_t)ctx->mti);
    }
}
int32_t MT19937_rand(MT19937 *restrict ctx) {
    int32_t y;
    const int32_t mag01[2] = { 0x0U, ctx->MATRIX_A };

    if (ctx->mti >= MT_N) {
        int i = 0;

        for (;i < MT_N - MT_M;i++) {
            y = (ctx->mt[i] & MT_MSK_U) | (ctx->mt[i + 1] & MT_MSK_L);
            ctx->mt[i] = ctx->mt[i + MT_M] ^ (y >> 1) ^ mag01[y & 1];
        }
        for (;i < MT_N - 1;i++) {
            y = (ctx->mt[i] & MT_MSK_U) | (ctx->mt[i + 1] & MT_MSK_L);
            ctx->mt[i] = ctx->mt[i + (MT_M - MT_N)] ^ (y >> 1) ^ mag01[y & 1];
        }
        y = (ctx->mt[MT_N - 1] & MT_MSK_U) | (ctx->mt[0] & MT_MSK_L);
        ctx->mt[MT_N - 1] = ctx->mt[MT_M - 1] ^ (y >> 1) ^ mag01[y & 1];
        ctx->mti = 0;
    }

    y = ctx->mt[ctx->mti++];
    y ^= y >> 11;
    y ^= (int32_t)(((uint32_t)y << 7) & ctx->TEMPERING_MASK_B);
    y ^= (int32_t)(((uint32_t)y << 15) & ctx->TEMPERING_MASK_C);
    y ^= y >> 18;
    return y;
}

EXPORT ssize_t decompress_lz10_raw(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        if (fbl <= 0) {
            f = src[ip++];
            CHKi(0);
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];
            uint16_t dist = (((b1 & 0x0F) << 8) | b2) + 1;
            uint8_t lng = (b1 >> 4) + 3;
            if (dist < lng && dist != 0) lng = dist;
            if (op + lng > usize) lng = usize - op;
            for (int i=0;i < lng;i++,op++) {
                CHKi(0);CHKo(0);
                dst[op] = dst[(op - dist) & 0xFFF];
            }
        } else {
            CHKo(0);
            dst[op++] = src[ip++];
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lz11_raw(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        if (fbl <= 0) {
            f = src[ip++];
            CHKi(0);
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];
            size_t dist,lng;

            if ((b1 >> 4) == 0) {
                CHKi(0);
                uint8_t b3 = src[ip++];
                dist = ((b2 & 0x0F) << 8) | b3;
                lng = (((b1 & 0x0F) << 4) | (b2 >> 4)) + 0x10;
            } else if ((b1 >> 4) == 1) {
                CHKi(1);
                uint8_t b3 = src[ip++];
                uint8_t b4 = src[ip++];
                dist = ((b3 & 0x0F) << 8) | b4;
                lng = (((b1 & 0x0F) << 12) | (b2 << 4) | (b3 >> 4)) + 0x110;
            } else {
                dist = ((b1 & 0x0F) << 8) | b2;
                lng = b1 >> 4;
            }
            dist += 1;
            lng += 1;
            if (dist > op) break;
            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = dst[op - dist];
            }
        } else {
            CHKo(0);
            dst[op++] = src[ip++];
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lz40_raw(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        if (fbl <= 0) {
            f = src[ip++];
            CHKi(0);
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];
            size_t dist,lng;

            if ((b1 >> 4) == 0) {
                CHKi(0);
                uint8_t b3 = src[ip++];
                dist = ((b2 & 0x0F) << 8) | b3;
                lng = (((b1 & 0x0F) << 4) | (b2 >> 4)) + 0x10;
            } else if ((b1 >> 4) == 1) {
                CHKi(1);
                uint8_t b3 = src[ip++];
                uint8_t b4 = src[ip++];
                dist = ((b3 & 0x0F) << 8) | b4;
                lng = (((b1 & 0x0F) << 12) | (b2 << 4) | (b3 >> 4)) + 0x110;
            } else {
                dist = ((b1 & 0x0F) << 8) | b2;
                lng = b1 >> 4;
            }
            if (dist > op) break;
            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = dst[op - dist];
            }
        } else {
            CHKo(0);
            dst[op++] = src[ip++];
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_blz_raw(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const ssize_t usize) {
    ssize_t ip = zsize;
    ssize_t op = usize;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip - (n) <= 0) goto eof;
    #define CHKo(n) if (op - (n) <= 0) goto eof;

    while (ip > 0 && op > 0) {
        CHKi(0);
        if (fbl <= 0) {
            f = src[--ip];
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1);
            uint8_t b1 = src[--ip];
            uint8_t b2 = src[--ip];
            uint16_t dist = (((b2 & 0x0F) << 8) | b1) + 3;
            uint8_t lng = (b2 >> 4) + 3;
            for (int i=0;i < lng;i++,op--) {
                CHKi(0);CHKo(0);
                dst[op - 1] = dst[op - 1 + dist];
            }
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lz4_fast(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        uint8_t tok = src[ip++];
        size_t lits = tok >> 4;

        if (tok == 0x0F) {
            while (ip < zsize) {
                uint8_t b = src[ip++];
                lits += b;
                if (b != 0xFF) break;
            }
        }

        for (int i=0;i < lits;i++) {
            CHKi(0);CHKo(0);
            dst[op++] = src[ip++];
        }

        CHKi(1);
        uint16_t off = src[ip] | (src[ip + 1] << 8);ip += 2;
        size_t len = (tok & 0x0F) + 4;
        if (len == 0x13) {
            while (ip < zsize) {
                uint8_t b = src[ip++];
                len += b;
                if (b != 0xFF) break;
            }
        }

        for (int i=0;i < len;i++,op++) {
            CHKo(0);
            dst[op] = dst[op - off];
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lzss0_lsb(const uint8_t *restrict src, const size_t zsize,
                                          uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int8_t fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        if (fbl <= 0) {
            CHKi(0);
            f = src[ip++];
            fbl = 8;
        }

        if (f & 1) {
            CHKi(0);CHKo(0);
            dst[op++] = src[ip++];
        } else {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];

            uint16_t dist = (op - 18 - (((b2 & 0xF0) << 4) | b1)) & 0xFFF;
            if (!dist) dist = 0x1000;
            uint8_t lng = (b2 & 0x0F) + 3;

            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = (op < dist) ? 0 : dst[op - dist];
            }
        }

        f >>= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lzss0_msb(const uint8_t *restrict src, const size_t zsize,
                                          uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int8_t fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        if (fbl <= 0) {
            CHKi(0);
            f = src[ip++];
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(0);CHKo(0);
            dst[op++] = src[ip++];
        } else {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];

            uint8_t lng = (b1 & 0x0F) + 3;
            uint16_t dist = (op - 18 - (((b1 & 0xF0) << 4) | b2)) & 0xFFF;
            if (!dist) dist = 0x1000;

            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = (op < dist) ? 0 : dst[op - dist];
            }
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_rtl_lz(const uint8_t *restrict src, const size_t zsize,
                                       uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        uint16_t b = src[ip++];

        if (0x20 > b) {
            if (b == 0) {
                CHKi(0);
                b = src[ip++];
                if (b == 0) {
                    CHKi(1);
                    uint16_t s = read16le(src+ip);ip += 2;
                    if (s == 0) break;
                    for (int i=0;i < s;i++) {
                        CHKi(0);CHKo(0);
                        dst[op++] = src[ip++];
                    }
                } else {
                    b += 0x1F;
                    for (int i=0;i < b;i++) {
                        CHKi(0);CHKo(0);
                        dst[op++] = src[ip++];
                    }
                }
            } else {
                for (int i=0;i < b;i++) {
                    CHKi(0);CHKo(0);
                    dst[op++] = src[ip++];
                }
            }
        } else if (0x40 > b) {
            uint16_t c = b - 0x20;
            if (c == 0) {
                CHKi(0);
                c = src[ip++] + 0x20;
            }
            for (int i=0;i < c;i++) {
                CHKo(0);
                dst[op++] = 0;
            }
        } else if (0x80 > b) {
            if ((b & 0x0F) == 0) {
                CHKi(3);
                uint16_t l = read16le(src+ip);ip += 2;
                uint16_t o = read16le(src+ip);ip += 2;
                if (o != 0) o -= 1;
                if (o > op) o = 0;
                if (o + l > op) {
                    if (l > op) {
                        o = 0;
                        l = op;
                    } else o = op - l;
                }
                while (b & 0x30) {
                    CHKi(0);CHKo(0);
                    dst[op++] = src[ip++];
                    b -= 0x10;
                }
                for (int i=0;i < l;i++,op++) {
                    CHKo(0);
                    dst[op] = dst[op - o - l];
                }
            } else {
                CHKi(1);
                uint8_t l = (b & 0x0F) + 2;
                uint16_t o = read16le(src+ip);ip += 2;
                if (o != 0) o -= 1;
                if (o > op) o = 0;
                if (o + l > op) {
                    if (l > op) {
                        o = 0;
                        l = op;
                    } else o = op - l;
                }
                while (b & 0x30) {
                    CHKi(0);CHKo(0);
                    dst[op++] = src[ip++];
                    b -= 0x10;
                }
                for (int i=0;i < l;i++,op++) {
                    CHKo(0);
                    dst[op] = dst[op - o - l];
                }
            }
        } else {
            if (b & 0x40) {
                CHKi(1);CHKo(1);
                dst[op++] = src[ip++];
                dst[op++] = src[ip++];
            }
            CHKo(1);
            uint8_t o = (b & 0x3F)*2 + 2;
            if (o > op) o = op;
            dst[op] = dst[op - o];op++;
            dst[op] = dst[op - o];op++;
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_vicious_lz(const uint8_t *restrict src, const size_t zsize,
                                           uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        uint8_t b = src[ip++];

        if (b & 0x80) {
            CHKi(0);
            uint8_t b2 = src[ip++];
            uint8_t lng = (b2 & 0x0F) + 2;
            uint16_t dist = (((b << 4) | (b2 >> 4)) ^ 0xFFF) + 2;
            for (uint8_t i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = (op < dist) ? 0 : dst[op - dist];
            }
        } else if (b & 0x40) {
            CHKi(0);
            uint8_t c = (b & 0x3F) + 2;
            uint8_t cb = src[ip++];
            for (uint8_t i=0;i < c;i++) {
                CHKo(0);
                dst[op++] = cb;
            }
        } else {
            uint8_t c = (b & 0x3F) + 1;
            for (uint8_t i=0;i < c;i++) {
                CHKi(0);CHKo(0);
                dst[op++] = src[ip++];
            }
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_huffman(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const ssize_t usize, const int8_t padding) {
    BitReader br;
    init_BitReader(&br, src, zsize);
    HuffNode tree[512];
    if (!read_hufftree(&br, 8, 256, tree)) return -1;

    if (padding) br.bits = 0;

    ssize_t op = 0;
    while (usize == -1 || op < usize) {
        if (br.bits == 0 && br.ptr >= br.end) break;
        dst[op++] = (uint8_t)get_huffcode(&br, tree);
    }

    return op;
}
EXPORT ssize_t decompress_ash0(const uint8_t *restrict src, const size_t zsize,
                                     uint8_t *restrict dst) {
    if (12 >= zsize) return -1;

    uint32_t usize = read24be(src+5);
    uint32_t symo = read32be(src+8);
    if (symo >= zsize) return -1;

    BitReader symr,distr;
    init_BitReader(&symr, src + 12, symo - 12);
    init_BitReader(&distr, src + symo, zsize - symo);

    HuffNode sym_tree[0x400];
    HuffNode dist_tree[0x1000];
    if (!read_hufftree(&symr ,9 ,0x200,sym_tree) ||
        !read_hufftree(&distr,11,0x500,dist_tree)) return -1;

    ssize_t op = 0;
    while (op < usize) {
        int sym = get_huffcode(&symr, sym_tree);
        if (sym < 0x100) dst[op++] = (uint8_t)sym;
        else {
            size_t lng = sym - 0x100 + 3;
            size_t dist = get_huffcode(&distr, dist_tree) + 1;
            if (dist > op) return -1;
            size_t cp = op - dist;
            if (op + lng > usize) lng = usize - op;
            for (size_t i=0;i < lng;i++) dst[op++] = dst[cp++];
        }
    }

    return op;
}
EXPORT ssize_t decompress_graw_bpe(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    if (usize == 0) return 0;
    size_t ip = 0;
    ssize_t op = 0;

    while (ip < zsize && (op < usize || usize == -1)) {
        uint8_t ls[0x100];
        uint8_t rs[0x100];
        for (uint16_t i=0;i < 0x100;i++) {
            ls[i] = i;
            rs[i] = 0;
        }

        uint16_t pc = 0;
        while (pc < 0x100) {
            if (ip >= zsize) return -1;
            uint8_t c = src[ip++];
            if (c > 0x7F) {
                pc += c - 0x7F;
                c = 0;
            }

            for (uint16_t i=0;i <= c && pc < 0x100;i++,pc++) {
                if (ip >= zsize) return -1;

                uint8_t l = src[ip++];
                ls[pc] = l;
                if (l != pc) {
                    if (ip >= zsize) return -1;
                    rs[pc] = src[ip++];
                }
            }
        }

        if (ip + 2 > zsize) return -1;
        uint16_t s = read16be(src+ip);ip += 2;
        if (ip + s > zsize) return -1;

        size_t ep = ip + s;
        while (ip < ep && (op < usize || usize == -1)) {
            uint8_t stack[0x2000];
            uint16_t sp = 0;
            stack[sp++] = src[ip++];

            while (sp > 0 && (op < usize || usize == -1)) {
                uint8_t v = stack[--sp];

                if (ls[v] == v) dst[op++] = v;
                else {
                    if (sp + 2 > sizeof(stack)) return -1;

                    stack[sp++] = rs[v];
                    stack[sp++] = ls[v];
                }
            }
        }
    }

    return op;
}
EXPORT ssize_t decompress_lzrw1kh(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const ssize_t usize) {
    if (zsize == 0) return 0;
    if (src[0] == 0x80) {
        size_t size = zsize - 1;
        if (usize != -1 && usize < size) size = usize;
        memcpy(dst, src + 1, size);
        return size;
    }

    size_t ip = 3;
    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    ssize_t op = 0;
    uint16_t cmd = read16le(src + 1);
    uint8_t bits = 0x10;
    while (ip < zsize && (op < usize || usize == -1)) {
        if (!bits) {
            CHKi(1)
            cmd = read16le(src + ip);ip += 2;
            bits = 0x10;
        }
        if (cmd & 0x8000) {
            CHKi(1)
            uint16_t dist = (src[ip++] << 4) | (src[ip] >> 4);
            if (dist) {
                uint8_t len = (src[ip++] & 0xF) + 3;
                if (op + len > usize) len = usize - op;
                for (uint8_t i=0;i < len;i++,op++) dst[op] = dst[op - dist];
            } else {
                CHKi(2)
                uint16_t len = read16le(src + ip) + 0x10;ip += 2;
                if (op + len > usize) len = usize - op;
                for (uint16_t i=0;i < len;i++) dst[op++] = src[ip];
                ip++;
            }
        } else {
            CHKi(0)
            dst[op++] = src[ip++];
        }
        cmd <<= 1;
        bits--;
    }

eof:
    #undef CHKi
    return op;
}

typedef struct {
    const uint8_t *src;
    size_t s;
    size_t p;
    uint8_t eofc;
    size_t full;
    size_t shift;
    uint32_t w;
    uint32_t v;
} YZRange;
static inline void init_YZRange(YZRange *restrict r, const uint8_t *restrict src, const size_t size, const size_t full, const size_t shift) {
    r->src = src;
    r->s = size;
    r->p = 1;
    r->eofc = 0;
    r->full = full;
    r->shift = shift;
    r->w = 0x80;
    r->v = src[0];
}
static inline uint16_t get_YZRange(YZRange *restrict r) {
    while (r->w <= (r->full >> 8)) {
        r->v <<= 8;
        if (r->p < r->s) r->v |= r->src[r->p++];
        else if (++r->eofc > 4) return -1;
        r->w <<= 8;
    }
    r->w >>= r->shift - 1;
    return (uint16_t)(r->v / r->w);
}
static inline void update_YZRange(YZRange *restrict r, const uint16_t w, const uint16_t v) {
    r->v -= r->w * v;
    r->w *= w;
    r->w >>= 1;
}
typedef struct {
    size_t size;
    size_t shift;
    uint16_t *ccnt;
    uint16_t *orngw;
    uint16_t *orngv;
    uint32_t sum;
    size_t bit;
    uint32_t cp;
    uint8_t flg;
    uint16_t *decs;
} YZFreqs;
static int8_t init_YZFreqs(YZFreqs *restrict f, const size_t size, const size_t shift) {
    f->size = size;
    f->shift = shift;

    f->ccnt = (uint16_t *)calloc(size, sizeof(uint16_t));
    if (!f->ccnt) return -1;
    f->orngw = (uint16_t *)malloc(size * sizeof(uint16_t));
    if (!f->orngw) return -1;
    f->orngv = (uint16_t *)malloc(size * sizeof(uint16_t));
    if (!f->orngv) return -1;
    f->decs = (uint16_t *)calloc(1 << shift, sizeof(uint16_t));
    if (!f->decs) return -1;

    size_t ix = 0;
    for (size_t i=0;i < (1 << shift);i++) {
        f->ccnt[ix]++;
        if (++ix >= size) ix = 0;
    }

    uint16_t sum = 0;
    for (size_t i=0;i < size;i++) {
        f->orngw[i] = f->ccnt[i];
        f->orngv[i] = sum;
        sum += f->ccnt[i];
    }

    for (size_t i=0;i < size;i++) f->ccnt[i] = 1;
    f->sum = size;
    f->bit = 0;
    for (;f->bit < shift && f->sum >= (1 << f->bit);f->bit++) {};
    f->cp = 1 << f->bit;
    f->flg = 0;

    return 0;
}
static void update_YZFreqs(YZFreqs *restrict f, const uint16_t c) {
    f->ccnt[c]++;
    f->sum++;

    if (f->shift > f->bit) {
        if (f->sum == f->cp) {
            uint16_t sum = 0;
            uint16_t x = 1 << (f->shift - f->bit);
            for (size_t i=0;i < f->size;i++) {
                f->orngw[i] = f->ccnt[i] * x;
                f->orngv[i] = sum;
                sum += f->orngw[i];
            }
            f->bit++;
            f->cp = 1 << f->bit;
            f->flg = 0;
        }
    } else {
        if (f->sum >= (1 << f->shift)) {
            uint16_t sum = 0;
            f->sum = 0;
            for (size_t i=0;i < f->size;i++) {
                f->orngw[i] = f->ccnt[i];
                f->orngv[i] = sum;
                sum += f->orngw[i];

                uint16_t c = f->ccnt[i] >> 1;
                f->ccnt[i] = (c == 0) ? 1 : c;
                f->sum += f->ccnt[i];
            }
            f->flg = 0;
        }
    }
}
static inline uint16_t get_YZFreqs(YZFreqs *restrict f, YZRange *restrict r) {
    uint16_t pos = get_YZRange(r);
    if (r->eofc > 4) return -1;

    if (!f->flg) {
        size_t j=0;
        for (size_t i=0;i < f->size;i++)
            for (;j < (f->orngv[i] + f->orngw[i]);j++)
                f->decs[j] = (uint16_t)i;
        f->flg = 1;
    }

    uint16_t c = f->decs[pos];
    update_YZRange(r, f->orngw[c], f->orngv[c]);
    update_YZFreqs(f, c);
    return c;
}
typedef struct {
    uint16_t c;
    size_t *off;
    uint32_t *len;
} YZDictE;
typedef struct {
    YZRange rng;
    YZFreqs fqc;
    YZFreqs fql;
    YZDictE *dict;
} YZ2;
static inline void free_YZ2(YZ2 *restrict y2, const uint16_t dicts) {
    if (y2->dict) {
        for (uint16_t i=0;i < dicts;i++) {
            if (y2->dict[i].off) free(y2->dict[i].off);
            if (y2->dict[i].len) free(y2->dict[i].len);
        }
        free(y2->dict);
    }
    if (y2->fqc.ccnt) free(y2->fqc.ccnt);
    if (y2->fqc.orngw) free(y2->fqc.orngw);
    if (y2->fqc.orngv) free(y2->fqc.orngv);
    if (y2->fqc.decs) free(y2->fqc.decs);
    if (y2->fql.ccnt) free(y2->fql.ccnt);
    if (y2->fql.orngw) free(y2->fql.orngw);
    if (y2->fql.orngv) free(y2->fql.orngv);
    if (y2->fql.decs) free(y2->fql.decs);
}
EXPORT ssize_t decompress_capcom_yz2(const uint8_t *restrict src, const size_t zsize,
                                           uint8_t *restrict dst, const ssize_t usize) {
    ssize_t op = -1;
    YZ2 y2;
    init_YZRange(&y2.rng, src, zsize, 0x80000000, 15);
    y2.dict = (YZDictE *)calloc(0x100,sizeof(YZDictE));
    if (!y2.dict) goto eof;
    for (uint16_t i=0;i < 0x100;i++) {
        y2.dict[i].off = (size_t *)calloc(0x200,sizeof(size_t));
        if (!y2.dict[i].off) goto eof;
        y2.dict[i].len = (uint32_t *)calloc(0x200,sizeof(uint32_t));
        if (!y2.dict[i].len) goto eof;
    }

    if ((op = init_YZFreqs(&y2.fqc, 0x500, 15)) < 0) goto eof;
    if ((op = init_YZFreqs(&y2.fql, 0x100, 15)) < 0) goto eof;

    size_t kp = 0;
    op = 0;
    while (op < usize || usize == -1) {
        uint16_t c = get_YZFreqs(&y2.fqc, &y2.rng);
        if (y2.rng.eofc > 4) break;
        size_t s = 1;

        if (c >= 0x400) dst[op++] = (uint8_t)(c - 0x400);
        else {
            if (op == 0) {
                op = -1;
                break;
            }
            uint32_t moto;
            if (c < 0x200) {
                uint16_t rtn = get_YZFreqs(&y2.fql, &y2.rng);
                if (y2.rng.eofc > 4) break;
                s = 0;
                switch (rtn) {
                    case 0: s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng) << 24;
                    case 1: s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng) << 16;
                    case 2: s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng) << 8;s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng);break;
                    default: s = rtn;
                }
                if (y2.rng.eofc > 4) break;
                s = s - 3 + 2;

                uint8_t key = dst[kp];
                moto = y2.dict[key].off[(c + y2.dict[key].c) % 0x200];
            } else {
                uint8_t key = dst[kp];
                uint16_t cnt = y2.dict[key].c;
                s = y2.dict[key].len[(c + cnt) % 0x200];
                moto = y2.dict[key].off[((uint16_t)(c - 0x200) + cnt) % 0x200];
            }

            if (moto > op) moto = op;
            if (op + s > usize) s = usize - op;
            for (size_t i=0;i < s;i++) dst[op++] = dst[moto++];
        }

        if (kp < op - 1) {
            uint8_t key = dst[kp];
            uint16_t cnt = y2.dict[key].c;
            y2.dict[key].off[cnt] = kp + 1;
            y2.dict[key].len[cnt] = (uint32_t)s;
            y2.dict[key].c = (cnt + 1) % 0x200;
            kp = op - 1;
        }
    }

eof:
    free_YZ2(&y2, 0x100);
    return op;
}

typedef struct {
    int16_t ls[0x4EA];
    int16_t rs[0x4EA];
    int16_t par[0x4EA];
    uint16_t wg[0x4EA];
    int dist_bits[6];
    int dist_base[6];
} d0llz3_AHuff;
static void d0llz3_AHuff_update(d0llz3_AHuff *ah, int16_t n1, int16_t n2) {
    while (1) {
        int16_t p = ah->par[n1];
        ah->wg[p] = ah->wg[n1] + ah->wg[n2];
        if (p == 1) break;
        n1 = p;
        n2 = ah->ls[ah->par[n1]];
        if (n2 == n1) n2 = ah->rs[ah->par[n1]];
    }

    if (ah->wg[1] == 2000) {
        for (int16_t i=1;i < 0x4EA;i++)
            ah->wg[i] >>= 1;
    }
}
static int16_t d0llz_AHuff_get(BitReader *restrict br, d0llz3_AHuff *restrict ah) {
    int16_t n = 1;
    while (n < 0x275) {
        if (get_bit(br)) n = ah->rs[n];
        else n = ah->ls[n];
    }
    int16_t sym = n - 0x275;

    int16_t p = ah->par[n];
    ah->wg[n]++;
    if (p != 1) {
        int16_t sib = ah->ls[p];
        if (sib == n) sib = ah->rs[p];
        d0llz3_AHuff_update(ah,n,sib);

        do {
            p = ah->par[n];
            int16_t pp = ah->par[p];
            int16_t c = ah->ls[pp];
            if (c == p) c = ah->rs[pp];

            if (ah->wg[c] < ah->wg[n]) {
                if (ah->ls[pp] == p) ah->ls[pp] = n;
                else ah->rs[pp] = n;
                if (ah->ls[p] == n) ah->ls[p] = c;
                else ah->rs[p] = c;

                ah->par[c] = p;
                ah->par[n] = pp;
                int16_t osib = ah->ls[p];
                if (osib == c) osib = ah->rs[p];
                d0llz3_AHuff_update(ah,c,osib);
                n = c;
            }
            n = ah->par[n];
            p = ah->par[n];
        } while (p != 1);
    }

    return sym;
}
EXPORT ssize_t decompress_d0llz3(const uint8_t *restrict src, const size_t zsize,
                                       uint8_t *restrict dst, const ssize_t usize) {
    BitReader br;
    init_BitReader(&br, src, zsize);

    d0llz3_AHuff ah;
    for (int8_t i=0,bs=4;i < 6;i++,bs+=2)
        ah.dist_bits[i] = bs;
    for (int16_t i=2;i < 0x4EA;i++) {
        ah.par[i] = i / 2;
        ah.wg[i] = 1;
    }
    for (int16_t i=1;i < 0x275;i++) {
        ah.ls[i] = i * 2;
        ah.rs[i] = i * 2 + 1;
    }
    ah.wg[1] = 0;

    size_t bs = 0;
    for (int8_t i=0;i < 6;i++,bs += (1 << ah.dist_bits[i]))
        ah.dist_base[i] = bs;

    ssize_t op = 0;

    while (op < usize || usize == -1) {
        int16_t sym = d0llz_AHuff_get(&br,&ah);
        if (sym == 0x100) break;

        if (sym < 0x100) dst[op++] = sym;
        else {
            int16_t grp = (sym - 0x101) / 0x3E;
            int16_t len = sym - grp * 0x3E - 0xFE;
            ssize_t dist = op - (get_bits_l(&br, ah.dist_bits[grp]) + len + ah.dist_base[grp]);
            for (int16_t i=0;i < len && (op < usize || usize == -1);i++,dist++) {
                uint8_t b;
                if (dist < 0) b = 0;
                else b = dst[dist];
                dst[op++] = b;
            }
        }
    }

    return op;
}

EXPORT void decrypt_inv(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst) {
    for (size_t p=0;p < size;p++) dst[p] = ~src[p];
}
EXPORT void decrypt_swp4(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst) {
    for (size_t p=0;p < size;p++) dst[p] = SWAP8(src[p]);
}
EXPORT void decrypt_roll(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] - key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rolr(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] + key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_xor(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                        const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] ^ key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rxor(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t key) {
    if (size == 0) return;
    size_t p = 1;
    dst[0] = src[0] ^ key;
    for (;p < size;p++) dst[p] = src[p] ^ dst[p - 1];
}
EXPORT void decrypt_cxor(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] ^ (uint8_t)(key[kc++] + p);
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_dxor(const uint8_t *restrict src,  const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key1, const size_t ksize1,
                         const uint8_t *restrict key2, const size_t ksize2) {
    size_t kc1 = 0;
    size_t kc2 = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] ^ key1[kc1++] ^ key2[kc2++];
        if (kc1 >= ksize1) kc1 = 0;
        if (kc2 >= ksize2) kc2 = 0;
    }
}
EXPORT void decrypt_tea(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                              uint8_t *restrict key, const int8_t le) {
    uint32_t *k = (uint32_t *)key;
    const uint32_t *inp = (uint32_t *)src;
    uint32_t *out = (uint32_t *)dst;
    size_t bc = size / 4;

    if (!le)
        for (int i=0;i < 4;i++) k[i] = SWAP32(k[i]);

    const uint32_t DLT = 0x9e3779b9;
    for (size_t p=0;p < bc;p+=2) {
        uint32_t v0 = inp[p];
        uint32_t v1 = inp[p + 1];
        if (!le) {
            v0 = SWAP32(v0);
            v1 = SWAP32(v1);
        }

        uint32_t sv = (DLT * 32) & 0xFFFFFFFF;
        for (int i = 0; i < 32; i++) {
            v1 -= ((v0 << 4) + k[2]) ^ (v0 + sv) ^ ((v0 >> 5) + k[3]);
            v0 -= ((v1 << 4) + k[0]) ^ (v1 + sv) ^ ((v1 >> 5) + k[1]);
            sv -= DLT;
        }

        if (!le) {
            v0 = SWAP32(v0);
            v1 = SWAP32(v1);
        }

        out[p] = v0;
        out[p + 1] = v1;
    }
}
EXPORT void decrypt_rsdk3(uint8_t *restrict buf, const size_t size,
                    const uint8_t *restrict key1, const uint8_t *restrict key2) {
    uint8_t kn = (size >> 2) & 0x7F;
    uint8_t k2p = (kn % 9) + 1;
    uint8_t k1p = (kn % k2p) + 1;
    int8_t swp = 0;

    for (size_t p=0;p < size;p++) {
        uint8_t b = buf[p];
        b ^= key2[k2p++] ^ kn;
        if (swp) b = SWAP8(b);
        b ^= key1[k1p++];
        buf[p] = b;

        if (k1p <= 19 || k2p <= 11) {
            if (k1p > 19) {
                k1p = 1;
                swp = !swp;
            }
            if (k2p > 11) {
                k2p = 1;
                swp = !swp;
            }
        } else {
            kn = (kn + 1) & 0x7F;
            if (swp) {
                k1p = (kn % 12) + 6;
                k2p = (kn % 5) + 4;
            } else {
                k1p = (kn % 15) + 3;
                k2p = (kn % 7) + 1;
            }
            swp = !swp;
        }
    }
}
EXPORT void decrypt_rsdk4(uint8_t *restrict buf, const size_t size,
                    const uint32_t key1, const uint32_t key2,
                    const uint8_t *restrict keyx1, const uint8_t *restrict keyx2) {
    int8_t swp = 0;
    uint8_t k1p = 0;
    uint8_t k2p = 8;
    uint8_t kn = (size >> 2) & 0x7F;

    for (size_t p=0;p < size;p++) {
        uint8_t b = buf[p];
        b ^= keyx2[k2p++] ^ kn;
        if (swp) b = SWAP8(b);
        b ^= keyx1[k1p++];
        buf[p] = b;

        if (k1p <= 15) {
            if (k2p > 12) {
                k2p = 0;
                swp = !swp;
            }
        } else if (k2p <= 8) {
            k1p = 0;
            swp = !swp;
        } else {
            kn = (kn + 2) & 0x7F;
            uint32_t t1 = HIMUL64(key2, kn);
            t1 += (kn - t1) >> 1;
            uint32_t t2 = (HIMUL64(key1, kn) >> 3) * 3;
            if (swp) {
                k1p = kn - (t1 >> 2) * 7;
                k2p = kn - (t2 << 2) + 2;
            } else {
                k1p = kn - (t2 << 2) + 3;
                k2p = kn - (t1 >> 2) * 7;
            }
            swp = !swp;
        }
    }
}
EXPORT void decrypt_rsdk5(uint8_t *restrict buf, const size_t size,
                    const uint8_t *restrict key1, const uint8_t *restrict key2) {
    int8_t swp = 0;
    uint8_t k1p = 0;
    uint8_t k2p = 8;
    uint8_t kn = (size >> 2) & 0x7F;

    for (size_t p=0;p < size;p++) {
        uint8_t b = buf[p];
        b ^= key2[k2p++] ^ kn;
        if (swp) b = SWAP8(b);
        b ^= key1[k1p++];
        buf[p] = b;

        if (k1p <= 15) {
            if (k2p > 12) {
                k2p = 0;
                swp = !swp;
            }
        } else if (k2p <= 8) {
            k1p = 0;
            swp = !swp;
        } else {
            kn = (kn + 2) & 0x7F;
            if (swp) {
                k1p = kn % 7;
                k2p = (kn % 12) + 2;
            } else {
                k1p = (kn % 12) + 3;
                k2p = kn % 7;
            }
            swp = !swp;
        }
    }
}
EXPORT void decrypt_hornby(uint8_t *restrict buf, const size_t size,
                     const uint8_t key, const uint8_t msk) {
    if (size < 2) return;

    buf[1] ^= key;
    for (size_t i=1;i < size;i++) buf[i] ^= buf[i - 1] ^ (buf[i] & msk);
}
EXPORT void init_mmfs(uint8_t *restrict dst, const uint8_t *restrict key) {
    size_t kp = 0;
    uint8_t i2 = 0;
    for (int i1=0;i1 < 0x100;i1++) {
        if (!key[kp]) kp = 0;
        i2 += key[kp++] + dst[i1];
        uint8_t b = dst[i2];
        dst[i2] = dst[i1];
        dst[i1] = b;
    }
}
EXPORT void decrypt_mmfs(uint8_t *restrict buf, const size_t size, uint8_t *restrict key) {
    uint8_t i1 = 0;
    uint8_t i2 = 0;
    for (size_t p=0;p < size;p++) {
        i2 += key[++i1];
        uint8_t b = key[i2];
        key[i2] = key[i1];
        key[i1] = b;
        buf[p] ^= key[(uint8_t)(key[i1] + key[i2])];
    }
}
EXPORT void init_selene(uint8_t *restrict dst, const uint8_t *restrict key, const size_t ksize, const uint32_t seed) {
    INIT_MT19937(mt);
    MT19937_seed(&mt,seed);
    size_t kc = 0;

    for (size_t i=0;i < 0x10000;i++) {
        dst[i] = (uint8_t)(key[kc++] ^ (MT19937_rand(&mt) >> 16));
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rc4_playpond(uint8_t *restrict buf, const size_t size, const uint8_t *restrict key, const size_t ksize, const size_t drop) {
    uint8_t S[0x100];
    for (size_t i=0;i < 0x100;i++) S[i] = i;

    uint8_t j = 0;
    size_t kc = 0;
    for (size_t ix=0;ix < 0x100;ix++) {
        for (size_t i=0;i < 0x100;i++) {
            j += S[i] + key[kc];
            uint8_t b = S[j];
            S[j] = S[i];
            S[i] = b;
            kc += 1;
            if (kc >= ksize) kc = 0;
        }
    }

    j = 0;
    uint8_t i = 0;
    for (size_t ix=0;ix < drop;ix++) {
        i += 1;
        j += S[i];
        uint8_t b = S[j];
        S[j] = S[i];
        S[i] = b;
    }

    for (size_t p=0;p < size;p++) {
        i += 1;
        j += S[i];
        uint8_t b = S[j];
        S[j] = S[i];
        S[i] = b;
        buf[p] ^= S[(S[i] + S[j]) & 0xFF];
    }
}
EXPORT void decrypt_zipcrypto(uint8_t *restrict buf, const size_t size, const uint8_t *restrict key, const size_t ksize) {
    uint32_t crc32t[0x100];
    for (size_t i=0;i < 0x100;i++) {
        uint32_t c = i;
        for (size_t j=0;j < 8;j++) {
            if (c & 1) c = (c >> 1) ^ 0xEDB88320;
            else c = c >> 1;
        }
        crc32t[i] = c;
    }
    #define crc32(crc,b) ((crc) >> 8) ^ crc32t[((crc) ^ (b)) & 0xFF]

    uint32_t k0 = 0x12345678;
    uint32_t k1 = 0x23456789;
    uint32_t k2 = 0x34567890;

    #define mix(b) \
        k0 = crc32(k0,(b));\
        k1 += (k0 & 0xFF);\
        k1 = k1 * 0x8088405 + 1;\
        k2 = crc32(k2,k1 >> 24);

    for (size_t p=0;p < ksize;p++)
        mix(key[p]);

    for (size_t p=0;p < size;p++) {
        uint32_t k = k2 | 2;
        buf[p] ^= (k * (k^1)) >> 8;
        mix(buf[p]);
    }

    #undef crc32
    #undef mix
}
EXPORT void decrypt_remedy_ras(uint8_t *restrict buf, const size_t size, const uint32_t key) {
    int32_t tmp1 = key;
    if (!tmp1) tmp1 = 1;
    uint8_t tmp2 = 0x12;

    for (size_t p=0;p < size;p++) {
        tmp1 = -2 * (tmp1 / 177) + 171 * (tmp1 % 177);
        uint8_t b = ((buf[p] << p % 5) | (buf[p] >> (8 - p % 5))) ^ tmp2;
        tmp2 += 6;
        buf[p] = (uint8_t)(b + tmp1);
    }
}
EXPORT void init_empire_magic(uint8_t *restrict buf) {
    uint64_t seed = 0x8647d59f;
    uint32_t state = 0;
    for (uint16_t i=0;i < 0x400;i++) {
        uint64_t prod = seed * 0x4e35;
        state = (((uint32_t)prod == 0xFFFFFFFF) | ((uint32_t)seed * 0x15a)) + (uint32_t)(prod >> 32) + state * 0x4e35;
        buf[i] = (uint8_t)state;
        seed = (uint32_t)prod + 1;
    }
}
EXPORT void decrypt_empire_magic(uint8_t *restrict buf, const size_t size, const uint8_t *restrict key, const size_t ksize,
                           const uint8_t *restrict table, const uint32_t offset) {
    for (size_t p=0;p < size;p++)
        buf[p] = (buf[p] + 1 + key[p % ksize]) ^ table[(offset + p) % 0x3cb];
}

static inline uint32_t tfit_get_t(const uint32_t *t, const uint8_t *buf, const uint8_t x) {
    return t[0x100 * x + buf[x]];
}
#define TFIT_ROUND_BLOCK(t,n,x10, x11, x12, x13,\
                             x20, x21, x22, x23,\
                             x30, x31, x32, x33,\
                             x40, x41, x42, x43)\
    void CONCATX(t,crypt_tfit_round##n)(uint8_t *restrict buf, const uint32_t *restrict k, const uint32_t *restrict t) {\
        uint32_t tmp[4];\
        tmp[0] = tfit_get_t(t,buf,x10) ^ tfit_get_t(t,buf,x11) ^ tfit_get_t(t,buf,x12) ^ tfit_get_t(t,buf,x13) ^ k[0];\
        tmp[1] = tfit_get_t(t,buf,x20) ^ tfit_get_t(t,buf,x21) ^ tfit_get_t(t,buf,x22) ^ tfit_get_t(t,buf,x23) ^ k[1];\
        tmp[2] = tfit_get_t(t,buf,x30) ^ tfit_get_t(t,buf,x31) ^ tfit_get_t(t,buf,x32) ^ tfit_get_t(t,buf,x33) ^ k[2];\
        tmp[3] = tfit_get_t(t,buf,x40) ^ tfit_get_t(t,buf,x41) ^ tfit_get_t(t,buf,x42) ^ tfit_get_t(t,buf,x43) ^ k[3];\
        memcpy(buf,tmp,0x10);\
    }
TFIT_ROUND_BLOCK(en,A, 0 ,1 ,2 ,3 ,
                       4 ,5 ,6 ,7 ,
                       8 ,9 ,10,11,
                       12,13,14,15)
TFIT_ROUND_BLOCK(en,B, 0 ,5 ,10,15,
                       3 ,4 ,9 ,14,
                       2 ,7 ,8 ,13,
                       1 ,6 ,11,12)
TFIT_ROUND_BLOCK(de,B, 0 ,7 ,10,13,
                       1, 4 ,11,14,
                       2, 5 ,8 ,15,
                       3, 6 ,9 ,12)
void decrypt_tfit_block(const uint8_t *restrict src, uint8_t *dst, const uint8_t *iv,
                        const size_t rounds, const uint32_t *restrict k, const uint32_t *restrict t) {
    uint8_t tmp[16];
    if (iv != NULL) {
        for (size_t i=0;i < 16;i++) tmp[i] = src[i] ^ iv[i];
    } else memcpy(tmp,src,0x10);
    encrypt_tfit_roundA(tmp,k + 0,t + 0x0000);
    encrypt_tfit_roundA(tmp,k + 4,t + 0x1000);
    for (size_t i=2;i < rounds - 1;i++)
        decrypt_tfit_roundB(tmp,k + i*4,t + i*0x1000);
    encrypt_tfit_roundA(tmp,k + (rounds - 1)*4,t + (rounds - 1)*0x1000);
    memcpy(dst,tmp,0x10);
}
void encrypt_tfit_block(const uint8_t *restrict src, uint8_t *dst, const uint8_t *iv,
                        const size_t rounds, const uint32_t *restrict k, const uint32_t *restrict t) {
    uint8_t tmp[16];
    if (iv != NULL) {
        for (size_t i=0;i < 16;i++) tmp[i] = src[i] ^ iv[i];
    } else memcpy(tmp,src,0x10);
    encrypt_tfit_roundA(tmp,k + 0,t + 0x0000);
    encrypt_tfit_roundA(tmp,k + 4,t + 0x1000);
    for (size_t i=2;i < rounds - 1;i++)
        encrypt_tfit_roundB(tmp,k + i*4,t + i*0x1000);
    encrypt_tfit_roundA(tmp,k + (rounds - 1)*4,t + (rounds - 1)*0x1000);
    memcpy(dst,tmp,0x10);
}
EXPORT void decrypt_tfit(uint8_t *restrict src, const size_t size, uint8_t *restrict dst, const uint8_t *restrict iv,
                   const uint32_t *restrict key, const uint32_t *restrict table, const size_t block_size) {
    uint8_t tmp[16];
    memcpy(tmp,iv,0x10);
    for (size_t p=0;p < size;p += block_size + 0x10) {
        for (size_t i=0;i < block_size / 16;i++) {
            decrypt_tfit_block(src + p + i*16, dst + p + i*16, tmp, 17, key, table);
            memcpy(tmp,dst + p + i*16,0x10);
        }
        decrypt_tfit_block(src + p + block_size, tmp, tmp, 17, key, table);
    }
}
EXPORT void mac_cmac_tfit(uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                    const uint32_t *restrict key, const uint32_t *restrict table) {
    uint8_t tmp[16] = {0};
    uint8_t lblk_scrmbl[16];

    encrypt_tfit_block(tmp, lblk_scrmbl, NULL, 13, key, table);
    DBLGF(lblk_scrmbl, lblk_scrmbl);
    if (size != 0) {
        size_t blocks = size / 16 + (size % 16 != 0);
        for (size_t i=0;i < blocks - 1;i++)
            encrypt_tfit_block(src + i*16, tmp, tmp, 13, key, table);
    }

    if (size % 16 || size == 0) {
        DBLGF(lblk_scrmbl, lblk_scrmbl);

        uint8_t block[16] = {0};
        block[size % 16] = 0x80;
        memcpy(block, src + size - (size % 16), size % 16);
        for (size_t i=0;i < 16;i++) tmp[i] ^= lblk_scrmbl[i] ^ block[i];
    } else {
        for (size_t i=0;i < 16;i++) tmp[i] ^= lblk_scrmbl[i] ^ src[size - 16 + i];
    }

    encrypt_tfit_block(tmp, dst, NULL, 13, key, table);
}

EXPORT uint32_t hash_pivotal(const uint8_t *restrict src, const size_t size) {
    uint32_t h = 1;

    for (size_t p=0;p < size;p++) {
        uint8_t b = src[p];
        for (int i=0;i < 8;i++) {
            h = (h << 1) | (((h >> 21) ^ (h >> 1) ^ h ^ (h >> 31) ^ (b >> i)) & 1);
        }
    }

    return h;
}
EXPORT uint32_t hash_super_fast_le(const uint8_t *restrict src, const size_t size) {
    if (size == 0) return 0;

    uint32_t h = (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        h += read16le(s);s+=2;
        h = (h << 16) ^ ((read16le(s) << 11) ^ h);s+=2;
        h += h >> 11;
    }

    switch (rem) {
        case 3:
            h += read16le(s);s+=2;
            h ^= (h << 16) ^ ((uint32_t)(int8_t)s[0] << 18);
            h += h >> 11;
            break;
        case 2:
            h += read16le(s);s+=2;
            h ^= h << 11;
            h += h >> 17;
            break;
        case 1:
            h += (uint32_t)(int8_t)s[0];
            h ^= h << 10;
            h += h >> 1;
            break;
    }

    h ^= h << 3;
    h += h >> 5;
    h ^= h << 4;
    h += h >> 17;
    h ^= h << 25;
    h += h >> 6;

    return h;
}
EXPORT uint32_t hash_super_fast_be(const uint8_t *restrict src, const size_t size) {
    if (size == 0) return 0;

    uint32_t h = (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        h += read16be(s);s+=2;
        h = (h << 16) ^ ((read16be(s) << 11) ^ h);s+=2;
        h += h >> 11;
    }

    switch (rem) {
        case 3:
            h += read16be(s);s+=2;
            h ^= (h << 16) ^ ((uint32_t)(int8_t)s[0] << 18);
            h += h >> 11;
            break;
        case 2:
            h += read16be(s);s+=2;
            h ^= h << 11;
            h += h >> 17;
            break;
        case 1:
            h += (uint32_t)(int8_t)s[0];
            h ^= h << 10;
            h += h >> 1;
            break;
    }

    h ^= h << 3;
    h += h >> 5;
    h ^= h << 4;
    h += h >> 17;
    h ^= h << 25;
    h += h >> 6;

    return h;
}
EXPORT uint32_t hash_elf(const uint8_t *restrict src, const size_t size) {
    uint32_t h = 0;
    uint32_t hi;
    for (size_t p=0;p < size;p++) {
        h = (h << 4) + src[p];
        if (hi = h & 0xf0000000)
            h ^= hi >> 24;
        h &= ~hi;
    }
    return h;
}
EXPORT uint32_t hash_ap(const uint8_t *restrict src, const size_t size) {
    uint32_t h = 0xAAAAAAAA;
    for (size_t p=0;p < size;p++) {
        h ^= ((p & 1) == 0) ? (  (h <<  7) ^  src[p] * (h >> 3)) :
                              (~((h << 11) + (src[p] ^ (h >> 5))));
    }
    return h;
}
#define MURMUR2_32_M 0x5bd1e995
EXPORT uint32_t hash_murmur2_le(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed ^ (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32le(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    switch (rem) {
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_32_M;
    }

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;
    return h;
}
EXPORT uint32_t hash_murmur2_be(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed ^ (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32be(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    switch (rem) {
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_32_M;
    }

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;
    return h;
}
EXPORT uint32_t hash_murmur2A_le(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32le(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    uint32_t t = 0;
    switch (rem) {
        case 3: t ^= s[2] << 16;
        case 2: t ^= s[1] << 8;
        case 1: t ^= s[0];
    }

    t *= MURMUR2_32_M;
    t ^= t >> 24;
    h = (h * MURMUR2_32_M) ^ (t * MURMUR2_32_M);
    uint32_t l = (uint32_t)size;
    l *= MURMUR2_32_M;
    l ^= l >> 24;
    h = (h * MURMUR2_32_M) ^ (l * MURMUR2_32_M);

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;

    return h;
}
EXPORT uint32_t hash_murmur2A_be(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32be(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    uint32_t t = 0;
    switch (rem) {
        case 3: t ^= s[2] << 16;
        case 2: t ^= s[1] << 8;
        case 1: t ^= s[0];
    }

    t *= MURMUR2_32_M;
    t ^= t >> 24;
    h = (h * MURMUR2_32_M) ^ (t * MURMUR2_32_M);
    uint32_t l = (uint32_t)size;
    l *= MURMUR2_32_M;
    l ^= l >> 24;
    h = (h * MURMUR2_32_M) ^ (l * MURMUR2_32_M);

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;

    return h;
}
#define MURMUR2_64_M 0xc6a4a7935bd1e995
EXPORT uint64_t hash_murmur2_64A_le(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint64_t h = seed ^ ((uint64_t)size * MURMUR2_64_M);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint64_t k = read64le(s);s+=8;
        k *= MURMUR2_64_M;
        k ^= k >> 47;
        h = (h ^ (k * MURMUR2_64_M)) * MURMUR2_64_M;
    }

    switch (rem) {
        case 7: h ^= (uint64_t)s[6] << 48;
        case 6: h ^= (uint64_t)s[5] << 40;
        case 5: h ^= (uint64_t)s[4] << 32;
        case 4: h ^= (uint64_t)s[3] << 24;
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_64_M;
    }

    h ^= h >> 47;
    h *= MURMUR2_64_M;
    h ^= h >> 47;
    return h;
}
EXPORT uint64_t hash_murmur2_64A_be(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint64_t h = seed ^ ((uint64_t)size * MURMUR2_64_M);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint64_t k = read64be(s);s+=8;
        k *= MURMUR2_64_M;
        k ^= k >> 47;
        h = (h ^ (k * MURMUR2_64_M)) * MURMUR2_64_M;
    }

    switch (rem) {
        case 7: h ^= (uint64_t)s[6] << 48;
        case 6: h ^= (uint64_t)s[5] << 40;
        case 5: h ^= (uint64_t)s[4] << 32;
        case 4: h ^= (uint64_t)s[3] << 24;
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_64_M;
    }

    h ^= h >> 47;
    h *= MURMUR2_64_M;
    h ^= h >> 47;
    return h;
}
EXPORT uint64_t hash_murmur2_64B_le(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint32_t h1 = (uint32_t)seed ^ (uint32_t)size;
    uint32_t h2 = (uint32_t)(seed >> 32);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k1 = read32le(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        uint32_t k2 = read32le(s);s+=4;
        k2 *= MURMUR2_32_M;
        k2 ^= k2 >> 24;
        h2 = (h2 * MURMUR2_32_M) ^ (k2 * MURMUR2_32_M);
    }

    if (rem >= 4) {
        uint32_t k1 = read32le(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        rem -= 4;
    }

    switch (rem) {
        case 3: h2 ^= s[2] << 16;
        case 2: h2 ^= s[1] << 8;
        case 1: h2 ^= s[0];
                h2 *= MURMUR2_32_M;
    }

    h1 ^= h2 >> 18;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 22;h2 *= MURMUR2_32_M;
    h1 ^= h2 >> 17;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 19;h2 *= MURMUR2_32_M;

    uint64_t h = h1;
    return (h << 32) | h2;
}
EXPORT uint64_t hash_murmur2_64B_be(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint32_t h1 = (uint32_t)seed ^ (uint32_t)size;
    uint32_t h2 = (uint32_t)(seed >> 32);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k1 = read32be(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        uint32_t k2 = read32be(s);s+=4;
        k2 *= MURMUR2_32_M;
        k2 ^= k2 >> 24;
        h2 = (h2 * MURMUR2_32_M) ^ (k2 * MURMUR2_32_M);
    }

    if (rem >= 4) {
        uint32_t k1 = read32be(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        rem -= 4;
    }

    switch (rem) {
        case 3: h2 ^= s[2] << 16;
        case 2: h2 ^= s[1] << 8;
        case 1: h2 ^= s[0];
                h2 *= MURMUR2_32_M;
    }

    h1 ^= h2 >> 18;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 22;h2 *= MURMUR2_32_M;
    h1 ^= h2 >> 17;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 19;h2 *= MURMUR2_32_M;

    uint64_t h = h1;
    return (h << 32) | h2;
}
EXPORT uint32_t hash_empire_magic(const uint8_t *restrict src, const size_t size, const int8_t end) {
    uint32_t h = size * 0x1EEF;

    uint8_t ss = (size < 4) ? size : 4;
    size_t off = end ? (size - ss) : 0;
    for (uint8_t i=0;i < ss;i++) h += src[off + i] << (24 - i*8);
    for (size_t p=0;p < size;p++) h += src[p] * 0x2F;

    return h % 0x3CB;
}

#ifdef __cplusplus
}
#endif

/*'''#*/
