struct ne {
    u64 off;
    char n[] @ (parent.noff + 8 + parent.nc*8 + off);
};

bitfield cf {
    padding : 1;
    unk1 : 1;
    oodle : 1;
    padding : 13;
};
struct e {
    padding[8];//u64 unk1;
    u64 unk2;
    s64 unk3;
    padding[8];//u64 unk4;
    u64 name_id_off;
    padding[8];//u64 unk5;
    padding[8];//u64 unk6;
    u64 offset;
    u64 zsize;
    u64 usize;
    u64 unk7;
    u64 unk8;
    u64 unk9;
    u32 unk10_1;
    u32 unk10_2;
    cf cf;
    u32 unk11;
    padding[2];
    padding[8];//u64 unk11;
    u64 unk12;
    padding[8];//u64 unk13;
};

struct a {
    char magic[4];
    s32 version;
    s32 unk1;
    s32 unk2;
    s64 unk3;
    s32 unk4;
    s32 unk5;
    if (version >= 0xD && unk1 != 0) s32 unkD_1;
    u32 c;
    u32 unk6;
    u32 dc;
    u32 unk7;
    u64 unk8;
    u64 off1;
    u64 noff;
    u64 doff;
    u64 ioff;
    u64 doff2;
    u64 doff_end;
    u64 data_off;

    u64 nc @ noff;
    ne ne[nc] @ (noff+8);

    e e[c] @ ioff;
    u32 d[dc] @ doff_end; 
};

a a @ 0;