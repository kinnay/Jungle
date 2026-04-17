
from jungle.errors import ParseError, SaveError
from jungle.gx2 import shaders, textures
from jungle import streams


class Tag:
    DATA = 0xD0600000
    STRING = 0xCA700000


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


class StreamOut(streams.StreamOut):
    """Stream class that implements relocations."""

    def __init__(self, endianness):
        super().__init__(endianness)
        self.pointers = {}
    
    def pointer(self, offset):
        self.pointers[self.tell()] = offset
        self.skip(4)
    
    def null_pointer(self):
        self.pointers[self.tell()] = None
        self.u32(0)

    def relocate(self, relocation_stream, source_base, target_base, tag):
        self.push()
        for source_offset, target_offset in self.pointers.items():
            if target_offset is not None:
                self.seek(source_offset)
                self.u32((target_base + target_offset) | tag)
                relocation_stream.u32((source_base + source_offset) | Tag.DATA)
            else:
                relocation_stream.u32(0)
        self.pop()


class Gfx2File:
    def __init__(self):
        self.alignment = True
        self.textures = []
        self.vertex_shaders = []
        self.pixel_shaders = []
        self.geometry_shaders = []
    
    def parse(self, data):
        stream = streams.StreamIn(data, ">")

        # Parse header
        if stream.ascii(4) != "Gfx2": raise ParseError("magic number is invalid")
        if stream.u32() != 32: raise ParseError("header size is invalid")
        if stream.u32() != 7: raise ParseError("unsupported major version")
        if stream.u32() != 1: raise ParseError("unsupported minor version")
        if stream.u32() != 2: raise ParseError("unsupported gpu version")
        self.alignment = bool(stream.u32())
        stream.pad(8)

        # Parse block headers
        blocks = {
            BlockType.PADDING: [],
            BlockType.VSHADER: [],
            BlockType.VSHADER_PROGRAM: [],
            BlockType.PSHADER: [],
            BlockType.PSHADER_PROGRAM: [],
            BlockType.GSHADER: [],
            BlockType.GSHADER_PROGRAM: [],
            BlockType.GSHADER_COPY_PROGRAM: [],
            BlockType.TEXTURE: [],
            BlockType.TEXTURE_DATA: [],
            BlockType.TEXTURE_MIPMAP_DATA: []
        }
        while True:
            block = Block()
            block.parse(stream)
            if block.type == BlockType.EOF: break
            elif block.type in blocks:
                blocks[block.type].append(block.data)
            else:
                raise ParseError("unknown block type")
        
        # A gtx file may have a texture without mipmaps
        while len(blocks[BlockType.TEXTURE]) > len(blocks[BlockType.TEXTURE_MIPMAP_DATA]):
            blocks[BlockType.TEXTURE_MIPMAP_DATA].append(b"")

        # Verify that the number of data blocks matches the number of header blocks
        if len(blocks[BlockType.VSHADER]) != len(blocks[BlockType.VSHADER_PROGRAM]):
            raise ParseError("wrong number of vertex shader blocks")
        if len(blocks[BlockType.PSHADER]) != len(blocks[BlockType.PSHADER_PROGRAM]):
            raise ParseError("wrong number of pixel shader blocks")
        if len(blocks[BlockType.GSHADER]) != len(blocks[BlockType.GSHADER_PROGRAM]):
            raise ParseError("wrong number of geometry shader blocks")
        if len(blocks[BlockType.GSHADER]) != len(blocks[BlockType.GSHADER_COPY_PROGRAM]):
            raise ParseError("wrong number of geometry copy shader blocks")
        if len(blocks[BlockType.TEXTURE]) != len(blocks[BlockType.TEXTURE_DATA]):
            raise ParseError("wrong number of texture data blocks")
        if len(blocks[BlockType.TEXTURE]) != len(blocks[BlockType.TEXTURE_MIPMAP_DATA]):
            raise ParseError("wrong number of texture mipmap blocks")
        
        # Parse texture blocks
        self.textures = []
        for i in range(len(blocks[BlockType.TEXTURE])):
            texture = self.parse_texture(blocks[BlockType.TEXTURE][i])
            texture.surface.image = blocks[BlockType.TEXTURE_DATA][i]
            texture.surface.mipmaps = blocks[BlockType.TEXTURE_MIPMAP_DATA][i]
            self.textures.append(texture)
        
        # Parse vertex shader blocks
        self.vertex_shaders = []
        for i in range(len(blocks[BlockType.VSHADER])):
            shader = self.parse_vshader(blocks[BlockType.VSHADER][i])
            shader.program = blocks[BlockType.VSHADER_PROGRAM][i]
            self.vertex_shaders.append(shader)
        
        # Parse pixel shader blocks
        self.pixel_shaders = []
        for i in range(len(blocks[BlockType.PSHADER])):
            shader = self.parse_pshader(blocks[BlockType.PSHADER][i])
            shader.program = blocks[BlockType.PSHADER_PROGRAM][i]
            self.pixel_shaders.append(shader)
        
        # Parse geometry shader blocks
        self.geometry_shaders = []
        for i in range(len(blocks[BlockType.GSHADER])):
            shader = self.parse_gshader(blocks[BlockType.GSHADER][i])
            shader.program = blocks[BlockType.GSHADER_PROGRAM][i]
            shader.copy_program = blocks[BlockType.GSHADER_COPY_PROGRAM][i]
            self.geometry_shaders.append(shader)

    def parse_texture(self, data):
        stream = streams.StreamIn(data, ">")

        texture = textures.GX2Texture()
        texture.surface.dim = stream.u32()
        texture.surface.width = stream.u32()
        texture.surface.height = stream.u32()
        texture.surface.depth = stream.u32()
        texture.surface.mip_levels = stream.u32()
        texture.surface.format = stream.u32()
        texture.surface.aa_mode = stream.u32()
        texture.surface.use = stream.u32()
        stream.skip(16)
        texture.surface.tile_mode = stream.u32()
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

    def parse_vshader(self, data):
        stream = streams.StreamIn(data, ">")

        shader = shaders.GX2VertexShader()
        shader.regs = stream.repeat(stream.u32, 52)
        stream.skip(8)
        shader.mode = stream.u32()
        
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
            shader.uniform_blocks.append(self.parse_uniform_block(stream))
        
        stream.seek(uniform_var_offset & 0xFFFFF)
        for i in range(uniform_var_count):
            shader.uniform_vars.append(self.parse_uniform_var(stream))
        
        stream.seek(initial_value_offset & 0xFFFFF)
        for i in range(initial_value_count):
            shader.initial_values.append(self.parse_initial_value(stream))
        
        stream.seek(loop_var_offset & 0xFFFFF)
        for i in range(loop_var_count):
            shader.loop_vars.append(self.parse_loop_var(stream))
        
        stream.seek(sampler_var_offset & 0xFFFFF)
        for i in range(sampler_var_count):
            shader.sampler_vars.append(self.parse_sampler_var(stream))
        
        stream.seek(attrib_var_offset & 0xFFFFF)
        for i in range(attrib_var_count):
            shader.attrib_vars.append(self.parse_attrib_var(stream))

        return shader

    def parse_pshader(self, data):
        stream = streams.StreamIn(data, ">")

        shader = shaders.GX2PixelShader()
        shader.regs = stream.repeat(stream.u32, 41)
        stream.skip(8)
        shader.mode = stream.u32()
        
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
            shader.uniform_blocks.append(self.parse_uniform_block(stream))
        
        stream.seek(uniform_var_offset & 0xFFFFF)
        for i in range(uniform_var_count):
            shader.uniform_vars.append(self.parse_uniform_var(stream))
        
        stream.seek(initial_value_offset & 0xFFFFF)
        for i in range(initial_value_count):
            shader.initial_values.append(self.parse_initial_value(stream))
        
        stream.seek(loop_var_offset & 0xFFFFF)
        for i in range(loop_var_count):
            shader.loop_vars.append(self.parse_loop_var(stream))
        
        stream.seek(sampler_var_offset & 0xFFFFF)
        for i in range(sampler_var_count):
            shader.sampler_vars.append(self.parse_sampler_var(stream))

        return shader

    def parse_gshader(self, data):
        stream = streams.StreamIn(data, ">")

        shader = shaders.GX2GeometryShader()
        shader.regs = stream.repeat(stream.u32, 19)
        stream.skip(16)
        shader.mode = stream.u32()
        
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
            shader.uniform_blocks.append(self.parse_uniform_block(stream))
        
        stream.seek(uniform_var_offset & 0xFFFFF)
        for i in range(uniform_var_count):
            shader.uniform_vars.append(self.parse_uniform_var(stream))
        
        stream.seek(initial_value_offset & 0xFFFFF)
        for i in range(initial_value_count):
            shader.initial_values.append(self.parse_initial_value(stream))
        
        stream.seek(loop_var_offset & 0xFFFFF)
        for i in range(loop_var_count):
            shader.loop_vars.append(self.parse_loop_var(stream))
        
        stream.seek(sampler_var_offset & 0xFFFFF)
        for i in range(sampler_var_count):
            shader.sampler_vars.append(self.parse_sampler_var(stream))

        return shader

    def parse_uniform_block(self, stream):
        block = shaders.GX2UniformBlock()
        block.name = stream.string_at(stream.u32() & 0xFFFFF)
        block.offset = stream.u32()
        block.size = stream.u32()
        return block

    def parse_uniform_var(self, stream):
        var = shaders.GX2UniformVar()
        var.name = stream.string_at(stream.u32() & 0xFFFFF)
        var.type = stream.u32()
        var.count = stream.u32()
        var.offset = stream.u32()
        var.block = stream.s32()
        return var
    
    def parse_initial_value(self, stream):
        value = shaders.GX2UniformInitialValue()
        value.value = stream.repeat(stream.float, 4)
        value.offset = stream.u32()
        return value
    
    def parse_loop_var(self, stream):
        var = shaders.GX2LoopVar()
        var.offset = stream.u32()
        var.value = stream.u32()
        return var
    
    def parse_sampler_var(self, stream):
        var = shaders.GX2SamplerVar()
        var.name = stream.string_at(stream.u32() & 0xFFFFF)
        var.type = stream.u32()
        var.location = stream.u32()
        return var
    
    def parse_attrib_var(self, stream):
        var = shaders.GX2AttribVar()
        var.name = stream.string_at(stream.u32() & 0xFFFFF)
        var.type = stream.u32()
        var.count = stream.u32()
        var.location = stream.u32()
        return var

    def save(self):
        # Write header
        stream = streams.StreamOut(">")
        stream.ascii("Gfx2")
        stream.u32(32)
        stream.u32(7)
        stream.u32(1)
        stream.u32(2)
        stream.u32(self.alignment)
        stream.pad(8)

        # Write shaders
        count = max(len(self.vertex_shaders), len(self.pixel_shaders), len(self.geometry_shaders))
        for i in range(count):
            if i < len(self.vertex_shaders):
                block = Block()
                block.type = BlockType.VSHADER
                block.data = self.save_shader(self.vertex_shaders[i])
                block.save(stream)

                self.pad(stream, 0x100)

                block = Block()
                block.type = BlockType.VSHADER_PROGRAM
                block.data = self.vertex_shaders[i].program
                block.save(stream)
            
            if i < len(self.pixel_shaders):
                block = Block()
                block.type = BlockType.PSHADER
                block.data = self.save_shader(self.pixel_shaders[i])
                block.save(stream)

                self.pad(stream, 0x100)

                block = Block()
                block.type = BlockType.PSHADER_PROGRAM
                block.data = self.pixel_shaders[i].program
                block.save(stream)
            
            if i < len(self.geometry_shaders):
                block = Block()
                block.type = BlockType.GSHADER
                block.data = self.save_shader(self.geometry_shaders[i])
                block.save(stream)

                self.pad(stream, 0x100)

                block = Block()
                block.type = BlockType.GSHADER_PROGRAM
                block.data = self.geometry_shaders[i].program
                block.save(stream)

                self.pad(stream, 0x100)

                block = Block()
                block.type = BlockType.GSHADER_COPY_PROGRAM
                block.data = self.geometry_shaders[i].copy_program
                block.save(stream)
        
        # Write textures
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
        
        # Write EOF block
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

    def save_shader(self, shader):
        data_stream = StreamOut(">")
        string_stream = streams.StreamOut(">")

        stream = StreamOut(">")
        stream.repeat(shader.regs, stream.u32)
        stream.u32(len(shader.program))
        stream.null_pointer()
        if isinstance(shader, shaders.GX2GeometryShader):
            stream.u32(len(shader.vertex_program))
            stream.null_pointer()
        stream.u32(shader.mode)

        stream.u32(len(shader.uniform_blocks))
        if shader.uniform_blocks:
            stream.pointer(data_stream.tell())
            for block in shader.uniform_blocks:
                self.save_uniform_block(block, data_stream, string_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.uniform_vars))
        if shader.uniform_vars:
            stream.pointer(data_stream.tell())
            for var in shader.uniform_vars:
                self.save_uniform_var(var, data_stream, string_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.initial_values))
        if shader.initial_values:
            stream.pointer(data_stream.tell())
            for value in shader.initial_values:
                self.save_initial_value(value, data_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.loop_vars))
        if shader.loop_vars:
            stream.pointer(data_stream.tell())
            for var in shader.loop_vars:
                self.save_loop_var(var, data_stream)
        else:
            stream.null_pointer()
        
        stream.u32(len(shader.sampler_vars))
        if shader.sampler_vars:
            stream.pointer(data_stream.tell())
            for var in shader.sampler_vars:
                self.save_sampler_var(var, data_stream, string_stream)
        else:
            stream.null_pointer()
        
        if isinstance(shader, (shaders.GX2VertexShader, shaders.GX2GeometryShader)):
            stream.u32(len(shader.attrib_vars))
            if shader.attrib_vars:
                stream.pointer(data_stream.tell())
                for var in shader.attrib_vars:
                    self.save_attrib_var(var, data_stream, string_stream)
            else:
                stream.null_pointer()
        
        if isinstance(shader, (shaders.GX2VertexShader, shaders.GX2GeometryShader)):
            stream.u32(shader.ring_item_size)
            stream.u32(shader.has_stream_out)
            stream.repeat(shader.stream_out_stride, stream.u32)
        stream.pad(16)

        self.finish_shader(stream, data_stream, string_stream)

        return stream.get()
    
    def save_uniform_block(self, block, stream, string_stream):
        stream.pointer(string_stream.tell())
        string_stream.string(block.name)
        string_stream.align(4)
        stream.u32(block.offset)
        stream.u32(block.size)
    
    def save_uniform_var(self, var, stream, string_stream):
        stream.pointer(string_stream.tell())
        string_stream.string(var.name)
        string_stream.align(4)
        stream.u32(var.type)
        stream.u32(var.count)
        stream.u32(var.offset)
        stream.s32(var.block)
    
    def save_initial_value(self, value, stream):
        stream.repeat(value.value, stream.float)
        stream.u32(value.offset)
    
    def save_loop_var(self, var, stream):
        stream.u32(var.offset)
        stream.u32(var.value)
    
    def save_sampler_var(self, var, stream, string_stream):
        stream.pointer(string_stream.tell())
        string_stream.string(var.name)
        string_stream.align(4)
        stream.u32(var.type)
        stream.u32(var.location)
    
    def save_attrib_var(self, var, stream, string_stream):
        stream.pointer(string_stream.tell())
        string_stream.string(var.name)
        string_stream.align(4)
        stream.u32(var.type)
        stream.u32(var.count)
        stream.u32(var.location)
    
    def finish_shader(self, stream, data_stream, string_stream):
        # Calculate offsets
        data_offset = stream.size()
        string_offset = data_offset + data_stream.size()
        relocation_offset = string_offset + string_stream.size()

        # Generate relocations
        relocation_stream = streams.StreamOut(">")
        stream.relocate(relocation_stream, 0, data_offset, Tag.DATA)
        data_stream.relocate(relocation_stream, data_offset, string_offset, Tag.STRING)
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
        stream.u32(Tag.DATA)
        stream.u32(string_stream.size())
        stream.u32(string_offset | Tag.DATA)
        stream.u32(0)
        stream.u32(len(stream.pointers) + len(data_stream.pointers) + 2)
        stream.u32(relocation_offset | Tag.DATA)
