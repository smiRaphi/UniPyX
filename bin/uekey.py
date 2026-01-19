import os,time
from hashlib import sha3_256

__db__ = os.path.join(os.path.dirname(__file__),'uekeys.bdb')

class UEKeys:
    def __init__(self): self.load()
    def load(self):
        if not os.path.exists(__db__): makedb()

        i = open(__db__,'rb')
        ot = int.from_bytes(i.read(6),'big')
        if time.time() - ot > (60*60*24*7*3):
            i.close()
            makedb()
            i = open(__db__,'rb')
            i.seek(6)

        self.db:dict[str,tuple[bytes,tuple[bytes,...]]] = {}
        while True:
            nl = i.read(1)
            if not nl: break
            n = i.read(nl[0]).decode('utf-8')
            hl = i.read(1)[0]
            hs = [i.read(0x20) for _ in range(hl)]
            self.db[n] = (i.read(0x20),hs)
        i.close()

    def get(self,f:str):
        if f in self.db: return self.db[f][0]
        assert os.path.exists(f) and os.path.isfile(f)
        h = sha3_256(open(f,'rb').read(0x500)).digest()
        for k in self.db:
            if h in self.db[k][1]: return self.db[k][0]
        return None

def makedb():
    import httpx,re,base64
    from html import unescape

    B64C = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    u = 'https://cs.rin.ru/forum/viewtopic.php?f=10&t=100672'
    s = httpx.get(u)
    if s.status_code == 401: s = httpx.get(u,cookies={x[0]:x[1] for x in re.findall(r'document\.cookie *= *"([^=]+)=([^;]+);',s.text)})
    s = s.text.replace('&nbsp;',' ').replace('\xa0',' ')

    o = open(__db__,'wb')
    o.write(int(time.time()).to_bytes(6,'big'))
    dn = []
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
            #print(unescape(m).encode('latin-1'),'|' + n + '|' + k + '|')
            continue

        if n in dn: continue
        dn.append(n)

        dx = []
        if n == 'princess peach showtime': dx.append("9FAD1D4A12CFE3AE4C4B36A8DDE24D906781F71387D217AC3FB0C7AD5016CAAC")

        assert len(dx) < 0x100
        n = n.encode('utf-8')
        assert len(n) < 0x100
        o.write(len(n).to_bytes(1,'big') + n + len(dx).to_bytes(1,'big') + b''.join(bytes.fromhex(x) for x in dx) + k)
    o.close()

if __name__ == '__main__':
    makedb()
