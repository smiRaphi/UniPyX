struct e1 {
    if (parent.type == "AGTP")
        padding[1];
    else if (parent.type == "SSBD")
        u32 unk;
    char name[];
    u32 size;
    $ += size;
};
using s;
struct e2 {
    u32 unk1;
    padding[1];
    char name[];
    u32 chunks;
    s s;
};
struct e3 {
    char name[];
    u32 count;
    float data[count*4];
};
struct e4 {
    char sig[4];
    u32 size;
    $ += size;
    if (!size) break;
};
struct e {
    char sig[4];
    if ($ >= sizeof($)) break;
    char type[4];
    u32 next_off;
    u64 xoff = $ + next_off;
    if (next_off) {
        match(type) {
            ("RCSO"|"PRCS"|"AGTP"|"GIRT"):{
                u32 count;
                e1 e1[count];
            }
            ("SSBD"):{
                u32 unk1;
                u32 count;
                e1 e1[count];
            }
            ("YPBD"):{
                char unk1[4];
                u32 unk2;
                u32 count;
                e2 e2[count];
            }
            ("KOLB"|"1DOL"):{
                e4 e4[while($ < xoff)];
                u32 count;
                e1 e1[count];
            }
            ("HTAP"):{
                u32 count;
                e3 e3[count];
            }
        }
    }
    $ = xoff;
};
struct b {
    char magic[4];
    u32 unk1;
    char head[4];
    u32 offset;
    $ += offset;
};
struct a:b {
    e e[while(1)];
};
struct s:b {
    e e[parent.chunks];
    char end[4];
};

a a @ 0;