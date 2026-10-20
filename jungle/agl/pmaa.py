
from dataclasses import dataclass, field
from jungle.errors import ParseError, SaveError
from jungle import streams, utils
from typing import Any

import enum
import struct
import typing


MAGIC_NUMBER = struct.unpack(">I", b"PMAA")[0]


class ParameterType(enum.IntEnum):
    Bool = 0
    F32 = 1
    Int = 2
    Vec2 = 3
    Vec3 = 4
    Vec4 = 5
    Color = 6
    String32 = 7
    String64 = 8
    Curve1 = 9
    Curve2 = 10
    Curve3 = 11
    Curve4 = 12
    BufferInt = 13
    BufferFloat = 14
    String256 = 15
    Quat = 16
    U32 = 17
    BufferU32 = 18
    BufferBinary = 19
    StringRef = 20


class CurveType(enum.IntEnum):
    Linear = 0
    Hermit = 1
    Step = 2
    Sin = 3
    Cos = 4
    SinPow2 = 5
    Linear2D = 6
    Hermit2D = 7
    Step2D = 8
    NonuniformSpline = 9
    Hermit2DSmooth = 10


@dataclass
class Curve:
    type: CurveType = CurveType.Hermit2D
    values: list[float] = field(
        default_factory=lambda: [.0, .0, .5, .5, .5, .5, 1., 1., .5]
    )
    
    def parse(self, stream: StreamIn) -> None:
        num_values = stream.u32()
        if num_values > 30:
            raise ParseError("curve has too many points")

        self.type = utils.parse_enum(stream.u32(), CurveType)
        self.values = stream.repeat(stream.float, num_values)
        stream.skip(4 * (30 - num_values))
    
    def save(self, stream: StreamOut) -> None:
        preset = [.0, .0, .5, .5, .5, .5, 1., 1., .5] + [1.] * 21
        values = self.values + preset[len(self.values):]

        stream.u32(len(self.values))
        stream.u32(self.type)
        stream.repeat(values, stream.float)


@dataclass(eq=False)
class Parameter:
    hash: int = 0
    type: ParameterType = ParameterType.Int
    value: Any = 0


@dataclass
class ParameterObject:
    hash: int = 0
    type_hash: int = 0
    parameters: list[Parameter] = field(default_factory=list)


@dataclass
class ParameterList:
    hash: int = 0
    children: list[ParameterList] = field(default_factory=list)
    objects: list[ParameterObject] = field(default_factory=list)


string_types = [
    ParameterType.String32, ParameterType.String64
]

parameter_sizes = {
    ParameterType.Bool: 1,
    ParameterType.F32: 4,
    ParameterType.Int: 4,
    ParameterType.Vec2: 8,
    ParameterType.Vec3: 12,
    ParameterType.Vec4: 16,
    ParameterType.Color: 16,
    ParameterType.Curve1: 128,
    ParameterType.Curve2: 256,
    ParameterType.Curve3: 384,
    ParameterType.Curve4: 512,
    ParameterType.U32: 4
}

