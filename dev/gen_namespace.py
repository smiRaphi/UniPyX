import os,re

ob = []
imps = ['from typing import NewType','from ..lib.main import *']
RG = re.compile(r'(?m)^@namespace(?:\(.*\))?\ndef (\w+)\(.*\):\n((?: {4}[^\n]+\n|\n)+)')
nms = []
for f in os.listdir('lib'):
    if f.endswith('.py') and f.startswith('sub'):
        fnc = RG.findall(open(os.path.join('lib',f),encoding='utf-8').read())
        for x in fnc:
            nn = x[0]
            if nn.startswith('_'): nn = nn[1:]
            nms.append(nn)
            ob.append(f'class {nn}:')
            fncs = []
            clss = []
            for l in x[1].strip('\n').split('\n'):
                if l == '    return locals()' or (not l.strip() and ob[-1][:5] == 'class'): continue
                if l.startswith('        nonlocal '): l = '        global' + l[16:]
                elif l.lstrip().startswith('from lib.'): l = l[:l.find('from lib.')] + 'from ..lib.' + l[l.find('from lib.') + 9:]
                if l.startswith(('    from ','    import ')):
                    l = l[4:]
                    if l not in imps: imps.append(l)
                else:
                    if l.startswith('    def '):
                        ob.append('    @staticmethod')
                        fncs.append(l[8:].split('(')[0].strip())
                    elif l.startswith('    class '): clss.append(l[10:].split(':')[0].split('(')[0].strip())
                    elif l.startswith('    ') and len(l) > 6 and l[5] in 'ABCEFGHIJKLMNOPQRSTUVWXYZ' and l.split()[1] == '=': fncs.append(l.split('=')[0].strip())
                    ob.append(l)
            if clss:
                ob.append(','.join(clss) + '=' + ','.join([f'NewType("{cl}",{nn}.{cl})' for cl in clss]))
            if fncs:
                ob.append(','.join(fncs) + '=' + ','.join([nn + '.' + fn for fn in fncs]))
            ob.append('')

open('dev/_namespaces.py','w',encoding='utf-8').write('\n'.join(imps) + '\n\n' + '\n'.join(ob))
open('dev/namespaces.py','w',encoding='utf-8').write('from ._namespaces import ' + ','.join(nms) + '\n')
