import zlib,struct,os,io
from lib.file import ENDMAP,UTFENDM,ILSTRM,asrt,align,File as _File

LOG = []
class File(_File):
    def __init__(self,f,mode='r',endian='>'):
        self.__end = None
        if 'r' in mode:
            self.obj = {'l':[],'e':None}
            LOG.append(self.obj)
            if isinstance(f,(bytes,bytearray)): self.obj['d'] = zlib.crc32(f)
            elif isinstance(f,str): self.obj['f'] = os.path.abspath(f).lower().replace('\\','/')

        asrt(not 't' in mode)
        self.mode = mode.replace('b','') + 'b'
        self.name = None
        if type(f) == str:
            self.name = f
            self._f = open(f,self.mode)
        elif type(f) == bytes:
            self._f = io.BytesIO(f)
        else: self._f = f
        self._end = endian

        self._start_pos = self._f.tell()
        if type(f) == bytes: self._size = len(f)
        else: self._size = self.seek(0,2,_basic=False)
        self._end_pos = None
        self.seek(0,_basic=False)

    def seek(self,n,whence=0,_basic=True):
        if _basic: self.obj['l'].append(('seek',n,whence))
        return super().seek(n,whence)
    def read(self,n=None,_basic=True):
        d = super().read(n)
        if _basic: self.obj['l'].append(('read',n,zlib.crc32(d) if d else None))
        return d

    def skip(self,n:int,_basic=True): return self.seek(n,1,_basic)
    def back(self,n:int,_basic=True): return self.skip(-n,_basic)
    def padc(self,n:int):
        self.obj['l'].append(('padc',n))
        if sum(self.readc(n,_basic=False)): raise ValueError(f"Unexpected Value in padding @ 0x{self.pos - n:08X} - 0x{self.pos:08X}")
        return 0 # for chaining
    def readu(self,c=b'\0',maxl=None,chks=0x80,include=False,skip=True,eoferr=False,_basic=True):
        if not maxl is None and maxl < chks: chks = maxl
        if _basic: self.obj['l'].append(('readu',c,maxl,include,skip))
        lnc = len(c)

        o = bytearray()
        while True:
            d = self.read(chks,_basic=False)
            o.extend(d)
            p = o.find(c,max(0,len(o) - len(d) - lnc + 1),maxl or len(o))
            if p != -1:
                o = o[:p + (lnc if include else 0)]
                self.back(len(d) - p - (lnc if skip else 0),_basic=False)
                break
            if len(d) != chks or (maxl is not None and len(o) >= maxl):
                if eoferr:
                    self.back(len(o),_basic=False)
                    raise EOFError
                break
        return bytes(o)
    def readc(self,n:int=None,_basic=True):
        d = self.read(n,_basic)
        if n is not None and len(d) != n: raise EOFError(f"Unexpected EOF ({len(d)} != {n}) @ 0x{self.pos - len(d):08X} - 0x{self.pos - len(d) + n:08X}")
        return d
    def readi(self,n:int,signed=False,end=None):
        d = self.readc(n,_basic=False)
        end = end or self._end
        if end == '-': d = self.middle_scramble(d)
        return int.from_bytes(d,ENDMAP[end],signed=bool(signed))
    def reads(self,n:int,encoding='utf-8'):
        if encoding == 'utf-16': return self.readutf16(n)
        self.obj['l'].append(('s',n))
        try: return self.readc(n,_basic=False).decode(encoding)
        except UnicodeDecodeError:
            print(f'Failed to decode {encoding} @ 0x{self.pos - n:08X} - 0x{self.pos:08X}')
            raise
    def unpack(self,fmt:str,end=None):
        d = self.readc(struct.calcsize(fmt),_basic=False)
        end = end or self._end
        if end == '-':
            d = self.middle_scramble(d)
            end = '>'
        return struct.unpack(end + fmt,d)[0]
    def readil(self,n:int|float,c:int,signed=False,end=None,eoferr=True,_basic=True) -> list[int|float]:
        if _basic: self.obj['l'].append(('il',n,c,signed,end))
        end = end or self._end
        asrt(end != '-')
        t = ILSTRM[n]
        if signed: t = t.lower()
        if isinstance(n,float): n = int(n*10)
        if isinstance(c,bytes):
            d = c
            c = len(d) // n
        else:
            d = self.read(c*n)
            if len(d) != c*n:
                if eoferr: raise EOFError
                d = d[:-len(d) % -n]
                c = len(d) // n
        return list(struct.unpack(f'{end}{c}{t}',d))

    def readu8(self,_basic=True):
        if _basic: self.obj['l'].append(('u8',))
        return super().readu8()
    def readu16(self,end=None,_basic=True):
        if _basic: self.obj['l'].append(('u16',end))
        return super().readu16(end)
    def readu24(self,end=None):
        self.obj['l'].append(('u24',end))
        return super().readu24(end)
    def readu32(self,end=None,_basic=True):
        if _basic: self.obj['l'].append(('u32',end))
        return super().readu32(end)
    def readu40(self,end=None):
        self.obj['l'].append(('u40',end))
        return super().readu40(end)
    def readu48(self,end=None):
        self.obj['l'].append(('u48',end))
        return super().readu48(end)
    def readu64(self,end=None):
        self.obj['l'].append(('u64',end))
        return super().readu64(end)
    def readu128(self,end=None):
        self.obj['l'].append(('u128',end))
        return super().readu128(end)
    def reads8(self):
        self.obj['l'].append(('s8',))
        return super().reads8()
    def reads16(self,end=None):
        self.obj['l'].append(('s16',end))
        return super().reads16(end)
    def reads24(self,end=None):
        self.obj['l'].append(('s24',end))
        return super().reads24(end)
    def reads32(self,end=None):
        self.obj['l'].append(('s32',end))
        return super().reads32(end)
    def reads40(self,end=None):
        self.obj['l'].append(('s40',end))
        return super().reads40(end)
    def reads48(self,end=None):
        self.obj['l'].append(('s48',end))
        return super().reads48(end)
    def reads64(self,end=None):
        self.obj['l'].append(('s64',end))
        return super().reads64(end)
    def reads128(self,end=None):
        self.obj['l'].append(('s128',end))
        return super().reads128(end)
    def readf16(self,end=None):
        self.obj['l'].append(('f16',end))
        return super().readf16(end)
    def readf32(self,end=None):
        self.obj['l'].append(('f32',end))
        return super().readf32(end)
    def readf64(self,end=None):
        self.obj['l'].append(('f64',end))
        return super().readf64(end)
    def readbool(self):
        self.obj['l'].append(('bool',))
        b = self.readu8(_basic=False)
        if b not in {0,1}: raise ValueError(f"Invalid bool value: {b} @ 0x{self.pos-1:08X}")
        return bool(b)
    def readbool16(self,end=None):
        self.obj['l'].append(('bool16',end))
        b = self.readu16(end,_basic=False)
        if b not in {0,1}: raise ValueError(f"Invalid bool value: {b} @ 0x{self.pos-2:08X}")
        return bool(b)
    def readbool32(self,end=None):
        self.obj['l'].append(('bool32',end))
        b = self.readu32(end,_basic=False)
        if b not in {0,1}: raise ValueError(f"Invalid bool value: {b} @ 0x{self.pos-4:08X}")
        return bool(b)

    def read0s(self,encoding:str=None,maxl:int=None,chks=0x100):
        self.obj['l'].append(('0s',maxl))
        r = self.readu(maxl=maxl,chks=chks,_basic=False)
        if encoding is not None: r = r.decode(encoding)
        return r
    def readutf16(self,l:int,end=None):
        self.obj['l'].append(('utf16',l,end))
        return self.readc(l * 2,_basic=False).decode('utf-16' + UTFENDM[end or self._end])
    def read0s16(self,maxl:int=None,chks=0x40,end=None):
        self.obj['l'].append(('0s16',maxl,end))
        r = []
        while self and (maxl is None or len(r) < maxl):
            v = self.readil(2,chks,eoferr=False,_basic=False)
            if 0 in v:
                i0 = v.index(0)
                r.extend(v[:i0])
                self.back((len(v) - i0) * 2,_basic=False)
                break
            r.extend(v)

        return struct.pack(f'<{len(r)}H',*r).decode('utf-16' + UTFENDM[end or self._end])

    def align(self,blocksize:int,base:int=0):
        self.obj['l'].append(('align',blocksize,base))
        v = align(self.tell() - base,blocksize)
        self.skip(v,_basic=False)
        return v
    def peek(self,fnc,*args,poffset=0,**kwargs):
        self.obj['l'].append(('peek',poffset))
        if isinstance(fnc,str):
            if fnc in {'u8','s8','u16','s16','u24','s24','u32','s32','u40','s40','u48','s48','u64','s64','u128','s128','f16','f32','f64','bool','bool32'}: fnc = ('write' if 'w' in self.mode else 'read') + fnc
            fnc = getattr(self,fnc)
        elif isinstance(fnc,int):
            args = (fnc,)
            fnc = self.read
        p = self.pos
        self.seek(p + poffset,_basic=False)
        try: r = fnc(*args,**kwargs)
        finally: self.seek(p,_basic=False)
        self.obj['l'].append(('peekend',))
        return r

    def close(self):
        del self.obj
        return super().close()

    @property
    def _end(self): return self.__end
    @_end.setter
    def _end(self,v):
        self.__end = v
        if 'e' in self.obj and self.obj['e'] is None: self.obj['e'] = (v,)
        else:
            asrt(isinstance(self.obj['e'],tuple))
            self.obj['e'] = v

