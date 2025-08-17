import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json,httpx,time,re
DLDB = json.load(open('lib/dldb.json',encoding='utf-8'))
NDLDB = {}

GRELTS = re.compile(r'<relative-time class="no-wrap" prefix="[^"]*" datetime="([^"]+)">')
GRELTG = re.compile(r'/releases/tag/([^"]+)" data-view-component=')
GFMTS = {
    'ip7z/7zip':lambda tag:f'7z{tag.replace(".","")}-x64.msi',
    'julian-r/file-windows':lambda tag:f'file_{tag[1:]}-build104-vs2022-x64.zip',
    'ExeinfoASL/ASL':lambda tag:f'Exeinfo_{tag[1:].replace(".","")}.zip',
    'aaru-dps/Aaru':lambda tag:f'aaru-{tag[1:]}_windows_x64.zip',
    'temisu/ancient':lambda tag:f'ancient_{tag[1:]}.zip',
    'Sappharad/GDIbuilder':lambda tag:f'gdibuilder{tag[1:].replace(".","")}_cmd_win_x64.zip',
    'upx/upx':lambda tag:f'upx-{tag[1:]}-win64.zip',
    'xchellx/bnrtool':lambda tag:f'bnrtool_{tag}_msys2-clang64_net9.0_win-x64.7z',
    'MaikelChan/AFSPacker':lambda tag:f'AFSPacker-{tag}-win-x64.7z',
    'mamedev/mame':lambda tag:f'{tag}b_64bit.exe',
    'Maschell/JWUDTool':lambda tag:f'JWUDTool-{tag}.jar',
    'ch-mcl/PS2_RidgeRacerV_ArchiveTool':lambda tag:f'{tag}.zip',
    'ZDoom/wadext':lambda tag:f'wadext_win32_{tag}.zip',
    'glacier-modding/RPKG-Tool':lambda tag:f'rpkg_{tag}-cli.zip',
    'lifenjoiner/ISx':lambda tag:f'ISx-{tag}.7z'
}

def ft(i:str,f:str): return int(time.mktime(time.strptime(i,f)))
def t(): return int(time.time())

class Cache:
    def __init__(self):
        self.c = httpx.Client()
        self._s = {}
    def get(self,u) -> str:
        if u in self._s: return self._s[u]
        r = self.c.get(u,follow_redirects=True).text
        self._s[u] = r
        return r
    def srch(self,p:str,u:str) -> str:
        s = self.get(u)
        return re.search(p,s)[1]
    def srcht(self,p:str,f:str,u:str) -> int:
        return ft(self.srch(p,u),f)

