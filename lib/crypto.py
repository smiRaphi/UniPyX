import struct
from lib.unipyxx import X

__FNCT = type(lambda:None)
def asrt(c:bool,*r,err:Exception=ValueError):
    if not c:
        if len(r) == 1 and isinstance(r[0],__FNCT): r = r[0]()
        elif r: r = ' '.join(str(x) for x in r)
        else: r = ''
        raise err(r)

def swap32(i:bytes):
    c = len(i) // 4
    return struct.pack(f'>{c}I',*struct.unpack(f'<{c}I',i))
def reflecti(v:int,w:int):
    r = 0
    for _ in range(w):
        r = (r << 1) | (v & 1)
        v >>= 1
    return r

UPXX = None
def uxx():
    global UPXX
    if UPXX is None: UPXX = X()
    return UPXX

MMFS_DEC = {}
FH3N_DEC = {}
BASEXX_DEC = {
    'b58':'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
    'b92':'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~+!$%\'()*,:@/?;^{}[]<>&|"=`',
    'g64':'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789[]',
    'z32':'ybndrfg8ejkmcpqxot1uwisza345h769',
    'c32':'0123456789ABCDEFGHJKMNPQRSTVWXYZ',
    'n32':'0123456789BCDFGHJKLMNPQRSTVWXYZ.',
}
BASEXXNS = {'base16':'b16',
            'base32':'b32','base32hex':'b32hex','b32h':'b32hex',
            'base58':'b58',
            'base64':'b64',
            'base85':'b85','ascii85':'a85',
            'base92':'b92',
            'gamespy64':'g64',
            'zbase32':'z32',
            'cbase32':'c32','crockford32':'c32',
            'nin32':'n32','nintendo32':'n32',}
