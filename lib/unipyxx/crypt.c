#include "util.h"
#include "const.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t d[4];
} hash128_t;
typedef struct {
    uint32_t d[5];
} hash160_t;
typedef struct {
    uint32_t d[8];
} hash256_t;
typedef struct {
    uint32_t d[16];
} hash512_t;
#define HASH128_ABC(H) uint32_t a = (H).d[0], b = (H).d[1], c = (H).d[2], d = (H).d[3]
#define PHASH128_ABC(H) uint32_t a = (H)->d[0], b = (H)->d[1], c = (H)->d[2], d = (H)->d[3]
#define HASH160_ABC(H) uint32_t a = (H).d[0], b = (H).d[1], c = (H).d[2], d = (H).d[3], e = (H).d[4]
#define PHASH160_ABC(H) uint32_t a = (H)->d[0], b = (H)->d[1], c = (H)->d[2], d = (H)->d[3], e = (H)->d[4]
#define HASH256_ABC(H) uint32_t a = (H).d[0], b = (H).d[1], c = (H).d[2], d = (H).d[3], e = (H).d[4], f = (H).d[5], g = (H).d[6], h = (H).d[7]
#define PHASH256_ABC(H) uint32_t a = (H)->d[0], b = (H)->d[1], c = (H)->d[2], d = (H)->d[3], e = (H)->d[4], f = (H)->d[5], g = (H)->d[6], h = (H)->d[7]

// expects a zero padded buffer
static inline void md_pad64(uint8_t buf[0x40], uint8_t c, void *restrict H, const uint64_t bits,
                            void (*process_block)(void *restrict, const uint32_t[16])) {
    uint32_t tbuf[0x10];
    buf[c] = 0x80;INCWi(c, 6);
    if (c > 0x38) c = 0;
    if (c == 0) {
        memcpy(tbuf, buf, 0x40);
        process_block(H, tbuf);
    }

    for (int i=c;i < 0x38;i++) buf[i] = 0;
    memcpy(tbuf, buf, 0x40);
    memcpy(tbuf + 14, &bits, 8);
    process_block(H, tbuf);
}
static inline void aes_mix(uint32_t *restrict arr,
                     const uint32_t i0, const uint32_t i1, const uint32_t i2, const uint32_t i3) {
    for (int i=0;i < 4;i++) {
        uint32_t a = arr[i0 * 4 + i];uint32_t b = arr[i1 * 4 + i];
        uint32_t c = arr[i2 * 4 + i];uint32_t d = arr[i3 * 4 + i];
        uint32_t ab = a ^ b;uint32_t bc = b ^ c;uint32_t cd = c ^ d;
        uint32_t abx = ((ab & 0x80808080U) >> 7) * 27
                     ^ ((ab & 0x7F7F7F7FU) << 1);
        uint32_t bcx = ((bc & 0x80808080U) >> 7) * 27
                     ^ ((bc & 0x7F7F7F7FU) << 1);
        uint32_t cdx = ((cd & 0x80808080U) >> 7) * 27
                     ^ ((cd & 0x7F7F7F7FU) << 1);
        arr[i0 * 4 + i] = abx ^ bc ^ d;
        arr[i1 * 4 + i] = bcx ^ cd ^ a;
        arr[i2 * 4 + i] = cdx ^ ab ^ d;
        arr[i3 * 4 + i] = abx ^ bcx ^ cdx ^ ab ^ c;
    }
}

static inline void shiftlx_arr32(uint32_t *restrict arr, const uint32_t o, const uint32_t s, const uint32_t c) {
    if (c < 2) return;
    uint32_t t = arr[o];
    for (uint32_t i=0;i < c - 1;i++) arr[o + i*s] = arr[o + (i + 1)*s];
    arr[o + (c - 1)*s] = t;
}
static inline void shiftrx_arr32(uint32_t *restrict arr, const uint32_t o, const uint32_t s, const uint32_t c) {
    if (c < 2) return;
    uint32_t t = arr[o + (c - 1)*s];
    for (uint32_t i=c - 1;i > 0;i--) arr[o + i*s] = arr[o + (i - 1)*s];
    arr[o] = t;
}
static inline void swap_arr32(uint32_t *restrict arr, const uint32_t i1, const uint32_t i2) {
    uint32_t t = arr[i1];
    arr[i1] = arr[i2];
    arr[i2] = t;
}
static inline void arr_swap(uint8_t *restrict arr, uint8_t *restrict Tarr, const size_t size, const size_t len) {
    memcpy(Tarr, arr + (size - len), len);
    memmove(arr + len, arr, size - len);
    memcpy(arr, Tarr, len);
}
static inline void arr32_swap(uint32_t *restrict arr, uint32_t *restrict Tarr, const size_t size, const size_t len) {
    arr_swap((uint8_t *)arr, (uint8_t *)Tarr, size * sizeof(uint32_t), len * sizeof(uint32_t));
}
static inline void swaple32_arr(uint32_t *restrict arr, const size_t size) {
    for (size_t i=0;i < size;i++) arr[i] = SWAPLE32(arr[i]);
}
static inline void swapbe32_arr(uint32_t *restrict arr, const size_t size) {
    for (size_t i=0;i < size;i++) arr[i] = SWAPBE32(arr[i]);
}
static inline void arr32_map8(uint32_t *restrict arr, uint32_t *restrict out, const uint8_t size, const uint8_t *restrict map) {
    for (uint8_t i=0;i < size;i++) out[i] = arr[map[i]];
}

typedef struct {
    int32_t MATRIX_A;
    uint32_t TEMPERING_MASK_B;
    uint32_t TEMPERING_MASK_C;
    uint32_t INIT_MULT;

    int32_t mt[MT_N];
    int32_t mti;
} MT19937S;
#define INIT_MT19937S(X) MT19937S X = { .MATRIX_A = (int32_t)MT_MATRIX_A, .TEMPERING_MASK_B = MT_TEMPERING_MASK_B,\
                                        .TEMPERING_MASK_C = MT_TEMPERING_MASK_C, .INIT_MULT = MT_INIT_MULT,\
                                        .mt = { 0 }, .mti = MT_N + 1 }
void MT19937S_seed(MT19937S *restrict ctx, int32_t seed) {
    ctx->mt[0] = seed;
    for (ctx->mti=1;ctx->mti < MT_N;ctx->mti++) {
        int32_t last = ctx->mt[ctx->mti - 1];
        ctx->mt[ctx->mti] = (int32_t)(ctx->INIT_MULT * (uint32_t)(last ^ (last >> 30)) + (uint32_t)ctx->mti);
    }
}
int32_t MT19937S_rand(MT19937S *restrict ctx) {
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

typedef struct {
    uint32_t MATRIX_A;
    uint32_t TEMPERING_MASK_B;
    uint32_t TEMPERING_MASK_C;
    uint32_t INIT_MULT;

    uint32_t mt[MT_N];
    uint32_t mti;
} MT19937U;
#define INIT_MT19937U(X) MT19937U X = { .MATRIX_A = MT_MATRIX_A, .TEMPERING_MASK_B = MT_TEMPERING_MASK_B,\
                                        .TEMPERING_MASK_C = MT_TEMPERING_MASK_C, .INIT_MULT = MT_INIT_MULT,\
                                        .mt = { 0 }, .mti = MT_N + 1 }
void MT19937U_seed(MT19937U *restrict ctx, uint32_t seed) {
    ctx->mt[0] = seed;
    for (ctx->mti=1;ctx->mti < MT_N;ctx->mti++) {
        uint32_t last = ctx->mt[ctx->mti - 1];
        ctx->mt[ctx->mti] = (uint32_t)(ctx->INIT_MULT * (uint32_t)(last ^ (last >> 30)) + (uint32_t)ctx->mti);
    }
}
uint32_t MT19937U_rand(MT19937U *restrict ctx) {
    uint32_t y;
    const uint32_t mag01[2] = { 0x0U, ctx->MATRIX_A };

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
    y ^= (uint32_t)(((uint32_t)y << 7) & ctx->TEMPERING_MASK_B);
    y ^= (uint32_t)(((uint32_t)y << 15) & ctx->TEMPERING_MASK_C);
    y ^= y >> 18;
    return y;
}

uint16_t micro_c_rand(uint16_t state) {
    return state * MICRO_C_RAND_A + MICRO_C_RAND_C;
}

