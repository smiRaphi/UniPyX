#define DUMMY1 /*

import os,sys
from hashlib import sha256
DLLP = os.path.splitext(__file__)[0] + ('.dll' if sys.platform == 'win32' else '.so')
CH = sha256(open(__file__,'rb').read().split(b"'''*" b"/",1)[1]).digest()

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
        cmd = ['/Ox','/GS-','/GR-','/Gs999999','/LD','/TC',__file__,f'/Fe:{DLLP}','/link','/NODEFAULTLIB','/MANIFEST:NO','/MERGE:.rdata=.text','/OPT:REF','/OPT:ICF','/ALIGN:16','/ENTRY:DllMain']
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
u32 = ctypes.c_uint32
s32 = ctypes.c_int
szt = ctypes.c_size_t
sszt = ctypes.c_ssize_t
void = ctypes.c_void_p
P = ctypes.POINTER

def _xbase_func(fnc,src,usize):
    i = (u8 * len(src)).from_buffer_copy(src)
    o = (u8 * usize)()
    r = fnc(i,len(src),o,usize)
    return bytes(o)[:r]
def _y1base_func(fnc,src,key):
    i = (u8 * len(src)).from_buffer_copy(src)
    o = (u8 * len(src))()
    k = (u8 * len(key)).from_buffer_copy(key)
    fnc(i,len(src),o,k,len(key))
    return bytes(o)
def _y2base_func(fnc,src,key,iv):
    i = (u8 * len(src)).from_buffer_copy(src)
    o = (u8 * len(src))()
    k = (u8 * len(key)).from_buffer_copy(key)
    v = (u8 * len(iv)).from_buffer_copy(iv)
    fnc(i,len(src),o,k,len(key),v,len(iv))
    return bytes(o)

class X:
    MMFS = {};SELENE = {}
    def __init__(self):
        assert os.path.exists(DLLP)
        d = open(DLLP,'rb')
        d.seek(d.seek(0,2) - len(CH))
        ch = d.read(len(CH))
        d.close()
        if ch != CH:
            os.remove(DLLP)
            raise ValueError('DLL is out of date, deleted')

        self.dll = ctypes.CDLL(DLLP)
        for e in (
            ('decompress_lz10_raw',(P(u8),szt,P(u8),sszt),    sszt,1),
            ('decompress_lz11_raw',(P(u8),szt,P(u8),sszt),    sszt,1),
            ('decompress_lz40_raw',(P(u8),szt,P(u8),sszt),    sszt,1),
            ('decompress_blz_raw', (P(u8),szt,P(u8),sszt),    sszt,0),
            ('decompress_lz4_fast',(P(u8),szt,P(u8),sszt),    sszt,1),
            ('decompress_lzss8',   (P(u8),szt,P(u8),sszt),    sszt,1),
            ('decompress_huffman', (P(u8),szt,P(u8),sszt,s32),sszt,0),
            ('decompress_rtl_lz',  (P(u8),szt,P(u8),sszt),    sszt,1),
            ('decrypt_xor'  ,(P(u8),szt,P(u8),P(u8),szt),void,2),
            ('decrypt_rxor' ,(P(u8),szt,P(u8),u8),void,0),
            ('decrypt_cxor' ,(P(u8),szt,P(u8),P(u8),szt),void,0),
            ('decrypt_dxor' ,(P(u8),szt,P(u8),P(u8),szt,P(u8),szt),void,0),
            ('decrypt_tea'  ,(P(u8),szt,P(u8),P(u8),s32),void,0),
            ('decrypt_hatch',(P(u8),szt,P(u8),P(u8)),void,0),
            ('decrypt_hornby',(P(u8),szt,u8,u8),void,0),
            ('init_mmfs',(P(u8),P(u8)),void,0),
            ('decrypt_mmfs',(P(u8),szt,P(u8)),void,0),
            ('init_selene',(P(u8),P(u8),szt,u32),void,0),
        ):
            fnc = self.dll[e[0]]
            fnc.argtypes = e[1]
            fnc.restype = e[2]

            if e[3]:
                if e[3] == 1:
                    def wrapper(src,usize,_f=fnc): return _xbase_func(_f,src,usize)
                elif e[3] == 2:
                    def wrapper(src,key,_f=fnc): return _y1base_func(_f,src,key)
                elif e[3] == 3:
                    def wrapper(src,key,iv,_f=fnc): return _y2base_func(_f,src,key,iv)
                setattr(self,e[0],wrapper)

    def decompress_lz10_raw(src:bytes,usize:int) -> bytes: ...
    def decompress_lz11_raw(src:bytes,usize:int) -> bytes: ...
    def decompress_lz4_fast(src:bytes,usize:int) -> bytes: ...
    def decompress_lzss8(src:bytes,usize:int) -> bytes: ...
    def decompress_rtl_lz(src:bytes,usize:int) -> bytes: ...

    def decompress_blz_raw(self,src:bytes,usize:int) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_blz_raw(i,len(src),o,usize)
        return bytes(o)[r:]
    def decompress_huffman(self,src:bytes,usize:int,padding:bool=False) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_huffman(i,len(src),o,usize,1 if padding else 0)
        if r == -1: raise ValueError('Decompression failed')
        return bytes(o)[:r]

    def decrypt_xor(src:bytes,key:bytes) -> bytes: ...

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
        assert len(key) == 0x10 and not len(src) % 8
        i = (u8 * len(src)).from_buffer_copy(src)
        k = (u8 * 0x10).from_buffer_copy(key)
        o = (u8 * len(src))()
        self.dll.decrypt_tea(i,len(src),o,k,1 if le else 0)
        return bytes(o)
    def decrypt_hatch(self,src:bytes,key:bytes) -> bytes:
        from zlib import crc32
        if len(key) == 4: key = key*4
        assert len(key) == 0x10
        iv = crc32(len(src).to_bytes(8,'little')).to_bytes(4,'little')*4

        d = (u8 * len(src)).from_buffer_copy(src)
        k = (u8 * 0x10).from_buffer_copy(key)
        v = (u8 * 0x10).from_buffer_copy(iv)
        self.dll.decrypt_hatch(d,len(src),k,v)
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
        from zlib import crc32
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

