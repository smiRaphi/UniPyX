#define SECS 0x200

import type.time;
import std.io;
import std.time;

fn format_dosd(u16 value) {
    auto d = std::time::to_dos_date(value);
    return std::format("{}/{}/{}", d.day, d.month, d.year + 2000);
};
using FATXDate = u16 [[format("format_dosd")]];

struct test {
    if ($[$]) break;
    $ += SECS;
};
enum Type:u8 {
    file,
    volume_label,
    dir,
    long_filename,
};
bitfield Attr {
    bool read_only : 1;
    bool hidden : 1;
    bool system : 1;
    Type type : 2;
    bool archive : 1;
    bool normal : 1;
};
u64 CLSTO = 0;
u64 CLSTS = 0;
struct de {
    u8 nl;
    if (nl == 0xFF || nl == 0) break;
    Attr attr;
    char n[nl];
    padding[0x2A - nl];
    u32 first_clst;
    u32 size;

    type::DOSTime mt;
    FATXDate md;
    type::DOSTime ct;
    FATXDate cd;
    type::DOSTime at;
    FATXDate ad;

    if (attr.type == Type::dir) {
        de de[while($ < sizeof($))] @ (CLSTO + CLSTS * first_clst);
    }
};
struct a {
    char magic[4];
    s32 volume_id;
    u32 sec_per_clst;
    u32 root_clst;
    padding[0xFF0];

    CLSTS = sec_per_clst * SECS;
    u64 CLSTC = sizeof($) / CLSTS + 1;
    u8 FATS = 4;
    if (CLSTC < 0xFFF0) FATS = 2;

    if (FATS == 2) u16 fats[CLSTC];
    else if (FATS == 4) u32 fats[CLSTC];

    $ += -$ % SECS;
    test test[while(1)] [[hidden]];
    CLSTO = $ - CLSTS;

    de root[while($ < sizeof($))] @ (CLSTO + CLSTS * root_clst);
};

a a @ 0;
