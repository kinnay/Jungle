
from dataclasses import dataclass

from jungle.errors import ParseError
from jungle.gx2.textures import GX2TileMode
from jungle.nw.layout import LayoutFile
from jungle.streams import StreamIn, StreamOut
from jungle import utils

import enum
import struct


class BFLIMFormat(enum.IntEnum):
    L8 = 0
    A8 = 1
    LA4 = 2
    LA8 = 3
    RG8 = 4
    BGR565 = 5
    RGBA5551 = 7
    ABGR4 = 8
    RGBA8 = 9
    BC1 = 12
    BC2 = 13
    BC3 = 14
    BC4L = 15
    BC4A = 16
    BC5 = 17
    RGBA_SRGB = 20
    BC1_SRGB = 21
    BC2_SRGB = 22
    BC3_SRGB = 23
    RGB10A2 = 24


@dataclass
class BFLIMFile:
    version: int = 0x02020000
    endianness: str = "<"

    width: int = 0
    height: int = 0
    alignment: int = 0
    format: BFLIMFormat = BFLIMFormat.L8
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

    def _find_footer(self, data: bytes) -> int:
        if len(data) < 4:
            raise ParseError("file is too small")

        offset_be = self._find_footer_with_endianness(data, ">")
        offset_le = self._find_footer_with_endianness(data, "<")

        if offset_be is not None:
            return offset_be
        elif offset_le is not None:
            return offset_le
        else:
            raise ParseError("failed to find footer")

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
