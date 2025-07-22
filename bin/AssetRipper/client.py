import httpx,os,json,subprocess

def dumps(i): return json.dumps(i,ensure_ascii=False,separators=(',',':'))

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
            exe = os.path.dirname(os.path.realpath(__file__)) + '\\'
            if os.path.exists('AssetRipper.GUI.Premium.exe'): exe += 'AssetRipper.GUI.Premium.exe'
            else: exe += 'AssetRipper.GUI.Free.exe'
        assert os.path.exists(exe),'AssetRipper not found'

        cmd = [exe,'--launch-browser=false','--log=false']
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
    def __del__(self): self.end()

    def cpath(self,i:int=None): return dumps({'P':([] if i is None else [i])})
    def cpathb(self,b:int): return dumps({'B':{'P':[b]},'I':0})
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
        self.post('LoadFile',path=path)
    def Reset(self): self.post('Reset')
    def SettingsUpdate(self,settings:dict): self.post('Settings/Update',**settings)
    def ExportPrimaryContent(self,path:str,create_subfolder=False):
        path = os.path.realpath(path)
        try: self.post('Export/PrimaryContent',Path=path,CreateSubfolder=create_subfolder)
        except httpx.ReadTimeout: pass
        assert os.listdir(path)
def extract(i,o,base=None):
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
        'ShaderExportMode': 'Dummy',
        'TextExportMode': 'Parse',
        'EnableAssetDeduplication': 'True',
        'EnablePrefabOutlining': 'False',
        'EnableStaticMeshSeparation': 'True',
        'ScriptLanguageVersion': 'AutoSafe',
        'ScriptExportMode': 'Hybrid',
    })

    c.LoadFile(i)
    c.ExportPrimaryContent(o)
    c.end()

if __name__ == '__main__':
    from sys import argv

    extract(*argv[1:])
