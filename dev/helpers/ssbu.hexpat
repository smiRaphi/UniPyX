#pragma array_limit 9999999
#pragma pattern_limit 9999999

struct Hash40 {
    u32 crc32;
    u8 len;
} [[single_color]];
struct Hash40p:Hash40 {
    padding[3];
};

enum regs:u32 {
    jp    = 0x087b3c2f,
    jp_ja = 0x9372c64c,
    us    = 0x34b5009c,
    us_en = 0xa89412b4,
    us_fr = 0x32fea967,
    us_es = 0xf95a0bb1,
    eu    = 0x11da64c2,
    eu_en = 0xd849ea67,
    eu_fr = 0xcb4686a3,
    eu_es = 0xcbf41e08,
    eu_de = 0xb068c886,
    eu_nl = 0x95501e00,
    eu_it = 0x8ca541fb,
    eu_ru = 0x7a89866f,
    kr    = 0xc6351721,
    kr_ko = 0x17f046f7,
    zh    = 0x22cc84c9,
    zh_cn = 0xfb809f55,
    zh_tw = 0x4cf4768f,
};

struct sn2h {
    Hash40 path;
    u24 idx;
    u32 flags;
};
struct so {
    u64 size;
    u64 offset;
};
struct rg {
    regs lang;
    regs reg;
    u32 reg_id;
};
struct di {
    Hash40 full_path;
    u24 idx;
    Hash40p name;
    Hash40p _parent;
    Hash40p dis_re;
    u32 file_inf_start_idx;
    u32 file_inf_count;
    s32 child_dir_start_idx;
    s32 child_dir_count;
    u32 flags; 
};
struct dof {
    u64 off;
    u32 unk_size;
    u32 size;
    u32 sub_dat_start_idx;
    u32 sub_dat_count;
    u32 redirect_idx;
};
struct fin {
    Hash40 path;
    u24 didx;
    Hash40 extension;
    u24 ftf;
    Hash40 _parent;
    u24 unk1;
    Hash40 unk2;
    u24 unk3;
    u32 sfidx;
    u32 flags;
};
bitfield sflg {
    padding : 1;
    empty : 1;
    padding : 2;
    unk1 : 1;
    padding : 1;
    zstd : 1;
    comp : 1;
};
struct sfin {
    u32 off;
    u32 zsize;
    u32 usize;
    u24 redirect_idx;
    be sflg flags;
};

import std.core;
struct f {
    u64 i = std::core::array_index();
    if (parent.finf[i].flags & 0x00300000 != 0x00300000) {
        if (!parent.finf[i].ftf) {
            u64 di = parent.dil[parent.finf[i].didx].idx;
            u64 off = parent.parent.file_seco + parent.dofs[di].off + parent.sfinf[parent.finf[i].sfidx].off << 2;
            u64 eoff = off + parent.sfinf[parent.finf[i].sfidx].zsize - 4;
            char data_start[4] @ off;
            char data_end[4] @ eoff;
        }
    }
} [[single_color]];

struct tb {
    u32 size;
    u32 cs[9];
    u32 tc[2];
    u8 rc[2];
    padding[2];
    
    u32 c1[4];
    $ += 12 * c1[0] + 8 * c1[1];
    sn2h Sn2h[c1[1]];
    u32 sidx2fidx[c1[2]];
    so So[c1[3]];
    rg rgm[rc[0]];
    di dil[cs[0]];
    dof dofs[cs[1]+cs[7]];
    break;
    $ += 8 * cs[5];
    fin finf[cs[6]];
    sfin sfinf[cs[3]+cs[8]];
    //f fs[cs[6]];
};

struct a {
    u64 magic;
    u64 stream_seco;
    u64 file_seco;
    u64 shared_seco;
    u64 file_syso;

    tb file_sys @ file_syso;
};

a a @ 0;
