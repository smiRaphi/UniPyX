import struct,io,sys

ENDMAP = {'<':'little','>':'big','-':'big'}
UTFENDM = {'<':'le','>':'be','-':'be'}

def align(n:int,blocksize:int): return -n % blocksize
def swap32(i:bytes):
    c = len(i) // 4
    return struct.pack(f'>{c}I',*struct.unpack(f'<{c}I',i))
def mask(n:int): return (1 << n) - 1
def maskb(n:int): return mask(n * 8)
def reflecti(v:int,w:int):
    r = 0
    for _ in range(w):
        r = (r << 1) | (v & 1)
        v >>= 1
    return r
def rotate8(v:int): return ((v << 7) & maskb(1)) | (v >> 1)

class File:
    def __init__(self,f,mode='r',endian='>'):
        self.name = None
        if type(f) == str:
            self.name = f
            f = open(f,mode.rstrip('b') + 'b')
        elif type(f) == bytes: f = io.BytesIO(f)
        self._f = f
        self._end = endian

        self._start_pos = self._f.tell()
        self._size = self.seek(0,2)
        self.seek(0)

    def read(self,n:int=None) -> bytes: return self._f.read(n)
    def write(self,data:bytes) -> int: return self._f.write(data)
    def seek(self,n:int,whence=0) -> int:
        if n < 0 and whence in {0,2}:
            whence = 0
            n += self._size
        return self._f.seek(n + (self._start_pos if whence == 0 else 0),whence)
    def tell(self) -> int: return self._f.tell() - self._start_pos
    def close(self): self._f.close()

    def skip(self,n:int): return self.seek(n,1)
    def back(self,n:int): return self.skip(-n)
    def reads(self,n:int,encoding='utf-8'):
        if encoding == 'utf-16': return self.readutf16(n)
        return self.readc(n).decode(encoding)
    def readc(self,n:int=None):
        d = self.read(n)
        if n is not None and len(d) != n: raise EOFError(f"Unexpected EOF ({len(d)} != {n}) @ 0x{self.pos - len(d):08X} - 0x{self.pos - len(d) + n:08X}")
        return d
    def padc(self,n:int): 
        if sum(self.readc(n)): raise ValueError(f"Unexpected Value in padding @ 0x{self.pos - n:08X} - 0x{self.pos:08X}")
    def readu(self,c=b'\0',max=None,chks=0x100):
        o = bytearray()
        while max is None or len(o) < max:
            d = self.read(chks)
            p = d.find(c)
            if p != -1 or len(d) != chks:
                o += d[:p]
                self.back(len(d) - p - 1)
                break
            o += d
        return bytes(o)

    def middle_scramble(self,d:bytes):
        o = bytearray()
        for i in range(len(d)//2):
            o.append(d[i*2+1])
            o.append(d[i*2])
        if len(d) % 2: o.append(d[-1])
        return bytes(o)
    def unpacki(self,n:int,signed=False,end=None):
        d = self.readc(n)
        end = end or self._end
        if end == '-': d = self.middle_scramble(d)
        return int.from_bytes(d,ENDMAP[end],signed=bool(signed))
    def unpack(self,fmt:str,end=None):
        d = self.readc(struct.calcsize(fmt))
        end = end or self._end
        if end == '-':
            d = self.middle_scramble(d)
            end = '>'
        return struct.unpack(end + fmt,d)[0]
    def packi(self,i:int,n:int,signed=False,end=None):
        d = i.to_bytes(n,ENDMAP[end or self._end],signed=bool(signed))
        if end == '-': d = self.middle_scramble(d)
        return self.write(d)

    def readu8 (self)         : return self.unpacki(1,0)
    def readu16(self,end=None): return self.unpacki(2,0,end)
    def readu24(self,end=None): return self.unpacki(3,0,end)
    def readu32(self,end=None): return self.unpacki(4,0,end)
    def readu40(self,end=None): return self.unpacki(5,0,end)
    def readu48(self,end=None): return self.unpacki(6,0,end)
    def readu64(self,end=None): return self.unpacki(8,0,end)
    def readu128(self,end=None):return self.unpacki(16,0,end)
    def reads8 (self)         : return self.unpacki(1,1)
    def reads16(self,end=None): return self.unpacki(2,1,end)
    def reads24(self,end=None): return self.unpacki(3,1,end)
    def reads32(self,end=None): return self.unpacki(4,1,end)
    def reads40(self,end=None): return self.unpacki(5,1,end)
    def reads48(self,end=None): return self.unpacki(6,1,end)
    def reads64(self,end=None): return self.unpacki(8,1,end)
    def reads128(self,end=None):return self.unpacki(16,1,end)
    def readf32(self,end=None):
        v = self.unpack('f',end)
        return float(f'{v:.7g}') # clamp precision to that of a float32
    def readf64(self,end=None) -> float: return self.unpack('d',end)
    def readleb128u(self):
        n = c = b = 0
        while True:
            b = self.readu8()
            n |= (b & mask(7)) << (c * 7)
            if not b & 0x80: return n
            c += 1
    def readvlq(self):
        n = b = 0
        while True:
            b = self.readu8()
            n = (n << 7) | (b & mask(7))
            if not b & 0x80: return n
    def readcompiu(self,null=False):
        b = self.readu8()
        if b == 0xFF and null: return None
        h = b >> 5
        if   h & 0b100 == 0b000: b =  b & mask(7)
        elif h & 0b110 == 0b100: b = (b & mask(6)) << 8 | self.readu8()
        elif h & 0b111 == 0b110: b = (b & mask(5)) << 24 | self.readu24('>')
        else: raise ValueError(f"Invalid compressed integer size (0b{h:03b} {b & mask(5):05b})")
        return b
    def readcompis(self,null=False):
        v = self.readcompiu(null)
        if v is None: return v
        if v & 1: return -(v >> 1) - 1
        return v >> 1

    def read0s(self,encoding:str=None) -> bytes|str:
        r = self.readu()
        if encoding is not None: r = r.decode(encoding)
        return r
    def readutf16(self,l:int): return self.readc(l * 2).decode('utf-16' + UTFENDM[self._end])

    def writeu8 (self,v:int): return self.packi(v,1,0)
    def writeu16(self,v:int,end=None): return self.packi(v,2,0,end)
    def writeu32(self,v:int,end=None): return self.packi(v,4,0,end)
    def writeu40(self,v:int,end=None): return self.packi(v,5,0,end)
    def writeu48(self,v:int,end=None): return self.packi(v,6,0,end)
    def writeu64(self,v:int,end=None): return self.packi(v,8,0,end)
    def writeu128(self,v:int,end=None):return self.packi(v,16,0,end)
    def writes8 (self,v:int): return self.packi(v,1,1)
    def writes16(self,v:int,end=None): return self.packi(v,2,1,end)
    def writes32(self,v:int,end=None): return self.packi(v,4,1,end)
    def writes40(self,v:int,end=None): return self.packi(v,5,1,end)
    def writes48(self,v:int,end=None): return self.packi(v,6,1,end)
    def writes64(self,v:int,end=None): return self.packi(v,8,1,end)
    def writes128(self,v:int,end=None):return self.packi(v,16,1,end)
    def writef32(self,v:float,end=None): return self.write(struct.pack((end or self._end)+'f',v))
    def writef64(self,v:float,end=None): return self.write(struct.pack((end or self._end)+'d',v))
    def writevlq(self,v:int):
        b = [v & mask(7)]
        v >>= 7

        while v > 0:
            b.append((v & mask(7)) | 0x80)
            v >>= 7

        return self.write(bytes(reversed(b)))

    def align(self,blocksize:int,base:int=0):
        v = align(self.tell() - base,blocksize)
        self.skip(v)
        return v

    def add_file(self,f):
        if type(f) == str: f = open(f,'rb')
        while True:
            p = f.read(0x4000)
            if not p: break
            self.write(p)

    def decompress(self,size:int,algo:str,*args,**kwargs): return decompress(self.readc(size),algo,*args,**kwargs)

    @property
    def pos(self): return self.tell()
    @property
    def size(self):
        p = self.pos
        r = self.seek(0,2)
        self.seek(p)
        return r

    def update_size(self): self._size = self.tell()
    def __len__(self): return self._size
    def __bool__(self): return self.pos < self.size
class BitReader:
    def __init__(self,d:bytes):
        self.d = d
        self.p = 0
        self.b = 0
        self.m = 0

    def get_bit(self):
        if not self.m:
            if self.p >= len(self.d): return None
            self.b = self.d[self.p]
            self.p += 1
            self.m = 0x80
        bit = 1 if self.b & self.m else 0
        self.m >>= 1
        return bit
    def get_bits(self,n,ret_none=False) -> int|None:
        v = 0
        for i in range(n):
            b = self.get_bit()
            if b is None:
                if ret_none: return None
                break
            v |= b << (n - 1 - i)
        return v
    def reset(self): self.m = 0
    @property
    def eof(self): return self.p >= len(self.d) and not self.m

class EXE(File):
    def __init__(self,f):
        super().__init__(f,mode='r',endian='<')

        assert self.read(2) == b'MZ'
        self.seek(0x3C)
        self.coff_off = self.readu32()
        self.seek(self.coff_off)
        self.secs = {}
        pe = self.read(4)
        if pe == b'PE\0\0':
            self.skip(2)
            secs = self.readu16()
            self.skip(12)
            self.skip(self.readu16() + 2)

            for _ in range(secs):
                n = self.read(8).strip(b'\0').decode(errors='ignore')
                self.skip(8)
                s,o = self.readu32(),self.readu32()
                self.secs[n] = (o,s,o+s)
                self.skip(0x10)
        elif pe[:2] == b'NE':
            self.skip(0x18)
            secs = self.readu16()
            self.skip(4)
            seco = self.readu16()
            self.reco = self.readu16()
            blcks = 1 << self.readu16()
            self.skip(12)
            self.recs = self.readu16()

            self.seek(self.coff_off + seco)
            for x in range(secs):
                s,o = self.readu16()*blcks,self.readu16()
                self.secs[x] = (o,s,o+s)
                self.skip(4)
        else: raise NotImplementedError(pe)

        self.ovl_off = max([x[2] for x in self.secs.values()])
def ext_exe(i:str,dotnet=False):
    if dotnet:
        import dnfile
        return dnfile.dnPE(i)
    else:
        import pefile
        r = pefile.PE(i)
        r.SECTIONS = {s.Name.rstrip(b'\0').decode(errors='ignore'):s for s in r.sections}
        return r

OODLE = None
GDEFLATE = None
UCL = None
def decompress(i:bytes,algo:str,**kwargs) -> bytes:
    global OODLE,GDEFLATE,UCL
    match algo:
        case 'none': return i
        case 'zlib':
            import zlib
            return zlib.decompress(i,wbits=kwargs.get('wbits',15))
        case 'deflate':
            import zlib
            return zlib.decompress(i,wbits=-15)
        case 'gzip':
            import gzip
            return gzip.decompress(i)
        case 'bz2'|'bzip2':
            import bz2
            return bz2.decompress(i)
        case 'zip':
            import io
            from zipfile import ZipFile
            z = ZipFile(io.BytesIO(i))

            om = kwargs.get('out',kwargs.get('o'))
            if type(om) == int and om == 1:
                assert len(z.namelist()) == 1
                r = z.read(z.namelist()[0])
            elif type(om) == str:
                z.extractall(om)
                r = z.namelist()
            else: r = {n:z.read(n) for n in z.namelist()}
            z.close()
            return r

        case 'lzma'|'lzma_alone':
            import lzma
            if kwargs.get('null_usize'): i = i[:5] + b'\xFF'*8 + i[13:]
            elif kwargs.get('usize') is not None: i = i[:5] + kwargs['usize'].to_bytes(8,'little') + i[13:]
            return lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(i)
        case 'lzma_us32'|'lzma_alone_us32': return decompress(i[:9] + b'\0'*4 + i[9:],'lzma_alone',*args,**kwargs)
        case 'xz':
            import lzma
            return lzma.LZMADecompressor(format=lzma.FORMAT_XZ).decompress(i)
        case 'msf':
            import lzma
            return lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=[{'id':lzma.FILTER_LZMA1,'dict_size':0x1000000,'lc':3,'lp':0,'pb':2}]).decompress(i)[:kwargs.get('usize')]
        case 'zstd':
            if sys.version_info >= (3,14): from compression import zstd # type: ignore
            else:
                try: import backports_zstd as zstd # type: ignore
                except: from backports import zstd # type: ignore
            if 'zstd_dict' in kwargs and type(kwargs['zstd_dict']) == bytes: kwargs['zstd_dict'] = zstd.ZstdDict(kwargs['zstd_dict'])
            return zstd.decompress(i,kwargs.get('zstd_dict'))
        case 'lz4'|'lz4_block':
            import lz4.block
            return lz4.block.decompress(i,uncompressed_size=(len(i) * 8) if kwargs.get('no_size') else kwargs['usize'])
        case 'lz4_frame':
            import lz4.frame
            return lz4.frame.decompress(i)
        case 'lz4_fast': return lz4_fast_decompress(i,usize=kwargs['usize'])

        case 'lzo'|'lzo1x'|'lzo1y':
            if 'db' in kwargs: kwargs['db'].get('lzo')
            if algo == 'lzo': algo = 'lzo1x'

            import bin.lzo # type: ignore
            return bin.lzo.decompress(i,False,kwargs['usize'],algorithm=algo.upper())
        case 'implode':
            if 'db' in kwargs: kwargs['db'].get('pwexplode')
            import bin.pwexplode # type: ignore
            return bin.pwexplode.explode(i)
        case 'ucl_nrv2b'|'ucl_nrv2b_8'|'ucl_nrv2b_16'|'ucl_nrv2b_32'|\
             'ucl_nrv2d'|'ucl_nrv2d_8'|'ucl_nrv2d_16'|'ucl_nrv2d_32'|\
             'ucl_nrv2e'|'ucl_nrv2e_8'|'ucl_nrv2e_16'|'ucl_nrv2e_32':
                assert 'usize' in kwargs and (UCL or kwargs.get('db'))
                UCLERR = {-ix:x for ix,x in enumerate(('OK','ERROR','OUT_OF_MEMORY','NOT_COMPRESSIBLE','INPUT_OVERRUN','OUTPUT_OVERRUN','LOOKBEHIND_OVERRUN','EOF_NOT_FOUND','INPUT_NOT_CONSUMED'))}

                if algo in {'ucl_nrv2b','ucl_nrv2d','ucl_nrv2e'}: algo += '_8'
                import ctypes
                if not UCL:
                    UCL = ctypes.CDLL(kwargs['db'].get('ucl'))
                    UCL.InitUCL.argtypes = []
                    UCL.InitUCL.restype = ctypes.c_int

                    for a in 'BDE':
                        for f in ('','_Safe'):
                            for s in ('8','LE16','LE32'):
                                fn = getattr(UCL,f'DecompressNRV2{a}{f}_{s}')
                                fn.argtypes = [ctypes.POINTER(ctypes.c_ubyte),ctypes.c_uint,ctypes.POINTER(ctypes.c_ubyte),ctypes.POINTER(ctypes.c_uint)]
                                fn.restype = ctypes.c_int

                    r = UCL.InitUCL()
                    if r != 0: raise ValueError(UCLERR[r])
                bs = int(algo.split('_')[-1])
                fn = getattr(UCL,'DecompressNRV2' + algo[8].upper() + ('_Safe' if kwargs.get('safe') else '') + '_' + (f'LE{bs}' if bs > 8 else '8'))

                src_len,dst_len = len(i),ctypes.c_uint(kwargs['usize'])
                src = (ctypes.c_ubyte * src_len).from_buffer_copy(i)
                dst = (ctypes.c_ubyte * kwargs['usize'])()
                r = fn(ctypes.cast(src,ctypes.POINTER(ctypes.c_ubyte)),src_len,ctypes.cast(dst,ctypes.POINTER(ctypes.c_ubyte)),ctypes.byref(dst_len))
                if r != 0: raise ValueError(UCLERR[r])
                return bytes(dst[:dst_len.value])
        case 'uclpack'|'uclpack_itc':
            itc = algo == 'uclpack_itc'
            safe = bool(kwargs.get('safe',True))

            if i[:8] != b'\x00\xE9UCL\xFF\x01\x1A': raise ValueError('invalid uclpack header')
            dcrc = int.from_bytes(i[8:12],'big') & 1 and safe
            crc = 1
            mth = i[12]
            if not mth in {0x2B,0x2D,0x2E}: raise ValueError(f'invalid uclpack method (0x{mth:02X})')
            mth = f'{mth:02x}'
            lvl = i[13]
            if 10 < lvl < 1: raise ValueError(f'invalid uclpack level ({lvl})')
            blks = int.from_bytes(i[14:18],'big')
            if (not itc) and (0x800000 < blks or blks < 0x400): raise ValueError(f'invalid uclpack block size ({blks})')

            p = 0x12
            ics = len(i)
            o = bytearray()
            while p < ics:
                us = int.from_bytes(i[p:p+4],'big');p += 4
                if us == 0: break
                if us > blks: raise ValueError(f'uncompressed block size ({us}) is larger than block size ({blks})')
                zs = int.from_bytes(i[p:p+4],'big');p += 4
                if zs > blks: raise ValueError(f'compressed block size ({zs}) is larger than block size ({blks})')
                if zs > us: raise ValueError(f'compressed block size ({zs}) is larger than uncompressed block size ({us})')
                if zs == 0: raise ValueError(f'compressed block size ({zs}) is zero')

                cd = i[p:p+zs];p += zs
                if len(cd) != zs: raise EOFError(f'unexpected EOF (by {zs - len(cd)})')
                if zs == us: d = cd
                else:
                    d = decompress(cd,f'ucl_nrv{mth}_{32 if itc else 8}',usize=us,safe=safe,db=kwargs.get('db'))
                    if len(d) != us: raise ValueError(f'actual decompressed block size ({len(d)}) is not equal to expected size ({us})')
                o.extend(d)
                if dcrc: crc = crc_hash(d,'adler32',init=crc)
                if len(cd) != zs: break

            if dcrc and crc != int.from_bytes(i[p:p+4],'big'): raise ValueError('CRC mismatch')
            return bytes(o)

        case 'huffman': return huffman_decompress(i,usize=kwargs['usize'],padding=kwargs.get('padding',False))
        case 'lzss': return lzss_decompress(i,usize=kwargs['usize'])
        case 'lzss8': return lzss8_decompress(i,usize=kwargs['usize'])
        case 'lzss16': return lzss16_decompress(i,usize=kwargs['usize'],big_endian=kwargs.get('big_endian',True))
        case 'lzw_lg':
            if algo == 'lzw_lg': args = {'bit_width':14,'reset':0x3FFE,'eof':0x3FFF,'max_dict':0x3FFE}
            return lzw_decompress(i,**args)
        case 'avlz':
            if len(i) < 8: raise ValueError("Not enough data to decompress")
            cs = int.from_bytes(i[:4],'little')
            us = int.from_bytes(i[4:8],'little')

            if cs == len(i): cs -= 8
            if cs != len(i) - 8: raise ValueError("Invalid compressed size")
            return lzss8_decompress(i[8:8+cs],usize=us)
        case 'rtl_lz': return rtl_lz_decompress(i,usize=kwargs.get('usize'))

        case 'mio0'|'yay0'|'yaz0'|'vpk0':
            import crunch64
            return getattr(crunch64,algo).decompress(i)
        case 'ash0': return ash0_decompress(i)

        case 'oodle'|'oodle_kraken'|'oodle_leviathan':
            assert 'usize' in kwargs and (OODLE or kwargs.get('db'))
            import ctypes
            if not OODLE:
                from ctypes import c_void_p,c_int,c_ssize_t,CFUNCTYPE
                OODLE = ctypes.CDLL(kwargs['db'].get('noodle'))
                OODLE.OodleLZ_Decompress.argtypes = [
                    c_void_p,c_ssize_t,c_void_p,c_ssize_t,c_int,c_int,c_int,c_void_p,c_ssize_t,c_void_p#CFUNCTYPE(None,c_void_p,c_void_p,c_ssize_t)
                   ,c_void_p,c_void_p,c_ssize_t,c_int
                ]
                OODLE.OodleLZ_Decompress.restype = c_ssize_t

            o = ctypes.create_string_buffer(kwargs['usize'])
            r = OODLE.OodleLZ_Decompress(i,len(i),o,kwargs['usize'],0 if algo in () else 1,0,0,None,0,None,None,None,0,0)
            if r == 0: raise Exception('Failed to decompress')
            return o.raw[:r]
        case 'gdeflate':
            assert GDEFLATE or kwargs.get('db')
            import ctypes
            if not GDEFLATE:
                GDEFLATE = ctypes.CDLL(kwargs['db'].get('gdeflate'))

                GDEFLATE.DecompressData.argtypes = [ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t]
                GDEFLATE.DecompressData.restype = ctypes.c_int

            assert i[:2] == b'\x04\xFB'
            isz = len(i)
            bcc = int.from_bytes(i[2:4],'little')
            if not bcc: raise ValueError('Empty block count')

            flgs = int.from_bytes(i[4:7],'little')
            if flgs & mask(2) != 1: raise ValueError(f'Invalid Tile Size Index ({flgs & mask(2)})')
            us = bcc * 0x10000 + ((flgs >> 2) & mask(18))

            ibuf = (ctypes.c_uint8 * isz).from_buffer_copy(i)
            obuf = (ctypes.c_uint8 * us)()

            r = GDEFLATE.DecompressData(ibuf,isz,obuf,us)
            if r == 0: raise ValueError('Failed to decompress')
            return bytes(obuf)
        case 'anaconda_deflate': return ananconda_decompress(i)
        case 'anaconda_zlib':
            if i[1] & 0x20: i = i[6:]
            else: i = i[2:]
            return ananconda_decompress(i)
    raise NotImplementedError(algo)
