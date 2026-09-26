#pragma pattern_limit 8388608
#pragma array_limit 131072

import std.core;
import std.io;

fn transformv(auto a) {
    if (a.t == '\0') return a.t;
    return a.v;
};
struct v {
    u64 ep = parent.ep;
    char t;
    match (t) {
    ('@'): v v[while($ < ep && $[$] != '@')];
    ('B'): u8 v;
    ('s'): u16 v;
    ('i'): u32 v;
    ('F'): float v;
    ('D'): double v;
    ('['):{
        u32 s;
        char st;
        if (st == 'B') u8 v[s];
        else std::error(std::format("{} @ {}",st,$ - 1));
    }
    ('\0'): break;
    ('\x88'): {}
    (_): std::error(std::format("{} @ {}",t,$ - 1));
    }
} [[transform("transformv"),format("transformv")]];
using b;
struct b1r {
    u64 i = std::core::array_index();
    u64 sp = 0 [[export]];
    u64 ep = 0 [[export]];
    if (i == 0 && parent.ofs[1] == 1) {
        sp = parent.ofs[3];
        ep = parent.ofs[0];
    } else {
        sp = parent.ofs[3 + i*2];
        ep = parent.ofs[3 + i*2 + 1];
    }
    
    $ = sp;
    b b[while($ < ep)];
};
struct b {
    u8 t;
    u8 u0;
    u16 u1;
    u32 s;
    u32 u2;
    u32 u3;

    u64 ep = $ - 0x10 + s;
    u64 oep = ep;
    match (t) {
    (1):{
        v root;
        ep = root.v[6] + root.v[7];
        v ofs[while($ < ep)] @ root.v[6];
        b bo @ ofs[2];
        if (ofs[1] == 1) b1r rs[1];
        else b1r rs[ofs[1] - 1];
    }
    (15|2):{
        v root[while($ < ep)];
    }
    (_): std::error(std::format("{} @ {}",t,$ - 0x10));
    }
    $ = oep;
};

b root @ 0;