'''*/

#include <stdint.h>

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
#ifdef _MSC_VER
    #pragma function(memset)
    void* memset(void* dest, int c, size_t count) {
        uint8_t* bytes = (uint8_t*)dest;
        while (count--) {
            *bytes++ = (uint8_t)c;
        }
        return dest;
    }
#endif

#ifdef __cplusplus
extern "C" {
#endif

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
EXPORT ssize_t decompress_lzss8(const uint8_t *restrict src, const size_t zsize,
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

        if (f & 1) {
            CHKo(0);
            dst[op++] = src[ip++];
        }
        else {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];

            size_t dist = (op - 18 - (((b2 & 0xF0) << 4) | b1)) & 0xFFF;
            if (dist == 0) dist = 0x1000;
            size_t lng = (b2 & 0x0F) + 3;

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
                    uint16_t s = src[ip] | (src[ip + 1] << 8);ip += 2;
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
                uint16_t l = src[ip] | (src[ip + 1] << 8);ip += 2;
                uint16_t o = src[ip] | (src[ip + 1] << 8);ip += 2;
                while (b & 0x30) {
                    CHKi(0);CHKo(0);
                    dst[op++] = src[ip++];
                    b -= 0x10;
                }
                for (int i=0;i < l;i++,op++) {
                    CHKo(0);
                    dst[op] = dst[op - o - l + 1];
                }
            } else {
                CHKi(1);
                uint16_t o = src[ip] | (src[ip + 1] << 8);ip += 2;
                uint16_t l = (b & 0x0F) + 2;
                while (b & 0x30) {
                    CHKi(0);
                    dst[op++] = src[ip++];
                    b -= 0x10;
                }
                for (int i=0;i < l;i++,op++) {
                    CHKo(0);
                    dst[op] = dst[op - o - l + 1];
                }
            }
        } else {
            if (b & 0x40) {
                CHKi(1);CHKo(1);
                dst[op++] = src[ip++];
                dst[op++] = src[ip++];
            }
            uint8_t o = (b & 0x3F)*2 + 2;
            dst[op] = dst[op - o];op++;
            dst[op] = dst[op - o];op++;
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_huffman(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const ssize_t usize, const int padding) {
    size_t ip = 0;
    uint8_t _gb = 0;
    uint8_t msk = 0;

    #define GET_BIT(ob) do { \
        if (!msk) { \
            if (ip >= zsize) goto error; \
            _gb = src[ip++]; \
            msk = 0x80; \
        } \
        ob = (_gb & msk) ? 1 : 0; \
        msk >>= 1; \
    } while(0)
    #define GET_BITS(n,ov) do { \
        ov = 0; \
        for (int _i=0;_i < (n);_i++) { \
            uint8_t _b; \
            GET_BIT(_b); \
            ov |= (_b << ((n) - 1 - _i)); \
        } \
    } while(0)

    uint16_t tok = 0x100;
    uint16_t lhs[0x200] = {0};
    uint16_t rhs[0x200] = {0};
    int root = -1;
    int nstack[512];
    int sstack[512];
    int sp = 0;
    int cur_par = -1;
    int cur_side = 0;

    while (1) {
        uint8_t b;
        GET_BIT(b);

        uint16_t nodev;
        if (b) {
            nodev = tok++;
            if (nodev >= 0x200) goto error;
        } else GET_BITS(8,nodev);

        if (cur_par == -1) root = nodev;
        else if (cur_side) lhs[cur_par] = nodev;
        else rhs[cur_par] = nodev;

        if (b) {
            if (cur_par != -1) {
                nstack[sp] = cur_par;
                sstack[sp] = cur_side;
                sp++;
            }

            cur_par = nodev;
            cur_side = 1;
        } else {
            if (cur_side) cur_side = 0;
            else {
                while (!cur_side && sp > 0) {
                    sp--;
                    cur_par = nstack[sp];
                    cur_side = sstack[sp];
                }
                if (!cur_side && sp == 0) break;
                if (cur_side) cur_side = 0;
                else break;
            }
        }
    }

    if (padding) msk = 0;

    ssize_t op = 0;
    while (usize == -1 || op < usize) {
        uint16_t sym = root;
        while (sym >= 0x100) {
            if (!msk && ip >= zsize) goto eof;
            uint8_t b;
            GET_BIT(b);
            if (b) sym = rhs[sym];
            else sym = lhs[sym];
        }
        dst[op++] = (uint8_t)sym;
    }

eof:
    #undef GET_BIT
    #undef GET_BITS
    return op;

error:
    #undef GET_BIT
    #undef GET_BITS
    return -1;
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
                              uint8_t *restrict key, const int le) {
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
EXPORT void decrypt_hatch(uint8_t *restrict buf, const size_t size,
                    const uint8_t *restrict key, const uint8_t *restrict iv) {
    int swp = 0;
    uint8_t i1 = 0;
    uint8_t i2 = 8;
    uint8_t xr = (size >> 2) & 0x7F;

    for (size_t i=0;i < size;i++) {
        uint8_t b = buf[i];
        b ^= xr ^ iv[i2++];
        if (swp) b = ((b & 0x0F) << 4) | (b >> 4);
        b ^= key[i1++];
        buf[i] = b;

        if (i1 < 0x10) {
            if (i2 > 12) {
                i2 = 0;
                swp = !swp;
            }
        } else if (i2 <= 8) {
            i1 = 0;
            swp = !swp;
        } else {
            xr = (xr + 2) & 0x7F;
            if (swp) {
                i1 = xr % 7;
                i2 = (xr % 12) + 2;
            } else {
                i1 = (xr % 12) + 3;
                i2 = xr % 7;
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

#ifdef __cplusplus
}
#endif

#define DUMMY2 /*
'''#*/
