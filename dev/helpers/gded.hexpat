#pragma pattern_limit 9999999

struct String {
    u32 length;
    if (length) {
        char string[length-1];
        padding[1];
    }
    $ += -$%4;
};
using b;
struct FDIRe {
    u32 offset;
    u32 size;
    char name[0x18];
    b gde @ offset;
};
struct Block {
    char name[4];
    u32 size;
    u64 p = $+size;

    match(name){
        ("FSIZ"): u32 file_size;
        ("VERS"): String version;
        ("EXBY"): String string;
        ("WDIM"): {
            u32 unk1;
            float min_x;
            float min_y;
            float min_z;
            float max_x;
            float max_y;
            float max_z;
            u32 scale_x;
            u32 scale_y;
            u32 scale_z;
        }
        ("CLAS"|"PRPS"|"OBPR"): Block blocks[while($ < p)];
        ("BRCM"|"ACCM"|"CPCM"|"PRCM"):{
            u32 count;
            String strings[count];
        }
        ("PRIM"):{
            if (parent.name == "CLAS") {
                u32 count;
                String strings[count*2];
            } else {
                u32 unk1;
                u32 unk2;
                Block blocks[while($ < p)];
            }
        }
        ("BNCH"):{
            u32 unk1;
            u32 isize;
        }
        ("BRTR"|"ACTN"|"CHBR"|"SCRT"):{
            u32 unk1;
            u32 unk2;
            Block blocks[while($ < p)];
        }
        ("FDIR"):{
            u32 unk1;
            u32 count;
            FDIRe e[count];
        }
        ("PROP"):{
            u16 id;
            u16 unk2;
            float data[while($ < p)];
        }
        ("RSRC"):{
            u32 unk1;
            u32 unk2;
            padding[4];
            Block blocks[while($ < p)];
        }
        ("GTEX"):{
            u32 id;
            u32 flags;
            if (flags & 0b00100000) {
                Block OBPR;
            }
            u32 unk3;
            padding[4];
            u32 unk4;
            u32 unk5;
            u32 unk6;
            Block zipn_block;
        }
        ("ZIPN"):{
            u32 size_data;
            u32 unk1;
            u32 unk2;
            u32 unk3;
            u32 unk4;
        }
        ("GMDL"):{
            u32 unk1;
            u32 flags;
            u32 unk2;
            Block blocks[while($ < p)];
        }
        ("MREG"):{
            u32 unk1;
            u32 flags;
            char unk2[4];
            u32 unk2;
            s32 unk3;
            Block blocks[while($ < p)];
        }
        ("PERF"): float perf;
        ("GMOV"):{
            u32 unk1;
            u32 flags;
            u32 unk3;
            char unk4[4];
            u32 unk5;
            u32 unk6;
            padding[4];
            String name;
            Block frml;
        }
        ("ENDF"): break;
    }

    $ = p;
    $ += -$%4;
};

struct ba {
    char magic[];
    padding[-$%4];
    u8 endf = 0;
};
struct b:ba {
    Block blocks[while($ < (parent.offset+parent.size))];
};
struct a:ba {
    Block blocks[while($ < sizeof($))];
};

a a @ 0;
