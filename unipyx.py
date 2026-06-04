import os
if __name__ == '__main__':
    print('UniPyX')
    from sys import argv,exit

    if argv[1:] == ['-clean']:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        import re
        from shutil import rmtree
        assert os.path.exists('.gitignore'),".gitignore does not exist"

        nr = re.findall(r'!/bin/([^\n]+\.\w+|[^\n/\\]+(?=/\*))',open('.gitignore',encoding='utf-8').read()) + ['prodkeys/dev.keys']
        for x in os.listdir('bin'):
            if x in nr: continue
            p = 'bin/' + x
            if os.path.isfile(p): os.remove(p)
            elif os.path.isdir(p):
                for y in os.listdir(p):
                    tp = x + '/' + y
                    if tp in nr: continue
                    if os.path.isfile(p + '/' + y):
                        os.chmod(p + '/' + y,128)
                        os.remove(p + '/' + y)
                    else: rmtree(p + '/' + y)
                if not os.listdir(p): os.rmdir(p)

        exit()
    elif argv[1:] == ['-pip']:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        from lib.dldb import DLDB,pip
        db = DLDB()
        pl = []
        pn = []
        for x,y in db.pdb.items():
            if y.get('old'): continue
            pn.append(x)
            pl.append(y['pip'])
        print('Downloading:')
        print(', '.join(pn))
        pip(*pl)
        exit()

    scan = '-os' in argv
    if scan: argv.remove('-os')

    inp = argv[1]
    if not '://' in inp:
        inp = os.path.abspath(inp)
        assert os.path.exists(inp),'Input file does not exist'
        assert os.path.isfile(inp),'Input is not a file'

    if len(argv) > 2: out = os.path.abspath(argv[2])
    else:
        out = bout = 'output' if '://' in inp else os.path.splitext(inp)[0]
        c = 1
        while os.path.exists(out): out = bout + '_' + str(c);c += 1

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if scan:
        from lib.main import analyze
        ts,rts = analyze(inp,raw=True)

        print(inp)
        print('Processed:')
        for x in ts: print(x)
        print()
        print('Raw:')
        for x in sorted(set(rts)): print(x)
    else:
        from lib.main import main_extract as extract
        extract(inp,out,quiet=False,rs=True)
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    from lib.main import analyze,main_extract as extract,extract as sub_extract
