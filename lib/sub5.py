from .main import *

def extract5(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def msdos(cmd,mscmd=[],tmpi=False,tmpic=False,inf=i,**kwargs):
        if tmpi:
            mkdir(o)
            tn = ('TP' + os.urandom(2).hex() + extname(inf) if not tmpic else basename(inf))
            tf = o + '/' + tn
            symlink(inf,tf)

        if db.print_try: print('Trying with',cmd[0])
        run(['msdos'] + mscmd + [db.get(cmd[0])] + [(tn if tmpi and x == inf else x) for x in cmd[1:]],print_try=False,**kwargs)

        if tmpi: remove(tf)

        if listdir(o): return
        return 1
    def dosbox(cmd:list,inf=i,oup=o,print_try=True,nowin=True,max=True,custs:str=None,tmpi=True,xcmds=[]):
        scr = cmd[0]
        s = db.get(scr)
        if not exists(s): s = custs

        mkdir(oup)
        oinf = inf
        if tmpi:
            td = TmpDir()
            inf = td + '\\TMP' + extname(inf)
            symlink(oinf,inf)

        if print_try and db.print_try: print('Trying with',scr)
        p = subprocess.Popen([db.get('dosbox'),'-nolog','-nopromptfolder','-savedir','NUL','-defaultconf','-fastlaunch','-nogui',('-silent' if nowin else ''),
             '-c','MOUNT I "' + dirname(inf) + '"','-c','MOUNT C "' + dirname(custs or s) + '"','-c','MOUNT O "' + oup + '"','-c','O:'] + xcmds + [
             '-c',subprocess.list2cmdline(['C:\\' + basename(s)] + [('I:\\' + basename(inf) if x == oinf else x) for x in cmd[1:]]) + (' > _OUT.TXT' if nowin else '')] + (sum([['-set',f'{x}={DOSMAX[x]}'] for x in DOSMAX],[]) if max else []),stdout=-3,stderr=-2)

        while not exists(oup + '/_OUT.TXT'): sleep(0.1)
        while True:
            try: open(oup + '/_OUT.TXT','ab').close()
            except PermissionError: sleep(0.1)
            else: break

        for _ in range(10):
            if getsize(oup + '/_OUT.TXT') > 0: break
            sleep(0.1)

        while True:
            r = open(oup + '/_OUT.TXT','rb').read()
            if len(r) == getsize(oup + '/_OUT.TXT'):
                r = r.decode('utf-8')
                break
            sleep(0.1)
        while True:
            try: remove(oup + '/_OUT.TXT')
            except PermissionError: sleep(0.1)
            else: break
        p.kill()
        if tmpi: td.destroy()

        return r

    match t:
        case 'qbp'|'TANGELO'|'CSC'|'NLZM'|'GRZipII'|'BALZ'|'SR3'|'SQUID'|'CRUSH (I.M.)'|'LZPX'|'LZPXJ'|'THOR'|'ULZ'|'LZPM':
            # merge some small compressors
            of = o + '/' + tbasename(i)
            run([t.split('(')[0].strip().lower(),'d',i,of])
            if exists(of) and getsize(of): return
        case 'ZCM':
            run(['zcm','x','-t0',i,o],timeout=300)
            if exists('master.tmp'): remove('master.tmp')
            if listdir(o): return
        case 'BCM':
            of = o + '/' + tbasename(i)
            run(['bcm','-d','-f',i,of])
            if exists(of) and getsize(of): return
        case 'RAZOR':
            run(['rz','-y','-o',o,'x',i,'*'])
            if listdir(o): return
        case 'NanoZip':
            run(['nz','x','-o' + o,i,'*'])
            if listdir(o): return
        case 'bsc'|'bsc-m03':
            of = o + '/' + tbasename(i)
            run([t,'d',i,of])
            if exists(of) and getsize(of): return
        case 'LZHAM':
            of = o + '/' + tbasename(i)
            run(['lzham','-c','-u','d',i,of])
            if exists(of) and getsize(of): return
        case 'YBS':
            YBSR = re.compile(r': Error opening ([^\n]+)')
            if db.print_try: print('Trying with ybs')
            while True:
                _,_,r = run(['ybs','-d','-y',i],print_try=False,cwd=o)
                fs = YBSR.findall(r)
                if not fs: break
                for f in fs: mkdir(o + '/' + dirname(f))
            if listdir(o): return
        case 'CSArc':
            run(['csarc','x','-t8','-o',o,i])
            if listdir(o): return
        case 'RK':
            run(['rk','-x','-y','-O','-D' + o,i])
            if listdir(o): return
        case 'GRZip':
            run(['grzip','e',i],cwd=o)
            if listdir(o): return
        case 'BOA Constrictor':
            dosbox(['boa','-x',i])
            if listdir(o): return
        case 'Flashzip':
            run(['flashzip','x','-t0',i,o])
            if listdir(o): return
        case 'Dark':
            run(['dark','u',i],cwd=o)
            if listdir(o): return
        case 'SBC':
            run(['sbc','x','-hn','-y','-t' + o,i])
            if listdir(o): return
        case 'SZIP':
            of = o + '/' + tbasename(i)
            run(['szip','-d',i,of])
            if exists(of) and getsize(of): return
        case 'Zzip':
            run(['zzip','x','-q',i],cwd=o)
            if listdir(o): return
        case 'Squeez':
            f = open(i,'rb')
            if f.read(2) == b'MZ':
                for of in (0x19600,0x1ce00,0x55c00,0x1c400,0x20200,0x65a00,0x19400,0x1ca00,0x55000):
                    f.seek(of)
                    if f.read(5) == b'SCSFX':break
                else:
                    f.close()
                    return 1

                f.seek(9,1)
                f.seek(int.from_bytes(f.read(4),'little'),1)
                f.seek(0x2C,1)
                for _ in range(3): f.seek(int.from_bytes(f.read(4),'little')*2,1)
                f.seek(7,1)
                assert f.read(5) == b'-sqx-'
                f.seek(-12,1)
            else: f.seek(-2,1)

            tf = o + '/tmp' + os.urandom(8).hex() + '.exe'
            t = open(tf,'wb')

            t.write(open(db.get('sqx'),'rb').read())
            # SCSFX
            import zlib,base64
            t.write(zlib.decompress(base64.b85decode('c-oy-&2Aev5LVDjp+ff_nE;X!G?uMDOHTR&N0u9-i5+;;ra;sKwM$8?cgZcum7=~;Z@u?WpfAuz=_~Xb?yj_U5}>F7+uWJq@SB-$h72ab`H!`~f4^7zv{tLlKdaUL`Qy(<{cR*{Xk_Z7RzEfBjrtM$icQrrmUcy-ZzJybPH}b9sCV)IQa9>7{GV_YinvklV|^{sn1_P#7=i%=tw6XeZPbUfp1yO2hptgS#@9tlEi~hEok1`n^>Y!!a*SoC(`nRCD!v=_r-9=t;wEAU0RRX|>uN2`#z-gFLdL?fjdUycW2w;zqESm264W;<p;)AqU?PVA6>FJHv3Aq8VMK8>?Gx6FGw<r5eRR0caU={@<t7mwI$`k-;JOs;B$nX~)9_M6)@DwZ)|7(+)&g*tTS+@p+=MH+7G&pEg4tArav?>;^3%xk;Qx4Lh2su8-6=N`%emOYCm-!|e^9$KQ?F@Xe(ugTG=h_*Trla7GPqIN!G*N0<LhuHd90TfK&hq^trpTGW#J*E+EzXD7%rnN3$=1wDj@annBob}X*auV3YrM;MrU!vwmM_6yzwbA1)V5W9s<>kc4G(egzBA#kJ^3%A#tYJzaQOa&$g)5OvT(fmgp!?a<luGHG81#(a!F>XCE~p=DhMuLM(>8;?{1oiJ<BE7<1OK2Tl8c0YX~niG5B`zB}wyEVu=B<&X)ABGkq}w=+iUy?)^>lBCjR%k;t<mt<*L@-I|qw&{O!>j76??0nOK#IQ;<RL4uPVQ13bppd_0uq8QFvN#EK69#-Bi)MyT7MTJW4$5(Grr;#yZbfH|_M5GU2^+yF*|ri!+`?y9zW7zPk{2p+kZ(UHPD6B3@~hms;aJB&fZAb1REah>`i44RE~Vo!vvR4p%Z#``Q&*`_hedM{)w$Yk_!b=M9~I@OWWVBa&0`t8@3Hefrm~gL#c;tL{he?98YszvI;%jQ_ZFKPqYa|$6Za<9lLIe+vQLyd4MSlqi-eMXN58-8H6r4!TdfcYwGXmc0xrh`Hc|C2l+6|k8A_CnB_hd*(I4K;?JjVsiokIbkmd1R%MUjIEQtu`u};%1QN=Te0B3Pb+VO74BU8vuX8jQC`{C~?K>?MM8k&K>n<y*nVKaL~RBYNJd*2Er45yo?>tjR{B%CfaNO~n;TptIgA1ITbB|$1gG|@?d5&_6e%~Zt=mGZU)g~Hcd#(a(fpvJUg=2p(7_Q~PlX0z#7+JKDwjEr<bog9+MM5kLLmn-+zZ>)QA(m&`Op$&sKQx>d2*lX#)ikYHW?#(PlAu_Y}DIHMRTlpM+g3rNw!BQRb+jKyMx`P=RU<b$=v{an4g3Ce4Wyq;47deqE`jqG03nIWU&U3LU2s{@6ypRfS1ra@FTj7wl={xE2!F+4auE|iXmqKMY>BPt4NBZ!n@<^Dui8JvRQ;542F>4_wg)Ughh4U7@+(P0dG4#oqMt(imkB`c}Q)q@2O`sD|s9r)v8EajrH4VJn#3yy=-zYywvB8@1(|W<pQm_m32vRxpfdmQN&4uXL$MXW$7S=w9Gl6c3NkxbQjT2h)Ej~TyOWcT9`)AYZZAxqZYzpMBv_8(ytXx$PdQhj%89C1!&BtR8?V9q94-X2JPeC6`8%9UIv06!j&c|nWPbGZy_Rp}9hx8n&N%<1Tj|O>K$~W5wNaf2);pRyi`Fq93H1aI;VT=fI9^Htb-U(<#h^z68bHMuu#ss;DZ`{k3c`##wT*fjcyiLpxybcpQ;vgB`mK67r_j&B!f9&D@AiM?rCV!8Sh<!P=Ay38EG+9GGvWlliilIXsL2HgFr0>;@(i>GgRPfNQeS+W5hqaIX+$(;oKmP(&ql(S')))

            t.write(f.read())
            f.close()
            t.close()
            if db.print_try: print('Trying with sqx sfx')
            run([tf],print_try=False)
            remove(tf)
            if listdir(o): return
        case 'IMP':
            run(['imp','e','-o' + o,'-y',i])
            if listdir(o): return
        case 'ARHANGEL':
            dosbox(['arhangel','x','-oq-',i])
            if listdir(o): return
        case 'JAR':
            run(['jar','x','-y',i],cwd=o)
            if listdir(o): return
        case 'Lizard':
            of = o + '/' + tbasename(i)
            run(['lizard','-d','-f','-q',i,of])
            if exists(of) and getsize(of): return
        case 'Zhuff':
            of = o + '/' + tbasename(i)
            run(['zhuff','-d','-s',i,of])
            if exists(of) and getsize(of): return
        case 'BriefLZ'|'QUAD':
            of = o + '/' + tbasename(i)
            run([t.lower(),'-d',i,of])
            if exists(of) and getsize(of): return
        case 'UltraCompressor 2': raise NotImplementedError
        case 'LZFSE':
            of = o + '/' + tbasename(i)
            run(['lzfse','-decode','-i',i,'-o',of])
            if exists(of) and getsize(of): return
        case 'LIMIT':
            dosbox(['limit','e','-y','-p',i])
            if listdir(o): return
        case 'Squeeze It': return msdos(['sqz','x',i],cwd=o)
        case 'QuARK': return msdos(['quark','x','/y',i],cwd=o,text=False)
        case 'LZOP':
            run(['lzop','-x','-qf',i],cwd=o)
            if listdir(o): return
        case 'OpenZL':
            of = o + '/' + tbasename(i)
            run(['zli','d','-o',of,'-f',i])
            if exists(of) and getsize(of): return
        case 'Flash': return msdos(['flash','-E',i,'*.*'],cwd=o)
        case 'Ai':
            run(['ai','e',i],cwd=o)
            if listdir(o): return
        case 'B1':
            if db.print_try: print('Trying with b1-pack')
            run(['java','-jar',db.get('b1-pack'),'x','-o',o,i],print_try=False)
            if listdir(o): return
        case 'BLINK':
            run(['blink','X',i,'*'],cwd=o)
            if listdir(o): return
        case 'BSArc':
            dosbox(['bsa','x','-y','-S',i])
            if listdir(o): return
        case 'BTSPK':
            dosbox(['btspk','x','-y','-e',i])
            if listdir(o): return
        case 'ChArc': return msdos(['charc','-E',i],cwd=o)
        case 'ChiefLZArchive':
            run(['lza',i,o,'/X'])
            if listdir(o): return
        case 'ChiefLZZ':
            of = o + '/' + tbasename(i)
            run(['lza',i,of,'/U'])
            if exists(of) and getsize(of): return
        case 'CMZ':
            run(['uncmz','-d',o,'-e',i])
            if listdir(o): return
        case 'Compressia':
            if db.print_try: print('Trying with compressia')
            prc = subprocess.Popen([db.get('compressia'),'e',i,o],stdout=-1,stderr=-1)
            run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',"(New-Object -ComObject WScript.Shell).SendKeys('{ENTER}')"],print_try=False,getexe=False)
            prc.wait()
            if listdir(o): return
        case 'CRUSH': return msdos(['uncrush','-qo',i],cwd=o)
        case 'DGCA':
            tf = i
            f = open(i,'rb')
            if f.read(2) == b'MZ':
                tf = TmpFile('.dgc')
                f.seek(0x36540)
                open(tf.p,'wb').write(f.read())
            f.close()
            run(['dgcac','e',tf,o])
            if hasattr(tf,'destroy'): tf.destroy()
            if listdir(o): return
        case 'Dzip':
            run(['dzip','-x',i,'-f'],cwd=o)
            if listdir(o): return
        case 'ESP':
            dosbox(['unesp','xys',i])
            if listdir(o): return
        case 'Snappy':
            _,od,_ = run(['snzip','-d','-k','-c',i],text=False)
            if not od: return 1
            open(o + '/' + tbasename(i),'wb').write(od)
            return
        case 'TERSE':
            of = o + '/' + (tbasename(i) if i.lower().endswith(('.pack','.spack','.terse')) else basename(i))
            run(['tersedecompress++',i,of])
            if exists(of) and getsize(of): return
            run(['tersedecompress++',i,of,'-b'])
            if exists(of) and getsize(of): return
        case 'UCL':
            of = o + '/' + tbasename(i)
            run(['uclpack','-d',i,o])
            if exists(of) and getsize(of): return
        case 'Binary ][ Archive':
            run(['nulib2','-xs',i],cwd=o)
            if listdir(o): return
        case 'Compression Workshop': return msdos(['cwunpack',i],cwd=o)
        case 'SEMONE':
            dosbox(['semone','x',i])
            if listdir(o): return
        case 'SLIM':
            tf = TmpFile(name='TMP.SLM',path=o)
            copy(i,tf.p)
            isz = getsize(tf.p)
            dosbox(['slim','X','O:\\TMP.SLM'],xcmds=['-c','C:\\SLIM.EXE ON'],tmpi=False)
            if getsize(tf.p) != isz:
                rename(tf.p,o + '/' + basename(i)[:-4 if i.lower().endswith('.slm') else None])
                return
            tf.destroy()
        case 'Hamarsoft HAP':
            tf = TmpFile(name='TMP.HAP',path=o)
            tf.link(i)
            r = msdos(['pah21',tf.p],cwd=o)
            tf.destroy()
            if not r:
                for f in listdir(o):
                    if f[:4] == 'TMP.': mv(o + '/' + f,o + '/' + tbasename(i) + f[3:])
                return
            return msdos(['pah3','e',i,'*'],cwd=o)
        case 'Hammer':
            db.get('hammer_decomp')
            if db.print_try: print('Trying with hammer_decomp')
            of = o + '/' + tbasename(i)

            import inspect
            class Hack:
                def __getitem__(self,k):
                    if k == 1: return i
                    elif k == 2: return of
                def __len__(self):
                    inspect.getouterframes(inspect.currentframe())[1].frame.f_globals['print'] = lambda *a,**k:None
                    return 3

            bargs = sys.argv.copy()
            sys.argv = Hack()
            import bin.hammer_decomp # type: ignore
            sys.argv = bargs
            if exists(of) and getsize(of): return
        case 'HIT': return msdos(['hit','x','-o',i],cwd=o)
        case 'Hyper': return msdos(['hyper','-xoo',i],cwd=o)
        case 'mcm':
            tf = o + '\\tmp' + os.urandom(8).hex() + '.mcm'
            symlink(i,tf)
            run(['mcm','d',tf],cwd=o)
            remove(tf,tf + '.decomp')
            if listdir(o): return

            symlink(i,tf)
            of = o + '\\' + tbasename(i)
            run(['mcmsk','d',tf,of])
            remove(tf,tf + '.decomp')
            if exists(of) and getsize(of): return
        case 'Kanzi':
            of = o + '/' + tbasename(i)
            run(['kanzi','-d','-i',i,'-o',of,'-v','0','-f'])
            if exists(of) and getsize(of): return
        case 'PPMd':
            tf = 'tmp' + os.urandom(4).hex() + '.pmd'
            symlink(i,o + '/' + tf)
            run(['ppmd','d',tf],cwd=o)
            remove(o + '/' + tf)
            if listdir(o): return
        case 'ZXC':
            of = o + '/' + tbasename(i)
            open(of,'wb').write(run(['zxc','-d','-T','0','-k','-c','-f','-q',i],text=False)[1])
            if exists(of) and getsize(of): return fix_tar(o)
        case 'Vlaz':
            of = o + '/' + tbasename(i)
            open(of,'wb').write(run(['vlaz','-d','-f','-c',i],text=False)[1])
            if exists(of) and getsize(of): return fix_tar(o)
        case 'Gipfeli':
            of = o + '\\' + tbasename(i)
            run(['gipfeli_tool','-d',i,of])
            if exists(of) and getsize(of): return
        case 'ELI 5750': raise NotImplementedError
        case 'Fold FOL'|'Fold ARK':
            f = open(i,'rb')
            if f.read(2) == b'MZ':
                f.seek(0x2be0)
                tg = f.read(5)
                if tg == b'F\xfa\xf6\xfa1': tf = TmpFile(name=tbasename(i) + '.fol',path=o)
                elif tg == b'FARC1': tf = TmpFile(name=tbasename(i) + '.ark',path=o)
                else: f.close();return 1
                f.seek(-5,1)
                open(tf.p,'wb').write(f.read())
                f.close()
                r = msdos(['unfold',basename(tf.p)],cwd=o)
                tf.destroy()
            else:
                f.close()
                r = msdos(['unfold',i],tmpi=True,tmpic=True,cwd=o)
            return r

        case 'P5'|'P6'|'PAQ1'|'PAQ2'|'PAQ5':
            run([t.lower(),i],cwd=o)
            if listdir(o): return
        case 'P12':
            run(['p12a',i],cwd=o)
            if listdir(o): return
        case 'PAQ3':
            run(['paq3n',i],cwd=o)
            if listdir(o): return
            run(['paq3c',i],cwd=o)
            if listdir(o): return
        case 'PAQ4':
            run(['paq4v2a',i],cwd=o)
            if listdir(o): return
        case 'Fast PAQ8':
            for ix in range(6,0,-1):
                _,r,_ = run([f'fp8_v{ix}','-l',i],text=False)
                for x in r.replace(b'\r',b'').strip(b'\n').split(b'\n')[1:]:
                    if b'\t' in x and x.split(b'\t')[0].isdigit():
                        try:
                            if not isvalid(x.split(b'\t')[1].decode('utf-8')):break
                        except UnicodeDecodeError:break
                    else:break
                else:
                    run([f'fp8_v{ix}','-d',i,o],print_try=False)
                    if listdir(o): return
        case 'Fast PAQ8 SK':
            f = open(i,'rb')
            f.seek(5)
            v = f.read(2).rstrip(b'\0').decode('ascii')
            f.close()

            scr = db.get('fp8sk' + v)
            if not exists(scr): raise NotImplementedError(v)

            run([scr,'-d',i,o])
            if listdir(o): return
        case 'PAQ8GEN':
            for ix in range(5,0,-1):
                tf = TmpFile(f'.paq8gen{ix}')
                tf.link(i)
                _,r,_ = run([f'paq8gen_v{ix}_speed','-t',tf])
                if not ' -> differ at ' in r:
                    run([f'paq8gen_v{ix}_speed','-d',tf,o])
                    tf.destroy()
                    if listdir(o): return
                tf.destroy()
        case 'PAQ8K':
            f = open(i,'rb')
            f.seek(5)
            v = f.read(1).decode('ascii').strip()
            f.close()

            scr = db.get('paq8k' + v + ('_lp2' if v in ('','2') else ''))
            if not exists(scr): raise NotImplementedError(v)

            run([scr,'-d',i,o])
            if listdir(o): return
        case 'PAQ8KX':
            f = open(i,'rb')
            f.seek(6)
            old = f.read(1) != b'\0'
            f.close()

            if old:
                for ix in range(3,0,-1):
                    _,r,_ = run([f'paq8kx_v{ix}','-d',i,o])
                    if 'Time ' in r and ' bytes of memory' in r and listdir(o): return
                    for f in listdir(o): remove(o + '/' + f)
            else:
                for ix in list(range(7,3,-1)) + ['4a','4a2']:
                    _,r,_ = run([f'paq8kx_v{ix}','-l',i],text=False)
                    for x in r.replace(b'\r',b'').strip(b'\n').split(b'\n')[1:]:
                        if b'\t' in x and x.split(b'\t')[0].isdigit():
                            try:
                                if not isvalid(x.split(b'\t')[1].decode('utf-8')):break
                            except UnicodeDecodeError:break
                        else:break
                    else:
                        run([f'paq8kx_v{ix}','-d',i,o])
                        if listdir(o): return
        case 'PAQ8F':
            for ix in range(4,0,-1):
                _,r,_ = run(['paq8f' if ix == 1 else f'paq8fthis{ix}','-d',i,o])
                if 'Time ' in r and ' bytes of memory' in r and listdir(o): return
                for f in listdir(o): remove(o + '/' + f)
        case 'PAQ8O':
            f = open(i,'rb')
            f.seek(5)
            v = f.read(3).split(b' ')[0].decode('ascii')
            f.close()
            if v in ('','1'): v = '2'
            elif v == '10t': v = '10tlp2'

            scr = db.get('paq8o' + v)
            if not exists(scr): raise NotImplementedError(v)

            run([scr,'-d',i,o])
            if listdir(o): return
        case 'PAQ8N':
            run(['paq8n','-d',i,o])
            if listdir(o): return
            run(['paq8o','-d',i,o]) # version 1 still had the paq8n signature
            if listdir(o): return
        case 'PAQ8P':
            _,r,_ = run(['paq8p_pc','-d',i,o])
            if 'Time ' in r and ' bytes of memory' in r and listdir(o): return
            run(['paq8p','-d',i,o])
            if listdir(o): return
        case 'PAQ8L'|'PAQ8PF':
            run([t.lower(),'-d',i,o])
            if listdir(o): return
        case 'PAQ8SK':
            f = open(i,'rb')
            f.seek(6)
            v = f.read(3).split(b'\0')[0]
            if not v or v[0] <= 8: v = '-'
            else: v = v.decode('ascii')
            f.close()

            if v == '-':
                for ix in list(range(38,32,-1)) + [1]:
                    _,r,_ = run([f'paq8sk{ix}','-l',i],text=False)
                    for x in r.replace(b'\r',b'').strip(b'\n').split(b'\n')[1:]:
                        if b'\t' in x and x.split(b'\t')[0].isdigit():
                            try:
                                if not isvalid(x.split(b'\t')[1].decode('utf-8')):break
                            except UnicodeDecodeError:break
                        else:break
                    else:
                        run([f'paq8sk{ix}','-d',i,o])
                        if listdir(o): return
            else:
                scr = db.get('paq8sk' + v)
                if not exists(scr): raise NotImplementedError(v)

                tf = TmpFile('.paq8sk' + v)
                tf.link(i)
                run([scr,'-d',tf,o])
                tf.destroy()
                if listdir(o): return
        case 'PAQ8PX':
            f = open(i,'rb')
            f.seek(6)
            old = f.read(1) != b'\0'
            f.close()

            if old:
                for ix in range(67,-1,-1):
                    scr = db.get('paq8px' + (f'_v{ix}' if ix else ''))
                    if not exists(scr): continue

                    tf = TmpFile('.paq8px')
                    tf.link(i)
                    _,r,_ = run([scr,'-d',tf,o])
                    tf.destroy()
                    if 'Time ' in r and ' bytes of memory' in r and listdir(o): return
                    for f in listdir(o): remove(o + '/' + f)
            else:
                for ix in list(range(210,136,-1)) + ['136b'] + list(range(136,80,-1)) + ['80b'] + list(range(80,67,-1)):
                    scr = db.get(f'paq8px_v{ix}')
                    if not exists(scr): continue

                    tf = TmpFile('.paq8px' + (str(ix) if (ix if type(x) == int else int(ix[:-1])) > 136 else ''))
                    tf.link(i)
                    _,r,_ = run([scr,'-d',tf,o])
                    tf.destroy()
                    if 'Time ' in r and ' bytes of memory' in r and listdir(o): return
                    for f in listdir(o): remove(o + '/' + f)
        case 'PAQ8P3X':
            for ix in [20]:
                tf = TmpFile('.paq8p3x')
                tf.link(i)
                _,r,_ = run([f'paq8p3x_v{ix}','-d',tf,o])
                tf.destroy()
                if 'Time ' in r and ' bytes of memory' in r and listdir(o): return
                for f in listdir(o): remove(o + '/' + f)
        case 'PAQ8PXKZU':
            run(['paq8pxkzu_v69','-d',i,o])
            if listdir(o): return
        case 'PAQ8PXV':
            f = open(i,'rb')
            f.seek(7)
            v = f.read(2).lstrip(b'v').rstrip(b'\0').decode('ascii')
            f.close()

            scr = db.get('paq8pxv_v' + v)
            if not exists(scr): raise NotImplementedError(v)

            tf = TmpFile('.paq8pxv' + v)
            tf.link(i)
            run([scr,'-d',tf,o],cwd=dirname(scr))
            tf.destroy()
            remove(dirname(scr) + '/pxv.log')
            if listdir(o): return
    return 1
