
from dataclasses import dataclass, field

from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut
from jungle.switch.binary import \
    BinaryBlockHeader, \
    BinaryFile, \
    BinaryFileHeader, \
    DictionaryBuilder, \
    RelocationTable, \
    StringTableBuilder
from jungle import utils

import enum
import struct


class ImageStorageDimension(enum.IntEnum):
    Storage1D = 1
    Storage2D = 2
    Storage3D = 3


class ImageDimension(enum.IntEnum):
    Image1D = 0
    Image2D = 1
    Image3D = 2
    ImageCube = 3
    Image1DArray = 4
    Image2DArray = 5
    ImageCubeArray = 6


class TileMode(enum.IntEnum):
    Swizzled = 0
    Linear = 1


class TypeFormat(enum.IntEnum):
    UNORM = 1
    SNORM = 2
    UINT = 3
    SINT = 4
    FLOAT = 5
    SRGB = 6
    UHALF = 7
    UFLOAT = 10


class ChannelFormat(enum.IntEnum):
    R8 = 2
    RGBA4 = 3
    RGB5A1 = 5
    A1BGR5 = 6
    RGB565 = 7
    BGR565 = 8
    RG8 = 9
    R16 = 10
    RGBA8 = 11
    BGRA8 = 12
    RGB9E5 = 13
    RGB10A2 = 14
    RG11B10 = 15
    RG16 = 18
    D24S8 = 19
    R32 = 20
    RGBA16 = 21
    D32S8 = 22
    RG32 = 23
    RGB32 = 24
    RGBA32 = 25
    BC1 = 26
    BC2 = 27
    BC3 = 28
    BC4 = 29
    BC5 = 30
    BC6 = 31
    BC7 = 32
    ASTC_4x4 = 45
    ASTC_5x4 = 46
    ASTC_5x5 = 47
    ASTC_6x5 = 48
    ASTC_6x6 = 49
    ASTC_8x5 = 50
    ASTC_8x6 = 51
    ASTC_8x8 = 52
    ASTC_10x5 = 53
    ASTC_10x6 = 54
    ASTC_10x8 = 55
    ASTC_10x10 = 56
    ASTC_12x10 = 57
    ASTC_12x12 = 58
    BGR5A1 = 59


class ChannelMapping(enum.IntEnum):
    Zero = 0
    One = 1
    Red = 2
    Green = 3
    Blue = 4
    Alpha = 5


BlockSize = {
    ChannelFormat.R8: (1, 1),
    ChannelFormat.RGBA4: (1, 1),
    ChannelFormat.RGB5A1: (1, 1),
    ChannelFormat.A1BGR5: (1, 1),
    ChannelFormat.RGB565: (1, 1),
    ChannelFormat.BGR565: (1, 1),
    ChannelFormat.RG8: (1, 1),
    ChannelFormat.R16: (1, 1),
    ChannelFormat.RGBA8: (1, 1),
    ChannelFormat.BGRA8: (1, 1),
    ChannelFormat.RGB9E5: (1, 1),
    ChannelFormat.RGB10A2: (1, 1),
    ChannelFormat.RG11B10: (1, 1),
    ChannelFormat.RG16: (1, 1),
    ChannelFormat.D24S8: (1, 1),
    ChannelFormat.R32: (1, 1),
    ChannelFormat.RGBA16: (1, 1),
    ChannelFormat.D32S8: (1, 1),
    ChannelFormat.RG32: (1, 1),
    ChannelFormat.RGB32: (1, 1),
    ChannelFormat.RGBA32: (1, 1),
    ChannelFormat.BC1: (4, 4),
    ChannelFormat.BC2: (4, 4),
    ChannelFormat.BC3: (4, 4),
    ChannelFormat.BC4: (4, 4),
    ChannelFormat.BC5: (4, 4),
    ChannelFormat.BC6: (4, 4),
    ChannelFormat.BC7: (4, 4),
    ChannelFormat.ASTC_4x4: (4, 4),
    ChannelFormat.ASTC_5x4: (5, 4),
    ChannelFormat.ASTC_5x5: (5, 5),
    ChannelFormat.ASTC_6x5: (6, 5),
    ChannelFormat.ASTC_6x6: (6, 6),
    ChannelFormat.ASTC_8x5: (8, 5),
    ChannelFormat.ASTC_8x6: (8, 6),
    ChannelFormat.ASTC_8x8: (8, 8),
    ChannelFormat.ASTC_10x5: (10, 5),
    ChannelFormat.ASTC_10x6: (10, 6),
    ChannelFormat.ASTC_10x8: (10, 8),
    ChannelFormat.ASTC_10x10: (10, 10),
    ChannelFormat.ASTC_12x10: (12, 10),
    ChannelFormat.ASTC_12x12: (12, 12),
    ChannelFormat.BGR5A1: (1, 1),
}

