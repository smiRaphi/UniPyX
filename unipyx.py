import os,sys
sys.argv = [sys.argv[0]] + [os.path.realpath(x) for x in sys.argv[1:]]
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from lib.main import main_extract as extract

if __name__ == '__main__':
    from sys import argv

    inp = argv[1]
    assert os.path.exists(inp),'Input file does not exist'
    if len(argv) > 2: out = argv[2]
    else:
        out = os.path.splitext(inp)[0]
        c = 1
        while os.path.exists(out): out = os.path.splitext(inp)[0] + '_' + str(c);c += 1
    extract(inp,out,quiet=False,rs=True)
