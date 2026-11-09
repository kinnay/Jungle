
from dataclasses import dataclass, field
from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut

import struct


@dataclass
class LayoutFile:
    magic: str = "XXXX"
    endianness: str = "<"
    version: int = 0
    filesize: int = 0
    sections: dict[str, bytes] = field(default_factory=dict)

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

        if stream.u16() != 0x14:
            raise ParseError("header size is invalid")
        
        self.version = stream.u32()
        self.filesize = stream.u32()

        num_sections = stream.u16()
        stream.pad(2)

        self.sections = {}
        for i in range(num_sections):
            type = stream.ascii(4)
            size = stream.u32()
            if size < 8:
                raise ParseError("section size is too small")
            self.sections[type] = stream.read(size - 8)
    
    def save(self) -> bytes:
        stream = StreamOut(self.endianness)
        stream.ascii(self.magic)
        stream.u16(0xFEFF)
        stream.u16(0x14)
        stream.u32(self.version)
        stream.u32(self.filesize)
        stream.u16(len(self.sections))
        stream.pad(2)
        for type, section in self.sections.items():
            stream.ascii(type)
            stream.u32(len(section) + 8)
            stream.write(section)
        return stream.get()
