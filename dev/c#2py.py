"""
"""

if __doc__ is None or not __doc__.strip():
    g = globals().copy()
    d = [(g[x],x) for x in g if not x.startswith('__')]
    s = max(x[0].bit_length() for x in d)
    s = (s + 3) // 4
else:
    import re
    h,d = re.sub(r'([\n\r\t]+| {2,})','',re.sub(r'//.*','',__doc__)).split('}',1)[0].split('{',1)
    s = {
        'byte':1,'ubyte':1,'char':1,'uchar':1,'bool':1,'u8':1,'s8':1,'uint8':1,'uint8_t':1,'int8':1,'int8_t':1,
        'short':2,'ushort':2,'u16':2,'s16':2,'uint16':2,'int16':2,'uint16_t':2,'int16_t':2,
        'u24':3,'s24':3,'uint24':3,'int24':3,'uint24_t':3,'int24_t':3,
        'uint':4,'int':4,'u32':4,'s32':4,'uint32':4,'int32':4,'uint32_t':4,'int32_t':4,
        'u48':6,'s48':6,'uint48':6,'int48':6,'uint48_t':6,'int48_t':6,
        'long':8,'ulong':8,'u64':8,'s64':8,'uint64':8,'int64':8,'uint64_t':8,'int64_t':8,'size_t':8,'ssize_t':8,
    }[h.split(':',1)[1].strip()] * 2
    pi = lambda x: int(x[2:],16) if x.startswith('0x') else int(x)
    d = [(pi(x.split('=',1)[1].strip()),x.split('=',1)[0].strip()) for x in d.split(',') if x.strip()]

d.sort(key=lambda x:x[0])
o = ['']
for x in d:
    if x[0] > 15: i = f'0x{x[0]:0{s}X}'
    else: i = str(x[0])
    o[-1] += f"{i}:'{x[1]}',"
    if len(o[-1]) > 140: o.append('')
if o[-1] == '': o.pop()

import os
n = os.path.basename(os.path.splitext(__file__)[0]).upper().replace(' ','_').replace('-','_')
tb = 12
op = f"\n{' '*12}{n} = {{{o[0]}";o.pop(0)
tb += len(n) + 4
for x in o: op += f"\n{' '*tb}{x}"
print(op[:-1] + '}')
