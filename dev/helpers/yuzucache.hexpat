enum Stage:u32 {
    VertexB,
    TessellationControl,
    TessellationEval,
    Geometry,
    Fragment,
    Compute,
    VertexA,
};

enum TextureType:u32 {
    Color1D,
    ColorArray1D,
    Color2D,
    ColorArray2D,
    Color3D,
    ColorCube,
    ColorArrayCube,
    Buffer,
    Color2DRect,
};
enum TexturePixelFormat:u32 {
    A8B8G8R8_UNORM,
    A8B8G8R8_SNORM,
    A8B8G8R8_SINT,
    A8B8G8R8_UINT,
    R5G6B5_UNORM,
    B5G6R5_UNORM,
    A1R5G5B5_UNORM,
    A2B10G10R10_UNORM,
    A2B10G10R10_UINT,
    A2R10G10B10_UNORM,
    A1B5G5R5_UNORM,
    A5B5G5R1_UNORM,
    R8_UNORM,
    R8_SNORM,
    R8_SINT,
    R8_UINT,
    R16G16B16A16_FLOAT,
    R16G16B16A16_UNORM,
    R16G16B16A16_SNORM,
    R16G16B16A16_SINT,
    R16G16B16A16_UINT,
    B10G11R11_FLOAT,
    R32G32B32A32_UINT,
    BC1_RGBA_UNORM,
    BC2_UNORM,
    BC3_UNORM,
    BC4_UNORM,
    BC4_SNORM,
    BC5_UNORM,
    BC5_SNORM,
    BC7_UNORM,
    BC6H_UFLOAT,
    BC6H_SFLOAT,
    ASTC_2D_4X4_UNORM,
    B8G8R8A8_UNORM,
    R32G32B32A32_FLOAT,
    R32G32B32A32_SINT,
    R32G32_FLOAT,
    R32G32_SINT,
    R32_FLOAT,
    R16_FLOAT,
    R16_UNORM,
    R16_SNORM,
    R16_UINT,
    R16_SINT,
    R16G16_UNORM,
    R16G16_FLOAT,
    R16G16_UINT,
    R16G16_SINT,
    R16G16_SNORM,
    R32G32B32_FLOAT,
    A8B8G8R8_SRGB,
    R8G8_UNORM,
    R8G8_SNORM,
    R8G8_SINT,
    R8G8_UINT,
    R32G32_UINT,
    R16G16B16X16_FLOAT,
    R32_UINT,
    R32_SINT,
    ASTC_2D_8X8_UNORM,
    ASTC_2D_8X5_UNORM,
    ASTC_2D_5X4_UNORM,
    B8G8R8A8_SRGB,
    BC1_RGBA_SRGB,
    BC2_SRGB,
    BC3_SRGB,
    BC7_SRGB,
    A4B4G4R4_UNORM,
    G4R4_UNORM,
    ASTC_2D_4X4_SRGB,
    ASTC_2D_8X8_SRGB,
    ASTC_2D_8X5_SRGB,
    ASTC_2D_5X4_SRGB,
    ASTC_2D_5X5_UNORM,
    ASTC_2D_5X5_SRGB,
    ASTC_2D_10X8_UNORM,
    ASTC_2D_10X8_SRGB,
    ASTC_2D_6X6_UNORM,
    ASTC_2D_6X6_SRGB,
    ASTC_2D_10X6_UNORM,
    ASTC_2D_10X6_SRGB,
    ASTC_2D_10X5_UNORM,
    ASTC_2D_10X5_SRGB,
    ASTC_2D_10X10_UNORM,
    ASTC_2D_10X10_SRGB,
    ASTC_2D_12X10_UNORM,
    ASTC_2D_12X10_SRGB,
    ASTC_2D_12X12_UNORM,
    ASTC_2D_12X12_SRGB,
    ASTC_2D_8X6_UNORM,
    ASTC_2D_8X6_SRGB,
    ASTC_2D_6X5_UNORM,
    ASTC_2D_6X5_SRGB,
    E5B9G9R9_FLOAT,
    D32_FLOAT,
    D16_UNORM,
    X8_D24_UNORM,
    S8_UINT,
    D24_UNORM_S8_UINT,
    S8_UINT_D24_UNORM,
    D32_FLOAT_S8_UINT,
};
enum ReplaceConstant:u32 {
    BaseInstance,
    BaseVertex,
    DrawID,
};

