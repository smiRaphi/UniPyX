from .main import *

def extract1_1(inp:str,out:str,t:str) -> bool:
    i,o = inp,out
    run = db.run

    match t:
        case 'Unified Diff':
            db.try_custom()
            import shlex
            from lib.crypto import decrypt
            from lib.file import decompress
            d = readfile(i,'rt').splitlines(True)

            c = p = 0
            fs = {}
            while True:
                cc = []
                for sp in range(p,len(d)):
                    if len(d) - sp < 2:
                        p = -1
                        break
                    if d[sp].startswith('--- ') and d[sp+1].startswith('+++ '):
                        p = sp
                        break
                    cc.append(d[sp])
                else: p = -1

                if len(cc) > 4 and cc[0].startswith('diff --git ') and cc[2].rstrip('\r\n') in {'GIT binary patch','GIT binary hexdump (non-reusable, for human eyes only) patch'}:
                    bty = cc[2].rstrip('\r\n')
                    if bty == 'GIT binary patch': bty = 'b'
                    elif bty == 'GIT binary hexdump (non-reusable, for human eyes only) patch':
                        # https://superuser.com/a/1741622
                        bty = 'x'

                    ps = shlex.split(cc[0])
                    mip,plp = ps[2].strip('" '),ps[3].strip('" ')
                    if not mip in fs: fs[mip] = [[],bytearray()]
                    if not plp in fs: fs[plp] = [[],bytearray()]
                    xcc = cc[:2]
                    cp = 3
                    sbc = 0
                    while cp < len(cc):
                        if cc[cp].startswith('delta ') and cc[cp][6:].rstrip('\r\n').isdigit():
                            vs = int(cc[cp].split()[1]);cp += 1
                            vl = []
                            while cp < len(cc):
                                l = cc[cp];cp += 1
                                if not l.rstrip('\r\n'): break
                                vl.append(l)

                            vp = plp if sbc == 0 else mip
                            if vp != '/dev/null':
                                if bty == 'b': vl = decompress(decrypt(vl,'git_b85'),'zlib')[:vs]
                                elif bty == 'h': vl = bytes.fromhex(''.join([x.split('|')[0] for x in vl]))
                                fs[vp][1] = read_pack_delta(vl,fs[vp][1])
                            sbc += 1
                        elif cc[cp].startswith('literal ') and cc[cp][6:].rstrip('\r\n').isdigit():
                            vs = int(cc[cp].split()[1]);cp += 1
                            vl = []
                            while cp < len(cc):
                                l = cc[cp];cp += 1
                                if not l.rstrip('\r\n'): break
                                vl.append(l)

                            vp = plp if sbc == 0 else mip
                            if vp != '/dev/null':
                                if bty == 'b': vl = decompress(decrypt(vl,'git_b85'),'zlib')[:vs]
                                elif bty == 'h': vl = bytes.fromhex(''.join([x.split('|')[0] for x in vl]))
                                fs[vp][1] = decompress(vl,'zlib')[:vs]
                            sbc += 1
                        else: xcc.append(cc[cp]);cp += 1
                    cc = xcc

                if p == -1:
                    if cc: writefile(o + '/$comments/footer.txt',''.join(cc))
                    break
                if cc: writefile(f'{o}/$comments/{c:03d}.txt',''.join(cc))
                c += 1

                mip,*mit = d[p][4:].rstrip('\r\n').split('\t',1);p += 1
                plp,*plt = d[p][4:].rstrip('\r\n').split('\t',1);p += 1
                if not mip in fs: fs[mip] = [mit]
                else: fs[mip][0].extend(mit)
                if not plp in fs: fs[plp] = [plt]
                else: fs[plp][0].extend(plt)

                while p < len(d):
                    if not d[p].startswith('@@ '): break
                    ml,pl = d[p][3:-1].split('@@',1)[0].strip().split();p += 1
                    asrt(ml[0] == '-' and pl[0] == '+')
                    mlo,mll = ml[1:].split(',',1)
                    plo,pll = pl[1:].split(',',1)
                    mlo = int(mlo);mll = int(mll)
                    plo = int(plo);pll = int(pll)
                    mb = []
                    pb = []
                    while (len(mb) < mll or len(pb) < pll) and p < len(d):
                        l = d[p];p += 1
                        if l[0] == ' ':
                            mb.append(l[1:])
                            pb.append(l[1:])
                        elif l[0] == '-': mb.append(l[1:])
                        elif l[0] == '+': pb.append(l[1:])
                        else: raise ValueError(l.rstrip('\r\n'))
                    if d[p].rstrip('\r\n') == '\\ No newline at end of file':
                        if mb: mb[-1] = mb[-1].rstrip('\r\n')
                        if pb: pb[-1] = pb[-1].rstrip('\r\n')
                        p += 1
                    fs[mip].append((mlo - 1,mb))
                    fs[plp].append((plo - 1,pb))

            fs.pop('/dev/null',None)
            for x in fs:
                if len(fs[x]) == 2 and isinstance(fs[x][1],bytearray): d = fs[x][1]
                else:
                    ls = []
                    eol = '\r\n' if len(fs[x]) > 1 and len(fs[x][1][1]) > 0 and fs[x][1][1][0].endswith('\r\n') else '\n'
                    for yo,yd in fs[x][1:]:
                        if (yo+len(yd)) > len(ls): ls.extend([eol]*(yo+len(yd)-len(ls)))
                        for ix,l in enumerate(yd): ls[yo+ix] = l
                    d = ''.join(ls)
                writefile(o + '/' + sanitize_relative(x),d,ct=max([str2unix(ts) for ts in fs[x][0]],default=None))

            if fs: return
        case 'Context Diff':
            db.try_custom()
            d = readfile(i,'rt').splitlines(True)

            c = p = 0
            fs = {}
            while True:
                cc = []
                for sp in range(p,len(d)):
                    if len(d) - sp < 3:
                        p = -1
                        break
                    if d[sp].startswith('*** ') and d[sp+1].startswith('--- ') and d[sp+2].rstrip('\r\n') == '***************':
                        p = sp
                        break
                    cc.append(d[sp])
                else: p = -1
                if p == -1:
                    if cc: writefile(o + '/$comments/footer.txt',''.join(cc))
                    break
                if cc: writefile(f'{o}/$comments/{c:03d}.txt',''.join(cc))
                c += 1

                mip,*mit = d[p][4:].rstrip('\r\n').split('\t',1);p += 1
                plp,*plt = d[p][4:].rstrip('\r\n').split('\t',1);p += 1
                if not mip in fs: fs[mip] = [mit]
                else: fs[mip][0].extend(mit)
                if not plp in fs: fs[plp] = [plt]
                else: fs[plp][0].extend(plt)
                p += 1

                while p < len(d):
                    l = d[p].rstrip('\r\n')
                    if not ((l.startswith('*** ') and l.endswith(' ****')) or (l.startswith('--- ') and l.endswith(' ----'))): break
                    ty = l[0]
                    vlo,vll = l[4:-5].split(',',1);p += 1
                    vlo = int(vlo);vll = int(vll)
                    vb = []

                    for sp in range(p,p + vll):
                        if d[sp][0] not in ' !+' or d[sp][1] != ' ': raise ValueError(d[sp].rstrip('\r\n'))
                        vb.append(d[sp][2:])
                    p += vll
                    if d[p].rstrip('\r\n') == '\\ No newline at end of file':
                        if vb: vb[-1] = vb[-1].rstrip('\r\n')
                        p += 1
                    fs[mip if ty == '*' else plp].append((vlo - 1,vb))

            fs.pop('/dev/null',None)
            for x in fs:
                ls = []
                eol = '\r\n' if len(fs[x]) > 1 and len(fs[x][1][1]) > 0 and fs[x][1][1][0].endswith('\r\n') else '\n'
                for yo,yd in fs[x][1:]:
                    if (yo+len(yd)) > len(ls): ls.extend([eol]*(yo+len(yd)-len(ls)))
                    for ix,l in enumerate(yd): ls[yo+ix] = l
                writefile(o + '/' + sanitize_relative(x),''.join(ls),ct=max([str2unix(ts) for ts in fs[x][0]],default=None))

            if fs: return
        case 'Normal Diff':
            db.try_custom()
            d = readfile(i,'rt').splitlines(True)

            p = 0
            ml,pl = [],[]
            while p < len(d):
                h = d[p].rstrip('\r\n');p += 1
                if not h: continue
                if 'c' in h: s = h.split('c')
                elif 'a' in h: s = h.split('a')
                else: raise ValueError(h)

                s1,s2 = s[0].split(','),s[1].split(',')

                if 'c' in h:
                    if len(s1) == 2: c = int(s1[1]) - int(s1[0]) + 1
                    else: c = 1
                    l = []
                    for _ in range(c):
                        if p >= len(d): break
                        l.append(d[p]);p += 1
                    asrt(all(x.startswith('< ') for x in l),p)
                    ml.append((int(s1[0]) - 1,l))
                    if p >= len(d): continue
                    asrt(d[p].rstrip('\r\n') == '---',p);p += 1

                if len(s2) == 2: c = int(s2[1]) - int(s2[0]) + 1
                else: c = 1
                l = []
                for _ in range(c):
                    if p >= len(d): break
                    l.append(d[p]);p += 1
                asrt(all(x.startswith('> ') for x in l),p)
                pl.append((int(s2[0]) - 1,l))

            for x,fn in ((ml,'input.txt'),(pl,'output.txt')):
                ls = []
                eol = '\r\n' if len(x) > 1 and len(x[0][1]) > 0 and x[0][1][0].endswith('\r\n') else '\n'
                for yo,yd in x:
                    if (yo+len(yd)) > len(ls): ls.extend([eol]*(yo+len(yd)-len(ls)))
                    for ix,l in enumerate(yd): ls[yo+ix] = l[2:]
                writefile(o + '/' + fn,''.join(ls))

            if ml or pl: return
        case 'Ed Script Diff':
            db.try_custom()
            d = readfile(i,'rt').splitlines(True)

            p = 0
            vl = []
            while p < len(d):
                h = d[p].rstrip('\r\n');p += 1
                if not h: continue
                asrt(h[-1] in 'ac',h)
                vo = int(h[:-1].split(',',1)[0])
                if ',' in h: vo -= 1
                else: vo += 1
                l = []
                while p < len(d) and d[p].rstrip('\r\n') != '.':
                    l.append(d[p]);p += 1
                p += 1
                vl.append((vo,l))

            ls = []
            eol = '\r\n' if len(vl) > 1 and len(vl[0][1]) > 0 and vl[0][1][0].endswith('\r\n') else '\n'
            for yo,yd in vl:
                if (yo+len(yd)) > len(ls): ls.extend([eol]*(yo+len(yd)-len(ls)))
                for ix,l in enumerate(yd): ls[yo+ix] = l
            writefile(f'{o}/{tbasename(i)}.txt',''.join(ls))
            if vl: return
        case 'RCS Diff':
            db.try_custom()
            d = readfile(i,'rt').splitlines(True)

            p = 0
            vl = []
            while p < len(d):
                h = d[p].rstrip('\r\n');p += 1
                if not h: continue
                asrt(h[0] in 'ad',h)
                vo,vs = h[1:].split(' ',1)
                vo,vs = int(vo),int(vs)
                if h[0] == 'd': continue

                l = []
                for _ in range(vs):
                    if p >= len(d): break
                    l.append(d[p]);p += 1
                vl.append((vo,l))

            ls = []
            eol = '\r\n' if len(vl) > 1 and len(vl[0][1]) > 0 and vl[0][1][0].endswith('\r\n') else '\n'
            for yo,yd in vl:
                if (yo+len(yd)) > len(ls): ls.extend([eol]*(yo+len(yd)-len(ls)))
                for ix,l in enumerate(yd): ls[yo+ix] = l
            writefile(f'{o}/{tbasename(i)}.txt',''.join(ls))
            if vl: return

    return 1

def read_pack_delta(i:bytes,ib:bytearray=None):
    from lib.file import File
    f = File(i,endian='>')

    o = bytearray(f.readvlq())
    if not ib is None: o[:len(ib)] = ib
    osz = f.readvlq()

    p = 0
    while f:
        fl = f.readu8()
        if fl & 0x80:
            of = sz = 0
            for ix in range(4):
                if fl & (1 << ix): of |= f.readu8() << (8 * ix)
            for ix in range(3):
                if fl & (1 << (ix + 4)): sz |= f.readu8() << (8 * ix)
            if sz == 0: sz = 0x10000
            o[p:p+sz] = o[of:of+sz]
        else:
            sz = fl & 0x7F
            o[p:p+sz] = f.readc(sz)
        p += sz

    del f
    return o[:osz]
