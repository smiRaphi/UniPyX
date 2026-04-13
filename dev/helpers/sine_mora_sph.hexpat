struct Str {
    u32 l;
    char n[l];
};
struct sv<T> {
    T v;
} [[inline]];

struct kvp {
    Str k;
    Str v;
};

struct a2 {
    u32 r3;
    u32 r4;
    u32 u4;
    u32 u5;
    $ += u5;
    u32 u6;
    padding[4];
    sv<u16> r6[u6];
    Str material;
    u32 vls;
    kvp kvps[vls];
    u32 u7;
    $ += u7 * 0x44;
};
struct a {
    u32 u1;
    s32 r0;
    u32 u2;
    if (u2 == 1) {
        sv<float> r1[6];
        u32 u3;
        a2 a2[u3];
        if ($ < sizeof($))
            Str pname;
    } else {
        Str r1;
    }
    sv<float> r2[16];
};

a a1 @ $;
a a[a1.r0-1] @ $;