from .main import *

def extract4(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def quickbms(scr,inf=i,ouf=o,print_try=True):
        if db.print_try and print_try: print('Trying with',scr)
        run(['quickbms','-Y',db.get(scr),inf,ouf],print_try=False)
        if os.listdir(ouf): return
        return 1

    match t:
        case 'U8'|'RARC':
            run(['wszst','X',i,'--max-file-size=2g','-o','-R','-E$','-d',o])
            remove(o + '/wszst-setup.txt')
            if os.listdir(o): return
        case 'SARC':
            class Stub:
                def __init__(self,*args,**kwargs):pass
                def __call__(self,*args,**kwargs): return Stub()
                def __getattribute__(self,name): return Stub()
            class OsStub:
                def __init__(self):pass
                def __add__(self,v): return os.devnull

            if db.print_try: print('Trying with sarc')
            db.get('sarc')
            sys.modules['oead'] = Stub()
            sys.modules['rstb'] = Stub()
            sys.modules['json'] = Stub()
            os.path.dirname = lambda x: OsStub() if x.endswith('\\sarc.py') else dirname(x)
            sys.modules['os'] = os

            try:
                from bin.sarc import SARC # type: ignore
                sarc = SARC(open(i,'rb').read())
                sarc.extract_to_dir(o)
                del sarc
            except ImportError: raise
            except: pass

            sys.modules.pop('oead')
            sys.modules.pop('rstb')
            sys.modules.pop('json')
            sys.modules.pop('os')
            os.path.dirname = dirname

            if os.listdir(o): return
        case 'Yaz0':
            run(['wszst','DEC',i,'-o','-E$','-d',o + '\\' + tbasename(i)])
            if exists(o + '\\' + tbasename(i)): return
        case 'LZSS'|'LZ77':
            run(['gbalzss','d',i,o + '\\' + tbasename(i)])
            if exists(o + '\\' + tbasename(i)): return
        case 'AFS':
            run(['afspacker','-e',i,o])
            if os.path.exists(noext(i) + '.json'): remove(noext(i) + '.json')
            if os.listdir(o): return
        case 'NDS Sound Data':
            td = TmpDir()
            tf = td + '\\' + 'tmp' + os.urandom(8).hex() + '.sdat'
            symlink(i,tf)
            run(['ndssndext','-x',tf])
            remove(tf)
            if os.listdir(td.p):
                copydir(td + '/' + os.listdir(td.p)[0],o)
                td.destroy()
                return
            td.destroy()
        case 'F-Zero G/AX .lz':
            td = TmpDir()
            tf = td + '/file.lz'
            symlink(i,tf)
            run(['gxpand','unpack',td,o])
            if os.path.exists(o + '/file,lz'):
                td.destroy()
                rename(o + '/file,lz',o + '/' + tbasename(i))
                return
            remove(tf)
            ouf = open(tf,'wb')
            inf = open(i,'rb')
            ouf.write((inf.read(1)[0] - 8).to_bytes(1,'little'))
            ouf.write(inf.read())
            ouf.close()
            inf.close()
            run(['gxpand','unpack',td,o])
            td.destroy()
            if os.path.exists(o + '/file,lz'):
                rename(o + '/file,lz',o + '/' + tbasename(i))
                return
        case 'GC opening.bnr':
            run(['bnrtool','decode','--bnr',i,'--image',o + '/' + tbasename(i) + '.png','--info',o + '/' + tbasename(i) + '.yaml','-f','-s'],useos=True)
            if os.path.exists(o + '/' + tbasename(i) + '.png') and os.path.exists(o + '/' + tbasename(i) + '.yaml'): return
        case 'Pokemon FSYS':
            td = TmpDir()
            osj = OSJump()
            osj.jump(td)
            run(['gcfsysd',i])
            osj.back()
            if os.listdir(td.p):
                copydir(td,o,True)
                return
            td.destroy()
        case 'BRSAR':
            run(['mrst','extract','-o',o,i])
            if os.listdir(o): return
        case 'ROFS Volume':
            tf = TmpFile('.iso')
            run(['cvm_tool','split',i,tf])
            r = extract(tf,o,'ISO')
            tf.destroy()
            return r
        case 'RetroStudio PAK':
            run(['paktool','-x',i,'-o',o])
            if os.listdir(o): return
        case 'CPK':
            run(['cpkextract',i,o])
            if os.listdir(o): return
        case 'CRI CPK': return quickbms('cpk')
        case 'Sonic AMB': return quickbms('sonic4')
        case 'Level5 ARC'|'Level5 XPCK':
            run(['3ds-xfsatool','-i',i,'-o',o,'-q'])
            if os.listdir(o): return
        case 'Iron Sky GPK':
            fs = []
            for x in re.findall(r'<File((?: \w+="\w{3}: [^"]*")+)\s*/>',open(i,encoding='utf-8').read()):
                tfs = {}
                for y in re.findall(r'(\w+)="(\w{3}): ([^"]*)"',x):
                    if y[1] in ['U16','U32','U64']: tfs[y[0]] = int(y[2])
                    elif y[1] == 'BOL': tfs[y[0]] = bool(int(y[2]))
                    else: tfs[y[0]] = y[2]
                fs.append(tfs)
            ofl = {}
            bid = dirname(i) + '/'
            for x in fs:
                if not x['source'] in ofl: ofl[x['source']] = open(bid + x['source'],'rb')
                ofl[x['source']].seek(x['offset'])
                xopen(o + '/' + x['alias'],'wb').write(ofl[x['source']].read(x['size']))
                if x['compression'] != 'CM_STORE' or x['size'] != x['originalSize']: print('Unknown compression',x)
            for x in ofl: ofl[x].close()
            return
        case 'NUB2': return quickbms('nus3_nub2')
        case 'CTPK':
            run(['ctpktool','-efd',i,o])
            if os.listdir(o): return
        case 'XBP': return quickbms('xbp')
        case 'Bezel Archive': return quickbms('bea')
        case 'PlayStation Archive':
            run(['psarc','extract','--input='+i,'--to='+o])
            if os.listdir(o): return
            run(['unpsarc',i,o])
            if os.listdir(o): return
        case 'Unity Bundle':
            if db.print_try: print('Trying with assetripper')
            run([sys.executable,dirname(db.get('assetripper')) + '\\client.py',i,o],print_try=False)
            if os.listdir(o): return
        case 'Unity Assets':
            b = basename(i).lower()
            if b.startswith('sharedassets') and '.assets.split' in b and b[-1].isdigit():
                bn = b.rstrip('0123456789')
                fs = []
                for x in os.listdir(dirname(i)):
                    if x.startswith(bn): fs.append((dirname(i) + '/' + x,int(x[len(bn):])))
                tf = dirname(i) + '\\' + os.urandom(8).hex() + '.assets'
                with open(tf,'wb') as f:
                    for x in sorted(fs,key=lambda x:x[1]): f.write(open(x[0],'rb').read())
                r = extract(tf,o,'Unity Bundle')
                remove(tf)
            else: r = extract(i,o,'Unity Bundle')
            if not r: return
        case 'Rayman DCZ': return quickbms('rayman_dcz')
        case 'iQiyi PAK':
            run(['iqipack',i,o])
            if os.listdir(o): return
        case 'LEGO JAM': return quickbms('legoracer_jam')
        case 'Metroid Samus Returns PKG': return quickbms('metroid_sr_3ds')
        case 'DDR DAT':
            if db.print_try: print('Trying with custom extractor')

            d = dirname(i)
            for _ in range(3):
                if exists(d + '/SYSTEM.CNF'): break
                d = dirname(d)
            else: return 1
            mf = d + '/' + re.search(r'cdrom0:\\(.+);\d+\n',open(d + '/SYSTEM.CNF').read())[1]
            if not exists(mf): return 1

            f = open(mf,'rb')
            size = f.seek(0,2)
            f.seek(0)
            if f.read(4) != b'\x7FELF': return 1

            def read32(): return int.from_bytes(f.read(4),'little')
            def skip(n): f.seek(n,1)
            def cs(): return size-f.tell()
            def reads(max=0xFF):
                t = b''
                for _ in range(max):
                    t += f.read(1)
                    if t[-1] == 0: break
                return t
            def testb():
                b = f.read(1)
                if b: f.seek(-1,1)
                return bool(b)

            f.seek(0x38)
            hsize = read32()
            load = read32()
            f.seek(load)

            ENTRY_SIZE = 4 * 11
            def read_table(ver=0) -> float:
                fs = read32()
                if fs == 0 or (fs*(ENTRY_SIZE + (4 if ver == 0 else 0))) > cs(): return -1

                tab = []
                for i in range(fs):
                    if read32() != i: return -2 # ID
                    t = read32()
                    if t > 0xFF: return -3
                    if t > 0x10: return -3.1 # type
                    if i == 0 and t != 1: return -3.2
                    if ver == 1: skip(4)

                    s = read32()
                    if s == 0: return -4 # size
                    o = read32() * 0x800

                    no = read32()
                    if no == 0: return -6.1 # name offset
                    no = no - load + hsize
                    if no < 0 or no > size: return -6 # name offset

                    skip(4) # hash
                    if read32() not in (0x7D6,0x7D5): return -8 # ?
                    for _ in range(4):
                        if read32() > 0xFF: return -9 # small values

                    pos = f.tell()
                    f.seek(no)
                    n = reads()
                    if n[-1] != 0: return -10
                    try: n = n[:-1].decode('ascii')
                    except: return -10
                    f.seek(pos)

                    tab.append({
                        'o':o,
                        's':s,
                        'n':n or f'0x{i:x}.bin'
                    })

                return tab

            tabs = []
            while testb():
                cp = f.tell()
                r = read_table()
                if type(r) == list:
                    #print(f'Found table at 0x{cp:X} to 0x{f.tell():X}')
                    tabs.append(r)
                else:
                    #if r <= -8: print(f'0x{cp:X} 0x{f.tell()-4:X}',r)
                    f.seek(cp+4)

            f.seek(load)
            while testb():
                cp = f.tell()
                r = read_table(1)
                if type(r) == list:
                    #print(f'Found v1 table at 0x{cp:X} to 0x{f.tell():X}')
                    tabs.append(r)
                else:
                    #if r <= -8: print('v1',f'0x{cp:X}',f'0x{f.tell()-4:X}',r)
                    f.seek(cp+4)

            ds = os.path.getsize(i)
            for t in tabs:
                lt = max([x['o'] + x['s'] for x in t])
                if lt == ds:
                    for xf in t:
                        f.seek(xf['o'])
                        os.makedirs(o + '/' + os.path.dirname(xf['n']),exist_ok=True)
                        open(o + '/' + xf['n'],'wb').write(f.read(xf['s']))
                    f.close()
                    return
            f.close()
        case 'Allegro DAT':
            run(['allegro_dat','-e','-o',o + '\\',i,'*\\'])
            if os.listdir(o): return
        case 'Doom WAD':
            osj = OSJump()
            osj.jump(o)
            run(['wadext',i,'-nogfxconvert','-nosndconvert'])
            osj.back()
            if os.listdir(o) and os.listdir(o + '/' + os.listdir(o)[0]):
                td = o + '/' + os.listdir(o)[0]
                while exists(td):
                    try: copydir(td,o,True)
                    except PermissionError:pass
                return
        case 'Glacier RPKG':
            run(['rpkg','-extract_from_rpkg',i,'-output_path',o])
            if os.listdir(o) and os.listdir(o + '/' + os.listdir(o)[0]):
                td = o + '/' + os.listdir(o)[0]
                while exists(td):
                    try: copydir(td,o,True)
                    except PermissionError:pass
                return
        case 'Glacier PKG Def':
            run(['rpkg','-decrypt_packagedefinition_thumbs',i,'-output_path',o])
            if os.listdir(o): return
        case 'Blur PAK': return quickbms('blur')
        case 'Konami DPG':
            if db.print_try: print('Trying with custom extractor')

            inf = open(i,'rb')
            def readstr():
                t = b''
                while True:
                    b = inf.read(1)
                    if b == b'\x00': break
                    t += b
                return t.decode()
            assert inf.read(8) == b'DP2\x1A0001'
            inf.seek(4,1)
            nfs = int.from_bytes(inf.read(4),byteorder='little')
            offs = [int.from_bytes(inf.read(4),byteorder='little') for _ in range(nfs+1)]
            fnms = [readstr() for _ in range(nfs)]

            for idx in range(nfs):
                tof = open(o + '/' + fnms[idx],'wb')
                inf.seek(offs[idx])
                print(hex(inf.tell()),fnms[idx])
                siz = int.from_bytes(inf.read(4),byteorder='little') - 5
                skp = 4

                inf.seek(skp + siz,1)
                while inf.read(1) != b'\x11':
                    skp += 1

                inf.seek(offs[idx] + 4 + skp)
                tof.write(inf.read(siz))
                tof.close()
            if os.listdir(o): return
        case 'Teardown Encrypted File':
            of = o + '\\' + basename(o) + '_'
            run(['tdedecrypt',i + '_',of])
            if exists(of[:-1]) and (os.path.getsize(of[:-1]) or not os.path.getsize(i)): return
        case 'Unreal Engine Package':
            if '/Content/' in i.split()[-1].replace('\\','/'): prgf = dirname(i.replace('\\','/').rsplit('/Content/',1)[0]) + '/Engine/Programs'
            else: prgf = None
            run(['unrealpak',i,'-Extract',o])
            if prgf and exists(prgf): remove(prgf)
            if os.listdir(o): return

            run(['repak','unpack','-o',o,'-q','-f',i])
            if os.listdir(o): return
        case 'Unreal ZenLoader':
            if '/Content/' in i.split()[-1].replace('\\','/'): prgf = dirname(i.replace('\\','/').rsplit('/Content/',1)[0]) + '/Engine/Programs'
            else: prgf = None
            run(['unrealpak',i,'-Extract',o])
            if prgf and exists(prgf): remove(prgf)
            if os.listdir(o): return

            run(['zentools','ExtractPackages',dirname(i),o,'-PackageFilter=' + i])[1]
            remove(o + '/PackageStoreManifest.json')
            if os.listdir(o): return
        case 'Danganronpa WAD':
            if db.print_try: print('Trying with wad_archiver')
            db.get('wad_archiver')
            from bin.wad_archiver import Commands # type: ignore
            class Args:
                input = i
                output = o
                silent = True
            Commands.extract_files(Args)
            if os.listdir(o): return
        case 'Valve Package':
            run(['vpkedit','-o',o,'--no-progress','-e','/',i])
            if os.listdir(o): return
        case 'Direct Storage Archive':
            run(['unpsarc',i,o])
            if os.listdir(o): return
        case 'NSMBW Coin World ARC':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            f.skip(6)

            fc = f.readu16()
            fs = []
            for _ in range(fc):
                fm = [f.read(0x40).strip(b'\0').decode()]
                f.skip(4)
                fm.append(f.readu32())
                f.skip(4)
                fm.append(f.readu32())
                fs.append(fm)
            for of in fs:
                tof = xopen(o + '/' + of[0],'wb')
                f.seek(of[2])
                tof.write(f.read(of[1]))
                tof.close()
            f.close()
            if fs: return
        case 'Arc System Works PAC': return quickbms('arcsys')
        case 'Chrome PAK':
            run(['chrome-pak','-u',i,o])
            if os.listdir(o): return
        case 'PS3/PSV PUP':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            PUPMAP = {
            1:{
                0x100: 'version.txt',
                0x101: 'license.xml',
                0x102: 'promo_flags.txt',
                0x103: 'update_flags.txt',
                0x104: 'patch_build.txt',

                0x200: 'ps3swu.self',
                0x201: 'vsh.tar',
                0x202: 'dots.txt',
                0x203: 'patch_data.pkg',

                0x501: 'spkg_hdr.tar',

                0x601: 'ps3swu2.self',
            },
            2:{
                0x100: 'version.txt',
                0x101: 'license.xml',

                0x200: 'psp2swu.self',
                0x204: 'cui_setupper.self',
                0x221: 'vs0_patch_tar_info.txt',
                0x231: 'vs0_patch_tar_2_info.txt',

                0x300: 'update_files.tar',
                0x302: 'SLB2',
                0x303: 'os0',
                0x304: 'vs0',
                0x305: 'unk_305',
                0x306: 'unk_306',
                0x307: 'unk_307',
                0x308: 'unk_308',
                0x309: 'unk_309',
                0x30A: 'unk_30A',
                0x30B: 'unk_30B',
                0x30C: 'unk_30C',
                0x30D: 'unk_30D',
                0x30E: 'unk_30E',
                0x30F: 'unk_30F',
                0x310: 'unk_310',
                0x311: 'vs0_patch_tar',
                0x312: 'vs0_patch_tar_2',
                0x313: 'sysscon_type_0',
                0x314: 'sysscon_type_1',
                0x315: 'sysscon_type_2',
                0x316: 'sysscon_type_3',
                0x317: 'sysscon_type_4',
                0x318: 'sysscon_type_5',
                0x319: 'sysscon_type_6',
                0x31A: 'sysscon_type_7',
                0x31B: 'sysscon_type_8',
                0x31C: 'sysscon_type_9',

                0x400: 'package_scewm.wm',
                0x401: 'package_sceas.as',

                0x2005: 'cp_es1_fw',
                0x2006: 'cp_es2_fw',
            }}

            f = File(i,endian='<')
            assert f.read(7) == b'SCEUF\0\0'
            f.skip(1)
            fv = f.readu64()
            if fv > 0xFFFFFFFFFFF:
                f.skip(-8)
                f._end = '>'
                fv = f.readu64()

            assert fv in (1,2) # PS3,PSV

            if fv in (1,2): f.skip(8)
            segs = f.readu64()
            assert 0xFFFFFFFFFFF >= segs
            if fv == 1: f.skip(16)
            elif fv == 2: f.skip(96)

            fs = []
            for _ in range(segs):
                fs.append((f.readu64(),f.readu64(),f.readu64()))
                f.skip(8)
            for of in fs:
                f.seek(of[1])
                if of[0] == 0x101:
                    xml = f.read(5)
                    f.skip(-5)
                    if xml in (b'<xml ',b'<?xml'): n = 'license.xml'
                    else: n = 'resource.txt'
                else: n = PUPMAP[fv].get(of[0],hex(of[0]))
                tof = xopen(o + '/' + n,'wb')
                tof.write(f.read(of[2]))
                tof.close()
            if fs: return
        case 'RPG Maker Archive (XP/VX/VX Ace)':
            run(['rpgmakerdecrypter',i,'-w','-o',o])
            if os.listdir(o): return
        case 'RDB':
            run(['cethleann','--rdb','-k','-p','-y','-z',o,dirname(i),'--filelist',basename(i)])
            if os.listdir(o): return
        case 'Konami GAME.DAT':
            db.get('ddrutil')
            if db.print_try: print('Trying with ddrutil')
            from bin.ddrutil import FileTable,FILE_TABLE_OFFSET,decompress # type: ignore

            f = open(i,'rb')
            f.seek(FILE_TABLE_OFFSET)
            ft = FileTable(f)
            d = b''
            for fe in ft.entries:
                if not fe.is_valid(): continue
                of = open(o + '/' + hex(fe.filename_hash),'wb')
                f.seek(fe.offset)
                d = f.read(fe.length)
                if fe.is_compressed(): d = decompress(d)
                of.write(d)
                of.close()
            f.close()
            if os.listdir(o): return
        case 'Hollow Knight Save':
            if db.print_try: print('Trying with custom extractor')
            try: from Cryptodome.Cipher import AES # type: ignore
            except ImportError: from Crypto.Cipher import AES # type: ignore
            from base64 import b64decode

            f = open(i,'rb')
            f.seek(0x19)
            dat = f.read().split(b'=')[0]
            f.close()
            dat = AES.new(b'UKu52ePUBwetZ9wNX88o54dnfKRu0T1l',AES.MODE_ECB).decrypt(b64decode(dat + b'===='))

            open(o + '/' + tbasename(i) + '.json','wb').write(dat[:-dat[-1]])
            return
        case 'Initial D XAF':
            run(['assamunpack',i],cwd=o)
            if os.listdir(o): return
        case 'Safari WebArchive':
            db.get('pywebarchive')
            if db.print_try: print('Trying with pywebarchive')
            import bin.webarchive # type: ignore

            try:
                with bin.webarchive.open(i) as f: f.extract(o + '/' + tbasename(i) + '.html',False)
            except bin.webarchive.WebArchiveError: pass
            else: return
        case 'WIM':
            run(['wimlib','apply',i,o])
            if os.listdir(o): return

            return extract(i,o,'7z')
        case 'WATCOM Archive':
            if db.print_try: print('Trying with wpack')
            run(['msdos',db.get('wpack'),i],print_try=False,cwd=o)
            if os.listdir(o): return
        case 'RPACK':
            if db.print_try: print('Trying with custom extractor') # https://github.com/Qivex/rpack-extract/blob/main/rpack-extract.lua
            raise NotImplementedError
            from lib.file import File

            f = File(i,endian='<')
            assert f.read(4) == b'RP6L','Invalid RPACK file'
            if f.readu32() == 4: offm = 16
            else: assert False,"Unknown offset multiplier"

            cmp = f.readu32()
            assert cmp in (0,),'Unknown compression method'

            pc,sc,fc,fncl,fnc,bs = f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32(),f.readu32()
            secis = {}
            for _ in range(sc):
                s = {'type':f.readu8()}
        case 'Konami LZSS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            f = File(i,endian='<')
            l = f.readu32()
            if not l: return 1
            of = open(o + '/' + basename(i)[:(-1 if i[-1] in 'zZ' else None)],'wb')

            ring = [b'\0'] * 0x1000
            rpos = 0x0FEE
            ctrlw = 1

            c1 = c2 = co = cl = 0
            b = b''
            while l > 0:
                if ctrlw == 1: ctrlw = 0x100 | f.readu8()

                if ctrlw & 1:
                    b = f.read(1)
                    of.write(b)
                    ring[rpos] = b
                    rpos = (rpos + 1) % 0x1000
                    l -= 1
                else:
                    c1,c2 = f.readu8(),f.readu8()
                    cl = (c2 & 0x0F) + 3
                    co = ((c2 & 0xF0) << 4) | c1

                    for _ in range(cl):
                        of.write(ring[co])
                        ring[rpos] = ring[co]
                        co = (co + 1) % 0x1000
                        rpos = (rpos + 1) % 0x1000
                        l -= 1

                ctrlw >>= 1

            of.close()
            return
        case 'Minecraft PCK': return quickbms('minecraft_pck')
        case 'Mo\'PaQ':
            run(['mpqextractor','-e','*','-o',o,i])
            if os.listdir(o): return
        case 'IPS Patch'|'IPS32 Patch':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            f = File(i)
            i32 = f.read(5) == b'IPS32'

            rof = f.readu32 if i32 else f.readu24
            eof = int.from_bytes(b'EEOF' if i32 else b'EOF')
            off = s = 0
            d = b''
            while True:
                off = rof()
                if off == eof:break
                s = f.readu16()
                if s == 0: d = f.readu16()*f.read(1)
                else: d = f.read(s)
                open(o + '/' + hex(off)[2:].upper().zfill(8 if i32 else 6) + '.bin','wb').write(d)
            if os.listdir(o): return
        case 'Bunny Pro. Das2 DPK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            f = File(i,endian='<')
            assert f.read(2) == b'PA'
            fc = f.readu16()
            assert fc > 0 and f.readu32() > 0
            fs = [(f.read(0x10).rstrip(b'\0').decode('ascii'),f.readu32()) for _ in range(fc)]

            for n,s in fs: open(o + '/' + n,'wb').write(f.read(s))
            f.close()

            if fs: return
        case 'The Sims FAR'|'Quake PAK'|'WAD'|'Agon Game Archive'|'Alien Vs Predator Game Data'|'Allods 2 Rage Of Mages Game Archive'|\
             'American Conquest 2 Game Archive'|'ASCARON Entertainment Game Archive'|'Bank Game Archive'|'Battlezone 2 Game Archive'|\
             'BioWare Entity Resource'|'Bloodrayne Game Archive'|'BOLT Game Archive'|'Broderbund Mohawk Game Archive'|'Chasm Game Archive'|\
             'CI Games Archive'|'Creative Assembly Game Data'|'Dark Reign Game Archive'|'Destan Game Archive'|'Digital Illusions Game Archive'|\
             'Dynamix Game Archive'|'Earth And Beyond Game Archive'|'Electronic Arts LIB'|'Empire Earth 1 Game Archive'|'Ensemble Studios Game Archive'|\
             'Etherlords 2 Game Archive'|'F.E.A.R. Game Archive'|'Final Fantasy Game Archive'|'Holistic Design Game Archive'|\
             'Gabriel Knight 3 Barn Game Archive'|'Haemimont Games AD Game Archive'|'Harry Potter: Quidditch World Cup Game Archive'|\
             'Highway Pursuit Game Archive':
            if db.print_try: print('Trying with gameextractor')
            run(['java','-jar',db.get('gameextractor'),'-extract','-input',i,'-output',o],print_try=False,cwd=dirname(db.get('gameextractor')))
            remove(dirname(db.get('gameextractor')) + '/logs')
            if os.listdir(o): return
        case 'Cosmo Volume Game Archive'|'Dark Ages Map File'|'Build Engine RFF'|'God of Thunder Game Archive'|'Highway Hunter Game Archive':
            run(['gamearch',i,'-X'],cwd=o)
            if os.listdir(o): return
        case 'Build Engine Group'|'Descent Game Archive'|'EPF Game Archive':
            if not extract4(i,o,'Cosmo Volume Game Archive'):return # gamearch
            if not extract4(i,o,'The Sims FAR'):return # gameextractor
        case 'HMM Packfile':
            if db.print_try: print('Trying with hmmunpack')
            db.get('hmmunpack')
            import bin.hmmunpack as hmmunpack # type: ignore

            hmmunpack.print = lambda *_,file=None:None
            hmmunpack.__Path = hmmunpack.Path
            hmmunpack.Path = lambda *args,**kwargs:hmmunpack.__Path(*((o,) if args == (f'output-{i}',) else args),**kwargs)
            hmmunpack.open = lambda *args,**kwargs:open('NUL' if args[0] == f'extract-report-{i.replace("\\","-").replace("/","-")}.txt' else args[0],*args[1:],**kwargs)

            hmmunpack.extract(i)
            if os.listdir(o): return
        case 'Compressed File Library':
            run(['uncfl',i],cwd=o)
            if os.listdir(o): return
        case 'ActiveMime':
            afp = db.get('amime')
            af = open(afp).read()
            if 'def main():' in af: open(afp,'w').write(af.split('def main():')[0])

            if db.print_try: print('Trying with amime')
            import bin.amime as amime # type: ignore

            class CDat(bytes):
                def encode(self,enc:str):
                    assert enc == 'hex'
                    return self.hex()
                def startswith(self,prefix,start=None,end=None):
                    if isinstance(prefix,str): prefix = prefix.encode('latin-1')
                    return super().startswith(prefix, start, end)
                def __getitem__(self,i):
                    if type(i) == slice: return self.__class__(super().__getitem__(i))
                    return super().__getitem__(i)
            amime.__zlib_decompress = amime.zlib.decompress
            amime.zlib.decompress = lambda *args,**kwargs:CDat(amime.__zlib_decompress(*args,**kwargs))

            dat = CDat(open(i,'rb').read())
            if amime.ActiveMimeDocument.is_activemime(dat[:14]): amd = amime.ActiveMimeDocument(dat,amime.ActiveMimeDocument.is_base64(dat[:14]))
            else: amd = amime.ActimeMimeParser().process(dat) # typo in amime.py
            assert amd
            open(o + '/' + hashlib.sha256(amd.data).hexdigest(),'wb').write(amd.data)
            del amd
            return
        case 'FATX':
            run(['chextract-fatx',tf,o])
            if os.listdir(o): return
        case 'QOOB Flash IMG':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            tp = f.read(4)

            n = f.read(0xF4).rstrip(b'\0').decode()
            if '\n' in n: n = n.split('\n')[0]
            if not n: n = tbasename(i)
            n += {b'(C) ':'.qoob',b'ELF0':'.elf',b'DOL0':'.dol',b'BIN0':'.bin'}[tp]

            f.seek(0x100)
            open(o + '/' + n,'wb').write(f.read())
            f.close()
            return
        case 'Viper Flash IMG':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            f.seek(0x10)
            n = f.read(0x10).rstrip(b'\0').decode()
            if '\n' in n: n = n.split('\n')[0]
            if not n: n = tbasename(i)
            n += '.vipr'

            f.seek(0x20)
            open(o + '/' + n,'wb').write(f.read())
            f.close()
            return
        case 'Blitz Games Archive': return quickbms('blitz_games')
        case 'Digimon Story Lost Evolution PAK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            fc = f.readu32()
            assert f.read(4) == b'2.01'
            f.skip(8)

            fs = []
            for _ in range(fc):
                off = f.readu32()
                f.skip(4)
                siz = f.readu32()
                if not f.readu32():
                    siz -= 5
                    off += 5
                fs.append((off,siz))

            mx = len(str(len(fs)))
            for ix,fe in enumerate(fs):
                f.seek(fe[0])

                tag = f.read(4)
                f.skip(-4)
                if tag[::-1] in (b'NCGR',b'NCLR',b'NSCR',b'NANR',b'NCBR',b'NCER',b'NFTR',b'MAPI'):
                    ext = tag.decode()[::-1].lower()
                elif tag == b'NARC': ext = 'narc'
                else: ext = 'bin'

                open(o + f'/{ix:0{mx}d}.{ext}','wb').write(f.read(fe[1]))
            if fs: return
        case 'GBA ADS MMSTR':
            mfp = db.get('load_from_mmstr')
            mf = open(mfp).read()
            if 'extract_mmstr_archive("commonresources.mmstr", True)' in mf: open(mfp,'w').write(mf.split('extract_mmstr_archive("commonresources.mmstr", True)')[0])

            if db.print_try: print('Trying with load_from_mmstr')
            import bin.load_from_mmstr as lfmmstr # type: ignore
            lfmmstr.print = lambda *args,**kwargs:None
            _splitext = lfmmstr.os.path.splitext
            lfmmstr.os.path.splitext = lambda *args,**kwargs: (o,) if args == (basename(i),) else _splitext(*args,**kwargs)
            REPM = {
                '*':'_',
                '?':'_',
                '\\':'_',
                '/':'_',
                '<':'_',
                '>':'_',
                ':':'_',
                '\n':' ',
                '\x99':'™',
                '\xA9':'©',
                '\xAE':'®',
                '"':"''",
            }
            _join = lfmmstr.os.path.join
            lfmmstr.os.path.join = lambda i1,i2: _join(i1,i2.translate(str.maketrans(REPM)))

            lfmmstr.extract_mmstr_archive(i,True)
            if os.listdir(o): return
        case 'Exient XPK':
            f = open(i,'rb')
            ver = f.read(1)[0]
            if ver == 1:
                f.seek(0x10)
                v12 = b''
                for _ in range(3):
                    v12 += f.read(4)
                    f.seek(4,1)
                f.close()
                if not sum(v12): return quickbms('angry_birds_starwars')
            else: f.close()

            return quickbms(['nfshp2010wii','angry_birds_go','xpk2'][ver])
        case 'NMZIP':
            import zlib
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            f.seek(0x20)
            data = zlib.decompress(f.read())
            f.close()

            ext = 'bin'
            if data[:4] == b'1LCR': ext = 'llcr'
            elif data[:4] == b'DTPK': ext = 'snd'
            elif data[:4] == b'\0\1\0\0' and data[5:8] == b'\0\0\0' and data[4] in (3,1,7,0x11,0xb):
                ext = 'pol'
            elif 0 < int.from_bytes(data[:4]) < 0xff and 0 < int.from_bytes(data[4:8]) < 0xff and 0 < int.from_bytes(data[8:12]) < 0xff:
                ext = 'mot'
            elif (len(data) == 0x004800 and data[-4: ] == b'\xFF\xFF\xFF\xFF') or\
                 (len(data) == 0x1DED10 and data[  :4] == b'\x97Z+C'):
                   ext = 'def'

            open(o + '/' + tbasename(i) + '.' + ext,'wb').write(data)
            return
        case 'TTGames DAT':
            if i.lower().endswith('.hdr'):
                i = i[:-3] + 'dat'
                if not exists(i): return 1

            return quickbms('ttgames')
        case 'XPAC':
            import zlib
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            hshs = {int(x[0],16):x[1][2:] for x in re.findall(r'case 0x([A-F\d]{8}): return "([^"]+)";',open(db.get('sasr_xpac_hashes'),encoding='utf-8').read())}
            hshs |= {0x72E575D5:'Resource/Audio/cars/AIAI.abc'         ,0x28A48754:'Resource/Audio/cars/AVATAR.abc'  ,0x937805F5:'Resource/Audio/cars/BANJO.abc',
                     0xB2AEE867:'Resource/Audio/cars/BDJOE.abc'        ,0xF71A6E43:'Resource/Audio/cars/BEAT.abc'    ,0xD88EA041:'Resource/Audio/cars/BIG.abc',
                     0xB594EA59:'Resource/Audio/cars/BILLY_HATCHER.abc',0x2CC5AD38:'Resource/Audio/cars/EGGMAN.abc'  ,0xD4202A23:'Resource/Audio/cars/HOUSEOFTHEDEAD.abc',
                     0x1C359E16:'Resource/Audio/cars/MII.abc'          ,0x5541CF1D:'Resource/Audio/cars/RYO_BIKE.abc',0x8C56C758:'Resource/Audio/cars/RYO_FL.abc',
                     0xE0289AB1:'Resource/Audio/cars/SHADOW.abc'       ,0x7841A33C:'Resource/Audio/cars/TAILS.abc'   ,0x360B3EA4:'Resource/Audio/cars/ULALA.abc',
                     0x69D5A62D:'Resource/Audio/cars/ALEXKIDD.abc'     ,0x00022583:'Resource/Audio/wav/COM_FRE/COM_COL_H_126.str'}
            hshs |= {0x77CC3C42:'Resource/DebugLights.zig',0x53310504:'Resource/Machine.zif',0xB0784A37:'Resource/Machine.zig',0x98F6FCDF:'$Unknown/Pipe.zif',0x0238A928:'$Unknown/Pipe.zig'}
            hshs |= {0xB3E850E4:'$Unknown/Unk1.zig',0x5875B07C:'$Unknown/Unk1.zif',0x8A3B39B7:'$Unknown/Particles.zig',0x71CA44A2:'$Unknown/Effects.zig',0x3C5249FB:'$Unknown/Effects.zif',0xC03C389F:'$Unknown/Particles.zif'}
            for h in (0x00FC9F2D,0x0AC1CFB4,0xF0B4ADEA,0x55F4D9E6,0x71F1ACF3,0x4638DEE8): hshs[h] = f'$Unknown/{h:08X}.zig'
            for h in (0x09A915C5,0x94AAD2E5,0x15048861,0x25A5E8D2): hshs[h] = f'$Unknown/{h:08X}.zif'
            for h in (0x0090AE05,0x9D853559,0x7EFC3B8B): hshs[h] = f'$Unknown/{h:08X}.tso'
            for h in (0xFFE6BEC5,0x59C8DA80): hshs[h] = f'$Unknown/{h:08X}.txt'

            f = File(i,endian='<')
            f.skip(12)
            c = f.readu32()
            f.skip(4)

            fs = []
            for _ in range(c):
                f.skip(4)
                hs = f.readu32()
                off = f.readu32()
                zsiz = f.readu32()
                siz = f.readu32()
                fs.append((hshs[hs] if hs in hshs else f'$Unknown/{hs:08X}',off,zsiz,siz))

            for of in fs:
                f.seek(of[1])
                zlb = of[2] >= 12 and f.read(2) == b'\x78\xDA'
                f.skip(-2)
                if zlb: d = zlib.decompress(f.read(of[2]))
                else: d = f.read(of[2] or of[3])
                xopen(o + '/' + of[0],'wb').write(d)
            if fs: return
        case 'IFF Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            assert f.read(4) == b'FORM'
            lng = f.readu32()
            if lng != f.size:
                f._end = '<'
                f.skip(-4)
                nlng = f.readu32()
                if nlng != f.size and abs(f.size-nlng) > abs(f.size-lng):
                    f._end = '>'
            BTYPE = f.read(4)

            cnt = 0
            FNAMES = []
            FDATA = {}
            def read_block(fpath:str,fname:str=None,addext=True):
                nonlocal cnt
                name = f.read(4)
                size = f.readu32()
                pos = f.pos
                epos = pos + size

                if name == b'FORM':
                    if BTYPE != b'4WRT':
                        typ = f.read(4).strip(b'\0 \t\r\n')

                        if BTYPE in (b'NSF1',b'NMF1') and typ[3:].isdigit(): typ = typ[:3]

                        try: typ = '.' + typ.decode().lower()
                        except: typ = '.iff'
                        f.skip(-12)

                        if not fname and FNAMES: fname = FNAMES.pop(0)
                        fname = fpath + '/' + (fname or f'{cnt}')
                        fcnt = 1
                        while exists(fname + (typ if addext else '')):
                            if fcnt > 1: fname = fname.rsplit('_',1)[0]
                            fname += f'_{fcnt}'
                            fcnt += 1

                        xopen(fname + (typ if addext else ''),'wb').write(f.read(8 + size))
                        cnt += 1
                        spath = fname + '_EXT'
                    else: spath = fpath

                    f.seek(pos + 4)
                    while f.pos < epos: read_block(spath)
                elif name == b'WRCH' and BTYPE == b'NSF1':
                    f.skip(4)
                    while f.pos < epos: read_block(fpath,f.read(f.readu32()).rstrip(b'\0').replace(b'\0',b' ').decode())
                elif name == b'NETN' and BTYPE in (b'NSF1',b'NMF1'):
                    FNAMES.append(f.read(f.readu32()).rstrip(b'\0').replace(b'\0',b' ').decode())

                elif name == b'RIdx' and BTYPE == b'IFRS':
                    fc = f.readu32()
                    fs = []
                    for _ in range(fc):
                        fs.append((f.read(4).decode() + str(f.readu32()),f.readu32()))
                        cnt += 1
                    for fe in fs:
                        f.seek(fe[1])
                        t = f.read(4)
                        open(fpath + '/' + fe[0] + '.' + t.decode(),'wb').write(f.read(f.readu32()))
                    if fc: return 1
                elif name == b'CHRS' and BTYPE == b'FTXT':
                    open(fpath + f'/{basename(i)}{cnt}.txt','wb').write(f.read(size).split(b'\0')[0])
                    cnt += 1

                elif name == b'TEXT' and BTYPE == b'HEAD':
                    if not 'TXT' in FDATA:
                        FDATA['TXT'] = open(fpath + f'/{basename(i)}{cnt}.txt','wb')
                        FDATA['INDENT'] = 0
                        cnt += 1
                    FDATA['TXT'].write(b'  '*FDATA['INDENT'] + f.read(size) + b'\n')
                elif name == b'NEST' and BTYPE == b'HEAD' and 'TXT' in FDATA:
                    FDATA['INDENT'] = f.readu16()

                elif (name == b'DOCU' and BTYPE == b'4WRT') or (name == b'DOC ' and BTYPE == b'WORD'):
                    FDATA['TXT'] = open(fpath + f'/{basename(i)}{cnt}.txt','wb')
                    cnt += 1
                elif (name == b'PARA' and BTYPE == b'4WRT') or (name in (b'HEAD',b'FOOT',b'PARA') and BTYPE == b'WORD'):
                    FDATA['TXT'].write(b'\r\n')

                elif name == b'TEXT' and BTYPE == b'4WRT':
                    FDATA['TXT'].write(f.read(size))
                elif name == b'PICT' and BTYPE == b'4WRT':
                    p = f'{basename(i)}{cnt}.pict'
                    open(fpath + '/' + p,'wb').write(f.read(size))
                    cnt += 1
                    FDATA['TXT'].write(f'<{p}>'.encode())

                elif name == b'TABS' and BTYPE == b'WORD':
                    FDATA['TXT'].write(b'\t')
                elif name == b'TEXT' and BTYPE == b'WORD':
                    FDATA['TXT'].write(f.read(size) + b'\r\n')

                elif BTYPE == b'AUDO':
                    f.skip(-8)
                    size = f.readu32()
                    epos = pos + size
                    fc = f.readu32()
                    fs = []
                    for _ in range(fc): fs.append(f.readu32())
                    for off in fs:
                        f.seek(off)
                        s = f.readu32()
                        open(fpath + f'/{cnt}.wav','wb').write(f.read(s))
                        cnt += 1

                f.seek(epos)

            while (f.pos+8) <= f.size:
                if read_block(o):break
                if f.pos % 2: f.skip(1)
            if 'TXT' in FDATA:
                try: FDATA['TXT'].close()
                except: pass
            if cnt: return
        case 'Xbox XB Compressed':
            run(['xbdecompress','/Y','/T',i,o])
            if os.listdir(o): return
        case 'Xbox FArc':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            assert f.read(4) == b'FArc'
            f.skip(8)
            fs = []
            foff = 0
            while not foff or (f.pos+9) < foff:
                nm = b''
                while True:
                    b = f.read(1)
                    if not b: raise EOFError
                    if b == b'\0': break
                    nm += b
                off = f.readu32()
                if not foff: foff = off
                fs.append((nm.decode(),off,f.readu32()))

            for fe in fs:
                f.seek(fe[1])
                xopen(o + '/' + fe[0],'wb').write(f.read(fe[2]))
            if fs: return
        case 'RouterOS Package':
            db.get('npkpy')

            import importlib,importlib.util,zlib
            class RedSpec:
                @classmethod
                def find_spec(cls,fullname,path,target=None):
                    if '.npk.' in fullname: rename = fullname.replace('.npk.','.')
                    elif fullname == 'npkpy.npk': rename = 'npkpy'
                    elif fullname == 'bin.npkpy._npk': rename = 'bin.npkpy.npk'
                    elif fullname.startswith('npkpy'): rename = fullname
                    else: rename = None
                    if rename:
                        if rename.startswith('npkpy.') or rename == 'npkpy': rename = 'bin.' + rename
                        spec = importlib.util.find_spec(rename)
                        spec.name = fullname
                        spec.fake = rename
                        spec.loader = cls
                        return spec
                @staticmethod
                def create_module(spec):return importlib.import_module(spec.fake) if hasattr(spec,'fake') else None
                @staticmethod
                def exec_module(spec):pass
            sys.meta_path.append(RedSpec)

            class Empty:pass
            com = Empty()
            com.sha1_sum_from_file = lambda x: hashlib.sha1(open(x,'rb').read()).digest()
            com.sha1_sum_from_binary = lambda x: hashlib.sha1(x).digest()
            for e in ('','Id','MagicBytes'): setattr(com,f'NPK{e}Error',Exception)

            sys.modules['npkpy.npk'] = __import__('bin.npkpy')
            sys.modules['npkpy.common'] = com

            from pathlib import Path

            if db.print_try: print('Trying with npkpy')
            from bin.npkpy._npk import Npk # type: ignore

            try: npk = Npk(Path(i))
            except: return 1
            inf = b''
            for f in npk.pck_cnt_list:
                if f.cnt_id_name in ('PckReleaseTyp','CntArchitectureTag','PckDescription','PckEckcdsaHash'): inf += f.cnt_id_name[3:].encode() + b': ' + f.cnt_payload + b'\n'
                elif f.cnt_id_name == 'CntZlibDompressedData': open(o + '/data.bin','wb').write(zlib.decompress(f.cnt_payload))
                elif f.cnt_id_name == 'CntSquashFsImage':
                    tf = o + '/cnt.squashsf'
                    open(tf,'wb').write(f.cnt_payload)
                    if not extract(tf,o,'SquashFS'): remove(tf)
            if inf: open(o + '/package.txt','wb').write(inf)
            return
        case 'Zeebo Resources':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            fs = []
            if f.read(8) == b'PPCPRCON':
                fc = f.readu32()

                for _ in range(fc): fs.append((f.readu32(),f.readu32(),f.readu32(),f.readu8()))

                fns = {}
                for fe in fs:
                    f.seek(fe[0])
                    fn = str(fe[2]).zfill(4)

                    if fe[2] in fns: fn += f'_{fns[fe[2]]}'
                    else: fns[fe[2]] = 0
                    fns[fe[2]] += 1

                    fn += '.'
                    if fe[3] == 2:
                        fn += 'txt'
                        if f.readu16('>') == (fe[1] - 2): fn += '.res'
                    else: fn += fix_zeebo(f,fe[3]) or f'{fe[3]}.unk'

                    f.seek(fe[0])
                    open(o + '/' + fn,'wb').write(f.read(fe[1]))
            else:
                f.seek(0)
                fc = f.readu32()
                boff = 4 + fc * 0x48
                for _ in range(fc): fs.append((f.read(0x40).strip(b'\0').decode(),boff + f.readu32(),f.readu32()))
                for fe in fs:
                    f.seek(fe[1])
                    open(o + '/' + fe[0],'wb').write(f.read(fe[2]))

            if fs: return
        case 'Zeebo FUFS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'FUFS'
            f.skip(4)
            fc = f.readu32()

            fs = []
            for _ in range(fc): fs.append((f.readu32(),f.readu32(),f.readu32()))
            for fe in fs:
                f.seek(fe[0])

                tag = f.read(4)
                ext = fix_zeebo(f)
                if not ext and fe[2] < 0x1000:
                    try: (tag + f.read(fe[2]-4)).decode('utf-8')
                    except: ext = 'bin'
                    else: ext = 'txt'
                else: ext = 'bin'

                f.seek(fe[0])
                open(o + '/' + hex(fe[1])[2:].upper().zfill(8) + '.' + ext,'wb').write(f.read(fe[2]))
            if fs: return
        case 'Zeebo PLZP':
            import zlib
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            f.seek(12)
            data = zlib.decompress(f.read())
            try: open(o + '/' + tbasename(i) + '.' + (fix_zeebo(data) or 'bin'),'wb').write(data)
            except zlib.error: pass
            else: return
        case 'ZLARC':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            fc = f.readu32()
            fso = [f.readu32() for _ in range(fc)]
            boff = f.readu32()

            fs = []
            for fo in fso:
                f.seek(fo)
                fs.append((boff + f.readu32(),f.readu32(),f.read(f.readu32()-1).decode()))
            for fe in fs:
                f.seek(fe[0])
                open(o + '/' + fe[2],'wb').write(f.read(fe[1]))
            if fs: return
        case 'ICU Data':
            run(['icupkg','-x','*','-d',o,'--ignore-deps','--auto_toc_prefix',i])
            if os.listdir(o): return
        case 'Unreal Engine Web Package':
            if inp.endswith('.data'): inp += '.js'
            elif inp.endswith('.data.gz'): inp = inp[:-2] + 'js.gz'
            assert exists(inp)
            if db.print_try: print('Trying with custom extractor')

            scr = open(i,encoding='utf-8').read()
            inf = json.loads(re.search(r'loadPackage\((\{.+\})\);\n',scr)[1])
            dirs = re.findall(r"Module\['FS_createPath'\]\(\"([^\"]+)\", *\"([^\"]+)\", *true, *true\);\n",scr)
            dat = re.search(r"var REMOTE_PACKAGE_BASE = '(.+)';\n",scr)[1]
            for d in dirs: mkdir(o + ('/' + d[0].strip('/') + '/').replace('//','/') + d[1])

            binp = inp
            if inp.endswith('.gz'): binp = inp[:-3]
            binp[:-3]
            for df in (dat,dat + '.gz',binp + '.data',binp + '.data.gz'):
                if exists(df): break
            else: return 1

            df = open(df,'rb')
            for fe in inf['files']:
                df.seek(fe['start'])
                xopen(o + '/' + fe['filename'].strip('/'),'wb').write(df.read(fe['end'] - fe['start']))
            return
        case 'BackupMii NAND Image':
            if db.print_try: print('Trying with custom extractor')
            try: from Cryptodome.Cipher import AES # type: ignore
            except ImportError: from Crypto.Cipher import AES # type: ignore

            if os.path.getsize(i) == 0x400:
                i = dirname(i) + '/nand.bin'
                assert exists(i)

            if os.path.getsize(i) != 0x21000400:
                kf = open(dirname(i) + '/keys.bin','rb')
            else:
                kf = open(i,'rb')
                kf.seek(0x21000000)

            kf.seek(0x100,1)
            open(o + '/OTP.bin','wb').write(kf.read(0x80))
            kf.seek(0x80,1)
            open(o + '/SEEPROM.bin','wb').write(kf.read(0x100))

            kf.seek(-0x200,1)
            open(o + '/boot1.hash','wb').write(kf.read(0x14))
            open(o + '/common.key','wb').write(kf.read(0x10))
            open(o + '/console.id','wb').write(kf.read(4))
            open(o + '/ECC_private.key','wb').write(kf.read(0x1E))
            kf.seek(-2,1)
            open(o + '/NAND.hmac','wb').write(kf.read(0x14))
            nand_key = kf.read(0x10)
            open(o + '/NAND.key','wb').write(nand_key)
            open(o + '/PRNG.seed','wb').write(kf.read(0x10))
            kf.seek(0x8C,1)
            open(o + '/ng.key','wb').write(kf.read(0x40))
            kf.close()

            from lib.file import File
            f = File(i,endian='>')
            noecc = os.path.getsize(i) == 0x20000000

            if noecc: noffs = (0x1FC00000,0x20000000,0x40000)
            else: noffs = (0x20BE0000,0x21000000,0x42000)
            f.seek(noffs[0] + 4)

            last = 0
            while f.pos < noffs[1]:
                cur = f.reads32()
                if cur > last: last = cur
                else: break
                f.skip(noffs[2] - 4)
            else: return 1
            fato = f.pos - 8 - noffs[2]
            fsto = fato + 0xC + (0x10000 if noecc else 0x10800)

            def get_fst(entry,path):
                f.seek(fsto + (entry // 0x40 * (0 if noecc else 2) + entry) * 0x20)
                fs = {
                    'path':path + '/' + f.read(0xC).replace(b'\0',b'').strip().decode('ascii').replace(':','-'),
                    'mode':f.readu8() & 1,
                    'attr':f.readu8(),
                    'sub':f.readu16(),
                    'sib':f.readu16(),
                    'size':f.readu32(),
                    'uid':f.readu32(),
                    'gid':f.readu16(),
                    'x3':f.readu32(),
                }
                if fs['sib'] != 0xFFFF: get_fst(fs['sib'],path)
                if fs['mode'] == 0:
                    mkdir(fs['path'])
                    if fs['sub'] != 0xFFFF: get_fst(fs['sub'],fs['path'])
                else:
                    of = xopen(fs['path'],'wb')

                    fat = fs['sub']
                    bsiz = 0
                    while fat < 0xFFF0:
                        f.seek(fat * (0x4000 if noecc else 0x4200))
                        cluster = []
                        for _ in range(8):
                            cluster.append(f.read(0x800))
                            if not noecc: f.skip(0x40)
                        data = AES.new(nand_key,AES.MODE_CBC,iv=bytes(0x10)).decrypt(b''.join(cluster))[:fs['size']-bsiz]
                        of.write(data)
                        bsiz += len(data)

                        fat += 6
                        f.seek(fato + (fat // 0x400 * (0 if noecc else 0x20) + fat) * 2)
                        fat = f.readu16()
                    of.close()
            get_fst(0,o + '/NAND')
            if os.listdir(o + '/NAND'): return
        case 'Wallpaper Engine PKG':
            run(['repkg','extract','-o',o,'-n','--no-tex-convert','--overwrite',i])
            if os.listdir(o): return
        case 'AMOS Memory Bank':
            if db.print_try: print('Trying with custom extractor')
            open(o + '/' + tbasename(i) + '.bin','wb').write(open(i,'rb').read()[20:])
            return
        case 'PS2 Memory Card':
            run(['mymc','-i',i,'extract','*'],cwd=o)
            if os.listdir(o): return
        case 'Coktel Vision STK':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            fc = f.readu16()
            fs = []
            for _ in range(fc):
                fs.append((f.read(13).split(b'\0')[0].decode('cp866'),f.readu32(),f.readu32(),f.readu8()))

            def decompress_chk(size:int):
                bidx = 4078
                buf = bytearray(b' ' * bidx + b'\0' * 36)
                dat = b''

                pos = f.pos
                cmd = 0
                while size > 0:
                    cmd >>= 1
                    if not cmd & 0x100: cmd = f.readu8() | 0xFF00

                    if cmd & 1:
                        b = f.reads()
                        dat += b
                        buf[bidx] = b[0]
                        bidx += 1
                        bidx %= 4096
                        size -= 1
                    else:
                        h,l = f.readu8(),f.readu8()
                        off = h | ((l & 0xF0) << 4)
                        leng = (l & 0x0F) + 3

                        for i in range(leng):
                            dat += bytes([buf[(off + i) % 4096]])
                            size -= 1
                            if size <= 0: break

                            buf[bidx] = buf[(off + i) % 4096]
                            bidx += 1
                            bidx %= 4096
                return dat
            def decompress():
                csize = usize = 0
                dat = b''
                while csize != 0xFFFF:
                    csize = f.readu16()
                    rsize = f.readu16()
                    usize += rsize

                    assert csize >= 4
                    f.skip(2)
                    dat += decompress_chk(rsize)
                assert len(dat) == usize
                return dat

            for fe in fs:
                f.seek(fe[2])
                if fe[3] == 2: dat = decompress()
                elif fe[3] > 0: dat = decompress_chk(f.readu32())
                else: dat = f.read(fe[1])
                open(o + '/' + fe[0],'wb').write(dat)
            if fs: return
        case 'SLUDGE Data File':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i)
            assert f.read(7) == b'SLUDGE\0'
            f.skip(0xAD + 2)

            dec_str = lambda s: ''.join(chr(x-1) for x in s)
            if f.readu8():
                for _ in range(f.readu16('>')): f.skip(f.readu16('>'))
                for _ in range(f.readu16('>')): f.skip(f.readu16('>'))
                fs = [dec_str(f.read(f.readu16('>'))) for _ in range(f.readu16('>'))]
            else: fs = None

            opts = open(o + '/' + tbasename(i) + '.slp','w',encoding='utf-8')
            opts.write('[SETTINGS]\n')

            opts.write('width=' + str(f.readu16('>')) + '\n')
            opts.write('height=' + str(f.readu16('>')) + '\n')

            opb = f.readu8()
            opts.write('fullscreen=' + ('Y' if opb & 2 else 'N') + '\n')
            opts.write('makesilent=' + ('Y' if opb & 8 else 'N') + '\n')
            opts.write('mouse=')
            if opb & 4 and opb & 0x10: opts.write('3')
            elif opb & 4: opts.write('2')
            elif opb & 0x10: opts.write('0')
            else: opts.write('1')
            opts.write('\n')
            opts.write('invisible=' + ('Y' if opb & 0x20 else 'N') + '\n')
            opts.write('showlogo=' + ('N' if opb & 0x40 else 'Y') + '\n')
            opts.write('showloading=' + ('N' if opb & 0x80 else 'Y') + '\n')

            opts.write('speed=' + str(f.readu8()) + '\n')

            f.skip(f.readu16('>') + 8)
            f.skip(f.readu16('>'))

            lngs = f.readu8()
            if lngs: opts.write('language=' + dec_str(f.read(f.readu16('>'))) + '\n')
            for _ in range(lngs):
                f.skip(2)
                f.skip(f.readu16('>'))

            opts.write('chrRender_max_readIni=' + ('Y' if f.readu8() else 'N') + '\n')
            opts.write('chrRender_max_enabled=' + ('Y' if f.readu8() else 'N') + '\n')
            opts.write('chrRender_max_softX=' + str(f.readfloat('<') * 16) + '\n')
            opts.write('chrRender_max_softY=' + str(f.readfloat('<') * 16) + '\n')

            assert dec_str(f.read(f.readu16('>'))) == 'okSoFar'

            clog = f.readu8()
            if clog: raise NotImplementedError
            opts.write('customicon=' + ('Y' if clog & 1 else 'N') + '\n')
            opts.write('customlogo=' + ('Y' if clog & 2 else 'N') + '\n')
            opts.close()

            f.skip(2)
            f.seek(f.readu32('<'))
            f.skip(f.readu32('<'))
            f.skip(f.readu32('<'))

            offs = [f.readu32('<') + f.pos]
            while f.pos < offs[0]: offs.append(f.readu32('<') + f.pos)
            mx = len(str(len(offs)-1))
            for ix,of in enumerate(offs):
                if fs: fn = fs[ix]
                else: fn = str(ix).zfill(mx)
                f.seek(of)
                xopen(o + '/' + fn,'wb').write(f.read(f.readu32('<')))
            if offs: return
        case 'Balko UFL Game Archive':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(8) == b'LiArFi\n\0'
            f.skip(4)
            f.seek(f.readu32())

            def read_dir(normal=True):
                f.skip(8)
                fc = f.readu32()
                if normal: path = o + '/' + f.read(f.readu16()+1).decode().strip('\\/')
                else: path = o

                fs = []
                for _ in range(fc):
                    fe = [f.read(f.readu8()+1),f.readu32(),f.readu32()]
                    f.skip(4)
                    if fe[1] == 0x20:
                        fe.append(f.readu32())
                        f.skip(12)
                    elif fe[1] != 0x10: raise NotImplementedError(str(f.pos))
                    fs.append(fe)

                for fe in fs:
                    f.seek(fe[2])
                    if fe[1] == 0x10: read_dir()
                    elif fe[1] == 0x20:
                        xopen(path + '/' + fe[0].decode().strip('\\/'),'wb').write(f.read(fe[3]))
            read_dir(False)
            if os.listdir(o): return
        case 'Anna-Marie Archive':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            if f.read(12) == b'Anna-Marie\x00\x00':
                f.seek(0x66)
                fs = []
                for _ in range(f.readu32()):
                    fe = [f.read(10).split(b'\0')[0].decode()]
                    f.skip(6)
                    fe.append(f.readu32())
                    fs.append(fe)
                for fe in fs:
                    open(o + '/' + fe[0],'wb').write(f.read(fe[1]))
                if fs: return
            else:
                f.skip(-12)
                c = 0
                while (f.pos+0xA0) < f.size:
                    size = f.readu32()
                    pos = f.pos
                    if size > 0x10:
                        if f.read(2) == b'BM' and f.readu32() == size: ext = 'bmp'
                        else: ext = 'bin'
                        f.seek(pos)
                    else: ext = 'bin'
                    open(o + f'/{c}.{ext}','wb').write(f.read(size))
                    c += 1
                if c: return
        case 'Ion Storm Resource':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.seek(0xC8)
            f.seek(f.readu32())
            fs = []
            while f: fs.append([f.read(0x78).split(b'\0')[0].decode(),f.readu32(),f.readu32()])
            for fe in fs:
                f.seek(fe[2])
                open(o + '/' + fe[0],'wb').write(f.read(fe[1]))
            if fs: return
        case 'MINICAT':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(8) == b'MINICAT\0'
            f.skip(8)

            cnt = 0
            def xfile():
                nonlocal cnt
                so = f.readu32()
                eo = f.readu32()
                pos = f.pos
                if so <= 0x70 or so > eo or eo > f.size or so > f.size: return

                f.seek(so)
                s = eo-so

                fn = str(cnt) + '.'
                hd = f.read(2)
                if hd == b'BM':
                    bs = f.readu32()
                    if bs != s:
                        if (so+bs) <= f.size: s = bs
                    if bs == s: fn += 'bmp'
                    else: fn += 'bin'
                elif (hd+f.read(2)) == b'PSCT': fn += 'psct'
                else: fn += 'bin'

                f.seek(so)
                d = f.read(s)
                if s < 0x500 and not sum(d): return
                open(o + '/' + fn,'wb').write(d)
                cnt += 1
                f.seek(pos)
            def pfile():
                of = f.readu32()
                pos = f.pos
                if (of+8) > f.size or of <= 0x70: return

                f.seek(of)
                xfile()
                f.seek(pos)

            pfile()
            f.skip(4)
            for _ in range(4): pfile()
            xfile()
            if cnt: return
        case 'NeoBook Cartoon':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'SN\x0C\x00'
            f.skip(2)
            s = f.readu32()
            f.skip(2)
            open(o + '/' + tbasename(i) + '.png','wb').write(f.read(s))
            if s: return
        case '1nsane Game Archive':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'FFFL'
            f.skip(8)
            f.seek(f.readu32())
            fc = f.readu32()
            fs = []
            for _ in range(fc): fs.append((f.read(0x38).split(b'\0')[0].decode(),f.readu32(),f.readu32()))
            for fe in fs:
                f.seek(fe[2])
                xopen(o + '/' + fe[0],'wb').write(f.read(fe[1]))
            if fs: return
        case 'Afterlife Game Data':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.seek(0x10)
            fc = f.readu32()
            f.skip(8)
            bof = 8 + 12 + 8 + 4*fc + 8 + 4*fc
            offs = [bof + f.readu32() for _ in range(fc)]
            for ix,of in enumerate(offs):
                f.seek(of)
                ext = f.read(4)[::-1].decode().lower()
                open(o + f'/{ix}.{ext}','wb').write(f.read(f.readu32()-8))
            if offs: return
        case 'Zyclunt Game Archive':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(9) == b'JAM2File\0'
            fc = f.readu16()
            fs = []
            for _ in range(fc):
                fn = f.read(12)
                assert f.read(1) == b'\0'
                fs.append((fn.strip(b'\0').decode(),f.readu32()))

            for ix,fe in enumerate(fs):
                f.seek(fe[1])
                if len(fs) == ix+1: ln = None
                else: ln = fs[ix+1][1]-fe[1]
                xopen(o + '/' + fe[0],'wb',ln).write(f.read(ln))
            if fs: return
        case 'ZDA Game Archive':
            if db.print_try: print('Trying with custom extractor')
            import zlib
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'ZDA\0'
            fc = f.readu32()
            bo = f.readu32()
            fs = []
            for _ in range(fc): fs.append((f.read(40).strip(b'\0').decode(),f.readu32(),f.readu32(),bo + f.readu32()))
            for fe in fs:
                f.seek(fe[3])
                d = f.read(fe[2])
                if fe[1] != fe[2]: d = zlib.decompress(d)
                of = xopen(o + '/' + fe[0],'wb')

                lb = 0xBB
                for b in d:
                    b ^= lb
                    of.write(bytes([b]))
                    lb = b
                of.close()
            if fs: return
        case 'Disney Games Archive':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(8) == b'Pod File'
            f.skip(4)
            fc = f.readu32()
            fs = [(f.read(12).strip(b'\0').decode(),f.readu32()) for _ in range(fc)]
            for fe in fs: xopen(o + '/' + fe[0],'wb').write(f.read(fe[1]))
            if fs: return
        case 'Dragon UnPACKer 5 Plugin':
            if db.print_try: print('Trying with custom extractor')
            import zlib,lzma

            def delzma(i): return lzma.decompress(i[:9] + b'\0'*4 + i[9:],format=lzma.FORMAT_ALONE)

            from lib.file import File
            f = File(i,endian='<')

            assert f.read(5) == b'DUPP\x1A'
            v = f.readu8()
            f.skip(2)

            inf = open(o + '/' + tbasename(i) + '.ini','w',encoding='utf-8')
            inf.write(f'[{tbasename(i)}]\nenabled=1\n')
            infsp = inf.tell()

            if v < 4:
                f.skip(12)
                ps = f.reads32()
                fc = f.reads32()

                for vn in ('name','url','author','comment'): inf.write(f'{vn}={f.read(f.readu8()).decode()}\n')
                if ps > 0: open(o + '/picture.bmp').write(f.read(ps))

                for _ in range(fc):
                    s = f.reads32()
                    f.skip(0x10)
                    c = f.reads32()
                    f.skip(8)
                    fn = f.read(f.readu8()).decode()
                    fn = o + '/' + os.path.join(f.read(f.readu8()).decode(),fn)
                    d = f.read(s)
                    if c == 1: d = zlib.decompress(d)
                    xopen(fn,'wb').write(d)
            elif v == 4:
                offc = f.reads32()
                offs = []
                for _ in range(offc):
                    oe = [f.readu8()]
                    fls = f.readu8()
                    if fls & 1: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x20: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x40: oe.append(f.reads32())
                    else:
                        f.skip(4)
                        oe.append(0)
                    oe += [f.reads64(),f.reads64()]
                    f.skip(0x28)
                    offs.append(oe)

                fs = []
                fnd = {}
                df = None
                for oe in offs:
                    f.seek(oe[4])
                    d = f.read(oe[5])
                    if oe[1] == 1: d = zlib.decompress(d)
                    elif oe[1] == 2: d = delzma(d)

                    b = File(d,endian='<')
                    if oe[0] == 1:
                        b.skip(12)
                        for vn in ('name','url','author'): inf.write(f'{vn}={b.read(b.readu8()).decode()}\n')
                        inf.write(f'comment={b.read(b.readu32()).decode()}\n')
                    elif oe[0] == 2:
                        for _ in range(oe[3]):
                            fe = [b.reads64(),b.reads64()]
                            b.skip(12)
                            fls = b.readu8()
                            if fls & 0x10: fe.append(b.readu8())
                            else:
                                b.skip(1)
                                fe.append(0)
                            b.skip(1)
                            fe.append(b.reads32())
                            b.skip(0x45)
                            if not fls & 0x40: fs.append(fe)
                    elif oe[0] == 10: open(o + '/' + tbasename(i) + '_banner.bmp','wb').write(d)
                    elif oe[0] == 20:
                        for ix in range(oe[3]): fnd[ix] = b.read(b.readu8()).decode()
                    elif oe[0] == 21: df = b
                    else: open(o + '/$' + str(oe[0]) + '.unkheader','wb').write(d)

                if fs and not df: return 1

                for fe in fs:
                    df.seek(fe[0])
                    d = df.read(fe[1])
                    if fe[2] == 1: d = zlib.decompress(d)
                    elif fe[2] == 2: d = delzma(d)
                    open(o + '/' + fnd.get(fe[3],str(fe[3])),'wb').write(d)
            elif v == 5:
                f.skip(2)
                offc = f.readu32()
                offs = []
                for _ in range(offc):
                    oe = [f.readu8()]
                    fls = f.readu8()
                    if fls & 1: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x20: oe.append(f.readu8())
                    else:
                        f.skip(1)
                        oe.append(0)
                    if fls & 0x40: oe.append(f.readu32())
                    else:
                        f.skip(4)
                        oe.append(0)
                    oe += [f.reads64(),f.reads64()]
                    f.skip(0x48)
                    offs.append(oe)

                fs = []
                fnd = {}
                fld = {}
                df = None
                for oe in offs:
                    f.seek(oe[4])
                    d = f.read(oe[5])
                    if oe[1] == 1: d = zlib.decompress(d)
                    #elif oe[1] == 2: d = lzma.decompress(d)

                    b = File(d,endian='<')
                    if oe[0] == 1:
                        b.skip(12)
                        for vn in ('name','url','author'): inf.write(f'{vn}={b.read(b.readu8()).decode()}\n')
                        inf.write(f'comment={b.read(b.readu32()).decode()}\n')
                    elif oe[0] == 2:
                        for _ in range(oe[3]):
                            fe = [b.reads64(),b.reads64()]
                            b.skip(12)
                            fls = b.readu32()
                            if fls & 0x10: fe.append(b.readu8())
                            else:
                                b.skip(1)
                                fe.append(0)
                            b.skip(5)
                            fe += [b.readu32(),b.readu32()]
                            b.skip(0x44)
                            if not fls & 0x40: fs.append(fe)
                    elif oe[0] == 10: open(o + '/' + tbasename(i) + '_banner.bmp','wb').write(d)
                    elif oe[0] == 20:
                        for ix in range(oe[3]): fnd[ix] = b.read(b.readu8()).decode()
                    elif oe[0] == 23:
                        for ix in range(oe[3]): fld[ix] = b.read(b.readu8()).decode()
                    elif oe[0] == 21: df = b
                    else: open(o + '/$' + str(oe[0]) + '.unkheader','wb').write(d)

            infp = inf.tell()
            inf.close()
            if len(os.listdir(o)) > 1 or infp != infsp: return
        case 'Yay0':
            db.get('n64decompress')
            if db.print_try: print('Trying with n64decompress')
            from bin.n64decompress import decompress_yay0 # type: ignore

            of = o + '/' + tbasename(i)
            open(of,'wb').write(decompress_yay0(open(i,'rb').read()))
            return
        case 'WarioWare Mega Party Game PAC':
            db.get('n64decompress')
            if db.print_try: print('Trying with n64decompress')
            from bin.n64decompress import decompress_yay0 # type: ignore

            of = o + '/' + tbasename(i)
            open(of,'wb').write(decompress_yay0(open(i,'rb').read()[0x20:]))
            return
        case 'Package Resource Index':
            of = o + '\\' + tbasename(i) + '.xml'
            run(['makepri','dump','/if',i,'/of',of,'/o','/dt','Detailed'])
            if exists(of) and os.path.getsize(of): return
        case 'DJarc':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(8) == b'DJarc \0\0'
            fc = f.readu16()
            fs = [(f.readu32(),f.readu32(),f.read(13).split(b'\0')[0].decode()) for _ in range(fc)]
            for fe in fs:
                f.seek(fe[0])
                d = f.read(fe[1])
                open(o + '/' + fe[2] + ('.djc' if d.startswith(b'DJcomp\0\0') else ''),'wb').write(d)
            if fs: return
        case 'Borland Form':
            of = o + '\\' + tbasename(i) + '.txt'
            run(['dfm2txt','bin',i,of])
            if not (exists(of) and os.path.getsize(of)): return 1

            if db.print_try: print('Trying with custom extractor')
            d = open(of,encoding='ansi').read()

            for ix,fd in enumerate(re.findall(r'(Picture|Icon)\.Data = \{([^\}]+)\}',d)):
                ft,fd = fd
                fd = bytes.fromhex(fd)
                if ft == 'Icon': ext = 'ico'
                else:
                    st = fd[1:fd[0]+1].decode()
                    fd = fd[fd[0]+1:]
                    if st == 'TBitmap':
                        ext = 'bmp'
                        fd = fd[4:]
                    elif st == 'TJPEGImage':
                        ext = 'jpg'
                        fd = fd[4:]
                    elif st == 'TGIFImage':
                        ext = 'gif'
                        fd = fd[4:]
                    elif st == 'TIcon':
                        ext = 'ico'
                    else: ext = 'unk'

                open(o + f'/{ix}.{ext}','wb').write(fd)
            return
        case 'Dragon VDK IMG':
            run(['dcopy',i,'*',o + '\\'])
            if os.listdir(o): return
        case 'FrontPage Theme':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            f.readline()
            n = int(f.readline().strip())
            fs = []
            for _ in range(n):
                fe = f.readline().strip().decode().rsplit(',',1)
                fs.append((fe[0],int(fe[1])))
            for fe in fs:
                f.seek(14,1)
                open(o + '/' + fe[0],'wb').write(f.read(fe[1]))
            if fs: return
        case 'Impact Screensaver ILB':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.skip(f.readu32())
            f.skip(f.readu32())

            while f:
                nl,fl = f.readu32(),f.readu32()
                n = f.read(nl).decode().replace('/','-')
                if n == '..': n = '__'
                open(o + '/' + n,'wb').write(f.read(fl))
                f.skip(1)
            if os.listdir(o): return
        case 'Across Crossword Puzzle':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.skip(0x2C)
            w,h = f.readu8(),f.readu8()
            clus = f.readu16()
            f.skip(4)

            solv = b'\r\n'.join(f.read(w) for _ in range(h))
            grid = b'\r\n'.join(f.read(w) for _ in range(h))

            of = open(o + '/' + tbasename(i) + '.txt','wb')
            of.write(f.read0s() + b'\r\n')
            at = f.read0s()
            of.write(at + (b' ' if at and at[-1] != 0x20 else b'') + f.read0s() + b'\r\n\r\n' + grid + b'\r\n\r\n' + solv + b'\r\n\r\n' + b'\r\n'.join(f.read0s() for _ in range(clus)) + b'\r\n\r\n')
            while f:
                n = f.read0s()
                if n: of.write(n + b'\r\n')
            of.close()
            f.close()
            return
        case 'HAL XBIN':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i)

            assert f.read(4) == b'XBIN'
            f._end = {b'\x34\x12':'<',b'\x12\x34':'>'}[f.read(2)]
            v = f.readu8()
            f.skip(1)
            s = f.readu32() - 0x10
            f.skip(4)
            if v in (4,5):
                f.skip(4)
                s -= 4

            tst = f.read(4)
            f.skip(-4)
            try:tst = tst.decode('ascii').lower()
            except:tst = 'bin'
            open(o + '/' + tbasename(i) + '.' + tst,'wb').write(f.read(s))
            f.close()
            if s: return
        case 'HAL Switch CMP': return quickbms('kirbyswitch-decompress')
        case 'HAL YAML': raise NotImplementedError # https://github.com/firubii/KirbyLib/blob/main/KirbyLib/Yaml.cs
        case 'Dr. Luigi ZALZ':
            from multiprocessing.pool import ThreadPool
            f = open(i,'rb')
            s = f.seek(0,2)

            fs = []
            lof = 0
            for ix in range(s//0x80):
                f.seek(ix*0x80)
                if f.read(4) == b'ZALZ':
                    fs.append((lof,(ix*0x80)-lof))
                    lof = ix*0x80
            fs.append((lof,s-lof))

            p = ThreadPool()
            fsl = len(fs)-1
            for ix,fe in enumerate(fs[1:]):
                f.seek(fe[0])
                tf = TmpFile()
                open(tf.p,'wb').write(f.read(fe[1]))

                def extr(tf,ix):
                    td = TmpDir()
                    quickbms('dr_luigi_wiiu',tf.p,td.p,print_try=not ix)
                    tf.destroy()

                    tfo = td.p + '/' + os.listdir(td.p)[0]
                    try:
                        tg = open(tfo,'rb').read(8)
                        tgf = tg[:4].decode('ascii')
                        if not tgf.isupper():
                            if tg == b'@echo of': tg = 'bat'
                            else: raise
                        else: tg = tgf.lower()
                    except: tg = 'bin'
                    mv(tfo,o + '/' + str(ix) + '.' + tg)
                    td.destroy()
                p.apply_async(extr,(tf,ix))

            while len(os.listdir(o)) < fsl: sleep(0.1)
            for _ in range(50):
                try: p.join()
                except ValueError:sleep(0.1)
                else:break
            else:p.terminate();p.join()
            p.close()

            if fs: return
        case 'Bezel Shader Pack':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i)
            assert f.read(12) == b'BEZSHAPK\0\0\1\0'
            f._end = {b'\xFF\xFE':'<',b'\xFE\xFF':'>'}[f.read(2)]
            f.skip(0x12)

            boff = f.readu64()
            fc = f.readu64()
            f.seek(boff)
            fs = [f.readu64() for _ in range(fc)]

            for ix,fe in enumerate(fs):
                f.seek(fe + 0x1C)
                s = f.readu32()
                f.seek(fe)
                open(o + '/' + str(ix) + '.bfsha','wb').write(f.read(s))

            f.close()
            if fs: return
        case 'Nintendo MSBT':
            db.get('ce_msbt')
            if db.print_try: print('Trying with ce_msbt')
            import bin.ce_msbt as msbt # type: ignore

            d = open(i,'rb').read()
            end = {b'\xFF\xFE':'<',b'\xFE\xFF':'>'}[d[8:10]]

            msbt._unpfr = msbt.struct.unpack_from
            def punpfr(f,d,o=0):
                f = f.strip('<>')
                if f == 'HxxHII': f = 'HxxHHxxI'
                r = msbt._unpfr(end + f,d,o)
                if f == 'HxxHHxxI':
                    r = list(r)
                    return r[:1] + [0x301] + r[2:]
                return r
            msbt.struct.unpack_from = punpfr

            mso = msbt.MSBT()
            mso.load(d)
            open(o + '/' + tbasename(i) + '.xml','wb').write(msbt.ET.tostring(mso.generate_xml(),'utf-8'))
            return

        case 'Ridge Racer V A':
            tf = dirname(i) + '\\rrv3vera.ic002'
            if os.path.exists(tf): remove(tf)
            symlink(db.get('rrv3va'),tf)

            cfp = dirname(db.get('rrvatool')) + '/RidgeRacerVArchiveTool.exe.config'
            d = open(cfp).read().replace('<value>True</value>','<value>False</value>')
            open(cfp,'w').write(d.replace('<setting name="ACV3Achecked" serializeAs="String">\n                <value>False</value>','<setting name="ACV3Achecked" serializeAs="String">\n                <value>True</value>'))
            if db.print_try: print('Trying with rrvatool')
            p = subprocess.Popen([db.get('rrvatool'),i],stdout=-1,stderr=-1)
            sleep(1)
            
            while not os.listdir(i + '_extract'): sleep(0.1)
            while True:
                try:copydir(i + '_extract',o,True)
                except:sleep(0.1)
                else:break
            p.kill()
            remove(tf)

            for x in os.listdir(o):
                if not os.path.getsize(o + '/' + x): remove(o + '/' + x)

            if os.listdir(o): return
        case 'Donkey Kong Banana Kingdom':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

            f = File(i,endian='<')
            f.seek(0x14)
            c = f.readu32()
            f.seek(0x20)
            fs = []
            for _ in range(c):
                fs.append((f.read(0x10).rstrip(b'\0').decode(),f.readu32(),f.readu32() * 0x200))
                f.skip(8)
            for fe in fs:
                f.seek(fe[2])
                open(o + '/' + fe[0],'wb').write(f.read(fe[1]))

            lo = max(fe[2] + fe[1] for fe in fs)
            xo = lo + (-lo % 0x200)
            if not xo >= f._size:
                f.seek(xo)
                open(o + '/_extra.bin','wb').write(f.read(f._size - xo - 0x200 - 0xB8B200 - 0x14C))

            f.close()
            if fs: return
        case 'Monkey Ball A':
            for d in ('CHUNK','DTPK','SPSD'):
                scn = f'monkey ball {d} extract'
                if d == 'CHUNK':
                    scp = db.get(scn)
                    scc = open(scp,encoding='utf-8').read()
                    if '\nnext A\n' in scc: open(scp,'w',encoding='utf-8').write(scc.replace('\nnext A\n','\nmath A + 1\n'))

                mkdir(o + '\\' + d)
                if quickbms(scn,ouf=o + '\\' + d): break
            else: return
        case 'Initial D 3 Export A':
            for d in ('NMZIP','TEX','SPSD'):
                mkdir(o + '\\' + d)
                if quickbms(f'initd3e {d} extract',ouf=o + '\\' + d): break
            else: return

    return 1
