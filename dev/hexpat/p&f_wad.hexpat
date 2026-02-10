#pragma endian big
import std.core;
import std.mem;

struct string_entry {
    char shash[4];
    u32 string_offset;
    char string[] @ string_offset;
};
fn get_string(str shash) {
    u64 addr = std::mem::find_string_in_range(0,a.strings_offset,std::mem::size(),shash);
    string_entry e @ addr;
    return e.string;
};

enum Type:u8 {
    Bool  = 1,
    Float = 2,
    U16   = 6,
    U8    = 8,
    U32   = 12,
};

struct dict_sub_entry {
    char name[4] [[format("get_string")]];
    bool unk1;
    Type type;
    u16 unk2;
    if (name == "\x00\x00\x00\x00") char name2[4] [[format("get_string")]];
    else char unk3[4];
    u32 offset;
};
struct dict_entry {
    char name[4] [[format("get_string")]];
    u32 count;
    u32 offset;
    dict_sub_entry entries[count] @ offset;
};

struct content_entry {
    u32 size;
    u32 offset;
    char unk1[4];
    u32 unk2;
    char name[4] [[format("get_string")]];
    padding[4];

    if (size == 8 && (
        name == "\x38\x97\xCE\x4E" || name == "\x44\x81\x9C\x79"
    )) {
        u32 count @ offset;
        u32 offset2 @ (offset+4);
    }
};

struct a {
    padding[4];
    u32 unk1;
    
    u32 dict_count;
    u32 dict_offset;
    u32 content_count;
    u32 content_offset;
    u32 unk_count;
    u32 unk_offset;
    u32 strings_count;
    u32 strings_offset;
    padding[8];

    dict_entry dicts[dict_count] @ dict_offset;
    content_entry content[content_count] @ content_offset;
    string_entry strings[strings_count] @ strings_offset;
};

a a @ 0;