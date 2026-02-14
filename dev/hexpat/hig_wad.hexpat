struct e {
    u32 crc;
    char path[0x60];
    u32 unk1;
    u32 size;
    u32 unk2;
    u32 nearly_next_off;
    u32 unk3;
    padding[0x48];

    char data_start[4];
    $ += size - 8;
    char data_end[4];
    $ += -size%0x10;
    u128 pad[while(($+16) < sizeof($) && !($[$]+$[$+1]+$[$+2]+$[$+3]))] [[hidden]];
};

e e[while(($+3) < sizeof($))] @ 0x000599CD;