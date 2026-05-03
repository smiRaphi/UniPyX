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
    def readu(self,c=b'\0',max=None,chks=0x100,include=False):
        if not max is None and max < chks: chks = max

        o = bytearray()
        while max is None or len(o) < max:
            d = self.read(chks)
            p = d.find(c)
            if p != -1 or len(d) != chks:
                o += d[:p + (1 if include else 0)]
                self.back(len(d) - p - 1)
                break
            o += d
        return bytes(o)
    def readall(self):
        self.seek(0)
        return self.read(self.size)

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

    def read0s(self,encoding:str=None,max:int=None,chks=0x100) -> bytes|str:
        r = self.readu(max=max,chks=chks)
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
    def size(self): return self._size

    def update_size(self,current=True):
        if current: self._size = self.tell()
        else:
            p = self.tell()
            self._size = self.seek(0,2)
            self.seek(p)
    def __len__(self): return self.size
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
        f = open(i,'rb')
        f.seek(0x3C)
        f.seek(int.from_bytes(f.read(4),'little'))
        t = f.read(2)
        f.close()

        if t == b'PE':
            import pefile
            r = pefile.PE(i)
            r.SECTIONS = {s.Name.rstrip(b'\0').decode(errors='ignore'):s for s in r.sections}
            return r
        elif t == b'NE':
            import nefile
            return nefile.NE(i)
        else: raise NotImplementedError(t.decode(errors='ignore'))

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
            from zlib import adler32
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
                if dcrc: crc = adler32(d,value=crc)
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
        case 'rtl_lz': return rtl_lz_decompress(i,usize=kwargs.get('usize'))

        case 'avlz':
            if len(i) < 8: raise ValueError("Not enough data to decompress")
            cs = int.from_bytes(i[:4],'little')
            us = int.from_bytes(i[4:8],'little')

            if cs == len(i): cs -= 8
            if cs != len(i) - 8: raise ValueError("Invalid compressed size")
            return lzss8_decompress(i[8:8+cs],usize=us)

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
