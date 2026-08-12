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
def swap32i(i:int): return int.from_bytes(i.to_bytes(4,'big'),'little')
def reflecti(v:int,w:int):
    r = 0
    for _ in range(w):
        r = (r << 1) | (v & 1)
        v >>= 1
    return r
def rotxl(v:int,w:int,r:int=1): return ((v << r) & ((1 << w) - 1)) | (v >> (w - r))
def rotxr(v:int,w:int,r:int=1): return (v >> r) | ((v & ((1 << r) - 1)) << (w - r))
def rot8l(v:int,r:int=1): return rotxl(v,8,r)
def rot8r(v:int,r:int=1): return rotxr(v,8,r)
def rot16l(v:int,r:int=1): return rotxl(v,16,r)
def rot16r(v:int,r:int=1): return rotxr(v,16,r)
def odd_parity(v:int):
    v &= 0xFE
    return v | ((v.bit_count() % 2) ^ 1)

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
            'base85':'b85','ascii85':'a85','zbase85':'z85',
            'base92':'b92',
            'gamespy64':'g64',
            'zbase32':'z32',
            'cbase32':'c32','crockford32':'c32',
            'nin32':'n32','nintendo32':'n32',}
PYCRHSHM = {
    'KECCAK':'keccak',
}
PYCRCIPM = {
    'aes':'AES',
    'rc2':'ARC2','arc2':'ARC2',
    'rc4':'ARC4','arc4':'ARC4',
    'cast':'CAST','cast5':'CAST',
    'des':'DES','des3':'DES3',
    'blowfish':'Blowfish',
    'chacha20':'ChaCha20','tls_chacha20':'ChaCha20','xchacha20':'ChaCha20',
}
CRYOCIPM = {
    'camellia':'Camellia','blowfish':'Blowfish','aes':'AES',
    'des3':'TripleDES','cast':'CAST5','cast5':'CAST5',
    'seed':'SEED','idea':'IDEA','sm4':'SM4',
}
def decrypt(i:bytes,algo:str,key:bytes=None,iv:bytes=None,**kwargs) -> bytes:
    match algo:
        case 'xor':
            if isinstance(key,int): key = key.to_bytes(1)
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_xor(i,key or b'\0')
        case 'rxor':
            if isinstance(key,int): key = key.to_bytes(1)
            return uxx().decrypt_rxor(i,key or b'\0')
        case 'cxor':
            if isinstance(key,int): key = key.to_bytes(1)
            if isinstance(iv,bytes): iv = iv[0]
            asrt(isinstance(key,bytes),err=TypeError)
            return uxx().decrypt_cxor(i,key or b'\0',iv or 0)
        case 'cxori'|'cxor_inv':
            if isinstance(key,int): key = key.to_bytes(1)
            if isinstance(iv,bytes): iv = iv[0]
            return uxx().decrypt_cxori(i,key or b'\0',iv or 0)
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

        case 'aes'|'aes_cbc'|'aes_ecb'|'aes_ctr'|'aes_ctr_be'|'aes_ctr_le'|'aes_gcm'|'aes_ccm'|'aes_eax'|\
             'aes_ocb3'|'aes_ocb'|'aes_siv'|'aes_cfb'|'aes_ofb'|'aes_openpgp'|'aes_kw'|'aes_kwp'|'rc2'|\
             'rc2_ecb'|'rc2_cbc'|'rc2_cfb'|'rc2_ofb'|'rc2_ctr'|'rc2_openpgp'|'rc2_eax'|'arc2'|'arc2_ecb'|\
             'arc2_cbc'|'arc2_cfb'|'arc2_ofb'|'arc2_ctr'|'arc2_openpgp'|'arc2_eax'|'cast'|'cast_ecb'|'cast_cbc'|\
             'cast_cfb'|'cast_ofb'|'cast_ctr'|'cast_openpgp'|'cast_eax'|'cast5'|'cast5_ecb'|'cast5_cbc'|'cast5_cfb'|\
             'cast5_ofb'|'cast5_ctr'|'cast5_openpgp'|'cast5_eax'|'des'|'des_ecb'|'des_cbc'|'des_cfb'|\
             'des_ofb'|'des_ctr'|'des_openpgp'|'des_eax'|'des3'|'des3_ecb'|'des3_cbc'|'des3_cfb'|'des3_ofb'|\
             'des3_ctr'|'des3_openpgp'|'des3_eax'|'blowfish'|'blowfish_ecb'|'blowfish_cbc'|'blowfish_cfb'|\
             'blowfish_ofb'|'blowfish_ctr'|'blowfish_openpgp'|'blowfish_eax':
            if not '_' in algo:
                if algo == 'aes': algo += '_cbc'
                else: algo += '_ecb'
            n,m = algo.split('_',1)
            if m.endswith(('_be','_le')): m = m[:-3]
            if m == 'ocb3': m = 'ocb'

            kw = kwargs
            if m in {'ccm','eax','gcm','siv','ocb'}: kw['nonce'] = iv
            elif m in {'cbc','cfb','ofb','openpgp'}: kw['iv'] = iv
            elif m == 'ctr':
                from Cryptodome.Util import Counter
                pref,suf = kwargs.pop('prefix',b''),kwargs.pop('suffix',b'')
                if isinstance(iv,bytes): iv = int.from_bytes(iv,'little' if algo.endswith('_le') else 'big')
                elif iv is None: iv = 1
                asrt(isinstance(iv,int),err=TypeError)

                kw['counter'] = Counter.new(kwargs.pop('bits',len(key)*8),prefix=pref,suffix=suf,initial_value=iv,
                                            little_endian=algo.endswith('_le'),allow_wraparound=True)
            c = __import__('Cryptodome.Cipher.' + PYCRCIPM[n],fromlist=['*'])
            c = c.new(key,mode=getattr(c,f'MODE_{m.upper()}'),**kw)
            if m in {'kw','kwp'}:
                c.decrypt = c.unseal
                c.encrypt = c.seal
            if i is None: return c

            return c.decrypt(i)
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
        case 'aes_gcm_siv':
            from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV
            c = AESGCMSIV(key)
            if i is None: return c
            return c.decrypt(iv,i,kwargs.get('aad'))
        case 'blowfish_le'|'blowfish_le_ecb'|'blowfish_le_cbc'|'blowfish_le_cfb'|'blowfish_le_ofb'|'blowfish_le_ctr'|\
             'blowfish_le_openpgp'|'blowfish_le_eax': return swap32(decrypt(swap32(i),'blowfish' + algo[12:],key,iv,**kwargs))
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
            o = ARC4.new(key,drop=iv or 0)
            if i is None: return o
            return o.decrypt(i)
        case 'zipcrypto': return uxx().decrypt_zipcrypto(i,key)
        case 'rsa_raw'|'rsa_raw_le':
            from Cryptodome.PublicKey import RSA
            if type(key) == int and type(iv) == int: k = RSA.construct((key,iv))
            elif type(key) == int and iv is None: k = RSA.construct((key,0x10001))
            elif type(key) == bytes and type(iv) == int: k = RSA.construct((int.from_bytes(key,'little' if algo == 'rsa_raw_le' else 'big'),iv))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            asrt(k.size_in_bytes() == len(i))
            return pow(int.from_bytes(i,'little' if algo == 'rsa_raw_le' else 'big'),k.e,k.n).to_bytes(k.size_in_bytes(),'big')
        case 'rsa'|'rsa_le':
            from Cryptodome.PublicKey import RSA
            if type(key) == int and type(iv) == int: k = RSA.construct((key,iv))
            elif type(key) == int and iv is None: k = RSA.construct((key,0x10001))
            elif type(key) == bytes and type(iv) == int: k = RSA.construct((int.from_bytes(key,'little' if algo == 'rsa_le' else 'big'),iv))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            dbs = (k.n.bit_length() - 2) // 8
            ebs = dbs + 1

            ob = bytearray()
            p = 0
            while p < len(i):
                ob.extend(pow(int.from_bytes(i[p:p+ebs],'little' if algo == 'rsa_le' else 'big'),k.e,k.n).to_bytes(dbs,'little' if algo == 'rsa_le' else 'big'))
                p += ebs
            return bytes(ob)
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
            elif type(key) == bytes and type(iv) == int: k = RSA.construct((int.from_bytes(key,'big'),iv))
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
            elif type(key) == bytes and type(iv) == int: k = RSA.construct((int.from_bytes(key,'little' if algo == 'rsa_inv_le' else 'big'),iv))
            elif type(key) == bytes and iv is None: k = RSA.import_key(key)
            else: raise NotImplementedError()

            asrt(k.size_in_bytes() == len(i))
            c = pow(int.from_bytes(i,'little' if algo == 'rsa_inv_le' else 'big'),k.e,k.n)
            R = pow(pow(pow(2,k.size_in_bits()),-1,k.n),kwargs['r'],k.n)
            return ((c * R) % k.n).to_bytes(k.size_in_bytes(),'big')
        case 'rijndael'|'rijndael128'|'rijndael192'|'rijndael256':
            from pprp.crypto_3 import rijndael
            o = rijndael(key,block_size={'rijndael':kwargs.get('block_size'),
                                         'rijndael128':0x10,'rijndael192':0x18,'rijndael256':0x20}[algo])

            o._encrypt,o._decrypt = o.encrypt,o.decrypt
            o.encrypt = lambda i: bytes(o._encrypt(i))
            o.decrypt = lambda i: bytes(o._decrypt(i))

            if i is None: return o
            return o.decrypt(i)
        case 'tea'|'tea_be'|'tea_le': return uxx().decrypt_tea(i,key,le=algo == 'tea_le')
        case 'tea_pad'|'tea_pad_be'|'tea_pad_le':
            lo = len(i) % 8
            return uxx().decrypt_tea(i[:-lo or None],key,le=algo == 'tea_pad_le') + (i[-lo:] if lo else b'')
        case 'transformit'|'tfit':
            return uxx().decrypt_tfit(i,key,kwargs['table'],iv,kwargs['block_size'])
        case 'cobblestone'|'cobblestone128'|'cobblestone256':
            from cryptography.cobblestone import Cobblestone128Decryptor,Cobblestone256Decryptor
            if algo == 'cobblestone256': c = Cobblestone256Decryptor
            else: c = Cobblestone128Decryptor
            c = c(key,iv or b'')
            return c.update(i) + c.finalize()
        case 'fernet':
            from cryptography.fernet import Fernet
            if len(key) == 0x20: key = encrypt(key,'b64url')
            c = Fernet(key)
            r = c.decrypt(i)
            if kwargs.get('time'): return r,c.extract_timestamp(i)
            return r
        case 'camellia'|'camellia_cbc'|'camellia_ecb'|'camellia_ctr'|'camellia_ofb'|'camellia_cfb1'|'camellia_cfb'|\
             'camellia_gcm'|'aes_cfb1'|'sm4'|'sm4_cbc'|'sm4_ecb'|'sm4_ctr'|'sm4_ofb'|'sm4_cfb1'|'sm4_cfb'|'sm4_gcm'|\
             'des3_cfb1'|'cast_cfb1'|'cast5_cfb1'|'blowfish_cfb1'|'seed'|'seed_cbc'|'seed_ecb'|'seed_ctr'|'seed_ofb'|\
             'seed_cfb1'|'seed_cfb'|'seed_gcm'|'idea'|'idea_cbc'|'idea_ecb'|'idea_ctr'|'idea_ofb'|'idea_cfb1'|'idea_cfb'|\
             'idea_gcm':
                from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
                from cryptography.hazmat.decrepit.ciphers import algorithms as dalgorithms,modes as dmodes

                if not '_' in algo: algo += '_cbc'
                n,m = algo.split('_',1)
                if m == 'cfb': m = 'cfb8'
                elif m == 'cfb1': m = 'cfb'

                kw = kwargs
                if m in {'ecb',}: mds = modes
                elif m in {'cbc','gcm'}: kw['initialization_vector'],mds = iv,modes
                elif m in {'ctr',}: kw['nonce'],mds = iv,modes
                elif m in {'ofb','cfb','cfb8'}: kw['initialization_vector'],mds = iv,dmodes
                if n in {'aes','sm4'}: ags = algorithms
                elif n in {'camellia','des3','cast','cast5','seed','idea','blowfish'}: ags = dalgorithms

                c = Cipher(getattr(ags,CRYOCIPM[n])(key),getattr(mds,m.upper())(**kw)).decryptor()
                return c.update(i) + c.finalize()
        case 'ascon_aead128':
            import ascon
            return ascon.ascon_decrypt(key,iv,kwargs.get('aad',b''),i,'Ascon-AEAD128')
        case 'ascon_128'|'ascon_128a'|'ascon_80pq'|'ascon_128_be'|'ascon_128a_be'|'ascon_80pq_be'|'ascon_128_le'|'ascon_128a_le'|'ascon_80pq_le':
            if algo.endswith('_le'): import ascon_old_le as ascon
            else: import ascon_old as ascon
            return ascon.ascon_decrypt(key,iv,kwargs.get('aad',b''),i,'Ascon-' + algo[6:])
        case 'hpke_aes128_gcm'|'hpke_aes256_gcm'|'hpke_chacha20_poly1305':
            from Cryptodome.Protocol import HPKE
            c = HPKE.new(receiver_key=key,enc=iv,psk=kwargs.get('psk'),info=kwargs.get('info'),
                         aead_id={'aes128_gcm':HPKE.AEAD.AES128_GCM,'aes256_gcm':HPKE.AEAD.AES256_GCM,'chacha20_poly1305':HPKE.AEAD.CHACHA20_POLY1305}[algo[5:]])
            c.decrypt = c.unseal
            c.encrypt = c.seal
            if i is None: return c
            return c.decrypt(i)

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
            key = key.replace(b'\0',b'')
            k = bytearray(key)[:0x80] + b'\0'*0x80
            if len(key) < 0xFF: k[len(key) + 1] = (sum(key) * 2) & 0xFF
            return decrypt(i,'rc4',k.split(b'\0')[0],iv)
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
        case 'camelot_xor': return uxx().decrypt_camelot_xor(i,key)
        case 'camelot_rand': return uxx().decrypt_camelot_rand(i,key,iv,drop=kwargs.get('drop',0))
        case 'zipd': return uxx().decrypt_zipd(i)
        case 'legaia2':
            if isinstance(key,bytes):
                asrt(0 < len(key) <= 4)
                key = int.from_bytes(key,'little')
            return uxx().decrypt_legaia2(i,key)
        case 'ady_glue': return uxx().decrypt_ady_glue(i,key)
        case 'airrc4'|'criptrc4': return uxx().decrypt_airrc4(i,key)

        case 'ddhex4': return uxx().decrypt_swp4(bytes.fromhex(i))
        case 'hex': return bytes.fromhex(i)
        case 'base64url'|'b64url':
            import base64
            r = base64.urlsafe_b64decode(i)
            return r if kwargs.get('bytes',True) else r.decode('latin-1')
        case 'base16'|'base32'|'base32hex'|'base64'|'base85'|'ascii85'|'zbase85'|\
             'b16'|'b32'|'b32hex'|'b32h'|'b64'|'b85'|'a85'|'z85':
            algo = BASEXXNS.get(algo,algo)
            import base64
            if algo == 'b64' and len(i) % 4 and kwargs.get('fix'):
                if isinstance(i,str): i = i.encode('latin-1')
                i += b'=' * (-len(i) % 4)

            r = getattr(base64,algo + 'decode')(i)
            return r if kwargs.get('bytes',True) else r.decode('latin-1')
        case 'base92'|'base58'|'gamespy64'|'zbase32'|'cbase32'|'crockford32'|'nin32'|'nintendo32'|\
             'b92'|'b58'|'g64'|'z32'|'c32'|'n32':
            algo = BASEXXNS.get(algo,algo)
            if isinstance(BASEXX_DEC[algo],str): BASEXX_DEC[algo] = BaseXX(BASEXX_DEC[algo])
            if isinstance(i,bytes): i = i.decode('latin-1')
            r = BASEXX_DEC[algo].decode(i)
            return r if kwargs.get('bytes',True) else r.decode('latin-1')
        case 'basexx'|'bxx':
            asrt(isinstance(key,str),err=TypeError)
            if key not in BASEXX_DEC: BASEXX_DEC[key] = BaseXX(key)
            if isinstance(i,bytes): i = i.decode('latin-1')
            r = BASEXX_DEC[key].decode(i)
            return r if kwargs.get('bytes',True) else r.decode('latin-1')
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
        case 'rfc1751':
            from Cryptodome.Util import RFC1751
            r = RFC1751.key_to_english(i)
            return r.encode('latin-1') if kwargs.get('bytes',True) else r

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

        case 'aes'|'aes_cbc'|'aes_ecb'|'aes_ctr'|'aes_ctr_be'|'aes_ctr_le'|'aes_gcm'|'aes_ccm'|'aes_eax'|\
             'aes_ocb3'|'aes_ocb'|'aes_siv'|'aes_cfb'|'aes_ofb'|'aes_openpgp'|'aes_kw'|'aes_kwp'|'rc2'|\
             'rc2_ecb'|'rc2_cbc'|'rc2_cfb'|'rc2_ofb'|'rc2_ctr'|'rc2_openpgp'|'rc2_eax'|'arc2'|'arc2_ecb'|\
             'arc2_cbc'|'arc2_cfb'|'arc2_ofb'|'arc2_ctr'|'arc2_openpgp'|'arc2_eax'|'cast'|'cast_ecb'|'cast_cbc'|\
             'cast_cfb'|'cast_ofb'|'cast_ctr'|'cast_openpgp'|'cast_eax'|'cast5'|'cast5_ecb'|'cast5_cbc'|'cast5_cfb'|\
             'cast5_ofb'|'cast5_ctr'|'cast5_openpgp'|'cast5_eax'|'des'|'des_ecb'|'des_cbc'|'des_cfb'|\
             'des_ofb'|'des_ctr'|'des_openpgp'|'des_eax'|'des3'|'des3_ecb'|'des3_cbc'|'des3_cfb'|'des3_ofb'|\
             'des3_ctr'|'des3_openpgp'|'des3_eax'|'blowfish'|'blowfish_ecb'|'blowfish_cbc'|'blowfish_cfb'|\
             'blowfish_ofb'|'blowfish_ctr'|'blowfish_openpgp'|'blowfish_eax':
            o = decrypt(None,algo,key,iv,**kwargs)
            if i is None: return o
            return o.encrypt(i)
        case 'rijndael'|'rijndael128'|'rijndael192'|'rijndael256':
            o = decrypt(None,algo,key,iv,**kwargs)
            if i is None: return o
            return o.encrypt(i)

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
        case 'tmd_secret':
            asrt(isinstance(i,int) and isinstance(key,int))
            o = bytearray()
            add = key + i
            for _ in range(i):
                o.append(key.to_bytes(8,'big',signed=True)[7])
                key,add = key + add,key
            return bytes(o)

        case 'hex':
            r = i.hex()
            return r if kwargs.get('bytes',False) else r.encode('ascii')
        case 'base64url'|'b64url':
            import base64
            r = base64.urlsafe_b64encode(i)
            return r if kwargs.get('bytes',True) else r.decode('latin-1')
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
        case 'rfc1751':
            from Cryptodome.Util import RFC1751
            if isinstance(i,(tuple,list)): i = ' '.join(x.decode('latin-1') if isinstance(x,(bytes,bytearray)) else x for x in i)
            if isinstance(i,(bytes,bytearray)): i = i.decode('latin-1')
            return RFC1751.english_to_key(i)

    raise NotImplementedError(algo)
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
        else: r = b""
        return (b'\0' * zc) + r