def update():
    c = Cache()

    for k,inf in DLDB.items():
        NDLDB[k] = inf
        if 'fs' not in inf: continue

        nfs = []
        tts = inf.get('ts',0)
        for f in inf['fs']:
            ots = tts
            if type(f) == str: u = f
            elif type(f) == list: u,p = f
            elif type(f) == dict:
                u = f['u']
                if 'ts' in f: ots = f['ts'] or tts
            dom = u.split('://')[1].split('/')[0]

            ts = ots
            if u == 'https://mark0.net/download/trid_w32.zip':
                v = c.srch(r'TrID v(\d{1,3}\.\d{1,3}),','https://mark0.net/soft-trid-e.html')
                if v != '2.24': ts = t()
                else: ts = 1459602900
            elif u == 'https://mark0.net/download/triddefs.zip':
                ts = c.srcht(r'\.zip-->(\d\d/\d\d/\d\d)<','%d/%m/%y','https://mark0.net/soft-trid-e.html')
            elif u == 'https://cdn.theunarchiver.com/downloads/unarWindows.zip':
                ts = ft(str(time.gmtime().tm_year),'%Y')

            elif dom == 'github.com' and '/releases/download/' in u:
                repo = u.split('/releases/download/')[0].split('//github.com/')[1]
                s = c.get(u.split('/releases/download/')[0] + '/releases/latest')
                ts = ft(GRELTS.search(s)[1],'%Y-%m-%dT%H:%M:%SZ')
                tag = GRELTG.search(s)[1]
                if ts > ots:
                    if repo in GFMTS: nu = f'https://github.com/{repo}/releases/download/{tag}/{GFMTS[repo](tag)}'
                    else: nu = f'https://github.com/{repo}/releases/download/{tag}/' + u.split('/')[-1]
                    if u != nu and c.c.head(nu).status_code == 302: u = nu
                    else: ts = 0
            elif dom == 'archive.ubuntu.com':
                bu = os.path.dirname(u) + '/'
                s = c.get(bu)
                ms = re.findall(r'"(' + re.escape(u.split('/')[-1].split('_')[0]) + r'_\d+\.\d+-[^"]+)">[^<]*</a></td><td[^>]*>([^<]+?) *</td>',s)[-1]
                ts = ft(ms[1],'%Y-%m-%d %H:%M')
                if ts > ots:
                    nu = bu + ms[0]
                    if u != nu: u = nu
            elif dom == 'entropymine.com':
                bu = os.path.dirname(u) + '/'
                s = c.get(bu)
                ms = re.findall(r'href="([^"]+)">[^<]+</a> *(\d{4}-\d\d-\d\d \d\d:\d\d)',s)[-1]
                ts = ft(ms[1],'%Y-%m-%d %H:%M')
                if ts > ots: u = bu + ms[0]
            elif dom == 'dl.dolphin-emu.org':
                s = c.get('https://dolphin-emu.org/download/')
                m = re.search(r'href="/download/dev/[^"]+">[^<]+</a></td>\s*<td class="reldate" title="([^"Z\.]+)[^"]*">[^<]*</td>\s*.+\s*</tr>\s*<tr class="download">\s*.+\s*<td class="download-links".*>\s*<a href="(https://[^"]+-x64\.7z)"',s)
                ts = ft(m[1],'%Y-%m-%dT%H:%M:%S')
                if m[2] != u: u = m[2]
            elif dom.endswith('.wiimm.de'):
                s = c.get(f'https://{dom}/download.html')
                m = re.search(r'<a href="(/download/[^"]+-cygwin64\.zip)">[^<\n]*</a>[^,\n]+, (\d{4}-\d\d-\d\d)',s)
                ts = ft(m[2],'%Y-%m-%d')
                nu = f'https://{dom}{m[1]}'
                if nu != u: u = nu
            elif dom == 'files.prodkeys.net':
                s = c.get(c.srch(r'href="(https://prodkeys\.net/yuzu-prod-keys-n\d+/)"','https://prodkeys.net/'))
                ts = ft(re.search(r'<meta property="og:updated_time" content="([^"]+)"',s)[1].split('+')[0],'%Y-%m-%dT%H:%M:%S')
                if ts > ots:
                    nu = re.search(r'href="(https://files\.prodkeys\.net/ProdKeys\.net-v\d+\.\d+\.\d+\.zip)"',s)[1]
                    if nu != u: u = nu

            if ts > ots:
                tts = max(tts,ts)
                if type(f) == str: nfs.append(u)
                elif type(f) == list: nfs.append([u,p])
                elif type(f) == dict:
                    f['u'] = u
                    f['ts'] = ts
                    nfs.append(f)
            else: nfs.append(f)

        inf['fs'] = nfs
        inf['ts'] = tts

    out = json.dumps(DLDB,ensure_ascii=False,separators=(',',':'),indent=4).replace(
                    '\n            {',           '{').replace(
                    '\n            [',           '[').replace(
                    '\n            }\n        ]','\n        }]').replace(
                    '\n            ]\n        ]','\n        ]]').replace(
                    '\n            ',          '\n        ')

    open('lib/dldb.json','w',encoding='utf-8').write(out)

if __name__ == '__main__':
    update()
