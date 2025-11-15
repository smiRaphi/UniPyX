import os,re
from base64 import b64decode

__db__ = os.path.join(os.path.dirname(__file__),'xb1keys.bdb')

class XB1Keys:
    def __init__(self): self.load()
    def load(self):
        self.changed = False
        self.db = {}
        self.rodk = None
        self.godk = None
        if not os.path.exists(__db__):
            self.makedb()
            return

        i = open(__db__,'rb')
        self.rodk = i.read(32) if i.read(1)[0] else None
        self.godk = i.read(32) if i.read(1)[0] else None
        while True:
            k = i.read(16)
            if not k: break
            self.db[k] = i.read(32)
        i.close()
    def save(self):
        o = open(__db__,'wb')
        if self.rodk: o.write(b'\1' + self.rodk)
        else: o.write(b'\0')
        if self.godk: o.write(b'\1' + self.godk)
        else: o.write(b'\0')
        for k in self.db: o.write(k + self.db[k])
        o.close()

    def makedb(self):
        import httpx

        s = httpx.get('https://www.psdevwiki.com/ps3/User_talk:Zecoxao',headers={'user-agent':os.urandom(8).hex()}).text.replace('\r','')

        rodk = re.search(r'(?i)RedOdk\.odk"><span>edit source</span>.+\n<pre>([a-f\d \n]+)</pre>',s)
        assert rodk
        if rodk: self.add(bytes.fromhex(rodk[1]),odk='red')

        godk = re.search(r'(?i)GreenOdk\.odk"><span>edit source</span>.+\n<pre>([a-f\d \n]+)</pre>',s)
        if godk: self.add(bytes.fromhex(godk[1]),odk='green')

        for k in re.findall(r'(?i)[a-f\d]{8}(?:-[a-f\d]{4}){4}[a-f\d]{8}\.cik"><span>edit source</span>.+\n<pre>([a-f\d \n]+)</pre>',s):
            self.add(bytes.fromhex(k))

        self.save()

    def add(self,k:bytes,odk=None):
        self.changed = True

        if odk:
            if odk == 'red': self.rodk = k[:32]
            elif odk == 'green': self.godk = k[:32]
        else: self.db[k[:16]] = k[16:48]
    def add_license(self,path:str):
        assert os.path.exists(path) and os.path.isfile(path),path
        xml = open(path,encoding='utf-8').read()
       
        lif = b64decode(getxv(xml,"SignedLicense")).decode()
        kid = getxv(lif,"KeyId")
        kh = b64decode(getxv(xml,"SigningKeyHash"))
        self.add(guid2bytes(kid) + kh)
    def get(self,i:str|bytes) -> bytes|None:
        if i == 'redodk': return self.rodk
        if i == 'greenodk': return self.godk

        if type(i) == str: i = guid2bytes(i)
        r = self.db.get(i)
        if r: r = i + r
        return r

    def __contains__(self,i): return not self.get(i) is None
    def __del__(self):
        if self.changed: self.save()

def getxv(xml:str,key:str,idx=0): return xml.split(f'<{key}>')[idx+1].split('<')[0]
def guid2bytes(i:str):
    if '-' in i: return b''.join(x[::-1] if ix < 3 else x for ix,x in enumerate([bytes.fromhex(x) for x in i.split('-')]))
    return bytes.fromhex(i)
