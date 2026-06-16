#pragma endian big

struct oe {
    u32 id;
    u32 off;
    padding[8];

    char start[4] @ (parent.do + off);
};
struct ote {
    u32 to;
    u32 do;
    u32 ds;
    u32 c;
    oe oe[c] @ to;
};
struct e {
    u64 u1;
    u32 u2;
    u64 u3;
    u32 nof;
    char n[] @ (parent.sof + nof);
    u32 u4;
    padding[12];
    u32 zs;
    u32 us;
    u32 u5;
    u32 u6;
    padding[4];
    u32 u7;
};

u64 UEP = 0;
struct ue {
    u32 size;
    u32 c;
    u32 off;
    u32 u3;
    u32 ut[0x44];

    u64 do = parent.udo + off;
    char start[4] @ do;
    char end[4] @ (do + size - 4);

    oe oe[c] @ UEP;
    UEP += c*0x10;
};

struct a {
    char magic[4];
    u32 v;
    u32 c;
    padding[4];
    u32 un1;
    padding[4];
    
    u32 us;
    u64 sof = 0x50 + us;
    u32 tab_off1;
    u64 to1 = sof + tab_off1;

    ote ote[2];
    u32 uc;
    u32 uo;
    u32 udo;
    u32 uds;
    UEP = uo + 0x120*uc;
    ue ue[uc] @ uo;

    e e[c] @ to1;
};
