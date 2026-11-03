
from jungle.errors import ParseError, SaveError
from jungle import streams, utils

import enum
import struct


class RollOffModel(enum.IntEnum):
    Inv = 1
    Linear = 2
    Exp = 3


class BAROCFile:
    version: int
    endianness: str

    roll_off_model: RollOffModel
    ref_distance: float
    max_distance: float
    roll_off_factor: float
    start_value: float
    is_increase_mode: bool
    culling_distance: float | None

    def __init__(self):
        self.version = 1
        self.endianness = "<"

        self.roll_off_model = RollOffModel.Inv
        self.ref_distance = 0
        self.max_distance = 0
        self.roll_off_factor = 0
        self.start_value = 0
        self.is_increase_mode = False
        self.culling_distance = None

    def parse(self, data: bytes) -> None:
        if len(data) < 6:
            raise ParseError("file is too small")
        
        bom = struct.unpack_from(">H", data, 4)[0]
        self.endianness = ">" if bom == 0xFEFF else "<"

        stream = streams.StreamIn(data, self.endianness)
        if stream.ascii(4) != "AROC":
            raise ParseError("magic number is invalid")
        if stream.u16() != 0xFEFF:
            raise ParseError("BOM is invalid")

        self.version = stream.u16()
        if self.version not in [1, 2]:
            raise ParseError("unsupported version number")

        self.roll_off_model = utils.parse_enum(stream.u32(), RollOffModel)
        self.ref_distance = stream.float()
        self.max_distance = stream.float()
        self.roll_off_factor = stream.float()
        self.start_value = stream.float()
        self.is_increase_mode = bool(stream.u32())

        self.culling_distance = None
        if self.version == 2:
            self.culling_distance = stream.float()

    def save(self) -> bytes:
        if self.version not in [1, 2]:
            raise SaveError("unsupported version number")
        
        stream = streams.StreamOut(self.endianness)
        stream.ascii("AROC")
        stream.u16(0xFEFF)
        stream.u16(self.version)
        stream.u32(self.roll_off_model)
        stream.float(self.ref_distance)
        stream.float(self.max_distance)
        stream.float(self.roll_off_factor)
        stream.float(self.start_value)
        stream.u32(self.is_increase_mode)

        if self.version == 2:
            if self.culling_distance is None:
                raise SaveError("Culling distance is required for version 2")
            stream.float(self.culling_distance)
        return stream.get()
