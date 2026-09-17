import ast,re
from math import ceil

CREG = re.compile(r'(?s)/(/[^\n]*|\*.*?\*/)')

def parsec(d:str) -> tuple[tuple[int],int,bool]:
    d = CREG.sub('',d).strip('{}()[]; \n\r\t=').replace('L','').replace('U','')
    l = 16 if 'L' in d else 8
    u0x = '0x' in d

    #d = [int(x,16) for x in re.findall(r'0x([A-F\d]{8})',d)]
    #d = [int(x) for x in re.findall(r'\bX(\d[\d ]),',d)]
    d = ast.literal_eval('(' + d + ')')
    return d,l,u0x
def fmtl(d:tuple[int]|list[int],l:int=None,u0x:bool=None,c:int=None):
    if u0x is None: u0x = any(x >= 0x10 for x in d)
    if l is None:
        if u0x: l = max(ceil(x.bit_length() / 4) for x in d)
        else: l = max(len(str(x)) for x in d)
    if c is None:
        if l == 16: c = 4
        elif l == 8: c = 8
        elif l == 2: c = 16
        elif len(d) < 16: c = len(d)
        else: c = 8
    if c < 1: c = len(d)

    o = []
    for x in range(ceil(len(d) / c)):
        col = []
        for y in d[x*c:(x+1)*c]:
            if u0x: col.append(f'0x{y:0{l}X}')
            else: col.append(f'{y:<{l}d}')
        o.append(' '*4 + ','.join(col) + ',')
    return '\n'.join(o) + f'\n0x{len(d):02X}'

if __name__ == '__main__':
    from sys import argv
    if len(argv) > 1:
        i = argv[1]
        with open(i,'rt',encoding='utf-8') as f: d = f.read()
    else:
        d = ''
        while True:
            inp = input(': ')
            if not inp: break
            d += inp + '\n'

    print(fmtl(*parsec(d)))
