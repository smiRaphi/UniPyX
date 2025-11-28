from .main import *

def extract2(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    match t:
        case 'RVZ':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if os.listdir(o):
                if exists(o + '/DATA'):
                    for sd in os.listdir(o):
                        rename(o + '/' + sd + '/sys',o + '/' + sd + '/$SYS')
                        for sf in os.listdir(o + '/' + sd):
                            if sf in ['$SYS','files']: continue
                            remove(o + '/' + sd + '/' + sf)
                        copydir(o + '/' + sd + '/files',o + '/' + sd,True)
                        if sd == 'DATA': copydir(o + '/DATA',o,True)
                        else: rename(o + '/' + sd,o + '/$' + sd)
                else:
                    rename(o + '/sys',o + '/$SYS')
                    copydir(o + '/files',o,True)
                return
            tf = TmpFile('.iso')
            run(['dolphintool','convert','-u',gtmp('user'),'-i',i,'-o',tf,'-f','iso'])
            if exists(tf.p):
                run(['wit','-q','X',tf,'-p','-o','-E$','-d',o])
                tf.destroy()
                fs = os.listdir(o)
                if len(fs) == 1:
                    try:
                        mv(o + '/' + fs[0] + '/sys',o + '/$SYS')
                        copydir(o + '/' + fs[0] + '/files',o,True)
                        remove(o + '/' + fs[0])
                    except:pass
                    else:return
            tf.destroy()
        case 'Wii ISO'|'GameCube ISO':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if os.listdir(o):
                rename(o + '/sys',o + '/$SYS')
                copydir(o + '/files',o,True)
                return
            run(['wit','-q','X',i,'-p','-o','-E$','-d',o])
            fs = os.listdir(o)
            if len(fs) == 1:
                try:
                    mv(o + '/' + fs[0] + '/sys',o + '/$SYS')
                    copydir(o + '/' + fs[0] + '/files',o,True)
                    remove(o + '/' + fs[0])
                except:pass
                else:return
        case 'GameCube GCAM ISO':
            if db.print_try: print('Trying with custom extractor')
            tf = TmpFile('.iso')
            with open(i,'rb') as fi:
                fi.seek(0x20)
                with open(tf.p,'wb') as f:
                    d = b''
                    while True:
                        d = fi.read(0x4000)
                        if not d: break
                        f.write(d)
            if extract(tf.p,o,'GameCube ISO'): mv(tf.p,o + '/' + tbasename(i) + '.iso')
            tf.destroy()
            return
        case 'GameCube TGC ISO':
            if db.print_try: print('Trying with custom extractor')
            tf = TmpFile('.iso')
            with open(i,'rb') as fi:
                fi.seek(8)
                off = int.from_bytes(fi.read(4),'big')
                fi.seek(0x10)
                fst = int.from_bytes(fi.read(4),'big') - off
                fi.seek(0x1C)
                dol = int.from_bytes(fi.read(4),'big') - off
                fi.seek(off)
                with open(tf.p,'wb') as f:
                    d = b''
                    while True:
                        d = fi.read(0x4000)
                        if not d: break
                        f.write(d)
                    f.seek(0x420)
                    f.write(int.to_bytes(dol,4,'big'))
                    f.write(int.to_bytes(fst,4,'big'))
            if extract(tf.p,o,'GameCube ISO'): mv(tf.p,o + '/' + tbasename(i) + '.iso')
            tf.destroy()
            return
        case 'NCSD':
            e,_,_ = run(['3dstool','-xt01267f','cci',o + '\\DP0.bin',o + '\\DP1.bin',o + '\\DP2.bin',o + '\\DP6.bin',o + '\\DP7.bin',i,'--header',o + '\\HNCSD.bin'])
            if e: return 1

            e,_,_ = run(['3dstool','-xtf','cxi',o + '\\DP0.bin','--header',o + '\\HNCCH0.bin','--exh',o + '\\DecExH.bin','--exh-auto-key','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key','--logo',o + '\\LogoLZ.bin','--plain',o + '\\PlainRGN.bin'])
            if e: return 1
            run(['3dstool','-xtf','cfa',o + '\\DP1.bin','--header',o + '\\HNCCH1.bin','--romfs',o + '\\DecManual.bin','--romfs-auto-key'])
            run(['3dstool','-xtf','cfa',o + '\\DP2.bin','--header',o + '\\HNCCH2.bin','--romfs',o + '\\DecDLPlay.bin','--romfs-auto-key'])
            run(['3dstool','-xtf','cfa',o + '\\DP6.bin','--header',o + '\\HNCCH6.bin','--romfs',o + '\\DecN3DSU.bin','--romfs-auto-key'])
            run(['3dstool','-xtf','cfa',o + '\\DP7.bin','--header',o + '\\HNCCH7.bin','--romfs',o + '\\DecO3DSU.bin','--romfs-auto-key'])

            remove(o + '\\DP0.bin',o + '\\DP1.bin',o + '\\DP2.bin',o + '\\DP6.bin',o + '\\DP7.bin')
            e,_,_ = run(['3dstool','-xtfu','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            run(['3dstool','-xtf','romfs',o + '\\DecManual.bin','--romfs-dir',o + '\\Manual'])
            run(['3dstool','-xtf','romfs',o + '\\DecDLPlay.bin','--romfs-dir',o + '\\DownloadPlay'])
            run(['3dstool','-xtf','romfs',o + '\\DecN3DSU.bin','--romfs-dir',o + '\\N3DSUpdate'])
            run(['3dstool','-xtf','romfs',o + '\\DecO3DSU.bin','--romfs-dir',o + '\\O3DSUpdate'])

            for x in os.listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            if os.listdir(o): return
        case 'NCCH CXI':
            e,_,_ = run(['3dstool','-xtf','cxi',i,'--header',o + '\\HNCCH.bin','--exh',o + '\\DecExH.bin','--exh-auto-key','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key','--logo',o + '\\LogoLZ.bin','--plain',o + '\\PlainRGN.bin'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            if e: return 1

            for x in os.listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            return
        case 'NCCH CFA':
            e,_,_ = run(['3dstool','-xtf','cfa',i,'--header',o + '\\HNCCH.bin','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            if e: return 1

            for x in os.listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            return
        case 'Switch NSP'|'Switch NCA'|'Switch XCI':
            for k in ('prod','dev'):
                bcd = ['hac2l','-t',{'Switch NSP':'pfs','Switch NCA':'nca','Switch XCI':'xci'}[t],'--disablekeywarns','-k',db.get(k+'keys'),'--titlekeys=' + db.get('titlekeys')]
                _,e,_ = run(bcd + [i],print_try=False)
                bcd += ['--exefsdir=' + o + '\\ExeFS','--romfsdir=' + o + '\\RomFS']
                if ' MetaType=Patch ' in e:
                    pinf = re.search(r'ProgramId=([\dA-F]+), Version=0x([\dA-F]+),',e)
                    pid,pv = pinf[1],int(pinf[2],16)
                    for x in os.listdir(dirname(i)):
                        if pid in x and x.endswith('.nsp'):
                            try: v = int(re.search(r'v(\d+)(?:\b|_)(?!\.)',x)[1])
                            except: v = 0
                            if v < pv: bf = dirname(i) + '\\' + x;break
                    else: return 1
                    bcd += ['--basepfs',bf]
                run(bcd + [i])
                if os.listdir(o) and os.listdir(o + '/ExeFS') and os.listdir(o + '/RomFS'): return
                rmdir(o)
                mkdir(o)
        case 'NDS':
            run(['mdnds','e',i,o])
            if os.listdir(o): return
        case 'PS4 PKG':
            rtd = TmpDir()
            run(['ps4pkg','img_extract','--passcode','00000000000000000000000000000000','--tmp_path',rtd,i,o])
            rtd.destroy()
            if os.path.exists(o + '/Image0') and os.listdir(o + '/Image0'):
                fs = os.listdir(o)
                copydir(o + '/Image0',o)
                mv(o + '/Sc0',o + '/sce_sys')
                for x in fs: remove(o + '/' + x)
                return
        case 'PS5 PKG':
            rtd = TmpDir()
            run(['ps5pkg','img_extract','--passcode','00000000000000000000000000000000','--tmp_path',rtd,i,o])
            rtd.destroy()
            if os.listdir(o): raise NotImplementedError()
            if os.path.exists(o + '/Image0') and os.listdir(o + '/Image0'):
                fs = os.listdir(o)
                copydir(o + '/Image0',o)
                mv(o + '/Sc0',o + '/sce_sys')
                for x in fs: remove(o + '/' + x)
                return
        case 'PS3 ISO':
            from bin.ps3key import PS3Keys
            k = PS3Keys().get(i)
            tf = TmpFile('.iso')
            tf.link(i)
            run(['ps3dec','--iso',tf,'--dk',k,'--tc','16','--skip'])
            rmdir('log')
            tf.destroy()
            if os.path.exists(tf.p + '_decrypted.iso'):
                if not extract(tf.p + '_decrypted.iso',o,'ISO'):
                    remove(tf.p + '_decrypted.iso')
                    return
                remove(tf.p + '_decrypted.iso')
            if not extract(i,o,'ISO'): return
        case 'PSVita PKG':
            import zlib,base64
            if exists(dirname(i) + '/work.bin'): work = dirname(i) + '/work.bin'
            elif exists(noext(i) + '.work.bin'): work = noext(i) + '.work.bin'
            else: return 1

            ZRIF_DICT = zlib.decompress(base64.b64decode(b"eNpjYBgFo2AU0AsYAIElGt8MRJiDCAsw3xhEmIAIU4N4AwNdRxcXZ3+/EJCAkW6Ac7C7ARwYgviuQAaIdoPSzlDaBUo7QmknIM3ACIZM78+u7kx3VWYEAGJ9HV0="))
            rif = open(work,'rb').read()
            c = zlib.compressobj(level=9,wbits=10,memLevel=8,zdict=ZRIF_DICT)
            bn = c.compress(rif)
            bn += c.flush()
            if len(bn) % 3: bn += bytes(3 - len(bn) % 3)
            zrif = base64.b64encode(bn).decode()

            osj = OSJump()
            osj.jump(o)
            run(['pkg2zip','-x',i,zrif])
            if exists('app') and os.listdir('app') and os.listdir('app/' + os.listdir('app')[0]):
                td = o + '/app/' + os.listdir('app')[0]
                osj.back()

                run(['psvpfsparser','-i',td,'-o',o,'-z',zrif])
                rmtree(o + '/app')

                if os.listdir(o): return
        case 'WUX':
            from bin.wiiudk import DKeys
            kys = DKeys()
            cmd = ['java','-jar',db.get('jwudtool'),'-commonkey',kys.get('common'),'-decrypt','-in',i,'-out',o]
            k = kys.get(i)
            if not k: cmd.append('-dev')
            else: cmd += ['-titleKey',k]
            if db.print_try: print('Trying with jwudtool')
            run(cmd,print_try=False)
            if os.listdir(o):
                for x in os.listdir(o):
                    try:
                        if not x.startswith('GM'): remove(o + '/' + x);continue
                        if not exists(o + '/' + x + '/content'): remove(o + '/' + x);continue
                        copydir(o + '/' + x,o,True)
                    except PermissionError: pass
                return
        case 'XISO':
            run(['xdvdfs','unpack',i,o])
            if os.listdir(o): return
        case 'Xbox LIVE ROM'|'Xbox PIRS':
            xpt = db.get('py360_stfs')
            xpd = open(xpt,encoding='utf-8').read()
            if 'from cStringIO import StringIO' in xpd:
                open(xpt,'w',encoding='utf-8').write(xpd.replace(
                    'from cStringIO import StringIO','from io import BytesIO as StringIO').replace(
                    'from constants import','from .constants import').replace(
                    ' print ',' pass#').replace(
                    'assert data in ("CON ",','assert data.decode() in ("CON ",').replace(
                    "'\\x00'","b'\\0'").replace(
                    '"%s\\x00"',"b'%s\\0'").replace(
                    "data[:0x28].strip(b'\\0')","data[:0x28].strip(b'\\0').decode()").replace(
                    "self.filename != ''","self.filename"))

            if db.print_try: print('Trying with py360_stfs')
            import bin.py360.stfs as stfs # type: ignore
            stfs.xrange = range
            stfs.ord = lambda x: x[0] if isinstance(x,bytes) else (x if isinstance(x,int) else ord(x))
            stfs.os = os

            stfs.extract_all(['',i,o])
            if os.listdir(o): return
        case 'GD-ROM CUE+BIN':
            run(['buildgdi','-extract','-cue',i,'-output',o + '\\','-ip',o + '\\IP.BIN'])
            if os.listdir(o):
                from bin.sgkey import SGKeys
                if exists(o + '/IP.BIN') and SGKeys().get(o): return extract(o + '\\IP.BIN',o,'Encrypted GD-ROM')
                return
        case 'Wii TMD':
            ckey = dirname(db.get('tmd_wii')) + '/'

            if not exists(ckey + 'common.key'):
                s = db.c.get('https://wiki.wiidatabase.de/wiki/Common-Key').text
                for r,k in [('Normal','common'),
                            ('Korea' ,'korea' ),
                            ('Debug' ,'debug' )]:
                    open(ckey + k + '.key','wb').write(bytes.fromhex(re.search(f'<b>{r}:</b> *<code>([^<]+)</code>',s)[1]))

            if db.print_try: print('Trying with tmd_wii')
            from bin.tmd import TMD,derive_key,check_sha1,decrypt_content

            dr = dirname(i)
            dls = [x for x in os.listdir(dr) if os.path.isfile(dr + '/' + x)]
            if 'tmd' in dls: tmd = 'tmd'
            else: tmd = max([x for x in dls if x.startswith('tmd.')],key=lambda x:int(x.split('.')[-1]))
            tmd = TMD(dr + '/' + tmd)

            for c in tmd.contents:
                fn = hex(c.cid)[2:].zfill(8)
                odr = o + '/' + fn
                ifl = dr + '/' + fn

                if not check_sha1(ifl,c.sha1):
                    tf = TmpFile()
                    decrypt_content(ifl,tf,derive_key(tmd.titleid,1),c)
                    assert check_sha1(tf, c.sha1)
                    ifl = str(tf)

                if c.type == 2: copy(ifl,o + '/CAFEDEAD.bin')
                elif c.type == 0x8001:
                    if extract(ifl,o + '/$SHARED','U8'): copy(ifl,o + '/$SHARED/' + fn + '.bin')
                elif c.index == 0 and tmd.titleid == b'\0\0\0\1\0\0\0\2': copy(ifl,o + '/build_tag.bin')
                elif c.index == 0: copy(ifl,o + '/banner.bnr')
                elif c.index == 1: copy(ifl,o + '/launch.dol')
                elif tmd.bootindex == c.index: copy(ifl,o + '/boot.dol')
                else:
                    if open(ifl,'rb').read(4) == b'U\xAA8\x2D':
                        if extract(ifl,odr,'U8'): copy(ifl,odr + '.bin')
                    else: copy(ifl,odr + '.bin')
            return
        case '3DO IMG':
            run(['3dt','unpack','-o',o,i])
            if os.listdir(o) and os.listdir(o + '/' + basename(i) + '.unpacked'):
                copydir(o + '/' + basename(i) + '.unpacked',o,True)
                return
        case 'Amiga IMG'|'SPS IPF':
            td = TmpDir()
            run(['uaeunp','-x',i,'**'],cwd=td.p)
            for f in os.listdir(td.p):
                if isdir(td.p + '/' + f): copydir(td.p + '/' + f,o)
            td.destroy()
            if os.listdir(o): return

            bcmd = ['hxcfe','-finput:' + i]
            _,op,_ = run(bcmd + ['-list'])

            op = op.replace('\r','')
            if '------- Disk Tree --------' in op:
                op = op.split('------- Disk Tree --------\n')[1].split('--------------------------\n')[0]
                cp = []
                for t in re.findall(r"( *)([> ])([^<\n]+) <\d+>\n",op):
                    while len(cp)*4 > len(t[0]): cp.pop()
                    if t[1] == '>':
                        cp.append(t[2])
                        mkdir(o + '/' + '/'.join(cp))
                    else:
                        f = '/'.join(cp + [t[2]])
                        run(bcmd + ['-getfile:/' + f],cwd=dirname(o + '/' + f).replace('/','\\'),print_try=False)

                if rldir(o): return
        case 'Atari ATR':
            run(['atr',i,'x','-a'],cwd=o)
            if os.listdir(o): return
        case 'ZArchive':
            run(['zarchive',i,o])
            if os.listdir(o): return
        case 'C64 Tape'|'C64 LiBRary':
            run(['dirmaster','/e',i],cwd=o)
            if os.listdir(o): return
        case 'Encrypted GD-ROM':
            from bin.sgkey import SGKeys

            id = dirname(i)
            t,key = SGKeys().get(i)
            if not key: return 1

            drvs = []
            for f in os.listdir(id):
                if len(f) != 7: continue
                ld = id + '\\' + f
                if isdir(ld) or os.path.getsize(ld) != 0x100: continue

                lf = open(ld,'rb')
                if sum(lf.read(8)) == 0 and sum(lf.read(8)) != 0 and sum(lf.read(3)) == 0 and lf.read(1)[0] == 0xFF and sum(lf.read(0x8C)) == 0:
                    lf.seek(0xC0)
                    drv = lf.read(0x20).strip(b'\0')
                    if drv:
                        try:drv = id + '\\' + drv.decode()
                        except:pass
                        else:
                            if exists(drv): drvs.append(drv)
                lf.close()

            if not drvs: return 1

            for f in drvs:
                tf = f + '.dec'
                run(['chdecrypt',f,tf,key.hex().upper()])
                assert exists(tf)
                od = f + '_ext'
                if t == 'C':
                    assert open(tf,'rb').read(4) == b'FATX',basename(tf)
                    mkdir(od)
                    extract(tf,od,'FATX')
                elif t == 'T':
                    tff = open(tf,'rb')
                    tff.seek(28)
                    chk = tff.read(4) == b'\xC2\x33\x9F\x3D'
                    tff.close()
                    assert chk,basename(tf)
                    mkdir(od)
                    extract2(tf,od,'GameCube ISO')
                elif t == 'N':
                    tff = open(tf,'rb')
                    nt = None
                    if tff.read(0x50) == b"NAOMI           SEGA ENTERPRISES,LTD.           MONKEY BALL JAPAN VERSION       ": nt = 'Monkey Ball A'
                    tff.close()
                    if nt:
                        mkdir(od)
                        extract(tf,od,nt)
                elif t == '2':
                    tff = open(tf,'rb')
                    nt = None
                    if tff.read(0x60) == b'Naomi2          SEGA CORPORATION                INITIAL D Ver.3                 INITIAL D Ver.3 IN USA          ': nt = 'Initial D 3 Export A'
                    tff.close()
                    if nt:
                        mkdir(od)
                        extract(tf,od,nt)
                if exists(od) and not os.listdir(od): rmdir(od)
            return
        case 'N64DD':
            run(['mfs_manager',i,'-e'],cwd=o)
            if os.listdir(o): return
        case 'MSX Cassette IMG':
            run(['mcp','-x',i],cwd=o)
            if os.listdir(o): return
        case 'ZX Spectrum Tape IMG':
            run(['tapsplit',i,o])
            if os.listdir(o): return
        case 'CPC Plus IMG':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File

            f = File(i)
            f._end = {b'RIFF':'<',b'FFIR':'>'}[f.read(4)]
            f.skip(4)
            assert f.read(4) == b'AMS!'
            cns = {}
            while True:
                cn = f.read(4)
                if not cn: break
                assert cn[:2] == b'cb' and cn[2:].isdigit()
                cns[int(cn[2:])] = f.read(f.readu32())
            assert (len(cns)-1) == max(list(cns))

            of = open(o + '/' + tbasename(i) + '.bin','wb')
            for ix in range(1,len(cns)): of.write(cns[ix])
            of.close()
            if cns: return
        case 'GBA ADS Video ROM'|'GBA ADS SFCD':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File

            f = File(i,endian='<')
            if t == 'GBA ADS Video ROM': f.seek(0xE38)
            aoff = f.pos
            assert f.read(4) == b'SFCD'

            boff = f.readu16() + 8
            f.skip(2)
            fsc = f.readu32()
            for _ in range(fsc):
                siz = f.readu32()
                off = aoff + boff + f.readu32()
                name = ''
                while True:
                    b = f.read(1)
                    if not b: raise EOFError
                    if b == b'\0': break
                    name += b.decode()
                cp = f.pos + -(f.pos-aoff) % 4
                f.seek(off)
                of = open(o + '/' + name,'wb')
                of.write(f.read(siz))
                of.close()
                f.seek(cp)
            if fsc: return
        case 'NES Remix ROM':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File
            f = File(i,endian='<')

            f.skip(8)
            start = f.readu32()
            size = f.readu32() - start
            f.skip(0x10)
            name = f.read(0x10).strip(b'\0').decode()

            f.seek(start)
            tag = f.read(3)
            if tag in (b'NES',b'UNI'):
                if not name: name = tbasename(i)
                name += '.' + tag.decode().lower()
            elif (tag+f.read(13)) == b'\x01*NINTENDO-HVC*\x01':
                if not name: name = f.read(4).strip(b' \0').decode()
                name += '.qd'
            else:
                if not name: name = tbasename(i)
                name += '.bin'
            f.seek(start)
            open(o + '/' + name,'wb').write(f.read(size))
            return
        case 'Famicom Disk Image':
            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import File
            f = File(i,endian='<')

            fds = f.read(3) == b'FDS'
            if fds: f.skip(13)
            else: f.skip(-3)

            od = o
            FNAMES = []
            FC = 0
            while f:
                blockt = f.readu8()
                if blockt == 1:
                    assert f.read(14) == b'*NINTENDO-HVC*'
                    f.skip(1)
                    disk_pos = f.pos - 0x10

                    name = f.read(4).strip(b' \0').decode()
                    if name: od = o + '/' + name;mkdir(od)
                    f.skip(0x24)

                    if not fds:
                        blockt = f.readu8()
                        f.skip(1)
                        blockt2 = f.readu8()
                        if blockt == 2 and blockt2 == 3: fds = True
                        f.skip(-3)
                elif blockt == 2: FC = f.readu8()
                elif blockt == 3:
                    bname = f'{f.readu8()}_{f.readu8()}'
                    name = f.read(8).strip(b' \0').decode() or bname
                    f.skip(2)
                    size = f.readu16()
                    if not '.' in name: name += '.' + ('prg','chr','nam')[f.readu8()]
                    else: f.skip(1)
                    FNAMES.append((od + '/' + name,size))
                elif blockt == 4:
                    name,size = FNAMES.pop(0)
                    open(name,'wb').write(f.read(size))
                    FC -= 1
                    if not FC: f.seek(disk_pos + 0xFFDC)
                if not fds: f.skip(2)
            if os.listdir(o): return
        case 'XVD':
            from bin.xb1key import XB1Keys

            xb1k = XB1Keys()

            for p in ('../',''):
                p = dirname(i) + '/' + p + 'Licenses'
                if exists(p):
                    for f in os.listdir(p):
                        if f.endswith('.xml') and f.lower().startswith('license'): xb1k.add_license(p + '/' + f)
                    xb1k.save()

            _,inf,_ = run(['xvdtool.streaming','info',i],print_try=False)
            keyid = re.search(r'Encryption Key 0 GUID: ([a-f\d]{8}(?:-[a-f\d]{4}){4}[a-f\d]{8})',inf)
            cmd = ['xvdtool.streaming','extract','-o',o]
            if keyid:
                cik = xb1k.get(keyid[1])
                if not cik: return 1
                tf = TmpFile('.cik')
                open(tf.p,'wb').write(cik)
                cmd += ['-c',tf.p]
            else: tf = None

            run(cmd + [i])
            if tf:
                if not os.listdir(o):
                    copy(i,o + '/' + basename(i) + '.dec.xvd')
                    run(['xvdtool.streaming','decrypt','-c',tf.p,'-n',o + '/' + basename(i) + '.dec.xvd'])
                    remove(tf.p)
                    return
                remove(tf.p)
            if os.listdir(o): return
        case 'Acorn Disc Filing IMG':
            tf = TmpFile('.txt')
            open(tf.p,'w',encoding='utf-8').write(f'insert "{i}"\nextract *\nfree\nexit\n')
            run(['discimagemanager','-c',tf],cwd=o)
            tf.destroy()
            if os.listdir(o):
                from time import strptime,mktime

                for f in rldir(o,False):
                    if not exists(f): continue
                    if exists(f + '.inf'):
                        finf = open(f + '.inf','rb').read()
                        if b'\n' in finf or b'\r' in finf: continue
                        try: finf = finf.decode()
                        except: continue
                        remove(f + '.inf')

                        if isfile(f) and len(f) > 4 and f[-4] == ',':
                            try: int(f[-3:],16)
                            except:pass
                            else:
                                nf = f.rsplit(',',1)[0]
                                if exists(nf):
                                    c = 1
                                    nf += '_0'
                                    while exists(nf): nf = nf.rsplit('_',1)[0] + f'_{c}';c += 1
                                rename(f,nf)
                                f = nf

                        if 'DATETIME=' in finf:
                            ft = mktime(strptime(finf.split('DATETIME=')[1].split()[0],'%Y%m%d%H%M%S'))
                            os.utime(f,(ft,ft))
                return
        case 'C64 IMG':
            run(['c1541'],stdin=f'attach "{i}"\nextract\nquit\n',cwd=o)
            cd = dirname(db.get('c1541'))
            remove(cd + '/stderr.txt',cd + '/stdout.txt')
            if os.listdir(o): return

            if not extract(i,o,'DIET'):return # deark 

            return extract2(i,o,'C64 Tape')
        case 'GPEComp':
            if db.print_try: print('Trying with custom extractor')
            f = open(i,'rb')
            for pos in (0xAA48,0xAA70):
                f.seek(pos)
                if f.read(8) == b"\x00\xE9\x55\x43\x4C\xFF\x01\x1A": break
            else: return 1
            f.seek(-8,1)
            tf = TmpFile('.ucl')
            open(tf.p,'wb').write(f.read())

            of = o + '\\' + basename(i) + '.elf'
            run(['uclpack','-d',tf.p,of])
            tf.destroy()
            if exists(of) and os.path.getsize(of): return
        case 'Playdate Container':
            raise NotImplementedError # https://github.com/rarenight/pdx-decrypt/blob/main/pdx-decrypt.py
        case 'PlayStation APA IMG':
            tf = TmpFile('.tar',path=o)
            run(['pfs2tar','--backup',i,tf])
            if not exists(tf.p): return 1
            r = extract(tf.p,o,'TAR')
            tf.destroy()
            return r

    return 1
