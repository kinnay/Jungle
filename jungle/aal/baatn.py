
from dataclasses import dataclass
from jungle.errors import ParseError, SaveError
from jungle import streams, utils
import enum
import struct


class CurveType(enum.IntEnum):
    RollOff = 0
    Custom = 1
    UnitDistance = 2


class DistanceParamTarget(enum.IntEnum):
    Volume = 0
    EnvFx = 1
    Filter = 2
    Spread = 3
    Priority = 4


@dataclass
class CurveDescription:
    name: str = ""
    type: CurveType = CurveType.RollOff


class StringTable:
    _strings: dict[str, int]
    _data: bytes

    def __init__(self):
        self._strings = {}
        self._data = b""
    
    def add(self, string: str) -> int:
        """
        Adds a string to the string table and returns its offset within the
        string table.
        """
        if string not in self._strings:
            self._strings[string] = len(self._data)
            self._data += string.encode() + b"\0"
        return self._strings[string]
    
    def get(self) -> bytes:
        """Returns the encoded string table."""
        return self._data


class BAATNFile:
    version: int
    endianness: str

    curves: dict[DistanceParamTarget, CurveDescription]

    directivity: str
    culling: str

    listener_enabled: bool
    occlusion_enabled: bool

    def __init__(self):
        self.version = 1
        self.endianness = "<"

        self.curves = {
            target: CurveDescription() for target in DistanceParamTarget
        }

        self.directivity = ""
        self.culling = ""

        self.listener_enabled = False
        self.occlusion_enabled = False

    def parse(self, data: bytes) -> None:
        if len(data) < 6:
            raise ParseError("file is too small")
        
        bom = struct.unpack_from(">H", data, 4)[0]
        self.endianness = ">" if bom == 0xFEFF else "<"

        stream = streams.StreamIn(data, self.endianness)
        if stream.ascii(4) != "AATN":
            raise ParseError("magic number is invalid")
        if stream.u16() != 0xFEFF:
            raise ParseError("BOM is invalid")

        self.version = stream.u16()
        if self.version != 1:
            raise ParseError("unsupported version number")

        string_offset = stream.u32()

        self.curves = {}
        for target in DistanceParamTarget:
            curve = CurveDescription()
            curve.name = stream.string_at(string_offset + stream.u32())
            curve.type = utils.parse_enum(stream.u32(), CurveType)
            self.curves[target] = curve
        
        self.directivity = stream.string_at(string_offset + stream.u32())
        self.culling = stream.string_at(string_offset + stream.u32())

        self.listener_enabled = bool(stream.u32())
        self.occlusion_enabled = bool(stream.u32())
    
    def save(self) -> bytes:
        if self.version != 1:
            raise SaveError("unsupported version number")
        
        string_table = StringTable()

        stream = streams.StreamOut(self.endianness)
        stream.ascii("AATN")
        stream.u16(0xFEFF)
        stream.u16(self.version)
        stream.u32(0x44)

        for target in DistanceParamTarget:
            stream.u32(string_table.add(self.curves[target].name))
            stream.u32(self.curves[target].type)

        stream.u32(string_table.add(self.directivity))
        stream.u32(string_table.add(self.culling))		
        stream.u32(self.listener_enabled)
        stream.u32(self.occlusion_enabled)
        stream.write(string_table.get())
        stream.align(4)
        return stream.get()