BytesPerBlock = {
    ChannelFormat.R8: 1,
    ChannelFormat.RGBA4: 2,
    ChannelFormat.RGB5A1: 2,
    ChannelFormat.A1BGR5: 2,
    ChannelFormat.RGB565: 2,
    ChannelFormat.BGR565: 2,
    ChannelFormat.RG8: 2,
    ChannelFormat.R16: 2,
    ChannelFormat.RGBA8: 4,
    ChannelFormat.BGRA8: 4,
    ChannelFormat.RGB9E5: 4,
    ChannelFormat.RGB10A2: 4,
    ChannelFormat.RG11B10: 4,
    ChannelFormat.RG16: 4,
    ChannelFormat.D24S8: 4,
    ChannelFormat.R32: 4,
    ChannelFormat.RGBA16: 8,
    ChannelFormat.D32S8: 5,
    ChannelFormat.RG32: 8,
    ChannelFormat.RGB32: 12,
    ChannelFormat.RGBA32: 16,
    ChannelFormat.BC1: 8,
    ChannelFormat.BC2: 16,
    ChannelFormat.BC3: 16,
    ChannelFormat.BC4: 8,
    ChannelFormat.BC5: 16,
    ChannelFormat.BC6: 16,
    ChannelFormat.BC7: 16,
    ChannelFormat.ASTC_4x4: 16,
    ChannelFormat.ASTC_5x4: 16,
    ChannelFormat.ASTC_5x5: 16,
    ChannelFormat.ASTC_6x5: 16,
    ChannelFormat.ASTC_6x6: 16,
    ChannelFormat.ASTC_8x5: 16,
    ChannelFormat.ASTC_8x6: 16,
    ChannelFormat.ASTC_8x8: 16,
    ChannelFormat.ASTC_10x5: 16,
    ChannelFormat.ASTC_10x6: 16,
    ChannelFormat.ASTC_10x8: 16,
    ChannelFormat.ASTC_10x10: 16,
    ChannelFormat.ASTC_12x10: 16,
    ChannelFormat.ASTC_12x12: 16,
    ChannelFormat.BGR5A1: 2,
}


@dataclass
class Texture:
    flags: int = 0
    storage_dimension: ImageStorageDimension = ImageStorageDimension.Storage2D
    tile_mode: TileMode = TileMode.Linear
    swizzle: int = 0
    multisample_count: int = 0
    type_format: TypeFormat = TypeFormat.UNORM
    channel_format: ChannelFormat = ChannelFormat.R8
    usage_flags: int = 0
    width: int = 0
    height: int = 0
    depth: int = 0
    array_length: int = 0
    packaged_texture_layout: int = 0

    alignment: int = 0

    mapping_r: ChannelMapping = ChannelMapping.Red
    mapping_g: ChannelMapping = ChannelMapping.Green
    mapping_b: ChannelMapping = ChannelMapping.Blue
    mapping_a: ChannelMapping = ChannelMapping.Alpha

    image_dimesion: ImageDimension = ImageDimension.Image2D

    data: bytes = b""
    mipmap_offsets: list[int] = field(default_factory=list)


