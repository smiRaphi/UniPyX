import struct

def align(n:int,blocksize:int): return -n % blocksize

class File:
    def __init__(self,f,mode='r',endian='>'):
        if type(f) == str: f = open(f,mode + 'b')
        self._f = f
        self._end = endian

        self._start_pos = self._f.tell()
        self.seek(0,2)
        self._size = self.tell()
        self.seek(0)

    def read(self,n:int=None) -> bytes: return self._f.read(n)
    def write(self,data:bytes) -> int: return self._f.write(data)
    def seek(self,n:int,whence=0) -> int: return self._f.seek(n + (self._start_pos if whence == 0 else 0),whence)
    def tell(self) -> int: return self._f.tell() - self._start_pos
    def close(self): self._f.close()

    def skip(self,n:int): self.seek(n,1)
    def reads(self): return self.read(1)

    def readu8 (self) -> int: return self.read(1)[0]
    def readu16(self,end=None) -> int: return struct.unpack((end or self._end)+'H',self.read(2))[0]
    def readu24(self,end=None) -> int:
        d = self.read(3)
        if (end or self._end) == '<': d = d + b'\0'
        else: d = b'\0' + d
        return struct.unpack((end or self._end)+'I',d)[0]
    def readu32(self,end=None) -> int: return struct.unpack((end or self._end)+'I',self.read(4))[0]
    def readu64(self,end=None) -> int: return struct.unpack((end or self._end)+'Q',self.read(8))[0]
    def reads8 (self) -> int: return struct.unpack('b',self.read(1))[0]
    def reads16(self,end=None) -> int: return struct.unpack((end or self._end)+'h',self.read(2))[0]
    def reads32(self,end=None) -> int: return struct.unpack((end or self._end)+'i',self.read(4))[0]
    def reads64(self,end=None) -> int: return struct.unpack((end or self._end)+'q',self.read(8))[0]
    def readfloat(self,end=None) -> float: return struct.unpack((end or self._end)+'f',self.read(4))[0]

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
        assert self.read(4) == b'PE\0\0'
        self.skip(2)
        secs = self.readu16()
        self.skip(12)
        self.skip(self.readu16() + 2)

        self.secs = {}
        for _ in range(secs):
            n = self.read(8).strip(b'\0').decode(errors='ignore')
            self.skip(8)
            s,o = self.readu32(),self.readu32()
            self.secs[n] = (o,s,o+s)
            self.skip(0x10)
