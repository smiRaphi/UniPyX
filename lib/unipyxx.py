__all__ = ['X']

import os,sys
PRJP = os.path.splitext(os.path.abspath(__file__))[0]
if __name__ == '__main__':
    import subprocess
    sys.exit(subprocess.call([sys.executable,os.path.join(PRJP,'build.py')]))

DLLP = PRJP + ('.dll' if sys.platform == 'win32' else '.so')
__FNCT = type(lambda:None)
def asrt(c:bool,*r,err:Exception=ValueError):
    if not c:
        if len(r) == 1 and isinstance(r[0],__FNCT): r = r[0]()
        elif r: r = ' '.join(str(x) for x in r)
        else: r = ''
        raise err(r)

import ctypes
cint = ctypes.c_int
u8 = ctypes.c_uint8
s8 = ctypes.c_int8
u32 = ctypes.c_uint32
u16 = ctypes.c_uint16
u64 = ctypes.c_uint64
szt = ctypes.c_size_t
sszt = ctypes.c_ssize_t
void = ctypes.c_void_p
voidp = ctypes.POINTER(ctypes.c_void_p)
P = ctypes.POINTER

class XMemCodecParametersLZX(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('flags',cint),
        ('windowSize',cint),
        ('compressionPartitionSize',cint),
    ]
ZSTDERR = {
    1:'Generic',10:'Prefix unknown',12:'Version unsupported',14:'Frame Parameter: Unsupported',16:'Frame Parameter: Window too large',
    20:'Corruption detected',22:'Checksum wrong',24:'Literals header wrong',30:'Dictionary: Corrupted',32:'Dictionary: Wrong',
    34:'Dictionary: Creation failed',40:'Parameter: Unsupported',41:'Parameter: Combination unsupported',42:'Parameter: Out of bound',
    44:'Table log too large',46:'Max Symbol Value: Too large',48:'Max Symbol Value: Too small',49:'Cannot produce uncompressed block',
    50:'Stability condition not respected',60:'Stage wrong',62:'Init missing',64:'Memory allocation',66:'Workspace too small',
    70:'Output buffer size too small',72:'Input buffer size wrong',74:'Output buffer is NULL',80:'No Forward Progress: Output full',
    82:'No Forward Progress: Input empty',100:'Frame index too large',102:'SeekableIO',104:'Output buffer wrong',105:'Input buffer wrong',
    106:'Sequence producer failed',107:'External sequences invalid'
}

def _1base_func(fnc,src,usize):
    i = (u8 * len(src)).from_buffer_copy(src)
    o = (u8 * ((len(src)*10) if usize == -1 else usize))()
    r = fnc(i,len(src),o,usize)
    if r < 0: raise ValueError(f'Decompression failed ({r})')
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
from hashlib import md5,sha256
from zlib import crc32

