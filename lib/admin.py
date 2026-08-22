from sys import argv
of = open(argv[2],'wb')

import subprocess,base64,json
from time import sleep

try:
    cmds = json.loads(base64.b85decode(argv[1]).decode('utf-8'))
    r = []
    for cmd in cmds:
        kw = cmd.get('k') or {}
        if not cmd.get('si') is None:
            kw['stdin'] = -1
            si = base64.b85decode(argv[3 + cmd['si']])
        else: si = None
        kw['stdout'] = -1
        kw['stderr'] = -1

        p = subprocess.Popen(cmd['c'],**kw)
        if cmd.get('t'):
            for _ in range(cmd['t']):
                if p.poll() != None: break
                sleep(0.1)
            else: p.kill()
            o,e = p.stdout.read(),p.stderr.read()
        else: o,e = p.communicate(input=si)
        r.append((p.returncode,o,e))
except:
    import traceback
    of.write(b'ER\n')
    of.write(traceback.format_exc().encode('utf-8'))
    of.close()
    raise

of.write(b'OK\n')
for c in r:
    of.write(c[0].to_bytes(4,'little'))
    of.write(len(c[1]).to_bytes(8,'little'))
    of.write(len(c[2]).to_bytes(8,'little'))
    of.write(c[1])
    of.write(c[2])
of.close()
