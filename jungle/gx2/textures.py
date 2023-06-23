
class GX2AAMode:
	MODE1X = 0
	MODE2X = 1
	MODE4X = 2


class GX2SurfaceDim:
	TEXTURE_1D = 0
	TEXTURE_2D = 1
	TEXTURE_3D = 2
	TEXTURE_CUBE = 3
	TEXTURE_1D_ARRAY = 4
	TEXTURE_2D_ARRAY = 5
	TEXTURE_2D_MSAA = 6
	TEXTURE_2D_MSAA_ARRAY = 7


class GX2SurfaceFormat:
	INVALID = 0
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


class GX2SurfaceType:
  UNORM = 0
  UINT = 1
  SNORM = 2
  SINT = 3
  SRGB = 4
  FLOAT = 8


class GX2SurfaceUse:
	NONE = 0
	TEXTURE = 1
	COLOR_BUFFER = 2
	DEPTH_BUFFER = 4
	SCAN_BUFFER = 8
	TV = 1 << 31


class GX2TileMode:
	DEFAULT = 0
	LINEAR_ALIGNED = 1
	TILED_1D_THIN1 = 2
	TILED_1D_THICK = 3
	TILED_2D_THIN1 = 4
	TILED_2D_THIN2 = 5
	TILED_2D_THIN4 = 6
	TILED_2D_THICK = 7
	TILED_2B_THIN1 = 8
	TILED_2B_THIN2 = 9
	TILED_2B_THIN4 = 10
	TILED_2B_THICK = 11
	TILED_3D_THIN1 = 12
	TILED_3D_THICK = 13
	TILED_3B_THIN1 = 14
	TILED_3B_THICK = 15
	LINEAR_SPECIAL = 16


class GX2Surface:
	def __init__(self):
		self.dim = GX2SurfaceDim.TEXTURE_2D
		self.width = 0
		self.height = 0
		self.depth = 0
		self.mip_levels = 0
		self.format = GX2SurfaceType.UNORM | GX2SurfaceFormat.R8_G8_B8_A8
		self.aa_mode = GX2AAMode.MODE1X
		self.use = GX2SurfaceUse.TEXTURE
		self.image = b""
		self.mipmaps = b""
		self.tile_mode = GX2TileMode.LINEAR_SPECIAL
		self.swizzle = 0
		self.alignment = 0
		self.pitch = 0
		self.mip_level_offset = [0] * 13


class GX2Texture:
	def __init__(self):
		self.surface = GX2Surface()
		self.view_first_mip = 0
		self.view_num_mips = 0
		self.view_first_slice = 0
		self.view_num_slices = 0
		self.comp_map = 0
		self.regs = [0] * 5
