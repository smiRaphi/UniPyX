enum t:u8 {
    IMAGE_1D=1,
    IMAGE_2D,
    IMAGE_3D,
    IMAGE_CUBE,
    BUFFER,
};

bitfield u40 {
    value : 40;
} [[inline]];
struct eb {
    u40 offset;
    u8 compression;
    padding[1];
    u8 flags;
    u32 size;
    u32 crc32;

    char data_start[4] @ offset.value;
    char data_end[4] @ (offset.value + size - 4);
};
struct ea {
    u16 nidx;
    t t;
    u8 format;

    u16 width;
    u16 height;
    u16 depth;
    u16 nmips;
    u16 ntmips;
    u16 arrsize;
    u16 base_blob_idx;
    u16 tail_base_blob_idx;
};

struct a {
    char magic[4];
    u32 version;
    u64 off;
    $ = off;
    u16 assc;
    u16 blobc;
    ea ea[assc];
    eb eb[blobc];
};

a a @ 0;

bitfield gb {
    idx:2;
    lts:18;
    padding:12;
};
struct g {
    u8 id;
    u8 magic;
    u16 bc;
    gb gb;
};

g g @ 0x10;