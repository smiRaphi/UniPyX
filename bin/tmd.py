import struct,io,os
from hashlib import pbkdf2_hmac,md5,sha1

try: from Cryptodome.Cipher import AES # type: ignore
except ImportError:
    try: from Crypto.Cipher import AES # type: ignore
    except ImportError: AES = None

BASED = os.path.dirname(os.path.abspath(__file__)) + '/tmd_'

def align(n:int,blocksize:int):  return -n % blocksize
def clamp(n:int,max:int):
    if n > max: return max
    return n

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

def check_sha1(f:str,hsh:bytes):
    f = open(str(f),'rb')
    sh1 = sha1()
    while True:
        p = f.read(0x4000)
        if not p: break
        sh1.update(p)
    f.close()

    return sh1.digest() == hsh
def decrypt_content(inf:str,ouf:str,key:bytes,tmdc:'TMD.TMDContent'):
    i,o = open(inf,'rb'),open(str(ouf),'wb')

    aes = AES.new(key,AES.MODE_CBC,tmdc.index.to_bytes(2,'big') + b'\0'*14)
    tln = 0

    p = d = b''
    while True:
        p = i.read(64*100)
        if not p: break
        if len(p) % 64 != 0: p += b'\0' * align(len(p),64)
        d = aes.decrypt(p)
        tln += len(d)
        if tln > tmdc.size: d = d[:tmdc.size - tln]
        o.write(d)
    i.close()
    o.close()

def secret(start:int,length:int):
    ret = b""
    add = start + length

    for _ in range(length):
        ret += struct.pack('>q',start)[-1:]
        start,add = start + add,start

    return ret
def get_pwd(i:bytes|str|int) -> bytes:
    if type(i) == int:
        if i > len(PWDS): i = -1
        i = PWDS[i]
    if type(i) == str: i = i.encode()
    return i
def derive_key(tid:str|bytes,pwd:str|bytes|int):
    if type(tid) == str: tid = bytes.fromhex(tid)
    tid = tid.lstrip(b'\0') or b'\0'

    return pbkdf2_hmac('sha1',get_pwd(pwd),md5(SECRET + tid).digest(),20,16)
def encrypt_key(tid:str|bytes,key:bytes,ckey:bytes) -> bytes:
    assert AES
    if type(tid) == str: tid = bytes.fromhex(tid)
    tid = tid.rjust(16,b'\0')

    return AES.new(key=ckey, mode=AES.MODE_CBC, IV=tid).encrypt(key)
def get_encrypted_key(tid:str|bytes,pwd:str|bytes|int,ckey:bytes):
    return encrypt_key(tid,derive_key(tid,pwd),ckey)

SECRET = secret(-3,10)
PWDS = [
    b'mypass',
    b'nintendo',
    b'test',
    b'1234567890',
    b'Lucy131211',
    b'fbf10',
    b'5678',
    b'1234',
    b'',
    b'mypass'
]

class Signature(File):
    def __init__(self,f:File):
        super().__init__(f)

        self.type = f.readu32()
        match self.type:
            case 0x010000 | 0x010003: d,p = 0x200,0x3C
            case 0x010001 | 0x010004: d,p = 0x100,0x3C
            case 0x010002 | 0x010005: d,p = 0x3C ,0x40
            case _: raise Exception(f'Unknown signature type: {self.type}')
        self.value = f.read(d)
        self.padding = f.read(p)

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)

class Certificate(File):
    def __init__(self,f:File):
        super().__init__(f)
        self.signature = Signature(self)

        self.issuer = self.read(0x40)
        self.key_type = self.readu32()
        self.name = self.read(0x40)
        self.unknown1 = self.readu32()

        match self.key_type:
            case 0: d,e,p = 0x200,1,0x34
            case 1: d,e,p = 0x100,1,0x34
            case 2: d,e,p = 0x3C ,0,0x3C
            case _: raise Exception(f'Unknown key type: {self.key_type}')
        self.modulus = self.read(d)
        if e: self.exponent = self.readu32()
        self.padding = self.read(p)

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)

class Ticket(File):
    def __init__(self,f:File):
        super().__init__(f)

        self.signature = Signature(self)

        self.issuer = self.read(0x40)
        self.ecdhdata = self.read(0x3C)
        self.unused1 = self.read(3)
        self.titlekey = self.read(0x10)
        self.unknown1 = self.read(1)
        self.ticketid = self.read(8)
        self.consoleid = self.read(4)
        self.titleid = self.read(8)
        self.unknown2 = self.read(2)
        self.titleversion = self.readu16()
        self.permitted_titles_mask = self.readu32()
        self.permit_mask = self.readu32()
        self.export_allowed = self.readu8()
        self.ckeyindex = self.readu8()
        self.unknown3 = self.read(0x30)
        self.content_access_permissions = self.read(0x40)
        self.padding = self.read(2)
        self.limits = self.read(0x40)

        self.certificates:list[Certificate] = []
        for _ in range(2):
            self.certificates.append(Certificate(self))

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)
class NTicket(File):
    def __init__(self,system:str,key:bytes,ckeyidx:int,tmd:'TMD'):
        super().__init__(io.BytesIO())

        bcetk = Ticket(BASED + system + '/cetk')
        self.write(bcetk.signature.data)
        self.write(bcetk.issuer)
        self.write(bcetk.ecdhdata)
        self.write(bcetk.unused1)
        self.write(key)
        self.write(bcetk.unknown1)
        self.write(bcetk.ticketid)
        self.write(bcetk.consoleid)
        self.write(tmd.titleid)
        self.write(bcetk.unknown2)
        self.writeu16(tmd.titleversion)
        self.writeu32(bcetk.permitted_titles_mask)
        self.writeu32(bcetk.permit_mask)
        self.writeu8(bcetk.export_allowed)
        self.writeu8(ckeyidx)
        self.write(bcetk.unknown3)
        self.write(bcetk.content_access_permissions)
        self.write(b'\0'*2)
        self.write(bcetk.limits)

        for c in bcetk.certificates: self.write(c.signature.data)
        self.certificates = bcetk.certificates

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)

class TMD(File):
    class TMDContent(File):
        def __init__(self,f:File):
            super().__init__(f)

            self.cid = self.readu32()
            self.index = self.readu16()
            self.type = self.readu16()
            self.size = self.readu64()
            self.sha1 = self.read(20)

            self.update_size()
            self.seek(0)
            self.data = self.read(self._size)

    def __init__(self,f,mode='r'):
        super().__init__(f,mode)

        self.signature = Signature(self)

        self.issuer = self.read(64)
        self.version = self.readu8()
        self.ca_crl_version = self.readu8()
        self.signer_crl_version = self.readu8()
        self.is_vwii = self.readu8()
        self.system_version = self.read(8)
        self.titleid = self.read(8)
        self.type = self.readu32()
        self.group_id = self.readu16()
        self.zero1 = self.read(2)
        self.region = self.readu16()
        self.ratings = self.read(16)
        self.reserved1 = self.read(12)
        self.ipc_mask = self.read(12)
        self.reserved2 = self.read(18)
        self.access_rights = self.readu32()
        self.titleversion = self.readu16()
        self.contentcount = self.readu16()
        self.bootindex = self.readu16()
        self.minor_version = self.read(2)

        self.contents:list[TMD.TMDContent] = []
        for _ in range(self.contentcount): self.contents.append(self.TMDContent(self))

        self.certificates:list[Certificate] = []
        for _ in range(2):
            self.certificates.append(Certificate(self))

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)
