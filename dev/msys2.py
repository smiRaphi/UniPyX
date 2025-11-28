import httpx,json,re
from sys import argv

RURL = re.compile(r'File:</dt>\s*<dd[^>]*>\s*<a href="([^"]+)">')
RFS = re.compile(r'>Files:</dt>\s*<dd[^>]+>\s*<pre[^<]+<code>([^<]+)</code></pre>')
RDP = re.compile(r'(?s)>Dependencies:</dt>\s*<dd[^>]+>\s*<ul[^>]+>\s*(.+)</ul>\s*</dd>\s*<dt[^>]+>Optional Dependencies:</dt>')
RDPS = re.compile(r'<a href="([^"]+)">')
RTIT = re.compile(r'Package:\s*<a href="[^"]+">mingw-w64-x86_64-(.+)</a></h4>')
RVPK = re.compile(r'<ul class="list-unstyled">\s*<li><a href="([^"]+)"')

o = {}
checked = []
def getpkg(i) -> tuple[str,list[str],list[str]]:
    if not i.startswith('https://'): i = 'https://packages.msys2.org/packages/mingw-w64-x86_64-' + i
    s = httpx.get(i).text
    while '<title>Virtual Package: ' in s: s = httpx.get(RVPK.search(s)[1]).text

    lt = RTIT.search(s)[1]
    if lt in checked: return
    checked.append(lt)

    fs = [x.strip('/') for x in RFS.search(s)[1].split('\n') if x.startswith('/mingw64/bin/')]
    if not fs: return

    if not o:
        t = lt
        o[t] = {
            'p':t + '/' + [x for x in fs if x.endswith('.exe')][0].split('/',2)[2],
            'fs':[]
        }
    else:
        fs = [x for x in fs if '.' in x and not x.endswith(('.exe','.sh','.py','.pyw','.pyc','.pyd'))]
        if not fs: return
        t = list(o)[0]

    url = RURL.search(s)[1]
    o[t]['fs'].append({
        'u':url,
        'x':{x:t + '/' + x.split('/',2)[2] for x in fs}
    })
    dp = RDP.search(s)
    if dp:
        for u in RDPS.findall(dp[1]): getpkg(u)

getpkg(argv[1])
print(json.dumps(o,ensure_ascii=False,separators=(',',':'),indent=4))
