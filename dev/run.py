import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.getcwd())

from lib.dldb import DLDB
db = DLDB()
c,o,e = db.run(sys.argv[1:])

print(c)
print(o)
print(e)
