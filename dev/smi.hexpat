#pragma once
#pragma author smiRaphi
#pragma description Utility library

namespace auto smi {

struct Data<auto size, auto name> {
    u8 tag_size = 4;
    if (tag_size > size) tag_size = size;
    u8 start[tag_size] @ $ [[name(name + ":start")]];
    padding[size];
    u8 end[tag_size] @ ($ - tag_size) [[name(name + ":end")]];
};

fn fmtStr(auto a) { return a.v; };
struct Str<auto size> {
    u64 ep = $ + size;
    char v[while($ < ep && $[$])];
} [[fixed_size(size),format("smi::fmtStr")]];

}
