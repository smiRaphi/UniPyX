import json

i = ''
print('def check(inp):')
while True:
    inp = input('    ')
    if not inp: break
    i += inp + '\n'

print(json.dumps(i.strip().replace('    ','\t')))
