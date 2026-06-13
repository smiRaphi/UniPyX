import pickle,struct,os,zlib,inspect,tokenize,io
from decimal import Decimal
from threading import Thread
from types import FunctionType
from .file import asrt,File

# 0: none or fixed size bytes
# 1: bool
# 2: +int
# 3: -int (signed int in static list)
# 4: str
# 5: bytes
# 6: float
# 7: list
# 8: static list
# 9: dict
# 10: Decimal
# 11: function
# 12: python pickle

def deflate0(d:bytes):
    d = zlib.compress(d,level=9,wbits=-15)
    return (d[0] & 0xF8 | (((d[0] >> 1) & 3) + 1) | (0 if d[0] & 1 else 1) << 2).to_bytes(1) + d[1:]
def dedeflate0(i:bytes):
    return zlib.decompress((i[0] & 0xF8 | ((i[0] & 3) - 1) << 1 | (0 if (i[0] >> 2) & 1 else 1)).to_bytes(1) + i[1:],wbits=-15)

class PyOUnpickler(pickle.Unpickler):
    UNSAFE = {'BaseException','KeyboardInterrupt','OSError','SystemExit','open','exit','exec','eval','id','input','print','type','super','quit','memoryview','compile'}
    def __init__(self,*args,**kwargs):
        self.SAFE = set([x for x in dir(__builtins__) if x not in self.UNSAFE and not x.startswith('_')])
        super().__init__(*args,**kwargs)

    def find_class(self,mn,n):
        if mn == 'builtins' and n in self.SAFE: return getattr(__builtins__,n)
        return None
class PyOFunc:
    def __init__(self,f:FunctionType,xenv={}):
        def _err(*args,**kwargs): raise RuntimeError
        self.env = {x:_err for x in dir(__builtins__) if x in PyOUnpickler.UNSAFE or x.startswith('_')} | xenv

        if f == None: self.source = None
        elif type(f) == str:
            self.source = f
            env = self.env.copy()
            if f.startswith(('lambda:','lambda ')): f = eval(f,env,env)
            elif f.startswith('def '):
                exec(f,env,env)
                for k,v in env.items():
                    if not k in self.env and type(v) == FunctionType:
                        f = v
                        break
                else: raise TypeError(self.source)
            else: raise TypeError(repr(self.source))
        elif type(f) != FunctionType: raise TypeError
        else:
            self.source = inspect.getsource(f)
            if not self.source.startswith('def '): raise TypeError(self.source)
        if f is not None:
            r = []
            fstl = None
            fstc = None
            cl = 1
            cc = 0
            for to in tokenize.generate_tokens(io.StringIO(self.source.rstrip('\n')).readline):
                if to.type == tokenize.DEDENT:
                    cc -= 1
                    continue
                if to.start[0] < cl or to.type in {tokenize.NEWLINE,tokenize.ENCODING,tokenize.ENDMARKER}: continue
                if to.type == tokenize.INDENT:
                    if fstl is None:
                        if '\t' in to.string: fstl = 1
                        else: fstl = len(to.string)
                        fstc = (len(self.source) - len(self.source.lstrip(to.string[0]))) // fstl
                    cc = len(to.string) // fstl - fstc
                if fstl is None: r.append(to.line)
                else:
                    r.append('\t'*cc)
                    r.append(to.line[cc*fstl+fstc:])
                cl = to.end[0] + 1
            self.source = ''.join(r)
        self.f = f
    def __call__(self,*args,**kwargs):
        if self.f is None:
            if not kwargs and len(args) == 1: return args[0]
            elif not kwargs: return args
            elif kwargs: return args,kwargs
            return None
        return self.f(*args,**kwargs)
    def __bool__(self): return bool(self.source)
    def __len__(self): return len(self.source)
    def __str__(self): return self.source
    def __eq__(self,other:'PyOFunc'):
        if other == None: return self.source == None
        return self.source == other.source
    def __ne__(self,other:'PyOFunc'):
        if other == None: return self.source != None
        return self.source != other.source
class PyOInlineF(PyOFunc): pass

