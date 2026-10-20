
from dataclasses import dataclass, field

import enum


class GX2SamplerVarType(enum.IntEnum):
    Sampler1D = 0
    Sampler2D = 1
    Sampler3D = 3
    SamplerCube = 4


class GX2ShaderMode(enum.IntEnum):
    UniformRegister = 0
    UniformBlock = 1
    GeometryShader = 2
    ComputeShader = 3


class GX2ShaderVarType(enum.IntEnum):
    Void = 0
    Bool = 1
    Int = 2
    Uint = 3
    Float = 4
    Double = 5
    Double2 = 6
    Double3 = 7
    Double4 = 8
    Float2 = 9
    Float3 = 10
    Float4 = 11
    Bool2 = 12
    Bool3 = 13
    Bool4 = 14
    Int2 = 15
    Int3 = 16
    Int4 = 17
    Uint2 = 18
    Uint3 = 19
    Uint4 = 20
    Float2X2 = 21
    Float2X3 = 22
    Float2X4 = 23
    Float3X2 = 24
    Float3X3 = 25
    Float3X4 = 26
    Float4X2 = 27
    Float4X3 = 28
    Float4X4 = 29
    Double2X2 = 30
    Double2X3 = 31
    Double2X4 = 32
    Double3X2 = 33
    Double3X3 = 34
    Double3X4 = 35
    Double4X2 = 36
    Double4X3 = 37
    Double4X4 = 38


@dataclass
class GX2UniformBlock:
    name: str = ""
    offset: int = 0
    size: int = 0


@dataclass
class GX2UniformVar:
    name: str = ""
    type: GX2ShaderVarType = GX2ShaderVarType.Void
    count: int = 0
    offset: int = 0
    block: int = 0


@dataclass
class GX2UniformInitialValue:
    value: list[float] = field(default_factory=lambda: [.0] * 4)
    offset: int = 0


@dataclass
class GX2LoopVar:
    offset: int = 0
    value: int = 0


@dataclass
class GX2SamplerVar:
    name: str = ""
    type: GX2SamplerVarType = GX2SamplerVarType.Sampler2D
    location: int = 0


@dataclass
class GX2AttribVar:
    name: str = ""
    type: GX2ShaderVarType = GX2ShaderVarType.Void
    count: int = 0
    location: int = 0


@dataclass
class GX2VertexShader:
    regs: list[int] = field(default_factory=lambda: [0] * 52)
    program: bytes = b""
    mode: GX2ShaderMode = GX2ShaderMode.UniformRegister
    uniform_blocks: list[GX2UniformBlock] = field(default_factory=list)
    uniform_vars: list[GX2UniformVar] = field(default_factory=list)
    initial_values: list[GX2UniformInitialValue] = field(default_factory=list)
    loop_vars: list[GX2LoopVar] = field(default_factory=list)
    sampler_vars: list[GX2SamplerVar] = field(default_factory=list)
    attrib_vars: list[GX2AttribVar] = field(default_factory=list)
    ring_item_size: int = 0
    has_stream_out: bool = False
    stream_out_stride: list[int] = field(default_factory=lambda: [0] * 4)


@dataclass
class GX2PixelShader:
    regs: list[int] = field(default_factory=lambda: [0] * 41)
    program: bytes = b""
    mode: GX2ShaderMode = GX2ShaderMode.UniformRegister
    uniform_blocks: list[GX2UniformBlock] = field(default_factory=list)
    uniform_vars: list[GX2UniformVar] = field(default_factory=list)
    initial_values: list[GX2UniformInitialValue] = field(default_factory=list)
    loop_vars: list[GX2LoopVar] = field(default_factory=list)
    sampler_vars: list[GX2SamplerVar] = field(default_factory=list)


@dataclass
class GX2GeometryShader:
    regs: list[int] = field(default_factory=lambda: [0] * 19)
    program: bytes = b""
    vertex_program: bytes = b""
    mode: GX2ShaderMode = GX2ShaderMode.GeometryShader
    uniform_blocks: list[GX2UniformBlock] = field(default_factory=list)
    uniform_vars: list[GX2UniformVar] = field(default_factory=list)
    initial_values: list[GX2UniformInitialValue] = field(default_factory=list)
    loop_vars: list[GX2LoopVar] = field(default_factory=list)
    sampler_vars: list[GX2SamplerVar] = field(default_factory=list)
    ring_item_size: int = 0
    has_stream_out: bool = False
    stream_out_stride: list[int] = field(default_factory=lambda: [0] * 4)
