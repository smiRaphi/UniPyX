bitfield fl {
    ps2 : 1;
    pc : 1;
    padding : 2;
    unk1 : 1;
    padding : 3;
    unk2 : 1;
    padding : 23;
};

struct de {
    u32 offset;
    u32 size;
    s32 unk1;
    u32 unk2;
    padding[4];
    u32 unk3;
    padding[8];

    char data_start[4] @ (parent.bo+offset);
    char data_end[4] @ (parent.bo+offset+size-4);
};
struct Pde {
    u32 off;
    u64 bo = parent.bo;
    de de @ (bo+off);
};
struct d {
    u32 unk1;
    u32 data_size;
    u32 c;
    u32 unk3;
    u32 unk4;
    u32 unk5;
    u32 unk6;
    u32 unk7;
    $ += 0x60;
    if (parent.fl.ps2) padding[-$%0x800];

    u64 bo = $ + c*4 + -c%4*4 + 0x10*(unk7!=5 && c);
    Pde de[c];
    $ = bo + data_size;
    if (parent.fl.ps2) padding[-$%0x800];
};

struct sd {
    u32 u1;
    u8 dat[u1];
};

struct e {
    fl fl;
    u32 xc;
    u64 id;
    u32 size;
    u32 offset;

    if (fl.unk1 && fl.unk2) {
        u64 p = $;
        $ = parent.bo+offset;
        d d;
        sd sd[xc];
        $ = p;
    } else {
        char data_start[4] @ (parent.bo+offset);
        char data_end[4] @ (parent.bo+offset+size-4);
    }
};

struct a {
    char magic[8];
    fl fl;
    u32 c;
    u64 bo = 0x10+c*0x18;
    e e[c];
    $ = bo + e[c-1].offset + e[c-1].size;
    if (fl.ps2) padding[-$%0x800];
    char spaces[0x80];
};

a a @ 0;