#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>

#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_MSC_VER) && defined(_WIN64)
    typedef long long ssize_t;
#elif defined(_MSC_VER) && defined(_WIN32)
    typedef long ssize_t;
#elif defined(INTPTR_MAX)
    typedef intptr_t ssize_t;
#else
    typedef long ssize_t;
#endif

typedef struct {
    uint64_t l;
    uint64_t h;
} uint128_t;
static inline uint128_t uint128(uint64_t l, uint64_t h) { return (uint128_t){l, h}; }
static inline void uint128_cpy(uint128_t *restrict a, uint128_t *restrict b) { a->l = b->l; a->h = b->h; }
static inline void uint128_add(uint128_t *restrict a, uint64_t b) {
    a->l += b;
    if (a->l < b) a->h++;
}
static inline uint32_t uint128_32(uint128_t *restrict a, const uint8_t i) {
    if (i == 3) return a->h >> 32;
    if (i == 2) return a->h & 0xFFFFFFFF;
    if (i == 1) return a->l >> 32;
    return a->l & 0xFFFFFFFF;
}

#define CONCAT(a,b) a##b
#define CONCATX(a,b) CONCAT(a,b)
#define D_PRAGMA(x) _Pragma(#x)

// see build.py
#define XEXPORT EXPORT
#define XIMPORT(...)

#if defined(__GNUC__) || defined(__clang__)
    #define SWAP32(x) __builtin_bswap32(x)
    #define SWAP64(x) __builtin_bswap64(x)
#elif defined(_MSC_VER)
    unsigned long __cdecl _byteswap_ulong(unsigned long);
    #pragma intrinsic(_byteswap_ulong)
    #define SWAP32(x) _byteswap_ulong(x)
    unsigned long long __cdecl _byteswap_uint64(unsigned long long);
    #pragma intrinsic(_byteswap_uint64)
    #define SWAP64(x) _byteswap_uint64(x)
#else
    static inline uint32_t SWAP32(uint32_t x) {
        return ((x & 0xFF) << 24 | (x & 0xFF00) << 8 | (x & 0xFF0000) >> 8 | (x & 0xFF000000) >> 24);
    }
    static inline uint64_t SWAP64(uint64_t x) {
        return ((x & 0xFF) << 56 | (x & 0xFF00) << 40 | (x & 0xFF0000) << 24 | (x & 0xFF000000) << 8 |
                (x & 0xFF00000000) >> 8 | (x & 0xFF0000000000) >> 24 | (x & 0xFF000000000000) >> 40 | (x & 0xFF00000000000000) >> 56);
    }
#endif
static inline uint16_t SWAP16(uint16_t x) {
    return ((uint16_t)x << 8) | (x >> 8);
}
static inline uint8_t SWAP8(uint8_t x) {
    return ((uint8_t)x << 4) | (x >> 4);
}
#define SWAPLE32(x) x
#define SWAPLE64(x) x
#define SWAPBE32(x) SWAP32(x)
#define SWAPBE64(x) SWAP64(x)

#define MASK(w) ((w == 64) ? ~0ULL : (1ULL << w) - 1)

static inline uint64_t ROTATER(uint64_t x, const uint8_t w, const uint8_t r) {
    return (x >> r) | (x << (w - r));
}
static inline uint64_t ROTATEL(uint64_t x, const uint8_t w, const uint8_t r) {
    return (x << r) | (x >> (w - r));
}
static inline uint8_t  ROT8R (uint8_t  x, const uint8_t r) { return ROTATER(x, 8,  r); }
static inline uint8_t  ROT8L (uint8_t  x, const uint8_t r) { return ROTATEL(x, 8,  r); }
static inline uint16_t ROT16R(uint16_t x, const uint8_t r) { return ROTATER(x, 16, r); }
static inline uint16_t ROT16L(uint16_t x, const uint8_t r) { return ROTATEL(x, 16, r); }
static inline uint32_t ROT32R(uint32_t x, const uint8_t r) { return ROTATER(x, 32, r); }
static inline uint32_t ROT32L(uint32_t x, const uint8_t r) { return ROTATEL(x, 32, r); }

static inline uint64_t ADDW(uint64_t x, const uint64_t a, const uint8_t w) {
    return (x + a) & ((1 << w) - 1);
}
static inline uint64_t INCW(uint64_t x, const uint8_t w) { return ADDW(x, 1, w); }
#define INCWi(X,w) X = INCW(X, w)
#define ADDWi(X,a,w) X = ADDW(X, a, w)

