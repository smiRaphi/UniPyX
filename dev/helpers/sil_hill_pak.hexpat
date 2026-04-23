import type.time;

enum t:u16 {
    NULL = 0,
    EIFF = 2,
    SYT = 4,
    CSV = 7,
    EIFF2 = 0x10,
    SHADER = 0x11,
    MCI = 0x17,
    HAVOC = 0x1D,
};

bitfield f {
    unk1 : 1;
    padding : 3;
    lzo : 1;
    padding : 1;
    unk3 : 1;
    padding : 1;
    unk4 : 1;
    padding : 4;
    unk5 : 1;
    padding : 2;
    padding : 16;
};

struct e {
    char name[0x40];
    f flags;
    type::time32_t unk2;
    u32 off;
    s32 size;
    s16 unk3;
    t t;
    u32 size2;

    if (size != -1) {
        char data_start[4] @ off;
        char data_end[4] @ (off+size-4);
    }
};

struct a {
    char magic[4];
    u32 v;
    u32 c;
    padding[4];
    e e[c];
};

a a @ 0;