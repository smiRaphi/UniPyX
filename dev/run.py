import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.getcwd())

from lib.dldb import DLDB
db = DLDB()

if sys.argv[1] == 'hfsexplorer':
    ce = os.environ.copy()
    ce['PATH'] += ';' + os.path.dirname(db.get('hfsexplorer'))
    c,o,e = db.run(['java','--enable-native-access=ALL-UNNAMED','-cp',db.get('hfsexplorer'),'org.catacombae.hfsexplorer.tools.UnHFS'] + sys.argv[2:],env=ce)
else: c,o,e = db.run(sys.argv[1:])

print(c)
print(o)
print(e)