static inline uint64_t REFLECT(uint64_t x, const size_t n) {
    uint64_t r = 0;
    for (size_t i=0;i < n;i++) {
        r = (r << 1) | (x & 1);
        x >>= 1;
    }
    return r;
}
static inline uint8_t REF8(uint8_t x) { return REFLECT(x, 8); }
static inline uint16_t REF16(uint16_t x) { return REFLECT(x, 16); }
static inline uint32_t REF32(uint32_t x) { return REFLECT(x, 32); }
static inline uint64_t REF64(uint64_t x) { return REFLECT(x, 64); }

static inline uint32_t HIMUL64(uint32_t a, uint32_t b) {
    return ((uint64_t)a) * ((uint64_t)b) >> 32;
}
static inline void DBLGF(uint8_t *src, uint8_t *dst) {
    uint8_t a = 0;
    if (src[0] & 0x80) a = 0x87;
    dst[15] = a ^ (src[15] << 1);
    for (int i=14;i >= 0;i--)
        dst[i] = (src[i + 1] >> 7) | (src[i] << 1);
}

static inline uint64_t SUMB(const uint8_t *restrict src, const size_t size) {
    uint64_t sum = 0;
    for (size_t i=0;i < size;i++) sum += src[i];
    return sum;
}

static inline uint16_t read16le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8);
}
static inline uint16_t read16be(const uint8_t *restrict ptr) {
    return ptr[1] | (ptr[0] << 8);
}
static inline uint32_t read24le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8) | (ptr[2] << 16);
}
static inline uint32_t read24be(const uint8_t *restrict ptr) {
    return ptr[2] | (ptr[1] << 8) | (ptr[0] << 16);
}
static inline uint32_t read32le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8) | (ptr[2] << 16) | ((uint32_t)ptr[3] << 24);
}
static inline uint32_t read32be(const uint8_t *restrict ptr) {
    return ptr[3] | (ptr[2] << 8) | (ptr[1] << 16) | ((uint32_t)ptr[0] << 24);
}
static inline uint64_t read64le(const uint8_t *restrict ptr) {
    return ptr[0] | (ptr[1] << 8) | (ptr[2] << 16) | ((uint64_t)ptr[3] << 24) | ((uint64_t)ptr[4] << 32) | ((uint64_t)ptr[5] << 40) | ((uint64_t)ptr[6] << 48) | ((uint64_t)ptr[7] << 56);
}
static inline uint64_t read64be(const uint8_t *restrict ptr) {
    return ptr[7] | (ptr[6] << 8) | (ptr[5] << 16) | ((uint64_t)ptr[4] << 24) | ((uint64_t)ptr[3] << 32) | ((uint64_t)ptr[2] << 40) | ((uint64_t)ptr[1] << 48) | ((uint64_t)ptr[0] << 56);
}

typedef struct {
    const uint8_t* ptr;
    const uint8_t* end;
    uint8_t buf;
    uint8_t bits;
} BitReader;
static inline void init_BitReader(BitReader *br, const uint8_t *ptr, const size_t size) {
    br->ptr = ptr;
    br->end = ptr + size;
    br->buf = 0;
    br->bits = 0;
}
static inline uint8_t get_bit(BitReader *br) {
    if (!br->bits) {
        if (br->ptr >= br->end) return 0;
        br->buf = *(br->ptr++);
        br->bits = 8;
    }
    br->bits--;
    return (br->buf >> br->bits) & 1;
}
static inline uint64_t get_bits(BitReader *br, size_t n) {
    uint64_t v = 0;
    while (n > 0) {
        if (!br->bits) {
            if (br->ptr >= br->end) return v << n;
            br->buf = *(br->ptr++);
            br->bits = 8;
        }

        int s = (n < br->bits) ? n : br->bits;
        v = (v << s) | ((br->buf >> (br->bits - s)) & ((1 << s) - 1));
        br->bits -= s;
        n -= s;
    }
    return v;
}
static inline uint64_t get_bits_l(BitReader *br, size_t n) {
    uint64_t v = 0;
    size_t p = 0;
    while (n > 0) {
        if (!br->bits) {
            if (br->ptr >= br->end) return v;
            br->buf = *(br->ptr++);
            br->bits = 8;
        }

        int s = (n < br->bits) ? n : br->bits;
        v |= (br->buf & ((1 << s) - 1)) << p;
        br->bits -= s;
        br->buf >>= s;
        n -= s;
        p += s;
    }
    return v;
}
static inline int is_eof(BitReader *br) {
    return br->ptr >= br->end && !br->bits;
}
static inline int is_eofn(BitReader *br, size_t n) {
    return (br->end - br->ptr) + br->bits < n;
}

#ifdef __cplusplus
}
#endif
