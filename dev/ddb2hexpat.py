import json,ast

inp = ''
while True:
    i = input(': ')
    if not i: break
    inp += i + '\n'

inp = json.loads(inp)
o = 'struct DDB {\n'
for x,i in enumerate(inp):
    if i[0] == 'isat':
        rv = ast.literal_eval('"' + i[1].replace('"','\\"') + '"').encode('latin1')
        o += f'\tchar {i[0]}{x}[{len(rv)}] @ 0x{i[2]:X}; // {i[1]}\n'
    elif i[0] == 'isatS':
        rv = ast.literal_eval('"' + i[1].replace('"','\\"') + '"').encode('latin1')
        o += f'\tchar {i[0]}{x}[{len(rv)*i[2]}] @ 0x{i[3]:X}; // {i[1]}\n'
    elif i[0] == 'str': o += f'\tchar {i[0]}{x}[{i[2]}] @ 0x{i[1]:X};\n'
    elif i[0] == 'str0': o += f'\tchar {i[0]}{x}[{i[2]}] @ 0x{i[1]:X}; {i[3]}\n'
o += '};\nDDB DDB @ 0;'

print()
print(o)
