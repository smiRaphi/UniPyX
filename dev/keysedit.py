import sys,os
sys.path.append(os.getcwd())

from lib.dldb import DLDB;db = DLDB()

from lib.pyob import PyOBinX
k = PyOBinX.dl('keys',db)

if not os.path.exists('keys.pyo'):
    INDENT = 2
    def fmt(i,idn=0):
        if i is None: return 'None'
        elif isinstance(i,(bytes,str,float,bool)): return repr(i)
        elif isinstance(i,int):
            if i < 0x10: return str(i)
            elif i < 0x100: return f'0x{i:02X}'
            elif i <= 0x800: return f'0x{i:03X}'
            elif i < 0x10000: return f'0x{i:04X}'
            elif i < 0x100000000: return f'0x{i:08X}'
            else: return f'0x{i:0X}'
        elif isinstance(i,list):
            if len(i) == 1: return f'[{fmt(i[0])}]'
            o = ['[']
            idn += 1
            for x in i:
                o.append(' '*(INDENT * idn) + fmt(x,idn) + ',')
            idn -= 1
            o.append(' '*(INDENT * idn) + ']')
            return '\n'.join(o)
        elif isinstance(i,dict):
            o = ['{']
            idn += 1
            for k,v in i.items():
                o.append(' '*(INDENT * idn) + fmt(k) + ': ' + fmt(v,idn) + ',')
            idn -= 1
            o.append(' '*(INDENT * idn) + '}')
            return '\n'.join(o)
        raise NotImplementedError(type(i))
    open('keys.pyo','w',encoding='utf-8').write(fmt(k.wait().db) + '\n')
else:
    k.wait().db = eval(open('keys.pyo',encoding='utf-8').read())
    k.save()