@dataclass
class TextureContainerData:
    platform: str = "NX  "
    count: int = 0
    texture_pointers_address: int = 0
    texture_data_address: int = 0
    dictionary_address: int = 0
    memory_pool_address: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.platform = stream.ascii(4)
        self.count = stream.u32()
        self.texture_pointers_address = stream.u64()
        self.texture_data_address = stream.u64()
        self.dictionary_address = stream.u64()
        self.memory_pool_address = stream.u64()
        stream.pad(16)

    def encode(self, stream: StreamOut) -> None:
        stream.ascii(self.platform)
        stream.u32(self.count)
        stream.u64(self.texture_pointers_address)
        stream.u64(self.texture_data_address)
        stream.u64(self.dictionary_address)
        stream.u64(self.memory_pool_address)
        stream.pad(16)


class BNTXParser:
    _file: BNTXFile

    def __init__(self, file: BNTXFile):
        self._file = file
    
    def parse(self, data: bytes) -> None:
        if len(data) < 32:
            raise ParseError("file is too small")

        bom = struct.unpack_from(">H", data, 12)[0]
        self._file.endianness = ">" if bom == 0xFEFF else "<"

        stream = StreamIn(data, self._file.endianness)

        header = stream.extract(BinaryFileHeader)

        if header.magic != "BNTX\0\0\0\0":
            raise ParseError("invalid magic number")

        if header.major_version != 4 or header.minor_version != 1 or \
            header.micro_version != 1:
            raise ParseError("unsupported version number")

        if header.address_size != 64:
            raise ParseError("address size is invalid")

        if header.flags:
            raise ParseError("unsupported binary file flags")

        if header.filesize != len(data):
            raise ParseError("file size is invalid")

        self._file.alignment = header.alignment
        self._file.filename = stream.string_at(header.filename_offset)

        container = stream.extract(TextureContainerData)
        self._file.platform = container.platform

        stream.seek(container.texture_pointers_address)
        texture_pointers = stream.repeat(stream.u64, container.count)
        for pointer in texture_pointers:
            stream.seek(pointer)

            block = BinaryBlockHeader()
            block.decode(stream)

            if block.type != "BRTI":
                raise ParseError("block type is invalid")

            texture = Texture()
            texture.flags = stream.u8()
            texture.storage_dimension = \
                utils.parse_enum(stream.u8(), ImageStorageDimension)
            texture.tile_mode = utils.parse_enum(stream.u16(), TileMode)
            texture.swizzle = stream.u16()
            mipmap_count = stream.u16()
            if mipmap_count < 1:
                raise ParseError("texture must have at least one mipmap")
            texture.multisample_count = stream.u16()
            stream.pad(2)
            image_format = stream.u32()
            texture.type_format = \
                utils.parse_enum(image_format & 0xFF, TypeFormat)
            texture.channel_format = \
                utils.parse_enum(image_format >> 8, ChannelFormat)
            texture.usage_flags = stream.u32()
            texture.width = stream.u32()
            texture.height = stream.u32()
            texture.depth = stream.u32()
            texture.array_length = stream.u32()
            texture.packaged_texture_layout = stream.u64()
            stream.pad(20)

            data_size = stream.u32()
            texture.alignment = stream.u32()
            texture.mapping_r = utils.parse_enum(stream.u8(), ChannelMapping)
            texture.mapping_g = utils.parse_enum(stream.u8(), ChannelMapping)
            texture.mapping_b = utils.parse_enum(stream.u8(), ChannelMapping)
            texture.mapping_a = utils.parse_enum(stream.u8(), ChannelMapping)
            texture.image_dimesion = \
                utils.parse_enum(stream.u8(), ImageDimension)
            stream.pad(3)

            with stream.jump(stream.u64()):
                name = stream.ascii(stream.u16())

            stream.skip(16)

            if stream.u64():
                raise ParseError("user data is not supported yet")

            stream.skip(32)
            stream.skip(512)

            mipmap_addrs = stream.repeat(stream.u64, mipmap_count)
            mipmap_base = mipmap_addrs[0]
            texture.mipmap_offsets = \
                [addr - mipmap_base for addr in mipmap_addrs]

            texture.data = stream.read_at(mipmap_base, data_size)

            self._file.textures[name] = texture