class X:
    CRC={};MMFS={};SELENE={};EMPIRE_MAGIC=None
    def __init__(self):
        if not os.path.exists(DLLP): raise FileNotFoundError
        if os.path.exists(os.path.dirname(DLLP) + '/.is_dev'):
            ch = sha256()
            for f in sorted(('comp.c','crypt.c','ext.c','unipyxx.c','util.h')):
                with open(os.path.join(PRJP,f),'rb') as f:
                    ch.update(f.read().replace(b'\r',b'').strip())
            ch = ch.digest()
            with open(DLLP,'rb') as f:
                f.seek(-len(ch),2)
                dch = f.read(len(ch))
            if dch != ch:
                try: os.remove(DLLP)
                except PermissionError: pass
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
            ('decompress_lzss1',    (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_rtl_lz',   (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_vicious_lz',(P(u8),szt,P(u8),sszt),  sszt,1),
            ('decompress_huffman',  (P(u8),szt,P(u8),sszt,s8),sszt,0),
            ('decompress_ash0',     (P(u8),szt,P(u8)),        sszt,0),
            ('decompress_vpk0',     (P(u8),szt,P(u8)),        sszt,0),
            ('decompress_graw_bpe', (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_lzrw1kh',  (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_camelot_blz',(P(u8),szt,P(u8),sszt), sszt,1),
            ('decompress_szdd_raw', (P(u8),szt,P(u8),sszt),   sszt,1),
            ('decompress_hammer',   (P(u8),szt,P(u8)),        sszt,0),
            ('decompress_lzw',      (P(u8),szt,P(u8),sszt,u8,u16,u16,u16,u16),sszt,0),
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
            ('decrypt_camelot_xor',(P(u8),szt,u8),void,0),
            ('decrypt_camelot_rand',(P(u8),szt,u8,u32,szt),void,0),
            ('decrypt_zipd',(P(u8),szt),s8,0),
            ('decrypt_legaia2',(P(u8),szt,u32),void,0),
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
            ('hash_westwood',(P(u32),szt),u32,0),
            ('hash_fnv1_64',(P(u8),szt,u64,u64),u64,0),
            ('hash_fnv1a_64',(P(u8),szt,u64,u64),u64,0),
            ('hash_fnv1_32',(P(u8),szt,u32,u32),u32,0),
            ('hash_fnv1a_32',(P(u8),szt,u32,u32),u32,0),
            ('hash_bkdr',(P(u8),szt,u32,u32),u32,0),
            ('hash_bkdr64',(P(u8),szt,u64,u64),u64,0),
            ('hash_sdbm',(P(u8),szt,u32,u32),u32,0),
            ('hash_djb2',(P(u8),szt,u32),u32,0),
            ('hash_djb2a',(P(u8),szt,u32),u32,0),
            ('hash_joaat',(P(u8),szt,u32),u32,0),
            ('hash_tarzan',(P(u8),szt),u32,4),
            ('hash_luas',(P(u8),szt),u32,4),
            ('mac_cmac_tfit',(P(u8),szt,P(u8),P(u8),P(u8),P(u8)),void,0),
            ('hash_crc_init',(P(u8),u32,u64,s8),s8,0),
            ('hash_crc',(P(u8),u32,P(u8),u64,u64,u64,s8),u64,0),

            ('XMemCreateDecompressionContext',(cint,P(XMemCodecParametersLZX),cint,voidp),cint,0),
            ('XMemDestroyDecompressionContext',(void,),void,0),
            ('XMemDecompress',(void,P(u8),P(szt),P(u8),szt),cint,0),
            ('XMemDecompressSegmentTD',(void,P(u8),P(szt),P(u8),szt,szt,szt),cint,0),
            ('decompress_zip_shrink',(P(u8),szt,P(u8),szt),cint,0),
            ('decompress_zip_reduce',(P(u8),szt,P(u8),szt,u8),cint,0),
            ('decompress_zip_implode',(P(u8),szt,P(u8),szt,u16),cint,0),
            ('decompress_lzfse',(P(u8),szt,P(u8),szt),sszt,1),
            ('decompress_lpaq8',(P(u8),szt,P(u8),szt),sszt,1),
            ('decompress_zstd',(P(u8),szt,P(P(u8)),szt,P(u8),szt),sszt,0),

            ('free_exp',(voidp,),void,0),
        ):
            fnc = getattr(self.dll,e[0])
            fnc.argtypes = e[1]
            fnc.restype = e[2]

            if len(e) > 3 and e[3]:
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
    def decompress_lzss1(src:bytes,usize:int) -> bytes: ...
    def decompress_rtl_lz(src:bytes,usize:int) -> bytes: ...
    def decompress_vicious_lz(src:bytes,usize:int) -> bytes: ...
    def decompress_graw_bpe(src:bytes,usize:int) -> bytes: ...
    def decompress_lzrw1kh(src:bytes,usize:int) -> bytes: ...
    def decompress_camelot_blz(src:bytes,usize:int) -> bytes: ...
    def decompress_szdd_raw(src:bytes,usize:int) -> bytes: ...
    def decompress_capcom_yz2(src:bytes,usize:int) -> bytes: ...
    def decompress_lzfse(src:bytes,usize:int) -> bytes: ...

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
    def decompress_ash0(self,src:bytes) -> bytes:
        if len(src) <= 12 or src[:4] != b'ASH0': raise ValueError('Invalid data')
        us = int.from_bytes(src[5:8],'big')
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * us)()
        r = self.dll.decompress_ash0(i,len(src),o)
        if r == -1: raise ValueError('Decompression failed')
        return bytes(o)[:r]
    def decompress_vpk0(self,src:bytes) -> bytes:
        if len(src) <= 9 or src[:4] != b'vpk0' or src[8] > 1: raise ValueError('Invalid data')
        us = int.from_bytes(src[4:8],'big')
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * us)()
        r = self.dll.decompress_vpk0(i,len(src),o)
        if r < 0: raise ValueError(f'Decompression failed ({r})')
        return bytes(o)[:r]
    def decompress_xmemlzx(self,src:bytes,usize:int,flags:int=0,win_size:int=0,block_size:int=0) -> bytes:
        ctx = void()
        par = XMemCodecParametersLZX(flags,win_size,block_size)
        r = self.dll.XMemCreateDecompressionContext(1,ctypes.byref(par),0,ctypes.byref(ctx))
        if r != 0: raise ValueError(f'Failed to create decompression context ({r})')
        try:
            i = (u8 * len(src)).from_buffer_copy(src)
            o = (u8 * usize)()
            fus = szt(usize)
            r = self.dll.XMemDecompress(ctx,o,ctypes.byref(fus),i,szt(len(src)))
            if r != 0: raise ValueError(f'Failed to decompress ({r})')
            return bytes(o)[:fus.value]
        except OSError: raise ValueError('Failed to decompress (OSError)')
        finally: self.dll.XMemDestroyDecompressionContext(ctx)
    def decompress_xb(self,src:bytes) -> bytes:
        i = src
        asrt(i[:3] == b'\x0F\xF5\x12')
        if i[3] == 0xED:
            asrt(i[4] == 1 and i[5] == 0,'Unsupported version',err=NotImplementedError)
            asrt(i[6] == i[7] == 0,'Non empty padding')
            fl = int.from_bytes(i[12:16],'big')

            ctx = void()
            par = XMemCodecParametersLZX(0,1 << ((fl & 15) + 15),0)
            r = self.dll.XMemCreateDecompressionContext(0,ctypes.byref(par),0x80000000,ctypes.byref(ctx))
            if r != 0: raise ValueError(f'Failed to create decompression context ({r})')

            try:
                o = bytearray()
                bps = [20,32][(fl >> 22) & 3]
                zbs = 0x8000 << ((fl >> 4) & 3)
                segs = (fl >> 6) & 0xFFFF
                bdo = 0x10 + ((bps * segs + 31) >> 5) * 4
                msk = (1 << bps) - 1
                sbs = (bps + 7) >> 3

                biv = bic = 0
                tof = 0x10
                for ix in range(segs):
                    if bic < bps:
                        biv |= int.from_bytes(i[tof:tof+sbs],'big') << bic
                        bic += sbs * 8
                        tof += sbs
                    ubs,biv = biv & msk,biv >> bps
                    bic -= bps
                    if ix == 0:
                        do = bdo
                        bs = zbs - do
                    else: do,bs = ix * zbs,zbs
                    if ubs > 0 and do > len(i): raise EOFError
                    bs = min(len(i) - do,bs)
                    off = 0
                    while off < ubs:
                        ts = min(bs,ubs - off)
                        ob = (u8 * ts)()
                        ib = (u8 * bs).from_buffer_copy(i[do:do+bs])
                        ts = szt(ts) 
                        r = self.dll.XMemDecompressSegmentTD(ctx,ob,ctypes.byref(ts),ib,bs,ubs,off)
                        if r != 0 or ts.value == 0: raise ValueError(f'Failed to decompress segment ({r}, {ts.value}, {ix} @ {off}/{ubs})')
                        o.extend(bytes(ob)[:ts.value])
                        off += ts.value
                return bytes(o)
            except OSError: raise ValueError('Failed to decompress (OSError)')
            finally: self.dll.XMemDestroyDecompressionContext(ctx)
        elif i[3] == 0xEE:
            asrt(i[4] == 1 and i[5] <= 3,'Unsupported version',err=NotImplementedError)
            asrt(i[6] == i[7] == 0,'Non empty padding')
            par = XMemCodecParametersLZX(int.from_bytes(i[12:16],'big'),int.from_bytes(i[0x10:0x14],'big'),int.from_bytes(i[0x14:0x18],'big'))
            us,zs = int.from_bytes(i[0x18:0x20],'big'),int.from_bytes(i[0x20:0x28],'big')
            ctx = ctypes.c_void_p()
            r = self.dll.XMemCreateDecompressionContext(0,ctypes.byref(par),0,ctypes.byref(ctx))
            if r != 0: raise ValueError(f'Failed to create decompression context ({r})')

            try:
                p = 0x30
                rb = bytearray()
                while len(rb) < us and p < len(i):
                    bs = int.from_bytes(i[p:p+4],'big',signed=True);p += 4
                    if bs < 0: raise ValueError(f'Invalid block size {bs}')
                    elif (p + bs) > len(i): raise EOFError
                    ts = us - len(rb)
                    ib = (ctypes.c_uint8 * (bs + 0x10)).from_buffer_copy(i[p:p+bs] + bytes(0x10))
                    ob = (ctypes.c_uint8 * ts)()
                    ts = ctypes.c_size_t(ts)
                    r = self.dll.XMemDecompress(ctx,ob,ctypes.byref(ts),ib,bs + 0x10)
                    if r != 0 or ts.value == 0: raise ValueError(f'Failed to decompress block ({r}, {ts.value})')
                    rb.extend(bytes(ob)[:ts.value])
                    p += bs
                return bytes(rb)
            except OSError: raise ValueError('Failed to decompress (OSError)')
            finally: self.dll.XMemDestroyDecompressionContext(ctx)
        else: raise ValueError(f'Invalid XB mode {i[3]:02X}')
    def decompress_zip_shrink(self,src:bytes,usize:int) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_zip_shrink(i,len(src),o,usize)
        if r < 0: raise ValueError(f'Decompression failed ({r})')
        return bytes(o)
    def decompress_zip_reduce(self,src:bytes,usize:int,level:int) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_zip_reduce(i,len(src),o,usize,level)
        if r < 0: raise ValueError(f'Decompression failed ({r})')
        return bytes(o)
    def decompress_zip_implode(self,src:bytes,usize:int,flags:int=0) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_zip_implode(i,len(src),o,usize,flags)
        if r < 0: raise ValueError(f'Decompression failed ({r})')
        return bytes(o)
    def decompress_zstd(self,src:bytes,usize:int,zdict:bytes=None) -> bytes:
        i = (u8 * len(src)).from_buffer_copy(src)
        if zdict:
            dl = len(zdict)
            d = (u8 * dl).from_buffer_copy(zdict)
        else: dl,d = 0,None
        if usize == -1: o = P(u8)()
        else:
            o = (u8 * usize)()
            o = ctypes.cast(o,P(u8))
        r = self.dll.decompress_zstd(i,len(src),ctypes.byref(o),usize,d,dl)
        if r < 0: raise ValueError(f'Decompression failed: {ZSTDERR[-r]} ({-r})')
        od = ctypes.string_at(o,r)
        if usize == -1: self._free(o)
        return od
    def decompress_lzw(self,src:bytes,usize:int,max_bits:int,init_code_size:int,first_code:int,clear_code:int,end_code:int,be=False,max_dict:int=None):
        if max_dict is None or max_dict < 0: max_dict = 1 << max_bits
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * usize)()
        r = self.dll.decompress_lzw(i,len(src),o,usize,max_bits,max_dict,init_code_size,first_code,clear_code,end_code,1 if be else 0)
        if r < 0: raise ValueError(f'Decompression failed ({r})')
        return bytes(o)[:r]
    def decompress_hammer(self,src:bytes):
        asrt(len(src) > 8 and src[:3] == b'Hmr' and src[3] < 2)
        i = (u8 * len(src)).from_buffer_copy(src)
        o = (u8 * int.from_bytes(src[4:8],'little'))()
        r = self.dll.decompress_hammer(i,len(src),o)
        if r < 0: raise ValueError(f'Decompression failed ({r})')
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
    def decrypt_camelot_xor(self,src:bytes,key:int) -> bytes:
        if isinstance(key,bytes): key = key[0]
        b = (u8 * len(src)).from_buffer_copy(src)
        self.dll.decrypt_camelot_xor(b,len(src),key)
        return bytes(b)[:-1]
    def decrypt_camelot_rand(self,src:bytes,key:int,seed:int,drop:int=0) -> bytes:
        if isinstance(key,bytes): key = key[0]
        asrt(isinstance(seed,int) and isinstance(drop,int))
        b = (u8 * len(src)).from_buffer_copy(src)
        self.dll.decrypt_camelot_rand(b,len(src),key,seed,drop)
        return bytes(b)[:-1]
    def decrypt_zipd(self,src:bytes) -> bytes:
        asrt(src[-2:] == b'\x09\xEB')
        src = src[:-2]
        b = (u8 * len(src)).from_buffer_copy(src)
        r = self.dll.decrypt_zipd(b,len(src))
        if r != 0: raise ValueError(f'Decryption failed ({r})')
        return bytes(b)[7:]
    def decrypt_legaia2(self,src:bytes,key:int) -> bytes:
        asrt(not len(src) % 4 and src[:4] == b'\2\0\0\0')
        b = (u8 * len(src)).from_buffer_copy(src)
        self.dll.decrypt_legaia2(b,len(src),key)
        return bytes(b)[0x10:]

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
    def hash_tarzan(self,src:bytes) -> int: ...
    def hash_luas(self,src:bytes) -> int: ...
    def hash_empire_magic(self,src:bytes,end:bool=False) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_empire_magic(b,len(src),1 if end else 0)
    def hash_westwood(self,src:bytes) -> int:
        src += bytes(-len(src) % 4)
        b = (u32 * (len(src) // 4)).from_buffer_copy(src)
        return self.dll.hash_westwood(b,len(src) // 4)
    def hash_fnv1_64(self,src:bytes,seed:int=0xCBF29CE484222645,prime:int=0x100000001B3) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_fnv1_64(b,len(src),seed,prime)
    def hash_fnv1a_64(self,src:bytes,seed:int=0xCBF29CE484222645,prime:int=0x100000001B3) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_fnv1a_64(b,len(src),seed,prime)
    def hash_fnv1_32(self,src:bytes,seed:int=0x811C9DC5,prime:int=0x1000193) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_fnv1_32(b,len(src),seed,prime)
    def hash_fnv1a_32(self,src:bytes,seed:int=0x811C9DC5,prime:int=0x1000193) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_fnv1a_32(b,len(src),seed,prime)
    def hash_bkdr(self,src:bytes,init:int=0,seed:int=131) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_bkdr(b,len(src),init,seed)
    def hash_bkdr64(self,src:bytes,init:int=0,seed:int=131) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_bkdr64(b,len(src),init,seed)
    def hash_sdbm(self,src:bytes,init:int=0,seed:int=0x1003F) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_sdbm(b,len(src),init,seed)
    def hash_djb2(self,src:bytes,init:int=0x1505) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_djb2(b,len(src),init)
    def hash_djb2a(self,src:bytes,init:int=0x1505) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_djb2a(b,len(src),init)
    def hash_joaat(self,src:bytes,init:int=0) -> int:
        b = (u8 * len(src)).from_buffer_copy(src)
        return self.dll.hash_joaat(b,len(src),init)
    def mac_cmac_tfit(self,src:bytes,key:bytes,table:bytes) -> bytes:
        asrt(len(key) == 4*4*13 and len(table) == 4*0x100*0x10*13)
        s = (u8 * len(src)).from_buffer_copy(src)
        d = (u8 * 0x10)()
        k = (u8 * len(key)).from_buffer_copy(key)
        t = (u8 * len(table)).from_buffer_copy(table)
        self.dll.mac_cmac_tfit(s,len(src),d,k,t)
        return bytes(d)

    def hash_crc(self,src:bytes,size:int,poly:int,xor:int,reflect:bool,init:int,value:int=None) -> int:
        k = (size,poly,1 if reflect else 0)
        if not k in self.CRC:
            t = (u8 * 0x805)()
            if self.dll.hash_crc_init(t,*k) != 0:
                raise ValueError
            self.CRC[k] = t

        i = (u8 * len(src)).from_buffer_copy(src)
        r = self.dll.hash_crc(i,len(src),self.CRC[k],init,xor,value or 0,0 if value is None else 1)
        return r

    def _free(self,p): self.dll.free_exp(ctypes.cast(p,voidp))
