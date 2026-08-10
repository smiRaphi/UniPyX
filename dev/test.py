import sys,os
sys.path.append(os.getcwd())

th = bytes.fromhex('2610EF72FDDB788115DF13E6B15F8A940FB42CEF9B73A875FE1CABAD')

FILE = 'lib/unipyxx/crypt.c'
cmds = (
    {'c':(sys.executable,'lib/unipyxx/build.py')},
    {'f':lambda: __import__('lib.unipyxx').unipyxx.X().hash_fugue(b'123456789',224),'cv':th}
)

import subprocess
from time import sleep
from lib.pyob import PyOFunc

import ast
class PyF(PyOFunc):
    def run_ext(self,*args,**kwargs):
        fnn = 'f' + os.urandom(16).hex()
        if self.islambda: f = fnn + '=' + self.source
        else: f = 'def ' + fnn + '(' + self.source.split('(',1)[1]
        f = f'import sys\n{f}\nprint({fnn}(*{repr(args)},**{repr(kwargs)}))\nsys.exit(0)\n'
        r = subprocess.Popen([sys.executable],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        sout,serr = r.communicate(f.encode())
        if r.returncode != 0: raise RuntimeError(serr.decode())
        return ast.literal_eval(sout.decode())

def fmt(i):
    if isinstance(i,bytes): return i.hex().upper()
    elif isinstance(i,str): return i
    elif isinstance(i,int):
        if i < 0x10: return str(i)
        b = (i.bit_length() + 7) // 8
        l = b * 2
        if b <= 4:
            p = '0x'
            if (i.bit_length() + 3) // 4 == 3: l = 3
        else: p = ''
        return p + f'{i:0{l}X}'
    elif isinstance(i,BaseException):
        tr = ''
        if i.__traceback__:
            tr = i.__traceback__.tb_next.tb_next.tb_next
            tr = f' @ {tr.tb_frame.f_code.co_filename}:{tr.tb_lineno}'
        return f'{i.__class__.__name__}: {i}{tr}'
    return str(i)
def printf(*args,**kwargs):
    print(' '.join(fmt(x) for x in args),**kwargs)

for x in cmds:
    if 'f' in x: x['f'] = PyF(x['f'])

ots = 0
while 1:
    if os.path.getmtime(FILE) != ots:
        ots = os.path.getmtime(FILE)
        for cmd in cmds:
            if 'c' in cmd:
                printf('Running:',*cmd['c'])
                r = subprocess.run(cmd['c']).returncode
                if r == 0: printf('Success! :D')
                else:
                    printf('Fail! D:')
                    break
            elif 'f' in cmd:
                printf('Running:',cmd['f'])
                try: v = cmd['f'].run_ext()
                except BaseException as e:
                    printf(e)
                    break
                if 'cv' in cmd:
                    printf(v,cmd['cv'])
                    if v == cmd['cv']: printf('Success! :D')
                    else:
                        printf('Fail! D:')
                        break
                elif v: printf('Success! :D')
                else:
                    printf('Fail! D:')
                    break
            print()
    else: sleep(0.25)