def fi(i:int):
    n = i < 0
    i = abs(i)
    if i > 15: r = f'0x{i:X}'
    else: r = str(i)
    if n: return f'-{r}'
    return r
def process(log:list=None):
    if log is None: log = LOG

    o = []
    HMP = {}
    FMP = {}
    DN = set()
    for x in log:
        if 'd' in x: fix = HMP[x['d']]
        elif 'f' in x:
            if x['f'] in FMP: fix = FMP[x['f']]
            else:
                fix = FMP[x['f']] = len(o)
                o.append([{}])
        else: raise RuntimeError(x)
        fth = (fix,hash(tuple(x['l'])))
        if fth in DN: continue
        DN.add(fth)

        if 'd' in x: o[fix][0][x['d']] = len(o[fix])
        e = x['e']
        if isinstance(e,tuple): e = e[0]
        obj = {'n':f'a{len(o[fix])}','e':UTFENDM[e],'l':[]}
        def gv(): return f'v{len(obj["l"])}'
        peek = False
        def gp(o=0):
            if not peek: return ''
            m = []
            if peek[0] != 0:
                if peek[0] < 0: m.append(f' - {abs(peek[0])}')
                else: m.append(f' + {peek[0]}')
            if o != 0:
                if o < 0: m.append(f' - {abs(o)}')
                else: m.append(f' + {o}')
            if m: return f" @ (${''.join(m)})"
            return ' @ $'

        for y in x['l']:
            if y[0] == 'peek':
                peek = (y[1],)
                continue
            elif y[0] == 'peekend':
                peek = False
                continue
            elif y[0] in {'u8','s8','u16','s16','u24','s24','u32','s32','u40','s40','u48','s48','u64','s64','u128','s128'}:
                if len(y) > 1: ye = y[1] or e
                if len(y) > 1 and ye != e: obj['l'].append(f'{UTFENDM[ye]} {y[0]} {gv()}')
                else: obj['l'].append(f'{y[0]} {gv()}')
            elif y[0] == 'bool': obj['l'].append(f'bool {gv()}')
            elif y[0] == 'bool16':
                ye = y[1] or e
                if y[1] == '<': obj['l'].append(f'bool {gv()}{gp()};padding[1]{gp(1)}')
                elif y[1] == '>': obj['l'].append(f'padding[1]{gp()};bool {gv()}{gp(1)}')
                continue
            elif y[0] == 'bool32':
                ye = y[1] or e
                if ye == '<': obj['l'].append(f'bool {gv()}{gp()};padding[3]{gp(1)}')
                elif ye == '>': obj['l'].append(f'padding[3]{gp()};bool {gv()}{gp(3)}')
                continue
            elif y[0] == 'read':
                if not y[2] is None:
                    if y[2] in HMP: asrt(HMP[y[2]] == fix)
                    else: HMP[y[2]] = fix

                    obj['l'].append((gv(),y[1],y[2],gp()))
                    continue
                elif y[1] is None: obj['l'].append(f'u8 {gv()}[sizeof($) - $]')
                else: obj['l'].append(f'u8 {gv()}[{fi(y[1])}]')
            elif y[0] == 's':
                if y[1] is None: obj['l'].append(f'char {gv()}[sizeof($) - $]')
                else: obj['l'].append(f'char {gv()}[{fi(y[1])}]')
            elif y[0] == 'utf16':
                ye = y[2] or e
                if ye != e: ye = UTFENDM[y[2]] + ' '
                else: ye = ''
                if y[1] is None: obj['l'].append(f'{ye}char16 {gv()}[(sizeof($) - $) / 2]')
                else: obj['l'].append(f'{ye}char16 {gv()}[{fi(y[1])}]')
            elif y[0] == '0s16':
                ye = y[2] or e
                if ye != e: ye = UTFENDM[y[2]] + ' '
                else: ye = ''
                if y[1] is None: obj['l'].append(f'{ye}char16 {gv()}[]')
                else:
                    v = gv()
                    obj['l'].append(f'u64 {v}ep=$+{fi(y[1])};{ye}char16 {v}[while($ < {v}ep && $[$]+$[$+1])]{gp()};padding[2]{gp()}')
                    continue
            elif y[0] == '0s':
                if y[1] is None: obj['l'].append(f'char {gv()}[]')
                else:
                    v = gv()
                    obj['l'].append(f'u64 {v}ep=$+{fi(y[1])};char {v}[while($ < {v}ep && $[$])]{gp()};padding[1]{gp()}')
                    continue
            elif y[0] == 'readu':
                if isinstance(y[1],bytes): ch = y[1][0]
                else: ch = y[1]
                if y[2] is None: obj['l'].append(f'u8 {gv()}[while($[$] != 0x{ch:02X})]')
                else:
                    v = gv()
                    obj['l'].append(f'u64 {v}ep=$+{fi(y[2])};u8 {v}[while($ < ep && $[$] != 0x{ch:02X})]')
            elif y[0] == 'seek':
                if y[2] == 1: obj['l'].append(f'$ += {fi(y[1])}')
                elif y[1] < 0 or (y[1] == 0 and y[2] == 2): obj['l'].append(f'$ = sizeof($){fi(y[1]) or ""}')
                else: obj['l'].append(f'$ = {fi(y[1])}')
            elif y[0] == 'padc': obj['l'].append(f'padding[{fi(y[1])}]')
            elif y[0] == 'align':
                if y[2] == 0: obj['l'].append(f'$ += -$ % {fi(y[1])}')
                else: obj['l'].append(f'$ += -($ - {fi(y[2])}) % {fi(y[1])}')
            else: raise NotImplementedError(y)

            if peek: obj['l'][-1] += gp()

        o[fix].append(obj)

    for z in o:
        for x in z[1:]:
            l = []
            for y in x['l']:
                if isinstance(y,tuple):
                    if y[2] in z[0]:
                        so = z[z[0][y[2]]]
                        if so['e'] != x['e']: ye = so['e'] + ' '
                        else: ye = ''
                        if not y[3]:
                            if y[1] is None: ep = 'sizeof($)'
                            else: ep = f'$+{fi(y[1])}'
                            l.append(f"u64 {y[0]}ep={ep};{ye}{so['n']} {y[0]};$={y[0]}ep")
                        else: l.append(f"{ye}{so['n']} {y[0]}{y[3]}")
                    else:
                        if y[1] is None: l.append(f'u8 {y[0]}[sizeof($)-$]')
                        else: l.append(f'u8 {y[0]}[{fi(y[1])}]')
                else: l.append(y)
            x['l'] = l

    ob = []
    for z in o:
        if len(z) < 2 or (len(z) == 2 and not z[1]['l']): continue
        ob.append([])
        for x in reversed(z[1:]):
            ob[-1].append(f"struct {x['n']} {{\n")
            for l in x['l']: ob[-1].append(f"    {l};\n")
            ob[-1].append("};\n\n")
        ob[-1].append(f"{z[1]['n']} {z[1]['n']} @ $;\n")

    for ix,x in enumerate(ob):
        open(f'{ix}.hexpat','w',encoding='utf-8').write(''.join(x))

import atexit
atexit.register(process)
