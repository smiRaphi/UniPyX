import std.io;

struct Str {
    char v[];
};
bitfield zstrl {
    length : 30;
    bool empty : 1;
    bool unk : 1;
};
struct ZStr {
    zstrl l;
    if (!l.empty)
        char v[l.length];
};

enum ST:u32 {
    Rebase = 0x12EBA5ED,
    TypeReindex = 0x3989BF9F,
    RuntimeResourceID = 0x578FBCEE,
};
struct RebLoc {
    s32 reb_loc_off @ sec_p;sec_p += 4;
    reb_o += reb_loc_off;
    $ = parent.p + reb_o;
    s32 v;
    s64 rv = v + reb_o [[export]];
    s64 rvo = rv + parent.p - 4 [[export]];
    if (rv != -1) {
        u32 pv @ rvo;
    }
};
struct Section {
    u64 p = $;
    ST type @ sec_p;sec_p += 4;
    u32 size @ sec_p;sec_p += 4;

    if (type == ST::Rebase) {
        reb_o = 0;
        u32 loc_c @ sec_p;sec_p += 4;
        RebLoc locs[loc_c];
    }
};

struct Block {
    char name[4];
    u32 hunk1;
    u32 hunk2;
    u32 size;
    s32 hunk3;
    s32 hunk4;
    u64 p = $ + size;

    match(name) {
        // resource lib
        ("BILR"):{}
        // header lib
        ("BILH"):{
            u32 refc;
            u32 unk1;
            u32 unk2;
            u32 unk3;
            Str refs[refc];

            char bin[3];
            char version;

            if (version == '2') {
                bool big_endian;
                u8 alignment;
                u8 sections_count;
                padding[1];
                be u32 data_length;
                padding[4];
                sec_p = $ + data_length;
                Section secs[sections_count];
            }
        }
        // FSB
        ("MBSF"):{
            char FSB[3];
            char version;
        }
    }
    $ = p;
};

u64 sec_p = 0;
s64 reb_o = 0;
Block a @ 0;