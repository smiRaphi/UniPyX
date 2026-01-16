import struct,io,os
from hashlib import pbkdf2_hmac,md5,sha1,sha256
from lib.file import File,align
_File = File

try: from Cryptodome.Cipher import AES # type: ignore
except ImportError: from Crypto.Cipher import AES # type: ignore

BASED = os.path.dirname(os.path.abspath(__file__)) + '/tmd_'

def clamp(n:int,max:int):
    if n > max: return max
    return n

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
        if i > len(PWDS): i = 0
        i = PWDS[i]
    if type(i) == str: i = i.encode()
    return i
def derive_key(tid:str|bytes,pwd:str|bytes|int):
    if type(tid) == str: tid = bytes.fromhex(tid)
    tid = tid.lstrip(b'\0') or b'\0'

    return pbkdf2_hmac('sha1',get_pwd(pwd),md5(SECRET + tid).digest(),20,16)
def encrypt_key(tid:str|bytes,key:bytes,ckey:bytes) -> bytes:
    if type(tid) == str: tid = bytes.fromhex(tid)
    tid = tid.rjust(16,b'\0')

    return AES.new(key=ckey,mode=AES.MODE_CBC,IV=tid).encrypt(key)
def decrypt_key(tid:str|bytes,key:bytes,ckey:bytes) -> bytes:
    if type(tid) == str: tid = bytes.fromhex(tid)
    tid = tid.rjust(16,b'\0')

    return AES.new(key=ckey,mode=AES.MODE_CBC,IV=tid).decrypt(key)
def get_encrypted_key(tid:str|bytes,pwd:str|bytes|int,ckey:bytes):
    return encrypt_key(tid,derive_key(tid,pwd),ckey)

def rol(v:int,r:int,m=128) -> int: return (v << r % m) & (2 ** m - 1) | ((v & (2 ** m - 1)) >> (m - (r % m)))
def unscramble_3ds(x:bytes|int,y:bytes|int,g:bytes|int):
    if type(x) == bytes: x = int.from_bytes(x,'big')
    if type(y) == bytes: y = int.from_bytes(y,'big')
    if type(g) == bytes: g = int.from_bytes(g,'big')

    return rol((rol(x,2) ^ y) + g,87).to_bytes(16,'big')

SECRET = secret(-3,10)
PWDS = [
    b'mypass',
    b'nintendo',
    b'password',
    b'',
    b'test',
    b'1234567890',
    b'Lucy131211',
    b'fbf10',
    b'5678',
    b'1234',
    b'56789',
    b'redsst',
    b'd4t4c3nt3r',
    b'datacenter',
    b'0',
    b'0000',
    b'5037',
    b'nintedno',
]

class File(_File):
    def __init__(self,f):
        super().__init__(f,'rb','>')
        self.init()

class Signature(File):
    def init(self):
        self.type = self.readu32()
        match self.type:
            case 0x010000 | 0x010003: d,p = 0x200,0x3C
            case 0x010001 | 0x010004: d,p = 0x100,0x3C
            case 0x010002 | 0x010005: d,p = 0x3C ,0x40
            case _: raise Exception(f'Unknown signature type: {self.type:X}')
        self.value = self.read(d)
        self.padding = self.read(p)

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)

class Certificate(File):
    def init(self):
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
    def init(self):
        self.signature = Signature(self)

        self.issuer = self.read(0x40)
        self.ecdhdata = self.read(0x3C)
        self.version = self.readu8()
        self.ca_crl_version = self.readu8()
        self.signer_crl_version = self.readu8()
        self.titlekey = self.read(0x10)
        self.reserved1 = self.read(1)
        self.ticketid = self.read(8)
        self.consoleid = self.read(4)
        self.titleid = self.read(8)
        self.reserved2 = self.read(2)
        self.titleversion = self.readu16()
        self.permitted_titles_mask = self.readu32()
        self.permit_mask = self.readu32()
        self.export_allowed = self.readu8()
        self.ckeyindex = self.readu8()
        self.reserved3 = self.read(0x2A)
        self.eshop_acc_id = self.read(4)
        self.reserved4 = self.readu8()
        self.audit = self.readu8()
        self.content_access_permissions = self.read(0x40)
        self.reserved5 = self.read(2)
        self.limits = self.read(0x40)

        if self.version == 1:
            self.skip(4)
            self.content_index_size = self.readu32()
            self.skip(-8)
            self.content_index_data = self.read(self.content_index_size)

        self.certificates:list[Certificate] = []
        for _ in range(2): self.certificates.append(Certificate(self))

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)

        self._key = None
    def get_key(self):
        if not self._key: self._key = decrypt_key(self.ticketid,self.titlekey,self.ckey)
        return self._key
class NTicket(_File):
    def __init__(self,system:str,key:bytes,ckeyidx:int,tmd:'TMD'):
        super().__init__(io.BytesIO(),'wb','>')

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
        def init(self):
            self.cid = self.readu32()
            self.index = self.readu16()
            self.type = self.readu16()
            self.csize = self.readu64()
            self.sha = self.read((20,0x20)[self._f.version])

            self.update_size()
            self.seek(0)
            self.data = self.read(self._size)
    class TMDInfo(File):
        def init(self):
            self.cid = self.readu16()
            self.ccc = self.readu16()
            self.sha256 = self.read(0x20)

            self.update_size()
            self.seek(0)
            self.data = self.read(self._size)

    def init(self):
        self.signature = Signature(self)
        self.sigt = self.signature.type & 0xFF

        self.issuer = self.read(0x40)
        self.version = self.readu8()
        self.ca_crl_version = self.readu8()
        self.signer_crl_version = self.readu8()
        self.is_vwii = self.readu8()
        self.system_version = self.read(8)
        self.titleid = self.read(8)
        self.type = self.readu32()
        self.group_id = self.readu16()
        if self.version == 1:
            self.save_data_size = self.readu32('<')
            self.srl_private_sizee = self.readu32('<')
            self.reserved1 = self.read(4)
            self.srl_flag = self.readu8()
            self.reserved2 = self.read(0x31)
        else:
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

        if self.version == 1:
            self.sha256 = self.read(0x20)
            self.content_info = [TMD.TMDInfo(self) for _ in range(0x40)]

        self.contents:list[TMD.TMDContent] = []
        for _ in range(self.contentcount): self.contents.append(self.TMDContent(self))

        self.certificates:list[Certificate] = []
        for _ in range(2): self.certificates.append(Certificate(self))

        self.update_size()
        self.seek(0)
        self.data = self.read(self._size)

    def check_file(self,f:str,hsh:bytes):
        f = open(str(f),'rb')
        sh = (sha1,sha256)[self.version]()
        while True:
            p = f.read(0x4000)
            if not p: break
            sh.update(p)
        f.close()

        return sh.digest() == hsh
