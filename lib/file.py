import struct,io,sys

ENDMAP = {'<':'little','>':'big','-':'big'}

def align(n:int,blocksize:int): return -n % blocksize
def swap32(i:bytes):
    c = len(i) // 4
    return struct.pack(f'>{c}I',*struct.unpack(f'<{c}I',i))
def mask(n:int): return (1 << n) - 1
def maskb(n:int): return mask(n * 8)

class File:
    def __init__(self,f,mode='r',endian='>'):
        if type(f) == str: f = open(f,mode.rstrip('b') + 'b')
        elif type(f) == bytes: f = io.BytesIO(f)
        self._f = f
        self._end = endian

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
    def readc(self,n:int=None):
        d = self.read(n)
        if n is not None: assert len(d) == n,"Unexpected EOF"
        return d
    def padc(self,n:int): assert not sum(self.readc(n)),"Unexpected Value in padding"

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
    def reads8 (self)         : return self.unpacki(1,1)
    def reads16(self,end=None): return self.unpacki(2,1,end)
    def reads24(self,end=None): return self.unpacki(3,1,end)
    def reads32(self,end=None): return self.unpacki(4,1,end)
    def reads40(self,end=None): return self.unpacki(5,1,end)
    def reads48(self,end=None): return self.unpacki(6,1,end)
    def reads64(self,end=None): return self.unpacki(8,1,end)
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

    def read0s(self):
        r = b''
        b = b''
        while True:
            b = self.reads()
            if not b or b == b'\0':break
            r += b
        return r

    def writeu8 (self,v:int): return self.packi(v,1,0)
    def writeu16(self,v:int,end=None): return self.packi(v,2,0,end)
    def writeu32(self,v:int,end=None): return self.packi(v,4,0,end)
    def writeu48(self,v:int,end=None): return self.packi(v,6,0,end)
    def writeu64(self,v:int,end=None): return self.packi(v,8,0,end)
    def writes8 (self,v:int): return self.packi(v,1,1)
    def writes16(self,v:int,end=None): return self.packi(v,2,1,end)
    def writes32(self,v:int,end=None): return self.packi(v,4,1,end)
    def writes48(self,v:int,end=None): return self.packi(v,6,1,end)
    def writes64(self,v:int,end=None): return self.packi(v,8,1,end)
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
def decompress(i:bytes,algo:str,**kwargs) -> bytes:
    match algo:
        case 'none': return i
        case 'zlib':
            import zlib
            return zlib.decompress(i,wbits=kwargs.get('wbits',15))
        case 'gzip':
            import gzip
            return gzip.decompress(i)
        case 'bz2'|'bzip2':
            import bz2
            return bz2.decompress(i)
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
            return zstd.decompress(i,kwargs.get('zstd_dict'))
        case 'lz4'|'lz4_block':
            import lz4.block
            return lz4.block.decompress(i,uncompressed_size=(len(i) * 8) if kwargs.get('no_size') else kwargs['usize'])
        case 'lz4_frame':
            import lz4.frame
            return lz4.frame.decompress(i)
        case 'lzo'|'lzo1x'|'lzo1y':
            if 'db' in kwargs: kwargs['db'].get('lzo')
            if algo == 'lzo': algo = 'lzo1x'

            import bin.lzo # type: ignore
            return bin.lzo.decompress(i,False,kwargs['usize'],algorithm=algo.upper())
        case 'huffman': return huffman_decompress(i,usize=kwargs['usize'],padding=kwargs.get('padding',False))
        case 'lzss': return lzss_decompress(i,usize=kwargs['usize'])
        case 'lzw_lg':
            if algo == 'lzw_lg': args = {'bit_width':14,'reset':0x3FFE,'eof':0x3FFF,'max_dict':0x3FFE}
            return lzw_decompress(i,**args)
        case 'implode':
            if 'db' in kwargs: kwargs['db'].get('pwexplode')
            import bin.pwexplode # type: ignore
            return bin.pwexplode.explode(i)
        case 'mio0'|'yay0'|'yaz0'|'vpk0':
            import crunch64
            return getattr(crunch64,algo).decompress(i)
        case 'ash0': return ash0_decompress(i)
        case 'oodle'|'oodle_kraken'|'oodle_leviathan':
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
    raise NotImplementedError(algo)
def crc_hash(i:bytes,algo:str,**kwargs) -> int:
    match algo:
        case 'crc32'|'adler32':
            import zlib
            return getattr(zlib,algo)(i,**kwargs) & maskb(4)
        case 'crc16': fnc = crc16
        case 'crc16_ccitt'|'crc16_ansi'|'crc16_ibm'|'crc16_dnp':
            kwargs['poly'] = {
                'ccitt':0x1021,
                'ibm':0x8005,'ansi':0x8005,
                'dnp':0x3D65,
            }[algo[6:]]
            fnc = crc16
        case 'fnv1_32': fnc = fnv1_32
        case 'fnv1a_32': fnc = fnv1a_32
        case 'fnv1_64': fnc = fnv1_64
        case 'fnv1a_64': fnc = fnv1a_64

        case 'sha1'|'sha256'|'md5':
            import hashlib
            r = getattr(hashlib,algo)(i).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')

        case 'tarzan': fnc = tarzan_hash
        case 'hash40': return (len(i) << 32) | crc_hash(i,'crc32',**kwargs)
        case _: raise NotImplementedError(algo)
    return fnc(i,**kwargs)
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

def crc16(i:bytes,poly=0x8005,init=0) -> int:
    crc = init
    for b in i:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000: crc = (crc << 1) ^ poly
            else: crc <<= 1
            crc &= maskb(2)
    return crc
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

import os,time
from threading import Thread

HASHTS = {
    'crc16':2,'crc16_ccitt':2,'crc16_ansi':2,'crc16_ibm':2,'crc16_dnp':2,
    'crc32':4,'adler32':4,
    'fnv1_32':4,'fnv1a_32':4,
    'fnv1_64':8,'fnv1a_64':8,
    'md5':16,'sha1':20,'sha256':32,
    'tarzan':4,'hash40':5,
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
    def wait(self):
        if self._load_thrd is not None:
            if self._load_thrd.is_alive(): self._load_thrd.join()
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
