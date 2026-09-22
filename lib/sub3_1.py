from .main import *

def extract3_1(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    match t:
        case 'Code Cruncher 3':
            db.try_custom()
            from lib.file import decompress
            d = readfile(i)
            asrt(d[:4] == b'\xF3KSA' and d[10] == 1 and d[0x19] == 0xC9)
            od = decompress(d[0x1A + int.from_bytes(d[11:13],'little'):],'cc3')
            if len(od) > len(d) :
                writefile(o + '/' + basename(i),od)
                return
        case 'install4j':
            db.try_custom()
            from lib.file import EXE
            from lib.crypto import decrypt
            f = EXE(i)
            f.seek(f.ovl_off)

            f.skip(0x14)
            sc = f.readu32()
            sd = {}
            for _ in range(sc):
                id = f.readu32()
                sd[id] = f.reads(f.readu32(),'utf-8')
            sc = f.readu32()
            for _ in range(sc):
                id = f.readu32()
                sd[id] = f.readutf16(f.readu32() // 2)
            sc = f.readu32()
            asrt(sc == 0,lambda:f.fmt(sc,'§@',back=4),err=NotImplementedError)
            writefile(o + '/.install4j/$strings.json',sd,'j',indent=4)

            idc = int(sd[2002])
            idn = sd[2003].split(';')
            asrt(len(idn) == idc or (len(idn) == idc + 1 and idn[-1] == ''))
            fs = []
            for ix in range(idc):
                s = f.readu64()
                fs.append((f.pos,s,idn[ix]))
                f.skip(s)

            tf = [x for x in fs if x[1] > 0x64 and x[2].lower().endswith('.jar')][0]
            f.seek(tf[0])
            k = decrypt(f.read(4),'xor',b'PK\3\4')
            asrt(all(k[0] == x for x in k[1:]))
            for fe in fs:
                f.seek(fe[0])
                d = decrypt(f.readc(fe[1]),'xor',k[0])
                writefile(o + '/.install4j/' + fe[2],d)
            f.close()

            if exists(o + '/.install4j/i4jparams.conf'):
                import re,ast,time
                import xml.etree.ElementTree as ET
                xml = ET.parse(o + '/.install4j/i4jparams.conf').getroot()
                lchs = {x.attrib['id']:x.attrib['file'] for x in xml.findall('launchers/launcher')}
                var = {
                    'installer':{
                        'sys.installationDir':o,
                        'timestamp':str(int(time.time()))
                    } | {x.attrib['name']:x.attrib['value'] for x in xml.findall('compilerVariables/variable')},
                    'i18n':{}
                }

                i18n = {}
                for x in xml.findall('languages/variable'):
                    lng = {}
                    for fn in ('messageFile','customLocalizationFile'):
                        fn = o + '/.install4j/' + x.get(fn,'?')
                        if exists(fn):
                            for l in readfile(fn,'rt',encoding=extname(fn)[1:]).split('\n'):
                                l = l.lstrip()
                                if not l or l.startswith('#'): continue
                                k,v = l.split('=',1)
                                lng[k] = ast.literal_eval('""" ' + v + ' """')[1:-1]
                    i18n[x.attrib['id']] = lng
                if 'en' in i18n: var['i18n'] = i18n['en']
                elif i18n: var['i18n'] = i18n[list(i18n)[0]]

                VRG = re.compile(r'(?<!\\)\$\{([\w\.\-]+):([\w\.\-]+)\}')
                def _VRG_sub(m): return var[m[1]][m[2]]
                def varstr(i:str):
                    if i is None: return None
                    return VRG.sub(_VRG_sub,i)

                asc = []
                reg = []
                srcs = []
                for x in xml.findall('applications/application[@id="installer"]'):
                    for y in x.findall('screens/screen'):
                        if y.find('java/object').attrib['class'] != 'com.install4j.runtime.beans.screens.InstallationScreen': continue
                        for ce in y.iterfind('.//java/object[@class="com.install4j.runtime.beans.actions.files.CopyFileAction"]'):
                            src = o + '/' + varstr(ce.find('void[@property="destinationFile"]/object/string').text)
                            srcs.append(src)
                            for cf in ce.findall('void[@property="files"]/array/void/object/string'):
                                cf = varstr(cf.text)
                                move(src + '/' + cf,o + '/' + cf)
                        for ae in y.iterfind('.//java/object[@class="com.install4j.runtime.beans.actions.desktop.CreateFileAssociationAction"]'):
                            asc.append({
                                'description':varstr(ae.find('void[@property="description"]/string').text),
                                'extension':varstr(ae.find('void[@property="extension"]/string').text),
                                'launcher':lchs[varstr(ae.find('void[@property="launcherId"]/string').text)],
                                'unix_icon':[o + '\\' + varstr(x.text) for x in ae.findall('void[@property="unixIconFile"]/object[@class="com.install4j.api.beans.ExternalFile"]/string')],
                                'win_icon':[o + '\\' + varstr(x.text) for x in ae.findall('void[@property="windowsIconFile"]/object[@class="com.install4j.api.beans.ExternalFile"]/string')],
                                'args':varstr(ae.find('void[@property="winAdditionalParameters"]/string').text),
                            })
                        for ge in y.iterfind('.//java/object[@class="com.install4j.runtime.beans.actions.registry.SetRegistryValueAction"]'):
                            reg.append({
                                'path':varstr(ge.find('void[@property="registryRoot"]/object/string').text) + '\\' + varstr(ge.find('void[@property="keyName"]/string').text),
                                'key':varstr(ge.find('void[@property="valueName"]/string').text),
                                'value':varstr(ge.find('void[@property="value"]/string').text),
                            })

                for x in srcs:
                    if not listdir(x): remove(x)
                if reg:
                    trg = {}
                    for x in reg:
                        if x['path'] not in trg: trg[x['path']] = {}
                        trg[x['path']][x['key']] = x['value']
                    od = ['Windows Registry Editor Version 5.00','']
                    for x,y in trg.items():
                        od.append('[' + x + ']')
                        for k,v in y.items(): od.append('"' + k + '"="' + v + '"')
                        od.append('')
                    writefile(o + '/.install4j/$registry.reg','\n'.join(od))
                if asc: writefile(o + '/.install4j/$associations.json',asc,'j',indent=4)
                if 'sys.timestamp' in var['installer']:
                    ts = int(var['installer']['sys.timestamp'])/1000
                    for fn in rldir(o): set_ftime(fn,ts)

            if exists(o + '/.install4j/jre.tar.gz'):
                import tarfile
                tarfile.open(o + '/.install4j/jre.tar.gz','r:gz').extractall(o + '/jre')
                remove(o + '/.install4j/jre.tar.gz')

            if fs: return
        case 'Themida':
            td = TmpDir(path=o)
            db.sandbox(['mal_unpack','/exe',td.link(i),'/timeout','10000','/dmode','3','/rebase','/imp','A','/dir',td],
                       sandbox_allow=[td,dirname(i)],sandbox_kill=True,fake_admin=True,cwd=td)

            mo = td + '/' + basename(i) + '.out'
            ofs = []
            if exists(mo) and listdir(mo):
                dmps = []
                for x in rldir(mo):
                    if x.endswith('dump_report.json'):
                        d = readfile(x,'j')
                        for y in d['dumps']:
                            p = dirname(x,2) + '/' + d['output_dir'] + '/'
                            dmps.append((p + y['dump_file'],y['dump_file'][len(y['module']) + 1:]))

                r = None
                # aoe = None
                if len(dmps) == 1:
                    of = o + '/' + dmps[0][1]
                    mv(dmps[0][0],of)

                    # f = xopen(of,'rb')
                    # f.seek(0x3C)
                    # f.seek(int.from_bytes(f.read(4),'little'))
                    # if f.read(4) == b'PE\0\0':
                    #     f.seek(0x10,1)
                    #     ops = int.from_bytes(f.read(2),'little')
                    #     f.seek(2,1)
                    #     if ops >= 0x14 and f.read(2) == b'\x0B\x01':
                    #         aoeo = f.seek(14,1)
                    #         aoe = int.from_bytes(f.read(4),'little')
                    # f.close()
                elif len(dmps) == 0: r = 1
                else:
                    for ix,fe in enumerate(dmps): mv(fe[0],ofs[-1])
            else: r = 1
            td.destroy()

            # if r is None and not aoe is None and aoe == 0:
            #     pass

            return r
        case 'Pyckage':
            db.try_custom()
            import tokenize,ast,io
            from lib.crypto import decrypt
            from lib.file import decompress
            d = readfile(i,'rt')

            if d.startswith('from lzma import decompress as x;'):
                eq = '='
                hd,d = d.split('d' + eq,1)
                b85 = ';from base64 import b85decode as x1;' in hd
            elif d.startswith('dc=lambda:(x:=__import__("lzma").decompress,'):
                eq = ':='
                hd,d = d.split('d' + eq,1)
                b85 = 'x1:=__import__("base64").b85decode,' in hd
            toks = tokenize.generate_tokens(io.StringIO(d).readline)
            for tok in toks:
                if tok.type == tokenize.STRING and tok.string.startswith('b'):
                    pl = ast.literal_eval(tok.string)
                    break
            else: return 1
            if b85:
                pl = decrypt(pl,'base85')
                asrt(next(toks).string == ')')

            asrt(next(toks).string == ',')
            fmt = int(next(toks).string)
            asrt(next(toks).string == ',' and next(toks).string == 'filters' and next(toks).string == '=')
            flt = [next(toks).string]
            asrt(flt[0] == '[')
            for tok in toks:
                flt.append(tok.string)
                if tok.type == tokenize.OP and tok.string == ']': break
            else: return 1
            asrt(next(toks).string == ')')
            pl = decompress(pl,'lzma_raw',format=fmt,filters=ast.literal_eval(''.join(flt)))

            while next(toks).string != eq: pass
            fs = [next(toks).string]
            asrt(fs[0] == '{')
            for tok in toks:
                fs.append(tok.string)
                if tok.type == tokenize.OP and tok.string == '}': break
            else: return 1
            fs = ast.literal_eval(''.join(fs))

            l = 0
            for fn,of in fs.items():
                writefile(o + '/' + fn,pl[l:of])
                l = of

            del d,pl
            if fs: return
        case 'InstallShield 2000':
            db.try_custom()
            import re
            from lib.file import ext_exe
            e = ext_exe(i,fast_load=False)

            txt = e.SECTIONS['.text'].get_data()
            drs = e.DIRECTORY_ENTRY_RESOURCE.entries
            rsc = {}
            while drs:
                res = drs.pop(0)
                if res.id is None: drs.extend(res.directory.entries)
                else: rsc[res.id] = res
            for x in re.findall(rb'\x68([\x00-\xFF]{4})\x6A\x00\xFF\xD6\x8B[\x00-\xFF]*?\x6A\x00\x68\x01\x10\x00\x00\x68([\x00-\xFF]{4})',txt):
                fn = e.get_string_at_rva(int.from_bytes(x[1],'little') - e.OPTIONAL_HEADER.ImageBase).decode('ascii')
                d = rsc[int.from_bytes(x[0],'little')].directory.entries[0].data.struct
                writefile(o + '/' + fn,e.get_data(d.OffsetToData,d.Size))

            del e
            if listdir(o): return
        case 'FWKCS Content Signature System':
            db.try_custom()
            from lib.file import File
            from lib.crypto import decrypt
            f = File(i,endian='<')
            asrt(f.readu8() == 0xE9)

            f.skip(f.readu16())
            f.readu(b'\xCD\x21',maxl=0x20,include=True,eoferr=True)
            asrt(f.readu8() == 0x73)
            f.skip(f.readu8())

            adrs = {}
            for _ in range(5):
                asrt(f.readu8() == 0xBE)
                adr = f.readu16()
                if f.readu8() != 0xB0:
                    f.back(1)
                    break
                adrs[adr] = f.readu8()
                if f.readu8() != 0xE8:
                    f.back(1)
                    break
                f.skip(2)

            f.readu(b'\x8A\x04',maxl=0x40,include=True,eoferr=True)
            asrt(f.readu8() == 0x86)
            f.skip(1)
            asrt(f.readu8() == 0x04)
            k = f.readu8()
            d = f.peek(0x80,offset=[adr - 0x100])
            if adr in adrs:
                d = decrypt(d,'xor',adrs[adr])
            d = decrypt(d,'rlcg',k)
            writefile(f'{o}/{adr:04X}.bin',d)
            f.close()
            return
        case 'BlackEnergy Crypter':
            db.try_custom()
            from lib.file import EXE,decompress
            from lib.crypto import decrypt
            e = EXE(i)
            e.seek(e.secs['.data'][0])

            us = e.readu32()
            ecs = e.readu32()
            k = e.readu32()
            d = e.read(e.secs['.data'][2] - e.pos)
            e.close()
            if ecs:
                ed,d = d[:ecs],d[ecs:]
                for p in range(0xFFF,-1,-1):
                    ed = decrypt(ed,'blackenergy_rc4',(k ^ p).to_bytes(4,'little'))
                d = ed + d
            asrt(d[:1] == b'M' and d[2:3] == b'Z' and d[1] & 0x80 == 0)
            d = decompress(d,'aplib',usize=us)
            asrt(len(d) == us,len(d),us,d[:0x20])

            writefile(o + '/' + basename(i),d)
            if d: return
        case 'ASC2COM':
            od = rldir(o)
            run(['deark','-m',DEARKMP[t],'-opt','text:encconv=0','-od',o,i])
            for x in rldir(o):
                if not x in od:
                    mv(x,o + '/' + tbasename(i) + '.txt')
                    return
        case 'PKLITE32':
            STRIP = {b'.pklstb\0',b'.relo2\0\0'}

            db.try_custom()
            from lib.crypto import crc_hash
            from lib.file import ext_exe,decompress
            d = readfile(i)
            e = ext_exe(d,fast_load=True)

            imb = e.OPTIONAL_HEADER.ImageBase
            ois = e.OPTIONAL_HEADER.SizeOfImage
            dd = getattr(e.OPTIONAL_HEADER,'DATA_DIRECTORY',[])
            if len(dd) > 4 and dd[4].VirtualAddress and dd[4].Size:
                ois = min(ois,dd[4].VirtualAddress)
            ep = e.get_offset_from_rva(e.OPTIONAL_HEADER.AddressOfEntryPoint)
            sal = e.OPTIONAL_HEADER.SectionAlignment or 1
            fal = e.OPTIONAL_HEADER.FileAlignment or 1
            soh = e.OPTIONAL_HEADER.SizeOfHeaders
            soh += -soh % fal
            mxva = max([x.VirtualAddress + max(x.Misc_VirtualSize,x.SizeOfRawData) for x in e.sections])
            mxva += -mxva % sal
            miva = min([x.VirtualAddress for x in e.sections]) - soh
            assert miva >= 0

            asrt(d[ep] == d[ep + 5] == d[ep + 10] == 0x68 and d[ep + 15] == 0xE8 and d[ep + 20] == 0xE9)
            dso = e.get_offset_from_rva(int.from_bytes(d[ep + 1:ep + 5],'little') - imb)
            oep = e.get_rva_from_offset(ep + 20) + 5 + int.from_bytes(d[ep + 21:ep + 25],'little',signed=True)

            p = dso
            asrt(d[p:p + 4] == b'\x44\x33\x22\x11')
            p += 8
            oimb = int.from_bytes(d[p:p + 4],'little');p += 4
            bc = int.from_bytes(d[p:p + 4],'little');p += 4
            p += 4

            zmi = max(miva - 0x8000,0)
            zmem = bytearray(max(mxva - zmi,0x8000))
            zmem[:soh] = d[:soh]
            for sec in e.sections:
                va = sec.VirtualAddress - zmi
                sd = sec.get_data()[:sec.Misc_VirtualSize]
                if len(sd) < sec.Misc_VirtualSize: sd += bytes(sec.Misc_VirtualSize - len(sd))
                zmem[va:va + sec.Misc_VirtualSize] = sd

            bs = []
            for _ in range(bc):
                asrt(d[p:p + 4] == b'\x44\x33\x22\x11');p += 4
                us = int.from_bytes(d[p:p + 4],'little');p += 4
                p += 4
                dva = int.from_bytes(d[p:p + 4],'little');p += 4
                zs = int.from_bytes(d[p:p + 4],'little');p += 4

                if zs > 0x8000:
                    raise NotImplementedError('deflate64 with zdict (https://codeberg.org/miurahr/inflate64/issues/16)')
                else:
                    zd = zmem[dva - 0x8000 - zmi:dva - zmi]
                    bd = decompress(d[p:p + zs],'deflate',usize=us,dict=bytes(0x8000 - len(zd)) + zd);p += zs
                    bd = bd[:us]
                    bd += bytes(us - len(bd))
                    zmem[dva - zmi:dva - zmi + us] = bd
                bs.append((bd,dva))

            mxva -= miva
            mem = bytearray(mxva)
            mem[:soh] = d[:soh]

            for sec in e.sections:
                if sec.SizeOfRawData > 0 and sec.PointerToRawData > 0:
                    va = sec.VirtualAddress - miva
                    if sec.Name in STRIP:
                        if va < len(mem): mem = mem[:va]
                        continue
                    sz = sec.SizeOfRawData
                    sz += -sz % fal
                    mem[va:va + sz] = d[sec.PointerToRawData:sec.PointerToRawData + sz]
            for bd,va in bs:
                va -= miva
                mem[va:va + len(bd)] = bd
            bs = [(x[1] - miva,len(x[0])) for x in bs]

            whtl = []
            dba = cba = csz = isz = usz = 0
            for sec in e.sections:
                if sec.Name in STRIP:
                    whtl.append((sec.get_file_offset(),sec.sizeof()))
                    continue

                va = sec.VirtualAddress - miva
                sec.VirtualAddress = va
                sec.SizeOfRawData = sec.Misc_VirtualSize + -sec.Misc_VirtualSize % fal
                sec.PointerToRawData = sec.VirtualAddress + -sec.VirtualAddress % fal

                if sec.Characteristics & 0x20:
                    if cba == 0: cba = va
                    else: cba = min(cba,va)
                    csz += sec.SizeOfRawData
                if sec.Characteristics & 0x40:
                    if dba == 0: dba = va
                    else: dba = min(dba,va)
                    isz += sec.SizeOfRawData
                if sec.Characteristics & 0x80:
                    usz += sec.SizeOfRawData
            asrt(cba | dba > 0)

            e.FILE_HEADER.NumberOfSections = len(e.sections) - len(whtl)
            e.OPTIONAL_HEADER.ImageBase = oimb
            e.OPTIONAL_HEADER.AddressOfEntryPoint = oep
            e.OPTIONAL_HEADER.BaseOfCode = cba
            e.OPTIONAL_HEADER.BaseOfData = dba
            e.OPTIONAL_HEADER.SizeOfImage = len(mem)
            e.OPTIONAL_HEADER.SizeOfCode = csz
            e.OPTIONAL_HEADER.SizeOfInitializedData = isz
            e.OPTIONAL_HEADER.SizeOfUninitializedData = usz
            e.OPTIONAL_HEADER.CheckSum = 0

            dd = getattr(e.OPTIONAL_HEADER,'DATA_DIRECTORY',[])
            if len(dd) > 4 and dd[4].VirtualAddress and dd[4].Size:
                dd[4].VirtualAddress = (dd[4].VirtualAddress - ois) + len(mem)
            mem += d[ois:]
            del d

            mem[:soh] = e.write()[:soh]
            chko = e.OPTIONAL_HEADER.get_file_offset() + 0x40
            del e
            for wh in whtl:
                mem[wh[0]:wh[0] + wh[1]] = bytes(wh[1])
            mem[chko:chko + 4] = crc_hash(mem,'pe').to_bytes(4,'little')

            writefile(o + '/' + basename(i),mem)
            return
        case 'Action Replay Code':
            db.try_custom()
            from lib.pyob import PyOBinX
            keys = PyOBinX.dl('keys',db)
            import struct
            from lib.crypto import decrypt,crc_hash
            cd = decrypt(readfile(i,'rt'),'ar_alpha')
            cd = list(struct.unpack(f'<{len(cd)}I',decrypt(struct.pack(f'<{len(cd)}I',*cd),'des_ecb',keys.wait()['ar'])))

            crc = cd[0] >> 28
            cd[0] &= 0x0FFFFFFF
            asrt(crc == crc_hash(cd,'crc16_4_ar'))
            writefile(o + '/' + basename(i),'\n'.join(f'{cd[ix]:08X} {cd[ix+1]:08X}' for ix in range(0,len(cd),2)))
            if cd: return

    return 1
