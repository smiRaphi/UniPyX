import type.time;

struct Str16 {
    u16 l;
    char v[l-1];
    padding[1];
};

fn format_dos_date(std::time::DOSDate date) {
    return std::time::format_dos_date(date);
};
fn format_dos_time(std::time::DOSTime time) {
    return std::time::format_dos_time(time);
};

using b;
struct se {
    char name[0x10];
    be std::time::DOSTime time [[format("format_dos_time")]];
    be std::time::DOSDate date [[format("format_dos_date")]];
    char type[4];
    u16 seg_id;
    u32 off;
    u32 size;

    if (size != 0 && seg_id == 1) {
        u64 p = $;
        b b @ off;
        $ = p;
    }
};
struct sge {
    u32 seg_id;
    Str16 name;
    Str16 path;
};

struct fe {
    padding[4];
    u32 nl;
    u32 stream_id;
    u32 unk2;
    char name[nl-1];
    padding[1];
};

enum bid:u32 {
    STREAM_SEG = 1000,
    OBJ = 1001,
    ROOT = 1002,
    FILE_INFO = 1004,
};
using pb;
struct b {
    bid id;
    u16 unkb0;
    u16 unkb1;
    u16 unkb2;
    u32 size;
    u64 ep = $ + size;

    match(id) {
        (bid::STREAM_SEG):{
            u32 n_strms;
            u16 unk1;
            u16 segc;
            se se[n_strms];
            u32 unk2;
            sge sge[segc];
        }
        (bid::OBJ):{
            char name[0x10];
            u32 unk1;
            u32 unk2;
            b b;
        }
        (bid::ROOT):pb b[while($ < ep)];
        (bid::FILE_INFO):{
            u16 unk1;
            u16 h;
            u16 w;
            u16 unk2;
            u16 unk3[8];

            u32 unk3;
            u32 c;
            fe fe[c];
        }
    }

    if (ep > $) $ = ep;
};
struct pb {
    padding[2];
    u32 off;
    $ = off;
    b b;
};

struct a {
    u16 unk1;
    u16 unk2;
    u32 unk3;
    pb root;
};

a a @ 0;