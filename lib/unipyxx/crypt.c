#include "util.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MT_N 624
#define MT_M 397
#define MT_MSK_U (int32_t)0x80000000
#define MT_MSK_L (int32_t)0x7FFFFFFF
typedef struct {
    int32_t MATRIX_A;
    uint32_t TEMPERING_MASK_B;
    uint32_t TEMPERING_MASK_C;
    uint32_t INIT_MULT;

    int32_t mt[624];
    int32_t mti;
} MT19937;
#define INIT_MT19937(X) MT19937 X = { .MATRIX_A = (int32_t)0x9908B0DF, .TEMPERING_MASK_B = 0x9D2C5680,\
                                      .TEMPERING_MASK_C = 0xEFC60000, .INIT_MULT = 0x6C078965,\
                                      .mt = { 0 }, .mti = MT_N + 1 }
void MT19937_seed(MT19937 *restrict ctx, int32_t seed) {
    ctx->mt[0] = seed;
    for (ctx->mti=1;ctx->mti < MT_N;ctx->mti++) {
        int32_t last = ctx->mt[ctx->mti - 1];
        ctx->mt[ctx->mti] = (int32_t)(ctx->INIT_MULT * (uint32_t)(last ^ (last >> 30)) + (uint32_t)ctx->mti);
    }
}
int32_t MT19937_rand(MT19937 *restrict ctx) {
    int32_t y;
    const int32_t mag01[2] = { 0x0U, ctx->MATRIX_A };

    if (ctx->mti >= MT_N) {
        int i = 0;

        for (;i < MT_N - MT_M;i++) {
            y = (ctx->mt[i] & MT_MSK_U) | (ctx->mt[i + 1] & MT_MSK_L);
            ctx->mt[i] = ctx->mt[i + MT_M] ^ (y >> 1) ^ mag01[y & 1];
        }
        for (;i < MT_N - 1;i++) {
            y = (ctx->mt[i] & MT_MSK_U) | (ctx->mt[i + 1] & MT_MSK_L);
            ctx->mt[i] = ctx->mt[i + (MT_M - MT_N)] ^ (y >> 1) ^ mag01[y & 1];
        }
        y = (ctx->mt[MT_N - 1] & MT_MSK_U) | (ctx->mt[0] & MT_MSK_L);
        ctx->mt[MT_N - 1] = ctx->mt[MT_M - 1] ^ (y >> 1) ^ mag01[y & 1];
        ctx->mti = 0;
    }

    y = ctx->mt[ctx->mti++];
    y ^= y >> 11;
    y ^= (int32_t)(((uint32_t)y << 7) & ctx->TEMPERING_MASK_B);
    y ^= (int32_t)(((uint32_t)y << 15) & ctx->TEMPERING_MASK_C);
    y ^= y >> 18;
    return y;
}

#define MICRO_C_RAND_A 0x358D
#define MICRO_C_RAND_C 0x3619
uint16_t micro_c_rand(uint16_t state) {
    return state * MICRO_C_RAND_A + MICRO_C_RAND_C;
}

