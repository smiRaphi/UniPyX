import os
if __name__ == '__main__':
    from sys import argv

    scan = '-os' in argv
    if scan: argv.remove('-os')

    inp = os.path.realpath(argv[1])
    assert os.path.exists(inp),'Input file does not exist'

    if len(argv) > 2: out = os.path.realpath(argv[2])
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
    from lib.main import main_extract as extract
