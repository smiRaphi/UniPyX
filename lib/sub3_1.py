from .main import *

def extract3_1(inp:str,out:str,t:str) -> bool:
    run = db.run
    i = inp
    o = out

    match t:
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
            import signal
            td = TmpDir(path=o)
            db.sandbox(['mal_unpack','/exe',td.link(i),'/timeout','10000','/dmode','3','/rebase','/imp','A','/dir',td],
                       sandbox_allow=[td,dirname(i)],sandbox_kill=True,cwd=td)

            mo = td + '/' + basename(i) + '.out'
            ofs = []
            if exists(mo) and listdir(mo):
                pids = set()
                for x in rldir(mo):
                    if x.endswith(('dump_report.json','scan_report.json')): pids.add(int(readfile(x,'j')['pid']))
                for pid in pids:
                    try: os.kill(int(pid),signal.SIGTERM if os.name == 'nt' else signal.SIGKILL)
                    except ProcessLookupError: pass
                    except OSError as e:
                        if e.winerror != 87: raise
                    except:
                        print(', '.join(pids))
                        td.destroy()
                        raise

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

    return 1
