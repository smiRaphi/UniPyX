struct e {
    u32 fname_length;
    u32 size;
    u32 offset;
    padding[4];
    u32 unk3;
    char fname[fname_length];
};

struct a {
    char sig[while($[$] != 0x1A)];
    padding[1];
    char unk1[7];
    u32 unk2;
    char fname[0x20];
    e e[25];
};

a a @ 0;
