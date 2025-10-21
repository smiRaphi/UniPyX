import os

__db__ = os.path.join(os.path.dirname(__file__),'chkeys.bdb')

class CHKeys:
    def __init__(self): self.load()
    def load(self):
        if not os.path.exists(__db__): makedb()

        i = open(__db__,'rb')
        self._db = {}
        while True:
            sid = i.read(1)
            if not sid: break
            pid = i.read(1)[0]
            id = ('GDX-','611-','CDV-1','CDP-1')[sid[0]] + str(pid & 0x7F).zfill(4)
            if pid & 0x80: id += i.read(1).decode()
            self._db[id] = i.read(8)
        i.close()

    def get(self,key:str) -> bytes:
        if os.path.exists(key):
            if os.path.isdir(key): key = os.path.join(key,'IP.BIN')
            assert os.path.exists(key) and os.path.isfile(key),key

            f = open(key,'rb')
            f.seek(0x40)
            key = f.read(10).lstrip(b' ').split(b' ')[0].decode()
            f.close()
        return self._db.get(key.upper())
    def __getitem__(self,key): return self.get(key)

def makedb():
    import httpx,re

    o = open(__db__,'wb')
    for sid,id,key in re.findall(r'<tr>\n(?:<td>.*</td>\n){2}<td>Chihiro.*</td>\n(?:<td>.*</td>\n){8}<td>(CD[VP]-1|[A-Z\d]{3}-)([A-Z]?\d{4}[A-Z]?)</td>\n(?:<td>.*</td>\n){14}<td>([A-Fa-f\d]{16})</td>\n',httpx.get('https://www.citylan.it/index.php/Naomi_-_Chihiro_-_Triforce').text):
        assert len(id) <= 5
        pid = int(id[:4])
        assert pid < 0x80
        if len(id) == 5: pid |= 0x80
        o.write(bytes([('GDX-','611-','CDV-1','CDP-1').index(sid),pid]) + id[4:].encode() + bytes.fromhex(key))
    o.close()

if __name__ == '__main__':
    makedb()
