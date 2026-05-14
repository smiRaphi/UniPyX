struct Str {
    u8 l;
    char v[l];
};
struct p<T> {
    u32 poff;
    T e @ (poff + parent.p) [[inline]];
};

bitfield flags {
    compressed : 1;
    padding : 7;
};

struct fe {
    Str name;
    u32 off;
    u32 usize;
    u32 zsize;
    u32 unk1;
    padding[4];
    flags flags;
    u24 unk2;
} [[inline]];

using e;
struct de {
    Str name;
    u32 off;
    e e @ off;
};
struct e {
    u16 dir_count;
    u16 file_count;
    u32 file_inf_off;
 
    u64 p = file_inf_off;
    p<fe> files[file_count] @ file_inf_off;
    p = $;
    p<de> dirs[dir_count];
};

struct footer {
    u8 day; // Gorky Zero release date in hex
    u8 month;
    u16 year;
    u32 version;
    u32 toc_start; // can be ignored
    u32 root_off;
    u32 unk1;

    e root @ root_off;
};

footer footer @ (sizeof($)-0x14);