struct text {
    u32 key;
    TextureType type;
};
struct tpxf {
    u32 key;
    TexturePixelFormat fmt;
};
struct cbuf {
    u32 key[2];
    u32 value;
};
struct cbufr {
    u32 key[2];
    ReplaceConstant rep;
};

struct env {
    u64 code_size;
    u64 num_texture_types;
    u64 num_texture_pixel_formats;
    u64 num_cbuf_values;
    u64 num_cbuf_replacement_values;
    u32 local_mem_size;
    u32 texture_bound;
    u32 start_address;
    u32 cached_lowest;
    u32 cache_highest;
    u32 viewform_transport_state;
    Stage stage;
    char code[code_size];
    text texs[num_texture_types];
    tpxf tpxf[num_texture_pixel_formats];
    cbuf cbuf[num_cbuf_values];
    cbufr cbufr[num_cbuf_replacement_values];

    if (stage == Stage::Compute) {
        u32 workgroup_size[3];
        u32 shared_mem_size;
    } else {
        u8 sph[80];
        if (stage == Stage::Geometry) u32 gp_passthrough_ask[8];
    }
};

struct ckey {
};

bitfield BlendingAttachment {
    mask_r:1;
    mask_g:1;
    mask_b:1;
    mask_a:1;
    equation_rgb:3;
    equation_a:3;
    factor_source_rgb:5;
    factor_dest_rgb:5;
    factor_source_a:5;
    factor_dest_a:5;
    enable:1;
    padding:1;
};
bitfield VertexAttribute {
    enabled:1;
    buffer:5;
    offset:14;
    type:3;
    size:6;
    padding:3;
};
bitfield DynamicState {
    cull_face:2;
    cull_enable:1;
    primitive_restart_enable:1;
    depth_bias_enable:1;
    rasterize_enable:1;
    logic_op:4;
    logic_op_enable:1;
    depth_clamp_disabled:1;
    line_stipple_enable:1;
    padding:19;

    front:12;
    back:12;
    stencil_enable:1;
    depth_write_enable:1;
    depth_bounds_enable:1;
    depth_test_enable:1;
    front_face:1;
    depth_test_func:3;
};
bitfield g {
    extended_dynamic_state:1;
    extended_dynamic_state_2:1;
    extended_dynamic_state_2_logic_op:1;
    extended_dynamic_state_3_blend:1;
    extended_dynamic_state_3_enables:1;
    dynamic_vertex_input:1;
    xfb_enabled:1;
    ndc_minus_one_to_one:1;
    polygon_mode:2;
    tessellation_primitive:2;
    tessellation_spacing:2;
    tessellation_clockwise:1;
    patch_control_points_minus_one:5;
    padding:4;
    topology:4;
    msaa_mode:4;

    padding:1;
    alpha_test_func:3;
    early_z:1;
    depth_enabled:1;
    depth_format:5;
    y_negate:1;
    provoking_vertex_last:1;
    conservative_raster_enable:1;
    smooth_lines:1;
    alpha_to_coverage_enabled:1;
    alpha_to_one_enabled:1;
    app_stage:3;
    padding:12;
};
struct XFBLayout {
    u32 stream;
    u32 varying_count;
    u32 stride;
};
struct gkey {
    u64 hashes[6];
    g g;
    u8 color_formats[8];
    u32 alpha_test_ref;
    u32 point_size;
    u16 viewport_swizzles[16];
    u64 attribute_types;
    u64 enabled_divisors;
    DynamicState dynamic_state;
    BlendingAttachment attachments[8];
    VertexAttribute attributes[32];
    u32 binding_divisors[32];
    u16 vertex_strides[32];
    XFBLayout xfb_layouts[4];
    u32 xfb_varyings[4*32];
    u32 depth_bounds_min;
    u32 depth_bounds_max;
    u32 line_stipple_factor;
    u32 line_stipple_pattern;
    $ -= 8;
};

struct e {
    u32 num_envs;
    env envs[num_envs];
    if (envs[0].stage == Stage::Compute) ckey key;
    else gkey key;
};
struct a {
    char magic[8];
    u32 version;
    e e[2];
};

a a @ 0;