CRC8 = {   #  poly,init,xor ,reflect
 'tech_3250':(0x1D,0xFF,0x00,True ),
    'gsm':   (0x1D,0x00,0x00,False),'gsm_a':(0x1D,0,0,False),
'mifare_mad':(0x1D,0xC7,0x00,False),
    'icode': (0x1D,0xFD,0x00,False),
    'hitag': (0x1D,0xFF,0x00,False),
    'j1850': (0x1D,0xFF,0xFF,False),'sae_j1850':(0x1D,0xFF,0xFF,False),
    'rohc':  (0x07,0xFF,0x00,True ),
    'smbus': (0x07,0x00,0x00,False),'atm':(0x07,0,0,False), # default
    'itu':   (0x07,0x00,0x55,False),'i432_1':(0x07,0,0x55,False),
    'wcdma': (0x9B,0x00,0x00,True ),
    'lte':   (0x9B,0x00,0x00,False),
  'cdma2000':(0x9B,0xFF,0x00,False),
    'maxim': (0x31,0x00,0x00,True ),'maxim_dow':(0x31,0,0,True),
    'nrsc5': (0x31,0xFF,0x00,False),
'opensafety':(0x2F,0x00,0x00,False),
   'autosar':(0x2F,0xFF,0xFF,False),
    'darc':  (0x39,0x00,0x00,True ),
    'gsm_b': (0x49,0x00,0xFF,False),
    'ccitt': (0x8D,0x00,0x00,False),
 'bluetooth':(0xA7,0x00,0x00,True ),
    'dvb_s2':(0xD5,0x00,0x00,False),
}
CRC16 = {   # poly  , init , xor  , reflect
    'ansi':  (0x8005,0x0000,0x0000,True ),'ibm':(0x8005,0,0,True),'arc':(0x8005,0,0,True),'lha':(0x8005,0,0,True), # default
    'maxim': (0x8005,0x0000,0xFFFF,True ),'maxim_dow':(0x8005,0,0xFFFF,True),
    'modbus':(0x8005,0xFFFF,0x0000,True ),
    'usb':   (0x8005,0xFFFF,0xFFFF,True ),
    'umts':  (0x8005,0x0000,0x0000,False),'buypass':(0x8005,0,0,False),'verifone':(0x8005,0,0,False),
   'dds_110':(0x8005,0x800D,0x0000,False),
    'cms':   (0x8005,0xFFFF,0x0000,False),
    'kermit':(0x1021,0x0000,0x0000,True ),'ccitt':(0x1021,0,0,True),'ccitt_true':(0x1021,0,0,True),
  'tms37157':(0x1021,0x89EC,0x0000,True ),
    'riello':(0x1021,0xB2AA,0x0000,True ),
'iso_iec_14443_3_a':(0x1021,0xC6C6,0,True),
   'mcrf4xx':(0x1021,0xFFFF,0x0000,True ),
    'x25':   (0x1021,0xFFFF,0xFFFF,True ),'ibm_sdlc':(0x1021,0xFFFF,0xFFFF,True),'iso_hdlc':(0x1021,0xFFFF,0xFFFF,True),
    'xmodem':(0x1021,0x0000,0x0000,False),'zmodem':(0x1021,0,0,False),'acorn':(0x1021,0,0,False),
    'gsm':   (0x1021,0x0000,0xFFFF,False),
'spi_fujitsu':(0x1021,0x1D0F,0x000,False),'aug_ccitt':(0x1021,0x1D0F,0,False),
'ccitt_false':(0x1021,0xFFFF,0x000,False),'ibm_3740':(0x1021,0xFFFF,0,False),
   'genibus':(0x1021,0xFFFF,0xFFFF,False),'icode':(0x1021,0xFFFF,0xFFFF,False),'darc':(0x1021,0xFFFF,0xFFFF,False),'epc':(0x1021,0xFFFF,0xFFFF,False),
'opensafety':(0x5935,0x0000,0x0000,False),'opensafety_a':(0x5935,0,0,False),
    'm17':   (0x5935,0xFFFF,0x0000,False),
    'dnp':   (0x3D65,0x0000,0xFFFF,True ),
   'en13757':(0x3D65,0x0000,0xFFFF,False),
    'dect_r':(0x0589,0x0000,0x0001,False),
    'dect_x':(0x0589,0x0000,0x0000,False),
'opensafety_b':(0x755B,0x00,0x0000,False),
  'teledisk':(0xA097,0x0000,0x0000,False),
   't10_dif':(0x8BB7,0x0000,0x0000,False),
  'profibus':(0x1DCF,0xFFFF,0xFFFF,False),
    'nrsc5': (0x080B,0xFFFF,0x0000,True ),
    'lj1200':(0x6F63,0x0000,0x0000,False),
  'cdma2000':(0xC867,0xFFFF,0x0000,False),
}
CRC24 = {   # poly    , init   , xor    , reflect
    'lte':   (0x864CFB,0x000000,0x000000,False),'lte_a':(0x864CFB,0,0,False),
   'openpgp':(0x864CFB,0xB704CE,0x000000,False), # default
   'flexray':(0x5D6DCB,0xFEDCBA,0x000000,False),'flexray_a':(0x5D6DCB,0xFEDCBA,0,False),
 'flexray_b':(0x5D6DCB,0xABCDEF,0x000000,False),
    'lte_b': (0x800063,0x000000,0x000000,False),
    'os9':   (0x800063,0xFFFFFF,0xFFFFFF,False),
    'ble':   (0x00065B,0x555555,0x000000,True ),
'interlaken':(0x328B63,0xFFFFFF,0xFFFFFF,False),
}
CRC32 = {   # poly      , init     , xor      , reflect
    'jamcrc':(0x04C11DB7,0xFFFFFFFF,0x00000000,True ),
    'ieee':  (0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True ),'iso':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True),'iso_hdlc':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True), # default
    'adccp': (0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True ),'pkzip':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True),'xz':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True),'v42':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True), # default
    'mpeg2': (0x04C11DB7,0xFFFFFFFF,0x00000000,False),
    'posix': (0x04C11DB7,0x00000000,0xFFFFFFFF,False),'cksum':(0x04C11DB7,0,0xFFFFFFFF,False),
    'bzip2': (0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),'aal5':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),'dect_b':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),'b':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),
    'mef':   (0x741B8CD7,0xFFFFFFFF,0x00000000,True ),
    'k':     (0x741B8CD7,0xFFFFFFFF,0xFFFFFFFF,True ),'koopman':(0x741B8CD7,0xFFFFFFFF,0xFFFFFFFF,True),
    'xfer':  (0x000000AF,0x00000000,0x00000000,False),
   'autosar':(0xF4ACFB13,0xFFFFFFFF,0xFFFFFFFF,True ),
    'c':     (0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True ),'castagnoli':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),'iscsi':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),'base91_c':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),
