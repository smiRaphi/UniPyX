import httpx,os,json,subprocess,re
from shutil import rmtree

BDIR = os.path.dirname(os.path.realpath(__file__))
def dumps(i): return json.dumps(i,ensure_ascii=False,separators=(',',':'))
REGS = tuple(re.compile(x) for x in (
    r'"/Bundles/View\?Path=%7B%22P%22%3A%5B(\d+)%5D%7D" class="btn btn-dark p-0 m-0">(.*?)</a></li>',
    r'href="/(\w+)/View\?Path=%7B%22B%22%3A%7B%22P%22%3A%5B(\d+)%5D%7D%2C%22I%22%3A(\d+)%7D"',
    r'" download="([^"]+)" class="btn btn-primary',
))

FileEntry = tuple[str,int,int]

class Client:
    def __init__(self,base:str=None):
        self.c = httpx.Client()
        self.p = None

        if base:
            base = base.strip('/')
            if not base.startswith('http'): base = 'http://' + base
            base += '/'
            self.test(True)
        self.base = base
    def start(self,exe:str=None,port:int=None):
        if not exe:
            exe = BDIR + '\\'
            if os.path.exists('AssetRipper.GUI.Premium.exe'): exe += 'AssetRipper.GUI.Premium.exe'
            else: exe += 'AssetRipper.GUI.Free.exe'
        assert os.path.exists(exe),'AssetRipper not found'

        cmd = [exe,'--headless','--log=false']
        if port: cmd += [f'--port={port}']
        self.p = subprocess.Popen(cmd,stdout=-1,stderr=-1)

        while True:
            assert not self.p.poll()
            l = self.p.stdout.readline()
            if l.strip().startswith(b'Now listening on: http'):
                self.base = l.decode().strip().split(': ')[1] + '/'
                break
        self.test(True)
    def end(self):
        if self.p: self.p.kill()
        if os.path.exists(BDIR + '/temp'): rmtree(BDIR + '/temp')
    def log(self): return self.p.stdout.read().decode(),self.p.stderr.read().decode()
    def __del__(self): self.end()

    def cpath(self,i:int=None): return dumps({'P':([] if i is None else [i])})
    def cpathb(self,b:int,i=0): return dumps({'B':{'P':[b]},'I':i})
    def herr(self,r:httpx.Response,cc=None):
        if cc is None: cc = 302 if r.request.method == 'POST' else 200
        if r.status_code != cc:
            if r.headers.get('content-type') != 'text/html': raise Exception(r.text)
            r.raise_for_status()

    def get(self,endpoint:str,herr=True,**params) -> httpx.Response:
        r = self.c.get(self.base+endpoint,params=params or None)
        if herr is not False: self.herr(r,herr if type(herr) == int else None)
        return r
    def post(self,endpoint:str,herr=True,**data) -> httpx.Response:
        r = self.c.post(self.base+endpoint,data=data or None)
        if herr is not False: self.herr(r,herr if type(herr) == int else None)
        return r

    def test(self,rs=False) -> bool:
        r = self.get('',herr=False)
        h = r.headers
        rt = r.status_code == 200 and h.get('content-type') == 'text/html' and h.get('server') == 'Kestrel'
        if rs: assert rt,'Bad Base Address'
        return rt

    def LoadFile(self,path:str):
        path = os.path.realpath(path)
        assert os.path.exists(path) and os.path.isfile(path)
        try: self.post('LoadFile',path=path)
        except httpx.ReadTimeout: pass
    def Reset(self): self.post('Reset')
    def SettingsUpdate(self,settings:dict): self.post('Settings/Update',**settings)
    def ExportPrimaryContent(self,path:str,create_subfolder=False):
        path = os.path.realpath(path)
        try: self.post('Export/PrimaryContent',Path=path,CreateSubfolder=create_subfolder)
        except httpx.ReadTimeout: pass
        if not os.listdir(path):
            self.end()
            if self.p: print('\n========\n'.join(self.log()))
            raise Exception('Failed to export')
    def Bundles(self): return [int(x) for x in REGS[0].findall(self.get('Bundles/View',Path=self.cpath()).text)]
    def BundleData(self,i:int) -> list[FileEntry]:
        o = []
        for x in REGS[1].findall(self.get('Bundles/View',Path=self.cpath(i)).text): o.append((x[0],int(x[1]),int(x[2])))
        return o
    def Data(self,f:FileEntry,name=True):
        if name: fn = REGS[2].search(self.get(f[0] + '/View',Path=self.cpathb(f[1],f[2])).text)[1]
        r = self.c.get(f'{self.base}{f[0]}/Data',params={'Path':self.cpathb(f[1],f[2])})
        r.raise_for_status()
        if name: return fn,r.content
        return r.content

def extract(i,o,base=None):
    r = 0
    c = Client(base)
    if not base: c.start()
    c.Reset()
    c.SettingsUpdate({
        'DefaultVersion': '0.0.0a0',
        'BundledAssetsExportMode': 'DirectExport',
        'ScriptContentLevel': 'Level2',
        'TargetVersion': '0.0.0a0',
        'AudioExportFormat': 'Native',
        'ImageExportFormat': 'Tga',
        'LightmapTextureExportFormat': 'Image',
        'SpriteExportMode': 'Texture2D',
        'ShaderExportMode': 'Yaml',
        'TextExportMode': 'Parse',
        'EnableAssetDeduplication': 'True',
        'EnablePrefabOutlining': 'False',
        'EnableStaticMeshSeparation': 'True',
        'ScriptLanguageVersion': 'AutoSafe',
        'ScriptExportMode': 'Hybrid',
        'ScriptTypesFullyQualified': 'True',
        'ExportUnreadableAssets': 'True',
    })

    c.LoadFile(i)

    c.ExportPrimaryContent(o)
    if os.path.exists(o + '/Assets/EditorSettings/EditorSettings.json') and os.path.getsize(o + '/Assets/EditorSettings/EditorSettings.json') == 162: os.remove(o + '/Assets/EditorSettings/EditorSettings.json')
    if os.path.exists(o + '/Assets/EditorSettings') and not os.listdir(o + '/Assets/EditorSettings'): os.rmdir(o + '/Assets/EditorSettings')
    if os.path.exists(o + '/Assets/Shader'):
        for f in os.listdir(o + '/Assets/Shader'):
            f = o + '/Assets/Shader/' + f
            if os.path.isdir(f): continue
            d = open(f,'rb').read()
            if b'"m_CorrespondingSourceObject": { "m_Collection": "unity default resources", "m_PathID": 0 },' in d and b'"m_Script": ""' in d: os.remove(f)
        if not os.listdir(o + '/Assets/Shader'): os.rmdir(o + '/Assets/Shader')
    if os.path.exists(o + '/Assets') and not os.listdir(o + '/Assets'): os.rmdir(o + '/Assets')
    for f in c.BundleData(0):
        if f[0] == 'Resources':
            fn,d = c.Data(f)
            open(o + '/' + fn,'wb').write(d)
        elif f[0] == 'FailedFiles': r = 1

    c.end()
    return r

if __name__ == '__main__':
    from sys import argv,exit

    exit(extract(*argv[1:]))
