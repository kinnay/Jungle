
from dataclasses import dataclass, field

from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut, Object

import uuid


@dataclass
class CGuid:
    value: str = "00000000-0000-0000-0000-000000000000"

    def __str__(self) -> str:
        return self.value

    def decode(self, stream: StreamIn) -> None:
        data = stream.read(16)
        guid = uuid.UUID(bytes=data)
        self.value = str(guid)

    def encode(self, stream: StreamOut) -> None:
        guid = uuid.UUID(self.value)
        stream.write(guid.bytes)


CObjectId = CGuid


@dataclass
class CObjectTag:
    type: str = "XXXX"
    id: CGuid = field(default_factory=CGuid)

    def decode(self, stream: StreamIn) -> None:
        self.type = stream.ascii(4)
        self.id = stream.extract(CGuid)

    def encode(self, stream: StreamOut) -> None:
        stream.ascii(self.type)
        stream.add(self.id)


@dataclass
class CAssetHeader:
    type: int = 0
    version: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.type = stream.u16()
        self.version = stream.u16()

    def encode(self, stream: StreamOut) -> None:
        stream.u16(self.type)
        stream.u16(self.version)


@dataclass
class CFormDescriptor:
    type: str = "XXXX"
    version: int = 0
    data: bytes = b""

    def decode(self, stream: StreamIn) -> None:
        if stream.ascii(4) != "RFRM":
            raise ParseError("invalid magic number") 

        size = stream.u64()
        stream.pad(8)
        self.type = stream.ascii(4)
        self.version = stream.u32()
        if stream.u32() != self.version:
            raise ParseError("inconsistent version number")
        self.data = stream.read(size)

    def encode(self, stream: StreamOut) -> None:
        stream.ascii("RFRM")
        stream.u64(len(self.data))
        stream.pad(8)
        stream.ascii(self.type)
        stream.u32(self.version)
        stream.u32(self.version)
        stream.write(self.data)

    @staticmethod
    def fromstream(stream: StreamIn, type: str, version: int) -> bytes:
        descriptor = CFormDescriptor()
        descriptor.decode(stream)

        if descriptor.type != type:
            raise ParseError("CFormDescriptor has unexpected type")
        if descriptor.version != version:
            raise ParseError("CFormDescriptor has unexpected version number")

        return descriptor.data

    @staticmethod
    def fromdata(data: bytes, type: str, version: int) -> bytes:
        stream = StreamIn(data, ">")
        return CFormDescriptor.fromstream(stream, type, version)


@dataclass
class CChunkDescriptor:
    type: str = "XXXX"
    version: int = 0
    data: bytes = b""

    def decode(self, stream: StreamIn) -> None:
        self.type = stream.ascii(4)
        size = stream.u64()
        self.version = stream.u32()
        stream.pad(8)
        self.data = stream.read(size)

    def encode(self, stream: StreamOut) -> None:
        stream.ascii(self.type)
        stream.u64(len(self.data))
        stream.u32(self.version)
        stream.u64(0)
        stream.write(self.data)


@dataclass
class CVector3f:
    x: float = .0
    y: float = .0
    z: float = .0

    def decode(self, stream: StreamIn) -> None:
        self.x = stream.float()
        self.y = stream.float()
        self.z = stream.float()
    
    def encode(self, stream: StreamOut) -> None:
        stream.float(self.x)
        stream.float(self.y)
        stream.float(self.z)


class CVector4i:
    x: int = 0
    y: int = 0
    z: int = 0
    w: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.x = stream.s32()
        self.y = stream.s32()
        self.z = stream.s32()
        self.w = stream.s32()
    
    def encode(self, stream: StreamOut) -> None:
        stream.s32(self.x)
        stream.s32(self.y)
        stream.s32(self.z)
        stream.s32(self.w)


class CColor4f:
    red: float = .0
    green: float = .0
    blue: float = .0
    alpha: float = .0

    def decode(self, stream: StreamIn) -> None:
        self.red = stream.float()
        self.green = stream.float()
        self.blue = stream.float()
        self.float = stream.float()
    
    def encode(self, stream: StreamOut) -> None:
        stream.float(self.red)
        stream.float(self.green)
        stream.float(self.blue)
        stream.float(self.alpha)


class CAABox:
    low: CVector3f = field(default_factory=CVector3f)
    high: CVector3f = field(default_factory=CVector3f)

    def decode(self, stream: StreamIn) -> None:
        self.low.decode(stream)
        self.high.decode(stream)

    def encode(self, stream: StreamOut) -> None:
        self.low.encode(stream)
        self.high.encode(stream)


class CQuaternion:
    w: float
    vector: CVector3f

    def decode(self, stream: StreamIn) -> None:
        self.w = stream.float()
        self.vector.decode(stream)

    def encode(self, stream: StreamOut) -> None:
        stream.float(self.w)
        stream.add(self.vector)
