import os
if __name__ == '__main__':
    print('UniPyX')
    from sys import argv

    if argv[1:] == ['-clean']:
        import re
        from shutil import rmtree
        assert os.path.exists('.gitignore'),".gitignore does not exist"

        nr = re.findall(r'!/bin/([^\n]+\.\w+|[^\n/\\]+(?=/\*))',open('.gitignore',encoding='utf-8').read())
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

    scan = '-os' in argv
    if scan: argv.remove('-os')

    inp = os.path.abspath(argv[1])
    assert os.path.exists(inp),'Input file does not exist'

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
