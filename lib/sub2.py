from .main import *

C64TM = {
    'C64 ROM-TAPE HEADER':'header',
    'PRG':'prg',
    'C64 ROM-TAPE DATA':'dat',
    'OCEAN/IMAGINE F1':'f1.prg',
}

def clean_dol(id:str):
    if len(listdir(id)) == 2 and exists(id + '/UPDATE'):
        mv(id + '/UPDATE',id + '/$UPDATE')
        clean_dol(id + '/$UPDATE')
    if exists(id + '/DATA'): copydir(id + '/DATA',id,True,True)
    asrt(exists(id + '/sys'),err=FileNotFoundError)
    mv(id + '/sys',id + '/$SYS')
    if exists(id + '/disc'): mv(id + '/disc',id + '/$SYS/disc')
    for f in listdir(id):
        if isfile(id + '/' + f): mv(id + '/' + f,id + '/$SYS/' + f)
    if exists(id + '/files'): copydir(id + '/files',id,True,True)

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
        case 'RVZ'|'NKit Wii ISO'|'NKit GameCube ISO':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if listdir(o):
                clean_dol(o)
                return
            tf = TmpFile('.iso')
            run(['dolphintool','convert','-u',gtmp('user'),'-i',i,'-o',tf,'-f','iso'])
            if exists(tf.p):
                run(['wit','-q','X',tf,'-p','-o','-E$','-d',o])
                tf.destroy()
                fs = listdir(o)
                if len(fs) == 1:
                    while True:
                        try:
                            if not exists(o + '/$SYS'): mv(o + '/' + fs[0] + '/sys',o + '/$SYS')
                            copydir(o + '/' + fs[0] + '/files',o,True)
                            remove(o + '/' + fs[0])
                        except PermissionError:sleep(0.1)
                        else:return
            tf.destroy()
        case 'Wii ISO'|'GameCube ISO':
            run(['dolphintool','extract','-i',i,'-o',o,'-q'])
            if listdir(o):
                clean_dol(o)
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
            db.try_custom()
            tf = TmpFile('.iso')
            with xopen(i,'rb') as fi:
                fi.seek(0x20)
                with tf.open('wb') as f:
                    d = b''
                    while True:
                        d = fi.read(0x4000)
                        if not d: break
                        f.write(d)
            if extract(tf.p,o,'GameCube ISO'): mv(tf.p,o + '/' + tbasename(i) + '.iso')
            tf.destroy()
            return
        case 'GameCube TGC ISO':
            db.try_custom()
            tf = TmpFile('.iso')
            with xopen(i,'rb') as fi:
                fi.seek(8)
                off = int.from_bytes(fi.read(4),'big')
                fi.seek(0x10)
                fst = int.from_bytes(fi.read(4),'big') - off
                fi.seek(0x1C)
                dol = int.from_bytes(fi.read(4),'big') - off
                fi.seek(off)
                with tf.open('wb') as f:
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
        case 'Switch NSP\0':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'PFS0')

            c = f.readu32()
            sts = f.readu32()
            f.padc(4)
            fs = []
            for _ in range(c):
                fs.append((f.readu64(),f.readu64(),f.readu32()))
                f.padc(4)
            so = f.pos

            for fe in fs:
                f.seek(so + fe[2])
                fn = f.read0s('utf-8')
                f.seek(so + sts + fe[0])
                writefile(o + '/' + fn,f.readc(fe[1]))

            f.close()
            if fs:
                extract2(o,o,'Switch Unpacked')
                return
        case 'Switch Unpacked\0':
            db.try_custom()
            from lib.file import File
            inf = [x for x in listdir(i) if x.lower().endswith('.cnmt.nca')]
            asrt(len(inf) == 1)
            inf = i + '/' + inf[0]

            f = File(inf,endian='<')
            nca = Nintendo(db).parse_nca(f)
        case 'Switch NCA\0':
            db.try_custom()
            from lib.crypto import decrypt
            from lib.file import File
            f = File(i,endian='<')
            nca = Nintendo(db).parse_nca(f)
            v = nca.version

            writefile(o + '/$header.dec',nca.data())
            for ix in range(4):
                sec = nca.section_entries[ix]
                if not sec.start_offset: continue
                off = sec.start_offset * 0x200
                f.seek(off)
                d = f.readc(sec.end_offset * 0x200 - off)
                fse = nca.fs_header_entries[ix]
                if nca.version <= 0: fse.values['enc_type'] = -1
                if fse.enc_type == 1: pass # decrypted
                elif fse.enc_type == 3: d = decrypt(d,'aes_ctr_be',nca.decrypted_keys[1],off >> 4,prefix=fse.aes_ctr_upper_iv,bits=0x40)
                else: raise NotImplementedError(f'encryption type {fse.enc_type}')
                if fse.fstype == 1: asrt(d[0x20:0x24] == b'PFS0',ix)
                writefile(f'{o}/{ix}.{("RomFS","PartitionFS")[fse.fstype]}',d)

            f.close()
            return
        case 'Switch NSP'|'Switch NCA'|'Switch XCI':
            import re

            st = {'Switch NSP':'pfs','Switch NCA':'nca','Switch XCI':'xci'}[t]
            for k in ('prod','dev'):
                bcd = ['hac2l','-t',st,'--disablekeywarns','-k',db.get(k+'keys'),'--titlekeys=' + dirname(db.get(k+'keys')) + '\\title.keys']
                _,e,_ = run(bcd + [i],print_try=False)
                bcd += ['--exefsdir=' + o + '\\ExeFS','--romfsdir=' + o + '\\RomFS','--outdir=' + o]
                if st == 'nca': bcd.append('--baseappfs=' + dirname(i))

                if ' MetaType=Patch ' in e and not ' MetaType=App ' in e:
                    pinf = re.search(r'ProgramId=([\dA-F]+), Version=0x([\dA-F]+),',e)
                    pid,pv = pinf[1],int(pinf[2],16)
                    pbf = []
                    for x in listdir(dirname(i)):
                        if x != basename(i) and pid in x and x.endswith('.nsp'):
                            try: v = int(re.search(r'v(\d+)(?:\b|_)(?!\.)',x)[1])
                            except: v = 0
                            if v < pv: pbf.append((v,dirname(i) + '\\' + x))
                    if not pbf: return 1
                    pbf.sort(key=lambda x:x[0])
                    bcd.append('--base' + st + '=' + pbf[0][1])

                if run(bcd + [i])[0] == 0xc0000005: raise ValueError('Access violation (0xc0000005/3221225477)')
                if listdir(o) and exists(o + '/ExeFS') and exists(o + '/RomFS') and listdir(o + '/ExeFS') and listdir(o + '/RomFS'): return
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
                copydir(o + '/Sc0',o + '/sce_sys',True)
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
            if not extract(i,o,'ISO'):
                if exists(o + '/PS3_GAME/USRDIR/EBOOT.BIN') and readfile(o + '/PS3_GAME/USRDIR/EBOOT.BIN',size=4) != b'SCE\0': return 1
                return
        case 'PSVita PKG':
            if exists(noext(i) + '.work.bin'): work = noext(i) + '.work.bin'
            elif exists(dirname(i) + '/work.bin'): work = dirname(i) + '/work.bin'
            else:
                ms = int.from_bytes(readfile(i,off=0x10,size=4),'big')
                if ms >= 0x140: return 1
                work = None

            if work:
                from lib.pyob import PyOBinX
                keys = PyOBinX.dl('keys',db)
                from lib.crypto import encrypt
                rif = readfile(work)
                keys.wait()
                zrif = encrypt(rif,'zrif_b64',keys['zrif_dict'])
                del keys

            run(['pkg2zip','-x',i] + ([zrif] if work else []),cwd=o)
            if exists(o + '/app') and listdir(o + '/app') and listdir(o + '/app/' + listdir(o + '/app')[0]):
                td = o + '\\tmp' + os.urandom(8).hex()
                mv(o + '/app',td)
                td += '\\' + listdir(td)[0]

                run(['psvpfsparser','-i',td,'-o',o,'-z',zrif])
                rmtree(dirname(td))

                if listdir(o): return
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
            xpd = readfile(xpt,'rt')
            if 'from cStringIO import StringIO' in xpd:
                writefile(xpt,xpd.replace(
                    'from cStringIO import StringIO','from io import BytesIO as StringIO').replace(
                    'from constants import','from .constants import').replace(
                    ' print ',' pass#').replace(
                    'assert data in ("CON ",','assert data.decode() in ("CON ",').replace(
                    "'\\x00'","b'\\0'").replace(
                    '"%s\\x00"',"b'%s\\0'").replace(
                    "data[:0x28].strip(b'\\0')","data[:0x28].strip(b'\\0').decode('utf-8')").replace(
                    "self.filename != ''","self.filename"),'w')

            if db.print_try: print('Trying with py360_stfs')
            import bin.py360.stfs as stfs # type: ignore
            stfs.xrange = range
            stfs.ord = lambda x: x[0] if isinstance(x,bytes) else (x if isinstance(x,int) else ord(x))
            stfs.os = os

            try: stfs.extract_all(['',i,o])
            except AssertionError: return 1
            if listdir(o): return
        case 'GD-ROM CUE+BIN':
            run(['buildgdi','-extract','-cue',i,'-output',o + '\\','-ip',o + '\\IP.BIN'])
            if listdir(o):
                from bin.sgkey import SGKeys
                if exists(o + '/IP.BIN') and SGKeys().get(o): return extract(o + '\\IP.BIN',o,'Encrypted GD-ROM')
                return
        case 'Nintendo TMD':
            db.try_custom()
            from lib.pyob import PyOBinX
            keys = PyOBinX.dl('keys',db)
            from lib.crypto import decrypt,encrypt,crc_hash
            if isdir(i): dr = i
            else: dr = dirname(i)
            ifs = [x.lower() for x in listdir(dr) if isfile(dr + '/' + x)]

            if 'tmd' in ifs: tmd = 'tmd'
            else: tmd = max([x for x in ifs if x.startswith('tmd.')],key=lambda x:int(x.split('.')[-1]))
            tmd = Nintendo(db).parse_tmd(dr + '/' + tmd)

            if tmd.signature.type & 0xFF == 1 and tmd.version == 0: cns = 'w'
            else: raise NotImplementedError(f'{tmd.signature.type:06X} {tmd.version}')

            db.set_temp_print(False)
            pids = list(range(len(keys.wait()['tmd']['p'])))
            sec = encrypt(10,'tmd_secret',keys['tmd']['s'])
            if cns == 'w': pids.remove(1);pids.insert(0,1)
            #elif cns == '3': pids.remove(0);pids.insert(0,0)
            tmd.contents.sort(key=lambda x:x.csize) # smallest first for faster key guessing
            for c in tmd.contents:
                fn = f'{c.cid:08X}'
                fi,fo = dr + '/' + fn,o + '/' + fn

                if c.type & 1:
                    inf,ouf = xopen(fi,'rb'),xopen(fo,'wb')
                    tid = crc_hash(sec + (tmd.title_id.to_bytes(8,'big').lstrip(b'\0') or b'\0'),'md5',bytes=True)
                    for ix in pids:
                        aes = decrypt(None,'aes_cbc',encrypt(keys['tmd']['p'][ix],'pbkdf2_sha1',tid,0x14,size=0x10),
                                                     c.index.to_bytes(2,'big') + bytes(14))
                        hsh = crc_hash(None,('sha1','sha256')[tmd.version])
                        inf.seek(0)
                        ol = 0
                        while ol < c.csize:
                            p = inf.read(1024**2)
                            if not p: break
                            d = aes.decrypt(p + bytes(-len(p) % 0x40))
                            ol += len(d)
                            if ol > c.csize: d = d[:c.csize - ol]
                            hsh.update(d)
                            ouf.write(d)

                        if hsh.digest() == c.sha:
                            if pids[0] != ix: pids.remove(ix);pids.insert(0,ix)
                            break
                    else: raise ValueError('No valid key found')
                    inf.close();ouf.close()
                elif getsize(fi) == c.csize: copy(fi,fo)
                else:
                    inf,ouf = xopen(fi,'rb'),xopen(fo,'wb')
                    ol = 0
                    while ol < c.csize:
                        p = inf.read(1024**2)
                        if not p: break
                        ol += len(p)
                        if ol > c.csize: p = p[:c.csize - ol]
                        ouf.write(p)
                    inf.close();ouf.close()

                od = readfile(fo,size=0x800)
                if cns == 'w':
                    if c.type == 2: mv(fo,o + '/CAFEDEAD.bin')
                    elif c.type & 0x8000:
                        mv(fo,f'{o}/shared_{fn}.arc')
                        extract(f'{o}/shared_{fn}.arc',o + '/shared','U8')
                    elif c.index == 0 and tmd.title_id == 0x0100000002: mv(fo,o + '/build_tag.bin')
                    elif c.index == 0: mv(fo,o + '/banner.bnr')
                    elif c.index == 1: mv(fo,o + '/launch.dol')
                    elif tmd.boot_index == c.index: mv(fo,o + '/boot.dol')
                    elif od[:4] == b'U\xAA8\x2D':
                        mv(fo,fo + '.arc')
                        extract(fo + '.arc',fo,'U8')
            db.reset_temp_print()
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
        case 'C64 LiBRary':
            run(['dirmaster','/e',i],cwd=o)
            if listdir(o): return
        case 'C64 Tape':
            td = TmpDir(path=o)
            tf = TmpFile('.exe',path=td.p)
            tf.link(db.get('tapclean'))
            if db.print_try: print('Trying with tapclean')
            run([tf.p,'-t',i,'-doprg'],print_try=False)
            tf.destroy()
            if exists(td + '/tcreport.txt') and exists(td + '/prg') and listdir(td + '/prg'):
                r = readfile(td + '/tcreport.txt','rt')
                for x in r.split('\n---------------------------------\n')[1:]:
                    x = x.split('\n')
                    asrt(x[0].startswith('Seq. no.: ') and x[1].startswith('File Type: '),x[0])
                    seq = int(x[0][10:])
                    ty = x[1][11:]
                    if ty == 'PAUSE': continue
                    asrt(x[3].startswith('LA: $'),seq)
                    dt = x[3].split()
                    if x[4].startswith('File Name: '):
                        rfn = x[4][11:]
                        fn = f' [{"".join(x if x.isalnum() else "_" for x in rfn)}]'
                    else: rfn = fn = ''

                    fn = f'{td}/prg/{seq:03d} ({dt[1][1:]}-{dt[3][1:]}){fn}.prg'
                    asrt(exists(fn),seq,err=FileNotFoundError)

                    rp = ""
                    dty = None
                    for l in x:
                        if l.startswith(' - File ID : REPEAT'): rp = "_REPEAT"
                        elif l.startswith(' - DATA FILE type : '): dty = l[20:]

                    nfn = f'{o}/{rfn}{"_" if rfn else ""}{seq:03d}{rp}.{C64TM.get(dty,C64TM.get(ty,ty))}'
                    mv(fn,nfn)
                td.destroy()
                if listdir(o): return
            td.destroy()
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

                lf = xopen(ld,'rb')
                if sum(lf.read(8)) == 0 and sum(lf.read(8)) != 0 and sum(lf.read(3)) == 0 and lf.read(1)[0] == 0xFF and sum(lf.read(0x8C)) == 0:
                    lf.seek(0xC0)
                    drv = lf.read(0x20).strip(b'\0')
                    if drv:
                        try:drv = id + '\\' + drv.decode('utf-8')
                        except:pass
                        else:
                            if exists(drv): drvs.append(drv)
                lf.close()

            if not drvs: return 1

            for f in drvs:
                tf = o + '\\' + basename(f) + '.dec'
                run(['chdecrypt',f,tf,key.hex().upper()])
                asrt(exists(tf),err=FileNotFoundError)
                od = tbasename(f) + '_ext'
                if t == 'C':
                    asrt(readfile(tf,size=4) == b'FATX',basename(tf))
                    mkdir(od)
                    extract(tf,od,'FATX')
                elif t == 'T':
                    chk = readfile(tf,off=0x1C,size=4) == b'\xC2\x33\x9F\x3D'
                    asrt(chk,basename(tf))
                    mkdir(od)
                    extract2(tf,od,'GameCube ISO')
                elif t == 'N':
                    tff = xopen(tf,'rb')
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
                    tff = xopen(tf,'rb')
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
            db.try_custom()
            from lib.file import File

            f = File(i)
            f._end = {b'RIFF':'<',b'FFIR':'>'}[f.read(4)]
            f.skip(4)
            asrt(f.read(4) == b'AMS!')
            cns = {}
            while True:
                cn = f.read(4)
                if not cn: break
                asrt(cn[:2] == b'cb' and cn[2:].isdigit())
                cns[int(cn[2:])] = f.read(f.readu32())
            asrt((len(cns)-1) == max(list(cns)))

            of = xopen(f'{o}/{tbasename(i)}.bin','wb')
            for ix in range(1,len(cns)): of.write(cns[ix])
            of.close()
            if cns: return
        case 'GBA ADS Video ROM'|'GBA ADS SFCD':
            db.try_custom()
            from lib.file import File

            f = File(i,endian='<')
            if t == 'GBA ADS Video ROM': f.seek(0xE38)
            aoff = f.pos
            asrt(f.read(4) == b'SFCD')

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
                    name += b.decode('utf-8')
                cp = f.pos + -(f.pos-aoff) % 4
                f.seek(off)
                writefile(o + '/' + name,f.readc(siz))
                f.seek(cp)
            if fsc: return
        case 'NES Remix ROM':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            f.skip(8)
            start = f.readu32()
            size = f.readu32() - start
            f.skip(0x10)
            name = f.read(0x10).strip(b'\0').decode('utf-8')

            f.seek(start)
            tag = f.read(3)
            if tag in {b'NES',b'UNI'}:
                if not name: name = tbasename(i)
                name += '.' + tag.decode().lower()
            elif (tag+f.read(13)) == b'\x01*NINTENDO-HVC*\x01':
                if not name: name = f.read(4).strip(b' \0').decode('utf-8')
                name += '.qd'
            else:
                if not name: name = tbasename(i)
                name += '.bin'
            f.seek(start)
            writefile(o + '/' + name,f.read(size))
            return
        case 'Famicom Disk Image':
            db.try_custom()
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
                    asrt(f.read(14) == b'*NINTENDO-HVC*')
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
                    writefile(name,f.read(size))
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
                writefile(tf.p,cik)
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
            writefile(tf.p,f'insert "{i}"\nextract *\nfree\nexit\n','w')
            run(['discimagemanager','-c',tf],cwd=o)
            tf.destroy()
            if listdir(o):
                from time import strptime,mktime

                for f in rldir(o,False):
                    if not exists(f): continue
                    if exists(f + '.inf'):
                        finf = readfile(f + '.inf')
                        if b'\n' in finf or b'\r' in finf: continue
                        try: finf = finf.decode('utf-8')
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
                            set_ftime(f,ft)
                return
        case 'C64 IMG':
            run(['c1541'],stdin=f'attach "{i}"\nextract\nquit\n',cwd=o)
            cd = dirname(db.get('c1541'))
            remove(cd + '/stderr.txt',cd + '/stdout.txt')
            if listdir(o): return

            if not extract(i,o,'DIET'):return # deark 

            return extract2(i,o,'C64 Tape')
        case 'Playdate Container': raise NotImplementedError
        case 'PlayStation APA IMG':
            tf = TmpFile('.tar',path=o)
            run(['pfs2tar','--backup',i,tf])
            if not exists(tf.p): return 1
            r = extract(tf.p,o,'TAR')
            tf.destroy()
            return r
        case 'PlayStation Boot Package':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            asrt(f.read(4) == b'\0PBP')
            f.skip(4)
            offs = [f.readu32() for _ in range(8)] + [f.size]
            fs = [(offs[x],offs[x+1]-offs[x]) for x in range(8)]

            f.seek(fs[0][0])
            writefile(o + '/PARAM.SFO',f.read(fs[0][1]))
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
            writefile(o + '/ICON0.PNG',f.read(fs[1][1]))
            if fs[2][1]:
                f.seek(fs[2][0])
                d = f.read(fs[2][1])
                writefile(o + '/ICON1.' + ('PNG' if d[:4] == b'\x89PNG' else 'PMF'),d)
            if fs[2][0] != fs[3][0]:
                f.seek(fs[3][0])
                writefile(o + '/PIC0.PNG',f.read(fs[3][1]))
            f.seek(fs[4][0])
            writefile(o + '/PIC' + ('T' if mini or ps else '') + '1.PNG',f.read(fs[4][1]))
            if mini or psp:
                f.seek(fs[5][0])
                writefile(o + '/SND0.AT3',f.read(fs[5][1]))
            f.seek(fs[6][0])
            writefile(o + '/DATA.PSP',f.read(fs[6][1]))
            f.seek(fs[7][0])
            writefile(o + '/DATA.PSAR',f.read(fs[7][1]))

            return
        case 'SimpleFlashFS':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            if f.read(13) != b'SimpleFlashFS':
                f.seek(0x800000)
                asrt(f.read(13) == b'SimpleFlashFS')
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

                writefile(o + '/' + fn,f.read(fs))
                f.seek(cp + ln)
            if listdir(o): return
        case 'Konami Python IMG':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='>')

            asrt(f.read(4) == b'\xDE\xAD\xBE\xEF')
            f.skip(2)
            fc = f.readu16()
            ss = f.readu16()
            f.skip(2)
            infs = f.readu16()
            writefile(o + '/$INFO.xml',f.read(infs-1))

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
                writefile(o + '/' + fe[1],f.read(fe[2]))
            if fs: return
        case 'StudyBox IMG':
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            asrt(f.read(4) == b'STBX')
            f.skip(f.readu32())

            c = 0
            while f:
                t = f.read(4).decode('latin1')
                s = f.readu32()
                if t == 'PAGE': ext = 'bin'
                elif t == 'AUDI':
                    ext = 'wav'
                    f.skip(4)
                    asrt(f.read(4) == b'RIFF')
                    f.skip(-4)
                    s -= 4
                else: raise NotImplementedError(t)

                writefile(o + f'/{t}{c:02d}.{ext}',f.read(s))
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

            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(4) == b'NES\x1A')

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
            if ines2 in {1,3}: v = 0
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
                    if (v in {1,1.1,1.2} and f8 != 1) or (v == 2 and f10&0xF0 != 7): inf.write('Designation: TLROM [128-512kb PRGROM]\n')
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
                elif mapr in {256,419}:
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
            elif v in {1.1,1.2}:
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
            if tr: writefile(o + '/trainer.prg',f.read(0x200))
            for ix in range(prgs):
                if ix == prgs - 1:
                    d = f.read(1024*16-6)
                    inf.write(f'NMI Vector: 0x{f.readu16():4X}\n')
                    inf.write(f'Reset Vector: 0x{f.readu16():4X}\n')
                    inf.write(f'IRQ Vector: 0x{f.readu16():4X}\n')
                else: d = f.read(1024*16)
                writefile(o + f'/PRG{ix}.prg',d)
            inf.close()

            for ix in range(chrs):
                d = f.read(1024*8)
                writefile(o + f'/CHR{ix}.chr',d)

                td = bytearray(256*128)
                for t in range(0x200):
                    to = t*16
                    tx = (t%0x20)*8
                    ty = (t//0x20)*8
                    for y in range(8):
                        b1,b2 = d[to+y],d[to+y+8]
                        for x in range(8): td[(ty+y)*256 + tx+x] = ((b1 >> (7-x)) & 1) | (((b2 >> (7-x)) & 1) << 1)
                writefile(o + f'/CHR{ix}.pgm',b'P5\n256 128\n3\n' + td)

            return
        case 'N64 Memory Pak':
            db.try_custom()
            from lib.file import File
            from lib.crypto import crc_hash
            f = File(i,endian='>')
            big = f.size >= 0x80000
            f.seek(0x100)

            pgs = []
            for _ in range(16 if big else 1):
                f.skip(2)
                pgs.extend([f.readu16() for _ in range(0x7F)])

            f.skip((16 if big else 1) * 0x100)
            fs = []
            for _ in range(0x10):
                gnr = f.read(6)
                sp = f.readu16()
                if not f.readu8() & 2:
                    f.skip(0x17)
                    continue
                try: gn = gnr.decode('ascii');asrt(gn.isprintable())
                except: gn = (gnr[:4].rstrip(b'\0') + gnr[4:].rstrip(b'\0')).hex().upper()
                gn = sub_path(gn,slash=True)

                ppd = f.readu8()
                ldrgcrc = f.readu16()

                ext = f.read(4).split(b'\0')[0].decode('n64mpak').strip()
                fn = sub_path(f.read(0x10).split(b'\0')[0].decode('n64mpak').strip() + ('.' if ext else '') + ext,slash=True)
                fn = f"{o}/{gn}/{fn}"
                f.back(0x20)
                rd = bytearray(f.read(0x20))
                rd[9:11] = b'\0\0'
                if crc_hash(rd,'crc16_opensafety_a') != ldrgcrc: ppd = 0

                pp = sp
                ps = 0
                while pp < len(pgs):
                    cp = pgs[pp];pp += 1
                    asrt(cp not in {0,2,3,4})
                    ps += 1
                    if cp == 1: break
                    pp = cp

                fs.append((fn,sp * 0x100,ps * 0x100 - ppd))

            for fe in fs:
                f.seek(fe[1])
                writefile(fe[0],f.read(fe[2]))
            return
        case 'Doctor V64 ROM':
            db.try_custom()
            import struct
            d = readfile(i)
            writefile(f'{o}/{tbasename(i)}.z64',struct.pack(f'>{len(d)//2}H',*struct.unpack(f'<{len(d)//2}H',d)))
            return

        case 'Ridge Racer V A':
            tf = dirname(i) + '\\rrv3vera.ic002'
            if os.path.exists(tf): remove(tf)
            symlink(db.get('rrv3va'),tf)

            cfp = dirname(db.get('rrvatool')) + '/RidgeRacerVArchiveTool.exe.config'
            d = readfile(cfp,'r').replace('<value>True</value>','<value>False</value>')
            writefile(cfp,d.replace('<setting name="ACV3Achecked" serializeAs="String">\n                <value>False</value>','<setting name="ACV3Achecked" serializeAs="String">\n                <value>True</value>'),'w')
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
            db.try_custom()
            from lib.file import File

            f = File(i,endian='<')
            f.seek(0x14)
            c = f.readu32()
            f.seek(0x20)
            fs = []
            for _ in range(c):
                fs.append((f.read(0x10).rstrip(b'\0').decode('utf-8'),f.readu32(),f.readu32() * 0x200))
                f.skip(8)
            for fe in fs:
                f.seek(fe[2])
                writefile(o + '/' + fe[0],f.read(fe[1]))

            lo = max(fe[2] + fe[1] for fe in fs)
            xo = lo + (-lo % 0x200)
            if not xo >= f._size:
                f.seek(xo)
                writefile(o + '/_extra.bin',f.read(f._size - xo - 0x200 - 0xB8B200 - 0x14C))

            f.close()
            if fs: return
        case 'Monkey Ball A':
            for d in ('CHUNK','DTPK','SPSD'):
                scn = f'monkey ball {d} extract'
                if d == 'CHUNK':
                    scp = db.get(scn)
                    scc = readfile(scp,'r')
                    if '\nnext A\n' in scc: writefile(scp,scc.replace('\nnext A\n','\nmath A + 1\n'),'w')

                mkdir(o + '\\' + d)
                if quickbms(scn,ouf=o + '\\' + d): break
            else: return
        case 'Initial D 3 Export A':
            for d in ('NMZIP','TEX','SPSD'):
                mkdir(o + '\\' + d)
                if quickbms(f'initd3e {d} extract',ouf=o + '\\' + d): break
            else: return
        case 'Virtua Striker 3 A':
            db.try_custom()
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
                writefile(o + '/' + fe[0],f.read(fe[2]))

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
        case 'Mario Kart 64 N64 ROM'|'F-Zero X N64 ROM'|'Wonder Project J2 N64 ROM':
            f = xopen(i,'rb')
            f.seek(0x3B)
            tg = f.read(4).decode('latin1')
            f.close()
            rt = t[:-8]

            if rt == 'Mario Kart 64' and tg == 'NKTE': scr = 'spaghettikart_yaml'
            elif rt == 'F-Zero X' and tg in {'CFZE','CFZJ'}: scr = 'fzerox_yaml'
            elif rt == 'Wonder Project J2' and tg ==  'NJ2J': scr = 'wonder_torch_yaml'
            else: raise NotImplementedError(t + ': ' + tg)

            import zipfile
            run(['torch','o2r','-s',db.get(scr),'-d',o,i])
            if len(listdir(o)) == 2:
                remove(o + '/torch.hash.yml')
                asrt(listdir(o) == ['generic.o2r'])
                zipfile.ZipFile(o + '/generic.o2r').extractall(o)
                remove(o + '/generic.o2r')
                return
        case 'Pilotwings 64 N64 ROM'|'Dr. Mario 64 N64 ROM'|'Wave Race 64 N64 ROM'|'Pokemon Puzzle League N64 ROM'|'Super Smash Bros. N64 ROM'|\
             'Gex 64: Enter The Gecko N64 ROM'|'Snowboard Kids 2 N64 ROM'|'Glover N64 ROM': # 'Wonder Project J2 N64 ROM'
            MP = {
                'Pilotwings 64':{
                    0:'pilotwings64decomp_yaml',
                    1:'config/{cc}/pilotwings64',
                    'NPWE':'us',
                },
                'Dr. Mario 64':{
                    0:'drmario64_yaml',
                    1:'config/{cc}/drmario64',
                    'NN6E':'us',
                    'NN6G':'gw',
                    '\0\0\0\0':'cn',
                },
                'Wave Race 64':{
                    0:'wave_race_64_yaml',
                    1:'waverace64',
                    2:{'linker_scripts'},
                    'NWRE:2.0':'us.rev1',
                },
                'Pokemon Puzzle League':{
                    0:'puzzleleague64_yaml',
                    1:'config/{cc}/puzzleleague64',
                    3:{'tools'},
                    'NPNE':'usa',
                    'NPNF':'fra',
                    'NPND':'ger',
                    'NPNP':'eur',
                },
                'Super Smash Bros.':{
                    0:'ssb_decomp_re_yaml',
                    1:'smashbrothers',
                    2:{'symbols'},
                    'NALJ':'jp',
                    'NALE':'us',
                },
                'Gex 64: Enter The Gecko':{
                    0:'gex64decomp_yaml',
                    1:'gexenterthegecko',
                    2:{'symbol_addrs.txt'},
                    'NX2E':'us',
                },
                'Snowboard Kids 2':{
                    0:'snowboardkids2_decomp_yaml',
                    1:'snowboardkids2',
                    2:{'symbol_addrs.txt','linker_scripts'},
                    'NK2E':'us',
                },
                'Glover':{
                    0:'glover_decomp_yaml',
                    1:'glover',
                    2:{'symbol_addrs.txt','reloc_addrs.txt'},
                    'NGVE':'us',
                },
                'Wonder Project J2':{
                    0:'wonder_splat_yaml',
                    1:'wonderprojectj2',
                    2:{'buggy_syms.txt','libultra_symbols.txt','symbol_addrs.txt','hardware_syms.txt'},
                    'NJ2J':'jp',
                },
            }

            f = xopen(i,'rb')
            f.seek(0x3B)
            tg = f.read(4).decode('latin1')
            v = f.read(1)[0]
            if v != 0: tg += f':{(v & 0xF) + 1}.{v >> 4}'
            f.close()
            rt = t[:-8]

            if rt in MP and tg in MP[rt]:
                bps = db.get(MP[rt][0])
                scr = MP[rt][1].format(cc=MP[rt][tg]) + f'.{MP[rt][tg]}.yaml'
            else: raise NotImplementedError(t + ': ' + tg)

            if db.print_try: print(f'Trying with splat + {MP[rt][0]}/{scr}')
            import splat.scripts.split as splat # type: ignore

            class Stub:
                def __init__(self,*args,**kwargs):pass
                def __call__(self,*args,**kwargs): return Stub()
                def __getattribute__(self,name): return Stub()
                def __setattr__(self,name,value): pass
                def __iter__(self): return self
                def __next__(self): raise StopIteration

            idat = readfile(i)
            if rt == 'Dr. Mario 64':
                import io
                ob = io.BytesIO()
                ob.close = Stub()
                class ArgStub:
                    def __init__(self,*args,**kwargs):pass
                    def add_argument(self,*args,**kwargs):pass
                    def parse_args(self):
                        obj = ArgStub()
                        obj.in_rom = i
                        obj.out_rom = '\0'
                        obj.segments = f'compress_segments.{MP[rt][tg]}.csv'
                        obj.version = MP[rt][tg]
                        return obj
                class PathStub:
                    def __init__(self):pass
                    def open(self,mode):
                        asrt(mode == 'wb')
                        return ob

                p = os.getcwd()
                os.chdir(bps)
                sys.path.append(bps)
                sys.modules['crunch64'] = Stub()
                import rom_decompressor # type: ignore
                rom_decompressor.argparse.ArgumentParser = ArgStub
                rom_decompressor.__Path = rom_decompressor.Path
                rom_decompressor.print = Stub()
                rom_decompressor.Path = lambda x: PathStub() if x == '\0' else rom_decompressor.__Path(x)

                rom_decompressor.romDecompressorMain()
                del rom_decompressor
                sys.path.remove(bps)
                os.chdir(p)
                sys.modules.pop('crunch64')
                ob.seek(0)
                idat = ob.getvalue()
                del ob
                asrt(idat)

            class StubProg:
                def __init__(self,lst): self.__lst = lst
                def __iter__(self): return self.__lst.__iter__()
                set_description = Stub()

            class SplatErr(Exception):pass
            def log_error(*args,**kargs): raise SplatErr(*args,**kargs)
            splat.log.error = log_error
            splat.log.write = Stub()
            splat.log.parsing_error_preamble = lambda p,ln,l: log_error(f'error reading {p}, line {ln+1}:\n\t{l}')
            splat.log.output_file = Stub()
            splat.log.newline = False
            splat.progress_bar.get_progress_bar = lambda i:StubProg(i)
            splat.statistics = Stub()
            splat.read_target_binary = lambda: idat

            if scr.startswith('config/'):
                copydir(bps + '/' + dirname(scr),o + '/' + dirname(scr))
                bbp = scr.split('/')[0]
                for x in listdir(bps + '/' + bbp):
                    p = f'{bps}/{bbp}/{x}'
                    if isfile(p): copy(p,f'{o}/{bbp}/{x}')
            else: copy(bps + '/' + scr,o + '/' + scr)
            if 2 in MP[rt]:
                for x in MP[rt][2]: copy(f'{bps}/{x}',f'{o}/{x}')
            old = len(listdir(o))
            if 3 in MP[rt]:
                for x in MP[rt][3]: copy(f'{bps}/{x}',f'{o}/{x}')
            splat.main([splat.Path(o + '/' + scr)],["all"],verbose=False,use_cache=False)
            if 3 in MP[rt]: remove(*[f'{o}/{x}' for x in MP[rt][3]])

            if len(listdir(o)) > old:
                if rt == 'Wave Race 64':
                    import re,ast
                    from lib.file import decompress

                    offs = ast.literal_eval(re.search(r'target_mio0_offsets = (\[[\s\dA-Fa-fx,]+\])',readfile(bps + '/mio0_extract.py','r'))[1])
                    f = xopen(i,'rb')
                    for of in offs:
                        f.seek(of)
                        if f.read(4) == b'MIO0':
                            f.seek(of)
                            writefile(f'{o}/mio0/decompressed_{of:08X}.bin',decompress(f.read(),'mio0'))
                    f.close()
                elif rt == 'Super Smash Bros.':
                    from lib.file import File,decompress
                    ass = o + '/assets/' + MP[rt][tg] + '/'
                    f = File(ass + 'relocData.bin',endian='>')

                    fs = []
                    while True:
                        off = f.readu32()
                        fs.append((off >> 31,off & 0x7FFFFFFF,f.readu16(),f.readu16(),f.readu16(),f.readu16()))
                        if sum(fs[-1]) == off: break
                    do = f.pos

                    cd = '\n'.join([f'{fe[0]}, {fe[1]:#08x}, {fe[2]:#06x}, {fe[3]:#06x}, {fe[4]:#06x}, {fe[5]:#06x}' for fe in fs])
                    writefile(ass + 'relocData.csv','isVpk0, dataOffset, relocInternOffset, compressedSize, relocExternOffset, decompressedSize\n' + cd,'wt')

                    ass += 'relocData/'
                    for ix,fe in enumerate(fs[:-1]):
                        f.seek(do + fe[1])
                        d = f.readc(fs[ix+1][1] - fe[1])
                        if fe[0]:
                            writefile(f'{ass}{ix}.vpk0',d)
                            writefile(f'{ass}{ix}.vpk0.bin',decompress(d,'vpk0'))
                        else: writefile(f'{ass}{ix}.bin',d)
                    f.close()
                return
        case 'Final Fantasy X 2 ISO':
            zip7(i,o + '\\$ISO','ISO')
            db.try_custom()
            from lib.file import File
            f = File(i,endian='<')

            f.seek(0x8C000)
            fs = []
            while f:
                of = f.readu32()
                if not of: break
                if of & 0x7FFFFF: fs.append(((of & 0x3FFFFF) * 0x800,(of >> 23) * 4))
            fs = sorted(fs,key=lambda x:x[0])
            fs.append((f.size,))

            for ix in range(len(fs)-1):
                if not fs[ix+1][0] - fs[ix][0]: continue
                f.seek(fs[ix][0])
                d = f.read((fs[ix+1][0] - fs[ix][0]) - fs[ix][1])
                if d[:4] == b'VS\0\0': ext = 'vs'
                elif d[6:9] in {b'BGM',b'EV0',b'MAP'}: ext = d[6:9].decode('ascii').lower()
                else: ext = guess_ext_ps2(d)
                writefile(o + f'/{ix:04d}.{ext}',d)

            f.close()
            if fs: return

    return 1

@namespace(include=['NCA','parse_nca','AmiiboRaw','amiibo_raw_decrypt','parse_tmd','parse_tmd_tik'])
def _Nintendo(db):
    from lib.file import File,FileStruct
    from lib.crypto import decrypt,crc_hash

    class AmiiboId(FileStruct):
        game_char_id:'u16'
        char_variant:'u8'
        figure_type:'u8'
        model_num:'u16'
        series:'u8'
        unk1:'u8'
    class AmiiboRaw(FileStruct):
        _ENDIAN = '>'
        mf_1:bytes = 3
        chk_1:bytes = 1
        mf_2:bytes = 4
        chk_2:bytes = 1
        internal:'u8'
        static_lock_bytes:bytes = 2
        capability_container:bytes = 4
        unk1:bytes = 1
        write_counter:'u16'
        pad2:'padding' = 1
        enc1:bytes = 0x20
        tag_hmac:bytes = 0x20
        amiibo_id:AmiiboId
        unk2:bytes = 4
        unk_hash:bytes = 0x20
        data_hmac:bytes = 0x20
        enc2:bytes = 0x114
        enc3:bytes = 0x54
        dyn_lock_bytes:bytes = 3
        rfui:'u8'
        cfg:bytes = 8
    class AmiiboKey(FileStruct):
        hmac_key:bytes = 0x10
        phrase:bytes = 14
        pad:'padding' = 1
        seed_size:'u8'
        seed:bytes = 0x10
        xor_pad:bytes = 0x20

    def amiibo_raw2base(raw:AmiiboRaw):
        return raw.data('write_counter') + bytes(14) + raw.data()[:8]*2 + raw.data('unk_hash')
    def amiibo_derive_key(key:AmiiboKey,base:bytes):
        seed = key.phrase + base[:0x10 - key.seed_size] + key.seed[:key.seed_size] + base[0x10:0x20] + decrypt(base[0x20:0x40],'xor',key.xor_pad)
        r = crc_hash(seed,'ctr_drbg_hmac_sha256',key=key.hmac_key,seed_size=480,size=0x30)
        return r[:0x10],r[0x10:0x20],r[0x20:0x30]
    def amiibo_raw_decrypt(raw:AmiiboRaw,key:AmiiboKey=None):
        if key is None:
            key = AmiiboKey(readfile(db.get('amiibo_retail_key'),size=0x50))
        key,iv,_ = amiibo_derive_key(key,amiibo_raw2base(raw))
        return decrypt(raw.enc1 + raw.enc2 + raw.enc3,'aes_ctr',key,iv)

    def parse_tmd_sig(d:bytes):
        f = File(d,endian='>')
        r = Empty()
        r.type = f.readu32()
        match r.type:
            case 0x010000|0x010003: d,p = 0x200,0x3C
            case 0x010001|0x010004: d,p = 0x100,0x3C
            case 0x010002|0x010005: d,p = 0x3C,0x40
            case _: raise Exception(f'Unknown signature type: {r.type:06X}')
        r.value = f.readc(d)
        r.padding = f.readc(p)
        return r
    def parse_tmd_cert(d:bytes):
        f = File(d,endian='>')
        r = Empty()
        r.signature = parse_tmd_sig(f)
        r.issuer = f.readc(0x40)
        r.type = f.readu32()
        r.name = f.readc(0x40)
        r.date = f.readu32('<')
        r.modulus = f.readc((0x200,0x100,0x3C)[r.type])
        if r.type in {0,1}: r.exponent = f.readu32()
        r.padding = f.readc((0x34,0x34,0x3C)[r.type])
        return r
    class TMDInfo(FileStruct):
        _ENDIAN = '>'
        cid:'u16'
        ccc:'u16'
        sha256:bytes = 0x20
    def parse_tmd_content(d:bytes,version:int):
        f = File(d,endian='>')
        r = Empty()
        r.cid = f.readu32()
        r.index = f.readu16()
        r.type = f.readu16()
        r.csize = f.readu64()
        r.sha = f.readc((0x14,0x20)[version])
        return r
    def parse_tmd(d:bytes):
        f = File(d,endian='>')
        r = Empty()

        r.signature = parse_tmd_sig(f)
        r.issuer = f.readc(0x40)
        r.version = f.readu8()
        r.ca_crl_version = f.readu8()
        r.signed_crl_version = f.readu8()
        r.is_vwii = f.readbool()
        r.system_version = f.readu64()
        r.title_id = f.readu64()
        r.type = f.readu32()
        r.group_id = f.readu16()

        if r.version == 1:
            r.save_data_size = f.readu32('<')
            r.srl_private_size = f.readu32('<')
            r.reserved1 = f.read(4)
            r.srl_flag = f.readu8()
            r.reserved2 = f.read(0x31)
        else:
            r.zero1 = f.read(2)
            r.region = f.readu16()
            r.ratings = f.readc(0x10)
            r.reserved1 = f.read(12)
            r.ipc_mask = f.readc(12)
            r.reserved2 = f.read(0x12)

        r.access_rights = f.readu32()
        r.title_version = f.readu16()
        r.content_count = f.readu16()
        r.boot_index = f.readu16()
        r.minor_version = f.readu16()

        if r.version == 1:
            r.sha256 = f.readc(0x20)
            r.content_info = [TMDInfo(f) for _ in range(0x40)]
        r.contents = [parse_tmd_content(f,r.version) for _ in range(r.content_count)]
        r.certificates = [parse_tmd_cert(f) for _ in range(2)]
        return r
    def parse_tmd_tik(d:bytes):
        f = File(d,endian='>')
        r = Empty()

        r.signature = parse_tmd_sig(f)
        r.issuer = f.readc(0x40)
        r.ecdhdata = f.readc(0x3C)
        r.version = f.readu8()
        r.ca_crl_version = f.readu8()
        r.signed_crl_version = f.readu8()
        r.title_key = f.readc(0x10)
        r.reserved1 = f.read(1)
        r.ticked_id = f.readu64()
        r.console_id = f.readu32()
        r.title_id = f.readu64()
        r.reserved2 = f.read(2)
        r.title_version = f.readu16()
        r.permitted_titles_mask = f.readu32()
        r.permit_mask = f.readu32()
        r.export_allowed = f.readu8()
        r.ckey_index = f.readu8()
        r.reserved3 = f.read(0x2A)
        r.eshop_acc_id = f.readu32()
        r.reserved4 = f.read(1)
        r.audit = f.readu8()
        r.content_access_permissions = f.readc(0x40)
        r.reserved5 = f.read(2)
        r.limits = f.readc(0x40)

        if r.version == 1:
            r.content_index_size = f.peek('u32',poffset=4)
            r.content_index = f.readc(r.content_index_size)
        r.certificates = [parse_tmd_cert(f) for _ in range(2)]
        return r

    _NXPKEYS = None
    _NXDKEYS = None
    def get_nxkeys(dev=False):
        nonlocal _NXPKEYS,_NXDKEYS
        if dev:
            if _NXDKEYS is None: 
                k = db.get('devkeys')
                if k: _NXDKEYS = {x.split('=')[0].strip().lower():bytes.fromhex(x.split('=')[1].strip()) for x in readfile(k).split('\n') if x.strip()}
                else: _NXDKEYS = {}
            return _NXDKEYS
        if _NXPKEYS is None: 
            k = db.get('prodkeys')
            if k: _NXPKEYS = {x.split('=')[0].strip().lower():bytes.fromhex(x.split('=')[1].strip()) for x in readfile(k,'rt').split('\n') if x.strip()}
            else: _NXPKEYS = {}
        return _NXPKEYS

    CRYPTO_TYPES = ('application','ocean','system')

    class NCASectionEntry(FileStruct):
        start_offset:'u32'
        end_offset:'u32'
        padding:'padding' = 8
    class NCAPatchInfo(FileStruct):
        indirect_offset:'s64'
        indirect_size:'s64'
        indirect_header_offset:'s64'
        indirect_header_size:'s64'
        aes_ctr_ex_offset:'s64'
        aes_ctr_ex_size:'s64'
        aes_ctr_ex_header_offset:'s64'
        aes_ctr_ex_header_size:'s64'
    class NCASparseInfo(FileStruct):
        bucket_offset:'s64'
        bucket_size:'s64'
        physical_offset:'s64'
        generation:'u16'
        padding:'padding' = 6
    class NCAFSHeaderEntry(FileStruct):
        version:'u16'
        fstype:'u8'
        hash_type:'u8'
        enc_type:'u8'
        meta_hash_type:'u8'
        padding1:'padding' = 2
        hash_data:bytes = 0x98
        patch_info:NCAPatchInfo
        aes_ctr_upper_iv:bytes = 8
        sparse_info:NCASparseInfo
        compression_info_bucket_offset:'s64'
        compression_info_bucket_size:'s64'
        compression_info_padding:'padding' = 8
        meta_hash_data_info_offset:'s64'
        meta_hash_data_info_size:'s64'
        meta_hash_data_info_hash:bytes = 0x20
        padding2:'padding' = 0x30        
    class NCA(FileStruct):
        fixed_key_sig:bytes = 0x100
        npdm_key_sig:bytes = 0x100
        magic:bytes = 4
        distribution:'u8'
        content_type:'u8'
        crypto_type:'u8'
        kaek_ind:'u8'
        nca_size:'u64'
        title_id:'u64'
        padding0:'padding' = 4
        sdk_version:'u32'
        crypto_type2:'u8'
        fixed_key_generation:'u8'
        padding1:'padding' = 14
        rights_id:bytes = 0x10
        section_entries:list[NCASectionEntry] = 4
        section_hashes:bytes = 0x20*4
        encrypted_keys:bytes = 0x10*5
        padding2:'padding' = 0xB0
        fs_header_entries:list[NCAFSHeaderEntry] = 4

    def chknca(d:bytes): return d[0x200:0x204] in {b'NCA0',b'NCA2',b'NCA3'} and not sum(d[0x350:0x400])
    def parse_nca(d:bytes,title_key:bytes=None) -> NCA:
        pkeys,dkeys = get_nxkeys(),get_nxkeys(True)
        if isinstance(d,File):
            f = d
            d = f.read(0xC00)
        else: f = None
        h = d[:0xC00]
        asrt(len(h) in {0xC00,0xA00})
        enc = not chknca(d)

        dev = False
        if enc:
            asrt('header_key' in pkeys and len(pkeys['header_key']) == 0x20)
            dh = decrypt(h[:0x400],'aes_xts_sec_be',pkeys['header_key'],sector_size=0x200)
            if not chknca(dh):
                if not dkeys: return
                dev = True
                asrt('header_key' in dkeys and len(dkeys['header_key']) == 0x20)
                dh = decrypt(h[:0x400],'aes_xts_sec_be',dkeys['header_key'],sector_size=0x200)
                if not chknca(dh): return
            tkeys = dkeys if dev else pkeys
        else:
            tkeys = pkeys
            dh = h

        nca = NCA(dh + (bytes(len(h) - 0x400) if enc else b''))
        ct = max(nca.crypto_type,nca.crypto_type2)
        if ct: ct -= 1
        kaek = tkeys[f'key_area_key_{CRYPTO_TYPES[nca.kaek_ind]}_{ct:02x}']
        ekey = nca.encrypted_keys
        dkey = [None]*4 # XTS64, CTR32, CTREx32, CTRHW32
        v = nca.magic[3] - 0x30

        if v == 3:
            if enc: dh = decrypt(h,'aes_xts_sec_be',tkeys['header_key'],sector_size=0x200)
        elif v == 2:
            if enc:
                dh = [dh]
                for ix in range(4):
                    th = h[0x400 + ix*0x200:0x600 + ix*0x200]
                    if sum(th[0x148:0x200]): dh.append(decrypt(th,'aes_xts_sec_be',tkeys['header_key'],sector_size=0x200))
                    else: dh.append(th)
                dh = b''.join(dh)
        elif v == 0:
            if not 'beta_nca0_modulus' in pkeys or not 'beta_nca0_exponent' in pkeys or not 'beta_nca0_label_hash' in pkeys:
                import ast,re
                s = db.c.get('https://raw.githubusercontent.com/SciresM/hactool/refs/heads/master/pki.c').text
                for vn,vs in (('modulus',0x100),('exponent',0x100),('label_hash',0x20)):
                    pkeys['beta_nca0_' + vn] = bytes(ast.literal_eval('[' + re.search(rf' unsigned const beta_nca0_{vn}\[0x{vs:x}\] = ' + r'\{([^\}]+)\};',s)[1] + ']'))
                pkd = '\n'.join(f'{k} = {v.hex()}' for k,v in pkeys.items())
                writefile(db.get('prodkeys'),pkd,'wt')

            pdkey = decrypt(ekey,'rsa2048_oeap_hash',pkeys['beta_nca0_modulus'],pkeys['beta_nca0_exponent'],label_hash=pkeys['beta_nca0_label_hash'])
            if pdkey is None:
                if crc_hash(ekey[:0x20],'sha256') == 0x9abbd2118600219d7adc5b4395f84efdff6b25ef9f968528189e76b092f06acb:
                    dkey[0] = ekey[:0x20]
                else: dkey[0] = decrypt(ekey[:0x20],'aes_ecb',kaek)
            else:
                asrt(len(pdkey) >= 0x20)
                dkey[0] = pdkey[:0x20]
                v = -1

            if enc:
                dh = [dh]
                for ix in range(4):
                    off = int.from_bytes(dh[0][0x240 + 0x10*ix:0x240 + 0x10*ix + 4],'little')
                    if off:
                        asrt(off > 1)
                        if f:
                            f.seek(off * 0x200)
                            th = f.read(0x200)
                        else: th = d[off * 0x200:off * 0x200 + 0x200]
                        asrt(len(th) == 0x200)
                        dh.append(decrypt(th,'aes_xts_sec_be',dkey[0],off - 2,sector_size=0x200))
                    else: dh.append(bytes(0x200))
                dh = b''.join(dh)
        else: raise Exception(f'Unknown NCA version: {v}')

        nca = NCA(dh)
        if not sum(nca.rights_id):
            if v > 0:
                tdkey = decrypt(ekey,'aes_ecb',kaek)
                dkey = tdkey[:0x20],tdkey[0x20:0x30],tdkey[0x30:0x40],tdkey[0x40:0x50]
        else:
            tdkey = decrypt(title_key,'aes_ecb',tkeys[f'titlekek_{ct:02X}'])
            dkey = tdkey[:0x20],tdkey[0x20:0x30],tdkey[0x30:0x40],tdkey[0x40:0x50]
        nca.values['decrypted_keys'] = dkey
        nca.values['decrypted'] = not enc
        nca.values['dev'] = dev
        nca.values['version'] = v
        return nca

    return locals()
