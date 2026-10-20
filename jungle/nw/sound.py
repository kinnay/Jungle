
from dataclasses import dataclass
from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut

import struct


@dataclass
class SectionReference:
    type: int = 0
    offset: int = -1

    def valid(self) -> bool:
        return self.type != 0 and self.offset != -1

    def check(self, type: int) -> None:
        if self.type != type:
            raise ParseError("section reference has invalid id")
    
    def parse(self, stream: StreamIn) -> None:
        self.type = stream.u16()
        stream.pad(2)
        self.offset = stream.s32()
    
    def save(self, stream: StreamOut) -> None:
        stream.u16(self.type)
        stream.pad(2)
        stream.s32(self.offset)


class SoundFile:
    magic: str
    endianness: str
    version: int
    blocks: dict[int, bytes]

    def __init__(self):
        self.magic = "XXXX"
        self.endianness = "<"
        self.version = 0
        self.blocks = {}
        
    def parse(self, data: bytes) -> None:
        # Determine endianness
        if len(data) < 6:
            raise ParseError("file is too small")
        
        bom = struct.unpack_from(">H", data, 4)[0]
        self.endianness = ">" if bom == 0xFEFF else "<"

        # Parse file
        stream = StreamIn(data, self.endianness)
        self.magic = stream.ascii(4)

        if stream.u16() != 0xFEFF:
            raise ParseError("BOM is invalid")
        
        stream.skip(2)
        self.version = stream.u32()

        if stream.u32() != len(data):
            raise ParseError("file size is invalid")

        num_blocks = stream.u16()
        stream.pad(2)

        for i in range(num_blocks):
            type = stream.u16()
            stream.pad(2)
            offset = stream.u32()
            size = stream.u32()
            self.blocks[type] = data[offset:offset+size]
    
    def save(self) -> bytes:
        header_size = 0x14 + len(self.blocks) * 0xC
        header_size = (header_size + 31) & ~31

        file_size = header_size
        for data in self.blocks.values():
            file_size = (file_size + 31) & ~31
            file_size += len(data)

        stream = StreamOut(self.endianness)
        stream.ascii(self.magic)
        stream.u16(0xFEFF)
        stream.u16(header_size)
        stream.u32(self.version)
        stream.u32(file_size)
        stream.u16(len(self.blocks))
        stream.pad(2)

        offset = header_size
        for type, data in self.blocks.items():
            stream.u16(type)
            stream.pad(2)
            stream.u32(offset)
            stream.u32(len(data))

            offset = (offset + len(data) + 31) & ~31
        
        stream.align(32)
        for data in self.blocks.values():
            stream.align(32)
            stream.write(data)
        return stream.get()
