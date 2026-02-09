from .main import *

def extract2(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def quickbms(scr,inf=i,ouf=o,print_try=True):
        if db.print_try and print_try: print('Trying with',scr)
        run(['quickbms','-Y',db.get(scr),inf,ouf],print_try=False)
        if listdir(ouf): return
        return 1

    match t:
        case 'RVZ':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if listdir(o):
                if exists(o + '/DATA'):
                    for sd in listdir(o):
                        rename(o + '/' + sd + '/sys',o + '/' + sd + '/$SYS')
                        for sf in listdir(o + '/' + sd):
                            if sf in ['$SYS','files']: continue
                            remove(o + '/' + sd + '/' + sf)
                        copydir(o + '/' + sd + '/files',o + '/' + sd,True,reni=True)
                        if sd == 'DATA': copydir(o + '/DATA',o,True,reni=True)
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
                fs = listdir(o)
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
            if listdir(o):
                rename(o + '/sys',o + '/$SYS')
                copydir(o + '/files',o,True)
                return
            run(['wit','-q','X',i,'-p','-o','-E$','-d',o])
            fs = listdir(o)
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

            for x in listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            if listdir(o): return
        case 'NCCH CXI':
            e,_,_ = run(['3dstool','-xtf','cxi',i,'--header',o + '\\HNCCH.bin','--exh',o + '\\DecExH.bin','--exh-auto-key','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key','--logo',o + '\\LogoLZ.bin','--plain',o + '\\PlainRGN.bin'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            if e: return 1

            for x in listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            return
        case 'NCCH CFA':
            e,_,_ = run(['3dstool','-xtf','cfa',i,'--header',o + '\\HNCCH.bin','--exefs',o + '\\DExeFS.bin','--exefs-auto-key','--exefs-top-auto-key','--romfs',o + '\\DRomFS.bin','--romfs-auto-key'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','exefs',o + '\\DExeFS.bin','--header',o + '\\HExeFS.bin','--exefs-dir',o + '\\ExeFS'])
            if e: return 1
            e,_,_ = run(['3dstool','-xtf','romfs',o + '\\DRomFS.bin','--romfs-dir',o + '\\RomFS'])
            if e: return 1

            for x in listdir(o):
                if x.endswith('.bin'): remove(o + '/' + x)
            return
        case 'Switch NSP'|'Switch NCA'|'Switch XCI':
            for k in ('prod','dev'):
                bcd = ['hac2l','-t',{'Switch NSP':'pfs','Switch NCA':'nca','Switch XCI':'xci'}[t],'--disablekeywarns','-k',db.get(k+'keys'),'--titlekeys=' + dirname(db.get(k+'keys')) + '\\title.keys']
                _,e,_ = run(bcd + [i],print_try=False)
                bcd += ['--exefsdir=' + o + '\\ExeFS','--romfsdir=' + o + '\\RomFS']
                if ' MetaType=Patch ' in e and not ' MetaType=App ' in e:
                    pinf = re.search(r'ProgramId=([\dA-F]+), Version=0x([\dA-F]+),',e)
                    pid,pv = pinf[1],int(pinf[2],16)
                    for x in listdir(dirname(i)):
                        if pid in x and x.endswith('.nsp'):
                            try: v = int(re.search(r'v(\d+)(?:\b|_)(?!\.)',x)[1])
                            except: v = 0
                            if v < pv: bf = dirname(i) + '\\' + x;break
                    else: return 1
                    bcd += ['--basepfs',bf]
                run(bcd + [i])
                if listdir(o) and listdir(o + '/ExeFS') and listdir(o + '/RomFS'): return
                rmdir(o)
                mkdir(o)
        case 'NDS':
            run(['mdnds','e',i,o])
            if listdir(o): return
        case 'PS4 PKG':
            rtd = TmpDir()
            run(['ps4pkg','img_extract','--passcode','00000000000000000000000000000000','--tmp_path',rtd,i,o])
            rtd.destroy()
            if os.path.exists(o + '/Image0') and listdir(o + '/Image0'):
                fs = listdir(o)
                copydir(o + '/Image0',o)
                mv(o + '/Sc0',o + '/sce_sys')
                for x in fs: remove(o + '/' + x)
                return
        case 'PS5 PKG':
            rtd = TmpDir()
            run(['ps5pkg','img_extract','--passcode','00000000000000000000000000000000','--tmp_path',rtd,i,o])
            rtd.destroy()
            if listdir(o): raise NotImplementedError()
            if os.path.exists(o + '/Image0') and listdir(o + '/Image0'):
                fs = listdir(o)
                copydir(o + '/Image0',o)
                mv(o + '/Sc0',o + '/sce_sys')
                for x in fs: remove(o + '/' + x)
                return
        case 'PS3 ISO':
            from bin.ps3key import PS3Keys
            k = PS3Keys().get(i)
            tf = TmpFile('.iso',path=o)
            tf.link(i)
            run(['ps3dec','-k',k,'-t','16','-s',tf],cwd=TMP)
            rmdir(TMP + '/log')
            tf.destroy()
            if os.path.exists(tf.p + '_decrypted.iso'):
                r = extract(tf.p + '_decrypted.iso',o,'ISO')
                remove(tf.p + '_decrypted.iso')
                if r or not listdir(o): return 1
                return
            if not extract(i,o,'ISO'): return
        case 'PSVita PKG':
            if exists(dirname(i) + '/work.bin'): work = dirname(i) + '/work.bin'
            elif exists(noext(i) + '.work.bin'): work = noext(i) + '.work.bin'
            else:
                f = open(i,'rb')
                f.seek(0x10)
                ms = int.from_bytes(f.read(4),'big')
                f.close()
                if ms >= 0x140: return 1
                work = None

            if work:
                import zlib,base64
                ZRIF_DICT = zlib.decompress(base64.b64decode(b"eNpjYBgFo2AU0AsYAIElGt8MRJiDCAsw3xhEmIAIU4N4AwNdRxcXZ3+/EJCAkW6Ac7C7ARwYgviuQAaIdoPSzlDaBUo7QmknIM3ACIZM78+u7kx3VWYEAGJ9HV0="))
                rif = open(work,'rb').read()
                c = zlib.compressobj(level=9,wbits=10,memLevel=8,zdict=ZRIF_DICT)
                bn = c.compress(rif)
                bn += c.flush()
                if len(bn) % 3: bn += bytes(3 - len(bn) % 3)
                zrif = base64.b64encode(bn).decode()

            osj = OSJump()
            osj.jump(o)
            run(['pkg2zip','-x',i] + ([zrif] if work else []))
            if exists('app') and listdir('app') and listdir('app/' + listdir('app')[0]):
                td = o + '/app/' + listdir('app')[0]
                osj.back()

                run(['psvpfsparser','-i',td,'-o',o,'-z',zrif])
                rmtree(o + '/app')

                if listdir(o): return
            else: osj.back()
            if not work and listdir(o):
                if exists(o + '/pspemu/PSP'):
                    copydir(o + '/pspemu/PSP',o,True,reni=True)
                    os.rmdir(o + '/pspemu')
                return
        case 'WUX':
            from bin.wiiudk import DKeys
            kys = DKeys()
            cmd = ['java','-jar',db.get('jwudtool'),'-commonkey',kys.get('common'),'-decrypt','-in',i,'-out',o]
            k = kys.get(i)
            if not k: cmd.append('-dev')
            else: cmd += ['-titleKey',k]
            if db.print_try: print('Trying with jwudtool')
            run(cmd,print_try=False)
            if listdir(o):
                for x in listdir(o):
                    try:
                        if not x.startswith('GM'): remove(o + '/' + x);continue
                        if not exists(o + '/' + x + '/content'): remove(o + '/' + x);continue
                        copydir(o + '/' + x,o,True)
                    except PermissionError: pass
                return
        case 'XISO':
            run(['xdvdfs','unpack',i,o])
            if listdir(o): return
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
            if listdir(o): return
        case 'GD-ROM CUE+BIN':
            run(['buildgdi','-extract','-cue',i,'-output',o + '\\','-ip',o + '\\IP.BIN'])
            if listdir(o):
                from bin.sgkey import SGKeys
                if exists(o + '/IP.BIN') and SGKeys().get(o): return extract(o + '\\IP.BIN',o,'Encrypted GD-ROM')
                return
        case 'Nintendo TMD':
            ckeys = db.get('tmd_keys') + '/'

            if db.print_try: print('Trying with custom extractor')
            from bin.tmd import TMD,Ticket,PWDS,derive_key,decrypt_content,unscramble_3ds

            dr = dirname(i)
            dls = [x for x in listdir(dr) if isfile(dr + '/' + x)]
            if 'tmd' in dls: tmd = 'tmd'
            else: tmd = max([x for x in dls if x.startswith('tmd.')],key=lambda x:int(x.split('.')[-1]))
            tmd = TMD(dr + '/' + tmd)

            if tmd.sigt == 1 and tmd.version == 0: cns = 'w'
            elif tmd.sigt in (3,4,5) and tmd.version == 1: cns = '3'
            else: raise NotImplementedError(f'{tmd.signature.type:4X} {tmd.version}')

            if exists(dr + '/cetk'):
                cetk = Ticket(dr + '/cetk')
                if cns == 'w':
                    if not exists(ckeys + 'wii-common.key'):
                        s = db.c.get('https://wiki.wiidatabase.de/wiki/Common-Key').text
                        for r,k in [('Normal','common'),
                                    ('Korea' ,'korea' ),
                                    ('Debug' ,'debug' )]:
                            open(ckeys + f'wii-{k}.key','wb').write(bytes.fromhex(re.search(f'<b>{r}:</b> *<code>([^<]+)</code>',s)[1]))
                    cetk.ckey = open(ckeys + f'wii-{["common","korea","debug"][cetk.ckeyindex]}.key','rb').read()
                elif cns == '3':
                    if not exists(ckeys + '3ds-generator.key'):
                        s = db.c.get('https://raw.githubusercontent.com/Kc57/ntool/refs/heads/master/lib/keys.py').text
                        open(ckeys + '3ds-generator.key','wb').write(bytes.fromhex(re.search(r'\) *\+ *0x([\da-fA-F]{32}), *87, *128\)',s)[1]))

                        x3d = re.search(r'KeyX0x3D *= *\(0x([\da-fA-F]{32}), *0x([\da-fA-F]{32})\)',s)
                        open(ckeys + '3ds-3Dx.key','wb').write(bytes.fromhex(x3d[1]))
                        open(ckeys + '3ds-dev-3D.key','wb').write(bytes.fromhex(x3d[2]))

                        y3d = re.search(r'KeyY0x3D *= *\(\s*((?:\(0x[\da-fA-F]{32}, *0x[\da-fA-F]{32}\),?\s*)+)\)\n',s)[1]
                        y3dr = []
                        y3dd = []
                        for r,d in re.findall(r'\(0x([\da-fA-F]{32}), *0x([\da-fA-F]{32})\)',y3d):
                            y3dr.append(bytes.fromhex(r))
                            y3dd.append(bytes.fromhex(d))

                        open(ckeys + '3ds-3Dy.key','wb').write(b''.join(y3dr))
                        open(ckeys + '3ds-dev-3Dy.key','ab').write(b''.join(y3dd))

                    g3d = open(ckeys + '3ds-generator.key','rb').read()
                    x3d = open(ckeys + '3ds-3Dx.key','rb').read()
                    y3d = open(ckeys + '3ds-3Dy.key','rb')
                    y3d.seek(0x10 * cetk.ckeyindex)
                    y3d = y3d.read(0x10)
                    cetk.ckey = unscramble_3ds(x3d,y3d,g3d)
            else: cetk = None

            for c in tmd.contents:
                fn = hex(c.cid)[2:].zfill(8)
                odr = o + '/' + fn
                ifl = dr + '/' + fn

                if c.type & 1:
                    tf = TmpFile()
                    pwids = list(range(len(PWDS)))
                    if cns == 'w': pwids.insert(0,1)
                    elif cns == '3': pwids.insert(0,0)
                    for ix in set([-1] + pwids):
                        if ix == -1: k = cetk.get_key()
                        else: k = derive_key(tmd.titleid,ix)
                        decrypt_content(ifl,tf,k,c)
                        if tmd.check_file(tf,c.sha): break
                    else: raise Exception
                    ifl = str(tf)

                if cns == 'w':
                    if c.type == 2: copy(ifl,o + '/CAFEDEAD.bin')
                    elif c.type & 0x8000:
                        if extract(ifl,o + '/$SHARED','U8'): copy(ifl,o + '/$SHARED/' + fn + '.bin')
                    elif c.index == 0 and tmd.titleid == b'\0\0\0\1\0\0\0\2': copy(ifl,o + '/build_tag.bin')
                    elif c.index == 0: copy(ifl,o + '/banner.bnr')
                    elif c.index == 1: copy(ifl,o + '/launch.dol')
                    elif tmd.bootindex == c.index: copy(ifl,o + '/boot.dol')
                    else:
                        if open(ifl,'rb').read(4) == b'U\xAA8\x2D':
                            if extract(ifl,odr,'U8'): copy(ifl,odr + '.bin')
                        else: copy(ifl,odr + '.bin')
                elif cns == '3':
                    if c.type & 0x4000: copy(ifl,odr + '.dlc')
                    elif c.index == 0 and tmd.srl_flag:
                        if extract2(ifl,odr,'NDS'): copy(ifl,odr + '.srl')
                    elif c.index == 0:
                        f = open(ifl,'rb')
                        f.seek(0x100)
                        ncch = f.read(4) == b'NCCH'
                        f.seek(0x208)
                        cxi = ncch and f.read(4) == b'\0\0\0\0'
                        f.seek(0x560)
                        cxi = cxi and f.read(0x10) == (b'\xFF'*0x10)
                        f.close()
                        if cxi:
                            if extract(ifl,odr,'NCCH CXI'): copy(ifl,odr + '.cxi')
                        elif ncch:
                            if extract(ifl,odr,'NCCH CFA'): copy(ifl,odr + '.cfa')
                        else: copy(ifl,odr + '.bin')
                    elif c.index in (1,2):
                        if extract2(ifl,odr,'NCCH CFA'): copy(ifl,odr + '.cfa')
                    else: copy(ifl,odr + '.bin')
            return
        case '3DO IMG':
            run(['3dt','unpack','-o',o,i])
            if listdir(o) and listdir(o + '/' + basename(i) + '.unpacked'):
                copydir(o + '/' + basename(i) + '.unpacked',o,True)
                return
        case 'Amiga IMG'|'SPS IPF':
            td = TmpDir()
            run(['uaeunp','-x',i,'**'],cwd=td.p)
            for f in listdir(td.p):
                if isdir(td.p + '/' + f): copydir(td.p + '/' + f,o)
            td.destroy()
            if listdir(o): return

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
            if listdir(o): return
        case 'ZArchive':
            run(['zarchive',i,o])
            if listdir(o): return
        case 'C64 Tape'|'C64 LiBRary':
            run(['dirmaster','/e',i],cwd=o)
            if listdir(o): return
        case 'Encrypted GD-ROM':
            from bin.sgkey import SGKeys

            id = dirname(i)
            t,key = SGKeys().get(i)
            if not key: return 1

            drvs = []
            for f in listdir(id):
                if len(f) != 7: continue
                ld = id + '\\' + f
                if isdir(ld) or getsize(ld) != 0x100: continue

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
                    else: tff.seek(0)

                    if not nt:
                        if tff.read(13) == b'SimpleFlashFS': nt = 'SimpleFlashFS'
                        else:
                            tff.seek(0x800000)
                            if tff.read(13) == b'SimpleFlashFS': nt = 'SimpleFlashFS'
                    tff.close()

                    if nt:
                        mkdir(od)
                        extract2(tf,od,nt)
                elif t == '2':
                    tff = open(tf,'rb')
                    nt = None

                    if tff.read(0x60) == b'Naomi2          SEGA CORPORATION                INITIAL D Ver.3                 INITIAL D Ver.3 IN USA          ': nt = 'Initial D 3 Export A'
                    else: tff.seek(0)
                    if tff.read(0x40) == b'Naomi2          SEGA ENTERPRISES,LTD.           VIRTUA STRIKER 3': nt = 'Virtua Striker 3 A'
                    else: tff.seek(0)

                    if not nt:
                        if tff.read(13) == b'SimpleFlashFS': nt = 'SimpleFlashFS'
                        else:
                            tff.seek(0x800000)
                            if tff.read(13) == b'SimpleFlashFS': nt = 'SimpleFlashFS'
                    tff.close()

                    if nt:
                        mkdir(od)
                        extract2(tf,od,nt)
                if exists(od) and not listdir(od): rmdir(od)
            return
        case 'N64DD':
            run(['mfs_manager',i,'-e'],cwd=o)
            if listdir(o): return
        case 'MSX Cassette IMG':
            run(['mcp','-x',i],cwd=o)
            if listdir(o): return
        case 'ZX Spectrum Tape IMG':
            run(['tapsplit',i,o])
            if listdir(o): return
        case 'CPC Plus IMG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File

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
            from lib.file import File

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
            from lib.file import File
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
            from lib.file import File
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

                    name = f.read(4).strip(b' \0\xFF').decode('ascii')
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
                    name = f.read(8).strip(b' \0\xFF').decode('ascii') or bname
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
            if listdir(o): return
        case 'XVD':
            from bin.xb1key import XB1Keys

            xb1k = XB1Keys()

            for p in ('../',''):
                p = dirname(i) + '/' + p + 'Licenses'
                if exists(p):
                    for f in listdir(p):
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
                if not listdir(o):
                    copy(i,o + '/' + basename(i) + '.dec.xvd')
                    run(['xvdtool.streaming','decrypt','-c',tf.p,'-n',o + '/' + basename(i) + '.dec.xvd'])
                    remove(tf.p)
                    return
                remove(tf.p)
            if listdir(o): return
        case 'Acorn Disc Filing IMG':
            tf = TmpFile('.txt')
            open(tf.p,'w',encoding='utf-8').write(f'insert "{i}"\nextract *\nfree\nexit\n')
            run(['discimagemanager','-c',tf],cwd=o)
            tf.destroy()
            if listdir(o):
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
                            set_ctime(f,ft)
                return
        case 'C64 IMG':
            run(['c1541'],stdin=f'attach "{i}"\nextract\nquit\n',cwd=o)
            cd = dirname(db.get('c1541'))
            remove(cd + '/stderr.txt',cd + '/stdout.txt')
            if listdir(o): return

            if not extract(i,o,'DIET'):return # deark 

            return extract2(i,o,'C64 Tape')
        case 'Playdate Container':
            raise NotImplementedError # https://github.com/rarenight/pdx-decrypt/blob/main/pdx-decrypt.py
        case 'PlayStation APA IMG':
            tf = TmpFile('.tar',path=o)
            run(['pfs2tar','--backup',i,tf])
            if not exists(tf.p): return 1
            r = extract(tf.p,o,'TAR')
            tf.destroy()
            return r
        case 'PlayStation Boot Package':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'\0PBP'
            f.skip(4)
            offs = [f.readu32() for _ in range(8)] + [f.size]
            fs = [(offs[x],offs[x+1]-offs[x]) for x in range(8)]

            f.seek(fs[0][0])
            open(o + '/PARAM.SFO','wb').write(f.read(fs[0][1]))
            sfo = File(o + '/PARAM.SFO',endian='<')
            sfo.skip(8)
            bko = sfo.readu32()
            sfo.skip(4)
            ksc = sfo.readu32()

            kso = []
            for _ in range(ksc):
                kso.append(sfo.readu16())
                sfo.skip(14)

            ks = []
            for kse in kso:
                sfo.seek(bko + kse)
                ks.append(sfo.read0s().decode('ascii'))
            sfo.close()

            psp = any(x in ks for x in ('DRIVER_PATH','MEMSIZE','UPDATER_VER','TITLE_XX'))
            ps = 'LICENSE' in ks
            pspr = not psp and any(x in ks for x in ('APP_VER','HRKGMP_VER'))
            mini = not psp and 'ATTRIBUTE' in ks

            f.seek(fs[1][0])
            open(o + '/ICON0.PNG','wb').write(f.read(fs[1][1]))
            if fs[2][1]:
                f.seek(fs[2][0])
                d = f.read(fs[2][1])
                open(o + '/ICON1.' + ('PNG' if d[:4] == b'\x89PNG' else 'PMF'),'wb').write(d)
            if fs[2][0] != fs[3][0]:
                f.seek(fs[3][0])
                open(o + '/PIC0.PNG','wb').write(f.read(fs[3][1]))
            f.seek(fs[4][0])
            open(o + '/PIC' + ('T' if mini or ps else '') + '1.PNG','wb').write(f.read(fs[4][1]))
            if mini or psp:
                f.seek(fs[5][0])
                open(o + '/SND0.AT3','wb').write(f.read(fs[5][1]))
            f.seek(fs[6][0])
            open(o + '/DATA.PSP','wb').write(f.read(fs[6][1]))
            f.seek(fs[7][0])
            open(o + '/DATA.PSAR','wb').write(f.read(fs[7][1]))

            return
        case 'SimpleFlashFS':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            if f.read(13) != b'SimpleFlashFS':
                f.seek(0x800000)
                assert f.read(13) == b'SimpleFlashFS'
            f.skip(0x23 + 8)
            f.skip(f.readu32() - 0x3C)

            while True:
                cp = f.pos
                skps = f.readu32()
                ln = f.readu32()
                if ln == 0xFFFFFFFF:
                    if skps == 0xFFFFFFFF: break
                    f.seek(cp + skps)
                    continue
                f.skip(4)
                fs = f.readu32()
                f.skip(0x70)
                fn = f.read(0x40).split(b'\0',1)[0].decode('ascii')
                f.skip(0x40)

                open(o + '/' + fn,'wb').write(f.read(fs))
                f.seek(cp + ln)
            if listdir(o): return
        case 'Konami Python IMG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='>')

            assert f.read(4) == b'\xDE\xAD\xBE\xEF'
            f.skip(2)
            fc = f.readu16()
            ss = f.readu16()
            f.skip(2)
            infs = f.readu16()
            open(o + '/$INFO.xml','wb').write(f.read(infs-1))

            f.seek(0x400)
            fs = []
            for _ in range(fc):
                fe = [f.readu32()*ss]
                xs = f.readu16()
                f.skip(1)
                fe.append(f.read(8).rstrip(b'\0').decode('ascii'))
                f.skip(1)
                es = f.readu32()
                f.skip(-4)

                fe.append(((es-1)*ss + xs)-fe[0])
                fs.append(fe)

            for fe in fs:
                f.seek(fe[0])
                open(o + '/' + fe[1],'wb').write(f.read(fe[2]))
            if fs: return
        case 'StudyBox IMG':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            assert f.read(4) == b'STBX'
            f.skip(f.readu32())

            c = 0
            while f:
                t = f.read(4).decode('latin-1')
                s = f.readu32()
                if t == 'PAGE': ext = 'bin'
                elif t == 'AUDI':
                    ext = 'wav'
                    f.skip(4)
                    assert f.read(4) == b'RIFF'
                    f.skip(-4)
                    s -= 4
                else: raise NotImplementedError(t)

                open(o + f'/{t}{c:02d}.{ext}','wb').write(f.read(s))
                c += 1
            if c: return
        case 'iNES ROM':
            MAPPERS = {ix:x for ix,x in enumerate(( # 0 - 92
                "No mapper","Nintendo MMC1B","UxROM","CNROM-32","MMC3","MMC5","Front Fareast Magic Card 1/2M RAM Cartridge",
                "AxROM","Front Fareast Magic Card 1/2M RAM Cartridge [Initial latch-based banking mode 4]","MMC2","MMC4",
                "Color Dreams","[Submapper]","CPROM","SL-1632","K-102xx","Bandai FCG","Front Fareast Super Magic Card RAM Cartridge",
                "Jaleco SS88006","Namco 129/163","Famicom Disk System","Konami VRC4a/VRC4c","Konami VRC2a","Konami VRC4e | VRC2b + VRC4f",
                "Konami VRC6a","Konami VRC4d | VRC2c + VRC4b","Konami VRC6b","World Hero","InfinteNESLives' Action 53",
                "RET-CUFROM","UNROM 512","NSF","G-101","Taito TC0190","[Submapper]","J.Y. Company ASIC [8kb WRAM]",
                "Micro Genius 01-22000-400","SMB + Tetris + NWC","Bit Corp. Crimee Busters","Study & Game 32-in-1","NTDEC 27xx",
                "Caltron 6-in-1","FDS -> NES Hacks","TONY-I/YS-612","Super Big 7-in-1","GA32C | TC3294","Lite Star's Rumble Station",
                "Nintendo Super Spike V'Ball + NWC","Taito TC0690","Super HIK 4-in-1","N-32","[Submapper]","Realtec 8213",
                "Supervision 16-in-1","Novel Diamond 9999999-in-1","QFJxxxx","KS202","GK","WQ","T3H53","Reset based NROM-128 4-in-1",
                "[Submapper]","Super 700-in-1","[Submapper]","Tengen RAMBO-1","Irem H3001","xxROM","Sunsoft-3","Sunsoft-4",
                "Sunsoft FME-7/5A/5b","Family Trainer Mat","Camerica","Jaleco JF-17 [16kb PRGROM]","Konami VRC3","860908C",
                "Konami VRC1","NAMCOT-3446","Napoleon Senki","74HC161/32","Tengen NINA-003/006","X1-005","N715021","X1-017",
                "Cony & Yoko","PC-SMB2J","Konami VRC7","Jaleco JF-13","JF87","Namco","Sunsoft 2.5","J.Y. Company ASIC [ROM Nametables + Extended Mirroring]",
                "J.Y. Company Clone Boards","Jaleco JF-17 [16kb PRGROM]",
            ))} | {
                124:"Super Game Mega Type III",126:"TEC9719",132:"TXC 05-00002-010",173:"C&E 05-00002-010",187:"Kǎ Shèng A98402",
                256:"V.R. Technology OneBus",269:"Nice Code Games Xplosion 121-in-1",355:"Jùjīng 3D-BLOCK",419:"Taikee TK-8007 MCU",
                422:"ING-022",423:"Lexibook Compact Cyber Arcade",424:"Lexibook Retro TV Game Console",425:"Cube Tech Handheld",
                426:"V.R. Technology OneBus [Serial ROM in GPIO]",534:"ING003C",594:"Rinco FSG2",595:"NES-4MROM-512"
            }

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'NES\x1A'

            prgs = f.readu8()
            chrs = f.readu8()
            f6,f7,f8,f9,f10 = [f.readu8() for _ in range(5)]
            x = sum(f.read(5))
            f.skip(-9)

            tr = trb = 1 if f6 & 0b1000 else 0
            if tr and f.size - (0x10 + prgs*1024*16 + chrs*1024*8) < 512: tr = 0
            ines2 = (f7 & 0b1100) >> 2
            cons = f7 & 3

            inf = open(o + '/info.txt','w',encoding='utf-8')
            inf.write(f'PRG: {prgs} * 16kb\nCHR: {chrs} * 8kb\nTrainer: {tr} * 512 (0b{trb})\n\nMirror: {"H" if f6&1 else "V"}\nIgnore Mirror: {bool(f6&2)}\nBattery: {bool(f6&4)}\n')
            if ines2 in (1,3): v = 0
            elif ines2 == 2 and (f9 << 8) <= f.size: v = 2
            elif x: v = 0.7
            elif f10: v = 1.2
            elif f8 or f9: v = 1.1
            else: v = 1

            mapr = f6 >> 4
            if v >= 0.7: mapr |= f7 & 0xF0
            if v >= 2: mapr |= (f8 & 0x0F) << 8
            inf.write(f'Mapper: {MAPPERS[mapr] if mapr in MAPPERS else "?"} ({mapr} 0b{bin(mapr)[2:].zfill((12 if v >= 2 else 8) if v >= 0.7 else 4)})\n')
            if mapr == 0: inf.write('Designation: NROM\n')
            elif mapr == 1: inf.write('Designation: SxROM\n')
            elif mapr == 4:
                if prgs >= 8 and chrs >= 16:
                    if (v in (1,1.1,1.2) and f8 != 1) or (v == 2 and f10&0xF0 != 7): inf.write('Designation: TLROM [128-512kb PRGROM]\n')
                    elif f6&4: inf.write('Designation: TKROM [128-512kb PRGROM, 8kb PRGRAM]\n')
                    else: inf.write('Designation: TSROM [128-512kb PRGROM, 8kb PRGRAM, no battery]\n')
                elif prgs == 4: inf.write('Designation: TBROM [64kb PRGROM]\n')
                else: inf.write('Designation: TxROM\n')
            if v >= 2:
                subm = f8 >> 4
                subn = ''
                if mapr == 3:
                    if subm == 0: subn = 'Bus conflict'
                    elif subm == 1: subn = 'No bus conflict'
                    elif subm == 2: subn = 'AND-type bus conflict'
                elif mapr == 12:
                    if subm == 0: subn = 'Supertone SL-5020B'
                    elif subm == 1: subn = 'Front Fareast Magic Card 4M RAM Cartridge'
                elif mapr == 16:
                    if subm == 0: subn = 'Bandai FCG-1/2 + Bandai LZ93D50'
                    elif subm == 4: subn = 'Bandai FCG-1/2'
                    elif subm == 5: subn = 'Bandai LZ93D50'
                elif mapr == 34:
                    if subm == 0: subn = 'Tengen NINA-001/002'
                    elif subm == 1: subn = 'BNROM'
                elif mapr == 40:
                    if subm == 0: subn = 'NTDEC 2722'
                    elif subm == 1: subn = 'NTDEC 2752'
                elif mapr == 51:
                    if subm == 1: subn = '11-in-1 Ball Games'
                elif mapr == 61:
                    if subm == 0: subn = 'NTDEC 0324'
                    elif subm == 1: subn = 'NTDEC BS-N032'
                    else: subn = 'GS-2017'
                elif mapr == 63:
                    if subm == 0: subn = 'NTDEC TH2xxx-x'
                    elif subm == 1: subn = '82-in-1'
                elif mapr in (256,419):
                    if subm == 0: subn = 'Normal'
                    elif subm == 1: subn = 'Waixing VT03'
                    elif subm == 2: subn = 'Nice Code VT02'
                    elif subm == 3: subn = 'Hummer Technology'
                    elif subm == 4: subn = 'Nice Code VT03'
                    elif subm == 5: subn = 'Waixing VT02'
                    elif subm == 11: subn = 'Vibes'
                    elif subm == 12: subn = 'Cheertone'
                    elif subm == 13: subn = 'Cube Tech'
                    elif subm == 14: subn = 'Karaoto'
                    elif subm == 15: subn = 'JungleTac Fuzhou'
                    if subn: subn += ' wiring'
                if subm and not subn: subn = '?'
                if subn: inf.write(f'Submapper: {subn} ({subm} 0b{bin(subm)[2:].zfill(4)})\n')

            vs = {0:"Archaic",0.7:"0.7",1:"1.0",1.1:"1.0 updated",1.2:"1.0 unofficial",2:f"2.0 ({ines2} 0b{bin(ines2)[2:].zfill(2)})"}[v]
            inf.write(f'iNES: {vs}\n\n')
            if v >= 0.7: inf.write(f'Console: {["Regular","Vs.","PlayChoice-10","[Extended]"][cons]} ({cons} 0b{bin(cons)[2:].zfill(2)})\n')

            if v == 2:
                EXPDEV = {ix:x for ix,x in enumerate((
                    'Unspecified','Standard Controllers','Four Score | Satellite','Famicom 4 Player Adapter',
                    'Vs. System 1P4016H','Vs. System 1P4017H','MAME Pinball Japan','Vs. Zapper','Zapper',
                    '2 Zappers','Bandai Hyper Shot Lightgun','Power Pad Side A','Power Pad Side B',
                    'Family Trainer Side A','Family Trainer Side B',
                ))} | {0x2A:'Multicart'}

                f11,f12,f13,f14,f15 = [f.readu8() for _ in range(5)]
                if f9:
                    prgs |= (f9 & 0x0F) << 8
                    chrs |= (f9 & 0xF0) << 4
                    inf.write(f'PRGROM (2.0): {prgs} * 16kb\n')
                    inf.write(f'CHRROM (2.0): {chrs} * 8kb\n')
                inf.write(f'PRGRAM Shift: {f10 & 0xF}\n')
                inf.write(f'EEPROM Shift: {f10 >> 4}\n')
                inf.write(f'CHRRAM Size Shift: {f11 & 0xF}\n')
                inf.write(f'CHRNVRAM Size Shift: {f11 >> 4}\n')
                tim = f12 & 0b11
                inf.write(f'Timing: {["NTSC","PAL","Multi","Dendy"][tim]} ({tim} 0b{bin(tim)[2:].zfill(2)})\n')
                if cons == 1:
                    VSPPU = {
                        0:"RP2C03/RC2C03 Variant",
                        2:"RP2C04-0001",
                        3:"RP2C04-0002",
                        4:"RP2C04-0003",
                        5:"RP2C04-0004",
                        8:"RC2C05-0001",
                        9:"RC2C05-0002",
                        10:"RC2C05-0003",
                        11:"RC2C05-0004",
                    }
                    VSHW = {ix:x for ix,x in enumerate((
                        ("Unisystem","Normal"),
                        ("Unisystem","RBI Baseball"),
                        ("Unisystem","TKO Boxing"),
                        ("Unisystem","Super Xevious"),
                        ("Unisystem","Vs. Ice Climber Japan"),
                        ("Dual System","Normal"),
                        ("Dual System","Raid on Bungeling Bay"),
                    ))}

                    vsppu = f13 & 0x0F
                    inf.write(f'Vs. PPU: {VSPPU[vsppu] if vsppu in VSPPU else "?"} ({vsppu} 0b{bin(vsppu)[2:].zfill(4)})\n')
                    vshw = f13 >> 4
                    inf.write(f'Vs. Hardware|Protection: {"|".join(VSHW[vshw]) if vshw in VSHW else "?|?"} ({vshw} 0b{bin(vshw)[2:].zfill(4)})\n')
                elif cons == 3:
                    EXTCON = {ix:x for ix,x in enumerate((
                        'Regular','Vs.','PlayChoice-10'
                        'Famiclone Decimal Mode','NES with EPSM | Plug-Through','V.R. Technology VT01',
                        'V.R. Technology VT02','V.R. Technology VT03','V.R. Technology VT09','V.R. Technology VT32',
                        'V.R. Technology VT369','UMC UM6578','Famicom Network System'
                    ))}
                    expdev = f13 & 0x0F
                    inf.write(f'Extended Device: {EXTCON[expdev] if expdev in EXTCON else "?"} ({expdev} 0b{bin(expdev)[2:].zfill(4)})\n')
                inf.write(f'Miscellaneous ROMs: {f14 & 0b11}\n')
                inf.write(f'Expansion Device: {EXPDEV[f15] if f15 in EXPDEV else "?"} ({f15} 0b{bin(f15)[2:].zfill(6)})\n')
            elif v in (1.1,1.2):
                inf.write(f'PRGRAM: {f8} * 8kb\n')
                inf.write(f'TV System: {["NTSC","PAL"][f9]}\n')
                if v == 1.2:
                    tv2 = f10 & 3
                    inf.write(f'TV System (unofficial): {["NTSC","NTSC & PAL","PAL","PAL & NTSC"][tv2]} ({tv2} 0b{bin(tv2)[2:].zfill(2)})\n')
                    inf.write(f'Ignore PRGRAM: {bool(f10 & 0x10)}\n')
                    inf.write(f'Bus Conflicts: {bool(f10 & 0x20)}\n')
            elif v <= 0.7:
                if v == 0.7: f.skip(1)
                inf.write(f'Ripper: {f.read(16-f.pos).rstrip(b"\0").decode("ascii")}\n')
            inf.write('\n')

            f.seek(0x10)
            if tr: open(o + '/trainer.prg','wb').write(f.read(512))
            for ix in range(prgs):
                if ix == prgs - 1:
                    d = f.read(1024*16-6)
                    inf.write(f'NMI Vector: 0x{f.readu16():4X}\n')
                    inf.write(f'Reset Vector: 0x{f.readu16():4X}\n')
                    inf.write(f'IRQ Vector: 0x{f.readu16():4X}\n')
                else: d = f.read(1024*16)
                open(o + f'/PRG{ix}.prg','wb').write(d)
            inf.close()

            for ix in range(chrs):
                d = f.read(1024*8)
                open(o + f'/CHR{ix}.chr','wb').write(d)

                td = bytearray(256*128)
                for t in range(0x200):
                    to = t*16
                    tx = (t%0x20)*8
                    ty = (t//0x20)*8
                    for y in range(8):
                        b1,b2 = d[to+y],d[to+y+8]
                        for x in range(8): td[(ty+y)*256 + tx+x] = ((b1 >> (7-x)) & 1) | (((b2 >> (7-x)) & 1) << 1)
                open(o + f'/CHR{ix}.pgm','wb').write(b'P5\n256 128\n3\n' + td)

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
            
            while not listdir(i + '_extract'): sleep(0.1)
            while True:
                try:copydir(i + '_extract',o,True)
                except:sleep(0.1)
                else:break
            p.kill()
            remove(tf)

            for x in listdir(o):
                if not getsize(o + '/' + x): remove(o + '/' + x)

            if listdir(o): return
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
        case 'Virtua Striker 3 A':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            f.seek(0x800000)
            fs = []
            while True:
                off1 = f.readu32()
                if not off1: break
                siz1 = f.readu32()
                f.skip(4)
                off2 = f.readu32()
                siz2 = f.readu32()
                if off2: f.skip(8)
                f.skip(4)
                fn = f.read(0x10).rstrip(b'\0').decode('ascii')
                fs.append((fn,off2 or off1,siz2 if off2 else siz1))

            for fe in fs:
                f.seek(fe[1])
                open(o + '/' + fe[0],'wb').write(f.read(fe[2]))

            f.close()
            if fs: return
        case 'Zelda N64 ROM':
            run(['zre','-o',o,i])
            if listdir(o): return
        case 'Banjo Kazooie N64 ROM':
            td = TmpDir(path=o)
            run(['bk_extract','-p',td,'-r',i])
            if exists(td.p + '/out') and listdir(td.p + '/out') and (len(listdir(td.p + '/out')) > 1 or listdir(td.p + '/out/' + listdir(td.p + '/out')[0])): raise NotImplementedError
            if not exists(td.p + '/bin') or not listdir(td.p + '/bin'): return 1
            if len(listdir(td.p + '/bin')) > 1: raise NotImplementedError
            copydir(td.p + '/bin/' + listdir(td.p + '/bin')[0],o,True)
            td.destroy()
            for f in listdir(o):
                if f.startswith('unknown_') and f.endswith('.bin') and not getsize(o + '/' + f): remove(o + '/' + f)
            return
        case 'Mario Kart 64 N64 ROM':
            f = open(i,'rb')
            f.seek(0x3B)
            tg = f.read(4).decode('ascii')
            f.close()

            if t == 'Mario Kart 64 N64 ROM' and tg == 'NKTE': scr = 'spaghettikart_yaml'
            else: raise NotImplementedError(t + ': ' + tg)

            import zipfile
            run(['torch','o2r','-s',db.get(scr),'-d',o,i])
            if len(listdir(o)) == 2:
                remove(o + '/torch.hash.yml')
                zipfile.ZipFile(o + '/' + listdir(o)[0]).extractall(o)
                remove(o + '/' + listdir(o)[0])
                return

    return 1