EXPORT void decrypt_inv(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst) {
    for (size_t p=0;p < size;p++) dst[p] = ~src[p];
}
EXPORT void decrypt_swp4(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst) {
    for (size_t p=0;p < size;p++) dst[p] = SWAP8(src[p]);
}
EXPORT void decrypt_roll(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] - key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rolr(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] + key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_xor(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                        const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] ^ key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rxor(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t key) {
    if (size == 0) return;
    size_t p = 1;
    dst[0] = src[0] ^ key;
    for (;p < size;p++) dst[p] = src[p] ^ dst[p - 1];
}
EXPORT void decrypt_cxor(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] ^ (uint8_t)(key[kc++] + p);
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_dxor(const uint8_t *restrict src,  const size_t size, uint8_t *restrict dst,
                         const uint8_t *restrict key1, const size_t ksize1,
                         const uint8_t *restrict key2, const size_t ksize2) {
    size_t kc1 = 0;
    size_t kc2 = 0;
    for (size_t p=0;p < size;p++) {
        dst[p] = src[p] ^ key1[kc1++] ^ key2[kc2++];
        if (kc1 >= ksize1) kc1 = 0;
        if (kc2 >= ksize2) kc2 = 0;
    }
}
EXPORT void decrypt_tea(const uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                              uint8_t *restrict key, const int8_t le) {
    uint32_t *k = (uint32_t *)key;
    const uint32_t *inp = (uint32_t *)src;
    uint32_t *out = (uint32_t *)dst;
    size_t bc = size / 4;

    if (!le)
        for (int i=0;i < 4;i++) k[i] = SWAP32(k[i]);

    const uint32_t DLT = 0x9e3779b9;
    for (size_t p=0;p < bc;p+=2) {
        uint32_t v0 = inp[p];
        uint32_t v1 = inp[p + 1];
        if (!le) {
            v0 = SWAP32(v0);
            v1 = SWAP32(v1);
        }

        uint32_t sv = (DLT * 32) & 0xFFFFFFFF;
        for (int i = 0; i < 32; i++) {
            v1 -= ((v0 << 4) + k[2]) ^ (v0 + sv) ^ ((v0 >> 5) + k[3]);
            v0 -= ((v1 << 4) + k[0]) ^ (v1 + sv) ^ ((v1 >> 5) + k[1]);
            sv -= DLT;
        }

        if (!le) {
            v0 = SWAP32(v0);
            v1 = SWAP32(v1);
        }

        out[p] = v0;
        out[p + 1] = v1;
    }
}
EXPORT void decrypt_rsdk3(uint8_t *restrict buf, const size_t size,
                    const uint8_t *restrict key1, const uint8_t *restrict key2) {
    uint8_t kn = (size >> 2) & 0x7F;
    uint8_t k2p = (kn % 9) + 1;
    uint8_t k1p = (kn % k2p) + 1;
    int8_t swp = 0;

    for (size_t p=0;p < size;p++) {
        uint8_t b = buf[p];
        b ^= key2[k2p++] ^ kn;
        if (swp) b = SWAP8(b);
        b ^= key1[k1p++];
        buf[p] = b;

        if (k1p <= 19 || k2p <= 11) {
            if (k1p > 19) {
                k1p = 1;
                swp = !swp;
            }
            if (k2p > 11) {
                k2p = 1;
                swp = !swp;
            }
        } else {
            kn = (kn + 1) & 0x7F;
            if (swp) {
                k1p = (kn % 12) + 6;
                k2p = (kn % 5) + 4;
            } else {
                k1p = (kn % 15) + 3;
                k2p = (kn % 7) + 1;
            }
            swp = !swp;
        }
    }
}
EXPORT void decrypt_rsdk4(uint8_t *restrict buf, const size_t size,
                    const uint32_t key1, const uint32_t key2,
                    const uint8_t *restrict keyx1, const uint8_t *restrict keyx2) {
    int8_t swp = 0;
    uint8_t k1p = 0;
    uint8_t k2p = 8;
    uint8_t kn = (size >> 2) & 0x7F;

    for (size_t p=0;p < size;p++) {
        uint8_t b = buf[p];
        b ^= keyx2[k2p++] ^ kn;
        if (swp) b = SWAP8(b);
        b ^= keyx1[k1p++];
        buf[p] = b;

        if (k1p <= 15) {
            if (k2p > 12) {
                k2p = 0;
                swp = !swp;
            }
        } else if (k2p <= 8) {
            k1p = 0;
            swp = !swp;
        } else {
            kn = (kn + 2) & 0x7F;
            uint32_t t1 = HIMUL64(key2, kn);
            t1 += (kn - t1) >> 1;
            uint32_t t2 = (HIMUL64(key1, kn) >> 3) * 3;
            if (swp) {
                k1p = kn - (t1 >> 2) * 7;
                k2p = kn - (t2 << 2) + 2;
            } else {
                k1p = kn - (t2 << 2) + 3;
                k2p = kn - (t1 >> 2) * 7;
            }
            swp = !swp;
        }
    }
}
EXPORT void decrypt_rsdk5(uint8_t *restrict buf, const size_t size,
                    const uint8_t *restrict key1, const uint8_t *restrict key2) {
    int8_t swp = 0;
    uint8_t k1p = 0;
    uint8_t k2p = 8;
    uint8_t kn = (size >> 2) & 0x7F;

    for (size_t p=0;p < size;p++) {
        uint8_t b = buf[p];
        b ^= key2[k2p++] ^ kn;
        if (swp) b = SWAP8(b);
        b ^= key1[k1p++];
        buf[p] = b;

        if (k1p <= 15) {
            if (k2p > 12) {
                k2p = 0;
                swp = !swp;
            }
        } else if (k2p <= 8) {
            k1p = 0;
            swp = !swp;
        } else {
            kn = (kn + 2) & 0x7F;
            if (swp) {
                k1p = kn % 7;
                k2p = (kn % 12) + 2;
            } else {
                k1p = (kn % 12) + 3;
                k2p = kn % 7;
            }
            swp = !swp;
        }
    }
}
EXPORT void decrypt_hornby(uint8_t *restrict buf, const size_t size,
                     const uint8_t key, const uint8_t msk) {
    if (size < 2) return;

    buf[1] ^= key;
    for (size_t i=1;i < size;i++) buf[i] ^= buf[i - 1] ^ (buf[i] & msk);
}
EXPORT void init_mmfs(uint8_t *restrict dst, const uint8_t *restrict key) {
    size_t kp = 0;
    uint8_t i2 = 0;
    for (int i1=0;i1 < 0x100;i1++) {
        if (!key[kp]) kp = 0;
        i2 += key[kp++] + dst[i1];
        uint8_t b = dst[i2];
        dst[i2] = dst[i1];
        dst[i1] = b;
    }
}
EXPORT void decrypt_mmfs(uint8_t *restrict buf, const size_t size, uint8_t *restrict key) {
    uint8_t i1 = 0;
    uint8_t i2 = 0;
    for (size_t p=0;p < size;p++) {
        i2 += key[++i1];
        uint8_t b = key[i2];
        key[i2] = key[i1];
        key[i1] = b;
        buf[p] ^= key[(uint8_t)(key[i1] + key[i2])];
    }
}
EXPORT void init_selene(uint8_t *restrict dst, const uint8_t *restrict key, const size_t ksize, const uint32_t seed) {
    INIT_MT19937(mt);
    MT19937_seed(&mt,seed);
    size_t kc = 0;

    for (size_t i=0;i < 0x10000;i++) {
        dst[i] = (uint8_t)(key[kc++] ^ (MT19937_rand(&mt) >> 16));
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rc4_playpond(uint8_t *restrict buf, const size_t size, const uint8_t *restrict key, const size_t ksize, const size_t drop) {
    uint8_t S[0x100];
    for (size_t i=0;i < 0x100;i++) S[i] = i;

    uint8_t j = 0;
    size_t kc = 0;
    for (size_t ix=0;ix < 0x100;ix++) {
        for (size_t i=0;i < 0x100;i++) {
            j += S[i] + key[kc];
            uint8_t b = S[j];
            S[j] = S[i];
            S[i] = b;
            kc += 1;
            if (kc >= ksize) kc = 0;
        }
    }

    j = 0;
    uint8_t i = 0;
    for (size_t ix=0;ix < drop;ix++) {
        i += 1;
        j += S[i];
        uint8_t b = S[j];
        S[j] = S[i];
        S[i] = b;
    }

    for (size_t p=0;p < size;p++) {
        i += 1;
        j += S[i];
        uint8_t b = S[j];
        S[j] = S[i];
        S[i] = b;
        buf[p] ^= S[(S[i] + S[j]) & 0xFF];
    }
}
EXPORT void decrypt_zipcrypto(uint8_t *restrict buf, const size_t size, const uint8_t *restrict key, const size_t ksize) {
    uint32_t crc32t[0x100];
    for (size_t i=0;i < 0x100;i++) {
        uint32_t c = i;
        for (size_t j=0;j < 8;j++) {
            if (c & 1) c = (c >> 1) ^ 0xEDB88320;
            else c = c >> 1;
        }
        crc32t[i] = c;
    }
    #define crc32(crc,b) ((crc) >> 8) ^ crc32t[((crc) ^ (b)) & 0xFF]

    uint32_t k0 = 0x12345678;
    uint32_t k1 = 0x23456789;
    uint32_t k2 = 0x34567890;

    #define mix(b) \
        k0 = crc32(k0,(b));\
        k1 += (k0 & 0xFF);\
        k1 = k1 * 0x8088405 + 1;\
        k2 = crc32(k2,k1 >> 24);

    for (size_t p=0;p < ksize;p++)
        mix(key[p]);

    for (size_t p=0;p < size;p++) {
        uint32_t k = k2 | 2;
        buf[p] ^= (k * (k^1)) >> 8;
        mix(buf[p]);
    }

    #undef crc32
    #undef mix
}
EXPORT void decrypt_remedy_ras(uint8_t *restrict buf, const size_t size, const uint32_t key) {
    int32_t tmp1 = key;
    if (!tmp1) tmp1 = 1;
    uint8_t tmp2 = 0x12;

    for (size_t p=0;p < size;p++) {
        tmp1 = -2 * (tmp1 / 177) + 171 * (tmp1 % 177);
        uint8_t b = ((buf[p] << p % 5) | (buf[p] >> (8 - p % 5))) ^ tmp2;
        tmp2 += 6;
        buf[p] = (uint8_t)(b + tmp1);
    }
}
EXPORT void init_empire_magic(uint8_t *restrict buf) {
    uint64_t seed = 0x8647d59f;
    uint32_t state = 0;
    for (uint16_t i=0;i < 0x400;i++) {
        uint64_t prod = seed * 0x4e35;
        state = (((uint32_t)prod == 0xFFFFFFFF) | ((uint32_t)seed * 0x15a)) + (uint32_t)(prod >> 32) + state * 0x4e35;
        buf[i] = (uint8_t)state;
        seed = (uint32_t)prod + 1;
    }
}
EXPORT void decrypt_empire_magic(uint8_t *restrict buf, const size_t size, const uint8_t *restrict key, const size_t ksize,
                           const uint8_t *restrict table, const uint32_t offset) {
    for (size_t p=0;p < size;p++)
        buf[p] = (buf[p] + 1 + key[p % ksize]) ^ table[(offset + p) % 0x3cb];
}
EXPORT void decrypt_camelot_exe(uint8_t *restrict buf, const size_t size, uint8_t key, const uint8_t off) {
    if (size < 2) return;
    uint8_t pre = buf[size - 1];
    for (ssize_t p=size - 2;p >= 0;p--) {
        uint8_t tpre = buf[p];
        buf[p] ^= ROT8L(pre) ^ key;
        pre = tpre;
        key += off;
    }
}
EXPORT int8_t decrypt_zipd(uint8_t *restrict buf, const size_t size) {
    if (size < 7) return -1;
    const uint8_t chk[6] = {0, 0, 0, 0, 5, 0x78};

    uint16_t s=0;
    while (1) {
        uint16_t ts = s;
        ts = micro_c_rand(ts);
        int8_t match = 1;
        for (uint8_t p=0;p < 6;p++) {
            if ((uint8_t)(buf[1 + p] ^ (ts = micro_c_rand(ts))) != chk[p]) {
                match = 0;
                break;
            }
        }
        if (match) break;
        if (s == 0xFFFF) return -1;
        s++;
    }

    for (size_t p=0;p < size;p++) buf[p] ^= (s = micro_c_rand(s));
    return 0;
}

static inline uint32_t tfit_get_t(const uint32_t *t, const uint8_t *buf, const uint8_t x) {
    return t[0x100 * x + buf[x]];
}
#define TFIT_ROUND_BLOCK(t,n,x10, x11, x12, x13,\
                             x20, x21, x22, x23,\
                             x30, x31, x32, x33,\
                             x40, x41, x42, x43)\
    void CONCATX(t,crypt_tfit_round##n)(uint8_t *restrict buf, const uint32_t *restrict k, const uint32_t *restrict t) {\
        uint32_t tmp[4];\
        tmp[0] = tfit_get_t(t,buf,x10) ^ tfit_get_t(t,buf,x11) ^ tfit_get_t(t,buf,x12) ^ tfit_get_t(t,buf,x13) ^ k[0];\
        tmp[1] = tfit_get_t(t,buf,x20) ^ tfit_get_t(t,buf,x21) ^ tfit_get_t(t,buf,x22) ^ tfit_get_t(t,buf,x23) ^ k[1];\
        tmp[2] = tfit_get_t(t,buf,x30) ^ tfit_get_t(t,buf,x31) ^ tfit_get_t(t,buf,x32) ^ tfit_get_t(t,buf,x33) ^ k[2];\
        tmp[3] = tfit_get_t(t,buf,x40) ^ tfit_get_t(t,buf,x41) ^ tfit_get_t(t,buf,x42) ^ tfit_get_t(t,buf,x43) ^ k[3];\
        memcpy(buf,tmp,0x10);\
    }
TFIT_ROUND_BLOCK(en,A, 0 ,1 ,2 ,3 ,
                       4 ,5 ,6 ,7 ,
                       8 ,9 ,10,11,
                       12,13,14,15)
TFIT_ROUND_BLOCK(en,B, 0 ,5 ,10,15,
                       3 ,4 ,9 ,14,
                       2 ,7 ,8 ,13,
                       1 ,6 ,11,12)
TFIT_ROUND_BLOCK(de,B, 0 ,7 ,10,13,
                       1, 4 ,11,14,
                       2, 5 ,8 ,15,
                       3, 6 ,9 ,12)
void decrypt_tfit_block(const uint8_t *restrict src, uint8_t *dst, const uint8_t *iv,
                        const size_t rounds, const uint32_t *restrict k, const uint32_t *restrict t) {
    uint8_t tmp[16];
    if (iv != NULL) {
        for (size_t i=0;i < 16;i++) tmp[i] = src[i] ^ iv[i];
    } else memcpy(tmp,src,0x10);
    encrypt_tfit_roundA(tmp,k + 0,t + 0x0000);
    encrypt_tfit_roundA(tmp,k + 4,t + 0x1000);
    for (size_t i=2;i < rounds - 1;i++)
        decrypt_tfit_roundB(tmp,k + i*4,t + i*0x1000);
    encrypt_tfit_roundA(tmp,k + (rounds - 1)*4,t + (rounds - 1)*0x1000);
    memcpy(dst,tmp,0x10);
}
void encrypt_tfit_block(const uint8_t *restrict src, uint8_t *dst, const uint8_t *iv,
                        const size_t rounds, const uint32_t *restrict k, const uint32_t *restrict t) {
    uint8_t tmp[16];
    if (iv != NULL) {
        for (size_t i=0;i < 16;i++) tmp[i] = src[i] ^ iv[i];
    } else memcpy(tmp,src,0x10);
    encrypt_tfit_roundA(tmp,k + 0,t + 0x0000);
    encrypt_tfit_roundA(tmp,k + 4,t + 0x1000);
    for (size_t i=2;i < rounds - 1;i++)
        encrypt_tfit_roundB(tmp,k + i*4,t + i*0x1000);
    encrypt_tfit_roundA(tmp,k + (rounds - 1)*4,t + (rounds - 1)*0x1000);
    memcpy(dst,tmp,0x10);
}
EXPORT void decrypt_tfit(uint8_t *restrict src, const size_t size, uint8_t *restrict dst, const uint8_t *restrict iv,
                   const uint32_t *restrict key, const uint32_t *restrict table, const size_t block_size) {
    uint8_t tmp[16];
    memcpy(tmp,iv,0x10);
    for (size_t p=0;p < size;p += block_size + 0x10) {
        for (size_t i=0;i < block_size / 16;i++) {
            decrypt_tfit_block(src + p + i*16, dst + p + i*16, tmp, 17, key, table);
            memcpy(tmp,dst + p + i*16,0x10);
        }
        decrypt_tfit_block(src + p + block_size, tmp, tmp, 17, key, table);
    }
}
EXPORT void mac_cmac_tfit(uint8_t *restrict src, const size_t size, uint8_t *restrict dst,
                    const uint32_t *restrict key, const uint32_t *restrict table) {
    uint8_t tmp[16] = {0};
    uint8_t lblk_scrmbl[16];

    encrypt_tfit_block(tmp, lblk_scrmbl, NULL, 13, key, table);
    DBLGF(lblk_scrmbl, lblk_scrmbl);
    if (size != 0) {
        size_t blocks = size / 16 + (size % 16 != 0);
        for (size_t i=0;i < blocks - 1;i++)
            encrypt_tfit_block(src + i*16, tmp, tmp, 13, key, table);
    }

    if (size % 16 || size == 0) {
        DBLGF(lblk_scrmbl, lblk_scrmbl);

        uint8_t block[16] = {0};
        block[size % 16] = 0x80;
        memcpy(block, src + size - (size % 16), size % 16);
        for (size_t i=0;i < 16;i++) tmp[i] ^= lblk_scrmbl[i] ^ block[i];
    } else {
        for (size_t i=0;i < 16;i++) tmp[i] ^= lblk_scrmbl[i] ^ src[size - 16 + i];
    }

    encrypt_tfit_block(tmp, dst, NULL, 13, key, table);
}

EXPORT uint32_t hash_pivotal(const uint8_t *restrict src, const size_t size) {
    uint32_t h = 1;

    for (size_t p=0;p < size;p++) {
        uint8_t b = src[p];
        for (int i=0;i < 8;i++) {
            h = (h << 1) | (((h >> 21) ^ (h >> 1) ^ h ^ (h >> 31) ^ (b >> i)) & 1);
        }
    }

    return h;
}
EXPORT uint32_t hash_super_fast_le(const uint8_t *restrict src, const size_t size) {
    if (size == 0) return 0;

    uint32_t h = (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        h += read16le(s);s+=2;
        h = (h << 16) ^ ((read16le(s) << 11) ^ h);s+=2;
        h += h >> 11;
    }

    switch (rem) {
        case 3:
            h += read16le(s);s+=2;
            h ^= (h << 16) ^ ((uint32_t)(int8_t)s[0] << 18);
            h += h >> 11;
            break;
        case 2:
            h += read16le(s);s+=2;
            h ^= h << 11;
            h += h >> 17;
            break;
        case 1:
            h += (uint32_t)(int8_t)s[0];
            h ^= h << 10;
            h += h >> 1;
            break;
    }

    h ^= h << 3;
    h += h >> 5;
    h ^= h << 4;
    h += h >> 17;
    h ^= h << 25;
    h += h >> 6;

    return h;
}
EXPORT uint32_t hash_super_fast_be(const uint8_t *restrict src, const size_t size) {
    if (size == 0) return 0;

    uint32_t h = (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        h += read16be(s);s+=2;
        h = (h << 16) ^ ((read16be(s) << 11) ^ h);s+=2;
        h += h >> 11;
    }

    switch (rem) {
        case 3:
            h += read16be(s);s+=2;
            h ^= (h << 16) ^ ((uint32_t)(int8_t)s[0] << 18);
            h += h >> 11;
            break;
        case 2:
            h += read16be(s);s+=2;
            h ^= h << 11;
            h += h >> 17;
            break;
        case 1:
            h += (uint32_t)(int8_t)s[0];
            h ^= h << 10;
            h += h >> 1;
            break;
    }

    h ^= h << 3;
    h += h >> 5;
    h ^= h << 4;
    h += h >> 17;
    h ^= h << 25;
    h += h >> 6;

    return h;
}
EXPORT uint32_t hash_elf(const uint8_t *restrict src, const size_t size) {
    uint32_t h = 0;
    uint32_t hi;
    for (size_t p=0;p < size;p++) {
        h = (h << 4) + src[p];
        if (hi = h & 0xf0000000)
            h ^= hi >> 24;
        h &= ~hi;
    }
    return h;
}
EXPORT uint32_t hash_ap(const uint8_t *restrict src, const size_t size) {
    uint32_t h = 0xAAAAAAAA;
    for (size_t p=0;p < size;p++) {
        h ^= ((p & 1) == 0) ? (  (h <<  7) ^  src[p] * (h >> 3)) :
                              (~((h << 11) + (src[p] ^ (h >> 5))));
    }
    return h;
}
#define MURMUR2_32_M 0x5bd1e995
EXPORT uint32_t hash_murmur2_le(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed ^ (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32le(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    switch (rem) {
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_32_M;
    }

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;
    return h;
}
EXPORT uint32_t hash_murmur2_be(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed ^ (uint32_t)size;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32be(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    switch (rem) {
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_32_M;
    }

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;
    return h;
}
EXPORT uint32_t hash_murmur2A_le(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32le(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    uint32_t t = 0;
    switch (rem) {
        case 3: t ^= s[2] << 16;
        case 2: t ^= s[1] << 8;
        case 1: t ^= s[0];
    }

    t *= MURMUR2_32_M;
    t ^= t >> 24;
    h = (h * MURMUR2_32_M) ^ (t * MURMUR2_32_M);
    uint32_t l = (uint32_t)size;
    l *= MURMUR2_32_M;
    l ^= l >> 24;
    h = (h * MURMUR2_32_M) ^ (l * MURMUR2_32_M);

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;

    return h;
}
EXPORT uint32_t hash_murmur2A_be(const uint8_t *restrict src, const size_t size, const uint32_t seed) {
    uint32_t h = seed;
    uint8_t rem = size & 3;
    size_t len = size >> 2;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k = read32be(s);s+=4;
        k *= MURMUR2_32_M;
        k ^= k >> 24;
        h = (h * MURMUR2_32_M) ^ (k * MURMUR2_32_M);
    }

    uint32_t t = 0;
    switch (rem) {
        case 3: t ^= s[2] << 16;
        case 2: t ^= s[1] << 8;
        case 1: t ^= s[0];
    }

    t *= MURMUR2_32_M;
    t ^= t >> 24;
    h = (h * MURMUR2_32_M) ^ (t * MURMUR2_32_M);
    uint32_t l = (uint32_t)size;
    l *= MURMUR2_32_M;
    l ^= l >> 24;
    h = (h * MURMUR2_32_M) ^ (l * MURMUR2_32_M);

    h ^= h >> 13;
    h *= MURMUR2_32_M;
    h ^= h >> 15;

    return h;
}
#define MURMUR2_64_M 0xc6a4a7935bd1e995
EXPORT uint64_t hash_murmur2_64A_le(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint64_t h = seed ^ ((uint64_t)size * MURMUR2_64_M);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint64_t k = read64le(s);s+=8;
        k *= MURMUR2_64_M;
        k ^= k >> 47;
        h = (h ^ (k * MURMUR2_64_M)) * MURMUR2_64_M;
    }

    switch (rem) {
        case 7: h ^= (uint64_t)s[6] << 48;
        case 6: h ^= (uint64_t)s[5] << 40;
        case 5: h ^= (uint64_t)s[4] << 32;
        case 4: h ^= (uint64_t)s[3] << 24;
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_64_M;
    }

    h ^= h >> 47;
    h *= MURMUR2_64_M;
    h ^= h >> 47;
    return h;
}
EXPORT uint64_t hash_murmur2_64A_be(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint64_t h = seed ^ ((uint64_t)size * MURMUR2_64_M);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint64_t k = read64be(s);s+=8;
        k *= MURMUR2_64_M;
        k ^= k >> 47;
        h = (h ^ (k * MURMUR2_64_M)) * MURMUR2_64_M;
    }

    switch (rem) {
        case 7: h ^= (uint64_t)s[6] << 48;
        case 6: h ^= (uint64_t)s[5] << 40;
        case 5: h ^= (uint64_t)s[4] << 32;
        case 4: h ^= (uint64_t)s[3] << 24;
        case 3: h ^= s[2] << 16;
        case 2: h ^= s[1] << 8;
        case 1: h ^= s[0];
                h *= MURMUR2_64_M;
    }

    h ^= h >> 47;
    h *= MURMUR2_64_M;
    h ^= h >> 47;
    return h;
}
EXPORT uint64_t hash_murmur2_64B_le(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint32_t h1 = (uint32_t)seed ^ (uint32_t)size;
    uint32_t h2 = (uint32_t)(seed >> 32);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k1 = read32le(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        uint32_t k2 = read32le(s);s+=4;
        k2 *= MURMUR2_32_M;
        k2 ^= k2 >> 24;
        h2 = (h2 * MURMUR2_32_M) ^ (k2 * MURMUR2_32_M);
    }

    if (rem >= 4) {
        uint32_t k1 = read32le(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        rem -= 4;
    }

    switch (rem) {
        case 3: h2 ^= s[2] << 16;
        case 2: h2 ^= s[1] << 8;
        case 1: h2 ^= s[0];
                h2 *= MURMUR2_32_M;
    }

    h1 ^= h2 >> 18;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 22;h2 *= MURMUR2_32_M;
    h1 ^= h2 >> 17;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 19;h2 *= MURMUR2_32_M;

    uint64_t h = h1;
    return (h << 32) | h2;
}
EXPORT uint64_t hash_murmur2_64B_be(const uint8_t *restrict src, const size_t size, const uint64_t seed) {
    uint32_t h1 = (uint32_t)seed ^ (uint32_t)size;
    uint32_t h2 = (uint32_t)(seed >> 32);
    uint8_t rem = size & 7;
    size_t len = size >> 3;
    const uint8_t *restrict s = src;

    for (;len > 0;len--) {
        uint32_t k1 = read32be(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        uint32_t k2 = read32be(s);s+=4;
        k2 *= MURMUR2_32_M;
        k2 ^= k2 >> 24;
        h2 = (h2 * MURMUR2_32_M) ^ (k2 * MURMUR2_32_M);
    }

    if (rem >= 4) {
        uint32_t k1 = read32be(s);s+=4;
        k1 *= MURMUR2_32_M;
        k1 ^= k1 >> 24;
        h1 = (h1 * MURMUR2_32_M) ^ (k1 * MURMUR2_32_M);
        rem -= 4;
    }

    switch (rem) {
        case 3: h2 ^= s[2] << 16;
        case 2: h2 ^= s[1] << 8;
        case 1: h2 ^= s[0];
                h2 *= MURMUR2_32_M;
    }

    h1 ^= h2 >> 18;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 22;h2 *= MURMUR2_32_M;
    h1 ^= h2 >> 17;h1 *= MURMUR2_32_M;
    h2 ^= h1 >> 19;h2 *= MURMUR2_32_M;

    uint64_t h = h1;
    return (h << 32) | h2;
}
EXPORT uint32_t hash_empire_magic(const uint8_t *restrict src, const size_t size, const int8_t end) {
    uint32_t h = size * 0x1EEF;

    uint8_t ss = (size < 4) ? size : 4;
    size_t off = end ? (size - ss) : 0;
    for (uint8_t i=0;i < ss;i++) h += src[off + i] << (24 - i*8);
    for (size_t p=0;p < size;p++) h += src[p] * 0x2F;

    return h % 0x3CB;
}

#ifdef __cplusplus
}
#endif
