import os,re

__db__ = os.path.join(os.path.dirname(__file__),'ps3keys.bdb')

class PS3Keys:
    def __init__(self):
        self.load()
    def load(self):
        if not os.path.exists(__db__): makedb()

        i = open(__db__,'rb')
        self._db = {}
        while True:
            id1 = i.read(4)
            if not id1: break
            zs = i.read(1)[0]
            nm = id1.decode() + '0'*zs + str(int.from_bytes(i.read(3),'little'))
            self._db[nm] = i.read(16).hex().upper()
        i.close()

    def get(self,key:str) -> str|None:
        assert os.path.exists(key) and os.path.isfile(key)
        f = open(key,'rb')
        f.seek(0x800)
        assert f.read(12) == b'PlayStation3'
        f.seek(4,1)
        key = f.read(0x20).strip().decode().replace('-','')

        return self._db.get(key) or self.__db['TEST01814']
    def __getitem__(self,key): return self.get(key)

def makedb():
    import httpx

    ks = re.findall(r'">(\w*)</a><TD>.+<TD>([A-Fa-f\d]*)</TR>',httpx.get('https://ps3.aldostools.org/dkey.html',verify=False).text)

    o = open(__db__,'wb')
    for i,k in ks:
        if not i: continue
        o.write(i[:4].encode())
        o.write((len(i[4:])-len(i[4:].lstrip('0'))).to_bytes(1,'little'))
        o.write(int(i[4:]).to_bytes(3,'little'))
        o.write(bytes.fromhex(k) if k else b'\0'*16)
    o.close()

if __name__ == '__main__':
    makedb()
