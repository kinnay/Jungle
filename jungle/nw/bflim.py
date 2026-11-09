
from dataclasses import dataclass

from jungle.errors import ParseError
from jungle.gx2.textures import GX2TileMode
from jungle.nw.layout import LayoutFile
from jungle.streams import StreamIn, StreamOut
from jungle import utils

import enum
import struct


class BFLIMFormat(enum.IntEnum):
    UNORM_R8_G8 = 3
    UNORM_R8_G8_B8_A8 = 9
    UNORM_BC1 = 12
    UNORM_BC2 = 13
    UNORM_BC3 = 14
    UNORM_BC4 = 16
    UNORM_BC5 = 17


@dataclass
class BFLIMFile:
    version: int = 0x02020000
    endianness: str = "<"

    width: int = 0
    height: int = 0
    alignment: int = 0
    format: BFLIMFormat = BFLIMFormat.UNORM_R8_G8_B8_A8
    tile_mode: GX2TileMode = GX2TileMode.Default
    swizzle: int = 0
    data: bytes = b""

    def parse(self, data: bytes) -> None:
        footer = self._find_footer(data)

        file = LayoutFile()
        file.parse(data[footer : -4])

        if file.magic != "FLIM":
            raise ParseError("invalid magic number")
        if file.filesize != len(data):
            raise ParseError("file size is invalid")
        if file.version not in [0x02020000, 0x03030000]:
            raise ParseError("unsupported version number")

        self.version = file.version
        self.endianness = file.endianness

        for section in file.sections:
            if section != "imag":
                raise ParseError("unsupported section type")

        if "imag" not in file.sections:
            raise ParseError("imag section is missing")

        stream = StreamIn(file.sections["imag"], file.endianness)
        self.width = stream.u16()
        self.height = stream.u16()
        self.alignment = stream.u16()
        self.format = utils.parse_enum(stream.u8(), BFLIMFormat)

        swizzle = stream.u8()
        self.tile_mode = utils.parse_enum(swizzle & 31, GX2TileMode)
        self.swizzle = swizzle >> 5

        self.data = data[:footer]

    def save(self) -> bytes:
        stream = StreamOut(self.endianness)
        stream.u16(self.width)
        stream.u16(self.height)
        stream.u16(self.alignment)
        stream.u8(self.format)
        stream.u8(self.tile_mode | (self.swizzle << 5))

        file = LayoutFile(
            magic = "FLIM",
            endianness = self.endianness,
            version = self.version,
            filesize = len(self.data) + 0x28,
            sections = {
                "imag": stream.get()
            }
        )

        stream = StreamOut(self.endianness)
        stream.write(self.data)
        stream.write(file.save())
        stream.u32(len(self.data))
        return stream.get()

    def _find_footer(self, data: bytes) -> tuple[int, str]:
        if len(data) < 4:
            raise ParseError("file is too small")

        offset_be = self._find_footer_with_endianness(data, ">")
        offset_le = self._find_footer_with_endianness(data, "<")

        if offset_be is None and offset_le is None:
            raise ParseError("failed to find footer")

        return offset_be or offset_le

    def _find_footer_with_endianness(
        self, data: bytes, endianness: str
    ) -> int | None:
        offset = struct.unpack_from(endianness + "I", data, -4)[0]
        if offset > len(data) - 6:
            return None

        if data[offset : offset + 4] != b"FLIM":
            return None

        if struct.unpack_from(endianness + "H", data, offset + 4)[0] != 0xFEFF:
            return None

        return offset
