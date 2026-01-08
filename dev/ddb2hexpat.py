import json,ast

inp = ''
while True:
    i = input(': ')
    if not i: break
    inp += i + '\n'

OFF = 0

def coff(i:int,l=0):
    global OFF

    if abs(i) < 0x10: si = str(abs(i))
    else: si = f'0x{abs(i):X}'

    if i < 0: return f' @ (sizeof($)-{si})'
    if OFF == i:
        OFF += l
        return ''
    return ' @ ' + si

inp = json.loads('[[' + inp.strip(' \t\n\r,[]') + ']]')
o = 'struct DDB {\n'
for x,i in enumerate(inp):
    if i[0] == 'isat':
        rv = ast.literal_eval('"""' + i[1].replace('"','\\"') + '"""').encode('latin1')
        o += f'\tchar {i[0]}_{x}[{len(rv)}]{coff(i[2],len(rv))}; // {i[1]}\n'
    elif i[0] == 'isatS':
        rv = ast.literal_eval('"""' + i[1].replace('"','\\"') + '"""').encode('latin1')
        o += f'\tchar {i[0]}_{x}[{len(rv)*i[2]}]{coff(i[3],len(rv)*i[2])}; // {i[1]}\n'
    elif i[0] == 'isin':
        rv = ast.literal_eval('"""' + i[1][0].replace('"','\\"') + '"""').encode('latin1')
        o += f'\tchar {i[0]}_{x}[{len(rv)}]{coff(i[2],len(rv))}; // {i[1]}\n'
    elif i[0] == 'str':
        o += f'\tchar {i[0]}_{x}[{i[2]}]{coff(i[1],i[2])};\n'
    elif i[0] in ('str0','str0e','str0nv'):
        o += f'\tchar {i[0]}_{x}[{i[2]}]{coff(i[1],i[2])}; {i[3]}\n'
    elif i[0] == 'n0':
        o += '\tu'
        if i[1] in (1,2,3,4,6,8,12,16): o += f'{i[1]*8} {i[0]}_{x}'
        else: o += f'8 {i[0]}_{x}[{i[1]}]'
        o += f'{coff(i[2],i[1])}\n'
    elif i[0] == 'py':
        if not (",'little')" in i[1] and ",'big')" in i[1]):
            if ",'little')" in i[1]: o = '#pragma endian little\n\n' + o
            elif ",'big')" in i[1]: o = '#pragma endian big\n\n' + o
o += '};\nDDB DDB @ 0;'

print()
print(o)