EXPORT void decrypt_inv(uint8_t *restrict buf, const size_t size) {
    for (size_t p=0;p < size;p++) buf[p] = ~buf[p];
}
EXPORT void decrypt_swp4(uint8_t *restrict buf, const size_t size) {
    for (size_t p=0;p < size;p++) buf[p] = SWAP8(buf[p]);
}
EXPORT void decrypt_roll(uint8_t *restrict buf, const size_t size,
                   const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        buf[p] -= key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rolr(uint8_t *restrict buf, const size_t size,
                   const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        buf[p] += key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_xor(uint8_t *restrict buf, const size_t size,
                  const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        buf[p] ^= key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_rxor(uint8_t *restrict buf, const size_t size, const uint8_t key) {
    if (size == 0) return;
    buf[0] ^= key;
    for (size_t p=1;p < size;p++) buf[p] ^= buf[p - 1];
}
EXPORT void decrypt_cxor(uint8_t *restrict buf, const size_t size,
                   const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        buf[p] ^= (key[kc++] + p);
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_cxori(uint8_t *restrict buf, const size_t size,
                    const uint8_t *restrict key, const size_t ksize, const size_t iv) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        buf[p] = (buf[p] - (p + iv)) ^ key[kc++];
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_dxor(uint8_t *restrict buf,  const size_t size,
                   const uint8_t *restrict key1, const size_t ksize1,
                   const uint8_t *restrict key2, const size_t ksize2) {
    size_t kc1 = 0;
    size_t kc2 = 0;
    for (size_t p=0;p < size;p++) {
        buf[p] ^= key1[kc1++] ^ key2[kc2++];
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

    #define TEA_SWAP32(x) (le) ? SWAPLE32((x)) : SWAPBE32((x))
    for (int i=0;i < 4;i++) k[i] = TEA_SWAP32(k[i]);

    for (size_t p=0;p < bc;p+=2) {
        uint32_t v0 = TEA_SWAP32(inp[p]);
        uint32_t v1 = TEA_SWAP32(inp[p + 1]);

        uint32_t sv = (TEA_DELTA * 32) & 0xFFFFFFFF;
        for (int i = 0; i < 32; i++) {
            v1 -= ((v0 << 4) + k[2]) ^ (v0 + sv) ^ ((v0 >> 5) + k[3]);
            v0 -= ((v1 << 4) + k[0]) ^ (v1 + sv) ^ ((v1 >> 5) + k[1]);
            sv -= TEA_DELTA;
        }

        out[p] = TEA_SWAP32(v0);
        out[p + 1] = TEA_SWAP32(v1);
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
EXPORT void init_selene(uint8_t *restrict dst, const uint8_t *restrict key, const size_t ksize, const uint32_t seed) {
    INIT_MT19937S(mt);
    MT19937S_seed(&mt,seed);
    size_t kc = 0;

    for (size_t i=0;i < 0x10000;i++) {
        dst[i] = (uint8_t)(key[kc++] ^ (MT19937S_rand(&mt) >> 16));
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
        j += S[++i];
        uint8_t b = S[j];
        S[j] = S[i];
        S[i] = b;
    }

    for (size_t p=0;p < size;p++) {
        j += S[++i];
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
EXPORT void decrypt_camelot_xor(uint8_t *restrict buf, const size_t size, const uint8_t key) {
    if (size < 2) return;
    uint8_t tkey = key * 4;
    uint8_t pre = buf[size - 1];
    for (ssize_t p=size - 2;p >= 0;p--) {
        uint8_t tpre = buf[p];
        buf[p] ^= ROT8R(pre, 1) ^ tkey;
        pre = tpre;
        tkey += key;
    }
}
EXPORT void decrypt_camelot_rand(uint8_t *restrict buf, const size_t size, const uint8_t key, const uint32_t seed, const size_t drop) {
    if (size < 2) return;
    INIT_MT19937U(mt);
    mt.TEMPERING_MASK_C = MT_CAMELOT_TEMPERING_MASK_C;
    MT19937U_seed(&mt,seed);
    for (size_t i=0;i < drop;i++) MT19937U_rand(&mt);

    uint8_t tkey = key * 4;
    uint8_t pre = buf[size - 1];
    for (ssize_t p=size - 2;p >= 0;p--) {
        uint8_t tpre = buf[p];
        buf[p] ^= ROT8R(pre, 1) ^ tkey ^ (uint8_t)MT19937U_rand(&mt);
        pre = tpre;
        tkey += key;
    }
}
EXPORT int8_t decrypt_zipd(uint8_t *restrict buf, const size_t size) {
    if (size < 7) return -1;
    const uint8_t chk[6] = ZIPD_CHECK;

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
EXPORT void decrypt_legaia2(uint32_t *restrict buf, const size_t size, const uint32_t key) {
    uint32_t k = key * ((buf[1] & 0xFFFF) ^ (buf[1] >> 16));
    for (size_t p=4;p < size / 4;p++) {
        buf[p] ^= k;
        k = k * 5 + 1;
    }
}
EXPORT void decrypt_ady_glue(uint8_t *restrict buf, const size_t size,
                       const uint8_t *restrict key, const size_t ksize) {
    size_t kc = 0;
    for (size_t p=0;p < size;p++) {
        buf[p] = ROT8R(buf[p] - key[kc++], 1);
        if (kc >= ksize) kc = 0;
    }
}
EXPORT void decrypt_airrc4(uint8_t *restrict buf, const size_t size, const uint8_t *restrict key, const size_t ksize) {
    uint8_t S[0x100];
    for (uint16_t i=0;i < 0x100;i++) S[i] = i;
    uint8_t j = 0;
    size_t kp = 0;
    for (uint16_t i=0;i < 0x100;i++) {
        j += S[i] + key[kp++];
        if (kp >= ksize) kp = 0;
        S[i] ^= S[j];
        S[j] ^= S[i];
        S[i] ^= S[j];
    }

    uint8_t i = 0;
    j = 0;
    for (size_t p=0;p < size;p++) {
        j += S[++i];
        S[i] ^= S[j];
        S[j] ^= S[i];
        S[i] ^= S[j];
        buf[p] ^= S[(S[i] + S[j]) & 0xFF];
    }
}
EXPORT void decrypt_eac(uint8_t *restrict buf, const size_t size, const uint8_t key) {
    if (size < 2) return;

    buf[size - 1] += key - key * size;
    for (size_t p=size - 2;p > 0;p--)
        buf[p] += -key * p - buf[p + 1];
    buf[0] -= buf[1];
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

EXPORT int8_t hash_crc_init(uint8_t *restrict t, const uint32_t size, const uint64_t poly, const int8_t reflect) {
    if (size % 8 || size == 0 || size > 64) return -1;
    const uint64_t mm = MASK(size);
    const uint8_t ref = reflect != 0;
    uint64_t pol = poly & mm;
    if (ref) pol = REFLECT(pol, size);

    t[0] = ref;
    *(uint32_t *)(t + 1) = size;

    if (ref) {
        for (uint16_t b=0;b < 256;b++) {
            uint64_t crc = b;
            for (uint8_t i=0;i < 8;i++) {
                if (crc & 1) crc = (crc >> 1) ^ pol;
                else crc >>= 1;
            }
            *(uint64_t *)(t + 5 + b * 8) = crc & mm;
        }
    } else {
        const uint64_t cm = 1ULL << (size - 1);
        const size_t sh = (size < 8) ? 0 : (size - 8);
        for (uint16_t b=0;b < 256;b++) {
            uint64_t crc = b << sh;
            for (uint8_t i=0;i < 8;i++) {
                if (crc & cm) crc = (crc << 1) ^ pol;
                else crc <<= 1;
            }
            *(uint64_t *)(t + 5 + b * 8) = crc & mm;
        }
    }

    return 0;
}
EXPORT uint64_t hash_crc(const uint8_t *restrict src, const uint32_t size, const uint8_t *restrict t,
                         uint64_t init, uint64_t xor, const uint64_t value, const int8_t has_value) {
    const int8_t ref = t[0];
    const uint32_t sizei = *(uint32_t *)(t + 1);
    const uint64_t mm = (sizei == 64) ? ~0ULL : (1ULL << sizei) - 1;
    init &= mm;
    xor &= mm;

    uint64_t h;
    if (has_value) h = (value & mm) ^ xor;
    else h = init;
    if (ref)
        for (size_t p=0;p < size;p++)
            h = (h >> 8) ^ *(uint64_t *)(t + 5 + ((h ^ src[p]) & 0xFF) * 8);
    else {
        const size_t sh = (sizei < 8) ? 0 : (sizei - 8);
        for (size_t p=0;p < size;p++)
            h = ((h << 8) & mm) ^ *(uint64_t *)(t + 5 + ((src[p] ^ (h >> sh)) & 0xFF) * 8);
    }
    return h ^ xor;
}
EXPORT uint64_t hash_fletcher(const uint8_t *restrict src, const size_t size, const uint64_t init,
                              const uint8_t bits, const uint64_t base) {
    const uint8_t s = bits / 2;
    uint64_t h1 = init & MASK(s);
    uint64_t h2 = (init >> s) & MASK(s);
    for (size_t p=0;p < size;p++) {
        h1 = (h1 + src[p]) % base;
        h2 = (h2 + h1) % base;
    }
    return ((h2 << s) | h1) & MASK(bits);
}
EXPORT uint32_t hash_prng32(const uint8_t *restrict src, const size_t size, const uint32_t init, const uint32_t mult, const uint32_t add) {
    uint32_t h = init;
    for (size_t p=0;p < size;p++) h = h * mult + add + src[p];
    return h;
}
EXPORT uint64_t hash_prng64(const uint8_t *restrict src, const size_t size, const uint64_t init, const uint64_t mult, const uint64_t add) {
    uint64_t h = init;
    for (size_t p=0;p < size;p++) h = h * mult + add + src[p];
    return h;
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
EXPORT uint32_t hash_westwood(const uint32_t *restrict src, const size_t size) {
    uint32_t h = 0;
    for (size_t p=0;p < size;p++) h = ROT32L(h, 1) + src[p];
    return h;
}
EXPORT uint64_t hash_fnv1_64(const uint8_t *restrict src, const size_t size, const uint64_t seed, const uint64_t prime) {
    uint64_t h = seed;
    for (size_t p=0;p < size;p++) h = (h * prime) ^ src[p];
    return h;
}
EXPORT uint64_t hash_fnv1a_64(const uint8_t *restrict src, const size_t size, const uint64_t seed, const uint64_t prime) {
    uint64_t h = seed;
    for (size_t p=0;p < size;p++) h = (h ^ src[p]) * prime;
    return h;
}
EXPORT uint32_t hash_fnv1_32(const uint8_t *restrict src, const size_t size, const uint32_t seed, const uint32_t prime) {
    uint32_t h = seed;
    for (size_t p=0;p < size;p++) h = (h * prime) ^ src[p];
    return h;
}
EXPORT uint32_t hash_fnv1a_32(const uint8_t *restrict src, const size_t size, const uint32_t seed, const uint32_t prime) {
    uint32_t h = seed;
    for (size_t p=0;p < size;p++) h = (h ^ src[p]) * prime;
    return h;
}
EXPORT uint32_t hash_sdbm(const uint8_t *restrict src, const size_t size, const uint32_t init, const uint32_t seed) {
    uint32_t h = init;
    for (size_t p=0;p < size;p++) h = (h + src[p]) * seed;
    return h;
}
EXPORT uint32_t hash_djb2(const uint8_t *restrict src, const size_t size, const uint32_t init) {
    uint32_t h = init;
    for (size_t p=0;p < size;p++) h = (h << 5) + h + src[p];
    return h;
}
EXPORT uint32_t hash_djb2a(const uint8_t *restrict src, const size_t size, const uint32_t init) {
    uint32_t h = init;
    for (size_t p=0;p < size;p++) h = ((h << 5) + h) ^ src[p];
    return h;
}
EXPORT uint32_t hash_joaat(const uint8_t *restrict src, const size_t size, const uint32_t init) {
    uint32_t h = init;
    for (size_t p=0;p < size;p++) {
        h += src[p];
        h += h << 10;
        h ^= h >> 6;
    }

    h += h << 3;
    h ^= h >> 11;
    h += h << 15;
    return h;
}
EXPORT uint32_t hash_tarzan(const uint8_t *restrict src, const size_t size) {
    uint32_t h = 0;
    for (size_t p=0;p < size;p++) h += src[p] << ((p & 3) * 8);
    return h + size;
}
EXPORT uint32_t hash_luas(const uint8_t *restrict src, const size_t size) {
    const size_t stp = (size >> 5) + 1;
    uint32_t h = size;
    for (size_t p=size;p >= stp;p-=stp) h ^= h * 0x20 + (h >> 2) + src[p - 1];
    return h;
}
EXPORT uint16_t hash_bsdsum(const uint8_t *restrict src, const size_t size, const uint16_t init) {
    uint16_t h = init;
    for (size_t p=0;p < size;p++) h = ROT16R(h, 1) + src[p];
    return h;
}
EXPORT uint16_t hash_sysvsum(const uint8_t *restrict src, const size_t size) {
    uint32_t s = SUMB(src, size);
    uint32_t r = (s & 0xFFFF) + (s >> 16);
    return (r & 0xFFFF) + (r >> 16);
}

static inline uint32_t dha256_sigma0(uint32_t x) { return ROT32L(x, 7 ) ^ ROT32L(x, 22) ^ x; }
static inline uint32_t dha256_sigma1(uint32_t x) { return ROT32L(x, 13) ^ ROT32L(x, 27) ^ x; }
static inline void dha256_block(hash256_t *restrict H, const uint32_t buf[16]) {
    PHASH256_ABC(H);
    uint32_t W[0x40];
    for (int i=0;i < 0x10;i++) W[i] = SWAPBE32(buf[i]);
    for (int i=0x10;i < 0x40;i++)
        W[i] = dha256_sigma1(W[i-15]) + W[i-9] + dha256_sigma0(W[i-1]) + W[i-16];
    for (int i=0;i < 0x40;i++) {
        uint32_t t1 = (ROT32L(h, 19) ^ ROT32L(h, 29) ^ h) +
                        (f & g ^ g & h ^ f & h) + e + SHA256_K[i] + W[i];
        uint32_t t2 = (ROT32L(d, 11) ^ ROT32L(d, 25) ^ d) +
                        (~b & d ^ b & c) + a + SHA256_K[i] + W[i];
        a = b;
        b = ROT32L(c, 17);
        c = d;
        d = t1;
        e = f;
        f = ROT32L(g, 2);
        g = h;
        h = t2;
    }

    H->d[0] += a;
    H->d[1] += b;
    H->d[2] += c;
    H->d[3] += d;
    H->d[4] += e;
    H->d[5] += f;
    H->d[6] += g;
    H->d[7] += h;
}
EXPORT hash256_t hash_dha256(const uint8_t *restrict src, const size_t size) {
    hash256_t H;
    memcpy(H.d, SHA256_H0, sizeof(H.d));
    uint32_t tbuf[0x10];

    size_t p = 0;
    for (;p + 0x40 <= size;p+=0x40) {
        memcpy(tbuf, src + p, 0x40);
        dha256_block(&H, tbuf);
    }
    uint8_t buf[0x40] = {0};
    uint8_t c = size - p;
    memcpy(buf, src + p, c);
    md_pad64(buf, c, &H, SWAPBE64(size * 8), dha256_block);
    swapbe32_arr(H.d, 8);
    return H;
}

#define K SHA256_K
static inline uint32_t fork256_F(uint32_t x) { return x + (ROT32L(x, 7 ) ^ ROT32L(x, 22)); }
static inline uint32_t fork256_G(uint32_t x) { return x ^ (ROT32L(x, 13) + ROT32L(x, 27)); }
static inline void fork256_step(uint32_t *restrict W, const uint32_t v1, const uint32_t v2, const uint32_t v3, const uint32_t v4) {
    uint32_t t1 = fork256_G(W[4] + v2);
    uint32_t t2 = fork256_F(W[4] + v2 + v4);
    uint32_t t3 = fork256_F(W[0] + v1);
    uint32_t t4 = fork256_G(W[0] + v1 + v3);

    uint32_t t = (W[7] + ROT32L(t1, 21)) ^ ROT32L(t2, 17);
          W[7] = (W[6] + ROT32L(t1, 9 )) ^ ROT32L(t2, 5 );
          W[6] = (W[5] + t1) ^ t2;
          W[5] =  W[4] + v2 + v4;
          W[4] = (W[3] + ROT32L(t3, 17)) ^ ROT32L(t4, 21);
          W[3] = (W[2] + ROT32L(t3, 5 )) ^ ROT32L(t4, 9 );
          W[2] = (W[1] + t3) ^ t4;
          W[1] =  W[0] + v1 + v3;
          W[0] = t;
}
static inline void fork256_block(hash256_t *restrict H, const uint32_t buf[16]) {
    uint32_t D[0x10];
    for (int i=0;i < 0x10;i++) D[i] = SWAPBE32(buf[i]);
    uint32_t t1[0x10];uint32_t t2[0x10];uint32_t t3[0x10];uint32_t t4[0x10];
    memcpy(t1, H->d, sizeof(t1));memcpy(t2, H->d, sizeof(t2));
    memcpy(t3, H->d, sizeof(t3));memcpy(t4, H->d, sizeof(t4));

    fork256_step(t1, D[0 ], D[1 ], K[0 ], K[1 ]);
    fork256_step(t1, D[2 ], D[3 ], K[2 ], K[3 ]);
    fork256_step(t1, D[4 ], D[5 ], K[4 ], K[5 ]);
    fork256_step(t1, D[6 ], D[7 ], K[6 ], K[7 ]);
    fork256_step(t1, D[8 ], D[9 ], K[8 ], K[9 ]);
    fork256_step(t1, D[10], D[11], K[10], K[11]);
    fork256_step(t1, D[12], D[13], K[12], K[13]);
    fork256_step(t1, D[14], D[15], K[14], K[15]);

    fork256_step(t2, D[14], D[15], K[15], K[14]);
    fork256_step(t2, D[11], D[9 ], K[13], K[12]);
    fork256_step(t2, D[8 ], D[10], K[11], K[10]);
    fork256_step(t2, D[3 ], D[4 ], K[9 ], K[8 ]);
    fork256_step(t2, D[2 ], D[13], K[7 ], K[6 ]);
    fork256_step(t2, D[0 ], D[5 ], K[5 ], K[4 ]);
    fork256_step(t2, D[6 ], D[7 ], K[3 ], K[2 ]);
    fork256_step(t2, D[12], D[1 ], K[1 ], K[0 ]);

    fork256_step(t3, D[7 ], D[6 ], K[1 ], K[0 ]);
    fork256_step(t3, D[10], D[14], K[3 ], K[2 ]);
    fork256_step(t3, D[13], D[2 ], K[5 ], K[4 ]);
    fork256_step(t3, D[9 ], D[12], K[7 ], K[6 ]);
    fork256_step(t3, D[11], D[4 ], K[9 ], K[8 ]);
    fork256_step(t3, D[15], D[8 ], K[11], K[10]);
    fork256_step(t3, D[5 ], D[0 ], K[13], K[12]);
    fork256_step(t3, D[1 ], D[3 ], K[15], K[14]);

    fork256_step(t4, D[5 ], D[12], K[14], K[15]);
    fork256_step(t4, D[1 ], D[8 ], K[12], K[13]);
    fork256_step(t4, D[15], D[0 ], K[10], K[11]);
    fork256_step(t4, D[13], D[11], K[8 ], K[9 ]);
    fork256_step(t4, D[3 ], D[10], K[6 ], K[7 ]);
    fork256_step(t4, D[9 ], D[2 ], K[4 ], K[5 ]);
    fork256_step(t4, D[7 ], D[14], K[2 ], K[3 ]);
    fork256_step(t4, D[4 ], D[6 ], K[0 ], K[1 ]);

    for (int i=0;i < 8;i++)
        H->d[i] += (t1[i] + t2[i]) ^ (t3[i] + t4[i]);
}
EXPORT hash256_t hash_fork256(const uint8_t *restrict src, const size_t size) {
    hash256_t H;
    memcpy(H.d, SHA256_H0, sizeof(H.d));
    uint32_t tbuf[0x10];

    size_t p = 0;
    for (;p + 0x40 <= size;p+=0x40) {
        memcpy(tbuf, src + p, 0x40);
        fork256_block(&H, tbuf);
    }
    uint8_t buf[0x40] = {0};
    uint8_t c = size - p;
    memcpy(buf, src + p, c);
    md_pad64(buf, c, &H, SWAPBE64(size * 8), fork256_block);
    swapbe32_arr(H.d, 8);
    return H;
}
#undef K

static inline void echo_block(uint32_t *restrict V, const int8_t big, uint128_t *restrict C, const uint32_t *restrict buf) {
    uint128_t K;
    uint128_cpy(&K, C);
    uint32_t W[0x40];
    const int Vsize = big ? 0x20 : 0x10;
    memcpy(W, V, sizeof(uint32_t) * Vsize);
    for (int i=0;i < 0x40 - Vsize;i++) W[i + Vsize] = SWAPLE32(buf[i]);

    for (int i=0;i < (big ? 10 : 8);i++) {
        for (int j=0;j < 0x40;j+=4) {
            uint32_t y0 = AES0[(W[j + 0] >> 0 ) & 0xFF] ^ AES1[(W[j + 1] >> 8 ) & 0xFF]
                        ^ AES2[(W[j + 2] >> 16) & 0xFF] ^ AES3[(W[j + 3] >> 24) & 0xFF] ^ uint128_32(&K,0);
            uint32_t y1 = AES0[(W[j + 1] >> 0 ) & 0xFF] ^ AES1[(W[j + 2] >> 8 ) & 0xFF]
                        ^ AES2[(W[j + 3] >> 16) & 0xFF] ^ AES3[(W[j + 0] >> 24) & 0xFF] ^ uint128_32(&K,1);
            uint32_t y2 = AES0[(W[j + 2] >> 0 ) & 0xFF] ^ AES1[(W[j + 3] >> 8 ) & 0xFF]
                        ^ AES2[(W[j + 0] >> 16) & 0xFF] ^ AES3[(W[j + 1] >> 24) & 0xFF] ^ uint128_32(&K,2);
            uint32_t y3 = AES0[(W[j + 3] >> 0 ) & 0xFF] ^ AES1[(W[j + 0] >> 8 ) & 0xFF]
                        ^ AES2[(W[j + 1] >> 16) & 0xFF] ^ AES3[(W[j + 2] >> 24) & 0xFF] ^ uint128_32(&K,3);
            W[j + 0] = AES0[(y0 >> 0 ) & 0xFF] ^ AES1[(y1 >> 8 ) & 0xFF]
                     ^ AES2[(y2 >> 16) & 0xFF] ^ AES3[(y3 >> 24) & 0xFF];
            W[j + 1] = AES0[(y1 >> 0 ) & 0xFF] ^ AES1[(y2 >> 8 ) & 0xFF]
                     ^ AES2[(y3 >> 16) & 0xFF] ^ AES3[(y0 >> 24) & 0xFF];
            W[j + 2] = AES0[(y2 >> 0 ) & 0xFF] ^ AES1[(y3 >> 8 ) & 0xFF]
                     ^ AES2[(y0 >> 16) & 0xFF] ^ AES3[(y1 >> 24) & 0xFF];
            W[j + 3] = AES0[(y3 >> 0 ) & 0xFF] ^ AES1[(y0 >> 8 ) & 0xFF]
                     ^ AES2[(y1 >> 16) & 0xFF] ^ AES3[(y2 >> 24) & 0xFF];
            uint128_add(&K, 1);
        }
        shiftlx_arr32(W, 4, 0x10, 4);
        shiftlx_arr32(W, 5, 0x10, 4);
        shiftlx_arr32(W, 6, 0x10, 4);
        shiftlx_arr32(W, 7, 0x10, 4);
        swap_arr32(W, 0x08, 0x28);swap_arr32(W, 0x18, 0x38);
        swap_arr32(W, 0x09, 0x29);swap_arr32(W, 0x19, 0x39);
        swap_arr32(W, 0x0A, 0x2A);swap_arr32(W, 0x1A, 0x3A);
        swap_arr32(W, 0x0B, 0x2B);swap_arr32(W, 0x1B, 0x3B);
        shiftrx_arr32(W, 0xC, 0x10, 4);
        shiftrx_arr32(W, 0xD, 0x10, 4);
        shiftrx_arr32(W, 0xE, 0x10, 4);
        shiftrx_arr32(W, 0xF, 0x10, 4);
        aes_mix(W, 0,  1,  2,  3);
        aes_mix(W, 4,  5,  6,  7);
        aes_mix(W, 8,  9,  10, 11);
        aes_mix(W, 12, 13, 14, 15);
    }

    if (big) {
        for (int i=0;i < 0x20;i++)
            V[i] ^= SWAPLE32(buf[i]) ^ W[i] ^ W[i + 0x20];
    } else {
        for (int i=0;i < 0x10;i++) {
            V[i] ^= SWAPLE32(buf[i + 0x00]) ^ SWAPLE32(buf[i + 0x10]) ^ SWAPLE32(buf[i + 0x20])
                ^ W[i] ^ W[i + 0x10] ^ W[i + 0x20] ^ W[i + 0x30];
        }
    }
}
EXPORT hash512_t hash_echo(const uint8_t *restrict src, const size_t size, const uint16_t bits) {
    const int8_t big = (bits > 0x100) ? 1 : 0;
    const uint8_t block_size = big ? 0x80 : 0xC0;

    uint32_t tbuf[0x30];
    uint32_t V[0x20] = {0};
    for (int i=0;i < (big ? 8 : 4);i++) V[i*4] = bits;
    uint128_t C = uint128(0, 0);

    size_t p = 0;
    for (;p + block_size <= size;p+=block_size) {
        uint128_add(&C, block_size * 8);
        memcpy(tbuf, src + p, block_size);
        echo_block(V, big, &C, tbuf);
    }

    uint16_t c = size - p;
    uint128_add(&C, c * 8);
    uint8_t buf[0xC0] = {0};
    memcpy(buf, src + p, c);
    buf[c++] = 0x80;
    if (c > block_size - 0x12) {
        memcpy(tbuf, buf, block_size);
        echo_block(V, big, &C, tbuf);
        c = 0;
        for (int i=0;i < block_size - 0x12;i++) buf[i] = 0;
    }
    buf[block_size - 0x12] = bits & 0xFF;
    buf[block_size - 0x11] = bits >> 8;
    memcpy(tbuf, buf, block_size);
    uint64_t tCv = SWAPLE64(C.l);
    memcpy(tbuf + block_size / 4 - 4, &tCv, 8);
    tCv = SWAPLE64(C.h);
    memcpy(tbuf + block_size / 4 - 2, &tCv, 8);
    if (c == 0 || c == 1) C = uint128(0, 0);
    echo_block(V, big, &C, tbuf);

    hash512_t h;
    for (int i=0;i < bits / 32;i++) h.d[i] = SWAPLE32(V[i]);
    return h;
}

static inline uint32_t sparkle_ELL(const uint32_t x) {
    return ROT32R(x ^ (x << 16), 16);
}
static inline void sparkle_opt(uint32_t *restrict W, const uint16_t s, const uint8_t r) {
    for (int i=0;i < r;i++) {
        W[1] ^= SPARKLE_RCON[i & 7];
        W[3] ^= i;

        for (int j=0;j < s*2;j+=2) {
            const uint32_t rc = SPARKLE_RCON[j / 2];
            W[j] += ROT32R(W[j + 1], 31);
            W[j + 1] ^= ROT32R(W[j], 24);
            W[j] ^= rc;

            W[j] += ROT32R(W[j + 1], 17);
            W[j + 1] ^= ROT32R(W[j], 17);
            W[j] ^= rc;

            W[j] += W[j + 1];
            W[j + 1] ^= ROT32R(W[j], 31);
            W[j] ^= rc;

            W[j] += ROT32R(W[j + 1], 24);
            W[j + 1] ^= ROT32R(W[j], 16);
            W[j] ^= rc;
        }

        uint32_t t0 = W[0];uint32_t t1 = W[1];
        uint32_t x0 = t0;uint32_t y0 = t1;
        for (int j=2;j < s;j+=2) {
            t0 ^= W[j];
            t1 ^= W[j + 1];
        }
        t0 = sparkle_ELL(t0);
        t1 = sparkle_ELL(t1);
        for (int j=2;j < s;j+=2) {
            W[j - 2] = W[j + s] ^ W[j] ^ t1;
            W[j + s] = W[j];
            W[j - 1] = W[j + s + 1] ^ W[j + 1] ^ t0;
            W[j + s + 1] = W[j + 1];
        }
        W[s - 2] = W[s] ^ x0 ^ t1;
        W[s] = x0;
        W[s - 1] = W[s + 1] ^ y0 ^ t0;
        W[s + 1] = y0;
    }
}
EXPORT hash512_t hash_esch(const uint8_t *restrict src, const size_t size,
                           const uint16_t digtl, const uint16_t statl, const uint16_t ratel,
                           const uint8_t bigc, const uint8_t slic) {
    const uint16_t state_bs = statl / 64;
    const uint16_t state_ws = statl / 32;
    const uint16_t rate_ws = ratel / 32;
    const uint16_t rate_bs = ratel / 8;
    const uint16_t dig_bs = digtl / 8;

    uint32_t t0,t1;
    size_t il = size;
    size_t ip = 0;
    uint32_t W[0x10] = {0};

    while (il > rate_bs) {
        t0 = 0;t1 = 0;
        for (int i=0;i < rate_ws;i+=2) {
            t0 ^= read32le(src + ip + i * 4);
            t1 ^= read32le(src + ip + i * 4 + 4);
        }
        t0 = sparkle_ELL(t0);
        t1 = sparkle_ELL(t1);
        for (int i=0;i < rate_ws;i+=2) {
            W[i] ^= read32le(src + ip + i * 4) ^ t1;
            W[i + 1] ^= read32le(src + ip + i * 4 + 4) ^ t0;
        }
        for (int i=rate_ws;i < state_bs;i+=2) {
            W[i] ^= t1;
            W[i + 1] ^= t0;
        }
        sparkle_opt(W, state_bs, slic);
        il -= rate_bs;ip += rate_bs;
    }
    W[state_bs - 1] ^= (il < rate_bs) ? 0x1000000 : 0x2000000;
    uint32_t buf[8] = {0};
    memcpy(buf, src + ip, il);
    if (il < rate_bs) buf[il >> 2] |= 0x80U << ((il & 3) * 8);
    t0 = 0;t1 = 0;
    for (int i=0;i < rate_ws;i+=2) {
        t0 ^= buf[i];
        t1 ^= buf[i + 1];
    }
    t0 = sparkle_ELL(t0);
    t1 = sparkle_ELL(t1);
    for (int i=0;i < rate_ws;i+=2) {
        W[i] ^= buf[i] ^ t1;
        W[i + 1] ^= buf[i + 1] ^ t0;
    }
    for (int i=rate_ws;i < state_bs;i+=2) {
        W[i] ^= t1;
        W[i + 1] ^= t0;
    }
    sparkle_opt(W, state_bs, bigc);

    hash512_t ret;
    memcpy(ret.d, W, state_ws * 4);
    uint16_t op = rate_bs;
    while (op < dig_bs) {
        sparkle_opt(W, state_bs, slic);
        uint32_t l = (dig_bs - op) / 4;
        if (l > rate_ws) l = rate_ws;
        memcpy(ret.d + op / 4, W, l * 4);
        op += rate_bs;
    }
    return ret;
}

static inline void fugue_smix(uint32_t *restrict S , const uint32_t i0, const uint32_t i1, const uint32_t i2, const uint32_t i3) {
    #define M0 FUGUE_MIX0
    #define M1 FUGUE_MIX1
    #define M2 FUGUE_MIX2
    #define M3 FUGUE_MIX3
    uint32_t c0,c1,c2,c3,r0,r1,r2,r3,t,xt;

    xt = S[i0];
    c0  = M0[(xt >> 24) & 0xFF];
    t   = M1[(xt >> 16) & 0xFF];
    c0 ^= t;r1 = t;
    t   = M2[(xt >>  8) & 0xFF];
    c0 ^= t;r2 = t;
    t   = M3[(xt >>  0) & 0xFF];
    c0 ^= t;r3 = t;

    xt = S[i1];
    t   = M0[(xt >> 24) & 0xFF];
    c1  = t;r0 = t;
    c1 ^= M1[(xt >> 16) & 0xFF];
    t   = M2[(xt >>  8) & 0xFF];
    c1 ^= t;r2 ^= t;
    t   = M3[(xt >>  0) & 0xFF];
    c1 ^= t;r3 ^= t;

    xt = S[i2];
    t   = M0[(xt >> 24) & 0xFF];
    c2  = t;r0 ^= t;
    t   = M1[(xt >> 16) & 0xFF];
    c2 ^= t;r1 ^= t;
    c2 ^= M2[(xt >>  8) & 0xFF];
    t   = M3[(xt >>  0) & 0xFF];
    c2 ^= t;r3 ^= t;

    xt = S[i3];
    t   = M0[(xt >> 24) & 0xFF];
    c3  = t;r0 ^= t;
    t   = M1[(xt >> 16) & 0xFF];
    c3 ^= t;r1 ^= t;
    t   = M2[(xt >>  8) & 0xFF];
    c3 ^= t;r2 ^= t;
    c3 ^= M3[(xt >>  0) & 0xFF];

    S[i0] = ((c0 ^ (r0 <<  0)) & 0xFF000000)
          | ((c1 ^ (r1 <<  0)) & 0x00FF0000)
          | ((c2 ^ (r2 <<  0)) & 0x0000FF00)
          | ((c3 ^ (r3 <<  0)) & 0x000000FF);
    S[i1] = ((c1 ^ (r0 <<  8)) & 0xFF000000)
          | ((c2 ^ (r1 <<  8)) & 0x00FF0000)
          | ((c3 ^ (r2 <<  8)) & 0x0000FF00)
          | ((c0 ^ (r3 >> 24)) & 0x000000FF);
    S[i2] = ((c2 ^ (r0 << 16)) & 0xFF000000)
          | ((c3 ^ (r1 << 16)) & 0x00FF0000)
          | ((c0 ^ (r2 >> 16)) & 0x0000FF00)
          | ((c1 ^ (r3 >> 16)) & 0x000000FF);
    S[i3] = ((c3 ^ (r0 << 24)) & 0xFF000000)
          | ((c0 ^ (r1 >>  8)) & 0x00FF0000)
          | ((c1 ^ (r2 >>  8)) & 0x0000FF00)
          | ((c2 ^ (r3 >>  8)) & 0x000000FF);

    #undef M0
    #undef M1
    #undef M2
    #undef M3
}
static inline void fugue_cmix(uint32_t *restrict S, const uint32_t size) {
    S[ 0] ^= S[4];
    S[ 1] ^= S[5];
    S[ 2] ^= S[6];
    const uint32_t o = size / 2;
    S[o+0] ^= S[4];
    S[o+1] ^= S[5];
    S[o+2] ^= S[6];
}
#define O(x) ((x) + 30 - o) % 30
static inline void fugue2xx_block(uint32_t *restrict S ,uint32_t *restrict rshift, uint32_t d) {
    const uint32_t o = *rshift * 6;
    S[O(10)] ^= S[O(0 )];
    S[O(0 )] = d;
    S[O(8 )] ^= S[O(0 )];
    S[O(1 )] ^= S[O(24)];
    S[O(27)] ^= S[O(1 )];
    S[O(28)] ^= S[O(2 )];
    S[O(29)] ^= S[O(3 )];
    S[O(12)] ^= S[O(1 )];
    S[O(13)] ^= S[O(2 )];
    S[O(14)] ^= S[O(3 )];
    fugue_smix(S, O(27), O(28), O(29), O(0 ));
    S[O(24)] ^= S[O(28)];
    S[O(25)] ^= S[O(29)];
    S[O(26)] ^= S[O(0 )];
    S[O(9 )] ^= S[O(28)];
    S[O(10)] ^= S[O(29)];
    S[O(11)] ^= S[O(0 )];
    fugue_smix(S, O(24), O(25), O(26), O(27));
    *rshift = (*rshift + 1) % 5;
}
#undef O
#define O(x) ((x) + 36 - o) % 36
static inline void fugue384_block(uint32_t *restrict S ,uint32_t *restrict rshift, uint32_t d) {
    const uint32_t o = *rshift * 9;
    S[O(16)] ^= S[O(0 )];
    S[O(0 )] = d;
    S[O(8 )] ^= S[O(0 )];
    S[O(1 )] ^= S[O(27)];
    S[O(4 )] ^= S[O(30)];
    S[O(33)] ^= S[O(1 )];
    S[O(34)] ^= S[O(2 )];
    S[O(35)] ^= S[O(3 )];
    S[O(15)] ^= S[O(1 )];
    S[O(16)] ^= S[O(2 )];
    S[O(17)] ^= S[O(3 )];
    fugue_smix(S, O(33), O(34), O(35), O(0 ));
    S[O(30)] ^= S[O(34)];
    S[O(31)] ^= S[O(35)];
    S[O(32)] ^= S[O(0 )];
    S[O(12)] ^= S[O(34)];
    S[O(13)] ^= S[O(35)];
    S[O(14)] ^= S[O(0 )];
    fugue_smix(S, O(30), O(31), O(32), O(33));
    S[O(27)] ^= S[O(31)];
    S[O(28)] ^= S[O(32)];
    S[O(29)] ^= S[O(33)];
    S[O(9 )] ^= S[O(31)];
    S[O(10)] ^= S[O(32)];
    S[O(11)] ^= S[O(33)];
    fugue_smix(S, O(27), O(28), O(29), O(30));
    *rshift = (*rshift + 1) % 4;
}
static inline void fugue512_block(uint32_t *restrict S ,uint32_t *restrict rshift, uint32_t d) {
    const uint32_t o = *rshift * 12;
    S[O(22)] ^= S[O(0 )];
    S[O(0 )] = d;
    S[O(8 )] ^= S[O(0 )];
    S[O(1 )] ^= S[O(24)];
    S[O(4 )] ^= S[O(27)];
    S[O(7 )] ^= S[O(30)];
    S[O(33)] ^= S[O(1 )];
    S[O(34)] ^= S[O(2 )];
    S[O(35)] ^= S[O(3 )];
    S[O(15)] ^= S[O(1 )];
    S[O(16)] ^= S[O(2 )];
    S[O(17)] ^= S[O(3 )];
    fugue_smix(S, O(33), O(34), O(35), O(0 ));
    S[O(30)] ^= S[O(34)];
    S[O(31)] ^= S[O(35)];
    S[O(32)] ^= S[O(0 )];
    S[O(12)] ^= S[O(34)];
    S[O(13)] ^= S[O(35)];
    S[O(14)] ^= S[O(0 )];
    fugue_smix(S, O(30), O(31), O(32), O(33));
    S[O(27)] ^= S[O(31)];
    S[O(28)] ^= S[O(32)];
    S[O(29)] ^= S[O(33)];
    S[O(9 )] ^= S[O(31)];
    S[O(10)] ^= S[O(32)];
    S[O(11)] ^= S[O(33)];
    fugue_smix(S, O(27), O(28), O(29), O(30));
    S[O(24)] ^= S[O(28)];
    S[O(25)] ^= S[O(29)];
    S[O(26)] ^= S[O(30)];
    S[O(6 )] ^= S[O(28)];
    S[O(7 )] ^= S[O(29)];
    S[O(8 )] ^= S[O(30)];
    fugue_smix(S, O(24), O(25), O(26), O(27));
    *rshift = (*rshift + 1) % 3;
}
#undef O
EXPORT hash512_t hash_fugue(const uint8_t *restrict src, const size_t size, const uint16_t bits) {
    uint32_t S[0x24] = {0};
    void (*fugue_block)(uint32_t *restrict S, uint32_t *restrict rshift, uint32_t d);
    switch (bits) {
    case 224:
        fugue_block = fugue2xx_block;
        memcpy(S + (30 - 7), FUGUE224_IV, 0x1C);
        break;
    case 256:
        fugue_block = fugue2xx_block;
        memcpy(S + (30 - 8), FUGUE256_IV, 0x20);
        break;
    case 384:
        fugue_block = fugue384_block;
        memcpy(S + (36 - 12), FUGUE384_IV, 0x30);
        break;
    case 512:
        fugue_block = fugue512_block;
        memcpy(S + (36 - 16), FUGUE512_IV, 0x40);
        break;
    }
    uint32_t rshift = 0;

    size_t ip = 0;
    for (;ip + 4 <= size;ip+=4) fugue_block(S, &rshift, read32be(src + ip));
    uint8_t l = size - ip;
    if (l > 0) {
        uint32_t d = 0;
        for (int i=0;i < l;i++) d = (d << 8) + src[ip + i];
        for (int i=l;i < 4;i++) d <<= 8;
        fugue_block(S, &rshift, d);
    }

    uint64_t c = size * 8;
    fugue_block(S, &rshift, c >> 32);
    fugue_block(S, &rshift, c & 0xFFFFFFFF);

    hash512_t h;
    uint32_t St[0x24];
    switch (bits) {
    case 224:
    case 256:
        arr32_swap(S, St, 0x1E, 6 * rshift);
        for (int i=0;i < 10;i++) {
            arr32_swap(S, St, 0x1E, 3);
            fugue_cmix(S, 0x1E);
            fugue_smix(S, 0, 1, 2, 3);
        }
        for (int i=0;i < 13;i++) {
            S[4] ^= S[0];S[15] ^= S[0];
            arr32_swap(S, St, 0x1E, 15);
            fugue_smix(S, 0, 1, 2, 3);
            S[4] ^= S[0];S[16] ^= S[0];
            arr32_swap(S, St, 0x1E, 14);
            fugue_smix(S, 0, 1, 2, 3);
        }
        S[4] ^= S[0];S[15] ^= S[0];
        h.d[0] = SWAPBE32(S[ 1]);
        h.d[1] = SWAPBE32(S[ 2]);
        h.d[2] = SWAPBE32(S[ 3]);
        h.d[3] = SWAPBE32(S[ 4]);
        h.d[4] = SWAPBE32(S[15]);
        h.d[5] = SWAPBE32(S[16]);
        h.d[6] = SWAPBE32(S[17]);
        if (bits >= 256) h.d[7] = SWAPBE32(S[18]);
        break;
    case 384:
        arr32_swap(S, St, 0x24, 9 * rshift);
        for (int i=0;i < 18;i++) {
            arr32_swap(S, St, 0x24, 3);
            fugue_cmix(S, 0x24);
            fugue_smix(S, 0, 1, 2, 3);
        }
        for (int i=0;i < 13;i++) {
            S[ 4] ^= S[0];
            S[12] ^= S[0];
            S[24] ^= S[0];
            arr32_swap(S, St, 0x24, 12);
            fugue_smix(S, 0, 1, 2, 3);
            S[ 4] ^= S[0];
            S[13] ^= S[0];
            S[24] ^= S[0];
            arr32_swap(S, St, 0x24, 12);
            fugue_smix(S, 0, 1, 2, 3);
            S[ 4] ^= S[0];
            S[13] ^= S[0];
            S[25] ^= S[0];
            arr32_swap(S, St, 0x24, 11);
            fugue_smix(S, 0, 1, 2, 3);
        }
        S[ 4] ^= S[0];
        S[12] ^= S[0];
        S[24] ^= S[0];
        h.d[ 0] = SWAPBE32(S[ 1]);
        h.d[ 1] = SWAPBE32(S[ 2]);
        h.d[ 2] = SWAPBE32(S[ 3]);
        h.d[ 3] = SWAPBE32(S[ 4]);
        h.d[ 4] = SWAPBE32(S[12]);
        h.d[ 5] = SWAPBE32(S[13]);
        h.d[ 6] = SWAPBE32(S[14]);
        h.d[ 7] = SWAPBE32(S[15]);
        h.d[ 8] = SWAPBE32(S[24]);
        h.d[ 9] = SWAPBE32(S[25]);
        h.d[10] = SWAPBE32(S[26]);
        h.d[11] = SWAPBE32(S[27]);
        break;
    case 512:
        arr32_swap(S, St, 0x24, 12 * rshift);
        for (int i=0;i < 32;i++) {
            arr32_swap(S, St, 0x24, 3);
            fugue_cmix(S, 0x24);
            fugue_smix(S, 0, 1, 2, 3);
        }
        for (int i=0;i < 13;i++) {
            S[ 4] ^= S[0];S[ 9] ^= S[0];
            S[18] ^= S[0];S[27] ^= S[0];
            arr32_swap(S, St, 0x24, 9);
            fugue_smix(S, 0, 1, 2, 3);
            S[ 4] ^= S[0];S[10] ^= S[0];
            S[18] ^= S[0];S[27] ^= S[0];
            arr32_swap(S, St, 0x24, 9);
            fugue_smix(S, 0, 1, 2, 3);
            S[ 4] ^= S[0];S[10] ^= S[0];
            S[19] ^= S[0];S[27] ^= S[0];
            arr32_swap(S, St, 0x24, 9);
            fugue_smix(S, 0, 1, 2, 3);
            S[ 4] ^= S[0];S[10] ^= S[0];
            S[19] ^= S[0];S[28] ^= S[0];
            arr32_swap(S, St, 0x24, 8);
            fugue_smix(S, 0, 1, 2, 3);
        }
        S[ 4] ^= S[0];S[ 9] ^= S[0];
        S[18] ^= S[0];S[27] ^= S[0];
        h.d[ 0] = SWAPBE32(S[ 1]);
        h.d[ 1] = SWAPBE32(S[ 2]);
        h.d[ 2] = SWAPBE32(S[ 3]);
        h.d[ 3] = SWAPBE32(S[ 4]);
        h.d[ 4] = SWAPBE32(S[ 9]);
        h.d[ 5] = SWAPBE32(S[10]);
        h.d[ 6] = SWAPBE32(S[11]);
        h.d[ 7] = SWAPBE32(S[12]);
        h.d[ 8] = SWAPBE32(S[18]);
        h.d[ 9] = SWAPBE32(S[19]);
        h.d[10] = SWAPBE32(S[20]);
        h.d[11] = SWAPBE32(S[21]);
        h.d[12] = SWAPBE32(S[27]);
        h.d[13] = SWAPBE32(S[28]);
        h.d[14] = SWAPBE32(S[29]);
        h.d[15] = SWAPBE32(S[30]);
        break;
    }

    return h;
}

static inline has160_block(hash160_t *restrict H, const uint32_t buf[16]) {
    PHASH160_ABC(H);
    uint32_t t;
    uint32_t W[0x14];
    for (int i=0;i < 0x10;i++) W[i] = SWAPLE32(buf[i]);

    W[16] = W[0 ] ^ W[1 ] ^ W[2 ] ^ W[3 ];
    W[17] = W[4 ] ^ W[5 ] ^ W[6 ] ^ W[7 ];
    W[18] = W[8 ] ^ W[9 ] ^ W[10] ^ W[11];
    W[19] = W[12] ^ W[13] ^ W[14] ^ W[15];
    for (int i=0;i < 20;i++) {
        t = ROT32L(a, HAS160_ROT[i]) + ((b & c) | (~b & d)) + e + W[HAS160_NDX[i]];
        e = d;d = c;
        c = ROT32L(b, 10);
        b = a;a = t;
    }

    W[16] = W[3 ] ^ W[6 ] ^ W[9 ] ^ W[12];
    W[17] = W[2 ] ^ W[5 ] ^ W[8 ] ^ W[15];
    W[18] = W[1 ] ^ W[4 ] ^ W[11] ^ W[14];
    W[19] = W[0 ] ^ W[7 ] ^ W[10] ^ W[13];
    for (int i=0;i < 20;i++) {
        t = ROT32L(a, HAS160_ROT[i]) + (b ^ c ^ d) + e + W[HAS160_NDX[i + 20]] + SHA1_K[0];
        e = d;d = c;
        c = ROT32L(b, 17);
        b = a;a = t;
    }

    W[16] = W[5 ] ^ W[7 ] ^ W[12] ^ W[14];
    W[17] = W[0 ] ^ W[2 ] ^ W[9 ] ^ W[11];
    W[18] = W[4 ] ^ W[6 ] ^ W[13] ^ W[15];
    W[19] = W[1 ] ^ W[3 ] ^ W[8 ] ^ W[10];
    for (int i=0;i < 20;i++) {
        t = ROT32L(a, HAS160_ROT[i]) + (c ^ (b | ~d)) + e + W[HAS160_NDX[i + 40]] + SHA1_K[1];
        e = d;d = c;
        c = ROT32L(b, 25);
        b = a;a = t;
    }

    W[16] = W[2 ] ^ W[7 ] ^ W[8 ] ^ W[13];
    W[17] = W[3 ] ^ W[4 ] ^ W[9 ] ^ W[14];
    W[18] = W[0 ] ^ W[5 ] ^ W[10] ^ W[15];
    W[19] = W[1 ] ^ W[6 ] ^ W[11] ^ W[12];
    for (int i=0;i < 20;i++) {
        t = ROT32L(a, HAS160_ROT[i]) + (b ^ c ^ d) + e + W[HAS160_NDX[i + 60]] + SHA1_K[2];
        e = d;d = c;
        c = ROT32L(b, 30);
        b = a;a = t;
    }

    H->d[0] += a;
    H->d[1] += b;
    H->d[2] += c;
    H->d[3] += d;
    H->d[4] += e;
}
EXPORT hash160_t hash_has160(const uint8_t *restrict src, const size_t size) {
    hash160_t H;
    memcpy(H.d, SHA1_H0, 0x14);
    uint32_t tbuf[0x10];

    size_t p = 0;
    for (;p + 0x40 <= size;p+=0x40) {
        memcpy(tbuf, src + p, 0x40);
        has160_block(&H, tbuf);
    }

    uint32_t c = size - p;
    uint8_t buf[0x40] = {0};
    memcpy(buf, src + p, c);
    md_pad64(buf, c, &H, SWAPLE64(size * 8), has160_block);
    swaple32_arr(H.d, 5);
    return H;
}

// Not working! https://github.com/jonelo/jacksum/blob/6106715ee964047eb88dc322ed0bd7abd4c6f1b7/src/main/java/net/jacksum/zzadopt/gnu/crypto/hash/Haval.java
static inline uint32_t haval_ff(uint32_t a[8], const uint32_t w, const uint32_t c, const uint32_t r, const uint32_t y) {
    uint32_t x[7];
    uint32_t of;
    if (y < 3) of = y * 3 + r - 3;
    else if (y == 3) of = 9 + r - 4;
    else if (y == 4) of = 11 + r - 5;

    arr32_map8(a + 1, x, 7, HAVAL_PHI + of*7);
    #define X(i) x[6 - (i)]

    uint32_t t;
    switch (y) {
    case 0: t = X(1) & (X(0) ^  X(4)) ^ X(2) &  X(5)  ^ X(3) & X(6)  ^ X(0);break;
    case 1: t = X(2) & (X(1) & ~X(3)  ^ X(4) &  X(5)  ^ X(6) ^ X(0)) ^ X(4)  & (X(1) ^  X(5)) ^ X(3) & X(5) ^ X(0);break;
    case 2: t = X(3) & (X(1) &  X(2)  ^ X(6) ^  X(0)) ^ X(1) & X(4)  ^ X(2)  &  X(5) ^  X(0);break;
    case 3: t = X(4) & (X(5) & ~X(2)  ^ X(3) & ~X(6)  ^ X(1) ^ X(6)  ^ X(0)) ^  X(3) & (X(1)  & X(2) ^ X(5) ^ X(6)) ^ X(2) & X(6) ^ X(0);break;
    case 4: t = X(0) & (X(1) &  X(2)  & X(3) ^ ~X(5)) ^ X(1) & X(4)  ^ X(2)  &  X(5) ^  X(3)  & X(6);break;
    }
    #undef X

    return ROT32R(t, 7) + ROT32R(a[0],11) + w + c;
}
static inline void haval_block(hash256_t *restrict H, const uint32_t buf[32], const uint8_t rounds) {
    uint32_t X[0x20];
    for (int i=0;i < 0x20;i++) X[i] = SWAPLE32(buf[i]);
    uint32_t t[8];
    memcpy(t, H->d, 0x20);

    if (rounds > 0) {
        #define T(i) t[7 - ((i) % 8)]
        for (int ix=0;ix < 32;ix++) {
            uint32_t tarr[8] = {T(ix + 0), T(ix + 1), T(ix + 2), T(ix + 3),
                                T(ix + 4), T(ix + 5), T(ix + 6), T(ix + 7)};
            T(ix) = haval_ff(tarr, X[ix], 0, rounds, 0);
        }
        for (int ri=0;ri < rounds - 1;ri++) {
            for (int ix=0;ix < 32;ix++) {
                uint32_t tarr[8] = {T(ix + 0), T(ix + 1), T(ix + 2), T(ix + 3),
                                    T(ix + 4), T(ix + 5), T(ix + 6), T(ix + 7)};
                T(ix) = haval_ff(tarr, X[HAVAL_XI[ix + 0x20 * ri]], HAVAL_C[ix + 0x20 * ri], rounds, ri + 1);
            }
        }
        #undef T
    }

    H->d[0] += t[0];
    H->d[1] += t[1];
    H->d[2] += t[2];
    H->d[3] += t[3];
    H->d[4] += t[4];
    H->d[5] += t[5];
    H->d[6] += t[6];
    H->d[7] += t[7];
}
EXPORT hash256_t hash_haval(const uint8_t *restrict src, const size_t size,
                            const uint16_t bits, const uint8_t rounds, const uint8_t version) {
    hash256_t H;
    memcpy(H.d, HAVAL_H0, 0x20);
    uint32_t tbuf[0x20];
    size_t p = 0;
    for (;p + 0x80 <= size;p+=0x80) {
        memcpy(tbuf, src + p, 0x80);
        haval_block(&H, tbuf, rounds);
    }

    uint8_t buf[0x80] = {0};
    uint8_t c = size - p;
    memcpy(buf, src + p, c);
    buf[c++] = 1;
    if (c > 0x76) c = 0;
    if (c == 0) {
        memcpy(tbuf, buf, 0x80);
        haval_block(&H, tbuf, rounds);
    }
    for (int i=c;i < 0x76;i++) buf[i] = 0;
    c = 0x76;
    buf[c++] = ((bits & 3) << 6) | ((rounds & 7) << 3) | (version & 7);
    buf[c++] = bits >> 2;
    memcpy(tbuf, buf, 0x80);
    const uint64_t bil = SWAPLE64((uint64_t)size * 8);
    memcpy(tbuf + 0x1E, &bil, 8);
    haval_block(&H, tbuf, rounds);

    uint32_t t;
    switch (bits) {
    case 128:
        t = (H.d[7] & 0x000000FF) | (H.d[6] & 0xFF000000) | (H.d[5] & 0x00FF0000) | (H.d[4] & 0x0000FF00);
        H.d[0] += ROT32R(t, 8);
        t = (H.d[7] & 0x0000FF00) | (H.d[6] & 0x000000FF) | (H.d[5] & 0xFF000000) | (H.d[4] & 0x00FF0000);
        H.d[1] += ROT32R(t, 16);
        t = (H.d[7] & 0x00FF0000) | (H.d[6] & 0x0000FF00) | (H.d[5] & 0x000000FF) | (H.d[4] & 0xFF000000);
        H.d[2] += ROT32R(t, 16);
        t = (H.d[7] & 0xFF000000) | (H.d[6] & 0x00FF0000) | (H.d[5] & 0x0000FF00) | (H.d[4] & 0x000000FF);
        H.d[3] += ROT32R(t, 8);
        break;
    case 160:
        t = (H.d[7] & 0x0000003F) | (H.d[6] & 0xFE000000) | (H.d[5] & 0x01F80000);
        H.d[0] += ROT32R(t, 19);
        t = (H.d[7] & 0x00000FC0) | (H.d[6] & 0x0000003F) | (H.d[5] & 0xFE000000);
        H.d[1] += ROT32R(t, 25);
        t = (H.d[7] & 0x0007F000) | (H.d[6] & 0x00000FC0) | (H.d[5] & 0x0000003F);
        H.d[2] += t;
        t = (H.d[7] & 0x01F80000) | (H.d[6] & 0x0007F000) | (H.d[5] & 0x00000FC0);
        H.d[3] += t >> 6;
        t = (H.d[7] & 0xFE000000) | (H.d[6] & 0x01F80000) | (H.d[5] & 0x0007F000);
        H.d[4] += t >> 12;
        break;
    case 192:
        t = (H.d[7] & 0x0000001F) | (H.d[6] & 0xBC000000);
        H.d[0] += ROT32R(t, 26);
        t = (H.d[7] & 0x000003E0) | (H.d[6] & 0x0000001F);
        H.d[1] += t;
        t = (H.d[7] & 0x0000FC00) | (H.d[6] & 0x000003E0);
        H.d[2] += t >> 5;
        t = (H.d[7] & 0x001F0000) | (H.d[6] & 0x0000FC00);
        H.d[3] += t >> 10;
        t = (H.d[7] & 0x03E00000) | (H.d[6] & 0x001F0000);
        H.d[4] += t >> 16;
        t = (H.d[7] & 0xFC000000) | (H.d[6] & 0x03E00000);
        H.d[5] += t >> 21;
        break;
    case 224:
        H.d[0] += (H.d[7] >> 27) & 0x1F;
        H.d[1] += (H.d[7] >> 22) & 0x1F;
        H.d[2] += (H.d[7] >> 18) & 0x0F;
        H.d[3] += (H.d[7] >> 13) & 0x1F;
        H.d[4] += (H.d[7] >> 9 ) & 0x0F;
        H.d[5] += (H.d[7] >> 4 ) & 0x1F;
        H.d[6] += H.d[7] & 0x0F;
        break;
    }

    for (int i=0;i < bits / 32;i++) H.d[i] = SWAPLE32(H.d[i]);
    return H;
}

#ifdef __cplusplus
}
#endif
