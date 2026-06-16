import os,zlib,time
from lib.crypto import HASHTS,asrt,crc_hash
from lib.file import File
from threading import Thread

class HashLibOld:
    def __init__(self,p:str,fmt=None,encoding='utf-8'):
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
            asrt(os.path.isfile(self.p))
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
        ks = [f.readi(self.hs) for _ in range(c)]
        d = b'\x78\xDA' + f.read()
        f.close()
        vs = [x.decode(self.enc) for x in zlib.decompress(d).split(b'\0')]
        db = zip(ks,vs)
        self.lhsh = hash(db)
        self.db = dict(db)

    def save(self):
        ks = list(self.db.keys())
        vs = list(self.db.values())
        nhsh = hash(zip(ks,vs))
        if self.lhsh == nhsh: return

        f = File(self.p,'wb',endian='>')
        ts = int(time.time()*100)
        f.writeu48(ts)
        f.write(self.ht.encode(self.enc) + b'\0')
        f.writevlq(len(ks))

        for k in ks: f.writei(k,self.hs)
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

if __name__ == '__main__':
    import time
    from lib.dldb import DLDB
    from lib.crypto import HashLib

    db = DLDB()
    fmt = None

    n = 'rsdk'
    enc = 'utf-8'
    def fmt(i):return i.lower()

    st = time.time()
    h = HashLibOld.dl(n,db,fmt=fmt,encoding=enc).loadb()
    et = time.time() - st
    print('Entries:',len(h.db))
    print('Old load:',et)
    print('Old size:',os.path.getsize(h.p))
    st = time.time()
    b = HashLib.new(n + '.pyob',h.ht,h.enc,h.fmt)
    b.add(h.db.values())
    b.save()
    print('New create:',time.time() - st)

    st = time.time()
    b = HashLib(n + '.pyob').loadb()
    print('New load:',time.time() - st)
    print('New size:',os.path.getsize(b.p))
    print(b.fmt.source)
    if b.obj == h.db: print('Yay :D')
    else:
        print('!!!!!')
        c = 0
        for k in h.db:
            if c > 10: break
            c += 1
            if not k in b:
                print(f'{k:0{h.hs*2}X} | {h[k]}')
            elif b[k] != h[k]:
                print(f'{k:0{h.hs*2}X} | {h[k]} | {b[k]}')
            else: c -= 1
