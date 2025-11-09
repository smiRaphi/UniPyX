from .main import *

def extract4(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def quickbms(scr,inf=i,ouf=o):
        if db.print_try: print('Trying with',scr)
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
            from bin.tmd import File
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
            from bin.tmd import File

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
            from bin.tmd import File

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
            from bin.tmd import File

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
            from bin.tmd import File

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
            from bin.tmd import File

            f = File(i,endian='<')
            assert f.read(2) == b'PA'
            fc = f.readu16()
            assert fc > 0 and f.readu32() > 0
            fs = [(f.read(0x10).rstrip(b'\0').decode('ascii'),f.readu32()) for _ in range(fc)]

            for n,s in fs: open(o + '/' + n,'wb').write(f.read(s))
            f.close()

            if fs: return
        case 'The Sims FAR'|'Quake PAK'|'WAD':
            if db.print_try: print('Trying with gameextractor')
            run(['java','-jar',db.get('gameextractor'),'-extract','-input',i,'-output',o],print_try=False,cwd=dirname(db.get('gameextractor')))
            remove(dirname(db.get('gameextractor')) + '/logs')
            if os.listdir(o): return
        case 'Build Engine Group':
            run(['gamearch',i,'-X'],cwd=o)
            if os.listdir(o): return
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
            from bin.tmd import File
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
            from bin.tmd import File

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
            from bin.tmd import File
            f = File(i,endian='>')

            assert f.read(4) == b'FORM'
            f.skip(4)
            BTYPE = f.read(4)

            cnt = [0]
            FNAMES = []
            def read_block(fpath:str,fname:str=None,addext=True):
                name = f.read(4)
                size = f.readu32()
                pos = f.pos
                epos = pos + size

                if name == b'FORM':
                    typ = f.read(4).strip(b'\0 \t\r\n')

                    if BTYPE in (b'NSF1',b'NMF1') and typ[3:].isdigit(): typ = typ[:3]

                    try: typ = '.' + typ.decode().lower()
                    except: typ = '.iff'
                    f.skip(-12)

                    if not fname and FNAMES: fname = FNAMES.pop(0)
                    fname = fpath + '/' + (fname or f'{cnt[0]}')
                    fcnt = 1
                    while exists(fname + (typ if addext else '')):
                        if fcnt > 1: fname = fname.rsplit('_',1)[0]
                        fname += f'_{fcnt}'
                        fcnt += 1

                    xopen(fname + (typ if addext else ''),'wb').write(f.read(8 + size))
                    cnt[0] += 1

                    f.seek(pos + 4)
                    while f.pos < epos: read_block(fname + '_EXT')
                elif name == b'WRCH' and BTYPE == b'NSF1':
                    f.skip(4)
                    while f.pos < epos: read_block(fpath,f.read(f.readu32()).rstrip(b'\0').replace(b'\0',b' ').decode())
                elif name == b'NETN' and BTYPE in (b'NSF1',b'NMF1'):
                    FNAMES.append(f.read(f.readu32()).rstrip(b'\0').replace(b'\0',b' ').decode())

                f.seek(epos)

            while f: read_block(o)
            if cnt[0]: return

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
            from bin.tmd import File

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
