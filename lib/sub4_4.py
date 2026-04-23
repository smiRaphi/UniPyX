from lib.main import *

def extract4_4(inp:str,out:str,t:str):
    run = db.run
    i = inp
    o = out

    match t:
        case 'Pixar USD Crate': raise NotImplementedError
        case 'Quest3D ZICB':
            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')

            of = o + '/' + basename(i)
            while f:
                n = f.read(4).decode('latin-1')
                s = f.readu32()
                ep = f.pos + s

                match n:
                    case 'ACTF'|'ZINS'|'ZIOS': pass
                    case 'ZICB':
                        if exists(of): raise FileExistsError
                        writefile(of,f.decompress(s,'zlib'))
                    case _: raise NotImplementedError(f'{n} ({s}) @ 0x{f.pos:08X}')

                f.seek(ep)

            f.close()
            if exists(of): return
        case 'Surreal Software SRSC':
            TMAP = {
                0x200:'node',
                0x203:'mesh',
                0x204:'uv',
                0x207:'pos',
                0x208:'skl',
                0x211:'parent',
                0x214:'anim',
                0x216:'vert',
                0x302:'sndinf',
                0x303:'pcm',
                0x305:'sndfmt',
                0x402:'lvl',
                0x501:'mdlinf',
                0x502:'mdl',
            }

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'SRSC' and f.readu8() == f.readu8() == 1

            of = f.readu32()
            c = f.readu16()
            f.padc(4)
            f.seek(of)
            fs = [(f.readu16(),f.readu16(),f.readu16(),f.readu32(),f.readu32()) for _ in range(c)]
            for fe in fs:
                f.seek(fe[3])
                ex = TMAP.get(fe[0],f'{fe[0]:03X}')
                writefile(f'{o}/{fe[2]:02X}/{fe[1]:02X}.{ex}',f.readc(fe[4]))

            f.close()
            if fs: return
        case 'Silent Hill PAK':
            TMAP = (
                'MYS','SCT','MDL','MAT','SYT',
                'GIN','PIN','XWB','XSB','CSV',
                None ,'DDB','TXT','HKC',None ,
                'STR','PTM','PGP','CMF','PHP',
                'MTM','XML','GAT','CAP','FTS',
                'XML','STR','APK','HKS','HKA',
                'HCL','SES','XGS','XWS','HKP',
                'NVM',None ,None ,None ,#'BIK',
                'OGG','SAC','XMB','GAB','CAB','FTB',
            )

            if db.print_try: print('Trying with custom extractor')
            from lib.file import File
            f = File(i,endian='<')
            assert f.read(4) == b'PAK_' and f.readu32() == 1

            c = f.readu32()
            f.skip(4)
            fs = []
            for _ in range(c):
                fe = [f.read(0x40).rstrip(b'\0').decode('ascii'),f.readu32(),f.readu32(),f.readu32(),f.reads32()]
                assert f.reads16() == -1
                fe.extend([f.readu16(),f.readu32()])
                if fe[4] == -1: assert fe[3] == fe[6] == 0,f.pos - 0x58
                fs.append(fe)

            for fe in fs:
                if fe[5] > len(TMAP) or TMAP[fe[5]] is None: ex = f'{fe[5]:02X}'
                else: ex = TMAP[fe[5]]
                if fe[4] == -1:
                    d = b''
                    ex += '.deleted'
                else:
                    f.seek(fe[3])
                    if fe[1] & 0x10:
                        assert fe[6] > 12 and f.read(4) == b'LZO\0'
                        us,zs = f.readu32('>'),f.readu32('>')
                        d = f.decompress(zs,'lzo1x',usize=us,db=db)
                    else: d = f.readc(fe[6])
                fn = f'{o}/{fe[0]}.{ex}'
                writefile(fn,d)
                if fe[2] > 0:
                    set_ctime(fn,fe[2])

            f.close()
            if fs: return

    return 1