'intrelaken':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True ),'nvme':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),
    'd':     (0xA833982B,0xFFFFFFFF,0xFFFFFFFF,True ),'base94':(0xA833982B,0xFFFFFFFF,0xFFFFFFFF,True),'base94_d':(0xA833982B,0xFFFFFFFF,0xFFFFFFFF,True),
    'q':     (0x814141AB,0x00000000,0x00000000,False),'aixm':(0x814141AB,0,0,False),
'cd_rom_edc':(0x8001801B,0x00000000,0x00000000,True ),
}
CRC64 = {   # poly              , init             , xor              , reflect
    'xz':    (0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True ),'go_ecma':(0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True),
    'ecma':  (0x42F0E1EBA9EA3693,0x0000000000000000,0x0000000000000000,False),'ecma_182':(0x42F0E1EBA9EA3693,0,0,False), # default
    'we':    (0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,False),
    'redis': (0xAD93D23594C935A9,0x0000000000000000,0x0000000000000000,True ),
    'jones': (0xAD93D23594C935A9,0xFFFFFFFFFFFFFFFF,0x0000000000000000,True ),
    'ms':    (0x259C84CBA6426349,0xFFFFFFFFFFFFFFFF,0x0000000000000000,True ),
    'go_iso':(0x000000000000001B,0x0000000000000000,0x0000000000000000,True ),
    'nvme':  (0xAD93D23594C93659,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True ),
}
def crc_hash(i:bytes,algo:str,**kwargs) -> int:
    match algo:
        case 'crc8': fnc = crc8
        case 'crc16': fnc = crc16
        case 'crc24': fnc = crc24
        case 'crc32'|'crc32_ieee'|'crc32_iso'|'crc32_iso_hdlc'|'crc32_adccp'|'crc32_pkzip':
            import zlib
            fnc = zlib.crc32
        case 'crc64': fnc = crc64
        case 'crc8_tech_3250'|'crc8_gsm'|'crc8_gsm_a'|'crc8_mifare_mad'|'crc8_icode'|'crc8_hitag'|\
             'crc8_j1850'|'crc8_sae_j1850'|'crc8_rohc'|'crc8_smbus'|'crc8_atm'|'crc8_itu'|'crc8_i432_1'|\
             'crc8_wcdma'|'crc8_lte'|'crc8_cdma2000'|'crc8_maxim'|'crc8_maxim_dow'|'crc8_nrsc5'|\
             'crc8_opensafety'|'crc8_autosar'|'crc8_darc'|'crc8_gsm_b'|'crc8_ccitt'|'crc8_bluetooth'|\
             'crc8_dvb_s2':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC8[algo[5:]]
            fnc = crc8
        case 'crc16_ansi'|'crc16_ibm'|'crc16_arc'|'crc16_lha'|'crc16_maxim'|'crc16_maxim_dow'|'crc16_modbus'|\
             'crc16_usb'|'crc16_umts'|'crc16_buypass'|'crc16_verifone'|'crc16_dds_110'|'crc16_cms'|'crc16_kermit'|\
             'crc16_ccitt'|'crc16_ccitt_true'|'crc16_tms37157'|'crc16_riello'|'crc16_iso_iec_14443_3_a'|\
             'crc16_mcrf4xx'|'crc16_x25'|'crc16_ibm_sdlc'|'crc16_iso_hdlc'|'crc16_xmodem'|'crc16_zmodem'|'crc16_acorn'|\
             'crc16_gsm'|'crc16_spi_fujitsu'|'crc16_aug_ccitt'|'crc16_ccitt_false'|'crc16_ibm_3740'|'crc16_genibus'|\
             'crc16_icode'|'crc16_darc'|'crc16_opensafety'|'crc16_opensafety_a'|'crc16_m17'|'crc16_dnp'|'crc16_en13757'|\
             'crc16_dect_r'|'crc16_dect_x'|'crc16_opensafety_b'|'crc16_teledisk'|'crc16_t10_dif'|'crc16_profibus'|\
             'crc16_nrsc5'|'crc16_lj1200'|'crc16_cdma2000'|'crc16_epc':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC16[algo[6:]]
            fnc = crc16
        case 'crc24_lte'|'crc24_lte_a'|'crc24_openpgp'|'crc24_flexray'|'crc24_flexray_a'|'crc24_flexray_b'|\
             'crc24_lte_b'|'crc24_os9'|'crc24_ble'|'crc24_interlaken':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC24[algo[6:]]
            fnc = crc24
        case 'crc32_jamcrc'|'crc32_ieee'|'crc32_iso'|'crc32_iso_hdlc'|'crc32_adccp'|'crc32_pkzip'|'crc32_xz'|'crc32_v42'|\
             'crc32_mpeg2'|'crc32_posix'|'crc32_cksum'|'crc32_bzip2'|'crc32_aal5'|'crc32_dect_b'|'crc32_b'|'crc32_mef'|\
             'crc32_k'|'crc32_koopman'|'crc32_xfer'|'crc32_autosar'|'crc32_c'|'crc32_castagnoli'|'crc32_iscsi'|\
             'crc32_base91_c'|'crc32_intrelaken'|'crc32_nvme'|'crc32_d'|'crc32_base94'|'crc32_base94_d'|'crc32_q'|\
             'crc32_aixm'|'crc32_cd_rom_edc':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC32[algo[5:].lstrip('_')]
            fnc = crc32
        case 'crc64_xz'|'crc64_go_ecma'|'crc64_ecma'|'crc64_ecma_182'|'crc64_we'|'crc64_redis'|'crc64_jones'|'crc64_ms'|\
             'crc64_go_iso'|'crc64_nvme':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC64[algo[6:]]
            fnc = crc64

        case 'crc40_gsm':
            kwargs['size'] = 40
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = {
                'gsm':(0x0004820009,0x0000000000,0x0000000000,False)
            }[algo[6:]]
            fnc = crc

        case 'adler32':
            import zlib
            if 'init' in kwargs: kwargs['value'] = kwargs.pop('init')
            fnc = zlib.adler32
        case 'fnv1_32': fnc = fnv1_32
        case 'fnv1a_32': fnc = fnv1a_32
        case 'fnv1_64': fnc = fnv1_64
        case 'fnv1a_64': fnc = fnv1a_64
        case 'bkdr'|'bkdr_ltr': fnc = bkdr
        case 'bkdr_rtl':
            i = i[::-1]
            fnc = bkdr
        case 'sdbm'|'sdbm_ltr': fnc = sdbm
        case 'sdbm_rtl':
            i = i[::-1]
            fnc = sdbm
        case 'murmur3'|'mmh3'|'murmur3_32'|'mmh3_32'|'murmur3_128'|'mmh3_128':
            import mmh3
            kwargs['seed'] = kwargs.get('seed',0) & maskb(4)
            fnc = getattr(mmh3,f'mmh3_{"x64_128" if "128" in algo else "32"}_uintdigest')
        case 'xxh32'|'xxh64'|'xxh3_64'|'xxh128'|'xxh3_128':
            if algo == 'xxh128': algo = 'xxh3_128'
            import xxhash
            fnc = getattr(xxhash,algo + '_' + ('' if kwargs.pop('bytes',False) else 'int') + 'digest')

        case 'sha1'|'sha224'|'sha256'|'sha384'|'sha512'|'sha3_224'|'sha3_256'|'sha3_384'|'sha3_512'|'sha512_224'|'sha512_256'|\
             'blake2b'|'blake2s'|'md5'|'shake128'|'shake_128'|'shake256'|'shake_256'|'ripemd160'|'sm3':
            if algo in {'shake128','shake256'}: algo = algo[:5] + '_' + algo[5:]
            oby = kwargs.pop('bytes',False)
            kw = {}
            if algo in {'shake_128','shake_256'}: kw['length'] = kwargs.pop('digest_size',int(algo[6:]) // 8)

            import hashlib
            r = hashlib.new(algo,i,**kwargs).digest(**kw)
            if oby: return r
            return int.from_bytes(r,'big')
        case 'md5_sha1':
            import hashlib
            r = hashlib.md5(i).digest() + hashlib.sha1(i).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')

        case 'tarzan': fnc = tarzan_hash
        case 'luas': fnc = luas_hash
        case 'sxm': fnc = sxm_hash
        case 'hash40':
            import zlib
            return (len(i) << 32) | zlib.crc32(i,value=kwargs.get('value') or 0)
        case _: raise NotImplementedError(algo)
    return fnc(i,**kwargs)
MMFS_DEC = {}
def decrypt(i:bytes,algo:str,key:bytes=None,iv:bytes=None,**kwargs) -> bytes:
    match algo:
        case 'xor':
            if type(key) == int: key = (key,)
            return bytes(i[x] ^ key[x % len(key)] for x in range(len(i)))
        case 'rxor':
            if type(key) == bytes: key = key[0]
            d = bytearray(i)
            for ix in range(len(i)): key = d[ix] = d[ix] ^ key
            return bytes(d)
        case 'dxor': return bytes(i[x] ^ key[x % len(key)] ^ iv[x % len(iv)] for x in range(len(i)))
        case 'inv'|'invert': return bytes(x ^ 0xFF for x in i)
        case 'roll':
            if type(key) == int: key = (key,)
            return bytes((i[x] - key[x % len(key)]) & 0xFF for x in range(len(i)))
        case 'rolr':
            if type(key) == int: key = (key,)
            return bytes((i[x] + key[x % len(key)]) & 0xFF for x in range(len(i)))

        case 'aes'|'aes_cbc'|'aes_ecb'|'aes_gcm':
            from Cryptodome.Cipher import AES
            m = algo[4:] or 'cbc'

            kw = kwargs
            if m in {'ccm','eax','gcm','siv','ocb','ctr'}: kw['nonce'] = iv
            elif m in {'cbc','cfb','ofb','openpgp'}: kw['iv'] = iv
            obj = AES.new(key,mode=getattr(AES,f'MODE_{m.upper()}'),**kw)
            if i is None: return obj

            return obj.decrypt(i)
        case 'blowfish'|'blowfish_ecb'|'blowfish_cbc':
            from Cryptodome.Cipher import Blowfish
            m = algo[9:] or 'ecb'

            kw = kwargs
            if m in {'cbc','cfb','ofb','openpgp'}: kw['iv'] = iv
            elif m in {'eax','ctr'}: kw['nonce'] = iv

            return Blowfish.new(key,getattr(Blowfish,f'MODE_{m.upper()}'),**kw).decrypt(i)
        case 'blowfish_le'|'blowfish_le_ecb': return swap32(decrypt(swap32(i),'blowfish' + algo[12:],key,iv))
        case 'salsa20':
            import ctypes
            from Cryptodome.Cipher import Salsa20
            ctx = Salsa20.new(key,iv[:8])
            pctx = ctypes.cast(ctx._state.get(),ctypes.POINTER(ctypes.c_uint32))

            bc = None
            if 'block_count' in kwargs: bc = kwargs['block_count']
            elif len(iv) > 8:
                assert len(iv) <= 16
                bc = int.from_bytes(iv[8:16],'little') # using int.from_bytes instead of struct to support len(iv) != 16
            if bc is not None:
                pctx[8],pctx[9] = bc & maskb(4),(bc >> 32) & maskb(4) # stream_state->input[8/9] = block count

            o = ctx.decrypt(i)
            if kwargs.get('return_block_count'): return o,pctx[8] | (pctx[9] << 32)
            return o
        case 'chacha20'|'xchacha20'|'tls_chacha20':
            from Cryptodome.Cipher import ChaCha20
            return ChaCha20.new(key,iv).decrypt(i)
        case 'chacha20_poly1305'|'xchacha20_poly1305'|'tls_chacha20_poly1305':
            from Cryptodome.Cipher import ChaCha20_Poly1305
            obj = ChaCha20_Poly1305.new(key,iv)
            if 'tag' in kwargs: tag = kwargs['tag']
            else: tag = i[-16:]
            if tag: return obj.decrypt_and_verify(i[:-16],tag)
            return obj.decrypt(i)
        case 'rc4'|'arc4':
            from Cryptodome.Cipher import ARC4
            return ARC4.new(key).decrypt(i)
        case 'rsa'|'rsa_le':
            from Cryptodome.PublicKey import RSA
            if type(key) == int and type(iv) == int: k = RSA.construct((key,iv))
            elif type(key) == int and iv is None: k = RSA.construct((key,0x10001))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            assert k.size_in_bytes() == len(i)
            return pow(int.from_bytes(i,'little' if algo == 'rsa_le' else 'big'),k.e,k.n).to_bytes(k.size_in_bytes(),'big')
        case 'rsa_inv'|'rsa_inv_le':
            assert 'r' in kwargs

            from Cryptodome.PublicKey import RSA
            if type(key) == int and type(iv) == int: k = RSA.construct((key,iv))
            elif type(key) == int and iv is None: k = RSA.construct((key,0x10001))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            assert k.size_in_bytes() == len(i)
            c = pow(int.from_bytes(i,'little' if algo == 'rsa_inv_le' else 'big'),k.e,k.n)
            R = pow(pow(pow(2,k.size_in_bits()),-1,k.n),kwargs['r'],k.n)
            return ((c * R) % k.n).to_bytes(k.size_in_bytes(),'big')
        case 'tea'|'tea_be'|'tea_le': return tea_decrypt(i,key,le=algo == 'tea_le')

        case 'hatch':
            d = bytearray(i)
            ln = len(i)
            swp = 0

            l1 = key * 4
            idx1 = 0
            l2 = crc_hash(ln.to_bytes(8,'little'),'crc32').to_bytes(4,'little')*4
            idx2 = 8
            xr = (ln >> 2) & mask(7)

            for ix in range(ln):
                v = d[ix]
                v ^= xr ^ l2[idx2];idx2 += 1
                if swp: v = ((v & mask(4)) << 4) | (v >> 4)
                v ^= l1[idx1];idx1 += 1
                d[ix] = v

                if idx1 < 16:
                    if idx2 > 12:
                        idx2 = 0
                        swp = not swp
                elif idx2 <= 8:
                    idx1 = 0
                    swp = not swp
                else:
                    xr = (xr + 2) & mask(7)
                    if swp:
                        swp = 0
                        idx1 = xr % 7
                        idx2 = (xr % 12) +2
                    else:
                        swp = 1
                        idx1 = (xr % 12) + 3
                        idx2 = xr % 7

            return bytes(d)
        case 'capcom_mame':
            if type(iv) == str: iv = iv.encode('ascii')
            key = [iv[3],key[0],iv[1],key[1],iv[0],key[2],iv[2],key[3]]
            for ix,b in enumerate(iv[4:]): key[ix % 8] ^= b
            return decrypt(i,'xor',bytes(key))
        case 'mmfs'|'mmfs_285'|'mmfs_286':
            assert type(key) == bytes
            if not key in MMFS_DEC:
                dec = bytearray(range(0x100))
                hv = kp = ix2 = 0
                for ix in range(0x100):
                    hv = rotate8(hv)
                    if hv == key[kp]: hv = kp = 0
                    ix2 = (ix2 + (hv ^ key[kp]) + dec[ix]) & maskb(1)
                    dec[ix2],dec[ix] = dec[ix],dec[ix2]
                    kp += 1
                MMFS_DEC[key] = dec

            d = bytearray(i)
            if algo == 'mmfs_286' and iv & 1:
                if isinstance(iv,int): iv = iv.to_bytes(2,'little')
                assert len(iv) == 2
                d[0] ^= iv[0] ^ iv[1]

            tmp = MMFS_DEC[key].copy()
            ix1 = ix2 = 0
            for ix in range(len(i)):
                ix1 = (ix1 + 1) & maskb(1)
                ix2 = (ix2 + tmp[ix1]) & maskb(1)
                tmp[ix1],tmp[ix2] = tmp[ix2],tmp[ix1]
                d[ix] ^= tmp[(tmp[ix1] + tmp[ix2]) & maskb(1)]

            return bytes(d)
        case 'mmfs_key':
            key = bytearray(i.replace(b'\0',b''))[:128] + b'\0'*128
            if len(i) < 255: key[len(i) + 1] = sum(b * 2 for b in i) & maskb(1)
            return bytes(key)

    raise NotImplementedError(algo)

class Huffman:
    TREE_SIZE = 512

    def __init__(self,inp:BitReader):
        self.inp = inp
        self.lhs = [0] * self.TREE_SIZE
        self.rhs = [0] * self.TREE_SIZE
        self.token = 256

    def create_tree(self):
        bit = self.inp.get_bit()
        
        if bit is None: raise EOFError("Unexpected EOF in compressed stream")
        elif bit != 0:
            v = self.token
            self.token += 1
            if v >= self.TREE_SIZE: raise ValueError("Invalid stream, tree size exceeded")

            self.lhs[v] = self.create_tree()
            self.rhs[v] = self.create_tree()
            return v
        else:
            v = self.inp.get_bits(8,True)
            if v is None: raise EOFError("Unexpected EOF while reading leaf")
            return v

    def unpack(self,usize:int,padding=False):
        self.token = 256
        root = self.create_tree()
        if padding: self.inp.reset()
        out = bytearray()

        for _ in range(usize):
            sym = root
            while sym >= 0x100:
                bit = self.inp.get_bit()
                if bit is None: return bytes(out)
                if bit != 0: sym = self.rhs[sym]
                else: sym = self.lhs[sym]
            out.append(sym)

        return bytes(out)
def huffman_decompress(i:bytes,usize:int,padding=False): return Huffman(BitReader(i)).unpack(usize,padding)
def lzss_decompress(i:bytes,usize:int=None):
    d = BitReader(i)
    ob = bytearray()
    win = bytearray(0x2000)
    winp = 1
    while True:
        flg = d.get_bit()
        if flg is None: break
        if flg:
            b = d.get_bits(8)
            ob.append(b)
            win[winp] = b
            winp = (winp + 1) & mask(13)
        else:
            of = d.get_bits(13)
            if of == 0: break
            l = d.get_bits(4) + 2
            for x in range(l + 1):
                b = win[(of + x) & mask(13)]
                ob.append(b)
                win[winp] = b
                winp = (winp + 1) & mask(13)
    return bytes(ob)[:usize]
def lzss8_decompress(i:bytes,usize:int=None,win_size=0x1000,threshold=3,maxm=18):
    ob = bytearray()
    ring = bytearray(win_size)
    p = 0
    rp = win_size - maxm
    f = 0

    while (usize is None or len(ob) < usize) and p < len(i):
        if not f & 0xFF00:
            if p >= len(i): break
            f = i[p] | 0x8000;p += 1

        if f & 1:
            if p >= len(i): break
            c = i[p];p += 1

            ob.append(c)
            ring[rp % win_size] = c
            rp += 1
        else:
            if p + 1 >= len(i): break
            b1 = i[p];p += 1
            b2 = i[p];p += 1

            idx = ((b2 & 0xF0) << 4) | b1
            c = (b2 & 0x0F) + threshold

            for ix in range(c):
                if usize is not None and len(ob) >= usize: break
                c = ring[(idx + ix) % win_size]
                ob.append(c)
                ring[rp % win_size] = c
                rp += 1

        f >>= 1

    return bytes(ob)
def lzss16_decompress(i:bytes,usize:int=None,big_endian=False):
    pos = 0

    def ru8():
        nonlocal pos
        if pos >= len(i): return
        b = i[pos]
        pos += 1
        return b

    def ru16():
        b1 = ru8()
        if b1 is None: return
        b2 = ru8()
        if b2 is None: return
        return (b1 << 8) | b2 if big_endian else (b2 << 8) | b1

    ob = bytearray()
    win = bytearray(0x2000)
    winp = 0

    ctrlw = ru16()
    if ctrlw is None: return bytes()
    bl = 16

    def get_flg():
        nonlocal ctrlw,bl

        if bl == 0:
            cw = ru16()
            if cw is None: return
            ctrlw = cw
            bl = 16

        bit = ctrlw & 1
        ctrlw >>= 1
        bl -= 1

        if bl == 0:
            cw = ru16()
            if cw is not None:
                ctrlw = cw
                bl = 16

        return bit

    while True:
        if usize and len(ob) >= usize: break

        f1 = get_flg()
        if f1 is None: break

        if f1 == 1:
            b = ru8()
            if b is None: break
            ob.append(b)
            win[winp] = b
            winp = (winp + 1) & mask(13)
        else:
            f2 = get_flg()
            if f2 is None: break
            if f2 == 0:
                b3 = get_flg()
                b4 = get_flg()
                if b3 is None or b4 is None: break

                mtlen = ((b3 << 1) | b4) + 2
                dist = ru8()
                if dist is None: break
                mtdist = dist
            else:
                b1 = ru8()
                if b1 is None: break
                b2 = ru8()
                if b2 is None: break

                mtdist = b1 + ((b2 >> 3) * 256)
                lenc = b2 & 0x07 

                if lenc != 0: mtlen = lenc + 2
                else:
                    b3 = ru8()
                    if b3 is None: break
                    if b3 == 0: break
                    elif b3 == 1: continue
                    else: mtlen = b3 + 1

            cpysrc = (winp - mtdist) & mask(13)
            for _ in range(mtlen):
                b = win[cpysrc]
                ob.append(b)
                win[winp] = b
                winp = (winp + 1) & mask(13)
                cpysrc = (cpysrc + 1) & mask(13)

    return bytes(ob)[:usize] if usize else bytes(ob)
def lzw_decompress(i:bytes,bit_width=9,reset=0x100,eof=0x101,max_dict:int=None):
    max_dict = max_dict or reset
    d = BitReader(i)

    resetd = lambda:{x:x.to_bytes() for x in range(0x100)}
    dic = resetd()
    nxt = 0x100
    def get_nxt():
        nonlocal dic,nxt
        while True:
            b = d.get_bits(bit_width)
            if b != reset: return b
            dic = resetd()
            nxt = 0x100

    c = get_nxt()
    if c in (None,eof): return b''

    o = []
    seq = dic[c]
    o.append(seq)
    prev_seq = seq

    while True:
        c = d.get_bits(bit_width)
        if c is None or c == eof: break
        if c == reset:
            dic = resetd()
            nxt = 256
            c = d.get_bits(bit_width)
            if c is None or c == eof: break
            seq = dic[c]
            o.append(seq)
            prev_seq = seq
            continue

        if c in dic: seq = dic[c]
        elif c == nxt: seq = prev_seq + prev_seq[:1]
        else: raise ValueError(f"Invalid LZW code encountered: {c}")

        o.append(seq)
        if nxt < max_dict:
            dic[nxt] = prev_seq + seq[:1]
            nxt += 1
        prev_seq = seq

    return b"".join(o)
def ash0_decompress(i:bytes):
    if len(i) < 12 or i[:4] != b'ASH0': return b''
    decomp_size = int.from_bytes(i[5:8],'big')
    sym_offset = int.from_bytes(i[8:12],'big')
    if sym_offset >= len(i): return b''

    out = bytearray(decomp_size)
    out_pos = 0
    dist_reader = BitReader(i[sym_offset:])
    sym_reader = BitReader(i[12:])

    def read_tree(reader, width, max_nodes):
        nodes = [(0,0)] * (max_nodes * 2)
        root = 0
        node_count = 1
        stack = []
        while True:
            if reader.get_bit():
                nodes[root] = (node_count, node_count + 1)
                stack.append(node_count + 1)
                root = node_count
                node_count += 2
            else:
                nodes[root] = (reader.get_bits(width), None)
                if not stack: break
                root = stack.pop()
        return nodes

    try:
        sym_tree = read_tree(sym_reader,9,1 << 9)
        dist_tree = read_tree(dist_reader,11,1 << 11)
    except: return b''

    def get_huffman_code(reader,tree):
        node = tree[0]
        while node[1] is not None: node = tree[node[reader.get_bit() or 0]] 
        return node[0]

    while out_pos < decomp_size:
        try:
            sym = get_huffman_code(sym_reader,sym_tree)
            if sym < 0x100: out[out_pos] = sym;out_pos += 1
            else:
                length = sym - 0x100 + 3
                dist = get_huffman_code(dist_reader,dist_tree) + 1
                copy_pos = out_pos - dist
                for _ in range(length):
                    if out_pos >= decomp_size: break
                    out[out_pos] = out[copy_pos];out_pos += 1
                    copy_pos += 1
        except: break

    return bytes(out)
def lz4_fast_decompress(d:bytes,usize:int=None):
    p = 0
    ob = bytearray()

    try:
        while usize is None or len(ob) < usize:
            tok = d[p]
            p += 1

            num_literals = tok >> 4
            if num_literals == 0x0F:
                while True:
                    l = d[p]
                    p += 1
                    num_literals += l
                    if l != 0xFF: break

            ob.extend(d[p : p + num_literals])
            p += num_literals

            if usize is not None and len(ob) >= usize: break

            off = d[p] | (d[p + 1] << 8)
            p += 2

            ml = (tok & 0x0F) + 4
            if ml == 19:
                while True:
                    l = d[p]
                    p += 1
                    ml += l
                    if l != 0xFF: break

            for _ in range(ml): ob.append(ob[-off])
    except IndexError: pass
        
    return bytes(ob[:usize])
class AnacondaDecoder:
    def __init__(self,d:bytes):
        self.d = d
        self.p = 0
        self.bit_accum = 0
        self.cnb = 0
        self.o = bytearray()

    def _get_bits(self,bits:int):
        while self.cnb < bits:
            if self.p >= len(self.d): raise EOFError("Unexpected end of compressed data stream")
            self.bit_accum |= (self.d[self.p] << self.cnb)
            self.cnb += 8
            self.p += 1

        val = self.bit_accum & ((1 << bits) - 1)
        self.bit_accum >>= bits
        self.cnb -= bits
        return val
    def _gen_huffman_table(self,syms:int,lngs:list[int]):
        lngc = [0] * 0x10
        for length in lngs:
            if length > 0: lngc[length] += 1
        fstc = [0] * 0x10
        for i in range(1, 16): fstc[i] = (fstc[i - 1] + lngc[i - 1]) << 1

        tbl = [0] * 0x800
        ix = 0
        for i in range(1, 16):
            code_limit = 1 << i
            next_code = fstc[i] + lngc[i]
            next_index = ix + (code_limit - fstc[i])

            for j in range(syms):
                if lngs[j] == i:
                    tbl[ix] = j
                    ix += 1
            for j in range(next_code, code_limit):
                tbl[ix] = ~next_index
                ix += 1
                next_index += 2

        return tbl
    def _get_huff(self,tbl:list[int]):
        bp = 0
        ix = 0
        while True:
            if self.cnb <= bp:
                if self.p >= len(self.d): raise EOFError("Unexpected end of compressed data stream")
                self.bit_accum |= (self.d[self.p] << self.cnb)
                self.cnb += 8

            b = (self.bit_accum >> bp) & 1
            bp += 1
            ix += b

            if tbl[ix] >= 0: break
            ix = ~tbl[ix]

        self.bit_accum >>= bp
        self.cnb -= bp
        return tbl[ix]

    def decode(self) -> bytes:
        final = False
        codelen_order = [18,17,16,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

        while not final:
            block_type_raw = self._get_bits(4)
            final = (block_type_raw >> 3) != 0
            block_type = block_type_raw & mask(3)

            type_map = {7:0,5:1,6:2}
            block_type = type_map.get(block_type, 3)

            if block_type == 3: raise ValueError("Invalid Anaconda block type encountered")

            if block_type == 0:
                self.cnb = 0
                self.bit_accum = 0
                lng = self._get_bits(16)

                self.o.extend(self.d[self.p:self.p + lng])
                self.p += lng
                continue

            if block_type == 2:
                literal_count = self._get_bits(5) + 0x101
                distance_count = self._get_bits(5) + 1
                code_len_count = self._get_bits(4) + 4

                cdln = [0] * 19
                for i in range(code_len_count):
                    cdln[codelen_order[i]] = self._get_bits(3)
                code_len_table = self._gen_huffman_table(19, cdln)

                lengths = [0] * (literal_count + distance_count)
                c = 0
                while c < literal_count + distance_count:
                    sym = self._get_huff(code_len_table)
                    if sym < 16:
                        lengths[c] = sym
                        c += 1
                    elif sym == 16:
                        repeat_count = self._get_bits(2) + 3
                        val = lengths[c - 1] if c else 0
                        for _ in range(repeat_count):
                            lengths[c] = val
                            c += 1
                    elif sym == 17:
                        repeat_count = self._get_bits(3) + 3
                        for _ in range(repeat_count):
                            lengths[c] = 0
                            c += 1
                    elif sym == 18:
                        repeat_count = self._get_bits(7) + 11
                        for _ in range(repeat_count):
                            lengths[c] = 0
                            c += 1

                lit_tbl = self._gen_huffman_table(literal_count, lengths[:literal_count])
                dist_tbl = self._gen_huffman_table(distance_count, lengths[literal_count:])
            else:
                fix_lit_lng = [8]*0x90 + [9]*0x70 + [7]*0x18 + [8]*8
                fix_dist_lng = [5]*0x20
                lit_tbl = self._gen_huffman_table(0x120, fix_lit_lng)
                dist_tbl = self._gen_huffman_table(0x20, fix_dist_lng)

            while True:
                sym = self._get_huff(lit_tbl)
                if sym < 0x100: self.o.append(sym)
                elif sym == 0x100: break
                else:
                    if sym <= 0x108: rep_l = (sym - 0x101) + 3
                    elif sym <= 0x11C:
                        lng_bits = (sym - 0x105) // 4
                        rep_l = self._get_bits(lng_bits) + 3 + ((4 + ((sym - 0x109) & 3)) << lng_bits)
                    elif sym == 0x11D: rep_l = 0x102
                    else: raise ValueError("Invalid length symbol encountered.")

                    dist_sym = self._get_huff(dist_tbl)
                    if dist_sym <= 3: dist = dist_sym + 1
                    elif dist_sym <= 29:
                        dist_bits = (dist_sym - 2) // 2
                        dist = self._get_bits(dist_bits) + 1 + ((2 + (dist_sym & 1)) << dist_bits)
                    else: raise ValueError("Invalid distance symbol encountered.")

                    if dist > len(self.o): raise ValueError("Invalid distance calculation; exceeds available output buffer.")

                    for _ in range(rep_l): self.o.append(self.o[-dist])

        return bytes(self.o)
def ananconda_decompress(data:bytes): return AnacondaDecoder(data).decode()
def rtl_lz_decompress(i:bytes,usize:int=None):
    if usize is None: usize,i = int.from_bytes(i[:8],byteorder="little"),i[8:]

    p = 0
    o = bytearray()
    while len(o) < usize:
        tok = i[p];p += 1
        if 0x20 > tok:
            if tok == 0:
                tok = i[p];p += 1
                if tok == 0:
                    s = int.from_bytes(i[p:p + 2],'little');p += 2
                    if s == 0: break
                    o.extend(i[p:p + s]);p += s
                else:
                    tok += 0x1F
                    o.extend(i[p:p + tok]);p += tok
            else: o.extend(i[p:p + tok]);p += tok
        elif 0x40 > tok >= 0x20:
            c = tok - 0x20
            if c == 0:
                tok = i[p];p += 1
                c = tok + 0x20
            o.extend([0]*c)
        elif 0x80 > tok >= 0x40:
            tok4 = tok & 0x0F
            if tok4 == 0:
                l = int.from_bytes(i[p:p + 2],'little');p += 2
                of = int.from_bytes(i[p:p + 2],'little');p += 2
                while tok & 0x30:
                    o.append(i[p]);p += 1
                    tok -= 0x10
                o.extend(o[-l-of+1:(-of+1) or None])
            else:
                of = int.from_bytes(i[p:p + 2],'little');p += 2
                while tok & 0x30:
                    o.append(i[p]);p += 1
                    tok -= 0x10
                o.extend(o[-of-tok4-2+1:(-of+1) or None])
        elif tok >= 0x80:
            if tok & 0x40: o.extend(i[p:p + 2]);p += 2
            of = (tok & 0x3F)*2 + 2
            o.extend(o[-of:(-of+2) or None])

    return bytes(o)

def crc(i:bytes,size:int,poly:int,init:int,xor:int,reflect:bool,value:int=None):
    crc = init if value is None else (value ^ xor)
    if reflect:
        poly = reflecti(poly,size)
        for b in i:
            crc ^= b
            for _ in range(8):
                if crc & 1: crc = (crc >> 1) ^ poly
                else: crc >>= 1
    else:
        msk1,msk2,sv = 1 << (size - 1),mask(size),size - 8
        for b in i:
            crc ^= b << sv
            for _ in range(8):
                if crc & msk1: crc = (crc << 1) ^ poly
                else: crc <<= 1
                crc &= msk2
    return crc ^ xor
def crc8(i:bytes,poly=0x7,init=0,xor=0,reflect=False,value:int=None): return crc(i,8,poly,init,xor,reflect,value)
def crc16(i:bytes,poly=0x8005,init=0,xor=0,reflect=True,value:int=None): return crc(i,16,poly,init,xor,reflect,value)
def crc24(i:bytes,poly=0x864CFB,init=0xB7074CE,xor=0,reflect=False,value:int=None): return crc(i,24,poly,init,xor,reflect,value)
def crc32(i:bytes,poly=0x04C11DB7,init=0xFFFFFFFF,xor=0xFFFFFFFF,reflect=True,value:int=None): return crc(i,32,poly,init,xor,reflect,value)
def crc64(i:bytes,poly=0x42F0E1EBA9EA3693,init=0x0000000000000000,xor=0x0000000000000000,reflect=False,value:int=None): return crc(i,64,poly,init,xor,reflect,value)
def fnv1_64(i:bytes,prime=0x100000001B3,offset=0xCBF29CE484222645):
    for b in i: offset = ((offset * prime) & maskb(8)) ^ b
    return offset
def fnv1a_64(i:bytes,prime=0x100000001B3,offset=0xCBF29CE484222645):
    for b in i: offset = ((offset ^ b) * prime) & maskb(8)
    return offset
def fnv1_32(i:bytes,prime=0x1000193,offset=0x811C9DC5):
    for b in i: offset = ((offset * prime) & maskb(4)) ^ b
    return offset
def fnv1a_32(i:bytes,prime=0x1000193,offset=0x811C9DC5):
    for b in i: offset = ((offset ^ b) * prime) & maskb(4)
    return offset
def bkdr(i:bytes,seed=131,init=0):
    h = init
    for b in i: h = (h * seed + b) & maskb(4)
    return h
def sdbm(i:bytes,seed=0x1003F,init=0):
    h = init
    for b in i: h = ((h + b) * seed) & maskb(4)
    return h
def tarzan_hash(i:bytes):
    o = 0
    shft = 0
    lng =  0

    for b in i:
        o += b << shft
        shft += 8
        if shft > 24: shft = 0
        lng += 1
    return (o + lng) & maskb(4)
def luas_hash(i:bytes):
    stp = (len(i) >> 5) + 1
    o = p = len(i)
    while p >= stp:
        o ^= (o * 0x20 + (o >> 2) + i[p - 1]) & maskb(4)
        p -= stp
    return o
def sxm_hash(i:bytes):
    v = 0
    for b in i: v = ((v * 137) + b) & maskb(8)
    return v

def tea_decrypt(i:bytes,k:bytes,le=False):
    e = '<' if le else '>'
    if type(i) == bytes: i = struct.unpack(f'{e}{len(i)//4}I',i)
    if type(k) == bytes: k = struct.unpack(f'{e}4I',k)
    i = list(i)
    assert len(k) == 4 and not len(i) % 2

    DLT = 0x9e3779b9
    def dec_blk(i):
        v0,v1 = i[0],i[1]
        sv = (DLT * 32) & maskb(4)
        for _ in range(32):
            v1 = (v1 - (((v0 << 4) + k[2]) ^ (v0 + sv) ^ ((v0 >> 5) + k[3]))) & maskb(4)
            v0 = (v0 - (((v1 << 4) + k[0]) ^ (v1 + sv) ^ ((v1 >> 5) + k[1]))) & maskb(4)
            sv = (sv - DLT) & maskb(4)
        return v0,v1

    for ix in range(0,len(i),2): i[ix:ix+2] = dec_blk(i[ix:ix+2])
    return struct.pack(f'{e}{len(i)}I',*i)

def __chmr(*i:tuple[int,int]): return set(sum([list(range(a,b)) for a,b in i],[]))
CHMS = {
'n64mpak':(
    '\0' + '\0'*14 + ' '
    '0123456789ABCDEF'
    'GHIJKLMNOPQRSTUV'
    'WXYZ!"#\'*+,-./:='
    '?@。゛゜ァィゥェォッャュョヲン'
    'アイウエオカキクケコサシスセソタ'
    'チツテトナニヌネノハヒフヘホマミ'
    'ムメモヤユヨラリルレロワガギグゲ'
    'ゴザジズゼゾダヂヅデドバビブベボ'
    'パピプペポ'
),'n64mpak?r':__chmr((1,0x0F),(149,0x100)),
'latin1c':(
    '\0' + 'ÿ'*0x1F +\
    ' !"#$%&\'()*+,-./'
    '0123456789:;<=>?'
    '@ABCDEFGHIJKLMNO'
    'PQRSTUVWXYZ[\\]^_'
    '`abcdefghijklmno'
    'pqrstuvwxyz{|}~▒'\
    +'▯'*0x20+\
    ' ¡¢£¤¥¦§¨©ª«¬—®¯'
    '°±²³´µ¶·¸¹º»¼½¾¿'
    'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏ'
    'ÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß'
    'àáâãäåæçèéêëìíîï'
    'ðñòóôõö÷øùúûüýþÿ'
)
}
def decode(i:bytes,algo:str):
    algo = algo.lower().replace('-','').replace('_','')
    ct = CHMS[algo]
    it = CHMS.get(algo + '?r',set())
    o = []
    for ix,b in enumerate(i):
        if b in it: raise UnicodeDecodeError(algo,i,ix,ix+1,'invalid character')
        o.append(ct[b])
    return ''.join(o)

import os,time
from threading import Thread

HASHTS = {
    f'crc8_{x}':1 for x in CRC8}|{
    f'crc16_{x}':2 for x in CRC16}|{
    f'crc24_{x}':3 for x in CRC24}|{
    f'crc32{"_" if len(x)>1 else ""}{x}':4 for x in CRC32}|{
    f'crc64_{x}':8 for x in CRC64}|{
    'crc8':1,'crc16':2,'crc24':3,'crc32':4,'crc40_gsm':5,'crc64':8,
    'adler32':4,
    'fnv1_32':4,'fnv1a_32':4,
    'fnv1_64':8,'fnv1a_64':8,
    'bkdr':4,'bkdr_ltr':4,'bkdr_rtl':4,
    'sdbm':4,'sdbm_ltr':4,'sdbm_rtl':4,
    'murmur3':4,'mmh3':4,'murmur3_32':4,'mmh3_32':4,
    'murmur3_128':16,'mmh3_128':16,
    'xxh32':4,'xxh64':8,'xxh3_64':8,'xxh128':16,'xxh3_128':16,
    'md5':16,'sha1':20,'md5_sha1':36,
    'sha224':28,'sha256':32,'sha384':48,'sha512':64,
    'sha3_224':28,'sha3_256':32,'sha3_384':48,'sha3_512':64,
    'sha512_224':28,'sha512_256':32,
    'blake2b':32,'blake2s':16,
    'shake128':16,'shake256':32,'shake_128':16,'shake_256':32,
    'ripemd160':20,'sm3':32,
    'tarzan':4,'luas':4,'sxm':8,'hash40':5,
}
class HashLib:
    def __init__(self,p:str,fmt=lambda x:x,encoding='utf-8'):
        self.p = os.path.abspath(p)
        self.fmt = fmt
        self.enc = encoding

        self.db = {}
        self.lhsh = None

        self._load_thrd = None
    @classmethod
    def new(cls,p:str,ht:str,**kwargs):
        c = cls(p,**kwargs)
        c.ht = ht
        c.hs = HASHTS[ht]
        return c
    @classmethod
    def dl(cls,p:str,db,**kwargs): return cls(db.get(p + '_hashes'),**kwargs).load()

    def load(self):
        if os.path.exists(self.p):
            assert os.path.isfile(self.p)
            self._load_thrd = Thread(target=self._load)
            self._load_thrd.start()
        return self
    def loadb(self):
        self.load().wait()
        return self
    def wait(self):
        if self._load_thrd is not None:
            self._load_thrd.join()
            self._load_thrd = None
    def _load(self):
        f = File(self.p,'rb',endian='>')
        self.ots = f.readu48()/100
        self.ht = f.read0s().decode(self.enc)
        self.hs = HASHTS[self.ht]
        c = f.readvlq()
        ks = [f.unpacki(self.hs) for _ in range(c)]
        d = b'\x78\xDA' + f.read()
        f.close()
        vs = [x.decode(self.enc) for x in decompress(d,'zlib').split(b'\0')]
        db = zip(ks,vs)
        self.lhsh = hash(db)
        self.db = dict(db)

    def save(self):
        ks = list(self.db.keys())
        vs = list(self.db.values())
        nhsh = hash(zip(ks,vs))
        if self.lhsh == nhsh: return
        import zlib

        f = File(self.p,'wb',endian='>')
        ts = int(time.time()*100)
        f.writeu48(ts)
        f.write(self.ht.encode(self.enc) + b'\0')
        f.writevlq(len(ks))

        for k in ks: f.packi(k,self.hs)
        f.write(zlib.compress(bytes(b'\0'.join([x.encode(self.enc) for x in vs])),level=9)[2:])
        f.close()

        self.lhsh = nhsh
        self.ots = ts

    def crc(self,i:str|bytes):
        if type(i) == str: i = i.encode(self.enc)
        return crc_hash(self.fmt(i),self.ht)

    def add(self,i:list[str]|str):
        if type(i) == str: i = [i]
        for v in i:
            k = self.crc(v)
            if k not in self.db: self.db[k] = v
    def get(self,v:str|int,default=None) -> str:
        if type(v) == str: v = self.crc(v)
        return self.db.get(v,default)
    def __getitem__(self,v:str|int): return self.get(v)
    def __contains__(self,v:str|int):
        if type(v) == str: v = self.crc(v)
        return v in self.db
