
from jungle.error import ParseError, SaveError
from jungle.gx2 import texture
from jungle import streams


class BlockType:
	EOF = 1
	PADDING = 2
	VSHADER = 3
	VSHADER_PROGRAM = 5
	PSHADER = 6
	PSHADER_PROGRAM = 7
	GSHADER = 8
	GSHADER_PROGRAM = 9
	GSHADER_COPY_PROGRAM = 10
	TEXTURE = 11
	TEXTURE_DATA = 12
	TEXTURE_MIPMAP_DATA = 13


class Block:
	def __init__(self):
		self.type = BlockType.EOF
		self.data = b""
	
	def parse(self, stream):
		if stream.ascii(4) != "BLK{": raise ParseError("block has invalid magic number")
		if stream.u32() != 32: raise ParseError("block has invalid header size")
		if stream.u32() != 1: raise ParseError("block has unsupported major version")
		if stream.u32() != 0: raise ParseError("block has unsupported minor version")
		self.type = stream.u32()
		size = stream.u32()
		stream.pad(8)
		self.data = stream.read(size)
	
	def save(self, stream):
		stream.ascii("BLK{")
		stream.u32(32)
		stream.u32(1)
		stream.u32(0)
		stream.u32(self.type)
		stream.u32(len(self.data))
		stream.pad(8)
		stream.write(self.data)


class Gfx2File:
	def __init__(self):
		self.alignment = True
		self.textures = []
	
	def parse(self, data):
		stream = streams.StreamIn(data, ">")
		if stream.ascii(4) != "Gfx2": raise ParseError("magic number is invalid")
		if stream.u32() != 32: raise ParseError("header size is invalid")
		if stream.u32() != 7: raise ParseError("unsupported major version")
		if stream.u32() != 1: raise ParseError("unsupported minor version")
		if stream.u32() != 2: raise ParseError("unsupported gpu version")

		self.alignment = bool(stream.u32())
		stream.pad(8)

		blocks = []
		while True:
			block = Block()
			block.parse(stream)
			if block.type == BlockType.EOF:
				break
			blocks.append(block)
		
		self.textures = []

		texture = None
		for block in blocks:
			if block.type == BlockType.PADDING: pass
			elif block.type == BlockType.TEXTURE:
				texture = self.parse_texture(block.data)
				self.textures.append(texture)
			elif block.type == BlockType.TEXTURE_DATA:
				if texture is None:
					raise ParseError("unexpected texture data block")
				texture.surface.image = block.data
			elif block.type == BlockType.TEXTURE_MIPMAP_DATA:
				if texture is None:
					raise ParseError("unexpected texture mipmap block")
				texture.surface.mipmaps = block.data
			else:
				raise ParseError("unsupported block type: %i" %block.type)
	
	def parse_texture(self, data):
		stream = streams.StreamIn(data, ">")

		tex = texture.GX2Texture()
		tex.surface.dim = stream.u32()
		tex.surface.width = stream.u32()
		tex.surface.height = stream.u32()
		tex.surface.depth = stream.u32()
		tex.surface.mip_levels = stream.u32()
		tex.surface.format = stream.u32()
		tex.surface.aa_mode = stream.u32()
		tex.surface.use = stream.u32()
		stream.skip(16)
		tex.surface.tile_mode = stream.u32()
		tex.surface.swizzle = stream.u32()
		tex.surface.alignment = stream.u32()
		tex.surface.pitch = stream.u32()
		tex.surface.mip_level_offset = stream.repeat(stream.u32, 13)

		tex.view_first_mip = stream.u32()
		tex.view_num_mips = stream.u32()
		tex.view_first_slice = stream.u32()
		tex.view_num_slices = stream.u32()
		tex.comp_map = stream.u32()
		tex.regs = stream.repeat(stream.u32, 5)
		return tex

	def save(self):
		stream = streams.StreamOut(">")
		stream.ascii("Gfx2")
		stream.u32(32)
		stream.u32(7)
		stream.u32(1)
		stream.u32(2)
		stream.u32(self.alignment)
		stream.pad(8)

		for texture in self.textures:
			block = Block()
			block.type = BlockType.TEXTURE
			block.data = self.save_texture(texture)
			block.save(stream)

			self.pad(stream, texture.surface.alignment)

			block = Block()
			block.type = BlockType.TEXTURE_DATA
			block.data = texture.surface.image
			block.save(stream)

			if texture.surface.mipmaps:
				self.pad(stream, texture.surface.alignment)

				block = Block()
				block.type = BlockType.TEXTURE_MIPMAP_DATA
				block.data = texture.surface.mipmaps
				block.save(stream)
		
		block = Block()
		block.type = BlockType.EOF
		block.save(stream)
		
		return stream.get()
	
	def pad(self, stream, alignment):
		pos = stream.tell() + 32
		padding = (alignment - pos % alignment) % alignment
		if padding and self.alignment:
			padding = (padding - 32) % alignment
			
			block = Block()
			block.type = BlockType.PADDING
			block.data = bytes(padding)
			block.save(stream)
	
	def save_texture(self, texture):
		stream = streams.StreamOut(">")
		stream.u32(texture.surface.dim)
		stream.u32(texture.surface.width)
		stream.u32(texture.surface.height)
		stream.u32(texture.surface.depth)
		stream.u32(texture.surface.mip_levels)
		stream.u32(texture.surface.format)
		stream.u32(texture.surface.aa_mode)
		stream.u32(texture.surface.use)
		stream.u32(len(texture.surface.image))
		stream.pad(4)
		stream.u32(len(texture.surface.mipmaps))
		stream.pad(4)
		stream.u32(texture.surface.tile_mode)
		stream.u32(texture.surface.swizzle)
		stream.u32(texture.surface.alignment)
		stream.u32(texture.surface.pitch)
		stream.repeat(texture.surface.mip_level_offset, stream.u32)

		stream.u32(texture.view_first_mip)
		stream.u32(texture.view_num_mips)
		stream.u32(texture.view_first_slice)
		stream.u32(texture.view_num_slices)
		stream.u32(texture.comp_map)
		stream.repeat(texture.regs, stream.u32)
		return stream.get()
