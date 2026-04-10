#pragma endian big

struct me {
    s32 id;
    u8 nl;
    char n[nl];
};
struct mde {
    char name[4];
    padding[2];
    u32 c;
    me me[c];
};
struct e {
    s32 id;
    u32 offset;
    u32 size;

    if (id == -1111 && parent.name == "mCTy") {
        u32 c @ offset;
        mde mde[c] @ (offset+4);
    } else {
        char data_start[4] @ offset;
        char data_end[4] @ (offset+size-4);
    }
};
struct d {
    char name[4];
    u32 c;
    e e[c];
};
struct u {
    u32 off;
    u32 size;
    char u[size] @ off;
};
struct a {
    char magic[4];
    u32 off;
    $ = off;

    u32 c;
    d d[c];
    u32 uc;
    u u[uc];
};

a a @ 0;