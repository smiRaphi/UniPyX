import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.getcwd())

import subprocess
from lib.dldb import DLDB
db = DLDB()

if sys.argv[1] == 'hfsexplorer':
    ce = os.environ.copy()
    ce['PATH'] += ';' + os.path.dirname(db.get('hfsexplorer'))
    c,o,e = db.run(['java','--enable-native-access=ALL-UNNAMED','-cp',db.get('hfsexplorer'),'org.catacombae.hfsexplorer.tools.' + sys.argv[2]] + sys.argv[3:],env=ce)
elif sys.argv[1] == 'dosbox':
    subprocess.run([db.get('dosbox'),"-nolog","-nopromptfolder","-savedir","NUL","-defaultconf","-fastlaunch","-nogui",
                    "-c","MOUNT C .","-c","C:"])
else: c,o,e = db.run(sys.argv[1:])

print(c)
print(o)
print(e)
