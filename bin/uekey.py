GUIDs = {}
LUIDs = set()
LUT = 1776344000

import os,time

__db__ = os.path.join(os.path.dirname(__file__),'uekeys.bdb')

class UEKeys:
    def __init__(self): self.load()
    def load(self):
        if not os.path.exists(__db__): makedb()

        i = open(__db__,'rb')
        ot = int.from_bytes(i.read(6),'big')
        if time.time() - ot > (60*60*24*7*3) or ot < LUT:
            i.close()
            makedb()
            i = open(__db__,'rb')
            i.seek(6)

        lc = int.from_bytes(i.read(4),'big')
        self.ldb = set([i.read(0x20) for _ in range(lc)])

        self.db:dict[int,tuple[bytes,...]] = {}
        while True:
            idc = i.read(1)
            if not idc: break
            ids = [int.from_bytes(i.read(0x10),'big') for _ in range(idc[0])]
            k = i.read(0x20)
            for id in ids: self.db[id] = k
        i.close()

    def get(self,guid:bytes|int):
        if type(guid) == bytes:
            if len(guid) != 0x10: raise ValueError(f'0x{len(guid):02X} != 0x10')
            guid = int.from_bytes(guid,'big')
        return self.db[guid]
    def __iter__(self): return iter(self.ldb)
    def __contains__(self,item): return item in self.db

def makedb():
    import httpx,re,base64
    from html import unescape

    B64C = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    u = 'https://cs.rin.ru/forum/viewtopic.php?f=10&t=100672'
    s = httpx.get(u)
    if s.status_code == 401: s = httpx.get(u,cookies={x[0]:x[1] for x in re.findall(r'document\.cookie *= *"([^=]+)=([^;]+);',s.text)})
    s = s.text.replace('&nbsp;',' ').replace('\xa0',' ')

    ks = {}
    lks = []
    for m in re.findall(r'"li[12]">([^<>]{45,})</li>',s):
        if not ' ' in m: continue
        n,k = unescape(m).strip().rsplit(' ',1)
        n,k = re.sub(r' +',' ',n.strip().lower().replace(':',' ')),k.strip()
        if n == 'princess peach showtime (demo)': n = 'princess peach showtime'

        if len(k) == 66 and k.startswith('0x') and all(c in '0123456789abcdef' for c in k[2:].lower()): k = bytes.fromhex(k[2:])
        elif len(k) == 64 and all(c in '0123456789abcdef' for c in k.lower()): k = bytes.fromhex(k)
        elif len(k) == 44 and k[-1] == '=' and all(c in B64C for c in k[:-1]): k = base64.b64decode(k)
        elif len(k) == 43 and all(c in B64C for c in k): k = base64.b64decode(k + '=')
        else:
            #print(unescape(m).encode('latin1'),'|' + n + '|' + k + '|')
            continue
        if len(k) != 0x20: raise ValueError(f'0x{len(k):02X} != 0x20')

        if n in GUIDs:
            if not k in ks: ks[k] = []
            for id in GUIDs[n]: ks[k].append(id.to_bytes(0x10,'big') if type(id) == int else id)
            if id in LUIDs: lks.append(k)
        else: lks.append(k)

    o = open(__db__,'wb')
    o.write(int(time.time()).to_bytes(6,'big'))
    lks = set(lks)
    o.write(len(lks).to_bytes(4,'big'))
    o.write(b''.join(lks))
    for k,ids in ks.items():
        ids = list(set(ids))
        o.write(len(ids).to_bytes(1))
        o.write(b''.join(ids))
        o.write(k)

    o.close()

if __name__ == '__main__':
    makedb()
