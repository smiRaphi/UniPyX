import os,sys,sysconfig,subprocess,re,httpx
from time import sleep
from hashlib import sha256

SRCD = os.path.dirname(os.path.abspath(__file__))
def get_src(p:str): return os.path.join(SRCD,p)
LIBD = os.path.join(SRCD,'.lib')
os.makedirs(LIBD,exist_ok=True)
HSFS = ('unipyxx.c','util.h','comp.c','crypt.c','ext.c','const.h')
FS = [get_src(x) for x in ('unipyxx.c','util.h','comp.c','crypt.c','ext.c')]
XEXR = re.compile(r'(?m)^XEXPORT [^\(]+ ([\w_]+)\('.encode())
IMPR = re.compile(r'(?m)^XIMPORT\(([^\)]+)\)'.encode())
DLLP = SRCD + ('.dll' if sys.platform == 'win32' else '.so')

def remove(f:str):
    for t in range(5):
        try: os.remove(f)
        except PermissionError: sleep(0.1)
        else: break

DLDB = {
    'kernel32':('kernel32.lib',None),
    'xcompress':('xcompress64.lib','https://raw.githubusercontent.com/NativeFunction/SC-CL/refs/heads/master/lib/xcompress64.lib'),
    # cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -Wno-author "-DCMAKE_POLICY_VERSION_MINIMUM=3.5" -DBUILD_SHARED_LIBS=OFF -A x64
    # cmake --build build -j <cores> --config Release
    'lzfse':('lzfse.lib',0), # static https://github.com/lzfse/lzfse
    # cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -Wno-author -A x64 -DZSTD_BUILD_STATIC=ON -DZSTD_BUILD_SHARED=OFF -DZSTD_BUILD_COMPRESSION=OFF -DZSTD_BUILD_DICTBUILDER=OFF -DZSTD_LEGACY_SUPPORT=1
    # cmake --build build -j <cores> --config Release
    'zstd':('zstd_static.lib',0), # static https://github.com/facebook/zstd
    # cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -Wno-author -A x64
    # cmake --build build -j <cores> --config Release
    # Base85 lzma ALONE patch:
# T>t<C0RR90|NsC0{{S)?NeROI5q(hJ3QtGP%+|kXOt?<5tU90woZbluxJ{S-xp4eqw;2vMh+sbU#(Q-Ofc@YrkDDTJJA?4>f7X5mif9Q^04)-%4|Hl|@-!HO?BLXMaM@*#5c>ci_ylTNsE3>Z!lDd<(bvN4FBbq%;0M)^=?!UL`a^Gp3DO`FQabAw8qCs!xMxhSE|{g4XfAz2*m1+4`-kQ=$yJ_>#Qql_i#YTjc2GQPC8rB&07?-~Ugq9h0Dt5_{bAw3^@c~MfFyr*#}SKX$Dr>GmU^zgRlF}#YURW%37Lmr$E(%YqbAd!WmK=+_w-3rOY3(IINoS#@NAidpb+kL4G0gkTR5nF2Ez@9(CQCWQ`4zR@4ZmC_d+!gZ(y5@+#0>Ta;8wa1GW}fm{juML7rJiv<`e5>N41^;%OV5R;*hXHa`FvpkIrgLH^FhgK+v8$9p9Ao&3yy2fTHw8#&^e!O3#(|HtOeJKiIAd^$wT^dQf4=UxiR;{E0#!(D>x3VzUJA_c0-Svikb&qt;us?eW>I9QutP&{Q)UBmjoI<1I#Yk{-|?1(?yfTwQexm<Z#;64NH6F0<$g_=x+2>1r{CWNkAA11|k(tJhJgM3c#(Mv12vZ%kDx{;AU0dYZS?iP^QUiH48tR*?*c-RKzWCt0vE6&gt;c*%@h;BX`Tr|`gkK79{>@^(?I4=8l&6xzh1a@~XpJ*011AB8pPCI#Hoy0XyWugW|^yBs-x)Kkmi|_euJBhEfXiV>&FPWnT<iZ;CVC-zJNQC}>e1g{HmMONdxhPi}2;!aFtmt&N54Fjx9Sge50l1<d9d8Y%viFn1GxaT?c0~an(h|R*wo))YhI@lfDmwV!n*A1zG061$LMVetp1hj*&rx_&+}p0=3U8)o3{zXYnoBX@?f~N==@GSUt#$t1^v;WasKyjvg($l-FB6ekQPmX<<UlP=7wI>=+A|PPvp%c`DDq4pH8Nv@n*w%Iqv-+-(2P$)`a~c}=AY`{<%)w*Fb+{TR2iIs^oHQrmV^((DqiyPHEGIqWRbQz{n<tK>771b%5aqCklXqgb4m-1crLD_6D*b-jt)x(^%aFMz|)pWBisgs-AC1?rb|%<^LOf2G(EE74CcLE1DOZh3r6S88{lavV-c&U!H-)8u^EZU!~nra@Ao#Bn#N@mE+WrloH0Nhcg!S6dA2OwIVfz1-;eFqNbW7GU9UJzzi;L~_J6`;`om#cG)l6D=wK>(4Kphly7T7vVtmw6TZ`|LU^T!^B%q&Ma|%MC`TfRQPd4`VSwPB%P|!iSaxlo7a=l5HBY5AX+?|=^jKLP6kx58{NTURB)Z^ekELtQ2f~0=7IGdB9bhN@(aJi!U3UINH^jXXuxX`Tb5GD)2og_GTR5GqYuqjyk`bmV$dcK^dcb?&xlkA4f=AoxZ#bbNESsrWefix$&s~NKUG|%pj{T3Ar<IIyvz17)Q?t?|}?Iey766KBiRqY%FO1-{g6_WS;fCRAMo`iz6G>KDhm9_6{!L(R-`ss?(@4m*gwM@KO1$H~MWA_URUBR|x!V6^_qFaMlPD5FUjI)-5U%3!T+jbKw!V5Gy>)r4O<(6Rp+x%=PErx_QzFZvJ#20Nz8Uoa<3gqSF#l=N7M59DlgU(KV-`-jb>6GAB!?x;%OyQov)DA}526LNcWf&7Y>6gKF*7UWWf==i5eGB?hG4Rb==6ijlh*N*{8o{U*ooqQoK%h6Sro9_9Xbk57!s#dE;63Rtlyk^1!$OP`*n)NTS$$9%n*PqDR-f?(mEi4acS(EID%=pHW>hN*nO>I(DEBAQwzQi!Em-`og|eITT=-(V^0;7Q3%AYp0<2y{?(IDTaf1n>K!o78>OA&n!Yuc6j5qUIh5K9xF9ZUjXnpax)n!auRfBJNPCzrl!IEm-|KX5}Z04w6|92l?dC>w&;eScWmI`i$c`hiaMBtZg3K(ib`zm(f4z|N@4#VD^4p1}eSoeYNTIWj0^D*UgSgqvHnvi48xy@$Npxk1YQTaQi<L1L%Q|Vb-6SKzw*Ri6~b!&TXZuBnHP^?I&107~DCte~ddPgR%CHjbYQc(r9DDktk=37pd)My?5;1v4Z@9<Bn%v~K5+U-|q%y5eM6mA*Tl~}e?nd59pHeIyf`<5H>QRWA-xYN+uhB*L`lOqz{3>(|fGJE~|*Aq4!R=Ln6b*owPMpg&x0hU?6AC8=ji%<hLXrLx)LR&&rk3RZil2g3f%#yG#W{cZ1-ILvJ0qrJhC7+o~BBir)KB@IVj`IHneU;e?rLUo>&Ft650?c*2Py-~mWj0~dG;q>??pq+Y7<cs==Ley$096^_?zx%1GYqRR<$I`Y|FzmCDKwlR*`AyUKrZe~|2Iw?Wu^0-31a^c$zLb2JKup}J?cp4IF!O!19v~a#-+s7Z8q9>)#Qf|y{(~4<dI#$L(<!bP3!K}Zi*HN;tD0-1;k9ro9G2wm*Agh3J7iAqQ6DSf51F<MG<1on*H0!^)3-JVd=Qi<_3)1_(9~68|p^?0S=&_<(c%umUQKJvaB9POP_yQ_QY{E<@%+IFkmaOMJI~<Bw(3~yUC2+x2LAiRYPtSUZ}|Gt8(KRu2wQO&ifd3Z8Y8lbQf}_g4@<?;Dn}kI_9RohI*igN3JN`$^rvz5|O69Y4|czgYEGW2`o}sDUp8$OX_`zAByC?^Q-1`?)O<#NWL(|tP<J@G1F!(U{aje?bN__eW1=q*x+l-b8s;Y%xyxWET#kFUhN2|)e0vEPZe&7yES9&0*m|}(6JA%5KF_!F)zck&!~w}hBh<?<bVd*4g`8?7OFd10OA<5^!>q|p?>neIdL9P)AQkwTQryEII?cM+qB8z0{dt|{aT~90h)$QqxlPg3iQLbI5KY?heG8DE)NZC4SfpB72B#Bw^Pi;wyt`Zy|jf$ip8tkWYx_u^T@+Q2lO^Pio!{;*9{%4oDq^URPJAbb~)E2>=mQX#<4{<R99Q$`k9M8<D}|w?!TBl*8=Fg2z%sHo5UXGu=1}GR*uZB6BP5GDq_XmQg7@t3>Kd7_i)yiH@&HQGjx}vKUQFM-Z5#55s^yar?M3SB8Z}2E<G$qPx=^mDeuZe6zu1dz1^Sd^!0>9s+TH7E}Rou`GR_Gg=qzEtXZBD&Bu|ie0tEdw1#F_bmwKzXq|5U;~|+~+D^A0r*Hsy7>lm+gnI@}M(T2bO-pFdY=1Jr1IzIlKSH&sAyroz2MpCw`|b$ffV0~jU!HsYRCyuz>U{K9S!*Zj)2w>_Ir*z`U3D6eMkqJvH3agbL5jXND9+D?YY1G3C+yd!n{6_Xx^wtcs`4niK`v{qO@;C5Qsgvqavovv)z1UxWduZlu5dgEq)K}vNebn2CWO|`B-y$KS8|&P_*=874;^$45Lv{dnY-8jt7E6mQiwlvPJ8;2rJ*+&K~cHiX0|5r!$>kj<fpIw#$`Cl{eT${Czu2W-I-O8+C}g0R3~Y$TxW0?I`*`UNpfA?8uo_BLZ8w0X`s=VGKZ<fJHd*Gc`bWDGGW`w;Y^}{SM+OT{IQnT&`(~HCvrnHDF|O(J0kr3xF*Wh9dY&u5pGTGb5PtF6;ixs=FM1?D<IPU@J1QRoU2ndG=rR<Y}YkpLP}>n^J%LJ86gJs3<d+}bSaDK_kgg;d6&>hQyUpW<K*95JQXv4tM1JNK8$<{u)I;C@GagdU=B31u`OF8o;HVx!<n#B@V*8z{Ao4PBxjTuR4f&)+n4$8xel#5*#f=$3mqC<=gHR0<za_e^{m0W=5Je&!uQ9mAw7%KTacbn>GWF;oh?do?DJHY;h*R+3Me&R+I6l?S_*YTZekHR)Rq~WWN#GRE%9B&8KgkwT*o7B1*RiC*WbEM=3b{Vi5fWce#$I~gx|#K=U=k{eSSj=?-sT7ngd(acor(ArP{V5<v6;V`Yo-32c>s-34(P$0S&5{Iq~-$AcdU}W#7cMzN`v%M5j)*)s-w#f<kIVk|NM|1=E^iGhFjE>OX*HaO1e<g0(iew8|QZ^w2+5dRhHM(MlcgIX?ld!I1UJlS|V6cYU<yq<DoWfs2c$269}3HhDhtN<dXJcO(sCmIsT%j!Kcjc|bIqe<OdkZvP?2nlnJZz7?n5HB*~yp!Tdp9v>T$?$_T#gP_NrL~TyK{a<|(#SWdLE!{Sqo3ns@ly5*w#+knuaPF1er&nSytJla%OdqmGi-NOSP+KoZ_}HcRal-dn_$Ikx$U>1DX`rKP&U2e?b=J$ys+VjN->#PkKo%^;;XA9KTOcr}V6rzHwP`<OMSU~Y5J+dkt2%yFmn}&cK&~CVw40FdQpNH#rKIsx*}65HyqKyRZ}2cB*+Y2Y$y?On*yG6BK;d!b*rW%5rq&HMf}Jmi;G{lzXtccj6R6A{*hH@-mUSGd$h^PORfq%X=_*)Bu`gxS<j!I!uB1Z2LV#hW*eT=`*;D)oucUIPOGKv}Sm?N82?Ocll;bIT8OG6;%qn^S`37{IwOm4a%!RtM6ItcH1CbV-Lr$?5n%)8d-JnC0Ss<I-@+OOKvlM^YD}?J=9?C0loM11p+$$TS#lg|A5pzgC2=;?ko;{k=`EBJlLY5;A<rgx5CY0$JHYw+62FWMK1p%>>RbjY>a03>-5Y2;DHq6gVPba&gbQe<F>5FDm3X?X1+?1>KY}-ca-)RC#3*J;d8AxkpE=AJVA_LyFCvPbdgZeJC9^#z_4ylsBFpJZ9aCR*+HrAi=yP&QcZkTpdtR=b)FH-Dnsv={z5$i1=m7-%+JIa7Pfx9~x$p6_ClbNk#w(Qjo=J%C#^6EP1Fm^Y&B|9=eK}#)!<G9F?)(^WzzH*q|S%+G>#`N`AJ^dffz4{gZr6apGW8~Zx#P%=*@ExHNzF2waP%7xd|2{xf3%gC2!BuR0ZW#D{6b}D^#!pI(Q$&cI{hI@l&TxiZ`C1OHP^mMUtNdUUN}N+cfFSnJv4cH*6v-jawN>9%p6V<Zn1|zK*)+gFhQLb)z`zTpfTrB2ELIbPeR7UA&V7ZOZgX8RL;7W$Gdw61wjSd5p1HL|%2@mMFoS38oeM=!ydt(Oxx5lF5+_t?o%XR2A9)U{NBL7mVFrER?9{|A6Jzf)t$m=Rq@}Qs{f;O<zA6FKnJWH%xp(CsuANGut{kj9k5VvX#3{={Q1wh7T>>VLlU@8hz_C)4TPeC3U*4ZK0)m((8i=GbrwS9I6(cN~U17af+fAUWefMym9Dq!MITxxG51)8ZG{=J9?(J6tbQ%(GOe13UO>?B9SjI$K7AhLFN$VeV+3;$=RFBy(pZ#otuX5dyzZ`Fe7}n3E8;nbd^%)n2RD?*Udb<@_!xgO{!u$J!faR&pWLi8O+KS_iMRO=IP+jZ#>@FLUf~eEc@dr4!ktzr^UAk{1Gu<ZxDq0(nq56<J|No~`7v@!nA?2mSaV>H~(;CILtWzbq#4MDF9A$aHD=^2mbZ8Q2G#}w325<)kAD>;L;AfPF!P;I=D}b_Aob?P1o=A0$5ElHxUqE2_VVm<3Av<G5zVh^|!l?D$07+8bYoDP7wU%cYkCQXes-=k5c=haGPONQE5Guz$iE-ryJesyWp8!~?`|e?FTd-12Qs@~lA^8Ot1#+Ex-`sW^xH>>_vSW_6ynZ}P>S26`7ewn5@AGXjA68JxNiS}k^*9?^WR8INr|#Dkm?|AWiLJ%y6^#LlaChumj#YULXe53JO<{pd4%J{E^)~$NUuS7OvW=z0xXJ(T&UyZb<ItjjvQ`p&Zi)#+2XgUl-_bEl&Xt7D`PBIj>2jLqDMiJnraWSB#3`ujU&nxn-Fyk&Kr884Z%LZ6iS$G`NsOh9%@>eAM7R{PP2T*%E4m;$*BVTu%knFHSrCi3R~+Y<{_}rw$W1&VeaKqYdjy;muC$9=CJ;;9@jpZ976rm+q~WIQko`-qeQ+K|Hp!xm?Y3d8u{=B3_~R-QUBm59&;G5&6IaRq`F)Ywsfw$sf9%=s2+_O+eWyn4%URzH1Z67H%?yG+Fu(l~bY}F=sW$*uK4b}}J*k`%iM=pZhl8bzZ!j_+WJIQ1{q(OIP4wvY;R3{5<GnLFz0_exN7tywAI%vAiHz&f7as|qJfhgM>~j_0lL<e?!4jp8YyZ*(m3Rd)?)kWlUG(c>eBQTfqUWC-vLEM{FHjstU653zs_Nc3{tp!m${rU}RB8Ejj+q1?B8W@K(zd_78=kPuRrXZgw!W_%Z|)CK_yH^j;nK4o?xIe~xA{WoR3Q?Qrg=-#s~DD=Y%(b5O=XrX+0GCH!;3%TVkZ=N9B^r^1vp7)68D<esoqM$EAUd{ZeucvlmITC;#}BAftJ<nDE7%H3VhD^7W{L65q_#EobSH)Tq}=P6}{E~^QjQ7gGz$ia$sx?99gx>w4(TU1<9uc;yaLAi2(=KdJZ#Zy(MlB+8h1l+%<jIYTVUM$AO6v)w3Drqz<1gTeca6@MyoaW#q~zgv%b-&T1cc#OL4+PH?w3-vnWX9M~4xa13Hq@!fQ)qB<aSHr%<LKK6z&$UQ}*vMxk%I-7bHghM0bOg4MZBgbo>Q5V#9<UN!s(DjByLSD>*deOw{U02|*>WbQ(X+q6;?~Nj6M)0GWBqKH~xNHJ=hMPm)tiTph_{(%`=q-TjSi1R+yFpD?0I^j{PHT{8&!6%SYqeP!sTQywG#2G5SFx<gV245ST|9QU89eL7EA08T2jHCk0j^Gzbju&O@v`G(IZRxb!tT%2`JQQ@g}P}mOMxqfivE?7UAZnr<zqJ+`b6*cxP$DkSXvZF|007kAdL&ua@a04QOc$@+ZfE9($ed{(pl<IanXG8j*Gc!8f{wB>6pp!{{*e@qB+%s)3Y$e_yp}1c!hpCUG1Nq`$lewW1YS71-9(TvI41OdcBZ=V-;Ba<rj*VGU-_i!SEG8YVJ9k4h{&21om8tPQ<H96_WFvi30=57uale8%~;e@3K#<)u2>04rM>;A7k+8u#&v2nCTI@LiR_1-`kY9^DKNWjm8bEs7|O`x^|FUUf9yeFNuI5o`yg!NjimW#0`ZoX-<`LL8pGH96NH1Vze8;LcpWr{v7&&tqd#@I~WCfgXMW<dZmq^_IQB=MiGxb5ymQK1HIX2jke$@PJjbF#iSin!B@fFEmpLh!bLxLBoNtEYPinnQ)Hmq4g7SxdRL|?ZOT<fdJ`Fhh{xSJR9t`Ms)kZAa%5~1Hsq0Kr=-YXvY}a3-acjsBL+N8WL<u?+X9jitb_L6@vy=`7G52!6ZTp<O-6C5nx+37Diz0vhozvd(2t`39t{Ymc}q*S7iZ;ai=LxAv>#?9qj8prGs7XZ6@76&*;Knc431U$k1<>IiqkpPU!6pEi?)?Lj{Z@ucNaN71XC2_M3=i=J~Yo2iAF1Qg1V|*Z;WudF9Wig(B0J>FEvm8OWqz2wE-deuiC@rm(g@dG<#7??t=V5jw^Z)RmuBvtK)d?yx1LTc=7ySn2F`+Q?j@VPfv6*BB0oHcKG33H<#<+(JGAIAiW^&Dz0$MpMG*0RBnKJm#{ZBscP+^Bknm9z+fa|G>ST00FKapnLdv32!C6UL}8~vdFFomwH~1pd#7-Xs1H><c(z#M=5eEVa&}qn!$69l>#MWb)!zyzD!3MS&UKSA@7@B0y;<tSkdlVzgn;+=Wo(GtH0)iR-*XTH{z8qmg;H@{%Cs^EVr?(=dc7x7aJ&$lUE3BkMGqo#&%IU$**ix8+BcUr7jljYx@ghqYwp`G6IoOO%pDoZMXq%~_zv9SMGS55rOpAwlYA@Pdq8WhaDcV**EC<1Xa8N!yQnpSZF!{xl>W4FcZPO6(FjJ-qnZ4-wfzeG!HBnxVQb0{LQT^P77v*qX$6<PI_R3wcpM!!p{(TOT9^OenW5Np2WPdYj*?4F&6g!rmLa={Fc0p*K2J_z0#7evnHDI51SL%5{ePz$71C{nI~C0Bu?`i@Bk{s3cnVT<5Wi`$5e#M<U+pg@;p~LUQmqRbKOsVtQ)tTQCCcMC;0Evg?E{hZKxFAR_%6bdK=e^`w|+g#$S}h8gJmIBRSB1fm_VK?_3BbW+O8jC2?eC5xiyUxcfnCICZc`ket)Ey(jH3O4Sjg-LM@Ds-3IcTPUYwQp~ap9L3QQ)vTgA3A*UE(0}~1*(>GYI>FZ(td(5VyNo>qHPtN3~j$nSC^BESS5-)!NezasQvHxJ3*O`sMWR)m)ebnDSUaQ)Lm*AIdG#O4UyG<;h@3sQeb)&Ul9+@dTNN8k)g#1BB$xT!7;1P^3a$Nk{T)|xD_R=V>nO$XLet2IvKQ}6SZ5FI%+E?a9ZAPiQ>GNo#W(KC&s7!U$SmSfVZYEXICB^kZ4XBc8N_xZx3^!z?|ImUN>@_?@RSRdR3M3o&Aqgkps$WT)pp!Pw0%83YT4oiVb;{~O-=>t!U6PO7q>umUKHZd-i)fWB7k|L0Ww5N>g=r*6WpyE{AKC05PjA=(pUjJNK<c>?vItg1HF<VwN7po-R`4%hQe$iiBS7%R3K2`js7vzZmt0I^!OVb`9bNuD-DYyd4kP_2ywBCw&CHYfwy=)=Jw0Xm?%`NXFNL-tPGwp(NX0pSraapv2DSPJYX(jmFm|c_4!+3XBl14}Iw6f6SD9iXkj}$57Q{>hAMu>7x#|pQ5?_4Qg4Eh|u1n?^`BL>Y$&i=d^m-VKTeK@5EwbmYWJGN@_E(W;`ncpK`Lv9SA7T8*$NwXGaB{UL1_}>?(@V17QN!}lUx+wEs8}p+Mh47S;l<yrYw}LT`*|#W0aG(L!E^;;N2F>a=}cFrV{c3s%L|QcN_gF!Clx27C_zX!K=PB*g(nF$k)bLOqz;^%{eCZR_J0@P<;q|9h!S9xrSbzw&;n~tpQN|}GxeTXN@0hdQNwN}Jwk!YBh{CMoaMCcUoDS%`om5vT59w%mZX2!r~!S)EYcnbrUp0d9*<km#<uFAc+OAwP=U(u{h*Li{JxiH2Coq&((JMO@OnmFE-$)#!^tfy|M{pl&1;T0?*v5C?YP4kLPvyCpb<4DbEQCB`@*kAK160;UAjC`QwHS*8jV%PNrx@>nLb|Iw!1><Q_RDEH8yGd=uKCdTR|x7V=VWJ2tMZkXC@lgW7~3>2_w&qR^KwnK$F#q%tjQZC|v?x)d_jEA64fMSjWs{`4Ban!8?c1gWbz8jC+d7l;>e!Q8D(B|0AQL`VX4eiR3-DhPlD7rfE8S*g`wacqgwcQM+3zOMi#VDzNr`C<z1iab7j9PLcTFpzrQR)9Y)(QSN;rl<cp?t(J~<uBjcC#gARK)?lS&-l!LU2WvV`SZv10*g$!!AyxQ$dpk7-&BXgc0*6NE)^^uH5rNb;&THc<eP+WsL*!j9`}QNeZ<sXr0tXQB5H10bhFv)J3sNCUdR42qgn!=-ok8FOiL{Q&^x-VQ?*189p6Tq;;VDqO58Llk1g!<|3LzH)gxo&u+GwAVIy0m>K;ehUF41Bf*di203^i<uL7t)zxjoQWM_4i^vo|g)z`bQAY%!7u@08FE&T>!LGulET^6=D+HJnp;92D^R0aW(nll^uqz{)Q{in%ZGXNMQbNW#hHJ%a)fwCKDx8FhraI2!XPx&#0D`tW`pb6IOtXS4<iOHe1x%r4nAIoz^XJp!QE@dwoYvMH!X9;0J^s)$>!kPcA>?pJD80UkZ-4xHxb_A_|MHQHx<dwI^K+=OG{+$9=PaqCH6ys!lD3KuKlvnf`L7u}fl2$g2}mR#vC%;QiD`UQT(oZ)y%sJ0Bwx?2YM1!BOd@QlV!1okRkh)~Z|5vW~}zFAi(28X<?^<v+Cxg@Qmk#<{YKeAh0Y8?V830DazuyLbY45cJ-^*8IlA&YbX`*r~~+KAAo2BYhJuXZ(A%cleqh6eX-af^e%u}A1wkm3h@_ikP;(r8bTLiUVNZs`D#T#an8L~-m<-Qld3E=QM`7hI$(Hnaa6!5=#(U|LE+oeg)Ut_5Rf0$TrE^^@}_EajBlMgI{1-_0>szaJ$=2?o%9lTKDDeQ}P#l|zTLZ6Pz~2z$uPa-;~8KHppYS0nnF&GJS~jJ&z)B(E7+_bKAQeK!!+27iMt*+Gx-=(FZ^IgSiYz5&Z>5=E|+kEi#6;Zq-4t&FaYCupi+1}q1v-{AzbxH+^?zZcOf0YaETdv&h8{~aS<2u&D0*wu+TF1KJ?G4x2huPa>7UXTspygjfP8yf}EqAaj@%On{zmnDO%x7W(_^rH{XZep=YgnI2i5k`m~{6&#+Cs21fsN-kTKW2?{*uT*2)tW-S2swBB9cClybwLCKgZ|+Hk3oT)sndi6Aw>S9e-JI7G_Gp=l%3+kQ0S?Zu$)wnvAtdq*J><etoO9Vhe(r(;IdbeVm_kK2*^OOEwovZ9vx#eqECH9sW#H@5>`QvzJzhb?~p=#vmdMGlh3gEQBn4P#P82fc-JLI)fi=RvZeNxYNl;B?*#Nvrf?k<B*h3Xe_dGa!wybj-{r)dfhPsohf@Xsz=HC~JSNkuS%3&`+}TlssLKkiU|e*OGJ83&Pf`ILZcV$(`X+YZTn&LCGzQBWaG5)NR^*_`1rVsURp&%Jo=(K~PH}0aN1Bg#C;<vvX6;7AZva1mP(~8~lf-Qg^DKQ?f!{J<6nAL29lP8Q{GH*nKukq=+y+xLSMYaiuy@KKAY?NfRag<VS0=sS`gj@H9}07sg>Efi6q2U_V%UpcSC=C;v<o(bBLkZILR%=-5&2!(e06LZU2vfrQ}A4!6X<l)n8U=-bZ~N>Cv2F+SSxG9n*K%Qy3PrvqJvx^pH(Gk>YaAs5OW_pchegPGRbY4S?nOh<XG__pxy24guBnCA$oz!tu<YoCk#Oda}v3P(?C1$U4cwM2nj~(7J3uk)(#$L>1cJ27erMbC+uA*2aXnXGrGpn8LDo?#0|`X*(-o+{4jCMXtL;nz}T;&LCG9AN;~VEr@7z%Sb7UdQEv$BiZrY%O^*SJ8K;GpP~+~(UXe}kQnU3qrkEp)J6yuG9rB6&@xHWv20xS5lvBD(ctlQ<fzlqo>ZrlYtr5)XK-~&7Uw8@ppE^I`EA_y%(F!bEP=DuNdn?nY#&qLrUqm|>O?I`5uBBxOmCdU&m*#N*`n%el=-6aFbJTXYX{?hITX)^0CiyHH;$Yf3rWkeGX-<A9pg`!^M9YRrNjSbWD=Cguydd8Vhb2<nshiU={}4;^xF&4660c{`1!^XEp`gxYsIJjkBe|DG|MHqig@V2%-2}<9-y=3j;Wnd(+zNXILs2w#ANB$Ub|g32X#k`*P{9>-s`N&LKk$;=oPp#0dBCJSMAd%8XpGszgeS_fygc$7JruRh5ptmbt1j;a1Pf=?&6iyQv1#AJ!@{<$Z1utHNa@UeO(Mmf`C6)Pk{Psh`4b1431tLDf`j~mAaZ>n8%>?NR37;G+|#U2C)&A}HfxJMy6dO<fW|mEV#Rbw_3hubRnCn*`PUqoJ4YU@#(Pn{oMD$PS?d_-|2)T<q4E;KZQ|)KzeBIyqI<#LfHzImlyKjkFtJte8aPPKf!A5#@}Ufvy)t5LZ1y+E^*zI8`#veWRXWFvn??Q;EOwvn>gk`Cl@=qAyDFTnNIHuB<ZTb3HxA3u6h8(@+^MqWh}RNUh6m>ahoevEj?D{3kgDxf(~*!&sfP5;=;R3k;I3eVRa~lz&r?9=IW_$t*TV3h+jpSbXpjZQ+@81SH)Q(vklNh$@~R4O0hWCtC8U10j0`!}UeQH3EME&L^N!#~pPX-H`*{$}1u6!=fkx8Y07ZV`%xy0K#B&P-qan1yMTb7l)ZgPyVTCRuhTXW{(t0k_o28{H!C*VHb;W+1^gOkUaA%B-eszz|K+$nZ0+;Mz)l1<w+O6}-S~+#OAB{JSy>T3P9L0xye0qhye%vQ%=>~-jyw|D2XidoWoMz5Zcgjddz9IFV%?+qhW6e*?gwQrgh4t@`CAJtO!`OrfKGjr#IyOq3jPxfmYVX$KGBx=?i%DaOs35;8gm<9({i$V50zg{_43%kp_`lgZrD;gpX4v5J3Kx)@^`vtcM~`zU4hmTMSP2YXgQhuVe$ViNQkrhWlkthQDgMHBD@y8HLl!4X-~U+rrbUn+>mFIMjt_)rep-P_!^g-F2d;j=C3zFKF(SZrk7lk;n=uQ2JFGsAINS2Sq@y)5?uap#Fh><2N1Qt5*h|CK#WdzIRl8en9uic?`g;O1rU+z|5MPc~5Oe+VZ8{ZW@~~iwPs`q~%k}Ij6%7aAbOOBI+d6g(J+ABQvB1$|g{v#tvU*X^i12~6;4j=JKmYZCsTKeL)^pKM;LNH|LLwZcKic+6N^jfw*hXWxhOw~1^o*RafLR4@+J?5I|DZHL*4fYursMKb-&$zpw;#vBL=0Aq{%0dKYM(X-(uGm3xxoTk{qVDtOJ>rGusSQdZ#&TpWD3<H^n2;gWFv@mp_D8Jm?%hZO*YX7eNdKj=Apsb8Ogltrp!Pb|BG9jU%KS?#0@KK+Igeq{`i>e7FECJJV~&pZIae+VY83jNhYY3zmJaqn|OIeRG}W0%R%co1lSRvM-$>-@RUoa`jhx6YI6eHp4TQG{d2Dqhrjz0x>u1oQ|r(o7lFrQ4S8DkJjxe61%l|$-1jS+p-ctVXKFe~1?IgP&C%9W!O4K<sPjd4%_%}EszF`V2yMM^Vgwtx-IW-SnqzV!uyH++@KjF}o!JRW4c8b*H^?|<1E}<^`g_AV3e&?@K?iVSg;_$|T02QbF3PgLD{Abmh?o6n|Ieao13$IQN<`1LD_51g@3Knm5DAkZ{N3kA=grm>nVty|l<gJX>jAY;>AeQ`03$@4N;+2O&P1f;5(|Y>9FG$5O2YGFM)^UvdOgf^PjKl-$@3rsuwqznS2-KQ01rpTIsMG8+O}la;$WQO6lApbcMfx2baHOU%o4=+fS=rZhqI;tN3Ri1UvKM;MvwxIP5KRRpUWvYG4@1^+8$C#YkTrmnLcO8k9kFmE37G9f9!+JkH-rvERTMWpwYLj+oVNm43F_ir9?54Lzu{>caJb%sQ?J&6yHPm`8aQ%nqGa??;`!Y>u!#F2?6(i^F?diET8a@yW*S?=p1~~2y**<LX%C6S%4elhCpD~sBp#Nj??7z`k=aRX4-#>k|UEDxL42;=C!T-?k{Gk_@;U_vpEN3*hgQ^-i+x)7t(>-kl1k1MsaZ(>Pm;xoH4UWx#TDpJ|{+&TyKW7SmY!zK?Fc$m@NgR%K&i9jguh8O%ck|3_mmS12PJ_!I!WT7W;d~!=wGjN%N7)s6s}?J&S#Y);}H#4n8WmpX4+hb(lk(Q*_2%tT<Z_LDtZq1uN+i+3v?V#z!Uj5@k>6&a!siE}xA>6ettYp<DJReVVbbd96TxKbi0)O9ZC!P+IG}R(3}YdQJ}#esF7*Z(5~$t*YOP+E_1Q?G>X4#zS=fhTb7DGd+qGC>!hc65lnzJiEB*_SOhLCy9C~XIWtMzP(HJ&{WnIDi!wt8s4PZaq@O#oo8d>Z{9K2-Pjt^!(G}fk#o;y3jDd_z5C$l?{!56(nhaMsvr3$z)x(|#KKy`>YQUY=k(?pFqdr_3YW_3kwGT512EKO36XH$nIUv%HYY^lFDi367W(~dpBr;@05?<@d*5g>s2D|+p{cA$006ID72I@&<FibJK3Mzd=trjXOWnIPt9G%TK)7u4iq1ub3Ld#Fg81YfzkCJyiWz~8Qq=xIX&BOz29|OmI8K}M(h{EZK!S5==<<lpiWBn0dDS_sY&dUF7^4UruBy1989*j?<)So+zw+#QWSs<{wHl-Gn&8vjs|jR_>N`(0!s2}Rq{R5EAwo^kCTPBZ`BeYShIcP|WJB2ydMetSQ`^n446b60=HY2^7R5ENd#w>lIUAon^5PHCWAh*Q+qKt}Fy|YBO9|)FyqmJPj|AS<!7!~>+a?j(=DDx%XYH-8iP8II7Fn%_`opj{t+{>;PzfGk1nj(2w>|D1lIVE2k<@<?>PB7@-pTFL3p~wR3+=G+3AY<J;{*GVm~dN;o`1<^o*LSThkE{XQ4ob+2Y7wTzSgLEnnO*FXwc4Yg4GY9tP|cjcf;L!d8M*DD8-k&?bkpiMFw(}pAJ&sjxEscyCMf|P)9pQVM;Rod3B5xZ%CcG97dgXryN3ITmglFXx5&Or~hWxVp_X;ld0wJ_uVM5`wVS37CUy$MQT_m0BaVh()JUM-iE1r4+csq)A~j2=z86$yzz|P*meRHIt%5Vj-mSjUapG%*xK(iDf}iUxF&+NuUzW1ASZ}$)1dx+XV-`2P@Hjp6%@7ZPPCtVy}^#+V?-9_!^jL;F3*L(<QfQAUJA!@gui3PffS@GlqJgTy3FT9D&{}gVwT;fL?kn6E^l=K>Wh}6xy}ZFGT$PkOm#$HVQ>ZYWC6qS1-?^HjnJf3m2;sqgQELomEmQ_-6>C$R?(;DNc*?`Ij(Cmyc*asrt1^OR<(%xN*V&3A-xrh1}Y?wUQ^{n^QL1g^A1rD6Y~;mj16bb*07U*V&KD%Dr@AepkV~UAsd@e%cG-`n)b|}zhDalv{U^akQ}mjo3NFzo=yfCI`gz?l3>TzIhYsfT@GCD0G|2f-UZ8=>mE<oIDPnz0X%ev0)gsdAIb)a!j-FrRredzMz+=xpvL>mrF3*ogAjHB8Y)@_5V(TD8>2J5I4dc7w53PdW~VZE>=PWm11;OJJRNJ^XZqbKP>Ll4uPdn80VJE9vG&-_lk~q$^p3<kkNetIT6$frunQ++PnOAJUy$M~MXxc&G(Pxj6Y)A9Tvm>&0wk1b(5k}Vvj1%Iqs4&rvuN+g21KC$<8iPC
    'Aaru.Compression.Native.WinZipJpeg':('Aaru.Compression.Native.WinZipJpeg.lib',0), # static https://github.com/aaru-dps/Aaru.Compression.Native
    'unimplode6a':('unimplode6a.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/unimplode6a.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'ozunreduce':('ozunreduce.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/ozunreduce.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'ozunshrink':('ozunshrink.h','https://raw.githubusercontent.com/jsummers/oldunzip/refs/heads/master/ozunshrink.h',(0,b'#include <stdint.h>\n#include <stdlib.h>\ntypedef intptr_t off_t;')),
    'lpaq8_zzz':('lpaq8_zzz.h','https://raw.githubusercontent.com/WangXuan95/TinyZZZ/refs/heads/main/src/lpaq8CD.c'),
}
def get_lib(n:str):
    if DLDB[n][1] == 0: return os.path.join(LIBD + 'x',DLDB[n][0])
    elif DLDB[n][1] is None: return DLDB[n][0]
    p = os.path.join(LIBD,DLDB[n][0])
    if not os.path.exists(p):
        d = httpx.get(DLDB[n][1],follow_redirects=True).content
        if len(DLDB[n]) > 2:
            d = d.replace(b'\r',b'')
            for x in DLDB[n][2:]:
                if isinstance(x[0],int): d = d[:x[0]] + x[1] + d[x[0]:]
                else: d = d.replace(x[0],x[1])
        open(p,'wb').write(d)
    return p
def compile(quiet=False):
    cc = None
    env = os.environ.copy()
    ch = sha256()
    libs = set()
    xfncs = set()
    for x in sorted(HSFS):
        d = open(get_src(x),'rb').read().replace(b'\r',b'').strip(b'\n')
        ch.update(d)
        for fn in XEXR.findall(d): xfncs.add(fn.decode('utf-8'))
        for lns in IMPR.findall(d):
            for ln in lns.decode('utf-8').split(','): libs.add(ln.replace(' ','').replace('"',''))
    libs = [get_lib(x) for x in libs]
    ch = ch.digest()

    if sysconfig.get_config_var('CC'):
        print('WARNING: GCC is untested')
        cc = sysconfig.get_config_var('CC')
        cmd = ['-O3','-shared','-o',DLLP,*FS]
    elif sys.platform == 'win32':
        from setuptools import msvc
        env |= {x.upper():v for x,v in msvc.EnvironmentInfo('x64' if sys.maxsize > 2**32 else 'x86').return_env().items()}
        cmd  = ['/Ox','/GS-','/GR-','/Gs999999','/LD','/I',LIBD,'/TC',*FS,f'/Fe:{DLLP}','/link','/MANIFEST:NO','/MERGE:.rdata=.text','/OPT:REF','/OPT:ICF','/ALIGN:128',
                '/NODEFAULTLIB:MSVCRT','/IGNORE:4108','/IGNORE:4217','/IGNORE:4286'] + ['/EXPORT:' + x for x in xfncs]
        for p in env['PATH'].split(';'):
            if os.path.exists(p + '/cl.exe') and os.path.isfile(p + '/cl.exe'): cc = os.path.join(p,'cl.exe');break
    if cc is None: raise ValueError('No C compiler found')

    if os.path.exists(DLLP):
        os.replace(DLLP,DLLP + '.bak')
    pls = os.listdir()
    r = subprocess.call([cc] + cmd + [l for l in libs if l.endswith(('.a','.lib'))],env=env,stdout=-3 if quiet else None,stderr=-2 if quiet else None)
    ex = ('exp','lib','a','pdb','obj')
    for ex in ex:
        dnf = os.path.splitext(DLLP)[0] + '.' + ex
        if os.path.exists(dnf): remove(dnf)
    for p in os.listdir():
        if p.endswith(ex) and p not in pls: remove(p)
    if r:
        if os.path.exists(DLLP + '.bak'): os.rename(DLLP + '.bak',DLLP)
    elif os.path.exists(DLLP + '.bak'): remove(DLLP + '.bak')
    if not r: open(DLLP,'ab').write(ch)
    return r

if __name__ == '__main__':
    sys.exit(compile())
