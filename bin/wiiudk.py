import os,re

__db__ = os.path.join(os.path.dirname(__file__),'wiiudk.bdb')
RFMT = re.compile(r'\((\w\w,)*\w\w\)')

class DKeys:
    def __init__(self):
        self.db = {}
        bdb = open(__db__,'rb')
        while True:
            ln = bdb.read(1)
            if not ln: break
            nm = bdb.read(ln[0]).decode()
            self.db[nm] = bdb.read(16).hex()
        bdb.close()
    def get(self,k:str):
        k = fmt(os.path.splitext(os.path.basename(k))[0])
        return self.db.get(k)

def fmt(i:str):
    nm = RFMT.sub('',i.lower())
    return ''.join(x for x in nm if x.isalnum())[:0xFF]
def makedb(quiet=True):
    import httpx

    fs = httpx.get('https://www.allmyroms.net/wiiu/keys.txt').text.strip().split('\n')
    o = open(__db__,'wb')
    for f in fs:
        k,n = f.split('#',1)
        n = fmt(n).encode()
        o.write(len(n).to_bytes(1,'little'))
        o.write(n)
        o.write(bytes.fromhex(k.strip()))
    o.close()

if __name__ == '__main__':
    makedb()
