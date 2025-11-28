from .main import *

def extract5(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    def msdos(cmd,mscmd=[],tmpi=False,inf=i,**kwargs):
        if tmpi:
            mkdir(o)
            tf = o + '/' + 'TMP' + extname(inf)
            symlink(inf,tf)

        if db.print_try: print('Trying with',cmd[0])
        run(['msdos'] + mscmd + [db.get(cmd[0])] + [(('TMP' + extname(inf)) if tmpi and x == inf else x) for x in cmd[1:]],print_try=False,**kwargs)

        if tmpi: remove(tf)

        if os.listdir(o): return
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
             '-c','MOUNT I "' + dirname(inf).replace('\\','\\\\') + '"','-c','MOUNT C "' + dirname(custs or s).replace('\\','\\\\') + '"','-c','MOUNT O "' + oup.replace('\\','\\\\') + '"','-c','O:'] + xcmds + [
             '-c',subprocess.list2cmdline(['C:\\' + basename(s)] + [('I:\\' + basename(inf) if x == oinf else x) for x in cmd[1:]]) + (' > _OUT.TXT' if nowin else '')] + (sum([['-set',f'{x}={DOSMAX[x]}'] for x in DOSMAX],[]) if max else []),stdout=-3,stderr=-2)

        while not exists(oup + '/_OUT.TXT'): sleep(0.1)
        while True:
            try: open(oup + '/_OUT.TXT','ab').close()
            except PermissionError: sleep(0.1)
            else: break

        for _ in range(10):
            if os.path.getsize(oup + '/_OUT.TXT') > 0: break
            sleep(0.1)

        while True:
            r = open(oup + '/_OUT.TXT','rb').read()
            if len(r) == os.path.getsize(oup + '/_OUT.TXT'):
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
            if exists(of) and os.path.getsize(of): return
        case 'ZCM':
            run(['zcm','x','-t0',i,o],timeout=300)
            if exists('master.tmp'): remove('master.tmp')
            if os.listdir(o): return
        case 'BCM':
            of = o + '/' + tbasename(i)
            run(['bcm','-d','-f',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'RAZOR':
            run(['rz','-y','-o',o,'x',i,'*'])
            if os.listdir(o): return
        case 'NanoZip':
            run(['nz','x','-o' + o,i,'*'])
            if os.listdir(o): return
        case 'bsc':
            of = o + '/' + tbasename(i)
            run(['bsc','d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'LZHAM':
            of = o + '/' + tbasename(i)
            run(['lzham','-c','-u','d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'YBS':
            YBSR = re.compile(r': Error opening ([^\n]+)')
            if db.print_try: print('Trying with ybs')
            while True:
                _,_,r = run(['ybs','-d','-y',i],print_try=False,cwd=o)
                fs = YBSR.findall(r)
                if not fs: break
                for f in fs: mkdir(o + '/' + dirname(f))
            if os.listdir(o): return
        case 'CSArc':
            run(['csarc','x','-t8','-o',o,i])
            if os.listdir(o): return
        case 'RK':
            run(['rk','-x','-y','-O','-D' + o,i])
            if os.listdir(o): return
        case 'GRZip':
            run(['grzip','e',i],cwd=o)
            if os.listdir(o): return
        case 'BOA Constrictor':
            dosbox(['boa','-x',i])
            if os.listdir(o): return
        case 'Flashzip':
            run(['flashzip','x','-t0',i,o])
            if os.listdir(o): return
        case 'Dark':
            run(['dark','u',i],cwd=o)
            if os.listdir(o): return
        case 'SBC':
            run(['sbc','x','-hn','-y','-t' + o,i])
            if os.listdir(o): return
        case 'SZIP':
            of = o + '/' + tbasename(i)
            run(['szip','-d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'Zzip':
            run(['zzip','x','-q',i],cwd=o)
            if os.listdir(o): return
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
            if os.listdir(o): return
        case 'IMP':
            run(['imp','e','-o' + o,'-y',i])
            if os.listdir(o): return
        case 'ARHANGEL':
            dosbox(['arhangel','x','-oq-',i])
            if os.listdir(o): return
        case 'JAR':
            run(['jar','x','-y',i],cwd=o)
            if os.listdir(o): return
        case 'Lizard':
            of = o + '/' + tbasename(i)
            run(['lizard','-d','-f','-q',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'Zhuff':
            of = o + '/' + tbasename(i)
            run(['zhuff','-d','-s',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'BriefLZ'|'QUAD':
            of = o + '/' + tbasename(i)
            run([t.lower(),'-d',i,of])
            if exists(of) and os.path.getsize(of): return
        case 'UltraCompressor 2': raise NotImplementedError
        case 'LZFSE':
            of = o + '/' + tbasename(i)
            run(['lzfse','-decode','-i',i,'-o',of])
            if exists(of) and os.path.getsize(of): return
        case 'LIMIT':
            dosbox(['limit','e','-y','-p',i])
            if os.listdir(o): return
        case 'Squeeze It': return msdos(['sqz','x',i],cwd=o)
        case 'QuARK': return msdos(['quark','x','/y',i],cwd=o,text=False)
        case 'LZOP':
            run(['lzop','-x','-qf',i],cwd=o)
            if os.listdir(o): return
        case 'OpenZL':
            of = o + '/' + tbasename(i)
            run(['zli','d','-o',of,'-f',i])
            if exists(of) and os.path.getsize(of): return
        case 'Flash': return msdos(['flash','-E',i,'*.*'],cwd=o)
        case 'Ai':
            run(['ai','e',i],cwd=o)
            if os.listdir(o): return
        case 'B1':
            if db.print_try: print('Trying with b1-pack')
            run(['java','-jar',db.get('b1-pack'),'x','-o',o,i],print_try=False)
            if os.listdir(o): return
        case 'BLINK':
            run(['blink','X',i,'*'],cwd=o)
            if os.listdir(o): return
        case 'BSArc':
            dosbox(['bsa','x','-y','-S',i])
            if os.listdir(o): return
        case 'BTSPK':
            dosbox(['btspk','x','-y','-e',i])
            if os.listdir(o): return
        case 'ChArc': return msdos(['charc','-E',i],cwd=o)
        case 'ChiefLZArchive':
            run(['lza',i,o,'/X'])
            if os.listdir(o): return
        case 'ChiefLZZ':
            of = o + '/' + tbasename(i)
            run(['lza',i,of,'/U'])
            if exists(of) and os.path.getsize(of): return
        case 'CMZ':
            run(['uncmz','-d',o,'-e',i])
            if os.listdir(o): return
        case 'Compressia':
            if db.print_try: print('Trying with compressia')
            prc = subprocess.Popen([db.get('compressia'),'e',i,o],stdout=-1,stderr=-1)
            run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',"(New-Object -ComObject WScript.Shell).SendKeys('{ENTER}')"],print_try=False,getexe=False)
            prc.wait()
            if os.listdir(o): return
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
            if os.listdir(o): return
        case 'Dzip':
            run(['dzip','-x',i,'-f'],cwd=o)
            if os.listdir(o): return
        case 'ESP':
            dosbox(['unesp','xys',i])
            if os.listdir(o): return
        case 'Snappy':
            _,od,_ = run(['snzip','-d','-k','-c',i],text=False)
            if not od: return 1
            open(o + '/' + tbasename(i),'wb').write(od)
            return
        case 'TERSE':
            of = o + '/' + (tbasename(i) if i.lower().endswith(('.pack','.spack','.terse')) else basename(i))
            run(['tersedecompress++',i,of])
            if exists(of) and os.path.getsize(of): return
            run(['tersedecompress++',i,of,'-b'])
            if exists(of) and os.path.getsize(of): return
        case 'UCL':
            of = o + '/' + tbasename(i)
            run(['uclpack','-d',i,o])
            if exists(of) and os.path.getsize(of): return
        case 'Binary ][ Archive':
            run(['nulib2','-xs',i],cwd=o)
            if os.listdir(o): return
        case 'Compression Workshop': return msdos(['cwunpack',i],cwd=o)

    return 1
