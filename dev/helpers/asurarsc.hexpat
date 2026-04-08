struct rsfle {
    char name[];
    padding[-$%4];
    u32 unk1;
    u32 unk2;
    u32 unk3;
};

struct b {
    char n[4];
    if (n == "\0\0\0\0") break;
    u32 size;
    u64 ep = $ + size - 8;
    u32 unk1;
    padding[4];
 
    match(n) {
        ("RSFL"):{
            u32 c;
            rsfle e[c];
        }
        ("RSCF"):{
            u32 unk2;
            padding[4];
            u32 size;
            char fnm[];
        }
        ("FONT"):{
        }
        ("FNFO"):{
            u32 file_size;
        }
        ("HANM"):{
            if (unk1 == 6) {
                u32 unk2;
                float speed;
                char name[];
            } else if (unk1 == 5) {
                char name1[];
                padding[0x80-sizeof(name1)];
                char name2[];
                padding[0x80-sizeof(name2)];
            }
        }
        ("HMPT"):{
            u32 unk2;
            char name[];
        }
    }
    
    $ = ep;
};

struct a {
    char magic[8];
    b b[while($ < sizeof($))];
};

a a @ 0;