def decrypt(i:bytes,algo:str,key:bytes=None,iv:bytes=None,**kwargs) -> bytes:
    match algo:
        case 'xor':
            if isinstance(key,int): key = key.to_bytes(1)
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_xor(i,key or b'\0')
        case 'rxor': return uxx().decrypt_rxor(i,key or b'\0')
        case 'cxor':
            if isinstance(key,int): key = key.to_bytes(1)
            if isinstance(iv,bytes): iv = iv[0]
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_cxor(i,key or b'\0',iv or 0)
        case 'dxor':
            if type(key) == int: key = key.to_bytes(1)
            if type(iv) == int: iv = iv.to_bytes(1)
            asrt(isinstance(key,bytes) and isinstance(iv,bytes),err=TypeError)
            return uxx().decrypt_dxor(i,key or b'\0',iv or b'\0')
        case 'inv'|'invert': return uxx().decrypt_inv(i)
        case 'inv_len': return uxx().decrypt_xor(i,(-1 - len(i)).to_bytes(1,signed=True))
        case 'swp4'|'swap4': return uxx().decrypt_swp4(i)
        case 'roll':
            if type(key) == int: key = key.to_bytes(1)
            return uxx().decrypt_roll(i,key or b'\0')
        case 'rolr':
            if type(key) == int: key = key.to_bytes(1)
            return uxx().decrypt_rolr(i,key or b'\0')

        case 'aes'|'aes_cbc'|'aes_ecb'|'aes_ctr'|'aes_ctr_be'|'aes_ctr_le'|'aes_gcm':
            from Cryptodome.Cipher import AES
            m = algo[4:-3 if algo.endswith(('_be','_le')) else None] or 'cbc'

            kw = kwargs
            if m in {'ccm','eax','gcm','siv','ocb'}: kw['nonce'] = iv
            elif m in {'cbc','cfb','ofb','openpgp'}: kw['iv'] = iv
            elif m == 'ctr' and iv is not None:
                from Cryptodome.Util import Counter
                if isinstance(iv,bytes): iv = int.from_bytes(iv,'little' if algo.endswith('_le') else 'big')
                asrt(isinstance(iv,int),err=TypeError)
                kw['counter'] = Counter.new(len(key)*8,initial_value=iv,little_endian=algo.endswith('_le'),allow_wraparound=True)
            obj = AES.new(key,mode=getattr(AES,f'MODE_{m.upper()}'),**kw)
            if i is None: return obj

            return obj.decrypt(i)
        case 'aes_xts':
            from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes

            c = Cipher(algorithms.AES(key),modes.XTS(iv))
            return c.decryptor().update(i) + c.decryptor().finalize()
        case 'aes_xts_sec'|'aes_xts_sec_be'|'aes_xts_sec_le':
            asrt('sector_size' in kwargs,err=TypeError)
            secs,sec = kwargs['sector_size'],iv or 0
            asrt(isinstance(sec,int) and isinstance(secs,int),err=TypeError)
            asrt(len(i) % secs == 0)

            from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
            end = 'little' if algo.endswith('_le') else 'big'

            od = []
            for ix in range(len(i)//secs):
                c = Cipher(algorithms.AES(key),modes.XTS((sec + ix).to_bytes(16,end)))
                od.append(c.decryptor().update(i[ix*secs:(ix+1)*secs]) + c.decryptor().finalize())

            return b''.join(od)
        case 'blowfish'|'blowfish_ecb'|'blowfish_cbc':
            from Cryptodome.Cipher import Blowfish
            m = algo[9:] or 'ecb'

            kw = kwargs
            if m in {'cbc','cfb','ofb','openpgp'}: kw['iv'] = iv
            elif m in {'eax','ctr'}: kw['nonce'] = iv

            return Blowfish.new(key,getattr(Blowfish,f'MODE_{m.upper()}'),**kw).decrypt(i)
        case 'blowfish_le'|'blowfish_le_ecb': return swap32(decrypt(swap32(i),'blowfish' + algo[12:],key,iv))
        case 'salsa20':
            import ctypes
            from Cryptodome.Cipher import Salsa20
            ctx = Salsa20.new(key,iv[:8])
            pctx = ctypes.cast(ctx._state.get(),ctypes.POINTER(ctypes.c_uint32))

            bc = None
            if 'block_count' in kwargs: bc = kwargs['block_count']
            elif len(iv) > 8:
                asrt(len(iv) <= 16)
                bc = int.from_bytes(iv[8:16],'little') # using int.from_bytes instead of struct to support len(iv) != 16
            if bc is not None:
                pctx[8],pctx[9] = bc & 0xFFFFFFFF,(bc >> 32) & 0xFFFFFFFF # stream_state->input[8/9] = block count

            o = ctx.decrypt(i)
            if kwargs.get('return_block_count'): return o,pctx[8] | (pctx[9] << 32)
            return o
        case 'chacha20'|'xchacha20'|'tls_chacha20':
            from Cryptodome.Cipher import ChaCha20
            return ChaCha20.new(key,iv).decrypt(i)
        case 'chacha20_poly1305'|'xchacha20_poly1305'|'tls_chacha20_poly1305':
            from Cryptodome.Cipher import ChaCha20_Poly1305
            obj = ChaCha20_Poly1305.new(key,iv)
            if 'tag' in kwargs: tag = kwargs['tag']
            else: tag = i[-16:]
            if tag: return obj.decrypt_and_verify(i[:-16 if not 'tag' in kwargs else None],tag)
            return obj.decrypt(i)
        case 'rc4'|'arc4':
            from Cryptodome.Cipher import ARC4
            return ARC4.new(key,drop=iv or 0).decrypt(i)
        case 'rsa'|'rsa_le':
            from Cryptodome.PublicKey import RSA
            if type(key) == int and type(iv) == int: k = RSA.construct((key,iv))
            elif type(key) == int and iv is None: k = RSA.construct((key,0x10001))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            asrt(k.size_in_bytes() == len(i))
            return pow(int.from_bytes(i,'little' if algo == 'rsa_le' else 'big'),k.e,k.n).to_bytes(k.size_in_bytes(),'big')
        case 'rsa2048_oeap_hash':
            asrt('label_hash' in kwargs and len(kwargs['label_hash']) == 0x20,err=TypeError)

            import hashlib
            def mgf1_xor(d:bytearray,h:bytes):
                of = 0
                seed = 0
                while of < len(d):
                    mgf = hashlib.sha256(h + seed.to_bytes(4,'big')).digest()
                    for i in range(min(len(d)-of,0x20)):
                        d[of+i] ^= mgf[i]
                    of += 0x20
                    seed += 1

            from Cryptodome.PublicKey import RSA
            if type(key) == bytes and type(iv) == bytes:
                asrt(len(key) == len(iv) == 0x100)
                key,iv = int.from_bytes(key,'big'),int.from_bytes(iv,'big')
            if type(key) == int and type(iv) == int: k = RSA.construct((key,iv))
            elif type(key) == int and iv is None: k = RSA.construct((key,0x10001))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            c = int.from_bytes(i,'big')
            m = pow(c,k.e,k.n).to_bytes(0x100,'big')
            if m[0] != 0: return None

            seed = bytearray(m[1:0x21])
            db = bytearray(m[0x21:])
            mgf1_xor(seed,bytes(db))
            seed = bytes(seed)
            mgf1_xor(db,seed)
            db = bytes(db)

            if db[:0x20] != kwargs['label_hash']: return None
            of = 0x20
            while of < len(db) and of < 0xBF and db[of] == 0: of += 1
            if of == 0xBF or db[of] != 1: return None
            of += 1
            return db[of:]
        case 'rsa_inv'|'rsa_inv_le':
            asrt('r' in kwargs)

            from Cryptodome.PublicKey import RSA
            if type(key) == int and type(iv) == int: k = RSA.construct((key,iv))
            elif type(key) == int and iv is None: k = RSA.construct((key,0x10001))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            asrt(k.size_in_bytes() == len(i))
            c = pow(int.from_bytes(i,'little' if algo == 'rsa_inv_le' else 'big'),k.e,k.n)
            R = pow(pow(pow(2,k.size_in_bits()),-1,k.n),kwargs['r'],k.n)
            return ((c * R) % k.n).to_bytes(k.size_in_bytes(),'big')
        case 'tea'|'tea_be'|'tea_le': return uxx().decrypt_tea(i,key,le=algo == 'tea_le')
        case 'tea_pad'|'tea_pad_be'|'tea_pad_le':
            lo = len(i) % 8
            return uxx().decrypt_tea(i[:-lo or None],key,le=algo == 'tea_pad_le') + (i[-lo:] if lo else b'')
        case 'transformit'|'tfit':
            return uxx().decrypt_tfit(i,key,kwargs['table'],iv,kwargs['block_size'])

        case 'rsdk3':
            asrt(isinstance(key,bytes) and isinstance(iv,bytes),err=TypeError)
            return uxx().decrypt_rsdk3(i,key,iv)
        case 'rsdk4':
            asrt(isinstance(key,int) and isinstance(iv,int),err=TypeError)
            return uxx().decrypt_rsdk4(i,key,iv)
        case 'rsdk5':
            if isinstance(key,str): key = swap32(crc_hash(key.upper().encode('utf-8'),'md5',bytes=True))
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_rsdk5(i,key)
        case 'hatch':
            if isinstance(key,int): key = key.to_bytes(4,'little')
            asrt(isinstance(key,bytes),err=TypeError)
            if len(key) == 4: key = key*4
            return uxx().decrypt_hatch(i,key)
        case 'capcom_mame':
            if type(iv) == str: iv = iv.encode('ascii')
            key = [iv[3],key[0],iv[1],key[1],iv[0],key[2],iv[2],key[3]]
            for ix,b in enumerate(iv[4:]): key[ix % 8] ^= b
            return decrypt(i,'xor',bytes(key))
        case 'mmfs':
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_mmfs(i,key)
        case 'rc4_pp'|'rc4_playpond':
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_rc4_playpond(i,key,iv or 0)
        case 'hornby':
            iv = iv or 0xFF
            if isinstance(iv,bytes): iv = iv[0]
            asrt(isinstance(iv,int) and isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_hornby(i,key or b'\0',iv)
        case 'selene':
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_selene(i,key or b'\0')
        case 'fh3name':
            istr = isinstance(i,str)
            if istr:
                i = i.encode('latin-1')
            if isinstance(key,dict):
                kh = hash(tuple(key.items()))
                if kh in FH3N_DEC: k = FH3N_DEC[kh]
                else:
                    k = bytearray(0x100)
                    for ix in range(0x100):
                        if ix in key: v = key[ix]
                        elif chr(ix) in key: v = key[chr(ix)]
                        elif ix.to_bytes(1) in key: v = key[ix.to_bytes(1)]
                        else: v = ix
                        if isinstance(v,str): v = v.encode('latin-1')[0]
                        elif isinstance(v,bytes): v = v[0]
                        k[ix] = v
                    k = bytes(k)
                    FH3N_DEC[kh] = k
            else: k = key
            asrt(isinstance(i,bytes) and isinstance(k,bytes) and len(k) == 0x100,err=TypeError)
            r = i.translate(k)
            if istr: r = r.decode('latin-1')
            return r
        case 'remedy_ras':
            if isinstance(key,bytes): key = int.from_bytes(key,'little')
            asrt(isinstance(key,int),err=TypeError)
            return uxx().decrypt_remedy_ras(i,key)
        case 'empire_magic':
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_empire_magic(i,key,kwargs.get('key_end',False))

        case 'ddhex4': return uxx().decrypt_swp4(bytes.fromhex(i))
        case 'hex': return bytes.fromhex(i)
        case 'base64url'|'b64url':
            from urllib.parse import unquote_to_bytes
            return decrypt(unquote_to_bytes(i),'base64',**kwargs)
        case 'base16'|'base32'|'base32hex'|'base64'|'base85'|'ascii85'|\
             'b16'|'b32'|'b32hex'|'b32h'|'b64'|'b85'|'a85'|'z85':
            algo = BASEXXNS.get(algo,algo)
            import base64
            if algo == 'b64' and len(i) % 4 and kwargs.get('fix'):
                if isinstance(i,str): i = i.encode('latin-1')
                i += b'=' * (-len(i) % 4)

            return getattr(base64,algo + 'decode')(i)
        case 'base92'|'base58'|'gamespy64'|'zbase32'|'cbase32'|'crockford32'|'nin32'|'nintendo32'|\
             'b92'|'b58'|'g64'|'z32'|'c32'|'n32':
            algo = BASEXXNS.get(algo,algo)
            if isinstance(BASEXX_DEC[algo],str): BASEXX_DEC[algo] = BaseXX(BASEXX_DEC[algo])
            if isinstance(i,bytes): i = i.decode('latin-1')
            r = BASEXX_DEC[algo].decode(i)
            if kwargs.get('bytes',True): return r
            return r.decode('latin-1')
        case 'basexx'|'bxx':
            asrt(isinstance(key,str),err=TypeError)
            if key not in BASEXX_DEC: BASEXX_DEC[key] = BaseXX(key)
            if isinstance(i,bytes): i = i.decode('latin-1')
            r = BASEXX_DEC[key].decode(i)
            if kwargs.get('bytes',True): return r
            return r.decode('latin-1')
        case 'uu'|'uue'|'uuencode'|'uuencoded':
            if isinstance(i,str): i = i.encode('latin-1')
            import binascii
            r = []
            for l in i.splitlines():
                try: r.append(binascii.a2b_uu(l))
                except binascii.Error:
                    r.append(binascii.a2b_uu(l[:(((ord(l[0])-32) & 63) * 4 + 5) // 3]))
            return b''.join(r)
        case 'url'|'urldecode'|'urlencode':
            from urllib.parse import unquote,unquote_to_bytes

            if not kwargs.get('bytes',True): return unquote(i,errors='strict')
            return unquote_to_bytes(i)

    raise NotImplementedError(algo)
def encrypt(i:bytes,algo:str,key:bytes=None,iv:bytes=None,**kwargs) -> bytes:
    match algo:
        case 'xor':
            if isinstance(key,int): key = key.to_bytes(1)
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_xor(i,key or b'\0')
        case 'inv'|'invert': return uxx().decrypt_inv(i)
        case 'inv_len': return uxx().decrypt_xor(i,(-1 - len(i)).to_bytes(1,signed=True))
        case 'swp4'|'swap4': return uxx().decrypt_swap4(i)
        case 'roll':
            if type(key) == int: key = key.to_bytes(1)
            return uxx().decrypt_rolr(i,key or b'\0')
        case 'rolr':
            if type(key) == int: key = key.to_bytes(1)
            return uxx().decrypt_roll(i,key or b'\0')

        case 'zrif'|'zrif_b64':
            asrt(len(key) == 0x400)
            import zlib
            c = zlib.compressobj(level=9,wbits=10,memlevel=8,zdict=key)
            bn = c.compress(i) + c.flush()
            if len(bn) % 3: bn += bytes(3 - len(bn) % 3)
            if algo == 'zrif_b64':
                import base64
                return base64.b64encode(bn).decode('latin-1')
            return bn

        case 'hex':
            r = i.hex()
            return r if kwargs.get('bytes',False) else r.encode('ascii')
        case 'base16'|'base32'|'base32hex'|'base64'|'base85'|'ascii85'|\
             'b16'|'b32'|'b32hex'|'b32h'|'b64'|'b85'|'a85'|'z85':
            algo = BASEXXNS.get(algo,algo)
            import base64
            r = getattr(base64,algo + 'encode')(i)
            return r if kwargs.get('bytes',True) else r.decode('latin-1')
        case 'base92'|'base58'|'gamespy64'|'zbase32'|'cbase32'|'crockford32'|'nin32'|'nintendo32'|\
             'b92'|'b58'|'g64'|'z32'|'c32'|'n32':
            algo = BASEXXNS.get(algo,algo)
            if isinstance(BASEXX_DEC[algo],str): BASEXX_DEC[algo] = BaseXX(BASEXX_DEC[algo])
            if isinstance(i,str): i = i.encode('latin-1')
            r = BASEXX_DEC[algo].encode(i)
            if kwargs.get('bytes',True): return r.encode('latin-1')
            return r
        case 'basexx'|'bxx':
            asrt(isinstance(key,str),err=TypeError)
            if key not in BASEXX_DEC: BASEXX_DEC[key] = BaseXX(key)
            if isinstance(i,str): i = i.encode('latin-1')
            r = BASEXX_DEC[key].encode(i)
            if kwargs.get('bytes',True): return r.encode('latin-1')
            return r
        case 'url'|'urldecode'|'urlencode':
            from urllib.parse import quote,quote_from_bytes

            r = (quote_from_bytes if isinstance(i,bytes) else quote)(i,safe='' if kwargs.get('plus',True) else '/',encoding='utf-8',errors='strict')
            return r.encode('utf-8') if kwargs.get('bytes',False) else r
class BaseXX:
    def __init__(self,alphabet:str):
        asrt(len(alphabet) > 1 and len(set(alphabet)) == len(alphabet))
        self.alpha = alphabet
        self.base = len(alphabet)
        self.null = alphabet[0]
        self.lookup = {c:i for i,c in enumerate(alphabet)}

    def encode(self,d:bytes):
        if not d: return ""

        zc = 0
        for b in d:
            if b != 0: break
            zc += 1

        n = int.from_bytes(d,'big')
        r = []
        while n:
            n,rem = divmod(n,self.base)
            r.append(self.alpha[rem])
        r.extend([self.null] * zc)
        return ''.join(reversed(r))
    def decode(self,s:str):
        if not s: return b""

        zc = 0
        for c in s:
            if c != self.null: break
            zc += 1

        n = 0
        for c in s: n = n * self.base + self.lookup[c]
        if n: r = n.to_bytes((n.bit_length() + 7) // 8,'big')
        return (b'\0' * zc) + r

CRC_LUT = {}
def crc(i:bytes,size:int,poly:int,init:int,xor:int,reflect:bool,value:int=None) -> int:
    k = (poly,reflect,size)
    mmsk = (1 << size) - 1
    if not k in CRC_LUT:
        lut = []
        if reflect:
            poly = reflecti(poly,size)
            for b in range(256):
                crc = b
                for _ in range(8):
                    if crc & 1: crc = (crc >> 1) ^ poly
                    else: crc >>= 1
                lut.append(crc)
        else:
            msk1,sv = 1 << (size - 1),size - 8
            for b in range(256):
                crc = b << sv
                for _ in range(8):
                    if crc & msk1: crc = (crc << 1) ^ poly
                    else: crc <<= 1
                    crc &= mmsk
                lut.append(crc)
        CRC_LUT[k] = tuple(lut)
    lut = CRC_LUT[k]

    crc = init if value is None else (value ^ xor)
    if reflect:
        for b in i: crc = (crc >> 8) ^ lut[(b ^ crc) & 0xFF]
    else:
        msk1,sv = 1 << (size - 1),size - 8
        for b in i: crc = ((crc << 8) & mmsk) ^ lut[(b ^ (crc >> sv)) & 0xFF]
    return crc ^ xor
def crc8(i:bytes,poly=0x7,init=0,xor=0,reflect=False,value:int=None): return crc(i,8,poly,init,xor,reflect,value)
def crc16(i:bytes,poly=0x8005,init=0,xor=0,reflect=True,value:int=None): return crc(i,16,poly,init,xor,reflect,value)
def crc24(i:bytes,poly=0x864CFB,init=0xB7074CE,xor=0,reflect=False,value:int=None): return crc(i,24,poly,init,xor,reflect,value)
def crc32(i:bytes,poly=0x04C11DB7,init=0xFFFFFFFF,xor=0xFFFFFFFF,reflect=True,value:int=None): return crc(i,32,poly,init,xor,reflect,value)
def crc64(i:bytes,poly=0x42F0E1EBA9EA3693,init=0x0000000000000000,xor=0x0000000000000000,reflect=False,value:int=None): return crc(i,64,poly,init,xor,reflect,value)
def fletcher(i:bytes,size:int):
    msk = (1 << size) - 1
    s1,s2 = 0,0
    for b in i:
        s1 = (s1 + b) & msk
        s2 = (s2 + s1) & msk
    return (s2 << size) | s1
def fnv1_64(i:bytes,prime=0x100000001B3,offset=0xCBF29CE484222645):
    for b in i: offset = ((offset * prime) & 0xFFFFFFFFFFFFFFFF) ^ b
    return offset
def fnv1a_64(i:bytes,prime=0x100000001B3,offset=0xCBF29CE484222645):
    for b in i: offset = ((offset ^ b) * prime) & 0xFFFFFFFFFFFFFFFF
    return offset
def fnv1_32(i:bytes,prime=0x1000193,offset=0x811C9DC5):
    for b in i: offset = ((offset * prime) & 0xFFFFFFFF) ^ b
    return offset
def fnv1a_32(i:bytes,prime=0x1000193,offset=0x811C9DC5):
    for b in i: offset = ((offset ^ b) * prime) & 0xFFFFFFFF
    return offset
def bkdr(i:bytes,seed=131,init=0):
    h = init
    for b in i: h = (h * seed + b) & 0xFFFFFFFF
    return h
def sdbm(i:bytes,seed=0x1003F,init=0):
    h = init
    for b in i: h = ((h + b) * seed) & 0xFFFFFFFF
    return h
def djb2(i:bytes,init=5381):
    h = init
    for b in i: h = ((h << 5) + h + b) & 0xFFFFFFFF
    return h
def djb2a(i:bytes,init=5381):
    h = init
    for b in i: h = (((h << 5) + h) ^ b) & 0xFFFFFFFF
    return h
def joaat(i:bytes,init=0):
    h = init
    for b in i:
        h = (h + b) & 0xFFFFFFFF
        h = (h + (h << 10)) & 0xFFFFFFFF
        h ^= (h >> 6)

    h = (h + (h << 3)) & 0xFFFFFFFF
    h ^= (h >> 11)
    return (h + (h << 15)) & 0xFFFFFFFF
def tarzan_hash(i:bytes):
    o = 0
    shft = 0
    lng =  0

    for b in i:
        o += b << shft
        shft += 8
        if shft > 24: shft = 0
        lng += 1
    return (o + lng) & 0xFFFFFFFF
def luas_hash(i:bytes):
    stp = (len(i) >> 5) + 1
    o = p = len(i)
    while p >= stp:
        o ^= (o * 0x20 + (o >> 2) + i[p - 1]) & 0xFFFFFFFF
        p -= stp
    return o
def java_hash(i:bytes):
    h = 0
    for b in i: h = (h * 31 + b) & 0xFFFFFFFF
    return h
def sxm_hash(i:bytes):
    v = 0
    for b in i: v = ((v * 137) + b) & 0xFFFFFFFFFFFFFFFF
    return v
def slf_hash(i:bytes):
    h = 0
    for b in i: h = (h * 33 + b) & 0xFFFFFFFF
    return h

CRC8 = {   #  poly,init,xor ,reflect
 'tech_3250':(0x1D,0xFF,0x00,True ),
    'gsm':   (0x1D,0x00,0x00,False),'gsm_a':(0x1D,0,0,False),
'mifare_mad':(0x1D,0xC7,0x00,False),
    'icode': (0x1D,0xFD,0x00,False),
    'hitag': (0x1D,0xFF,0x00,False),
    'j1850': (0x1D,0xFF,0xFF,False),'sae_j1850':(0x1D,0xFF,0xFF,False),
    'rohc':  (0x07,0xFF,0x00,True ),
    'smbus': (0x07,0x00,0x00,False),'atm':(0x07,0,0,False), # default
    'itu':   (0x07,0x00,0x55,False),'i432_1':(0x07,0,0x55,False),
    'wcdma': (0x9B,0x00,0x00,True ),
    'lte':   (0x9B,0x00,0x00,False),
  'cdma2000':(0x9B,0xFF,0x00,False),
    'maxim': (0x31,0x00,0x00,True ),'maxim_dow':(0x31,0,0,True),
    'nrsc5': (0x31,0xFF,0x00,False),
'opensafety':(0x2F,0x00,0x00,False),
   'autosar':(0x2F,0xFF,0xFF,False),
    'darc':  (0x39,0x00,0x00,True ),
    'gsm_b': (0x49,0x00,0xFF,False),
    'ccitt': (0x8D,0x00,0x00,False),
 'bluetooth':(0xA7,0x00,0x00,True ),
    'dvb_s2':(0xD5,0x00,0x00,False),
}
CRC16 = {   # poly  , init , xor  , reflect
    'latin1':  (0x8005,0x0000,0x0000,True ),'ibm':(0x8005,0,0,True),'arc':(0x8005,0,0,True),'lha':(0x8005,0,0,True), # default
    'maxim': (0x8005,0x0000,0xFFFF,True ),'maxim_dow':(0x8005,0,0xFFFF,True),
    'modbus':(0x8005,0xFFFF,0x0000,True ),
    'usb':   (0x8005,0xFFFF,0xFFFF,True ),
    'umts':  (0x8005,0x0000,0x0000,False),'buypass':(0x8005,0,0,False),'verifone':(0x8005,0,0,False),
   'dds_110':(0x8005,0x800D,0x0000,False),
    'cms':   (0x8005,0xFFFF,0x0000,False),
    'kermit':(0x1021,0x0000,0x0000,True ),'ccitt':(0x1021,0,0,True),'ccitt_true':(0x1021,0,0,True),
  'tms37157':(0x1021,0x89EC,0x0000,True ),
    'riello':(0x1021,0xB2AA,0x0000,True ),
'iso_iec_14443_3_a':(0x1021,0xC6C6,0,True),
   'mcrf4xx':(0x1021,0xFFFF,0x0000,True ),
    'x25':   (0x1021,0xFFFF,0xFFFF,True ),'ibm_sdlc':(0x1021,0xFFFF,0xFFFF,True),'iso_hdlc':(0x1021,0xFFFF,0xFFFF,True),
    'xmodem':(0x1021,0x0000,0x0000,False),'zmodem':(0x1021,0,0,False),'acorn':(0x1021,0,0,False),
    'gsm':   (0x1021,0x0000,0xFFFF,False),
'spi_fujitsu':(0x1021,0x1D0F,0x000,False),'aug_ccitt':(0x1021,0x1D0F,0,False),
'ccitt_false':(0x1021,0xFFFF,0x000,False),'ibm_3740':(0x1021,0xFFFF,0,False),
   'genibus':(0x1021,0xFFFF,0xFFFF,False),'icode':(0x1021,0xFFFF,0xFFFF,False),'darc':(0x1021,0xFFFF,0xFFFF,False),'epc':(0x1021,0xFFFF,0xFFFF,False),
'opensafety':(0x5935,0x0000,0x0000,False),'opensafety_a':(0x5935,0,0,False),
    'm17':   (0x5935,0xFFFF,0x0000,False),
    'dnp':   (0x3D65,0x0000,0xFFFF,True ),
   'en13757':(0x3D65,0x0000,0xFFFF,False),
    'dect_r':(0x0589,0x0000,0x0001,False),
    'dect_x':(0x0589,0x0000,0x0000,False),
'opensafety_b':(0x755B,0x00,0x0000,False),
  'teledisk':(0xA097,0x0000,0x0000,False),
   't10_dif':(0x8BB7,0x0000,0x0000,False),
  'profibus':(0x1DCF,0xFFFF,0xFFFF,False),
    'nrsc5': (0x080B,0xFFFF,0x0000,True ),
    'lj1200':(0x6F63,0x0000,0x0000,False),
  'cdma2000':(0xC867,0xFFFF,0x0000,False),
}
CRC24 = {   # poly    , init   , xor    , reflect
    'lte':   (0x864CFB,0x000000,0x000000,False),'lte_a':(0x864CFB,0,0,False),
   'openpgp':(0x864CFB,0xB704CE,0x000000,False), # default
   'flexray':(0x5D6DCB,0xFEDCBA,0x000000,False),'flexray_a':(0x5D6DCB,0xFEDCBA,0,False),
 'flexray_b':(0x5D6DCB,0xABCDEF,0x000000,False),
    'lte_b': (0x800063,0x000000,0x000000,False),
    'os9':   (0x800063,0xFFFFFF,0xFFFFFF,False),
    'ble':   (0x00065B,0x555555,0x000000,True ),
'interlaken':(0x328B63,0xFFFFFF,0xFFFFFF,False),
}
CRC32 = {   # poly      , init     , xor      , reflect
    'ludia': (0x04C11DB7,0x00000000,0x00000000,True ),
    'jamcrc':(0x04C11DB7,0xFFFFFFFF,0x00000000,True ),
    'ieee':  (0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True ),'iso':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True),'iso_hdlc':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True), # default
    'adccp': (0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True ),'pkzip':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True),'xz':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True),'v42':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,True), # default
    'mpeg2': (0x04C11DB7,0xFFFFFFFF,0x00000000,False),
    'posix': (0x04C11DB7,0x00000000,0xFFFFFFFF,False),'cksum':(0x04C11DB7,0,0xFFFFFFFF,False),
    'bzip2': (0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),'aal5':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),'dect_b':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),'b':(0x04C11DB7,0xFFFFFFFF,0xFFFFFFFF,False),
    'mef':   (0x741B8CD7,0xFFFFFFFF,0x00000000,True ),
    'k':     (0x741B8CD7,0xFFFFFFFF,0xFFFFFFFF,True ),'koopman':(0x741B8CD7,0xFFFFFFFF,0xFFFFFFFF,True),
    'xfer':  (0x000000AF,0x00000000,0x00000000,False),
   'autosar':(0xF4ACFB13,0xFFFFFFFF,0xFFFFFFFF,True ),
    'c':     (0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True ),'castagnoli':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),'iscsi':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),'base91_c':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),
