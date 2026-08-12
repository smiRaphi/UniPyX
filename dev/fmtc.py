import ast,re
from math import ceil

d = open('c.h').read()
u0x = '0x' in d
lng = 16 if 'L' in d else 8
COLC = 4 if lng == 16 else 8
#d = [int(x,16) for x in re.findall(r'0x([A-F\d]{8})',d)]
#d = [int(x) for x in re.findall(r'\bX(\d[\d ]),',d)]
d = ast.literal_eval('[' + d.replace('L','') + ']')

for x in range(ceil(len(d) / COLC)):
    c = []
    for y in d[x*COLC:(x+1)*COLC]:
        if u0x: c.append(f'0x{y:0{lng}X}')
        else: c.append(f'{y:<2}')
    print(' '*4 + ','.join(c) + ',')
print(f'0x{len(d):02X}')
