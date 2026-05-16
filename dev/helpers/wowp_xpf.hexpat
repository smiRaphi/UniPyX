struct S16 {
    u16 l;
    char16 v[l];
};

struct e0 {
    S16 name;
    u32 unk1;
    u32 unk2;
};
struct e1 {
    u16 id;
    S16 name;
};
struct e1_1 {
    u16 id;
    u32 unk1;
    S16 name;
};
struct e2 {
    u16 unk1;
    s16 flags; // 0 = uncompressed, < 0 = lz11
    u32 off;
    char data_start[4] @ (off + parent.bp);
};
struct e3 {
    u16 id1; // ??? seems to be somewhat based on the count
    u16 off_id;
    s16 unk[parent.xc];
};

struct a {
    u32 magic; // 0xBADBEEF1
    u8 unk1;
    e0 e0[unk1];
    u32 v = e0[0].unk1; // should be "Engine"
    u64 bp = $;

    if (v >= 0x20) {
        u32 unk2;
        u16 c;
        e1_1 e1[c];
        u16 uc1;
        e2 e2[uc1];
        u16 uc2;
        u32 xc = ((e2[0].off + bp) - $)/2/uc2 - 2; // e2[0].off should be the smallest offset
        e3 e3[uc2];
    } else if (v >= 0x10) {
        u32 unk2;
        u16 c;
        e1_1 e1[c];
        u16 uc1;
        u16 uc2;
        u32 xc = 3;
        e3 e3[uc2];
        e2 e2[uc1];
    } else {
        u16 c;
        e1 e1[c];

        u16 uc1;
        u16 unk6[uc1];
        e2 e2[uc1];
    }
    
 
};

a a @ 0;