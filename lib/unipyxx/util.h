#include <stdint.h>
#include <stdlib.h>

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

#define CONCAT(a,b) a##b
#define CONCATX(a,b) CONCAT(a,b)
#define D_PRAGMA(x) _Pragma(#x)

// see build.py
#define XEXPORT EXPORT
#define XIMPORT(...)

#if defined(__GNUC__) || defined(__clang__)
    #define SWAP32(x) __builtin_bswap32(x)
#elif defined(_MSC_VER)
    unsigned long __cdecl _byteswap_ulong(unsigned long);
    #pragma intrinsic(_byteswap_ulong)
    #define SWAP32(x) _byteswap_ulong(x)
#else
    static inline uint32_t SWAP32(uint32_t x) {
        return ((x & 0xFF) << 24 | (x & 0xFF00) << 8 | (x & 0xFF0000) >> 8 | (x & 0xFF000000) >> 24);
    }
#endif
static inline uint8_t SWAP8(uint8_t x) {
    return ((uint8_t)x << 4) | (x >> 4);
}
static inline uint8_t ROT8R(uint8_t x) {
    return (x >> 1) | (x << 7);
}
static inline uint8_t ROT8L(uint8_t x) {
    return (x << 1) | (x >> 7);
}
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
static inline uint32_t get_bits(BitReader *br, size_t n) {
    uint32_t v = 0;
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
static inline uint32_t get_bits_l(BitReader *br, size_t n) {
    uint32_t v = 0;
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

#ifdef __cplusplus
}
#endif