'intrelaken':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True ),'nvme':(0x1EDC6F41,0xFFFFFFFF,0xFFFFFFFF,True),
    'd':     (0xA833982B,0xFFFFFFFF,0xFFFFFFFF,True ),'base94':(0xA833982B,0xFFFFFFFF,0xFFFFFFFF,True),'base94_d':(0xA833982B,0xFFFFFFFF,0xFFFFFFFF,True),
    'q':     (0x814141AB,0x00000000,0x00000000,False),'aixm':(0x814141AB,0,0,False),
'cd_rom_edc':(0x8001801B,0x00000000,0x00000000,True ),
}
CRC64 = {   # poly              , init             , xor              , reflect
    'xz':    (0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True ),'go_ecma':(0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True),
    'ecma':  (0x42F0E1EBA9EA3693,0x0000000000000000,0x0000000000000000,False),'ecma_182':(0x42F0E1EBA9EA3693,0,0,False), # default
    'we':    (0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,False),
    'redis': (0xAD93D23594C935A9,0x0000000000000000,0x0000000000000000,True ),
    'jones': (0xAD93D23594C935A9,0xFFFFFFFFFFFFFFFF,0x0000000000000000,True ),
    'ms':    (0x259C84CBA6426349,0xFFFFFFFFFFFFFFFF,0x0000000000000000,True ),
    'go_iso':(0x000000000000001B,0x0000000000000000,0x0000000000000000,True ),
    'nvme':  (0xAD93D23594C93659,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True ),
}
def crc_hash(i:bytes,algo:str,**kwargs) -> int:
    match algo:
        case 'crc8': fnc = crc8
        case 'crc16': fnc = crc16
        case 'crc24': fnc = crc24
        case 'crc32'|'crc32_ieee'|'crc32_iso'|'crc32_iso_hdlc'|'crc32_adccp'|'crc32_pkzip':
            import zlib
            return zlib.crc32(i,kwargs.get('value') or 0)
        case 'crc64': fnc = crc64
        case 'crc8_tech_3250'|'crc8_gsm'|'crc8_gsm_a'|'crc8_mifare_mad'|'crc8_icode'|'crc8_hitag'|\
             'crc8_j1850'|'crc8_sae_j1850'|'crc8_rohc'|'crc8_smbus'|'crc8_atm'|'crc8_itu'|'crc8_i432_1'|\
             'crc8_wcdma'|'crc8_lte'|'crc8_cdma2000'|'crc8_maxim'|'crc8_maxim_dow'|'crc8_nrsc5'|\
             'crc8_opensafety'|'crc8_autosar'|'crc8_darc'|'crc8_gsm_b'|'crc8_ccitt'|'crc8_bluetooth'|\
             'crc8_dvb_s2':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC8[algo[5:]]
            fnc = crc8
        case 'crc16_ansi'|'crc16_ibm'|'crc16_arc'|'crc16_lha'|'crc16_maxim'|'crc16_maxim_dow'|'crc16_modbus'|\
             'crc16_usb'|'crc16_umts'|'crc16_buypass'|'crc16_verifone'|'crc16_dds_110'|'crc16_cms'|'crc16_kermit'|\
             'crc16_ccitt'|'crc16_ccitt_true'|'crc16_tms37157'|'crc16_riello'|'crc16_iso_iec_14443_3_a'|\
             'crc16_mcrf4xx'|'crc16_x25'|'crc16_ibm_sdlc'|'crc16_iso_hdlc'|'crc16_xmodem'|'crc16_zmodem'|'crc16_acorn'|\
             'crc16_gsm'|'crc16_spi_fujitsu'|'crc16_aug_ccitt'|'crc16_ccitt_false'|'crc16_ibm_3740'|'crc16_genibus'|\
             'crc16_icode'|'crc16_darc'|'crc16_opensafety'|'crc16_opensafety_a'|'crc16_m17'|'crc16_dnp'|'crc16_en13757'|\
             'crc16_dect_r'|'crc16_dect_x'|'crc16_opensafety_b'|'crc16_teledisk'|'crc16_t10_dif'|'crc16_profibus'|\
             'crc16_nrsc5'|'crc16_lj1200'|'crc16_cdma2000'|'crc16_epc':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC16[algo[6:]]
            fnc = crc16
        case 'crc24_lte'|'crc24_lte_a'|'crc24_openpgp'|'crc24_flexray'|'crc24_flexray_a'|'crc24_flexray_b'|\
             'crc24_lte_b'|'crc24_os9'|'crc24_ble'|'crc24_interlaken':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC24[algo[6:]]
            fnc = crc24
        case 'crc32_jamcrc'|'crc32_ieee'|'crc32_iso'|'crc32_iso_hdlc'|'crc32_adccp'|'crc32_pkzip'|'crc32_xz'|'crc32_v42'|\
             'crc32_mpeg2'|'crc32_posix'|'crc32_cksum'|'crc32_bzip2'|'crc32_aal5'|'crc32_dect_b'|'crc32b'|'crc32_mef'|\
             'crc32k'|'crc32_koopman'|'crc32_xfer'|'crc32_autosar'|'crc32c'|'crc32_castagnoli'|'crc32_iscsi'|\
             'crc32_base91_c'|'crc32_intrelaken'|'crc32_nvme'|'crc32d'|'crc32_base94'|'crc32_base94_d'|'crc32q'|\
             'crc32_aixm'|'crc32_cd_rom_edc'|'crc32_ludia':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC32[algo[5 + (1 if algo[5] == '_' else 0):]]
            fnc = crc32
        case 'crc64_xz'|'crc64_go_ecma'|'crc64_ecma'|'crc64_ecma_182'|'crc64_we'|'crc64_redis'|'crc64_jones'|'crc64_ms'|\
             'crc64_go_iso'|'crc64_nvme':
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC64[algo[6:]]
            fnc = crc64

        case 'crc40_gsm':
            kwargs['size'] = 40
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = {
                'gsm':(0x0004820009,0x0000000000,0x0000000000,False)
            }[algo[6:]]
            fnc = crc

        case 'adler32':
            import zlib
            if 'init' in kwargs: kwargs['value'] = kwargs.pop('init')
            fnc = zlib.adler32
        case 'fnv1_32': fnc = fnv1_32
        case 'fnv1a_32': fnc = fnv1a_32
        case 'fnv1_64': fnc = fnv1_64
        case 'fnv1a_64': fnc = fnv1a_64
        case 'bkdr'|'bkdr_ltr': fnc = bkdr
        case 'bkdr_rtl':
            i = i[::-1]
            fnc = bkdr
        case 'sdbm'|'sdbm_ltr': fnc = sdbm
        case 'sdbm_rtl':
            i = i[::-1]
            fnc = sdbm
        case 'djb2'|'djb2_ltr': fnc = djb2
        case 'djb2_rtl':
            i = i[::-1]
            fnc = djb2
        case 'djb2a'|'djb2a_ltr': fnc = djb2a
        case 'djb2a_rtl':
            i = i[::-1]
            fnc = djb2a
        case 'joaat': fnc = joaat
        case 'super_fast'|'super_fast_le': fnc = uxx().hash_super_fast_le
        case 'super_fast_be': fnc = uxx().hash_super_fast_be
        case 'elf'|'pjw': fnc = uxx().hash_elf
        case 'aphash': fnc = uxx().hash_ap
        case 'murmur2'|'mmh2'|'murmur2_32'|'mmh2_32'|'murmur2_le'|'mmh2_le'|'murmur2_32_le'|'mmh2_32_le':
            fnc = uxx().hash_murmur2_le
            if not 'seed' in kwargs: kwargs['seed'] = 0x9747b28c
        case 'murmur2_be'|'mmh2_be'|'murmur2_32_be'|'mmh2_32_be':
            fnc = uxx().hash_murmur2_be
            if not 'seed' in kwargs: kwargs['seed'] = 0x9747b28c
        case 'murmur2a'|'mmh2a'|'murmur2_32a'|'mmh2_32a'|'murmur2a_le'|'mmh2a_le'|'murmur2_32a_le'|'mmh2_32a_le':
            fnc = uxx().hash_murmur2A_le
            if not 'seed' in kwargs: kwargs['seed'] = 0x9747b28c
        case 'murmur2a_be'|'mmh2a_be'|'murmur2_32a_be'|'mmh2_32a_be':
            fnc = uxx().hash_murmur2A_be
            if not 'seed' in kwargs: kwargs['seed'] = 0x9747b28c
        case 'murmur2_64'|'mmh2_64'|'murmur2_64a'|'mmh2_64a'|'murmur2_64_le'|'mmh2_64_le'|'murmur2_64a_le'|'mmh2_64a_le':
            fnc = uxx().hash_murmur2_64A_le
            if not 'seed' in kwargs: kwargs['seed'] = 0xe17a1465
        case 'murmur2_64_be'|'mmh2_64_be'|'murmur2_64a_be'|'mmh2_64a_be':
            fnc = uxx().hash_murmur2_64A_be
            if not 'seed' in kwargs: kwargs['seed'] = 0xe17a1465
        case 'murmur2_64b'|'mmh2_64b'|'murmur2_64b_le'|'mmh2_64b_le':
            fnc = uxx().hash_murmur2_64B_le
            if not 'seed' in kwargs: kwargs['seed'] = 0xe17a1465
        case 'murmur2_64b_be'|'mmh2_64b_be':
            fnc = uxx().hash_murmur2_64B_be
            if not 'seed' in kwargs: kwargs['seed'] = 0xe17a1465
        case 'murmur3'|'mmh3'|'murmur3_32'|'mmh3_32'|'murmur3_128'|'mmh3_128':
            import mmh3
            return getattr(mmh3,f'mmh3_{"x64_128" if "128" in algo else "32"}_uintdigest')(i,kwargs.get('seed',0) & 0xFFFFFFFF)
        case 'xxh32'|'xxh64'|'xxh3_64'|'xxh128'|'xxh3_128':
            if algo == 'xxh128': algo = 'xxh3_128'
            import xxhash
            fnc = getattr(xxhash,algo + '_' + ('' if kwargs.pop('bytes',False) else 'int') + 'digest')
        case 'spooky2_32'|'spooky2_64'|'spooky2_128':
            import spookyhash
            fnc = getattr(spookyhash,'hash' + algo[8:])
            if algo == 'spooky2_128' and 'seed' in kwargs:
                s = kwargs.pop('seed')
                kwargs['seed1'] = s & 0xFFFFFFFFFFFFFFFF
                kwargs['seed2'] = s >> 64

        case 'sha1'|'sha224'|'sha256'|'sha384'|'sha512'|'sha3_224'|'sha3_256'|'sha3_384'|'sha3_512'|'sha512_224'|'sha512_256'|\
             'blake2b'|'blake2s'|'md5'|'shake128'|'shake_128'|'shake256'|'shake_256'|'ripemd160'|'sm3':
            if algo in {'shake128','shake256'}: algo = algo[:5] + '_' + algo[5:]
            oby = kwargs.pop('bytes',False)
            kw = {}
            if algo in {'shake_128','shake_256'}: kw['length'] = kwargs.pop('digest_size',int(algo[6:]) // 8)

            import hashlib
            r = hashlib.new(algo,i,**kwargs).digest(**kw)
            if oby: return r
            return int.from_bytes(r,'big')
        case 'md5r':
            oby = kwargs.pop('bytes',False)
            import hashlib
            r = hashlib.md5(i).digest()
            r = r[12:16] + r[8:12] + r[4:8] + r[0:4]
            if oby: return r
            return int.from_bytes(r,'big')
        case 'md5_sha1':
            import hashlib
            r = hashlib.md5(i).digest() + hashlib.sha1(i).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')

        case 'cmac_transformit'|'cmac_tfit':
            asrt(isinstance(kwargs['key'],bytes) and isinstance(kwargs['table'],bytes))
            r = uxx().mac_cmac_tfit(i,kwargs['key'],kwargs['table'])
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'ctr_drbg_hmac_sha256':
            asrt(isinstance(kwargs['key'],bytes) and isinstance(kwargs['size'],int))
            import hashlib,hmac

            seed = i[:kwargs.get('seed_size',None)]
            s = kwargs['size']

            o = bytearray()
            c = kwargs.get('init',0)
            while len(o) < s:
                o.extend(hmac.new(kwargs['key'],c.to_bytes(2,'big') + seed,hashlib.sha256).digest())
                c += 1

            return bytes(o)[:s]

        case 'tarzan': fnc = tarzan_hash
        case 'luas': fnc = luas_hash
        case 'java': fnc = java_hash
        case 'sxm': fnc = sxm_hash
        case 'slf': fnc = slf_hash
        case 'hash40':
            import zlib
            return (len(i) << 32) | zlib.crc32(i,kwargs.get('value') or 0)
        case 'pivotal': fnc = uxx().hash_pivotal
        case 'empire_magic': fnc = uxx().hash_empire_magic
        case _: raise NotImplementedError(algo)
    return fnc(i,**kwargs)

HASHTS = {
    f'crc8_{x}':1 for x in CRC8}|{
    f'crc16_{x}':2 for x in CRC16}|{
    f'crc24_{x}':3 for x in CRC24}|{
    f'crc32{"_" if len(x)>1 else ""}{x}':4 for x in CRC32}|{
    f'crc64_{x}':8 for x in CRC64}|\
{
    'crc8':1,'crc16':2,'crc24':3,'crc32':4,'crc40_gsm':5,'crc64':8,
    'adler32':4,
    'fnv1_32':4,'fnv1a_32':4,
    'fnv1_64':8,'fnv1a_64':8,
    'bkdr':4,'bkdr_ltr':4,'bkdr_rtl':4,
    'sdbm':4,'sdbm_ltr':4,'sdbm_rtl':4,
    'djb2':4,'djb2_ltr':4,'djb2_rtl':4,
    'djb2a':4,'djb2a_ltr':4,'djb2a_rtl':4,
    'joaat':4,
    'super_fast':4,'super_fast_le':4,'super_fast_be':4,
    'elf':4,'pjw':4,
    'aphash':4,
    'murmur2':4,'mmh2':4,'murmur2_32':4,'mmh2_32':4,'murmur2_le':4,'mmh2_le':4,'murmur2_32_le':4,'mmh2_32_le':4,'murmur2_be':4,'mmh2_be':4,'murmur2_32_be':4,'mmh2_32_be':4,
    'murmur2a':4,'mmh2a':4,'murmur2_32a':4,'mmh2_32a':4,'murmur2a_le':4,'mmh2a_le':4,'murmur2_32a_le':4,'mmh2_32a_le':4,'murmur2a_be':4,'mmh2a_be':4,'murmur2_32a_be':4,'mmh2_32a_be':4,
    'murmur2_64':8,'mmh2_64':8,'murmur2_64a':8,'mmh2_64a':8,'murmur2_64_le':8,'mmh2_64_le':8,'murmur2_64a_le':8,'mmh2_64a_le':8,'murmur2_64_be':8,'mmh2_64_be':8,'murmur2_64a_be':8,'mmh2_64a_be':8,
    'murmur2_64b':8,'mmh2_64b':8,'murmur2_64b_le':8,'mmh2_64b_le':8,'murmur2_64b_be':8,'mmh2_64b_be':8,
    'murmur3':4,'mmh3':4,'murmur3_32':4,'mmh3_32':4,
    'murmur3_128':16,'mmh3_128':16,
    'xxh32':4,'xxh64':8,'xxh3_64':8,'xxh128':16,'xxh3_128':16,
    'spooky2_32':4,'spooky2_64':8,'spooky2_128':16,
    'md5':16,'md5r':16,'sha1':20,'md5_sha1':36,
    'sha224':28,'sha256':32,'sha384':48,'sha512':64,
    'sha3_224':28,'sha3_256':32,'sha3_384':48,'sha3_512':64,
    'sha512_224':28,'sha512_256':32,
    'blake2b':64,'blake2s':32,
    'shake128':16,'shake256':32,'shake_128':16,'shake_256':32,
    'ripemd160':20,'sm3':32,
    'tarzan':4,'luas':4,'sxm':8,'slf':4,'hash40':5,'pivotal':4,'java':4,
    'empire_magic':2,
}
from .pyob import PyOBin,PyOFunc
class HashLib(PyOBin):
    def __init__(self,p:str):
        self.obj:dict[int,str] = {}
        super().__init__(p,unpickle=True)
    @classmethod
    def new(cls,p:str,ht:str,enc='utf-8',fmt=None):
        c = cls(p)
        c.db = {'t':ht,'s':HASHTS[ht],'e':enc,'fmt':PyOFunc(fmt) if not isinstance(fmt,PyOFunc) else fmt,'hs':[],'ns':[]}
        c.ht = c.db['t']
        c.hs = c.db['s']
        c.enc = c.db['e']
        c.fmt = c.db['fmt']
        return c
    @classmethod
    def dl(cls,p:str,db): return cls(db.get(p + '_hashes')).load()
    def wait(self):
        ld = bool(self._load_thrd)
        super().wait()
        if ld:
            self.ht:str = self.db['t']
            self.hs:int = self.db['s']
            self.enc:str = self.db['e']
            self.obj = dict(zip(self.db['hs'],self.db['ns']))
            self.fmt:PyOFunc = self.db['fmt']
        return self
    def save(self):
        self.db = {'t':self.ht,'s':self.hs,'e':self.enc,'fmt':self.fmt,'hs':list(self.obj.keys()),'ns':list(self.obj.values())}
        super().save()

    def crc(self,i:str|bytes):
        if type(i) == str: i = i.encode(self.enc)
        return crc_hash(self.fmt(i),self.ht)
    def add(self,i:list[str]|str):
        if type(i) == str: i = [i]
        for v in i:
            k = self.crc(v)
            if k not in self: self.obj[k] = v

    def get(self,k:int|str,default=None):
        if isinstance(k,int) and k in self.obj: return self.obj.get(k,default)
        elif isinstance(k,str): return self.crc(k)
        raise TypeError
    def __getitem__(self,k:int):
        if not isinstance(k,int): raise TypeError
        r = self.get(k)
        if r is None: raise KeyError(k)
        return r
    def __contains__(self,k:int):
        if not isinstance(k,int): raise TypeError
        return k in self.obj
    def __len__(self): return len(self.obj)
