enum ca:u16 {
    NONE,
    ZLIB,
    LZ4,
    ZSTD,
};
enum ea:u16 {
    NONE,
    SimpleCrypt,
    RC4,
    AES,
    SimpleCryptEx,
};
enum ha:u16 {
    MURMUR3 = 2,
};

struct e {
    u32 id;
    u32 off;
    u32 zsize;
    u32 usize;
    u32 zcrc;
    u32 crc;
    ca comp_algo;
    ea enc_algo;
};

struct a {
    char magic[4];
    u32 c;
    u32 unk1;
    ea enc_algo;
    padding[2];
    ha ha;
    padding[2];
    u32 tof;
    e e[c] @ tof;
};

a a @ 0;