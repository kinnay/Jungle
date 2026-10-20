
from dataclasses import dataclass, field

import enum


class GX2AAMode(enum.IntEnum):
    Mode1X = 0
    Mode2X = 1
    Mode4X = 2


class GX2SurfaceDim(enum.IntEnum):
    Texture1D = 0
    Texture2D = 1
    Texture3D = 2
    TextureCube = 3
    Texture1DArray = 4
    Texture2DArray = 5
    Texture2DMSAA = 6
    Texture2DMSAAArray = 7


class GX2SurfaceFormat(enum.IntEnum):
    Invalid = 0
    R8 = 1
    R4_G4 = 2
    R16 = 5
    R16_F = 6
    R8_G8 = 7
    R5_G6_B5 = 8
    R5_G5_B5_A1 = 10
    R4_G4_B4_A4 = 11
    A1_B5_G5_R5 = 12
    R32 = 13
    R32_F = 14
    R16_G16 = 15
    R16_G16_F = 16
    R24_X8 = 17
    R11_G11_B10 = 22
    R10_G10_B10_A2 = 25
    R8_G8_B8_A8 = 26
    A2_B10_G10_R10 = 27
    G8_X24 = 28
    R32_G32 = 29
    R32_G32_F = 30
    R16_G16_B16_A16 = 31
    R16_G16_B16_A16_F = 32
    R32_G32_B32_A32 = 34
    R32_G32_B32_A32_F = 35
    BC1 = 49
    BC2 = 50
    BC3 = 51
    BC4 = 52
    BC5 = 53
    NV12 = 129


class GX2SurfaceType(enum.IntEnum):
  UNORM = 0
  UINT = 1
  SNORM = 2
  SINT = 3
  SRGB = 4
  FLOAT = 8


class GX2SurfaceUse(enum.IntFlag):
    Texture = 1
    ColorBuffer = 2
    DepthBuffer = 4
    ScanBuffer = 8
    TV = 1 << 31


class GX2TileMode(enum.IntEnum):
    Default = 0
    LinearAligned = 1
    Tiled1DThin1 = 2
    Tiled1DThick = 3
    Tiled2DThin1 = 4
    Tiled2DThin2 = 5
    Tiled2DThin4 = 6
    Tiled2DThick = 7
    Tiled2BThin1 = 8
    Tiled2BThin2 = 9
    Tiled2BThin4 = 10
    Tiled2BThick = 11
    Tiled3DThin1 = 12
    Tiled3DThick = 13
    Tiled3BThin1 = 14
    Tiled3BThick = 15
    LinearSpecial = 16


@dataclass
class GX2Surface:
    dim: GX2SurfaceDim = GX2SurfaceDim.Texture2D
    width: int = 0
    height: int = 0
    depth: int = 0
    mip_levels: int = 0
    type: GX2SurfaceType = GX2SurfaceType.UNORM
    format: GX2SurfaceFormat = GX2SurfaceFormat.R8_G8_B8_A8
    aa_mode: GX2AAMode = GX2AAMode.Mode1X
    use: GX2SurfaceUse = GX2SurfaceUse.Texture
    image: bytes = b""
    mipmaps: bytes = b""
    tile_mode: GX2TileMode = GX2TileMode.LinearSpecial
    swizzle: int = 0
    alignment: int = 0
    pitch: int = 0
    mip_level_offset: list[int] = field(default_factory=lambda: [0] * 13)


@dataclass
class GX2Texture:
    surface: GX2Surface = field(default_factory=GX2Surface)
    view_first_mip: int = 0
    view_num_mips: int = 0
    view_first_slice: int = 0
    view_num_slices: int = 0
    comp_map: int = 0
    regs: list[int] = field(default_factory=lambda: [0] * 5)
