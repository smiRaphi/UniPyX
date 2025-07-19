import os,re

DB = os.path.join(os.path.dirname(__file__),'wiiudk.bdb')
REG = [
    'unk', # Unknown
    'usa', # USA
    'eur', # Europe
    'jpn', # Japan
    'rus', # Russia
    'kor', # Korea
]

REVM = re.compile(r'[\(\[]rev ?(\d+)[\)\]]')

class DKeys:
    def __init__(self):
        self.db = {}
        bdb = open(DB,'rb')
        while True:
            ln = bdb.read(1)
            if not ln: break
            nm = bdb.read(ln[0]).decode()
            nm += '-' + REG[bdb.read(1)[0]]
            rev = bdb.read(1)[0]
            if rev: nm += f'+{rev}'
            self.db[nm] = bdb.read(16).hex()
        bdb.close()
    def get(self,k):
        nk = fmt(os.path.splitext(os.path.basename(k))[0])
        if not nk in self.db and '+' in nk: nk = nk.split('+')[0]
        return self.db.get(nk)

def fmt(i:str):
    i = i.lower()
    nm = re.sub(r'\(\w\w,[\w,]+\)','',re.sub(r'\[.*\]','',i))
    reg = 'unk'
    for cn,cc in [
        ('usa','usa'),('canada','usa'),
        ('japan','jpn'),
        ('europe','eur'),('germany','eur'),('france','eur'),('italy','eur'),('spain','eur'),('uk','eur'),('australia','eur'),
        ('russia','rus'),
        ('korea','kor'),
        ('russia','rus'),
        ('unknown','unk'),
    ]:
        cn = f'({cn})'
        if cn in i:
            reg = cc
            nm = nm.replace(cn,'')
            break
    else:
        if i.endswith(']') and len(i.split('[')[-1]) == 3: reg = {'eu':'eur','us':'usa','jp':'jpn','kr':'kor','ru':'rus','un':'unk'}[i.split('[')[-1][:-1].lower()]

    rev = ''
    rm = REVM.search(i)
    if rm:
        if rm[1] != '0': rev = '+' + rm[1]
        nm = REVM.sub('',nm)

    return ''.join(x for x in nm if x.isalnum()) + '-' + reg + rev

if __name__ == '__main__':
    from sys import argv
    ks = open(argv[1] if len(argv) > 1 else 'keys.txt',encoding='utf-8').read()
    kp = []
    for x in ks.split('\n'):
        if not x or x.startswith(('#',' ')) or not '[' in x:continue
        i = [bytes.fromhex(x.split('#')[0].strip()),None,'UNK',0]
        n,tg = x.split('#',1)[1].strip().rsplit(' [',1)
        i[1] = ''.join(c for c in n.lower() if c.isalnum())
        tg = tg.split(',')[0].lower()
        i[2] = tg[:3]
        if 'rev' in tg: i[3] = int(re.search(r'rev ?(\d+)',tg)[1])
        kp.append(i)

    o = open(DB,'wb')
    for x in kp:
        en = x[1].encode()
        o.write(len(en).to_bytes(1,'little'))
        o.write(en)
        o.write(REG.index(x[2]).to_bytes(1,'little'))
        o.write(x[3].to_bytes(1,'little'))
        o.write(x[0])
        
    o.close()
