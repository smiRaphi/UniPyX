#include "util.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef unsigned long DWORD;
XIMPORT(xcompress, kernel32)
XEXPORT long __stdcall XMemCreateDecompressionContext(int CodecType, const void *pCodecParams, DWORD Flags, void **pContext);
XEXPORT void __stdcall XMemDestroyDecompressionContext(void *pContext);
XEXPORT long __stdcall XMemDecompress(void *pContext, void *pDestination, size_t *pDestSize, const void *pSource, size_t SrcSize);
XEXPORT long __stdcall XMemDecompressSegmentTD(void *pContext, void *pDestination, size_t *pDestSize, const void *pSource,
                                              size_t SrcSize, size_t DestSize, size_t Offset);

struct OZUserData {
    const uint8_t *ib;
    size_t ip;
    size_t is;
    uint8_t *ob;
    size_t op;
    size_t os;
};
static size_t oz_readb(void *ctx, uint8_t *buf, size_t s) {
    struct OZUserData *b = *(struct OZUserData **)ctx;
    if (b->ip + s > b->is) s = b->is - b->ip;
    memcpy(buf, b->ib + b->ip, s);
    b->ip += s;
    return s;
}
static size_t oz_writeb(void *ctx, const uint8_t *buf, size_t s) {
    struct OZUserData *b = *(struct OZUserData **)ctx;
    if (b->op + s > b->os) s = b->os - b->op;
    memcpy(b->ob + b->op, buf, s);
    b->op += s;
    return s;
}
XIMPORT(unimplode6a)
#include <unimplode6a.h>
EXPORT int decompress_zip_implode(const uint8_t *restrict src, const size_t zsize,
                                        uint8_t *restrict dst, const size_t usize, const uint16_t flags) {
    ui6a_ctx *ui6a = NULL;
    struct OZUserData u;
    u.ib = src;u.ip = 0;u.is = zsize;
    u.ob = dst;u.op = 0;u.os = usize;

    ui6a = ui6a_create(&u);
    if (!ui6a) return -1;

    ui6a->cmpr_size = zsize;
    ui6a->uncmpr_size = usize;
    ui6a->bit_flags = flags;
    ui6a->cb_read = oz_readb;
    ui6a->cb_write = oz_writeb;

    ui6a_unimplode(ui6a);
    int r = ui6a->error_code;
    free(ui6a);
    return r;
}
XIMPORT(ozunreduce)
#include <ozunreduce.h>
EXPORT int decompress_zip_reduce(const uint8_t *restrict src, const size_t zsize,
                                       uint8_t *restrict dst, const size_t usize, const uint8_t level) {
    ozur_ctx *ozur = NULL;
    struct OZUserData u;
    u.ib = src;u.ip = 0;u.is = zsize;
    u.ob = dst;u.op = 0;u.os = usize;

    ozur = (ozur_ctx *)calloc(1, sizeof(ozur_ctx));
    if (!ozur) return -1;

    ozur->userdata = &u;
    ozur->cmpr_size = zsize;
    ozur->uncmpr_size = usize;
    ozur->cmpr_factor = level;
    ozur->cb_read = oz_readb;
    ozur->cb_write = oz_writeb;

    ozur_run(ozur);
    int r = ozur->error_code;
    free(ozur);
    return r;
}
XIMPORT(ozunshrink)
#include <ozunshrink.h>
EXPORT int decompress_zip_shrink(const uint8_t *restrict src, const size_t zsize,
                                       uint8_t *restrict dst, const size_t usize) {
    ozus_ctx *ozus = NULL;
    struct OZUserData u;
    u.ib = src;u.ip = 0;u.is = zsize;
    u.ob = dst;u.op = 0;u.os = usize;

    ozus = (ozus_ctx *)calloc(1, sizeof(ozus_ctx));
    if (!ozus) return -1;

    ozus->userdata = &u;
    ozus->cmpr_size = zsize;
    ozus->uncmpr_size = usize;
    ozus->cb_read = oz_readb;
    ozus->cb_write = oz_writeb;

    ozus_run(ozus);
    int r = ozus->error_code;
    free(ozus);
    return r;
}

XIMPORT(lzfse)
EXPORT ssize_t decompress_lzfse(const uint8_t *restrict src, const size_t zsize,
                                      uint8_t *restrict dst, const size_t usize) {
    void *aux = malloc(lzfse_decode_scratch_size());
    if (!aux) return -1;
    ssize_t r = lzfse_decode_buffer(dst, usize, src, zsize, aux);
    free(aux);
    return r;
}

XIMPORT(lpaq8_zzz)
#include <lpaq8_zzz.h>
EXPORT ssize_t decompress_lpaq8(uint8_t *restrict src, size_t zsize,
                                uint8_t *restrict dst, const size_t usize) {
    size_t us = usize;
    uint8_t d1;
    size_t d2;
    int r = lpaq8D(src, zsize, dst, &us, &d1, &d2);
    if (r != 0) return -r;
    return us;
}

#ifdef __cplusplus
}
#endif
