
class GX2SamplerVarType:
    SAMPLER_1D = 0
    SAMPLER_2D = 1
    SAMPLER_3D = 3
    SAMPLER_CUBE = 4


class GX2ShaderMode:
    UNIFORM_REGISTER = 0
    UNIFORM_BLOCK = 1
    GEOMETRY_SHADER = 2
    COMPUTE_SHADER = 3


class GX2ShaderVarType:
    VOID = 0
    BOOL = 1
    INT = 2
    UINT = 3
    FLOAT = 4
    DOUBLE = 5
    DOUBLE2 = 6
    DOUBLE3 = 7
    DOUBLE4 = 8
    FLOAT2 = 9
    FLOAT3 = 10
    FLOAT4 = 11
    BOOL2 = 12
    BOOL3 = 13
    BOOL4 = 14
    INT2 = 15
    INT3 = 16
    INT4 = 17
    UINT2 = 18
    UINT3 = 19
    UINT4 = 20
    FLOAT2X2 = 21
    FLOAT2X3 = 22
    FLOAT2X4 = 23
    FLOAT3X2 = 24
    FLOAT3X3 = 25
    FLOAT3X4 = 26
    FLOAT4X2 = 27
    FLOAT4X3 = 28
    FLOAT4X4 = 29
    DOUBLE2X2 = 30
    DOUBLE2X3 = 31
    DOUBLE2X4 = 32
    DOUBLE3X2 = 33
    DOUBLE3X3 = 34
    DOUBLE3X4 = 35
    DOUBLE4X2 = 36
    DOUBLE4X3 = 37
    DOUBLE4X4 = 38


class GX2UniformBlock:
    def __init__(self):
        self.name = ""
        self.offset = 0
        self.size = 0


class GX2UniformVar:
    def __init__(self):
        self.name = ""
        self.type = GX2ShaderVarType.VOID
        self.count = 0
        self.offset = 0
        self.block = 0


class GX2UniformInitialValue:
    def __init__(self):
        self.value = [.0] * 4
        self.offset = 0


class GX2LoopVar:
    def __init__(self):
        self.offset = 0
        self.value = 0


class GX2SamplerVar:
    def __init__(self):
        self.name = ""
        self.type = GX2SamplerVarType.SAMPLER_2D
        self.location = 0


class GX2AttribVar:
    def __init__(self):
        self.name = ""
        self.type = GX2ShaderVarType.VOID
        self.count = 0
        self.location = 0


class GX2VertexShader:
    def __init__(self):
        self.regs = [0] * 52
        self.program = b""
        self.mode = GX2ShaderMode.UNIFORM_REGISTER
        self.uniform_blocks = []
        self.uniform_vars = []
        self.initial_values = []
        self.loop_vars = []
        self.sampler_vars = []
        self.attrib_vars = []
        self.ring_item_size = 0
        self.has_stream_out = False
        self.stream_out_stride = [0] * 4


class GX2PixelShader:
    def __init__(self):
        self.regs = [0] * 41
        self.program = b""
        self.mode = GX2ShaderMode.UNIFORM_REGISTER
        self.uniform_blocks = []
        self.uniform_vars = []
        self.initial_values = []
        self.loop_vars = []
        self.sampler_vars = []


class GX2GeometryShader:
    def __init__(self):
        self.regs = [0] * 19
        self.program = b""
        self.vertex_program = b""
        self.mode = GX2ShaderMode.GEOMETRY_SHADER
        self.uniform_blocks = []
        self.uniform_vars = []
        self.initial_values = []
        self.loop_vars = []
        self.sampler_vars = []
        self.ring_item_size = 0
        self.has_stream_out = False
        self.stream_out_stride = [0] * 4
