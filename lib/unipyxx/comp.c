#include "util.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int16_t l;
    int16_t r; // -1 = leaf
} HuffNode;
static inline int read_hufftree(BitReader *br, int width, int max, HuffNode *tree) {
    int root = 0;
    int nodec = 1;
    int16_t stack[0x800];
    int stacki = 0;

    while (1) {
        if (get_bit(br)) {
            if (nodec + 1 >= max * 2) return 0;
            tree[root].l = nodec;
            tree[root].r = nodec + 1;
            stack[stacki++] = nodec + 1;
            root = nodec;
            nodec += 2;
        } else {
            tree[root].l = get_bits(br, width);
            tree[root].r = -1;
            if (!stacki) break;
            root = stack[--stacki];
        }
    }
    return 1;
}
static inline int get_huffcode(BitReader *br, HuffNode *tree) {
    int node = 0;
    while (tree[node].r != -1) {
        node = (get_bit(br)) ? tree[node].r : tree[node].l;
    }
    return tree[node].l;
}

EXPORT ssize_t decompress_lz10_raw(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        if (fbl <= 0) {
            f = src[ip++];
            CHKi(0);
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];
            uint16_t dist = (((b1 & 0x0F) << 8) | b2) + 1;
            uint8_t lng = (b1 >> 4) + 3;
            if (dist < lng && dist != 0) lng = dist;
            if (op + lng > usize) lng = usize - op;
            for (int i=0;i < lng;i++,op++) {
                CHKi(0);CHKo(0);
                dst[op] = dst[(op - dist) & 0xFFF];
            }
        } else {
            CHKo(0);
            dst[op++] = src[ip++];
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lz11_raw(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        if (fbl <= 0) {
            f = src[ip++];
            CHKi(0);
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];
            size_t dist,lng;

            if ((b1 >> 4) == 0) {
                CHKi(0);
                uint8_t b3 = src[ip++];
                dist = ((b2 & 0x0F) << 8) | b3;
                lng = (((b1 & 0x0F) << 4) | (b2 >> 4)) + 0x10;
            } else if ((b1 >> 4) == 1) {
                CHKi(1);
                uint8_t b3 = src[ip++];
                uint8_t b4 = src[ip++];
                dist = ((b3 & 0x0F) << 8) | b4;
                lng = (((b1 & 0x0F) << 12) | (b2 << 4) | (b3 >> 4)) + 0x110;
            } else {
                dist = ((b1 & 0x0F) << 8) | b2;
                lng = b1 >> 4;
            }
            dist += 1;
            lng += 1;
            if (dist > op) break;
            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = dst[op - dist];
            }
        } else {
            CHKo(0);
            dst[op++] = src[ip++];
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lz40_raw(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        if (fbl <= 0) {
            f = src[ip++];
            CHKi(0);
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];
            size_t dist,lng;

            if ((b1 >> 4) == 0) {
                CHKi(0);
                uint8_t b3 = src[ip++];
                dist = ((b2 & 0x0F) << 8) | b3;
                lng = (((b1 & 0x0F) << 4) | (b2 >> 4)) + 0x10;
            } else if ((b1 >> 4) == 1) {
                CHKi(1);
                uint8_t b3 = src[ip++];
                uint8_t b4 = src[ip++];
                dist = ((b3 & 0x0F) << 8) | b4;
                lng = (((b1 & 0x0F) << 12) | (b2 << 4) | (b3 >> 4)) + 0x110;
            } else {
                dist = ((b1 & 0x0F) << 8) | b2;
                lng = b1 >> 4;
            }
            if (dist > op) break;
            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = dst[op - dist];
            }
        } else {
            CHKo(0);
            dst[op++] = src[ip++];
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_blz_raw(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const ssize_t usize) {
    ssize_t ip = zsize;
    ssize_t op = usize;
    uint8_t f = 0;
    int fbl = 0;

    #define CHKi(n) if (ip - (n) <= 0) goto eof;
    #define CHKo(n) if (op - (n) <= 0) goto eof;

    while (ip > 0 && op > 0) {
        if (fbl <= 0) {
            CHKi(0)
            f = src[--ip];
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1)
            uint8_t b1 = src[--ip];
            uint8_t b2 = src[--ip];
            uint16_t dist = (((b2 & 0x0F) << 8) | b1) + 3;
            uint8_t lng = (b2 >> 4) + 3;
            for (int i=0;i < lng;i++,op--) {
                CHKi(0);CHKo(0)
                dst[op - 1] = dst[op - 1 + dist];
            }
        } else {
            CHKi(0)
            dst[--op] = src[--ip];
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lz4_fast(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        uint8_t tok = src[ip++];
        size_t lits = tok >> 4;

        if (tok == 0x0F) {
            while (ip < zsize) {
                uint8_t b = src[ip++];
                lits += b;
                if (b != 0xFF) break;
            }
        }

        for (int i=0;i < lits;i++) {
            CHKi(0);CHKo(0);
            dst[op++] = src[ip++];
        }

        CHKi(1);
        uint16_t off = src[ip] | (src[ip + 1] << 8);ip += 2;
        size_t len = (tok & 0x0F) + 4;
        if (len == 0x13) {
            while (ip < zsize) {
                uint8_t b = src[ip++];
                len += b;
                if (b != 0xFF) break;
            }
        }

        for (int i=0;i < len;i++,op++) {
            CHKo(0);
            dst[op] = dst[op - off];
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lzss0_lsb(const uint8_t *restrict src, const size_t zsize,
                                          uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int8_t fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        if (fbl <= 0) {
            CHKi(0);
            f = src[ip++];
            fbl = 8;
        }

        if (f & 1) {
            CHKi(0);CHKo(0);
            dst[op++] = src[ip++];
        } else {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];

            uint16_t dist = (op - 18 - (((b2 & 0xF0) << 4) | b1)) & 0xFFF;
            if (!dist) dist = 0x1000;
            uint8_t lng = (b2 & 0x0F) + 3;

            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = (op < dist) ? 0 : dst[op - dist];
            }
        }

        f >>= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_lzss0_msb(const uint8_t *restrict src, const size_t zsize,
                                          uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    uint8_t f = 0;
    int8_t fbl = 0;

    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        if (fbl <= 0) {
            CHKi(0);
            f = src[ip++];
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(0);CHKo(0);
            dst[op++] = src[ip++];
        } else {
            CHKi(1);
            uint8_t b1 = src[ip++];
            uint8_t b2 = src[ip++];

            uint8_t lng = (b1 & 0x0F) + 3;
            uint16_t dist = (op - 18 - (((b1 & 0xF0) << 4) | b2)) & 0xFFF;
            if (!dist) dist = 0x1000;

            for (int i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = (op < dist) ? 0 : dst[op - dist];
            }
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_rtl_lz(const uint8_t *restrict src, const size_t zsize,
                                       uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        uint16_t b = src[ip++];

        if (0x20 > b) {
            if (b == 0) {
                CHKi(0);
                b = src[ip++];
                if (b == 0) {
                    CHKi(1);
                    uint16_t s = read16le(src+ip);ip += 2;
                    if (s == 0) break;
                    for (int i=0;i < s;i++) {
                        CHKi(0);CHKo(0);
                        dst[op++] = src[ip++];
                    }
                } else {
                    b += 0x1F;
                    for (int i=0;i < b;i++) {
                        CHKi(0);CHKo(0);
                        dst[op++] = src[ip++];
                    }
                }
            } else {
                for (int i=0;i < b;i++) {
                    CHKi(0);CHKo(0);
                    dst[op++] = src[ip++];
                }
            }
        } else if (0x40 > b) {
            uint16_t c = b - 0x20;
            if (c == 0) {
                CHKi(0);
                c = src[ip++] + 0x20;
            }
            for (int i=0;i < c;i++) {
                CHKo(0);
                dst[op++] = 0;
            }
        } else if (0x80 > b) {
            if ((b & 0x0F) == 0) {
                CHKi(3);
                uint16_t l = read16le(src+ip);ip += 2;
                uint16_t o = read16le(src+ip);ip += 2;
                if (o != 0) o -= 1;
                if (o > op) o = 0;
                if (o + l > op) {
                    if (l > op) {
                        o = 0;
                        l = op;
                    } else o = op - l;
                }
                while (b & 0x30) {
                    CHKi(0);CHKo(0);
                    dst[op++] = src[ip++];
                    b -= 0x10;
                }
                for (int i=0;i < l;i++,op++) {
                    CHKo(0);
                    dst[op] = dst[op - o - l];
                }
            } else {
                CHKi(1);
                uint8_t l = (b & 0x0F) + 2;
                uint16_t o = read16le(src+ip);ip += 2;
                if (o != 0) o -= 1;
                if (o > op) o = 0;
                if (o + l > op) {
                    if (l > op) {
                        o = 0;
                        l = op;
                    } else o = op - l;
                }
                while (b & 0x30) {
                    CHKi(0);CHKo(0);
                    dst[op++] = src[ip++];
                    b -= 0x10;
                }
                for (int i=0;i < l;i++,op++) {
                    CHKo(0);
                    dst[op] = dst[op - o - l];
                }
            }
        } else {
            if (b & 0x40) {
                CHKi(1);CHKo(1);
                dst[op++] = src[ip++];
                dst[op++] = src[ip++];
            }
            CHKo(1);
            uint8_t o = (b & 0x3F)*2 + 2;
            if (o > op) o = op;
            dst[op] = dst[op - o];op++;
            dst[op] = dst[op - o];op++;
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_vicious_lz(const uint8_t *restrict src, const size_t zsize,
                                           uint8_t *restrict dst, const ssize_t usize) {
    size_t ip = 0;
    ssize_t op = 0;
    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (usize == -1 || op < usize) {
        CHKi(0);
        uint8_t b = src[ip++];

        if (b & 0x80) {
            CHKi(0);
            uint8_t b2 = src[ip++];
            uint8_t lng = (b2 & 0x0F) + 2;
            uint16_t dist = (((b << 4) | (b2 >> 4)) ^ 0xFFF) + 2;
            for (uint8_t i=0;i < lng;i++,op++) {
                CHKo(0);
                dst[op] = (op < dist) ? 0 : dst[op - dist];
            }
        } else if (b & 0x40) {
            CHKi(0);
            uint8_t c = (b & 0x3F) + 2;
            uint8_t cb = src[ip++];
            for (uint8_t i=0;i < c;i++) {
                CHKo(0);
                dst[op++] = cb;
            }
        } else {
            uint8_t c = (b & 0x3F) + 1;
            for (uint8_t i=0;i < c;i++) {
                CHKi(0);CHKo(0);
                dst[op++] = src[ip++];
            }
        }
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}
EXPORT ssize_t decompress_huffman(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const ssize_t usize, const int8_t padding) {
    BitReader br;
    init_BitReader(&br, src, zsize);
    HuffNode tree[512];
    if (!read_hufftree(&br, 8, 256, tree)) return -1;

    if (padding) br.bits = 0;

    ssize_t op = 0;
    while (usize == -1 || op < usize) {
        if (br.bits == 0 && br.ptr >= br.end) break;
        dst[op++] = (uint8_t)get_huffcode(&br, tree);
    }

    return op;
}
EXPORT ssize_t decompress_ash0(const uint8_t *restrict src, const size_t zsize,
                                     uint8_t *restrict dst) {
    if (12 >= zsize) return -1;

    uint32_t usize = read24be(src+5);
    uint32_t symo = read32be(src+8);
    if (symo >= zsize) return -1;

    BitReader symr,distr;
    init_BitReader(&symr, src + 12, symo - 12);
    init_BitReader(&distr, src + symo, zsize - symo);

    HuffNode sym_tree[0x400];
    HuffNode dist_tree[0x1000];
    if (!read_hufftree(&symr ,9 ,0x200,sym_tree) ||
        !read_hufftree(&distr,11,0x500,dist_tree)) return -1;

    ssize_t op = 0;
    while (op < usize) {
        int sym = get_huffcode(&symr, sym_tree);
        if (sym < 0x100) dst[op++] = (uint8_t)sym;
        else {
            size_t lng = sym - 0x100 + 3;
            size_t dist = get_huffcode(&distr, dist_tree) + 1;
            if (dist > op) return -1;
            size_t cp = op - dist;
            if (op + lng > usize) lng = usize - op;
            for (size_t i=0;i < lng;i++) dst[op++] = dst[cp++];
        }
    }

    return op;
}
EXPORT ssize_t decompress_graw_bpe(const uint8_t *restrict src, const size_t zsize,
                                         uint8_t *restrict dst, const ssize_t usize) {
    if (usize == 0) return 0;
    size_t ip = 0;
    ssize_t op = 0;

    while (ip < zsize && (op < usize || usize == -1)) {
        uint8_t ls[0x100];
        uint8_t rs[0x100];
        for (uint16_t i=0;i < 0x100;i++) {
            ls[i] = i;
            rs[i] = 0;
        }

        uint16_t pc = 0;
        while (pc < 0x100) {
            if (ip >= zsize) return -1;
            uint8_t c = src[ip++];
            if (c > 0x7F) {
                pc += c - 0x7F;
                c = 0;
            }

            for (uint16_t i=0;i <= c && pc < 0x100;i++,pc++) {
                if (ip >= zsize) return -1;

                uint8_t l = src[ip++];
                ls[pc] = l;
                if (l != pc) {
                    if (ip >= zsize) return -1;
                    rs[pc] = src[ip++];
                }
            }
        }

        if (ip + 2 > zsize) return -1;
        uint16_t s = read16be(src+ip);ip += 2;
        if (ip + s > zsize) return -1;

        size_t ep = ip + s;
        while (ip < ep && (op < usize || usize == -1)) {
            uint8_t stack[0x2000];
            uint16_t sp = 0;
            stack[sp++] = src[ip++];

            while (sp > 0 && (op < usize || usize == -1)) {
                uint8_t v = stack[--sp];

                if (ls[v] == v) dst[op++] = v;
                else {
                    if (sp + 2 > sizeof(stack)) return -1;

                    stack[sp++] = rs[v];
                    stack[sp++] = ls[v];
                }
            }
        }
    }

    return op;
}
EXPORT ssize_t decompress_lzrw1kh(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const ssize_t usize) {
    if (zsize == 0) return 0;
    if (src[0] == 0x80) {
        size_t size = zsize - 1;
        if (usize != -1 && usize < size) size = usize;
        memcpy(dst, src + 1, size);
        return size;
    }

    size_t ip = 3;
    #define CHKi(n) if (ip + (n) >= zsize) goto eof;
    ssize_t op = 0;
    uint16_t cmd = read16le(src + 1);
    uint8_t bits = 0x10;
    while (ip < zsize && (op < usize || usize == -1)) {
        if (!bits) {
            CHKi(1)
            cmd = read16le(src + ip);ip += 2;
            bits = 0x10;
        }
        if (cmd & 0x8000) {
            CHKi(1)
            uint8_t b0 = src[ip++];
            uint16_t dist = (b0 << 4) | (b0 >> 4);
            if (dist) {
                uint8_t len = (src[ip++] & 0xF) + 3;
                if (op + len > usize) len = usize - op;
                for (uint8_t i=0;i < len;i++,op++) dst[op] = dst[op - dist];
            } else {
                CHKi(2)
                uint16_t len = read16le(src + ip) + 0x10;ip += 2;
                if (op + len > usize) len = usize - op;
                for (uint16_t i=0;i < len;i++) dst[op++] = src[ip];
                ip++;
            }
        } else {
            CHKi(0)
            dst[op++] = src[ip++];
        }
        cmd <<= 1;
        bits--;
    }

eof:
    #undef CHKi
    return op;
}
EXPORT ssize_t decompress_camelot_blz(const uint8_t *restrict src, const size_t zsize,
                                            uint8_t *restrict dst, const ssize_t usize) {
    ssize_t op = 0;
    ssize_t ip = zsize;
    uint8_t f = 0;
    int8_t fbl = 0;

    #define CHKi(n) if (ip - (n) <= 0) goto eof;
    #define CHKo(n) if (usize != -1 && op + (n) >= usize) goto eof;

    while (ip > 0 && (op < usize || usize == -1)) {
        if (fbl <= 0) {
            CHKi(0);
            f = -src[--ip]; // - is correct, not ~
            fbl = 8;
        }

        if (f & 0x80) {
            CHKi(1)
            uint8_t b1 = src[--ip];
            uint8_t b2 = src[--ip];
            uint16_t dist = (b1 >> 4) | (b2 << 4);
            if (dist == 0) goto eof;

            uint32_t lng = b1 & 0xF;
            if (lng == 0) {
                CHKi(0);
                lng = src[--ip] + 0x10;
            } else if (lng == 1) {
                CHKi(1);
                uint8_t b0 = src[--ip];
                lng = (b0 | (src[--ip] << 8)) + 0x110;
            }
            if (usize != -1 && op + lng > usize) lng = usize - op;
            if (dist > op) return -1;
            for (uint32_t i=0;i < lng;i++,op++) dst[op] = dst[op - dist];
        } else {
            CHKi(0);
            dst[op++] = src[--ip];
        }

        f <<= 1;
        fbl--;
    }

eof:
    #undef CHKi
    #undef CHKo
    return op;
}

typedef struct {
    const uint8_t *src;
    size_t s;
    size_t p;
    uint8_t eofc;
    size_t full;
    size_t shift;
    uint32_t w;
    uint32_t v;
} YZRange;
static inline void init_YZRange(YZRange *restrict r, const uint8_t *restrict src, const size_t size, const size_t full, const size_t shift) {
    r->src = src;
    r->s = size;
    r->p = 1;
    r->eofc = 0;
    r->full = full;
    r->shift = shift;
    r->w = 0x80;
    r->v = src[0];
}
static inline uint16_t get_YZRange(YZRange *restrict r) {
    while (r->w <= (r->full >> 8)) {
        r->v <<= 8;
        if (r->p < r->s) r->v |= r->src[r->p++];
        else if (++r->eofc > 4) return -1;
        r->w <<= 8;
    }
    r->w >>= r->shift - 1;
    return (uint16_t)(r->v / r->w);
}
static inline void update_YZRange(YZRange *restrict r, const uint16_t w, const uint16_t v) {
    r->v -= r->w * v;
    r->w *= w;
    r->w >>= 1;
}
typedef struct {
    size_t size;
    size_t shift;
    uint16_t *ccnt;
    uint16_t *orngw;
    uint16_t *orngv;
    uint32_t sum;
    size_t bit;
    uint32_t cp;
    uint8_t flg;
    uint16_t *decs;
} YZFreqs;
static int8_t init_YZFreqs(YZFreqs *restrict f, const size_t size, const size_t shift) {
    f->size = size;
    f->shift = shift;

    f->ccnt = (uint16_t *)calloc(size, sizeof(uint16_t));
    if (!f->ccnt) return -1;
    f->orngw = (uint16_t *)malloc(size * sizeof(uint16_t));
    if (!f->orngw) return -1;
    f->orngv = (uint16_t *)malloc(size * sizeof(uint16_t));
    if (!f->orngv) return -1;
    f->decs = (uint16_t *)calloc(1 << shift, sizeof(uint16_t));
    if (!f->decs) return -1;

    size_t ix = 0;
    for (size_t i=0;i < (1 << shift);i++) {
        f->ccnt[ix]++;
        if (++ix >= size) ix = 0;
    }

    uint16_t sum = 0;
    for (size_t i=0;i < size;i++) {
        f->orngw[i] = f->ccnt[i];
        f->orngv[i] = sum;
        sum += f->ccnt[i];
    }

    for (size_t i=0;i < size;i++) f->ccnt[i] = 1;
    f->sum = size;
    f->bit = 0;
    for (;f->bit < shift && f->sum >= (1 << f->bit);f->bit++) {};
    f->cp = 1 << f->bit;
    f->flg = 0;

    return 0;
}
static void update_YZFreqs(YZFreqs *restrict f, const uint16_t c) {
    f->ccnt[c]++;
    f->sum++;

    if (f->shift > f->bit) {
        if (f->sum == f->cp) {
            uint16_t sum = 0;
            uint16_t x = 1 << (f->shift - f->bit);
            for (size_t i=0;i < f->size;i++) {
                f->orngw[i] = f->ccnt[i] * x;
                f->orngv[i] = sum;
                sum += f->orngw[i];
            }
            f->bit++;
            f->cp = 1 << f->bit;
            f->flg = 0;
        }
    } else {
        if (f->sum >= (1 << f->shift)) {
            uint16_t sum = 0;
            f->sum = 0;
            for (size_t i=0;i < f->size;i++) {
                f->orngw[i] = f->ccnt[i];
                f->orngv[i] = sum;
                sum += f->orngw[i];

                uint16_t c = f->ccnt[i] >> 1;
                f->ccnt[i] = (c == 0) ? 1 : c;
                f->sum += f->ccnt[i];
            }
            f->flg = 0;
        }
    }
}
static inline uint16_t get_YZFreqs(YZFreqs *restrict f, YZRange *restrict r) {
    uint16_t pos = get_YZRange(r);
    if (r->eofc > 4) return -1;

    if (!f->flg) {
        size_t j=0;
        for (size_t i=0;i < f->size;i++)
            for (;j < (f->orngv[i] + f->orngw[i]);j++)
                f->decs[j] = (uint16_t)i;
        f->flg = 1;
    }

    uint16_t c = f->decs[pos];
    update_YZRange(r, f->orngw[c], f->orngv[c]);
    update_YZFreqs(f, c);
    return c;
}
typedef struct {
    uint16_t c;
    size_t *off;
    uint32_t *len;
} YZDictE;
typedef struct {
    YZRange rng;
    YZFreqs fqc;
    YZFreqs fql;
    YZDictE *dict;
} YZ2;
static inline void free_YZ2(YZ2 *restrict y2, const uint16_t dicts) {
    if (y2->dict) {
        for (uint16_t i=0;i < dicts;i++) {
            if (y2->dict[i].off) free(y2->dict[i].off);
            if (y2->dict[i].len) free(y2->dict[i].len);
        }
        free(y2->dict);
    }
    if (y2->fqc.ccnt) free(y2->fqc.ccnt);
    if (y2->fqc.orngw) free(y2->fqc.orngw);
    if (y2->fqc.orngv) free(y2->fqc.orngv);
    if (y2->fqc.decs) free(y2->fqc.decs);
    if (y2->fql.ccnt) free(y2->fql.ccnt);
    if (y2->fql.orngw) free(y2->fql.orngw);
    if (y2->fql.orngv) free(y2->fql.orngv);
    if (y2->fql.decs) free(y2->fql.decs);
}
EXPORT ssize_t decompress_capcom_yz2(const uint8_t *restrict src, const size_t zsize,
                                           uint8_t *restrict dst, const ssize_t usize) {
    ssize_t op = -1;
    YZ2 y2;
    init_YZRange(&y2.rng, src, zsize, 0x80000000, 15);
    y2.dict = (YZDictE *)calloc(0x100,sizeof(YZDictE));
    if (!y2.dict) goto eof;
    for (uint16_t i=0;i < 0x100;i++) {
        y2.dict[i].off = (size_t *)calloc(0x200,sizeof(size_t));
        if (!y2.dict[i].off) goto eof;
        y2.dict[i].len = (uint32_t *)calloc(0x200,sizeof(uint32_t));
        if (!y2.dict[i].len) goto eof;
    }

    if ((op = init_YZFreqs(&y2.fqc, 0x500, 15)) < 0) goto eof;
    if ((op = init_YZFreqs(&y2.fql, 0x100, 15)) < 0) goto eof;

    size_t kp = 0;
    op = 0;
    while (op < usize || usize == -1) {
        uint16_t c = get_YZFreqs(&y2.fqc, &y2.rng);
        if (y2.rng.eofc > 4) break;
        size_t s = 1;

        if (c >= 0x400) dst[op++] = (uint8_t)(c - 0x400);
        else {
            if (op == 0) {
                op = -1;
                break;
            }
            uint32_t moto;
            if (c < 0x200) {
                uint16_t rtn = get_YZFreqs(&y2.fql, &y2.rng);
                if (y2.rng.eofc > 4) break;
                s = 0;
                switch (rtn) {
                    case 0: s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng) << 24;
                    case 1: s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng) << 16;
                    case 2: s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng) << 8;s |= (uint32_t)get_YZFreqs(&y2.fql, &y2.rng);break;
                    default: s = rtn;
                }
                if (y2.rng.eofc > 4) break;
                s = s - 3 + 2;

                uint8_t key = dst[kp];
                moto = y2.dict[key].off[(c + y2.dict[key].c) % 0x200];
            } else {
                uint8_t key = dst[kp];
                uint16_t cnt = y2.dict[key].c;
                s = y2.dict[key].len[(c + cnt) % 0x200];
                moto = y2.dict[key].off[((uint16_t)(c - 0x200) + cnt) % 0x200];
            }

            if (moto > op) moto = op;
            if (op + s > usize) s = usize - op;
            for (size_t i=0;i < s;i++) dst[op++] = dst[moto++];
        }

        if (kp < op - 1) {
            uint8_t key = dst[kp];
            uint16_t cnt = y2.dict[key].c;
            y2.dict[key].off[cnt] = kp + 1;
            y2.dict[key].len[cnt] = (uint32_t)s;
            y2.dict[key].c = (cnt + 1) % 0x200;
            kp = op - 1;
        }
    }

eof:
    free_YZ2(&y2, 0x100);
    return op;
}

typedef struct {
    int16_t ls[0x4EA];
    int16_t rs[0x4EA];
    int16_t par[0x4EA];
    uint16_t wg[0x4EA];
    int dist_bits[6];
    int dist_base[6];
} d0llz3_AHuff;
static void d0llz3_AHuff_update(d0llz3_AHuff *ah, int16_t n1, int16_t n2) {
    while (1) {
        int16_t p = ah->par[n1];
        ah->wg[p] = ah->wg[n1] + ah->wg[n2];
        if (p == 1) break;
        n1 = p;
        n2 = ah->ls[ah->par[n1]];
        if (n2 == n1) n2 = ah->rs[ah->par[n1]];
    }

    if (ah->wg[1] == 2000) {
        for (int16_t i=1;i < 0x4EA;i++)
            ah->wg[i] >>= 1;
    }
}
static int16_t d0llz_AHuff_get(BitReader *restrict br, d0llz3_AHuff *restrict ah) {
    int16_t n = 1;
    while (n < 0x275) {
        if (get_bit(br)) n = ah->rs[n];
        else n = ah->ls[n];
    }
    int16_t sym = n - 0x275;

    int16_t p = ah->par[n];
    ah->wg[n]++;
    if (p != 1) {
        int16_t sib = ah->ls[p];
        if (sib == n) sib = ah->rs[p];
        d0llz3_AHuff_update(ah,n,sib);

        do {
            p = ah->par[n];
            int16_t pp = ah->par[p];
            int16_t c = ah->ls[pp];
            if (c == p) c = ah->rs[pp];

            if (ah->wg[c] < ah->wg[n]) {
                if (ah->ls[pp] == p) ah->ls[pp] = n;
                else ah->rs[pp] = n;
                if (ah->ls[p] == n) ah->ls[p] = c;
                else ah->rs[p] = c;

                ah->par[c] = p;
                ah->par[n] = pp;
                int16_t osib = ah->ls[p];
                if (osib == c) osib = ah->rs[p];
                d0llz3_AHuff_update(ah,c,osib);
                n = c;
            }
            n = ah->par[n];
            p = ah->par[n];
        } while (p != 1);
    }

    return sym;
}
EXPORT ssize_t decompress_d0llz3(const uint8_t *restrict src, const size_t zsize,
                                       uint8_t *restrict dst, const ssize_t usize) {
    BitReader br;
    init_BitReader(&br, src, zsize);

    d0llz3_AHuff ah;
    for (int8_t i=0,bs=4;i < 6;i++,bs+=2)
        ah.dist_bits[i] = bs;
    for (int16_t i=2;i < 0x4EA;i++) {
        ah.par[i] = i / 2;
        ah.wg[i] = 1;
    }
    for (int16_t i=1;i < 0x275;i++) {
        ah.ls[i] = i * 2;
        ah.rs[i] = i * 2 + 1;
    }
    ah.wg[1] = 0;

    size_t bs = 0;
    for (int8_t i=0;i < 6;i++,bs += (1 << ah.dist_bits[i]))
        ah.dist_base[i] = bs;

    ssize_t op = 0;

    while (op < usize || usize == -1) {
        int16_t sym = d0llz_AHuff_get(&br,&ah);
        if (sym == 0x100) break;

        if (sym < 0x100) dst[op++] = sym;
        else {
            int16_t grp = (sym - 0x101) / 0x3E;
            int16_t len = sym - grp * 0x3E - 0xFE;
            ssize_t dist = op - (get_bits_l(&br, ah.dist_bits[grp]) + len + ah.dist_base[grp]);
            for (int16_t i=0;i < len && (op < usize || usize == -1);i++,dist++) {
                uint8_t b;
                if (dist < 0) b = 0;
                else b = dst[dist];
                dst[op++] = b;
            }
        }
    }

    return op;
}

#ifdef __cplusplus
}
#endif