class BNTXEncoder:
    _file: BNTXFile

    _string_table: StringTableBuilder
    _dictionary: DictionaryBuilder
    _relocation_table: RelocationTable

    _texture_pointer_address: int
    _string_table_address: int
    _dictionary_address: int
    _texture_info_addresses: list[int]
    _texture_info_end: int
    _texture_data_base: int
    _texture_data_size: int
    _texture_data_addresses: list[int]
    _relocation_table_address: int

    def __init__(self, file: BNTXFile):
        self._file = file

        self._string_table = StringTableBuilder()
        self._dictionary = DictionaryBuilder(self._string_table)
        self._relocation_table = RelocationTable()

        self._texture_pointer_address = 0
        self._string_table_address = 0
        self._texture_info_addresses = []
        self._texture_info_end = 0
        self._texture_data_base = 0
        self._texture_data_size = 0
        self._texture_data_addresses = []
        self._relocation_table_address = 0

    def encode(self) -> bytes:
        self._prepare_encoding()
        self._prepare_relocation_table()

        stream = StreamOut(self._file.endianness)
        stream.add(self._string_table)
        stream.add(self._dictionary)
        string_table = stream.get()

        blocks = [("_STR", string_table)]
        for index, (name, texture) in enumerate(self._file.textures.items()):
            block_data = self._encode_texture(index, name, texture)
            if index == len(self._file.textures) - 1:
                expected_size = self._texture_data_base - \
                    self._texture_info_addresses[-1]
                padding_size = expected_size - len(block_data) - 16
                block_data += bytes(padding_size)

            blocks.append(("BRTI", block_data))
        blocks.append(("BRTD", self._collect_texture_data()))

        file = BinaryFile()
        file.magic = "BNTX\0\0\0\0"
        file.major_version = 4
        file.minor_version = 1
        file.micro_version = 1
        file.endianness = self._file.endianness
        file.alignment = self._file.alignment
        file.address_size = 64
        file.filename_offset = \
            self._string_table.address(self._file.filename) + 2
        file.header = self._encode_header()
        file.blocks = blocks
        file.relocation_table = self._relocation_table
        return file.save()

    def _encode_header(self) -> bytes:
        container = TextureContainerData()
        container.platform = self._file.platform
        container.count = len(self._file.textures)
        container.texture_pointers_address = self._texture_pointer_address
        container.texture_data_address = self._texture_data_base
        container.dictionary_address = \
            self._string_table_address + self._string_table.size()
        container.memory_pool_address = 0x58

        stream = StreamOut(self._file.endianness)
        stream.add(container)
        stream.pad(320)
        stream.repeat(self._texture_info_addresses, stream.u64)
        return stream.get()

    def _encode_texture(self, index: int, name: str, texture: Texture) -> bytes:
        info_base = self._texture_info_addresses[index]
        data_base = self._texture_data_addresses[index]

        stream = StreamOut(self._file.endianness)
        stream.u8(texture.flags)
        stream.u8(texture.storage_dimension)
        stream.u16(texture.tile_mode)
        stream.u16(texture.swizzle)
        stream.u16(len(texture.mipmap_offsets))
        stream.u16(texture.multisample_count)
        stream.pad(2)
        stream.u32((texture.channel_format << 8) | texture.type_format)
        stream.u32(texture.usage_flags)
        stream.u32(texture.width)
        stream.u32(texture.height)
        stream.u32(texture.depth)
        stream.u32(texture.array_length)
        stream.u64(texture.packaged_texture_layout)
        stream.pad(20)

        stream.u32(len(texture.data))
        stream.u32(texture.alignment)
        stream.u8(texture.mapping_r)
        stream.u8(texture.mapping_g)
        stream.u8(texture.mapping_b)
        stream.u8(texture.mapping_a)
        stream.u8(texture.image_dimesion)
        stream.pad(3)
        stream.u64(self._string_table.address(name))
        stream.u64(0x20)
        stream.u64(info_base + 0x2A0)
        stream.u64(0)
        stream.u64(info_base + 0xA0)
        stream.u64(info_base + 0x1A0)
        stream.pad(16)
        stream.pad(512)

        addresses = [data_base + offset for offset in texture.mipmap_offsets]
        stream.repeat(addresses, stream.u64)
        return stream.get()

    def _collect_texture_data(self) -> bytes:
        data = b""
        for texture in self._file.textures.values():
            data += texture.data

        aligned_size = utils.align_up(len(data), 1 << self._file.alignment)
        return data + bytes(aligned_size - len(data))

    def _prepare_encoding(self) -> None:
        self._string_table.add(self._file.filename)
        for name in self._file.textures:
            self._string_table.add(name)
            self._dictionary.add(name)
        
        self._texture_pointer_address = 0x198

        self._string_table_address = \
            self._texture_pointer_address + 8 * len(self._file.textures)
        self._dictionary_address = \
            self._string_table_address + self._string_table.size()

        self._string_table.update_address(self._string_table_address)

        address = self._dictionary_address + 24 + 16 * len(self._file.textures)
        self._texture_info_addresses = []
        for texture in self._file.textures.values():
            self._texture_info_addresses.append(address)
            address += 0x2A0 + 8 * len(texture.mipmap_offsets)
        self._texture_info_end = address
        
        aligned_data_address = \
            utils.align_up(address, 1 << self._file.alignment) - 16
        if aligned_data_address < self._texture_info_end:
            aligned_data_address += 1 << self._file.alignment

        self._texture_data_base = aligned_data_address

        self._texture_data_size = 16
        self._texture_data_addresses = []
        for texture in self._file.textures.values():
            address = self._texture_data_base + self._texture_data_size
            self._texture_data_addresses.append(address)
            self._texture_data_size += len(texture.data)
        
        self._texture_data_size = \
            utils.align_up(
                self._texture_data_size - 16, 1 << self._file.alignment
            ) + 16

        self._relocation_table_address = \
            self._texture_data_base + self._texture_data_size

    def _prepare_relocation_table(self) -> None:
        self._relocation_table.offset = self._relocation_table_address

        header = self._relocation_table.add_section(0, self._texture_info_end)
        data = self._relocation_table.add_section(
            self._texture_data_base, self._texture_data_size
        )

        header.add(0x28)
        data.add(0x30)
        header.add(0x38)
        header.add(0x40)

        for i in range(len(self._file.textures)):
            header.add(0x198 + 8 * i)

        self._dictionary.update_relocations(self._dictionary_address, header)

        for address, texture in zip(
            self._texture_info_addresses, self._file.textures.values()
        ):
            header.add(address + 0x60)
            header.add(address + 0x68)
            header.add(address + 0x70)
            header.add(address + 0x80)
            header.add(address + 0x88)
            for i in range(len(texture.mipmap_offsets)):
                data.add(address + 0x2A0 + i * 8)


@dataclass
class BNTXFile:
    endianness: str = "<"
    alignment: int = 0
    filename: str = ""
    platform: str = "NX  "
    textures: dict[str, Texture] = field(default_factory=dict)

    def parse(self, data: bytes) -> None:
        parser = BNTXParser(self)
        parser.parse(data)

    def save(self) -> bytes:
        encoder = BNTXEncoder(self)
        return encoder.encode()