CRC8  = {   # poly,init,xor ,reflect
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
    'latin1':(0x8005,0x0000,0x0000,True ),'ibm':(0x8005,0,0,True),'arc':(0x8005,0,0,True),'lha':(0x8005,0,0,True), # default
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
CRC40 = {   # poly        , init       , xor        , reflect
    'gsm':   (0x0004820009,0x0000000000,0x0000000000,False), # default
}
CRC64 = {   # poly              , init             , xor              , reflect
    'xz':    (0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True ),'go_ecma':(0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True),
    'ecma':  (0x42F0E1EBA9EA3693,0x0000000000000000,0x0000000000000000,False),'ecma_182':(0x42F0E1EBA9EA3693,0,0,False), # default
    'we':    (0x42F0E1EBA9EA3693,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,False),
    'redis': (0xAD93D23594C935A9,0x0000000000000000,0x0000000000000000,True ),
    'jones': (0xAD93D23594C935A9,0xFFFFFFFFFFFFFFFF,0x0000000000000000,True ),
    'ms':    (0x259C84CBA6426349,0xFFFFFFFFFFFFFFFF,0x0000000000000000,True ),
    'trembl':(0x000000000000001B,0x0000000000000000,0x0000000000000000,True ),
    'go_iso':(0x000000000000001B,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True ),
    'nvme':  (0xAD93D23594C93659,0xFFFFFFFFFFFFFFFF,0xFFFFFFFFFFFFFFFF,True ),
}
PRNG32 = {  # mult,      add,       init
'bkdr32_ltr':(131,       0,         0         ),'bkdr':(131,0,0),'bkdr32':(131,0,0),'bkdr_ltr':(131,0,0),
 'aststrsum':(0x63C63CD9,0x9C39C33D,0         ),'ast_strsum':(0x63C63CD9,0x9C39C33D,0),
    'java':  (31,        0,         0         ),
    'slf':   (33,        0,         0         ),
    'nlg':   (33,        0,         0xFFFFFFFF), # Next Level Games
   'solaris':(0x01000193,0,         0x811c9dc5),
}
PRNG64 = {
'bkdr64_ltr':(131,       0,         0),'bkdr64':(131,0,0),
    'sxm':   (137,       0,         0), # Sunday vs. Magazine
}
FLETCH = { #   width,init,base
    'adler8':   (8, 1,0xD),
    'adler16':  (16,1,0xFB),
    'adler32':  (32,1,0xFFF1),
'adler32_rsync':(32,1,0x10000),
    'adler64':  (64,1,0xFFFFFFFB),
 'fletcher16':  (16,0,0xFF),
}
def crc_hash(i:bytes,algo:str,**kwargs) -> int:
    match algo:
        case 'crc32'|'crc32_ieee'|'crc32_iso'|'crc32_iso_hdlc'|'crc32_adccp'|'crc32_pkzip':
            import zlib
            return zlib.crc32(i,kwargs.get('value') or 0)
        case 'crc8'|'crc8_tech_3250'|'crc8_gsm'|'crc8_gsm_a'|'crc8_mifare_mad'|'crc8_icode'|'crc8_hitag'|\
             'crc8_j1850'|'crc8_sae_j1850'|'crc8_rohc'|'crc8_smbus'|'crc8_atm'|'crc8_itu'|'crc8_i432_1'|\
             'crc8_wcdma'|'crc8_lte'|'crc8_cdma2000'|'crc8_maxim'|'crc8_maxim_dow'|'crc8_nrsc5'|\
             'crc8_opensafety'|'crc8_autosar'|'crc8_darc'|'crc8_gsm_b'|'crc8_ccitt'|'crc8_bluetooth'|\
             'crc8_dvb_s2':
            if algo == 'crc8': algo = 'crc8_smbus'
            kwargs['size'] = 8
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC8[algo[5:]]
            fnc = uxx().hash_crc
        case 'crc16'|'crc16_latin1'|'crc16_ansi'|'crc16_ibm'|'crc16_arc'|'crc16_lha'|'crc16_maxim'|'crc16_maxim_dow'|'crc16_modbus'|\
             'crc16_usb'|'crc16_umts'|'crc16_buypass'|'crc16_verifone'|'crc16_dds_110'|'crc16_cms'|'crc16_kermit'|\
             'crc16_ccitt'|'crc16_ccitt_true'|'crc16_tms37157'|'crc16_riello'|'crc16_iso_iec_14443_3_a'|\
             'crc16_mcrf4xx'|'crc16_x25'|'crc16_ibm_sdlc'|'crc16_iso_hdlc'|'crc16_xmodem'|'crc16_zmodem'|'crc16_acorn'|\
             'crc16_gsm'|'crc16_spi_fujitsu'|'crc16_aug_ccitt'|'crc16_ccitt_false'|'crc16_ibm_3740'|'crc16_genibus'|\
             'crc16_icode'|'crc16_darc'|'crc16_opensafety'|'crc16_opensafety_a'|'crc16_m17'|'crc16_dnp'|'crc16_en13757'|\
             'crc16_dect_r'|'crc16_dect_x'|'crc16_opensafety_b'|'crc16_teledisk'|'crc16_t10_dif'|'crc16_profibus'|\
             'crc16_nrsc5'|'crc16_lj1200'|'crc16_cdma2000'|'crc16_epc':
            if algo == 'crc16': algo = 'crc16_latin1'
            kwargs['size'] = 16
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC16[algo[6:]]
            fnc = uxx().hash_crc
        case 'crc24'|'crc24_lte'|'crc24_lte_a'|'crc24_openpgp'|'crc24_flexray'|'crc24_flexray_a'|'crc24_flexray_b'|\
             'crc24_lte_b'|'crc24_os9'|'crc24_ble'|'crc24_interlaken':
            if algo == 'crc24': algo = 'crc24_openpgp'
            kwargs['size'] = 24
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC24[algo[6:]]
            fnc = uxx().hash_crc
        case 'crc32'|'crc32_jamcrc'|'crc32_ieee'|'crc32_iso'|'crc32_iso_hdlc'|'crc32_adccp'|'crc32_pkzip'|'crc32_xz'|'crc32_v42'|\
             'crc32_mpeg2'|'crc32_posix'|'crc32_cksum'|'crc32_bzip2'|'crc32_aal5'|'crc32_dect_b'|'crc32b'|'crc32_mef'|\
             'crc32k'|'crc32_koopman'|'crc32_xfer'|'crc32_autosar'|'crc32c'|'crc32_castagnoli'|'crc32_iscsi'|\
             'crc32_base91_c'|'crc32_intrelaken'|'crc32_nvme'|'crc32d'|'crc32_base94'|'crc32_base94_d'|'crc32q'|\
             'crc32_aixm'|'crc32_cd_rom_edc'|'crc32_ludia':
            if algo == 'crc32': algo = 'crc32_ieee'
            kwargs['size'] = 32
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC32[algo[5 + (1 if algo[5] == '_' else 0):]]
            fnc = uxx().hash_crc
        case 'crc64'|'crc64_xz'|'crc64_go_ecma'|'crc64_ecma'|'crc64_ecma_182'|'crc64_we'|'crc64_redis'|'crc64_jones'|'crc64_ms'|\
             'crc64_go_iso'|'crc64_nvme'|'crc64_trembl':
            if algo == 'crc64': algo = 'crc64_ecma'
            kwargs['size'] = 64
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC64[algo[6:]]
            fnc = uxx().hash_crc
        case 'crc40'|'crc40_gsm':
            if algo == 'crc40': algo = 'crc40_gsm'
            kwargs['size'] = 40
            kwargs['poly'],kwargs['init'],kwargs['xor'],kwargs['reflect'] = CRC40[algo[6:]]
            fnc = uxx().hash_crc
        case 'crc32_16': return crc_hash(i,'crc32',**kwargs) & 0xFFFF
        case 'crc32_php': return swap32i(crc_hash(i,'crc32_bzip2',**kwargs))
        case 'bkdr'|'bkdr_ltr'|'bkdr32'|'bkdr32_ltr'|'aststrsum'|'ast_strsum'|'java'|'slf'|'nlg'|'solaris':
            kwargs['mult'],kwargs['add'],init = PRNG32[algo]
            if not 'init' in kwargs: kwargs['init'] = init
            fnc = uxx().hash_prng32
        case 'bkdr64'|'bkdr64_ltr'|'sxm':
            kwargs['mult'],kwargs['add'],init = PRNG64[algo]
            if not 'init' in kwargs: kwargs['init'] = init
            fnc = uxx().hash_prng64
        case 'adler32':
            import zlib
            if 'init' in kwargs: kwargs['value'] = kwargs.pop('init')
            fnc = zlib.adler32
        case 'adler8'|'adler16'|'adler32'|'adler32_rsync'|'adler64'|'fletcher16':
            kwargs['width'],kwargs['init'],kwargs['base'] = FLETCH[algo]
            fnc = uxx().hash_fletcher

        case 'fnv0_32':
            if not 'init' in kwargs: kwargs['init'] = 0
            fnc = uxx().hash_fnv1_32
        case 'fnv0_64':
            if not 'init' in kwargs: kwargs['init'] = 0
            fnc = uxx().hash_fnv1_64
        case 'fnv1_32': fnc = uxx().hash_fnv1_32
        case 'fnv1a_32': fnc = uxx().hash_fnv1a_32
        case 'fnv1_64': fnc = uxx().hash_fnv1_64
        case 'fnv1a_64': fnc = uxx().hash_fnv1a_64
        case 'bkdr_rtl'|'bkdr32_rtl':
            i = i[::-1]
            kwargs['mult'],kwargs['add'] = 131,0
            fnc = uxx().hash_prng32
        case 'bkdr64_rtl':
            i = i[::-1]
            kwargs['mult'],kwargs['add'] = 131,0
            fnc = uxx().hash_prng64
        case 'sdbm'|'sdbm_ltr': fnc = uxx().hash_sdbm
        case 'sdbm_rtl':
            i = i[::-1]
            fnc = uxx().hash_sdbm
        case 'djb2'|'djb2_ltr': fnc = uxx().hash_djb2
        case 'djb2_rtl':
            i = i[::-1]
            fnc = uxx().hash_djb2
        case 'djb2a'|'djb2a_ltr': fnc = uxx().hash_djb2a
        case 'djb2a_rtl':
            i = i[::-1]
            fnc = uxx().hash_djb2a
        case 'joaat': fnc = uxx().hash_joaat
        case 'super_fast'|'super_fast_le': fnc = uxx().hash_super_fast_le
        case 'super_fast_be': fnc = uxx().hash_super_fast_be
        case 'elf'|'pjw': fnc = uxx().hash_elf
        case 'aphash': fnc = uxx().hash_ap
        case 'murmur2'|'mmh2'|'murmur2_32'|'mmh2_32'|'murmur2_le'|'mmh2_le'|'murmur2_32_le'|'mmh2_32_le':
            fnc = uxx().hash_murmur2_le
            if not 'init' in kwargs: kwargs['init'] = 0x9747b28c
        case 'murmur2_be'|'mmh2_be'|'murmur2_32_be'|'mmh2_32_be':
            fnc = uxx().hash_murmur2_be
            if not 'init' in kwargs: kwargs['init'] = 0x9747b28c
        case 'murmur2a'|'mmh2a'|'murmur2_32a'|'mmh2_32a'|'murmur2a_le'|'mmh2a_le'|'murmur2_32a_le'|'mmh2_32a_le':
            fnc = uxx().hash_murmur2A_le
            if not 'init' in kwargs: kwargs['init'] = 0x9747b28c
        case 'murmur2a_be'|'mmh2a_be'|'murmur2_32a_be'|'mmh2_32a_be':
            fnc = uxx().hash_murmur2A_be
            if not 'init' in kwargs: kwargs['init'] = 0x9747b28c
        case 'murmur2_64'|'mmh2_64'|'murmur2_64a'|'mmh2_64a'|'murmur2_64_le'|'mmh2_64_le'|'murmur2_64a_le'|'mmh2_64a_le':
            fnc = uxx().hash_murmur2_64A_le
            if not 'init' in kwargs: kwargs['init'] = 0xe17a1465
        case 'murmur2_64_be'|'mmh2_64_be'|'murmur2_64a_be'|'mmh2_64a_be':
            fnc = uxx().hash_murmur2_64A_be
            if not 'init' in kwargs: kwargs['init'] = 0xe17a1465
        case 'murmur2_64b'|'mmh2_64b'|'murmur2_64b_le'|'mmh2_64b_le':
            fnc = uxx().hash_murmur2_64B_le
            if not 'init' in kwargs: kwargs['init'] = 0xe17a1465
        case 'murmur2_64b_be'|'mmh2_64b_be':
            fnc = uxx().hash_murmur2_64B_be
            if not 'init' in kwargs: kwargs['init'] = 0xe17a1465
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
        case 'bsdsum'|'bsd': fnc = uxx().hash_bsdsum
        case 'sysvsum'|'sysv': fnc = uxx().hash_sysvsum
        case 'sum': return sum(i)
        case 'sum8'|'sum16'|'sum24'|'sum32'|'sum40'|'sum48'|'sum56'|'sum64':
            return sum(i) & ((1 << int(algo[3:])) - 1)
        case 'sum_rotl'|'sum8_rotl'|'sum16_rotl'|'sum24_rotl'|'sum32_rotl'|'sum40_rotl'|'sum48_rotl'|'sum56_rotl'|'sum64_rotl':
            r = sum(rot8l(b) for b in i)
            if algo[3] == '_': return r
            s = int(algo[3:].split('_',1)[0])
            return r & ((1 << s) - 1)
        case 'sum_rotr'|'sum8_rotr'|'sum16_rotr'|'sum24_rotr'|'sum32_rotr'|'sum40_rotr'|'sum48_rotr'|'sum56_rotr'|'sum64_rotr':
            r = sum(rot8r(b) for b in i)
            if algo[3] == '_': return r
            s = int(algo[3:].split('_',1)[0])
            return r & ((1 << s) - 1)
        case 'xor'|'xor8':
            r = kwargs.get('init',0)
            for b in i: r ^= b
            return r

        case 'sha1'|'sha224'|'sha256'|'sha384'|'sha512'|'sha3_224'|'sha3_256'|'sha3_384'|'sha3_512'|'sha512_224'|'sha512_256'|\
             'blake2b'|'blake2s'|'md5'|'shake128'|'shake_128'|'shake256'|'shake_256'|'ripemd160'|'sm3':
            if algo in {'shake128','shake256'}: algo = algo[:5] + '_' + algo[5:]
            oby = kwargs.pop('bytes',False)
            kw = {}
            if 'size' in kwargs: kw['length'] = kwargs.pop('size')
            elif algo in {'shake_128','shake_256'}: kw['length'] = int(algo[6:]) // 8

            import hashlib
            if i is None: return hashlib.new(algo,**kwargs)
            r = hashlib.new(algo,i,**kwargs).digest(**kw)
            if oby: return r
            return int.from_bytes(r,'big')
        case 'md5r':
            import hashlib
            r = hashlib.md5(i).digest()
            r = r[12:16] + r[8:12] + r[4:8] + r[0:4]
            if kwargs.get('bytes',False): return r
            return int.from_bytes(r,'big')
        case 'md5x':
            le = kwargs.get('le',False)
            import hashlib
            r = struct.unpack(('<' if le else '>') + '4I',hashlib.md5(i).digest())
            r = r[0] ^ r[1] ^ r[2] ^ r[3]
            if kwargs.get('bytes',False): return r.to_bytes(4,'little' if le else 'big')
            return r
        case 'md5_lh5':
            r = kwargs.get('init',0xCAFEDECA)
            le = kwargs.get('le',False)
            import hashlib
            for x in range(0,max(1,len(i)),0x2000): r ^= crc_hash(i[x:x+0x2000],'md5x',le=le)
            if kwargs.get('bytes',False): return r.to_bytes(4,'little' if le else 'big')
            return r
        case 'md5_sha1':
            import hashlib
            r = hashlib.md5(i).digest() + hashlib.sha1(i).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'md2'|'md4':
            algo = algo.upper()
            h = __import__('Cryptodome.Hash.' + PYCRHSHM.get(algo,algo),fromlist=['*'])
            if i is None: return h.new(**kwargs)
            r = h.new(i,**kwargs).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'ed2k'|'emule'|'edonkey':
            BS = 0x947000
            from Cryptodome.Hash import MD4

            c1 = MD4.new()
            if BS > len(i):
                c1.update(i)
                return c1.digest()

            c2 = MD4.new()
            p = 0
            while p < len(i):
                c1.update(i[p:p+BS])
                if p + BS <= len(i):
                    c2.update(c1.digest())
                    c1 = MD4.new()
                p += BS
            c2.update(c1.digest())
            r = c2.digest()
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'keccak'|'keccak224'|'keccak256'|'keccak384'|'keccak512':
            from Cryptodome.Hash import keccak
            oby = kwargs.pop('bytes',False)
            h = keccak.new(digest_bits=kwargs.pop('size')*8 if algo == 'keccak' else int(algo[6:]),**kwargs)
            if i is None: return h
            h.update(i)
            r = h.digest()
            if oby: return r
            return int.from_bytes(r,'big')
        case 'tuplehash'|'tuplehash128'|'tuplehash256':
            from Cryptodome.Hash import TupleHash128,TupleHash256
            oby = kwargs.pop('bytes',False)
            h = {'tuplehash':TupleHash128,'tuplehash128':TupleHash128,
                 'tuplehash256':TupleHash256}[algo].new(digest_bytes=kwargs.pop('size',0x40))
            if i is None: return h
            if isinstance(i,(bytes,bytearray)): h.update(i)
            else: h.update(*i)
            r = h.digest()
            if oby: return r
            return int.from_bytes(r,'big')
        case 'cshake128'|'cshake_128'|'cshake256'|'cshake_256'|'kangaroo_twelve'|'k12'|'kangaroo12'|'turboshake128'|'turboshake_128'|\
             'turboshake256'|'turboshake_256':
            NMP = {'cshake128':'cSHAKE128','cshake256':'cSHAKE256',
                   'kangarootwelve':'KangarooTwelve','k12':'KangarooTwelve','kangaroo12':'KangarooTwelve',
                   'turboshake128':'TurboSHAKE128','turboshake256':'TurboSHAKE256'}

            oby = kwargs.pop('bytes',False)
            sz = kwargs.pop('size')
            h = __import__('Cryptodome.Hash.' + NMP[algo.replace('_','')]).new(custom=kwargs.get('custom'),fromlist=['*'])
            if i is None: return h
            h.update(i)
            r = h.read(sz)
            if oby: return r
            return int.from_bytes(r,'big')
        case 'ascon_hash256'|'ascon256':
            import ascon
            r = ascon.ascon_hash(i,'Ascon-Hash256',0x20)
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'ascon_xof128':
            import ascon
            r = ascon.ascon_hash(i,'Ascon-XOF128',kwargs['size'])
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'ascon_cxof128':
            import ascon
            r = ascon.ascon_hash(i,'Ascon-CXOF128',kwargs['size'],kwargs['key'])
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'ascon_hash'|'ascon_hasha'|'ascon_hash_be'|'ascon_hasha_be'|'ascon_hash_le'|'ascon_hasha_le':
            if algo.endswith('_le'): import ascon_old_le as ascon
            else: import ascon_old as ascon
            r = ascon.ascon_hash(i,'Ascon-Hash' + algo[10:11].strip('_'),0x20)
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'ascon_xof'|'ascon_xofa'|'ascon_xof_be'|'ascon_xofa_be'|'ascon_xof_le'|'ascon_xofa_le':
            if algo.endswith('_le'): import ascon_old_le as ascon
            else: import ascon_old as ascon
            r = ascon.ascon_hash(i,'Ascon-Xof' + algo[9:10].strip('_'),kwargs['size'])
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'blake3':
            import blake3
            oby = kwargs.pop('bytes',False)
            kw = {}
            if 'key' in kwargs: kw['key'] = kwargs['key']
            if 'iv' in kwargs: kw['derive_key_context'] = kwargs['iv']
            h = blake3.blake3(**kw)
            if i is None: return h
            h.update(i)
            kw = {'length':kwargs.get('size',0x20)}
            if 'offset' in kwargs: kw['seek'] = kwargs['offset']
            r = h.digest(**kw)
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'blake'|'blake224'|'blake256'|'blake384'|'blake512':
            if algo == 'blake': s = kwargs['size']*8
            else: s = int(algo[5:])

            import blake
            h = blake.BLAKE(s)
            if 'key' in kwargs: h.addsalt(kwargs['key'])
            if i is None: return h
            h.update(i)
            r = h.digest()
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'dha256'|'fork256'|'has160':
            r = getattr(uxx(),'hash_' + algo)(i)
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'echo224'|'echo256'|'echo384'|'echo512':
            r = uxx().hash_echo(i,int(algo[4:7]))
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'esch256'|'esch384':
            r = uxx().hash_esch(i,*{ # digest len, state len, block len, big rounds, slim rounds
                'esch256':(256,384,128,11,7),
                'esch384':(384,512,128,12,8),
            }[algo])
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'fugue224'|'fugue256'|'fugue384'|'fugue512':
            r = uxx().hash_fugue(i,int(algo[5:8]))
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'haval'|'haval128'|'haval160'|'haval192'|'haval224'|'haval256':
            raise NotImplementedError
            if '_' in algo:
                algo,r = algo.split('_',1)
                r = int(r)
            else: r = 3
            r = uxx().hash_haval(i,int(algo[5:] or 128),r)
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')
        case 'mdc2':
            h = bytearray(b'\x52'*8 + b'\x25'*8)

            def g(a:bytearray,m:int):
                r = a.copy()
                r[0] = (r[0] & 0x9F) | m
                for i in range(8): r[i] = odd_parity(r[i])
                return r
            def block(d:bytes):
                k1 = g(h[:8],0x40)
                k2 = g(h[8:],0x20)
                c1 = encrypt(encrypt(d,'des',k1),'xor',d)
                c2 = encrypt(encrypt(d,'des',k2),'xor',d)
                h[0:4] = c1[0:4]
                h[4:8] = c2[4:8]
                h[8:12] = c2[0:4]
                h[12:16] = c1[4:8]

            for p in range(0,len(i),8):
                d = i[p:p+8]
                block(d + bytes(-len(d) % 8))
            r = bytes(h)
            return r if kwargs.get('bytes',False) else int.from_bytes(r,'big')

        case 'cmac_transformit'|'cmac_tfit':
            asrt(isinstance(kwargs['key'],bytes) and isinstance(kwargs['table'],bytes))
            r = uxx().mac_cmac_tfit(i,kwargs['key'],kwargs['table'])
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'cmac'|'cmac_aes'|'cmac_rc2'|'cmac_arc2'|'cmac_blowfish'|'cmac_des'|'cmac_des3'|'cmac_cast'|'cmac_cast5':
            from Cryptodome.Hash import CMAC
            if not '_' in algo: n = 'aes'
            else: n = algo[5:]
            oby = kwargs.pop('bytes',False)
            sz = kwargs.pop('size',None)
            c = CMAC.new(kwargs.pop('key'),ciphermod=__import__('Cryptodome.Cipher.' + PYCRCIPM[n],fromlist=['*']),cipher_params=kwargs,mac_len=sz,update_after_digest=True)
            if i is None: return c
            c.update(i)
            r = c.digest()
            if oby: return r
            return int.from_bytes(r,'big')
        case 'cmac_camellia'|'cmac_sm4'|'cmac_idea'|'cmac_seed':
            from cryptography.hazmat.primitives import cmac
            from cryptography.hazmat.primitives.ciphers import algorithms
            from cryptography.hazmat.decrepit.ciphers import algorithms as dalgorithms

            n = CRYOCIPM[algo[5:]]
            if n == 'SM4': c = getattr(algorithms,n)
            else: c = getattr(dalgorithms,n)
            c = cmac.CMAC(c(kwargs['key']))
            if i is None: return c
            c.update(i)
            r = c.finalize()
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

            r = bytes(o)[:s]
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'hmac_sha1'|'hmac_md5'|'hmac_sha256'|'hmac_sha384'|'hmac_sha512'|'hmac_sha224'|'hmac_sha3_224'|'hmac_sha3_256'|\
             'hmac_sha3_384'|'hmac_sha3_512'|'hmac_blake2b'|'hmac_blake2s'|'hmac_ripemd160'|'hmac_sm3':
            import hashlib,hmac
            c = hmac.new(kwargs['key'],i,getattr(hashlib,algo[5:]))
            if i is None: return c
            r = c.digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'hmac_md2'|'hmac_md4':
            from Cryptodome.Hash import HMAC
            algo = algo[5:].upper()
            h = HMAC.new(kwargs['key'],digestmod=__import__('Cryptodome.Hash.' + PYCRHSHM.get(algo,algo),fromlist=['*']))
            if i is None: return h.new(**kwargs)
            r = h.new(i,**kwargs).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'hmac_blake3':
            import blake3,hmac
            c = hmac.new(kwargs['key'],i,blake3.blake3)
            if i is None: return c
            r = c.digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'poly1305_aes'|'poly1305_chacha20'|'poly1305_xchacha20'|'poly1305_tls_chacha20':
            from Cryptodome.Hash import Poly1305
            if 'iv' in kwargs and not kwargs.get('nonce'): kwargs['nonce'] = kwargs['iv']
            h = Poly1305.new(kwargs['key'],cipher=__import__('Cryptodome.Cipher.' + PYCRCIPM[algo[5:]],fromlist=['*']),nonce=kwargs['nonce'])
            if i is None: return h
            r = h.update(i).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'kmac128'|'kmac256':
            h = __import__('Cryptodome.Hash.' + algo.upper(),fromlist=['*']).new(kwargs['key'],mac_len=kwargs.get('size',0x40),custom=kwargs.get('custom'))
            if i is None: return h
            r = h.update(i).digest()
            if kwargs.get('bytes'): return r
            return int.from_bytes(r,'big')
        case 'eac':
            b = kwargs.get('iv',kwargs.get('iv',b'\0'*0x20))
            asrt(len(b) == len(kwargs['key']) == 0x20)
            o = encrypt(None,'rijndael256',kwargs['key'])

            for p in range(0,len(i),0x20):
                b = o.encrypt(encrypt(i[p:p+0x20].ljust(0x20,b'\0'),'xor',b))

            if kwargs.get('bytes'): return b
            return int.from_bytes(b,'big')
        case 'ascon_mac'|'ascon_prf'|'ascon_prf_short':
            import ascon
            r = ascon.ascon_mac(kwargs['key'],i,{'mac':'Ascon-Mac','prf':'Ascon-Prf','prf_short':'Ascon-PrfShort'}[algo[6:]],kwargs.get('size',0x10))
            return r if kwargs.get('bytes') else int.from_bytes(r,'big')
        case 'ascon_mac_old'|'ascon_maca'|'ascon_prf_old'|'ascon_prfa'|'ascon_prf_short_old'|'ascon_maca_le'|'ascon_prfa_le':
            if algo.endswith('_old'): algo = algo[:-4]
            if algo.endswith('_le'):
                algo = algo[:-3]
                import ascon_old_le as ascon
            else: import ascon_old as ascon
            r = ascon.ascon_mac(kwargs['key'],i,'Ascon-' + {'mac':'Mac','maca':'Maca','prf':'Prf','prfa':'Prfa','prf_short':'PrfShort'}[algo[6:]],kwargs.get('size',0x10))
            return r if kwargs.get('bytes') else int.from_bytes(r,'big')

        case 'pbkdf2'|'pbkdf2_sha1'|'pbkdf2_sha224'|'pbkdf2_sha256'|'pbkdf2_sha384'|'pbkdf2_sha512'|'pbkdf2_sha3_224'|\
             'pbkdf2_sha3_256'|'pbkdf2_sha3_384'|'pbkdf2_sha3_512'|'pbkdf2_md2'|'pbkdf2_md4'|'pbkdf2_md5'|'pbkdf2_ripemd160'|\
             'pbkdf1'|'pbkdf1_sha1'|'pbkdf1_sha224'|'pbkdf1_sha256'|'pbkdf1_sha384'|'pbkdf1_sha512'|'pbkdf1_sha3_224'|\
             'pbkdf1_sha3_256'|'pbkdf1_sha3_384'|'pbkdf1_sha3_512'|'pbkdf1_md2'|'pbkdf1_md4'|'pbkdf1_md5'|'pbkdf1_ripemd160':
            df1 = algo.startswith('pbkdf1')
            if not '_' in algo: algo = 'sha1'
            else: algo = algo[7:]
            algo = algo.upper()

            from Cryptodome.Protocol.KDF import PBKDF2,PBKDF1
            h = __import__('Cryptodome.Hash.' + PYCRHSHM.get(algo,algo),fromlist=['*'])
            args = (i,kwargs['key'],kwargs['size'] if 'size' in kwargs else h.digest_size,kwargs['c'])
            if df1: r = PBKDF1(*args,hashAlgo=h)
            else: r = PBKDF2(*args,hmac_hash_module=h)
            if kwargs.get('bytes',True): return r
            return int.from_bytes(r,'big')
        case 'scrypt':
            from Cryptodome.Protocol.KDF import scrypt
            r = scrypt(i,kwargs['key'],kwargs['size'],kwargs['c'],kwargs.get('r',8),kwargs.get('p',1),kwargs.get('num',1))
            if kwargs.get('bytes',True): return r
            return int.from_bytes(r,'big')
        case 'bcrypt':
            from Cryptodome.Protocol.KDF import bcrypt
            r = bcrypt(i,kwargs['c'],salt=kwargs.get('key'))
            if kwargs.get('bytes',True): return r
            return int.from_bytes(r,'big')
        case 'bcrypt_b64_sha1'|'bcrypt_b64_sha224'|'bcrypt_b64_sha256'|'bcrypt_b64_sha384'|'bcrypt_b64_sha512'|\
             'bcrypt_b64_sha3_224'|'bcrypt_b64_sha3_256'|'bcrypt_b64_sha3_384'|'bcrypt_b64_sha3_512'|'bcrypt_b64_md2'|\
             'bcrypt_b64_md4'|'bcrypt_b64_md5'|'bcrypt_b64_ripemd160'|'bcrypt_b64_blake2b'|'bcrypt_b64_blake2s'|'bcrypt_b64_blake3'|\
             'bcrypt_b64_ascon256'|'bcrypt_b64_ascon_hash256':
            from Cryptodome.Protocol.KDF import bcrypt
            return crc_hash(encrypt(crc_hash(i,algo[11:],bytes=True),'base64'),'bcrypt',**kwargs)
        case 'hkdf'|'hkdf_sha1'|'hkdf_sha224'|'hkdf_sha256'|'hkdf_sha384'|'hkdf_sha512'|'hkdf_sha3_224'|'hkdf_sha3_256'|\
             'hkdf_sha3_384'|'hkdf_sha3_512'|'hkdf_md2'|'hkdf_md4'|'hkdf_md5'|'hkdf_ripemd160':
            if algo == 'hkdf': algo = 'sha512'
            else: algo = algo[5:]
            algo = algo.upper()

            from Cryptodome.Protocol.KDF import HKDF
            h = __import__('Cryptodome.Hash.' + PYCRHSHM.get(algo,algo),fromlist=['*'])
            r = HKDF(i,kwargs['size'] if 'size' in kwargs else h.digest_size,kwargs['key'],h,kwargs.get('num',1),context=kwargs.get('iv'))
            if kwargs.get('bytes',True): return r
            return int.from_bytes(r,'big')
        case 'sp800_108_counter_cmac_transformit'|'sp800_108_counter_cmac_tfit':
            from Cryptodome.Protocol.KDF import SP800_108_Counter
            tab = kwargs['table']
            def prf(s,x): return crc_hash(x,'cmac_tfit',key=s,table=tab,bytes=True)
            r = SP800_108_Counter(i,kwargs['size'],prf,kwargs.get('num',1),kwargs.get('iv',b''),kwargs.get('nonce',b''))
            if kwargs.get('bytes',True): return r
            return int.from_bytes(r,'big')
        case 'sp800_108_counter_cmac_aes'|'sp800_108_counter_cmac_rc2'|'sp800_108_counter_cmac_arc2'|'sp800_108_counter_cmac_cast'|'sp800_108_counter_cmac_cast5'|\
             'sp800_108_counter_cmac_blowfish'|'sp800_108_counter_cmac_des'|'sp800_108_counter_cmac_des3'|'sp800_108_counter_cmac_idea'|\
             'sp800_108_counter_cmac_seed'|'sp800_108_counter_cmac_sm4'|'sp800_108_counter_cmac_camellia'|'sp800_108_counter_hmac_sha1'|\
             'sp800_108_counter_hmac_sha224'|'sp800_108_counter_hmac_sha256'|'sp800_108_counter_hmac_sha384'|'sp800_108_counter_hmac_sha512'|\
             'sp800_108_counter_hmac_sha3_224'|'sp800_108_counter_hmac_sha3_256'|'sp800_108_counter_hmac_sha3_384'|'sp800_108_counter_hmac_sha3_512'|\
             'sp800_108_counter_hmac_md2'|'sp800_108_counter_hmac_md4'|'sp800_108_counter_hmac_md5'|'sp800_108_counter_hmac_ripemd160':
            from Cryptodome.Protocol.KDF import SP800_108_Counter
            def prf(s,x): return crc_hash(x,algo,key=s,bytes=True)
            r = SP800_108_Counter(i,kwargs['size'],prf,kwargs.get('num',1),kwargs.get('iv',b''),kwargs.get('nonce',b''))
            if kwargs.get('bytes',True): return r
            return int.from_bytes(r,'big')
        case 'argon2d'|'argon2i'|'argon2id':
            import cryptography.hazmat.primitives.kdf.argon2 as argon2
            c = getattr(argon2,algo.capitalize())(salt=kwargs['salt'],length=kwargs['size'],iterations=kwargs.get('c',1),lanes=kwargs.get('p',4),memory_cost=kwargs['m'],
                                                  ad=kwargs.get('iv'),secret=kwargs.get('key'))
            if i is None: return c
            r = c.derive(i)
            if kwargs.get('bytes',True): return r
            return int.from_bytes(r,'big')
        case 'concatkdf'|'concatkdf_sha1'|'concatkdf_sha224'|'concatkdf_sha256'|'concatkdf_sha384'|'concatkdf_sha512'|'concatkdf_sha3_224'|'concatkdf_sha3_256'|\
             'concatkdf_sha3_384'|'concatkdf_sha3_512'|'concatkdf_md5'|'concatkdf_sm3'|'concatkdf_blake2b'|'concatkdf_blake2s'|'concatkdf_shake128'|'concatkdf_shake256'|\
             'concatkdf_hmac'|'concatkdf_hmac_sha1'|'concatkdf_hmac_sha224'|'concatkdf_hmac_sha256'|'concatkdf_hmac_sha384'|'concatkdf_hmac_sha512'|'concatkdf_hmac_sha3_224'|\
             'concatkdf_hmac_sha3_256'|'concatkdf_hmac_sha3_384'|'concatkdf_hmac_sha3_512'|'concatkdf_hmac_md5'|'concatkdf_hmac_sm3'|'concatkdf_hmac_blake2b'|'concatkdf_hmac_blake2s'|\
             'concatkdf_hmac_shake128'|'concatkdf_hmac_shake256'|\
             'hkdfexpand'|'hkdfexpand_sha1'|'hkdfexpand_sha224'|'hkdfexpand_sha256'|'hkdfexpand_sha384'|'hkdfexpand_sha512'|'hkdfexpand_sha3_224'|'hkdfexpand_sha3_256'|\
             'hkdfexpand_sha3_384'|'hkdfexpand_sha3_512'|'hkdfexpand_md5'|'hkdfexpand_sm3'|'hkdfexpand_blake2b'|'hkdfexpand_blake2s'|'hkdfexpand_shake128'|'hkdfexpand_shake256'|\
             'x963kdf'|'x963kdf_sha1'|'x963kdf_sha224'|'x963kdf_sha256'|'x963kdf_sha384'|'x963kdf_sha512'|'x963kdf_sha3_224'|'x963kdf_sha3_256'|'x963kdf_sha3_384'|\
             'x963kdf_sha3_512'|'x963kdf_md5'|'x963kdf_sm3'|'x963kdf_blake2b'|'x963kdf_blake2s'|'x963kdf_shake128'|'x963kdf_shake256':
                from cryptography.hazmat.primitives import hashes
                for pn in ('concatkdf_hmac','concatkdf','hkdfexpand','x963kdf'):
                    if algo.startswith(pn): n = pn;break
                if n == 'concatkdf':
                    from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
                    c = ConcatKDFHash
                elif n == 'concatkdf_hmac':
                    from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHMAC
                    c = ConcatKDFHMAC
                elif n == 'hkdfexpand':
                    from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand
                    c = HKDFExpand
                elif n == 'x963kdf':
                    from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
                    c = X963KDF

                if algo == n: m = 'sha256'
                else: m = algo[len(n) + 1:]
                if m == 'blake2b': args = (0x40,)
                elif m == 'blake2s': args = (0x20,)
                elif m in {'shake128','shake256'}: args = (kwargs['hash_size'],)
                else: args = ()

                kw = {}
                if n in {'concatkdf','x963kdf'}: kw['otherinfo'] = kwargs.get('iv')
                elif n =='concatkdf_hmac': kw['salt'],kw['otherinfo'] = kwargs['key'],kwargs.get('iv')
                elif n == 'hkdfexpand': kw['info'] = kwargs.get('iv')
                c = c(getattr(hashes,m.upper())(*args),length=kwargs['size'],**kw)
                if i is None: return c
                r = c.derive(i)
                if kwargs.get('bytes',True): return r
                return int.from_bytes(r,'big')

        case 'tarzan': fnc = uxx().hash_tarzan
        case 'luas': fnc = uxx().hash_luas
        case 'hash40':
            import zlib
            return ((len(i) & 0xFF) << 32) | zlib.crc32(i,kwargs.get('value') or 0)
        case 'pivotal': fnc = uxx().hash_pivotal
        case 'empire_magic': fnc = uxx().hash_empire_magic
        case 'westwood': fnc = uxx().hash_westwood
        case _: raise NotImplementedError(algo)
    return fnc(i,**kwargs)

HASHTS = {
    f'crc8_{x}':1 for x in CRC8}|{
    f'crc16_{x}':2 for x in CRC16}|{
    f'crc24_{x}':3 for x in CRC24}|{
    f'crc32{"_" if len(x)>1 else ""}{x}':4 for x in CRC32}|{
    f'crc40_{x}':5 for x in CRC40}|{
    f'crc64_{x}':8 for x in CRC64}|{
    x:4 for x in PRNG32}|{
    x:8 for x in PRNG64}|{
    x:FLETCH[x][0]//8 for x in FLETCH}|\
{
    'crc8':1,'crc16':2,'crc24':3,'crc32':4,'crc40':5,'crc64':8,'crc32_16':2,'crc32_php':4,
    'adler8':1,'adler16':2,'adler32':4,'adler64':8,
    'fnv1_32':4,'fnv1a_32':4,'fnv0_32':4,
    'fnv1_64':8,'fnv1a_64':8,'fnv0_64':8,
    'bkdr_rtl':4,'bkdr32_rtl':4,'bkdr64_rtl':8,
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
    'bsdsum':2,'bsd':2,'sysv':2,'sysvsum':2,
    'sum8':1,'sum16':2,'sum24':3,'sum32':4,'sum40':5,'sum48':6,'sum56':7,'sum64':8,
    'sum8_rotl':1,'sum16_rotl':2,'sum24_rotl':3,'sum32_rotl':4,'sum40_rotl':5,'sum48_rotl':6,'sum56_rotl':7,'sum64_rotl':8,
    'sum8_rotr':1,'sum16_rotr':2,'sum24_rotr':3,'sum32_rotr':4,'sum40_rotr':5,'sum48_rotr':6,'sum56_rotr':7,'sum64_rotr':8,
    'xor':1,'xor8':1,
    'md5':16,'md5r':16,'sha1':20,'md5_sha1':36,'md2':16,'md4':16,
    'ed2k':16,'emule':16,'edonkey':16,
    'md5x':4,'md5_lh5':4,
    'sha224':28,'sha256':32,'sha384':48,'sha512':64,
    'sha3_224':28,'sha3_256':32,'sha3_384':48,'sha3_512':64,
    'sha512_224':28,'sha512_256':32,
    'blake224':28,'blake256':32,'blake384':48,'blake512':64,
    'blake2b':64,'blake2s':32,
    'blake3':32,
    'shake128':16,'shake256':32,'shake_128':16,'shake_256':32,
    'ripemd160':20,'sm3':32,
    'keccak224':28,'keccak256':32,'keccak384':48,'keccak512':64,
    'tuplehash':64,'tuplehash128':64,'tuplehash256':64,
    'ascon_hash':32,'ascon_hasha':32,'ascon_hash_be':32,'ascon_hasha_be':32,'ascon_hash_le':32,'ascon_hasha_le':32,
    'ascon_hash256':32,'ascon256':32,
    'dha256':32,'fork256':32,'has160':20,
    'esch256':32,'esch384':48,
    'echo224':28,'echo256':32,'echo384':48,'echo512':64,
    'fugue224':28,'fugue256':32,'fugue384':48,'fugue512':64,
    'haval':16,'haval128':16,'haval160':20,'haval192':24,'haval224':28,'haval256':32,
    'mdc2':16,
    'tarzan':4,'luas':4,'hash40':5,'pivotal':4,
    'empire_magic':2,'westwood':4,
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
