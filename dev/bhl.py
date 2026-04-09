import os,sys
argv = sys.argv
sys.path.append(os.getcwd())
from lib.file import HashLib

h = HashLib.new(os.path.splitext(os.path.basename(argv[2]))[0] + '.bhl',argv[1])
for x in argv[2:]:
    h.add(open(x,encoding='utf-8').read().split('\n'))
h.save()
