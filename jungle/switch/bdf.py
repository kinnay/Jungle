
from dataclasses import dataclass

from jungle.errors import ParseError, SaveError
from jungle.streams import StreamIn, StreamOut

import enum


class TrustedCertStatus(enum.IntEnum):
    Invalid = -1
    Removed = 0
    EnabledTrusted = 1
    EnabledNotTrusted = 2
    Revoked = 3


@dataclass
class BDFEntry:
    id: int = 0
    status: TrustedCertStatus = TrustedCertStatus.Invalid
    data: bytes = b""


class BDFFile:
    entries: list[BDFEntry]

    def __init__(self):
        self.entries = []

    def parse(self, data: bytes) -> None:
        stream = StreamIn(data, "<")
        if stream.ascii(4) != "sslT":
            raise ParseError("magic number is invalid")

        count = stream.u32()
        self.entries = []
        for i in range(count):
            self.entries.append(self._parse_entry(stream))

    def save(self) -> bytes:
        stream = StreamOut("<")
        stream.ascii("sslT")
        stream.u32(len(self.entries))

        offset = len(self.entries) * 16
        for entry in self.entries:
            stream.u32(entry.id)
            stream.s32(entry.status)
            stream.u32(len(entry.data))
            stream.u32(offset)
            offset += (len(entry.data) + 3) & ~3

        for entry in self.entries:
            stream.write(entry.data)
            stream.align(4)
        
        return stream.get()

    def _parse_entry(self, stream: StreamIn) -> BDFEntry:
        id = stream.u32()

        status_value = stream.s32()
        if status_value not in TrustedCertStatus:
            raise ParseError("certificate status is invalid")

        status = TrustedCertStatus(status_value)

        size = stream.u32()
        offset = stream.u32()
        with stream.jump(8 + offset):
            data = stream.read(size)

        return BDFEntry(id, status, data)
