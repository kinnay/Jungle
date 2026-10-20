
from dataclasses import dataclass
from jungle.errors import ParseError
from jungle.gx2.shaders import *
from jungle.gx2.textures import *
from jungle.streams import StreamIn, StreamOut
from jungle import utils

import enum


class Tag(enum.IntEnum):
    Data = 0xD0600000
    String = 0xCA700000


class BlockType(enum.IntEnum):
    End = 1
    Padding = 2
    VertexShader = 3
    VertexShaderProgram = 5
    PixelShader = 6
    PixelShaderProgram = 7
    GeometryShader = 8
    GeometryShaderProgram = 9
    GeometryShaderCopyProgram = 10
    Texture = 11
    TextureData = 12
    TextureMipmapData = 13


@dataclass
class Block:
    type: BlockType = BlockType.End
    data: bytes = b""

    def parse(self, stream: StreamIn) -> None:
        if stream.ascii(4) != "BLK{":
            raise ParseError("block has invalid magic number")
        if stream.u32() != 32:
            raise ParseError("block has invalid header size")
        if stream.u32() != 1:
            raise ParseError("block has unsupported major version")
        if stream.u32() != 0:
            raise ParseError("block has unsupported minor version")
        self.type = utils.parse_enum(stream.u32(), BlockType)
        size = stream.u32()
        stream.pad(8)
        self.data = stream.read(size)
    
    def save(self, stream: StreamOut) -> None:
        stream.ascii("BLK{")
        stream.u32(32)
        stream.u32(1)
        stream.u32(0)
        stream.u32(self.type)
        stream.u32(len(self.data))
        stream.pad(8)
        stream.write(self.data)


class RelocatableStreamOut(StreamOut):
    """Stream class that implements relocations."""

    _pointers: dict[int, int | None]

    def __init__(self, endianness: str):
        super().__init__(endianness)
        self._pointers = {}
    
    def pointer(self, offset: int) -> None:
        self._pointers[self.tell()] = offset
        self.skip(4)
    
    def null_pointer(self) -> None:
        self._pointers[self.tell()] = None
        self.u32(0)
    
    def pointer_count(self) -> int:
        return len(self._pointers)

    def relocate(
        self, relocation_stream: StreamOut, source_base: int,
        target_base: int, tag: Tag
    ) -> None:
        self.push()
        for source_offset, target_offset in self._pointers.items():
            if target_offset is not None:
                self.seek(source_offset)
                self.u32((target_base + target_offset) | tag)
                relocation_stream.u32((source_base + source_offset) | Tag.Data)
            else:
                relocation_stream.u32(0)
        self.pop()


