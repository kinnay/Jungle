
from dataclasses import dataclass, field
from jungle.dkctf.common import CFormDescriptor, CChunkDescriptor
from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut
from jungle import utils

import enum


class TextureType(enum.IntEnum):
    Texture1D = 0
    Texture2D = 1
    Texture3D = 2
    TextureCube = 3
    Texture1DArray = 4
    Texture2DArray = 5
    Texture2DMSAA = 6
    Texture2DMSAAArray = 7


class TextureFormat(enum.IntEnum):
    UNORM_R8_G8_B8_A8 = 12
    UNORM_BC1 = 20
    UNORM_BC3 = 24
    UNORM_BC5 = 28


class TextureFilter(enum.IntEnum):
    Point = 0
    Linear = 1


class TextureWrap(enum.IntEnum):
    Clamp = 0
    Wrap = 1
    Mirror = 2
    MirrorOnce = 3


@dataclass
class CompressedBufferInfo:
    decompressed_size: int = 0
    compressed_size: int = 0
    offset: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.decompressed_size = stream.u32()
        self.compressed_size = stream.u32()
        self.offset = stream.u32()

    def encode(self, stream: StreamOut) -> None:
        stream.u32(self.decompressed_size)
        stream.u32(self.compressed_size)
        stream.u32(self.offset)


@dataclass
class TextureSamplerData:
    flags: int = 0
    filter: TextureFilter = TextureFilter.Point
    wrap_x: TextureWrap = TextureWrap.Clamp
    wrap_y: TextureWrap = TextureWrap.Clamp
    wrap_z: TextureWrap = TextureWrap.Clamp

    def decode(self, stream: StreamIn) -> None:
        self.flags = stream.u32()
        self.filter = utils.parse_enum(stream.u8(), TextureFilter)
        self.wrap_x = utils.parse_enum(stream.u8(), TextureWrap)
        self.wrap_y = utils.parse_enum(stream.u8(), TextureWrap)
        self.wrap_z = utils.parse_enum(stream.u8(), TextureWrap)

    def encode(self, stream: StreamOut) -> None:
        stream.u32(self.flags)
        stream.u8(self.filter)
        stream.u8(self.wrap_x)
        stream.u8(self.wrap_y)
        stream.u8(self.wrap_z)


@dataclass
class TextureHeader:
    type: TextureType = TextureType.Texture2D
    format: TextureFormat = TextureFormat.UNORM_BC1
    width: int = 0
    height: int = 0
    depth: int = 0
    tile_mode: int = 0
    swizzle: int = 0
    mipmap_sizes: list[int] = field(default_factory=list)
    sampler_data: TextureSamplerData = field(default_factory=TextureSamplerData)

    def decode(self, stream: StreamIn) -> None:
        self.type = utils.parse_enum(stream.u32(), TextureType)
        self.format = utils.parse_enum(stream.u32(), TextureFormat)
        self.width = stream.u32()
        self.height = stream.u32()
        self.depth = stream.u32()
        self.tile_mode = stream.u32()
        self.swizzle = stream.u32()
        self.mipmap_sizes = [stream.u32() for i in range(stream.u32())]
        self.sampler_data = stream.extract(TextureSamplerData)

    def encode(self, stream: StreamOut) -> None:
        stream.u32(self.type)
        stream.u32(self.format)
        stream.u32(self.width)
        stream.u32(self.height)
        stream.u32(self.depth)
        stream.u32(self.tile_mode)
        stream.u32(self.swizzle)
        stream.u32(len(self.mipmap_sizes))
        for size in self.mipmap_sizes:
            stream.u32(size)
        stream.add(self.sampler_data)


@dataclass
class TXTRMetadata:
    allocation_category: int = 0
    header_size: int = 0
    alignment: int = 0
    data_offset: int = 0
    data_size: int = 0
    buffers: list[CompressedBufferInfo] = field(default_factory=list)

    def parse(self, data: bytes) -> None:
        stream = StreamIn(data, ">")
        if stream.u32() != 4:
            raise ValueError("invalid version number")

        self.allocation_category = stream.u32()
        self.header_size = stream.u32()
        self.alignment = stream.u32()
        self.data_offset = stream.u32()
        self.data_size = stream.u32()

        self.buffers = []
        for i in range(stream.u32()):
            self.buffers.append(stream.extract(CompressedBufferInfo))

    def save(self) -> bytes:
        stream = StreamOut(">")
        stream.u32(4)
        stream.u32(self.allocation_category)
        stream.u32(self.header_size)
        stream.u32(self.alignment)
        stream.u32(self.data_offset)
        stream.u32(self.data_size)
        stream.u32(len(self.buffers))
        for buffer in self.buffers:
            stream.add(buffer)
        return stream.get()


@dataclass
class TXTRFile:
    header: TextureHeader = field(default_factory=TextureHeader)
    data: bytes = b""

    def parse(self, data: bytes) -> None:
        form = CFormDescriptor.fromdata(data, "TXTR", 14)

        stream = StreamIn(form, ">")
        head = stream.extract(CChunkDescriptor)
        gpu = stream.extract(CChunkDescriptor)

        if head.type != "HEAD" or head.version != 1:
            raise ParseError("HEAD chunk is invalid")
        if gpu.type != "GPU " or gpu.version != 1:
            raise ParseError("GPU chunk is invalid")

        stream = StreamIn(head.data, ">")
        self.header = stream.extract(TextureHeader)
        self.data = gpu.data

    def save(self) -> bytes:
        stream = StreamOut(">")
        stream.add(self.header)

        head = CChunkDescriptor("HEAD", 1, stream.get())
        gpu = CChunkDescriptor("GPU ", 1, self.data)

        stream = StreamOut(">")
        stream.add(head)
        stream.add(gpu)

        form = CFormDescriptor("TXTR", 14, stream.get())

        stream = StreamOut(">")
        stream.add(form)
        return stream.get()
