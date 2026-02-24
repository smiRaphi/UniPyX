import struct,io

def align(n:int,blocksize:int): return -n % blocksize

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
    def writefloat(self,data:float,end=None): return self.write(struct.pack((end or self._end)+'f',data))

    def align(self,blocksize:int): return self.write(b'\0' * align(self.tell(),blocksize))
    def alignpos(self,blocksize:int): self.skip(align(self.tell(),blocksize))

    def add_file(self,f):
        if type(f) == str: f = open(f,'rb')
        while True:
            p = f.read(0x4000)
            if not p: break
            self.write(p)

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
        self.skip(-1)
        return bool(b)

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