class Gfx2File:
    alignment: bool
    textures: list[GX2Texture]
    vertex_shaders: list[GX2VertexShader]
    pixel_shaders: list[GX2PixelShader]
    geometry_shaders: list[GX2GeometryShader]

    def __init__(self):
        self.alignment = True
        self.textures = []
        self.vertex_shaders = []
        self.pixel_shaders = []
        self.geometry_shaders = []
    
    def parse(self, data: bytes) -> None:
        stream = StreamIn(data, ">")

        # Parse header
        if stream.ascii(4) != "Gfx2":
            raise ParseError("magic number is invalid")
        if stream.u32() != 32: raise ParseError("header size is invalid")
        if stream.u32() != 7: raise ParseError("unsupported major version")
        if stream.u32() != 1: raise ParseError("unsupported minor version")
        if stream.u32() != 2: raise ParseError("unsupported gpu version")
        self.alignment = bool(stream.u32())
        stream.pad(8)

        # Parse block headers
        blocks: dict[BlockType, list[bytes]] = {
            BlockType.Padding: [],
            BlockType.VertexShader: [],
            BlockType.VertexShaderProgram: [],
            BlockType.PixelShader: [],
            BlockType.PixelShaderProgram: [],
            BlockType.GeometryShader: [],
            BlockType.GeometryShaderProgram: [],
            BlockType.GeometryShaderCopyProgram: [],
            BlockType.Texture: [],
            BlockType.TextureData: [],
            BlockType.TextureMipmapData: []
        }
        while True:
            block = Block()
            block.parse(stream)
            if block.type == BlockType.End: break
            elif block.type in blocks:
                blocks[block.type].append(block.data)
            else:
                raise ParseError("unknown block type")
        
        # A gtx file may have a texture without mipmaps
        while len(blocks[BlockType.Texture]) > \
              len(blocks[BlockType.TextureMipmapData]):
            blocks[BlockType.TextureMipmapData].append(b"")

        # Verify that the number of data blocks matches the number of header
        # blocks
        if len(blocks[BlockType.VertexShader]) != \
           len(blocks[BlockType.VertexShaderProgram]):
            raise ParseError("wrong number of vertex shader blocks")
        if len(blocks[BlockType.PixelShader]) != \
           len(blocks[BlockType.PixelShaderProgram]):
            raise ParseError("wrong number of pixel shader blocks")
        if len(blocks[BlockType.GeometryShader]) != \
           len(blocks[BlockType.GeometryShaderProgram]):
            raise ParseError("wrong number of geometry shader blocks")
        if len(blocks[BlockType.GeometryShader]) != \
           len(blocks[BlockType.GeometryShaderCopyProgram]):
            raise ParseError("wrong number of geometry copy shader blocks")
        if len(blocks[BlockType.Texture]) != len(blocks[BlockType.TextureData]):
            raise ParseError("wrong number of texture data blocks")
        if len(blocks[BlockType.Texture]) != \
           len(blocks[BlockType.TextureMipmapData]):
            raise ParseError("wrong number of texture mipmap blocks")
        
        # Parse texture blocks
        self.textures = []
        for i in range(len(blocks[BlockType.Texture])):
            texture = self._parse_texture(blocks[BlockType.Texture][i])
            texture.surface.image = blocks[BlockType.TextureData][i]
            texture.surface.mipmaps = blocks[BlockType.TextureMipmapData][i]
            self.textures.append(texture)
        
        # Parse vertex shader blocks
        self.vertex_shaders = []
        for i in range(len(blocks[BlockType.VertexShader])):
            vshader = self._parse_vshader(blocks[BlockType.VertexShader][i])
            vshader.program = blocks[BlockType.VertexShaderProgram][i]
            self.vertex_shaders.append(vshader)
        
        # Parse pixel shader blocks
        self.pixel_shaders = []
        for i in range(len(blocks[BlockType.PixelShader])):
            pshader = self._parse_pshader(blocks[BlockType.PixelShader][i])
            pshader.program = blocks[BlockType.PixelShaderProgram][i]
            self.pixel_shaders.append(pshader)
        
        # Parse geometry shader blocks
        self.geometry_shaders = []
        for i in range(len(blocks[BlockType.GeometryShader])):
            gshader = self._parse_gshader(blocks[BlockType.GeometryShader][i])
            gshader.program = blocks[BlockType.GeometryShaderProgram][i]
            gshader.vertex_program = \
                blocks[BlockType.GeometryShaderCopyProgram][i]
            self.geometry_shaders.append(gshader)

    def _parse_texture(self, data: bytes) -> GX2Texture:
        stream = StreamIn(data, ">")

        texture = GX2Texture()
        texture.surface.dim = utils.parse_enum(stream.u32(), GX2SurfaceDim)
        texture.surface.width = stream.u32()
        texture.surface.height = stream.u32()
        texture.surface.depth = stream.u32()
        texture.surface.mip_levels = stream.u32()

        format = stream.u32()
        texture.surface.type = utils.parse_enum(format >> 8, GX2SurfaceType)
        texture.surface.format = \
            utils.parse_enum(format & 0xFF, GX2SurfaceFormat)

        texture.surface.aa_mode = utils.parse_enum(stream.u32(), GX2AAMode)
        texture.surface.use = utils.parse_flags(stream.u32(), GX2SurfaceUse)
        stream.skip(16)
        texture.surface.tile_mode = utils.parse_enum(stream.u32(), GX2TileMode)
        texture.surface.swizzle = stream.u32()
        texture.surface.alignment = stream.u32()
        texture.surface.pitch = stream.u32()
        texture.surface.mip_level_offset = stream.repeat(stream.u32, 13)

        texture.view_first_mip = stream.u32()
        texture.view_num_mips = stream.u32()
        texture.view_first_slice = stream.u32()
        texture.view_num_slices = stream.u32()
        texture.comp_map = stream.u32()
        texture.regs = stream.repeat(stream.u32, 5)
        return texture

    def _parse_vshader(self, data: bytes) -> GX2VertexShader:
        stream = StreamIn(data, ">")

        shader = GX2VertexShader()
        shader.regs = stream.repeat(stream.u32, 52)
        stream.skip(8)
        shader.mode = utils.parse_enum(stream.u32(), GX2ShaderMode)
        
        uniform_block_count = stream.u32()
        uniform_block_offset = stream.u32()
        uniform_var_count = stream.u32()
        uniform_var_offset = stream.u32()
        initial_value_count = stream.u32()
        initial_value_offset = stream.u32()
        loop_var_count = stream.u32()
        loop_var_offset = stream.u32()
        sampler_var_count = stream.u32()
        sampler_var_offset = stream.u32()
        attrib_var_count = stream.u32()
        attrib_var_offset = stream.u32()

        shader.ring_item_size = stream.u32()
        shader.has_stream_out = bool(stream.u32())
        shader.stream_out_stride = stream.repeat(stream.u32, 4)
        stream.pad(16)

        stream.seek(uniform_block_offset & 0xFFFFF)
        for i in range(uniform_block_count):
            shader.uniform_blocks.append(self._parse_uniform_block(stream))
        
        stream.seek(uniform_var_offset & 0xFFFFF)
        for i in range(uniform_var_count):
            shader.uniform_vars.append(self._parse_uniform_var(stream))
        
        stream.seek(initial_value_offset & 0xFFFFF)
        for i in range(initial_value_count):
            shader.initial_values.append(self._parse_initial_value(stream))
        
        stream.seek(loop_var_offset & 0xFFFFF)
        for i in range(loop_var_count):
            shader.loop_vars.append(self._parse_loop_var(stream))
        
        stream.seek(sampler_var_offset & 0xFFFFF)
        for i in range(sampler_var_count):
            shader.sampler_vars.append(self._parse_sampler_var(stream))
        
        stream.seek(attrib_var_offset & 0xFFFFF)
        for i in range(attrib_var_count):
            shader.attrib_vars.append(self._parse_attrib_var(stream))

        return shader

    def _parse_pshader(self, data: bytes) -> GX2PixelShader:
        stream = StreamIn(data, ">")

        shader = GX2PixelShader()
        shader.regs = stream.repeat(stream.u32, 41)
        stream.skip(8)
        shader.mode = utils.parse_enum(stream.u32(), GX2ShaderMode)
        
        uniform_block_count = stream.u32()
        uniform_block_offset = stream.u32()
        uniform_var_count = stream.u32()
        uniform_var_offset = stream.u32()
        initial_value_count = stream.u32()
        initial_value_offset = stream.u32()
        loop_var_count = stream.u32()
        loop_var_offset = stream.u32()
        sampler_var_count = stream.u32()
        sampler_var_offset = stream.u32()
        stream.pad(16)

        stream.seek(uniform_block_offset & 0xFFFFF)
        for i in range(uniform_block_count):
            shader.uniform_blocks.append(self._parse_uniform_block(stream))
        
        stream.seek(uniform_var_offset & 0xFFFFF)
        for i in range(uniform_var_count):
            shader.uniform_vars.append(self._parse_uniform_var(stream))
        
        stream.seek(initial_value_offset & 0xFFFFF)
        for i in range(initial_value_count):
            shader.initial_values.append(self._parse_initial_value(stream))
        
        stream.seek(loop_var_offset & 0xFFFFF)
        for i in range(loop_var_count):
            shader.loop_vars.append(self._parse_loop_var(stream))
        
        stream.seek(sampler_var_offset & 0xFFFFF)
        for i in range(sampler_var_count):
            shader.sampler_vars.append(self._parse_sampler_var(stream))

        return shader

    def _parse_gshader(self, data: bytes) -> GX2GeometryShader:
        stream = StreamIn(data, ">")

        shader = GX2GeometryShader()
        shader.regs = stream.repeat(stream.u32, 19)
        stream.skip(16)
        shader.mode = utils.parse_enum(stream.u32(), GX2ShaderMode)
        
        uniform_block_count = stream.u32()
        uniform_block_offset = stream.u32()
        uniform_var_count = stream.u32()
        uniform_var_offset = stream.u32()
        initial_value_count = stream.u32()
        initial_value_offset = stream.u32()
        loop_var_count = stream.u32()
        loop_var_offset = stream.u32()
        sampler_var_count = stream.u32()
        sampler_var_offset = stream.u32()

        shader.ring_item_size = stream.u32()
        shader.has_stream_out = bool(stream.u32())
        shader.stream_out_stride = stream.repeat(stream.u32, 4)
        stream.pad(16)

        stream.seek(uniform_block_offset & 0xFFFFF)
        for i in range(uniform_block_count):
            shader.uniform_blocks.append(self._parse_uniform_block(stream))
        
        stream.seek(uniform_var_offset & 0xFFFFF)
        for i in range(uniform_var_count):
            shader.uniform_vars.append(self._parse_uniform_var(stream))
        
        stream.seek(initial_value_offset & 0xFFFFF)
        for i in range(initial_value_count):
            shader.initial_values.append(self._parse_initial_value(stream))
        
        stream.seek(loop_var_offset & 0xFFFFF)
        for i in range(loop_var_count):
            shader.loop_vars.append(self._parse_loop_var(stream))
        
        stream.seek(sampler_var_offset & 0xFFFFF)
        for i in range(sampler_var_count):
            shader.sampler_vars.append(self._parse_sampler_var(stream))

        return shader

    def _parse_uniform_block(self, stream: StreamIn) -> GX2UniformBlock:
        block = GX2UniformBlock()
        block.name = stream.string_at(stream.u32() & 0xFFFFF)
        block.offset = stream.u32()
        block.size = stream.u32()
        return block

    def _parse_uniform_var(self, stream: StreamIn) -> GX2UniformVar:
        var = GX2UniformVar()
        var.name = stream.string_at(stream.u32() & 0xFFFFF)
        var.type = utils.parse_enum(stream.u32(), GX2ShaderVarType)
        var.count = stream.u32()
        var.offset = stream.u32()
        var.block = stream.s32()
        return var
    
    def _parse_initial_value(
        self, stream: StreamIn
    ) -> GX2UniformInitialValue:
        value = GX2UniformInitialValue()
        value.value = stream.repeat(stream.float, 4)
        value.offset = stream.u32()
        return value
    
    def _parse_loop_var(self, stream: StreamIn) -> GX2LoopVar:
        var = GX2LoopVar()
        var.offset = stream.u32()
        var.value = stream.u32()
        return var
    
    def _parse_sampler_var(self, stream: StreamIn) -> GX2SamplerVar:
        var = GX2SamplerVar()
        var.name = stream.string_at(stream.u32() & 0xFFFFF)
        var.type = utils.parse_enum(stream.u32(), GX2SamplerVarType)
        var.location = stream.u32()
        return var
    
    def _parse_attrib_var(self, stream: StreamIn) -> GX2AttribVar:
        var = GX2AttribVar()
        var.name = stream.string_at(stream.u32() & 0xFFFFF)
        var.type = utils.parse_enum(stream.u32(), GX2ShaderVarType)
        var.count = stream.u32()
        var.location = stream.u32()
        return var

    def save(self) -> bytes:
        # Write header
        stream = StreamOut(">")
        stream.ascii("Gfx2")
        stream.u32(32)
        stream.u32(7)
        stream.u32(1)
        stream.u32(2)
        stream.u32(self.alignment)
        stream.pad(8)

        # Write shaders
        count = max(
            len(self.vertex_shaders),
            len(self.pixel_shaders),
            len(self.geometry_shaders)
        )
        for i in range(count):
            if i < len(self.vertex_shaders):
                block = Block()
                block.type = BlockType.VertexShader
                block.data = self._save_shader(self.vertex_shaders[i])
                block.save(stream)

                self._pad(stream, 0x100)

                block = Block()
                block.type = BlockType.VertexShaderProgram
                block.data = self.vertex_shaders[i].program
                block.save(stream)
            
            if i < len(self.pixel_shaders):
                block = Block()
                block.type = BlockType.PixelShader
                block.data = self._save_shader(self.pixel_shaders[i])
                block.save(stream)

                self._pad(stream, 0x100)

                block = Block()
                block.type = BlockType.PixelShaderProgram
                block.data = self.pixel_shaders[i].program
                block.save(stream)
            
            if i < len(self.geometry_shaders):
                block = Block()
                block.type = BlockType.GeometryShader
                block.data = self._save_shader(self.geometry_shaders[i])
                block.save(stream)

                self._pad(stream, 0x100)

                block = Block()
                block.type = BlockType.GeometryShaderProgram
                block.data = self.geometry_shaders[i].program
                block.save(stream)

                self._pad(stream, 0x100)

                block = Block()
                block.type = BlockType.GeometryShaderCopyProgram
                block.data = self.geometry_shaders[i].vertex_program
                block.save(stream)
        
        # Write textures
        for texture in self.textures:
            block = Block()
            block.type = BlockType.Texture
            block.data = self._save_texture(texture)
            block.save(stream)

            self._pad(stream, texture.surface.alignment)

            block = Block()
            block.type = BlockType.TextureData
            block.data = texture.surface.image
            block.save(stream)

            if texture.surface.mipmaps:
                self._pad(stream, texture.surface.alignment)

                block = Block()
                block.type = BlockType.TextureMipmapData
                block.data = texture.surface.mipmaps
                block.save(stream)
        
        # Write EOF block
        block = Block()
        block.type = BlockType.End
        block.save(stream)

        return stream.get()
    
    def _pad(self, stream: StreamOut, alignment: int) -> None:
        pos = stream.tell() + 32
        padding = (alignment - pos % alignment) % alignment
        if padding and self.alignment:
            padding = (padding - 32) % alignment
            
            block = Block()
            block.type = BlockType.Padding
            block.data = bytes(padding)
            block.save(stream)
    
    def _save_texture(self, texture: GX2Texture) -> bytes:
        stream = StreamOut(">")
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

    def _save_shader(
        self, shader: GX2VertexShader | GX2PixelShader | GX2GeometryShader
    ) -> bytes:
        data_stream = RelocatableStreamOut(">")
        string_stream = StreamOut(">")

        stream = RelocatableStreamOut(">")
        stream.repeat(shader.regs, stream.u32)
        stream.u32(len(shader.program))
        stream.null_pointer()
        if isinstance(shader, GX2GeometryShader):
            stream.u32(len(shader.vertex_program))
            stream.null_pointer()
        stream.u32(shader.mode)

        stream.u32(len(shader.uniform_blocks))
        if shader.uniform_blocks:
            stream.pointer(data_stream.tell())
            for block in shader.uniform_blocks:
                self._save_uniform_block(block, data_stream, string_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.uniform_vars))
        if shader.uniform_vars:
            stream.pointer(data_stream.tell())
            for var in shader.uniform_vars:
                self._save_uniform_var(var, data_stream, string_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.initial_values))
        if shader.initial_values:
            stream.pointer(data_stream.tell())
            for value in shader.initial_values:
                self._save_initial_value(value, data_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.loop_vars))
        if shader.loop_vars:
            stream.pointer(data_stream.tell())
            for loop_var in shader.loop_vars:
                self._save_loop_var(loop_var, data_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.sampler_vars))
        if shader.sampler_vars:
            stream.pointer(data_stream.tell())
            for sampler_var in shader.sampler_vars:
                self._save_sampler_var(sampler_var, data_stream, string_stream)
        else:
            stream.null_pointer()
        
        if isinstance(shader, GX2VertexShader):
            stream.u32(len(shader.attrib_vars))
            if shader.attrib_vars:
                stream.pointer(data_stream.tell())
                for attrib_var in shader.attrib_vars:
                    self._save_attrib_var(
                        attrib_var, data_stream, string_stream
                    )
            else:
                stream.null_pointer()

        if isinstance(shader, (GX2VertexShader, GX2GeometryShader)):
            stream.u32(shader.ring_item_size)
            stream.u32(shader.has_stream_out)
            stream.repeat(shader.stream_out_stride, stream.u32)
        
        stream.pad(16)

        self._finish_shader(stream, data_stream, string_stream)

        return stream.get()
    
    def _save_uniform_block(
        self, block: GX2UniformBlock, stream: RelocatableStreamOut,
        string_stream: StreamOut
    ) -> None:
        stream.pointer(string_stream.tell())
        string_stream.string(block.name)
        string_stream.align(4)
        stream.u32(block.offset)
        stream.u32(block.size)
    
    def _save_uniform_var(
        self, var: GX2UniformVar, stream: RelocatableStreamOut,
        string_stream: StreamOut
    ) -> None:
        stream.pointer(string_stream.tell())
        string_stream.string(var.name)
        string_stream.align(4)
        stream.u32(var.type)
        stream.u32(var.count)
        stream.u32(var.offset)
        stream.s32(var.block)
    
    def _save_initial_value(
        self, value: GX2UniformInitialValue, stream: StreamOut
    ) -> None:
        stream.repeat(value.value, stream.float)
        stream.u32(value.offset)
    
    def _save_loop_var(self, var: GX2LoopVar, stream: StreamOut) -> None:
        stream.u32(var.offset)
        stream.u32(var.value)
    
    def _save_sampler_var(
        self, var: GX2SamplerVar, stream: RelocatableStreamOut,
        string_stream: StreamOut
    ) -> None:
        stream.pointer(string_stream.tell())
        string_stream.string(var.name)
        string_stream.align(4)
        stream.u32(var.type)
        stream.u32(var.location)
    
    def _save_attrib_var(
        self, var: GX2AttribVar, stream: RelocatableStreamOut,
        string_stream: StreamOut
    ) -> None:
        stream.pointer(string_stream.tell())
        string_stream.string(var.name)
        string_stream.align(4)
        stream.u32(var.type)
        stream.u32(var.count)
        stream.u32(var.location)
    
    def _finish_shader(
        self, stream: RelocatableStreamOut, data_stream: RelocatableStreamOut,
        string_stream: StreamOut
    ) -> None:
        # Calculate offsets
        data_offset = stream.size()
        string_offset = data_offset + data_stream.size()
        relocation_offset = string_offset + string_stream.size()

        # Generate relocations
        relocation_stream = StreamOut(">")
        stream.relocate(relocation_stream, 0, data_offset, Tag.Data)
        data_stream.relocate(
            relocation_stream, data_offset, string_offset, Tag.String
        )
        relocation_stream.pad(16)

        # Write data into main stream
        stream.write(data_stream.get())
        stream.write(string_stream.get())
        stream.write(relocation_stream.get())

        # Write footer
        stream.ascii("}BLK")
        stream.u32(0x28)
        stream.pad(4)
        stream.u32(relocation_offset)
        stream.u32(Tag.Data)
        stream.u32(string_stream.size())
        stream.u32(string_offset | Tag.Data)
        stream.u32(0)
        stream.u32(stream.pointer_count() + data_stream.pointer_count() + 2)
        stream.u32(relocation_offset | Tag.Data)
