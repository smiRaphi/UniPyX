import os
if __name__ == '__main__':
    print('UniPyX')
    from sys import argv,exit

    if argv[1:] == ['-clean']:
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
                    if os.path.isfile(p + '/' + y): os.remove(p + '/' + y)
                    else: rmtree(p + '/' + y)
                if not os.listdir(p): os.rmdir(p)

        exit()
    elif argv[1:] == ['-pip']:
        from lib.dldb import DLDB
        db = DLDB()
        for x in db.pdb:
            if not db.pdb[x].get('old'): db.pip(x)
        exit()

    scan = '-os' in argv
    if scan: argv.remove('-os')

    inp = os.path.abspath(argv[1])
    assert os.path.exists(inp),'Input file does not exist'
    assert os.path.isfile(inp),'Input is not a file'

    if len(argv) > 2: out = os.path.abspath(argv[2])
    else:
        out = os.path.splitext(inp)[0]
        c = 1
        while os.path.exists(out): out = os.path.splitext(inp)[0] + '_' + str(c);c += 1

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
