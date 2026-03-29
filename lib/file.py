import struct,io,sys

def align(n:int,blocksize:int): return -n % blocksize
def swap32(i:bytes):
    c = len(i) // 4
    return struct.pack(f'>{c}I',*struct.unpack(f'<{c}I',i))

class File:
    def __init__(self,f,mode='r',endian='>',middle_u24_little=True):
        if 'w' in mode and endian == '-': raise NotImplementedError('Middle endian not implemented for writing')
        if type(f) == str: f = open(f,mode.rstrip('b') + 'b')
        elif type(f) == bytes: f = io.BytesIO(f)
        self._f = f
        self._end = endian
        self._mend_u24_le = middle_u24_little

        self._start_pos = self._f.tell()
        self._size = self.seek(0,2)
        self.seek(0)

    def read(self,n:int=None) -> bytes: return self._f.read(n)
    def write(self,data:bytes) -> int: return self._f.write(data)
    def seek(self,n:int,whence=0) -> int: return self._f.seek(n + (self._start_pos if whence == 0 else 0),whence)
    def tell(self) -> int: return self._f.tell() - self._start_pos
    def close(self): self._f.close()

    def skip(self,n:int): return self.seek(n,1)
    def back(self,n:int): return self.skip(-n)
    def reads(self): return self.read(1)

    def middle_scramble(self,d:bytes):
        o = bytearray()
        for i in range(len(d)//2):
            o.append(d[i*2+1])
            o.append(d[i*2])
        if len(d) % 2: o.append(d[-1])
        return bytes(o)
    def unpack(self,fmt:str,end=None):
        d = self.read(struct.calcsize(fmt))
        end = end or self._end
        if end == '-':
            d = self.middle_scramble(d)
            end = '>'
        return struct.unpack(end + fmt,d)[0]

    def readu8 (self) -> int: return self.unpack('B')
    def readu16(self,end=None) -> int: return self.unpack('H',end)
    def readu24(self,end=None) -> int:
        end = end or self._end
        d = self.read(3)
        if end == '-':
            if not self._mend_u24_le: d = self.middle_scramble(d)
            end = '>'
        if end == '<': d = d + b'\0'
        else: d = b'\0' + d
        return struct.unpack(end+'I',d)[0]
    def readu32(self,end=None) -> int: return self.unpack('I',end)
    def readu64(self,end=None) -> int: return self.unpack('Q',end)
    def reads8 (self) -> int: return self.unpack('b')
    def reads16(self,end=None) -> int: return self.unpack('h',end)
    def reads32(self,end=None) -> int: return self.unpack('i',end)
    def reads64(self,end=None) -> int: return self.unpack('q',end)
    def readf32(self,end=None):
        v = self.unpack('f',end)
        return float(f'{v:.7g}') # clamp precision to that of a float32
    def readf64(self,end=None) -> float: return self.unpack('d',end)
    def readleb128u(self):
        n = c = b = 0
        while True:
            b = self.readu8()
            n |= (b & 0x7f) << (c * 7)
            if not b & 0x80: return n
            c += 1

    def read0s(self):
        r = b''
        b = b''
        while True:
            b = self.reads()
            if not b or b == b'\0':break
            r += b
        return r

    def writeu8 (self,data:int): return self.write(struct.pack('B',data))
    def writeu16(self,data:int,end=None): return self.write(struct.pack((end or self._end)+'H',data))
    def writeu32(self,data:int,end=None): return self.write(struct.pack((end or self._end)+'I',data))
    def writeu64(self,data:int,end=None): return self.write(struct.pack((end or self._end)+'Q',data))
    def writes8 (self,data:int): return self.write(struct.pack('b',data))
    def writes16(self,data:int,end=None): return self.write(struct.pack((end or self._end)+'h',data))
    def writes32(self,data:int,end=None): return self.write(struct.pack((end or self._end)+'i',data))
    def writes64(self,data:int,end=None): return self.write(struct.pack((end or self._end)+'q',data))
    def writef32(self,data:float,end=None): return self.write(struct.pack((end or self._end)+'f',data))
    def writef64(self,data:float,end=None): return self.write(struct.pack((end or self._end)+'d',data))

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

    def decompress(self,size:int,algo:str,*args,**kwargs): return decompress(self.read(size),algo,*args,**kwargs)

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
    def __bool__(self):
        b = self.reads()
        if b: self.back(1)
        return bool(b)
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
            self.skip()
            self.recs = self.readu16()

            self.seek(self.coff_off + seco)
            for x in range(secs):
                s,o = self.readu16()*blcks,self.readu16()
                self.secs[x] = (o,s,o+s)
                self.skip(4)
        else: raise NotImplementedError(pe)
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
def decompress(i:bytes,algo:str,*args,**kwargs) -> bytes:
    match algo:
        case 'none': return i
        case 'zlib':
            import zlib
            fnc = zlib.decompress
        case 'gzip':
            import gzip
            fnc = gzip.decompress
        case 'lzma'|'lzma_alone':
            import lzma
            if kwargs.get('null_usize'): i = i[:5] + b'\xFF'*8 + i[13:]
            return lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(i)
        case 'lzma_us32'|'lzma_alone_us32': return decompress(i[:9] + b'\0'*4 + i[9:],'lzma_alone',*args,**kwargs)
        case 'zstd':
            if sys.version_info >= (3,14): from compression import zstd # type: ignore
            else:
                try: import backports_zstd as zstd # type: ignore
                except: from backports import zstd # type: ignore
            if 'zstd_dict' in kwargs and type(kwargs['zstd_dict']) == bytes: kwargs['zstd_dict'] = zstd.ZstdDict(kwargs['zstd_dict'])
            fnc = zstd.decompress
        case 'lz4'|'lz4_block':
            import lz4.block
            fnc = lz4.block.decompress
        case 'lz4_frame':
            import lz4.frame
            fnc = lz4.frame.decompress
        case 'lzo'|'lzo1x':
            if 'db' in kwargs: kwargs['db'].get('lzo')
            import bin.lzo # type: ignore
            return bin.lzo.decompress(i,False,kwargs.get('usize',args[0]),algorithm='LZO1X')
        case 'lzo1y':
            if 'db' in kwargs: kwargs['db'].get('lzo')
            import bin.lzo # type: ignore
            return bin.lzo.decompress(i,False,kwargs.get('usize',args[0]),algorithm='LZO1Y')
        case 'huffman': fnc = huffman_decompress
        case 'lzss': fnc = lzss_decompress
        case 'lzw_lg':
            fnc = lzw_decompress
            if algo == 'lzw_lg': kwargs |= {'bit_width':14,'reset':0x3FFE,'eof':0x3FFF,'max_dict':0x3FFE}
        case 'implode':
            if 'db' in kwargs: kwargs['db'].get('pwexplode')
            import bin.pwexplode # type: ignore
            return bin.pwexplode.explode(i)
        case 'mio0'|'yay0'|'yaz0'|'vpk0':
            import crunch64
            fnc = getattr(crunch64,algo).decompress
        case 'oodle_kraken':
            global OODLE
            assert 'usize' in kwargs and (OODLE or 'db' in kwargs)
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
        case _: raise NotImplementedError(algo)
    return fnc(i,*args,**kwargs)
def crc_hash(i:bytes,algo:str,*args,**kwargs) -> int:
    match algo:
        case 'crc32':
            import zlib
            return zlib.crc32(i,*args,**kwargs) & 0xFFFFFFFF
        case 'crc16': fnc = crc16
        case 'tarzan': fnc = tarzan_hash
        case 'sha1'|'sha256'|'md5':
            import hashlib
            r = getattr(hashlib,algo)(i).digest()
            if kwargs.get('bytes') or args in {(True,),(1,)}: return r
            return int.from_bytes(r,'big')
        case _: raise NotImplementedError(algo)
    return fnc(i,*args,**kwargs)
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
                pctx[8],pctx[9] = bc & 0xFFFFFFFF,(bc >> 32) & 0xFFFFFFFF # stream_state->input[8/9] = block count

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

        case 'hatch':
            d = bytearray(i)
            ln = len(i)
            swp = 0

            l1 = key * 4
            idx1 = 0
            l2 = crc_hash(ln.to_bytes(8,'little'),'crc32').to_bytes(4,'little')*4
            idx2 = 8
            xr = (ln >> 2) & 0x7F

            for ix in range(ln):
                v = d[ix]
                v ^= xr ^ l2[idx2];idx2 += 1
                if swp: v = ((v & 0x0F) << 4) | (v >> 4)
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
                    xr = (xr + 2) & 0x7F
                    if swp:
                        swp = 0
                        idx1 = xr % 7
                        idx2 = (xr % 12) +2
                    else:
                        swp = 1
                        idx1 = (xr % 12) + 3
                        idx2 = xr % 7

            return bytes(d)
        case _: raise NotImplementedError(algo)

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
            winp = (winp + 1) & 0x1FFF
        else:
            of = d.get_bits(13)
            if of == 0: break
            l = d.get_bits(4) + 2
            for x in range(l + 1):
                b = win[(of + x) & 0x1FFF]
                ob.append(b)
                win[winp] = b
                winp = (winp + 1) & 0x1FFF
    return bytes(ob)[:usize]
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
            d.append(seq)
            prev_seq = seq
            continue

        if c in dic: seq = dic[c]
        elif c == nxt: seq = prev_seq + prev_seq[:1]
        else: raise ValueError(f"Invalid LZW code encountered: {c}")

        d.append(seq)
        if nxt < max_dict:
            dic[nxt] = prev_seq + seq[:1]
            nxt += 1
        prev_seq = seq

    return b"".join(d)

N64CHM = (
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
)
def decode_n64_mpak(i:bytes):
    o = []
    for b in i:
        assert b < len(N64CHM) and (b >= 0x0F or b == 0)
        o.append(N64CHM[b])
    return ''.join(o)

def crc16(i:bytes,poly:int,init=0) -> int:
    crc = init
    for b in i:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000: crc = (crc << 1) ^ poly
            else: crc <<= 1
            crc &= 0xFFFF
    return crc
def tarzan_hash(i:bytes):
    o = 0
    shft = 0
    lng =  0

    for b in i:
        o += b << shft
        shft += 8
        if shft > 24: shft = 0
        lng += 1
    return (o + lng) & 0xFFFFFFFF
