import os

__db__ = os.path.join(os.path.dirname(__file__),'sgkeys.bdb')

TIDL = (
    "611",
    "840",
    "841",
    "842",
    "834",
    "GDS",
    "GDT",
    "GDX",
    "GDL",
    "CDV",
    "CDP",
)
TID1 = (
    "834",
    "CDV",
    "CDP",
)
TIDF = (
    "842",
)
TIDB = (
    "834",
)

class SGKeys:
    def __init__(self,t:str=None):
        self.t = t
        self.load()
    def load(self):
        if not os.path.exists(__db__): makedb()

        i = open(__db__,'rb')
        self._db = {}
        while True:
            t = i.read(1)
            if not t: break
            t = t.decode()
            tbid = i.read(1)[0]
            tbn = TIDL[tbid & 0x7F]
            if tbn in TIDF: id = tbn + '-' + i.read(8).decode()
            else:
                if tbn in TIDB: tid = int.from_bytes(i.read(2),'big')
                else: tid = i.read(1)[0]
                id = tbn + '-' + ('1' if tbn in TID1 else '') + str(tid).zfill(4)
                if tbid & 0x80: id += i.read(1).decode()
            ft = ({'L':'N','3':'2'}[t] if t in 'L3' else t)
            if not ft in self._db: self._db[ft] = {}
            self._db[ft][id] = i.read(4 if t in 'N2' else 8)
        i.close()

    def get(self,key:str,t:str=None) -> bytes|tuple[str,bytes]:
        t = t or self.t
        if os.path.exists(key):
            if os.path.isdir(key): key = os.path.join(key,'IP.BIN')
            assert os.path.exists(key) and os.path.isfile(key),key

            f = open(key,'rb')
            f.seek(0x40)
            key = f.read(10).lstrip(b' ').split(b' ')[0].decode()
            f.close()
        key = key.upper()
        if t == None:
            for t in self._db:
                v = self._db[t].get(key)
                if v: return t,v
            return None
        return self._db[t].get(key)
    def __getitem__(self,key): return self.get(key)

def makedb():
    import httpx,re
    TL = {
        "Naomi":           "N",
        "Naomi Multiboard":"N",
        "Naomi GD-ROM":    "N",
        "Naomi Satellite Terminal":"N",
        "Naomi 2":         "2",
        "Naomi 2 Satellite Terminal":"2",
        "Chihiro":         "C",
        "Chihiro GD-ROM":  "C",
        "Chihiro Satellite Terminal":"C",
        "Triforce":        "T",
        "Triforce GD-ROM": "T",
    }

    o = open(__db__,'wb')
    for t,tid,key in re.findall(r'<tr>\n<td>[^<]+</td>\n<td>[^<]*</td>\n<td>([^<]+)</td>\n(?:<td>.*</td>\n){8}<td>([A-Z\d]+\-[A-Z\d]+)</td>\n(?:<td>.*</td>\n){14}<td>(?:0x)?([A-Fa-f\d]{16}|[A-Fa-f\d]{8})</td>\n',httpx.get('https://www.citylan.it/index.php/Naomi_-_Chihiro_-_Triforce').text):
        if len(key) not in (8,16): continue
        if not t in TL:
            print(t,tid,'TL')
            continue
        if not '-' in tid: continue
        tbn,tidn = tid.split('-')
        if not tbn in TIDL:
            print(tid,'TIDL')
            continue
        t = TL[t]
        if t == 'N' and len(key) == 16: t = 'L'
        elif t == '2' and len(key) == 16: t = '3'
        o.write(t.encode())
        tidb = TIDL.index(tbn)
        if tbn in TIDF:
            o.write(bytes([tidb]))
            o.write(tidn.encode('ascii'))
        else:
            if tbn in TID1: tidn = tidn[1:]
            assert len(tidn) in (4,5),tid
            o.write(bytes([tidb | (0x80 if len(tidn) == 5 else 0)]))
            if tbn in TIDB: o.write(int(tidn[:4]).to_bytes(2,'big'))
            else:
                assert int(tidn[:4]) <= 0xFF,tid
                o.write(bytes([int(tidn[:4])]))
            o.write(tidn[4:].encode())
        o.write(bytes.fromhex(key))
    o.close()

if __name__ == '__main__':
    makedb()