_SMAP = (4,5,6,8,10,12,16,20,24,32,40,48,64,128,256)
class PyOBin:
    def __init__(self,p:str,unpickle=False,xenv={}):
        if type(xenv) in (list,tuple,set): xenv = {x.__name__:x for x in xenv}

        self.p = os.path.abspath(p)
        self.unpickle = unpickle
        self.xenv = xenv
        self.db = None
    
        self._load_thrd = None
    @classmethod
    def new(cls,p:str,base={},**kwargs):
        asrt(type(base) in (dict,list),err=TypeError)
        c = cls(p,**kwargs)
        c.db = base
        return c

    def load(self):
        if os.path.exists(self.p) and self._load_thrd is None:
            assert os.path.isfile(self.p) # not asrt
            self._load_thrd = Thread(target=self._load)
            self._load_thrd.start()
        return self
    def loadb(self):
        self.load().wait()
        return self
    def wait(self):
        if self._load_thrd is not None:
            self._load_thrd.join()
            self._load_thrd = None
    def _load(self):
        f = File(self.p,'rb',endian='>')
        asrt(f.read(4) == b'PyOB')
        funcs = []
        def interp(ty=None,lst=False):
            nonlocal sdbix
            if ty is None: ty = f.readu8()
            ty,fl = ty & 0b1111,ty >> 4

            match ty:
                case 0:
                    if fl:
                        xr = fl ^ (_SMAP[fl - 1] & 0xFF) ^ 0xFF
                        return bytes(v ^ xr for v in f.readc(_SMAP[fl - 1]))
                    else: return None
                case 1:
                    assert not fl >> 1 # not asrt!
                    return fl == 1
                case 2:
                    if fl & 8: return fl & 7
                    if fl & 7: return f.unpacki(fl & 7)
                    if lst: return f.unpacki((fl >> 4) + 7)
                    v = f.readu8()
                    return v >> 4 | f.unpacki((v & 15) + 7) << 4
                case 3:
                    if lst: return f.unpacki(fl,signed=True)
                    else: return -f.unpacki(fl)
                case 4:
                    if fl & 8:
                        if fl == 0b1100:
                            fl = f.readu8()
                            v,s = fl & 0b1111,fl >> 4
                            sdbix = v | f.unpacki(s) << 4
                        else: sdbix += (fl & 3) * (-1 if fl >> 2 & 1 else 1)
                        r = sdb[sdbix]
                        sdbix += 1
                        return r
                    else: return sdb[f.unpacki(fl & 7)]
                case 5:
                    if fl & 8: return f.decompress(f.unpacki(fl & 7),'deflate0' if fl & 8 else 'none')
                    xr = (ty | fl << 4) ^ 0xFF
                    return bytes(v ^ xr for v in f.readc(f.unpacki(fl)))
                case 6: return (f.readf16,f.readf32,f.readf64)[fl]()
                case 7:
                    c = f.unpacki(fl)
                    o = [interp() for _ in range(c)]
                    return o
                case 8:
                    c = f.unpacki(fl)
                    if c == 0: return []
                    sty = f.readu8()
                    if sty == 0:
                        interp(sty,lst=True)
                        return [None] * c
                    elif sty & 0b1111 == 1:
                        o = []
                        b = sty >> 4
                        for ix in range(min(4,c)):
                            o.append(bool((b >> ix) & 1))
                            c -= 1
                        for _ in range((c + 7)//8):
                            b = f.readu8()
                            for ix in range(min(8,c)):
                                o.append(bool((b >> ix) & 1))
                                c -= 1
                        return o
                    else:
                        if sty == 2: sty |= f.readu8() << 8
                        return [interp(sty,lst=True) for _ in range(c)]
                case 9:
                    c = f.unpacki(fl)
                    ks = [interp() for _ in range(c)]
                    o = {}
                    for k in ks: o[k] = interp()
                    return o
                case 10:
                    ml = -1 if fl & 8 else 1
                    if fl & 4: r = Decimal(('0','Infinity','NaN','sNaN')[fl & 3])
                    else:
                        v = fl & 3 | f.readu8() << 2
                        s1,s2 = (v & 0b11111) * 3,(v >> 5) * 4
                        v = f.unpacki((s1 + s2 + 7) // 8)
                        r = Decimal(v & ((1 << s1) - 1)) / Decimal(v >> s1)
                    return r * ml
                case 11:
                    # d = f.readc(f.unpacki((fl & 3) + 1) + 7)
                    # if d == b'\0': d = None
                    # else: d = d.decode('utf-0' if fl & 4 else 'ascii7')

                    bseed = fl & 3
                    seed = [0,0,0,0]
                    for ix in range(4): seed[(bseed + ix) & 3] = ix
                    fsdbix = v = c = 0
                    def rb(lng) -> int:
                        nonlocal v,c
                        while c < lng:
                            v |= f.readu8() << c;c += 8
                        r = v & ((1 << lng) - 1);v >>= lng;c -= lng
                        if lng == 2: r = seed[r]
                        return r
                    mxix = 0
                    def rs():
                        nonlocal fsdbix,mxix
                        m = rb(2)
                        if m == 0b00:
                            ixs = rb(5) + 1
                            ix = rb(ixs)
                            return sdb[ix]
                        elif m == 0b01:
                            ixs = rb(4) + 1
                            ix = rb(ixs)
                            fsdbix = ix
                        elif m == 0b10:
                            fsdbix += rb(2)
                        elif m == 0b11:
                            fsdbix -= rb(2) + 1
                        fsdbix += 1
                        mxix = max(mxix,fsdbix)
                        return sdb[sdbix + fsdbix - 1]

                    d = []
                    tbc = 0
                    while True:
                        t1 = rb(2)
                        if t1 != 0b00 and d and d[-1] == '\n': d.append('\t'*tbc)
                        if t1 == 0b00:
                            t2 = rb(2)
                            if t2 == 0b00: break
                            elif t2 == 0b01: d.append('\n')
                            elif t2 == 0b10:
                                tbc = rb(4)
                                d.append('\t'*tbc)
                            elif t2 == 0b11: tbc -= 1
                        elif t1 == 0b01:
                            tv = rs()
                            if tv in {'and','or','not','is','in','as'}: tv = f' {tv} '
                            elif tv in {'if','else','import'} and d and not '\t' in d[-1] and not '\n' in d[-1]: tv = f' {tv} '
                            elif tv in {'if','elif','except','for','while','with','def','class','return','raise','assert','lambda','nonlocal','global','yield','import','from'}:
                                tv = f'{tv} '
                            d.append(tv)
                        elif t1 == 0b10: d.append(OPS[rb(6)])
                        elif t1 == 0b11:
                            t2 = rb(1)
                            if t2 == 0b0:
                                vs = rb(5) * 2 + 2
                                d.append(str(rb(vs)))
                            elif t2 == 0b1:
                                vs1,vs2 = rb(5) * 2 + 2,rb(5) * 2 + 2
                                d.append(f'{rb(vs1)}.{rb(vs2)}')

                    if d: d = ''.join(d)
                    else: d = None
                    sdbix += mxix

                    if self.unpickle:
                        r = PyOFunc(d,self.xenv.copy())
                        if fl & 8: funcs.append(r)
                        return r
                    else: return (PyOInlineF if fl & 8 else PyOFunc,d)
                case 12:
                    d = f.decompress(f.unpacki(fl & 7),'deflate0' if fl & 8 else 'none')
                    if self.unpickle: return PyOUnpickler(d,encoding='utf-8').load()
                    else: return (PyOUnpickler,d)
                case _: raise ValueError(f'Unknown type: {ty} (0x{fl << 4 | ty:02X}) @ 0x{f.pos-1:08X}')

        ss = f.readvlq()
        if ss:
            if ss & 1: d = f.decompress(ss >> 1,'deflate0').decode('utf-8')
            elif ss & 2: d = f.readc(ss >> 2).decode('ascii7')
            else: d = f.readc(ss >> 2).decode('utf0')
        sdb = d.split('\0')
        del d
        sdbix = 0
        fd = f.read()
        f.close()
        if fd[0] == 0xF1: fd = dedeflate0(fd[1:])
        f = File(fd,endian=f._end)
        del fd
        ty = f.readu8()
        asrt((ty & 0b1111) in {7,8,9})
        self.db = interp(ty)
        f.close()
        for fnc in funcs: fnc(self.db)
    def save(self):
        asrt(type(self.db) in (dict,list),err=TypeError)
        sdb = []
        sdbix = 0
        f = File(b'',endian='>')
        ibytes = False

        def interp(x,pt):
            nonlocal sdb,sdbix,ibytes
            t = None if x == None else type(x)

            if t == str: asrt(not '\0' in x)

            if t == None: f.writeu8(0)
            elif t == bool: f.writeu8(1 | (1 if x else 0) << 4)
            elif t == int and x >= 0:
                if x.bit_length() < 4: f.writeu8(2 | 0x80 | x << 4)
                else:
                    s = (x.bit_length() + 7) // 8
                    if s > 7:
                        f.writeu8(2)
                        asrt(x.bit_length() <= 180)
                        v = (x.bit_length() - 4 - 7*8 + 7) // 8
                        f.writeu8(v | (x & 15) << 4)
                        f.packi(x >> 4,s)
                    else:
                        f.writeu8(2 | s << 4)
                        f.packi(x,s)
            elif t == int and x < 0:
                x = -x
                s = (x.bit_length() + 7) // 8
                f.writeu8(3 | s << 4)
                f.packi(x,s)
            elif t == str:
                if x in sdb: ix = sdb.index(x)
                else:
                    ix = len(sdb)
                    sdb.append(x)
                df = ix - sdbix
                if 3 >= df >= -3:
                    f.writeu8(4 | 0x80 | (0x40 if df < 0 else 0) | (abs(df) & 3) << 4)
                    sdbix = ix + 1
                else:
                    s = (ix.bit_length() + 7) // 8
                    asrt(s < 0b1000)
                    f.writeu8(4 | s << 4)
                    f.packi(ix,s)
            elif t == bytes and len(x) in _SMAP:
                xr = _SMAP.index(len(x)) + 1
                f.writeu8(0 | xr << 4)
                xr ^= (len(x) & 0xFF) ^ 0xFF
                f.write(bytes(v ^ xr for v in x))
            elif t == bytes:
                ibytes = True
                xc = deflate0(x)
                bs = 0x80 if len(xc) < len(x) else 0
                if len(xc) < len(x): x = xc
                else:
                    xr = (5 | ((len(x).bit_length() + 7) // 8) << 4) ^ 0xFF
                    x = bytes(v ^ xr for v in x)
                s = (len(x).bit_length() + 7) // 8
                f.writeu8(5 | bs | s << 4)
                f.packi(len(x),s)
                f.write(x)
            elif t == float:
                for ix,fm in enumerate('efd'):
                    try:
                        d = struct.pack(f'>{fm}',x)
                        v = struct.unpack(f'>{fm}',d)[0]
                    except (struct.error,OverflowError): continue
                    df = abs(x - v)
                    if df < 0.00001:
                        f.writeu8(6 | ix << 4)
                        f.write(d)
                        return
                return interp(Decimal(str(x)),pt)
            elif t == list:
                if len(x) == 0: f.writeu8(7);return
                s = (len(x).bit_length() + 7) // 8
                t1 = type(x[0])
                if all(type(y) == t1 for y in x):
                    if x[0] == None:
                        f.writeu8(8 | s << 4)
                        f.packi(len(x),s)
                        f.writeu8(0)
                        return
                    elif t1 == bool:
                        f.writeu8(8 | s << 4)
                        f.packi(len(x),s)
                        v = 0
                        x = x.copy()
                        for ix in range(min(4,len(x))): v |= (1 if x.pop(0) else 0) << ix
                        f.writeu8(1 | v << 4)
                        while x:
                            v = 0
                            for ix in range(min(8,len(x))): v |= (1 if x.pop(0) else 0) << ix
                            f.writeu8(v)
                        return
                    elif t1 == int:
                        f.writeu8(8 | s << 4)
                        f.packi(len(x),s)
                        if all(y >= 0 for y in x):
                            s = (max(x).bit_length() + 7) // 8
                            if s > 7:
                                f.writeu8(2)
                                f.writeu8(s - 7)
                            else: f.writeu8(2 | s << 4)
                            for y in x: f.packi(y,s)
                        else:
                            s = (max(abs(y) for y in x) + 1 + 7) // 8
                            f.writeu8(3 | s << 4)
                            for y in x: f.packi(y,s,signed=True)
                        return
                    elif t1 == bytes and len(x[0]) in _SMAP and all(len(y) == len(x[0]) for y in x[1:]):
                        f.writeu8(8 | s << 4)
                        f.packi(len(x),s)
                        xr = _SMAP.index(len(x[0])) + 1
                        f.writeu8(0 | xr << 4)
                        xr ^= (len(x[0]) & 0xFF) ^ 0xFF
                        f.write(bytes(v ^ xr for v in (b''.join(x))))
                        return
                    elif t1 == bytes:
                        f.writeu8(8 | s << 4)
                        f.packi(len(x),s)
                        xc = deflate0(x[0])
                        bs = 0x80 if len(xc) < len(x[0]) else 0
                        if bs: x = [xc] + [deflate0(y) for y in x[1:]]
                        s = (max(len(y) for y in x).bit_length() + 7) // 8
                        asrt(s < 0b1000)
                        f.writeu8(5 | bs | s << 4)
                        for y in x:
                            f.packi(len(y),s)
                            f.write(y)
                        return
                    elif t1 == float:
                        f.writeu8(8 | s << 4)
                        f.packi(len(x),s)
                        f.writeu8(6)
                        for y in x: f.writef32(y)
                        return
                    elif t1 == str and (not any(y in sdb for y in x) or len(x) > 5000):
                        f.writeu8(8 | s << 4)
                        f.packi(len(x),s)
                        f.writeu8(4 | 0x80)
                        sdb.extend(x)
                        sdbix += len(x)
                        return
                f.writeu8(7 | s << 4)
                f.packi(len(x),s)
                for y in x: interp(y,t)
            elif t == dict:
                s = (len(x).bit_length() + 7) // 8
                f.writeu8(9 | s << 4)
                f.packi(len(x),s)
                ks = list(x.keys())
                if pt == list and len(ks) > 1 and all(type(y) == str for y in ks) and ks[0] in sdb:
                    ix = sdb.index(ks[0])
                    df = ix - sdbix
                    sdbix = ix + 1
                    if 3 >= df >= -3: f.writeu8(4 | 0x80 | (0x40 if df < 0 else 0) | (abs(df) & 3) << 4)
                    else:
                        f.writeu8(4 | 0x80 | 0x40)
                        s = (ix.bit_length() - 4 + 7) // 8
                        f.writeu8(s << 4 | ix & 0b1111)
                        ix >>= 4
                        f.packi(ix,s)
                    for k in ks[1:]: interp(k,t)
                else:
                    for k in x: interp(k,t)
                for v in x.values(): interp(v,t)
            elif t == Decimal:
                fl = 0b1000 if x.is_signed() else 0
                if x.is_infinite(): fl |= 0b101
                elif x.is_qnan():   fl |= 0b110
                elif x.is_snan():   fl |= 0b111
                elif x.is_zero():   fl |= 0b100
                else:
                    i1,i2 = x.as_integer_ratio()
                    i1 = abs(i1)
                    s1,s2 = (i1.bit_length() + 2) // 3,(i2.bit_length() + 3) // 4
                    asrt(s1.bit_length() < 6 and s2.bit_length() < 8)
                    v = (s2 << 5) | s1
                    fl |= v & 0b11;v >>= 2
                    f.writeu8(10 | fl << 4)
                    f.writeu8(v)
                    f.packi(i2 << (s1 * 3) | i1,(s1 * 3 + s2 * 4 + 7) // 8)
                    return
                f.writeu8(10 | fl << 4)
            elif t in (FunctionType,PyOFunc,PyOInlineF):
                if t == FunctionType: x = PyOFunc(x)
                fl = 0b1000 if t == PyOInlineF else 0
                if x:
                    x = list(tokenize.generate_tokens(io.StringIO(x.source).readline))
                    seed = len(x) & 3
                    f.writeu8(11 | (fl | seed) << 4)
                    seed = [(seed+ix) & 3 for ix in range(4)]

                    fsdb = []
                    fsdbix = v = c = 0
                    d = bytearray()
                    def wb(val,lng):
                        nonlocal v,c
                        if lng == 2: val = seed[val]
                        v |= val << c;c += lng
                        while c >= 8: d.append(v & 0xFF);v >>= 8;c -= 8
                    def ws(s:str):
                        nonlocal fsdbix
                        if s in fsdb:
                            wb(0b01,2)
                            ix = fsdb.index(s)
                            df = ix - fsdbix
                            if 0 <= df <= 3:
                                wb(0b10,2)
                                wb(df,2)
                            elif -4 <= df < 0:
                                wb(0b11,2)
                                wb(-df - 1,2)
                            else:
                                wb(0b01,2)
                                ixs = (ix.bit_length() or 1) - 1
                                asrt(ixs < 16)
                                wb(ixs,4)
                                wb(ix,ix.bit_length() or 1)
                            fsdbix = ix + 1
                        elif s in sdb:
                            wb(0b01,2)
                            wb(0b00,2)
                            ix = sdb.index(s)
                            ixs = (ix.bit_length() or 1) - 1
                            asrt(ixs < 32)
                            wb(ixs,5)
                            wb(ix,ix.bit_length() or 1)
                        else:
                            fsdb.append(s)
                            ws(s)

                    tbc = 0
                    while x:
                        tok = x.pop(0)
                        match tok.type:
                            case tokenize.NAME|tokenize.STRING: ws(tok.string)
                            case tokenize.OP:
                                asrt(tok.string in OPS,tok.string)
                                wb(0b10,2)
                                wb(OPS.index(tok.string),6)
                            case tokenize.NUMBER:
                                if '.' in tok.string:
                                    tv1,tv2 = tok.string.split('.')
                                    tv1,tv2 = int(tv1),int(tv2)
                                    asrt(tv1.bit_length() <= 32 and tv2.bit_length() <= 32)
                                    wb(0b11,2)
                                    wb(0b1,1)
                                    vs1,vs2 = ((tv1.bit_length() or 1) + 1) // 2 - 1,((tv2.bit_length() or 1) + 1) // 2 - 1
                                    wb(vs1,5)
                                    wb(vs2,5)
                                    wb(tv1,(vs1 + 1) * 2)
                                    wb(tv2,(vs2 + 1) * 2)
                                else:
                                    tv = int(tok.string,{'0b':2,'0o':8,'0x':16}.get(tok.string[:2].lower(),10))
                                    asrt(tv.bit_length() <= 64)
                                    wb(0b11,2)
                                    wb(0b0,1)
                                    vs = ((tv.bit_length() or 1) + 1) // 2 - 1
                                    wb(vs,5)
                                    wb(tv,(vs + 1) * 2)
                            case tokenize.INDENT:
                                asrt(len(tok.string) < 16)
                                tbc = len(tok.string)
                                wb(0b00,2)
                                wb(0b10,2)
                                wb(tbc,4)
                            case tokenize.DEDENT:
                                tbc -= 1
                                wb(0b00,2)
                                wb(0b11,2)
                            case tokenize.NEWLINE:
                                wb(0b00,2)
                                wb(0b01,2)
                            case tokenize.ENCODING|tokenize.ENDMARKER|tokenize.COMMENT: pass
                            case _: raise TypeError(tok)
                    wb(0b00,2)
                    wb(0b00,2)
                    if c: d.append(v)
                    f.write(d)
                    sdb.extend(fsdb)
                    sdbix += len(fsdb) - 1
                else:
                    f.writeu8(11 | fl << 4)
                    f.writeu8(0)
            else: raise TypeError

        interp(self.db,-1)

        if sdb:
            sdb = '\0'.join(sdb)
            sdbd = sdb.encode('utf-8')
            sdbc = deflate0(sdbd)
            z = len(sdbc) < len(sdbd)
            if z:
                d = sdbc
                s = len(d) << 1 | 1
            else:
                try: sdb.encode('ascii')
                except UnicodeEncodeError:
                    d = sdb.encode('utf0')
                    s = len(d) << 2 | 0
                else:
                    d = sdb.encode('ascii7')
                    s = len(d) << 2 | 0b10
        else: d,s = b'',0
        of = File(self.p,'wb',endian='>')
        of.write(b'PyOB')
        of.writevlq(s)
        of.write(d)
        d = f.readall()
        del f
        if not ibytes:
            dc = deflate0(d)
            if (len(dc) + 1) < len(d):
                d = dc
                of.writeu8(0xF1) # bool with full flags
            of.write(d)
        else: of.write(d)
        of.close()

class PyOBinX(PyOBin):
    @classmethod
    def dl(cls,n:str,db,unpickle=False): return cls(db.get(n),unpickle=unpickle).load()

    def get(self,v,default=None): return self.db.get(v,default)
    def __getitem__(self,v): return self.db.__getitem__(v)
    def __setitem__(self,k,v): self.db.__setitem__(k,v)
    def __contains__(self,v): return self.db.__contains__(v)
    def __len__(self): return self.db.__len__()
    def __iter__(self): return self.db.__iter__()
    def keys(self): return self.db.keys()
    def values(self): return self.db.values()
    def items(self): return self.db.items()
    def pop(self,k,default=None): return self.db.pop(k,default)
    def remove(self,k): return self.db.pop(k)
    def append(self,v): self.db.append(v)
    def extend(self,v): self.db.extend(v)
    def insert(self,i,v): self.db.insert(i,v)

OPS = (':',':=',',','.','@','(','[','{','}',']',')','*','*=','**','**=','+','+=','-','-=','/','/=','//','//=','=','==','<','<=','>','>=','!=','|','|=','&','&=','^','^=','~','~=','>>','>>=','<<','<<=','%','%=',';')
