import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.getcwd())

import httpx,re,importlib
from urllib.parse import unquote
import lib.main

url = sys.argv[1].strip('/') + '/'
assert '://sembiance.com/' in url and url.startswith(('https://','http://'))
div = int(sys.argv[2]) if len(sys.argv) > 2 else 3

fs = re.findall(r'(?m)^<a href="([^"]+)">',httpx.get(url).text)
assert len(fs)

f = fs[(len(fs)-1)//div]
fn = os.path.abspath(unquote(f))
ur = url + f
print(os.path.basename(fn),ur)
if not os.path.exists(fn) or os.path.getsize(fn) == 0:
    open(fn,'wb').write(httpx.get(ur).content)

ts,rts = lib.main.analyze(fn,raw=True)

print('Processed:')
for x in ts: print(x)
print()
print('Raw:')
for x in sorted(set(rts)): print(x)

print()
input('Paused: ')
print()

importlib.reload(lib.main)
lib.main.remove('test_out')
lib.main.main_extract(fn,os.path.abspath('test_out'),quiet=False,rs=True)

print()
input('Remove pause: ')
lib.main.remove('test_out',fn)
