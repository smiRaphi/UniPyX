import os,locale
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json,httpx,time,re
DLDB = json.load(open('lib/dldb.json',encoding='utf-8'))
NDLDB = {}

GRELTS = re.compile(r'<relative-time class="no-wrap" prefix="[^"]*" datetime="([^"]+)">')
GRELTG = re.compile(r'/releases/tag/([^"]+)" data-view-component=')
GFMTS = {
    'ip7z/7zip':lambda tag:f'7z{tag.replace(".","")}-x64.msi',
    'julian-r/file-windows':lambda tag:f'file_{tag[1:]}-build104-vs2022-x64.zip',
    #'ExeinfoASL/ASL':lambda tag:f'Exeinfo_{tag[1:].replace(".","")}.zip',
    'aaru-dps/Aaru':lambda tag:f'aaru-{tag[1:]}_windows_x64.zip',
    'Sappharad/GDIbuilder':lambda tag:f'gdibuilder{tag[1:].replace(".","")}_cmd_win_x64.zip',
    'upx/upx':lambda tag:f'upx-{tag[1:]}-win64.zip',
    'xchellx/bnrtool':lambda tag:f'bnrtool_{tag}_msys2-clang64_net9.0_win-x64.7z',
    'MaikelChan/AFSPacker':lambda tag:f'AFSPacker-{tag}-win-x64.7z',
    'mamedev/mame':lambda tag:f'{tag}b_x64.exe',
    'Maschell/JWUDTool':lambda tag:f'JWUDTool-{tag}.jar',
    'ch-mcl/PS2_RidgeRacerV_ArchiveTool':lambda tag:f'{tag}.zip',
    'ZDoom/wadext':lambda tag:f'wadext_win32_{tag}.zip',
    'glacier-modding/RPKG-Tool':lambda tag:f'rpkg_{tag}-cli.zip',
    'lifenjoiner/ISx':lambda tag:f'ISx-{tag}.7z',
    'activescott/lessmsi':lambda tag:f'lessmsi-{tag}.zip',
    'rm-NoobInCoding/UnPSARC':lambda tag:f'UnPSARC_{tag}.zip',
    'AppleCommander/AppleCommander':lambda tag:f'AppleCommander-acx-{tag}.jar',
    'unsound/hfsexplorer':lambda tag:f'{tag}-bin.zip',
    'IlyaGrebnov/libbsc':lambda tag:f'bsc-{tag[1:]}-x64.zip',
    'GDRETools/gdsdecomp':lambda tag:f'GDRE_tools-{tag}-windows.zip',
    '0CBH0/nsnsotool':lambda tag:f'nsnsotool_{tag}.zip',
    'apoloval/mcp':lambda tag:f'mcp-{tag[1:]}_x64.exe',
}

def ft(i:str,f:str,loc='en_US'):
    locale.setlocale(locale.LC_TIME,loc)
    r = int(time.mktime(time.strptime(i,f)))
    locale.setlocale(locale.LC_TIME,'')
    return r
def t(): return int(time.time())