def parse_value(
    stream: StreamIn, type: ParameterType, size: int | None = None
) -> Any:
    if type == ParameterType.Bool: return stream.bool()
    elif type == ParameterType.F32: return stream.float()
    elif type == ParameterType.Int: return stream.s32()
    elif type == ParameterType.Vec2:
        x = stream.float()
        y = stream.float()
        return x, y
    elif type == ParameterType.Vec3:
        x = stream.float()
        y = stream.float()
        z = stream.float()
        return x, y, z
    elif type == ParameterType.Vec4:
        x = stream.float()
        y = stream.float()
        z = stream.float()
        w = stream.float()
        return x, y, z, w
    elif type == ParameterType.Color:
        r = stream.float()
        g = stream.float()
        b = stream.float()
        a = stream.float()
        return r, g, b, a
    elif type == ParameterType.String32:
        if size is not None:
            return stream.fixed_string(size, 32)
        return stream.string()
    elif type == ParameterType.String64:
        if size is not None:
            return stream.fixed_string(size, 64)
        return stream.string()
    elif type == ParameterType.Curve1:
        curve = Curve()
        curve.parse(stream)
        return curve
    elif type == ParameterType.Curve2:
        value = []
        for i in range(2):
            curve = Curve()
            curve.parse(stream)
            value.append(curve)
        return value
    elif type == ParameterType.Curve3:
        value = []
        for i in range(3):
            curve = Curve()
            curve.parse(stream)
            value.append(curve)
        return value
    elif type == ParameterType.Curve4:
        value = []
        for i in range(4):
            curve = Curve()
            curve.parse(stream)
            value.append(curve)
        return value
    elif type == ParameterType.BufferFloat:
        if size is not None:
            return stream.repeat(stream.float, size // 4)
        else:
            raise ParseError(f"unsupported parameter type: {type}")
    elif type == ParameterType.U32: return stream.u32()
    elif type == ParameterType.BufferU32:
        if size is not None:
            return stream.repeat(stream.u32, size // 4)
        else:
            raise ParseError(f"unsupported parameter type: {type}")
    else:
        raise ParseError(f"unsupported parameter type: {type}")

def save_value(stream: StreamOut, type: ParameterType, value: Any) -> None:
    if type == ParameterType.Bool: stream.bool(value)
    elif type == ParameterType.F32: stream.float(value)
    elif type == ParameterType.Int: stream.s32(value)
    elif type == ParameterType.Vec2:
        for i in range(2):
            stream.float(value[i])
    elif type == ParameterType.Vec3:
        for i in range(3):
            stream.float(value[i])
    elif type == ParameterType.Vec4:
        for i in range(4):
            stream.float(value[i])
    elif type == ParameterType.Color:
        for i in range(4):
            stream.float(value[i])
    elif type == ParameterType.String32: stream.fixed_string(value, 32)
    elif type == ParameterType.String64: stream.fixed_string(value, 64)
    elif type == ParameterType.Curve1: value.save(stream)
    elif type == ParameterType.Curve2:
        for curve in value:
            curve.save(stream)
    elif type == ParameterType.Curve3:
        for curve in value:
            curve.save(stream)
    elif type == ParameterType.Curve4:
        for curve in value:
            curve.save(stream)
    elif type == ParameterType.BufferFloat: stream.repeat(value, stream.float)
    elif type == ParameterType.U32: stream.u32(value)
    elif type == ParameterType.BufferU32: stream.repeat(value, stream.u32)
    else:
        raise ParseError(f"unsupported parameter type: {type}")


class StreamIn(streams.StreamIn):
    """
    Memory stream that detects quirks of Nintendo's tooling.

    In some games, strings with a fixed size contain uninitialized bytes
    behind the null terminator. This stream class detects whether that
    is the case.

    In some games, strings with a fixed size always use the maximum
    number of bytes. In other games, they only use the necessary
    number of bytes. This class detects that.
    """

    minimize_strings: bool | None
    string_padding: int | None

    def __init__(self, data: bytes, endianness: str):
        super().__init__(data, endianness)
        self.minimize_strings = None
        self.string_padding = None
    
    def fixed_string(self, size: int, max_size: int | None = None) -> str:
        data = self.read(size)
        if b"\0" not in data:
            raise ParseError("expected null terminator behind string")
        
        string, padding = data.split(b"\0", 1)

        # Detect whether the memory behind the string
        # contains uninitialized bytes
        if len(padding) > 1:
            self.string_padding = padding[0]
        
        # Detect whether the string uses the necessary or the
        # maximum number of bytes.
        if self.minimize_strings is None and max_size is not None:
            if size != max_size:
                self.minimize_strings = True
            elif padding:
                self.minimize_strings = False

        return string.decode()


class StreamOut(streams.StreamOut):
    """
    Memory stream that reproduces quirks of Nintendo's tooling.

    In some games, strings with a fixed size contain uninitialized bytes
    behind the null terminator. This stream class mimics that behavior.

    In some games, strings with a fixed size always use the maximum
    number of bytes. In other games, they only use the necessary
    number of bytes. This class mimics the desired behavior.
    """

    minimize_strings: bool
    string_padding: int

    def __init__(
        self, endianness: str, minimize_strings: bool | None = None,
        string_padding: int | None = None
    ):
        super().__init__(endianness)
        self.minimize_strings = minimize_strings or False
        self.string_padding = string_padding or 0
    
    def fixed_string(
        self, value: str, size: int, allow_minize: bool = True
    ) -> None:
        data = value.encode() + b"\0"
        if not allow_minize or not self.minimize_strings:
            data = data.ljust(size - 1, bytes([self.string_padding]))
            data = data.ljust(size, b"\0")
        if len(data) > size:
            raise SaveError("string is too large")
        self.write(data)


class PMAADecoderType(typing.Protocol):
    def parse(self, data: bytes) -> None:
        ...


class PMAAEncoderType(typing.Protocol):
    def save(self, file: PMAAFile) -> bytes:
        ...


class PMAADecoderV1:
    _file: PMAAFile

    def __init__(self, file: PMAAFile):
        self._file = file
    
    def parse(self, data: bytes) -> None:
        stream = StreamIn(data, self._file.endianness)
        stream.skip(8)

        endianness_flag = "<" if stream.u32() & 1 else ">"
        if endianness_flag != self._file.endianness:
            raise ParseError("unexpected endianness flag")
        
        if stream.u32() != len(data): raise ParseError("file size is invalid")

        self._file.effect_version = stream.u32()
        self._file.effect_type = stream.fixed_string(stream.u32())

        self._file.align = stream.tell() & 3 == 0

        self._file.root = self._parse_parameter_list(stream)

        self._file.minimize_strings = stream.minimize_strings
        self._file.string_padding = stream.string_padding
    
    def _parse_parameter_list(self, stream: StreamIn) -> ParameterList:
        stream.skip(4)

        list = ParameterList()
        list.hash = stream.u32()

        num_children = stream.u32()
        num_objects = stream.u32()
        for i in range(num_children):
            list.children.append(self._parse_parameter_list(stream))		
        for i in range(num_objects):
            list.objects.append(self._parse_parameter_object(stream))
        return list
    
    def _parse_parameter_object(self, stream: StreamIn) -> ParameterObject:
        stream.skip(4)

        num_parameters = stream.u32()

        object = ParameterObject()
        object.hash = stream.u32()
        object.type_hash = stream.u32()
        for i in range(num_parameters):
            object.parameters.append(self._parse_parameter(stream))
        return object
    
    def _parse_parameter(self, stream: StreamIn) -> Parameter:
        base = stream.tell()
        size = stream.u32()

        parameter = Parameter()
        parameter.type = utils.parse_enum(stream.u32(), ParameterType)
        parameter.hash = stream.u32()
        parameter.value = parse_value(stream, parameter.type, size - 12)

        if stream.tell() != base + size:
            raise ParseError("parameter has invalid size")
        return parameter


class PMAADecoderV2:
    _file: PMAAFile

    def __init__(self, file: PMAAFile):
        self._file = file
    
    def parse(self, data):
        stream = StreamIn(data, self._file.endianness)
        stream.skip(8)

        flags = stream.u32()
        if flags & 1 != (self._file.endianness == "<"):
            raise ParseError("unexpected endianness flag")
        self._file.shift_jis = bool(flags & 2)
        
        if stream.u32() != len(data): raise ParseError("file size is invalid")

        self._file.effect_version = stream.u32()
        
        type_length = stream.u32()
        stream.skip(20)
        stream.pad(4)

        self._file.effect_type = stream.fixed_string(type_length)
        self._file.root = self._parse_parameter_list(stream)

        self._file.align = True
        self._file.minimize_strings = False
        self._file.string_padding = 0
    
    def _parse_parameter_list(self, stream: StreamIn) -> ParameterList:
        base = stream.tell()

        list = ParameterList()
        list.hash = stream.u32()

        list_info = stream.u32()
        object_info = stream.u32()

        stream.seek(base + (list_info & 0xFFFF) * 4)
        for i in range(list_info >> 16):
            list.children.append(self._parse_parameter_list(stream))
        
        stream.seek(base + (object_info & 0xFFFF) * 4)
        for i in range(object_info >> 16):
            list.objects.append(self._parse_parameter_object(stream))

        stream.seek(base + 12)
        return list
    
    def _parse_parameter_object(self, stream: StreamIn) -> ParameterObject:
        base = stream.tell()

        object = ParameterObject()
        object.hash = stream.u32()

        parameter_info = stream.u32()

        stream.seek(base + (parameter_info & 0xFFFF) * 4)
        for i in range(parameter_info >> 16):
            object.parameters.append(self._parse_parameter(stream))
        
        stream.seek(base + 8)
        return object

    def _parse_parameter(self, stream: StreamIn) -> Parameter:
        base = stream.tell()

        parameter = Parameter()
        parameter.hash = stream.u32()

        info = stream.u32()
        parameter.type = utils.parse_enum(info >> 24, ParameterType)

        stream.seek(base + (info & 0xFFFFFF) * 4)
        parameter.value = parse_value(stream, parameter.type)

        stream.seek(base + 8)
        return parameter


class PMAAEncoderV1:
    def save(self, file: PMAAFile) -> bytes:
        stream = StreamOut(
            file.endianness, file.minimize_strings, file.string_padding
        )
        stream.u32(MAGIC_NUMBER)
        stream.u32(1)
        stream.u32(1 if file.endianness == "<" else 0)
        stream.skip(4)
        stream.u32(file.effect_version)

        type_length = len(file.effect_type) + 1
        if file.align:
            type_length = (type_length + 3) & ~3
        
        stream.u32(type_length)
        stream.fixed_string(file.effect_type, type_length, False)

        self._save_parameter_list(stream, file.root)

        stream.u32_at(12, stream.size())
        return stream.get()

    def _save_parameter_list(
        self, stream: StreamOut, list: ParameterList
    ) -> None:
        base = stream.reserve(4)
        stream.u32(list.hash)
        stream.u32(len(list.children))
        stream.u32(len(list.objects))
        for child in list.children:
            self._save_parameter_list(stream, child)
        for object in list.objects:
            self._save_parameter_object(stream, object)
        stream.u32_at(base, stream.tell() - base)
    
    def _save_parameter_object(
        self, stream: StreamOut, object: ParameterObject
    ) -> None:
        base = stream.reserve(4)
        stream.u32(len(object.parameters))
        stream.u32(object.hash)
        stream.u32(object.type_hash)
        for parameter in object.parameters:
            self._save_parameter(stream, parameter)
        stream.u32_at(base, stream.tell() - base)
    
    def _save_parameter(self, stream: StreamOut, parameter: Parameter) -> None:
        base = stream.reserve(4)
        stream.u32(parameter.type)
        stream.u32(parameter.hash)
        save_value(stream, parameter.type, parameter.value)
        stream.u32_at(base, stream.tell() - base)


class PMAAEncoderV2:
    def save(self, file: PMAAFile) -> bytes:
        # Generate flags
        flags = 0
        if file.endianness == "<": flags |= 1
        if file.shift_jis: flags |= 2

        # Determine length of effect type name
        type_length = len(file.effect_type) + 1
        type_length = (type_length + 3) & ~3

        # This will hold all lists, objects and parameters
        lists = [file.root]
        objects = []
        parameters = []

        # Streams for data and string tables
        data_stream = StreamOut(file.endianness)
        string_stream = StreamOut(file.endianness)

        # This will hold the offset within a table for each value
        data_offsets = {}
        string_offsets = {}

        # We collect all lists, objects and parameters here
        todo = [file.root]
        allow_overlap = False
        while todo:
            # Analyze next list
            list = todo.pop(0)
            for child in list.children:
                lists.append(child)
                todo.append(child)
            
            # Loop through objects in the list
            for object in list.objects:
                objects.append(object)

                for parameter in object.parameters:
                    parameters.append(parameter)

                    if parameter.type in string_types:
                        # Add value to string table if necessary
                        if parameter.value not in string_offsets:
                            string_offsets[parameter.value] = \
                                string_stream.size()
                            string_stream.string(parameter.value)
                            string_stream.align(4)
                    else:
                        # First generate the data that represents this value
                        temp_stream = StreamOut(file.endianness)
                        save_value(temp_stream, parameter.type, parameter.value)
                        temp_stream.align(4)
                        value = temp_stream.get()

                        # Check if the data is already present in the data table
                        data = data_stream.get()
                        offset = data.find(value)
                        while offset & 3 and offset != -1:
                            offset = data.find(value, offset + 1)

                        # If the data is not yet present, add it
                        if offset == -1:
                            # If part of the value overlaps with the previous
                            # value, Nintendo's tooling makes the offset point
                            # to the part of the previous value, while still
                            # writing the whole new value to the file. Except in
                            # the very first case.
                            overlap = 0
                            while data[-overlap-4:] == value[:overlap+4]:
                                overlap += 4
                            if overlap and not allow_overlap:
                                overlap = 0
                                allow_overlap = True
                            offset = data_stream.size() - overlap
                            data_stream.write(value)
                        
                        # Add the offset to the map
                        data_offsets[parameter] = offset
        
        # Determine file size
        file_size = 0x30 + type_length
        file_size += len(lists) * 12
        file_size += len(objects) * 8
        file_size += len(parameters) * 8
        file_size += data_stream.size() + string_stream.size()

        # Save header
        stream = StreamOut(file.endianness)
        stream.u32(MAGIC_NUMBER)
        stream.u32(2)
        stream.u32(flags)
        stream.u32(file_size)
        stream.u32(file.effect_version)
        stream.u32(type_length)
        stream.u32(len(lists))
        stream.u32(len(objects))
        stream.u32(len(parameters))
        stream.u32(data_stream.size())
        stream.u32(string_stream.size())
        stream.pad(4)

        stream.fixed_string(file.effect_type, type_length, False)

        # Save parameter lists
        list_offset = 3
        object_offset = 3 * len(lists)
        for list in lists:
            stream.u32(list.hash)
            stream.u32((len(list.children) << 16) | list_offset)
            stream.u32((len(list.objects) << 16) | object_offset)
            list_offset += 3 * len(list.children) - 3
            object_offset += 2 * len(list.objects) - 3
        
        # Save parameter objects
        offset = 2 * len(objects)
        for object in objects:
            stream.u32(object.hash)
            stream.u32((len(object.parameters) << 16) | offset)
            offset += 2 * len(object.parameters) - 2
        
        # Save parameters
        offset = 2 * len(parameters)
        for parameter in parameters:
            target_offset = offset
            if parameter.type in string_types:
                target_offset += data_stream.size() // 4
                target_offset += string_offsets[parameter.value] // 4
            else:
                target_offset += data_offsets[parameter] // 4

            stream.u32(parameter.hash)
            stream.u32((parameter.type << 24) | target_offset)
            offset -= 2
        
        stream.write(data_stream.get())
        stream.write(string_stream.get())
        return stream.get()


class PMAAFile:
    endianness: str
    version: int
    shift_jis: bool

    effect_version: int
    effect_type: str

    align: bool
    minimize_strings: bool | None
    string_padding: int | None

    root: ParameterList

    def __init__(self):
        self.endianness = "<"
        self.version = 1
        self.shift_jis = False

        self.effect_version = 0
        self.effect_type = "aglenv"

        # These are inconsistent quirks of Nintendo's tooling
        self.align = True
        self.minimize_strings = None
        self.string_padding = None

        self.root = ParameterList()

    def parse(self, data: bytes) -> None:
        if len(data) < 8:
            raise ParseError("file is too small")
        
        # Determine endianness
        if data[:4] == b"AAMP": self.endianness = "<"
        elif data[:4] == b"PMAA": self.endianness = ">"
        else:
            raise ParseError("magic number is invalid")
        
        # Determine version and parse file
        self.version = struct.unpack_from(self.endianness + "I", data, 4)[0]

        parser: PMAADecoderType
        if self.version == 1: parser = PMAADecoderV1(self)
        elif self.version == 2: parser = PMAADecoderV2(self)
        else:
            raise ParseError("unsupported version number")
        parser.parse(data)
    
    def save(self) -> bytes:
        encoder: PMAAEncoderType
        if self.version == 1: encoder = PMAAEncoderV1()
        elif self.version == 2: encoder = PMAAEncoderV2()
        else:
            raise SaveError("unsupported version number")
        return encoder.save(self)
