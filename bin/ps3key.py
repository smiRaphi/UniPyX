import os,re

__db__ = os.path.join(os.path.dirname(__file__),'ps3keys.bdb')

class PS3Keys:
    def __init__(self):
        self.load()
    def load(self):
        i = open(__db__,'rb')
        self._db = {}
        while True:
            sln = i.read(1)
            if not sln: break
            nm = i.read(sln[0]).decode()
            self._db[nm] = i.read(16).hex().upper()

    def get(self,key:str) -> str|None:
        if os.path.exists(key) or '\\' in key or '/' in key:
            if not os.path.isdir(key) or key.endswith('.iso'): key = os.path.splitext(os.path.basename(key))[0]
            else: key = os.path.basename(key)
        key = fmt(key)
        return self._db.get(key)
    def __getitem__(self,key): return self.get(key)

def fmt(i:str): return ''.join(x for x in re.sub(r'\(\w\w,[\w,]+\)','',i.lower()) if x.isalnum())
def makedb(dr:str,out:str):
    o = open(out,'wb')
    p = nm = ''
    for x in os.listdir(dr):
        if not x.endswith('.dkey'): continue
        print(x)
        p = os.path.join(dr,x)
        nm = fmt(x[:-5]).encode()
        assert len(nm) <= 0xff,f"Name too long {nm}"
        o.write(len(nm).to_bytes(1,'little'))
        o.write(nm)
        o.write(bytes.fromhex(open(p).read().strip()))
    o.close()

if __name__ == '__main__':
    from sys import argv

    if len(argv) > 1: dr = argv[1]
    else: dr = 'ps3keys'
    if len(argv) > 2: out = argv[2]
    else: out = __db__
    try: makedb(dr,out)
    except Exception as e: input(e)