class Cache:
    def __init__(self):
        self.c = httpx.Client(timeout=10)
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
            if u == '.': dom = None
            else: dom = u.split('://')[1].split('/')[0]

            ts = ots
            if u == '.': tts = -1
            elif u in ('https://mark0.net/download/trid_w32.zip','https://mark0.net/download/trid_win64.zip','https://mark0.net/download/trid.zip'):
                ts = c.srch(r'>TrID(?:/(?:Linux|32|64))? v\d+\.\d+\w?(?: \(all platforms\))? - (\d\d/\d\d/\d{2,4})</','https://mark0.net/soft-trid-e.html')
                ts = ft(ts,'%d/%m/%' + ('y' if len(ts) == 8 else 'Y'))
                u = 'https://mark0.net/download/trid.zip'
            elif u == 'https://mark0.net/download/triddefs.zip':
                ts = c.srcht(r'\.zip-->(\d\d/\d\d/\d\d)<','%d/%m/%y','https://mark0.net/soft-trid-e.html')
            elif u == 'https://cdn.theunarchiver.com/downloads/unarWindows.zip':
                ts = ft(str(time.gmtime().tm_year),'%Y')
            elif u == 'http://takeda-toshiya.my.coocan.jp/msdos/msdos.7z':
                ts = c.srcht(r'</a> \((\d+/\d+/\d{4})\)','%m/%d/%Y','http://takeda-toshiya.my.coocan.jp/msdos/index.html')
            elif u.startswith('https://github.com/horsicq/Detect-It-Easy/releases/download/Beta/'):
                ts = ft(str(time.gmtime().tm_year),'%Y')
            elif u == "https://github.com/horsicq/Detect-It-Easy/releases/download/current-database/db.zip":
                ct = time.gmtime()
                ts = ft(f'{ct.tm_year}.{ct.tm_mon:02d}.{ct.tm_mday:02d}','%Y.%m.%d')

            elif dom == 'github.com' and '/releases/download/' in u:
                repo = u.split('/releases/download/')[0].split('//github.com/')[1]

                if repo not in ('VirusTotal/yara'):
                    if repo in ('aaru-dps/Aaru','GDRETools/gdsdecomp'): s = c.get(u.split('/releases/download/')[0] + '/releases/tag/' + re.search(r'<a href="/[^/]+/[^/]+/releases/tag/([^"/]+)"',c.get(u.split('/releases/download/')[0] + '/releases'))[1])
                    elif repo in (): s = c.get(u.split('/releases/download/')[0] + '/releases/tag/' + u.split('/')[7])
                    else: s = c.get(u.split('/releases/download/')[0] + '/releases/latest')

                    ts = ft(GRELTS.search(s)[1],'%Y-%m-%dT%H:%M:%SZ')
                    tag = GRELTG.search(s)[1]

                    if ts > ots:
                        if repo in GFMTS:
                            of = GFMTS[repo](tag)
                            nu = f'https://github.com/{repo}/releases/download/{tag}/{of}'
                        else: nu = f'https://github.com/{repo}/releases/download/{tag}/' + u.split('/')[-1]
                        if u != nu:
                            if c.c.head(nu).status_code == 302: u = nu
                            else:
                                print('[!] 404:',u,'!->',nu)
                                ts = ots
                        else: ts = ots
            elif dom == 'archive.ubuntu.com':
                bu = os.path.dirname(u) + '/'
                s = c.get(bu)
                ms = re.findall(r'"(' + re.escape(u.split('/')[-1].split('_')[0]) + r'_\d+\.\d+-[^"]+)">[^<]*</a></td><td[^>]*>([^<]+?) *</td>',s)[-1]
                ts = ft(ms[1],'%Y-%m-%d %H:%M')
                if ts > ots:
                    nu = bu + ms[0]
                    if u != nu: u = nu
                    else: ts = 0
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
                else: ts = 0
            elif dom.endswith('.wiimm.de'):
                s = c.get(f'https://{dom}/download.html')
                m = re.search(r'<a href="(/download/[^"]+-cygwin64\.zip)">[^<\n]*</a>[^,\n]+, (\d{4}-\d\d-\d\d)',s)
                ts = ft(m[2],'%Y-%m-%d')
                nu = f'https://{dom}{m[1]}'
                if nu != u: u = nu
                else: ts = 0
            elif dom == 'files.prodkeys.net':
                s = c.get(c.srch(r'href="(https://prodkeys\.net/yuzu-prod-keys-n\d+/)"','https://prodkeys.net/'))
                ts = ft(re.search(r'<meta property="og:updated_time" content="([^"]+)"',s)[1].split('+')[0],'%Y-%m-%dT%H:%M:%S')
                if ts > ots:
                    nu = re.search(r'href="(https://files\.prodkeys\.net/ProdKeys\.net-v\d+\.\d+\.\d+\.zip)"',s)[1]
                    if nu != u: u = nu
                    else: ts = 0
            elif dom == 'dl.xpdfreader.com':
                s = c.get('https://www.xpdfreader.com/download.html')
                ts = ft(re.search(r'Released: ([^<]+)</p>',s)[1],'%Y %b %d')
                if ts > ots:
                    nu = re.search(r'href="(https://dl\.xpdfreader\.com/xpdf-tools-win-[^"]+\.zip)">',s)[1]
                    if nu != u: u = nu
                    else: ts = 0
            elif dom == 'wimlib.net':
                s = c.get('https://wimlib.net/')
                m = re.search(r'Current release: (wimlib\-\d+\.\d+\.\d+) \(released (\w+ \d{1,2}, \d{4})\)',s)
                ts = ft(m[2],'%B %d, %Y')
                if ts > ots:
                    nu = f'https://wimlib.net/downloads/{m[1]}-windows-x86_64-bin.zip'
                    if nu != u: u = nu
                    else: ts = 0

            if ts > ots:
                print(k,'->',u)
                tts = max(tts,ts)
                if type(f) == str: nfs.append(u)
                elif type(f) == list: nfs.append([u,p])
                elif type(f) == dict:
                    f['u'] = u
                    f['ts'] = ts
                    nfs.append(f)
            else: nfs.append(f)

        inf['fs'] = nfs
        if tts >= 0: inf['ts'] = tts

    out = json.dumps(DLDB,ensure_ascii=False,separators=(',',':'),indent=4).replace(
                    '\n            {',           '{').replace(
                    '\n            [',           '[').replace(
                    '\n            }\n        ]','\n        }]').replace(
                    '\n            ]\n        ]','\n        ]]').replace(
                    '\n            ',          '\n        ')

    open('lib/dldb.json','w',encoding='utf-8').write(out)

if __name__ == '__main__':
    update()
