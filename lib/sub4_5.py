from lib.main import *

def extract4_5(inp:str,out:str,t:str):
    i,o = inp,out

    match t:
        case 'Retro Engine RSDKv3':
            K1,K2 = b"4RaS9D7KaEbxcp2o5r6t",b"3tRaUxLmEaSn"
            if db.print_try: print('Trying with custom extractor')
            from lib.crypto import decrypt
            from lib.file import File
            f = File(i,endian='<')

            hs = f.readu32()
            dc = f.readu16()
            ds = [(decrypt(f.read(f.readu8()),'inv_len').decode('utf-8'),hs + f.readu32()) for _ in range(dc)]
            ds.append((0,f.size))
            for ix,de in enumerate(ds[:-1]):
                f.seek(de[1])
                xof = ds[ix+1][1]
                while f < xof:
                    fn = decrypt(f.read(f.readu8()),'inv').decode('utf-8')
                    writefile(o + '/' + de[0] + fn,decrypt(f.readc(f.readu32()),'rsdk3',K1,K2))

            f.close()
            if de: return
        case 'Retro Engine RSDKv4':
            KEY = (0xAAAAAAAB,0x24924925)

            if db.print_try: print('Trying with custom extractor')
            from lib.crypto import decrypt,HashLib
            hl = HashLib.dl('rsdk',db,fmt=lambda x:x.lower(),encoding='utf-8')
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(6) == b'RSDKvB')

            c = f.readu16()
            fs = []
            for _ in range(c):
                fe = [f.readu128(),f.readu32()]
                sz = f.readu32()
                fs.append((*fe,sz & 0x7FFFFFFF,sz & 0x80000000))

            hl.wait()
            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                if fe[3]: d = decrypt(d,'rsdk4',*KEY)
                if fe[0] in hl: fn = hl[fe[0]]
                else:
                    ex = guess_ext(d)
                    fn = f'$unk/{fe[0]:032X}.{ex}'
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return
        case 'Retro Engine RSDKv5':
            if db.print_try: print('Trying with custom extractor')
            from lib.crypto import decrypt,HashLib
            hl = HashLib.dl('rsdk',db,fmt=lambda x:x.lower(),encoding='utf-8')
            from lib.file import File
            f = File(i,endian='<')
            asrt(f.read(5) == b'RSDKv' and f.read(1) in b'345')

            c = f.readu16()
            fs = []
            for _ in range(c):
                fe = [f.readu128(),f.readu32()]
                sz = f.readu32()
                fs.append((*fe,sz & 0x7FFFFFFF,sz & 0x80000000))

            hl.wait()
            for fe in fs:
                f.seek(fe[1])
                d = f.readc(fe[2])
                if fe[0] in hl:
                    fn = hl[fe[0]]
                    if fe[3]: d = decrypt(d,'rsdk5',fn)
                else:
                    fn = f'$unk/{fe[0]:032X}.'
                    if fe[3]: fn += 'enc'
                    else: fn += guess_ext(d)
                writefile(o + '/' + fn,d)

            f.close()
            if fs: return

    return 1
