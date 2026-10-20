
from dataclasses import dataclass
from jungle.errors import ParseError, SaveError
from jungle.streams import StreamIn, StreamOut
from jungle import utils

import enum
import struct


class AssetType(enum.IntEnum):
    Wave = 0
    Stream = 1


class Flags(enum.IntFlag):
    Stream = 1
    Prefetch = 2
    Looped = 4
    Opus = 16


@dataclass
class StreamTrack:
    channels: int = 0
    volume: float = 1.0
    
    def parse(self, stream: StreamIn) -> None:
        self.channels = stream.u32()
        self.volume = stream.float()
    
    def save(self, stream: StreamOut) -> None:
        stream.u32(self.channels)
        stream.float(self.volume)


@dataclass
class MarkerInfo:
    id: int = 0
    name: str = ""
    start: int = 0
    length: int = 0


@dataclass
class ExtEntry:
    name: str = ""
    value: float = 0.0


class StringTableIn:
    """
    A string table that works around a bug from Nintendo's tooling.

    Nintendo's files have wrong string table offsets if a string
    contains non-ascii characters. This string table works around
    that behavior.
    """

    _strings: dict[int, str]

    def __init__(self):
        self._strings = {}
    
    def get(self, offset: int) -> str:
        if offset not in self._strings:
            raise ParseError("string table offset is invalid")
        return self._strings[offset]

    def parse(self, stream: StreamIn) -> None:
        if stream.ascii(4) != "STRG":
            raise ParseError("STRG section has invalid identifier")
        size = stream.u32()

        offset = 0
        end = stream.tell() + size
        while stream.tell() < end:
            string = stream.string()
            self._strings[offset] = string
            offset += len(string) + 1


class StringTableOut:
    """
    A string table that mimics a bug from Nintendo's tooling.

    Nintendo's files have wrong string table offsets if a string
    contains non-ascii characters. This string table emulates
    that behavior.
    """

    _strings: dict[str, int]
    _offset: int = 0
    _bytes: int = 0

    def __init__(self):
        self._strings = {}
        self._offset = 0
        self._bytes = 0

    def add(self, string: str) -> int:
        if string in self._strings:
            return self._strings[string]

        offset = self._offset
        self._strings[string] = offset
        self._offset += len(string) + 1
        self._bytes += len(string.encode()) + 1
        return offset

    def size(self) -> int:
        return 8 + self._bytes
    
    def save(self, stream: StreamOut) -> None:
        stream.ascii("STRG")
        stream.u32(self._bytes)
        for string in self._strings:
            stream.string(string)


class BAMETAFile:
    version: int
    endianness: str

    name: str
    num_output_samples: int
    type: AssetType
    num_channels: int
    flags: Flags
    amplitude_rms: float
    sample_rate: int
    loop_start: int
    num_samples: int
    loudness: float
    stream_tracks: list[StreamTrack]
    amplitude_peak: float

    markers: list[MarkerInfo]
    ext: list[ExtEntry]

    def __init__(self):
        self.version = 0x100
        self.endianness = "<"

        self.name = ""
        self.num_output_samples = 0
        self.type = AssetType.Wave
        self.num_channels = 1
        self.flags = Flags(0)
        self.amplitude_rms = 0.0
        self.sample_rate = 32000
        self.loop_start = 0
        self.num_samples = 0
        self.loudness = 0.0
        self.stream_tracks = []
        self.amplitude_peak = 1.0

        self.markers = []
        self.ext = []

    def parse(self, data: bytes) -> None:
        # Determine endianness
        if len(data) < 6:
            raise ParseError("file is too small")
        
        bom = struct.unpack_from(">H", data, 4)[0]
        self.endianness = ">" if bom == 0xFEFF else "<"

        # Parse file
        stream = StreamIn(data, self.endianness)
        if stream.ascii(4) != "AMTA":
            raise ParseError("magic number is invalid")
        if stream.u16() != 0xFEFF:
            raise ParseError("BOM is invalid")

        self.version = stream.u16()
        if self.version not in [0x100, 0x300, 0x400]:
            raise ParseError("unsupported version number")

        if stream.u32() != len(data):
            raise ParseError("file size is invalid")
        
        data_offset = stream.u32()
        marker_offset = stream.u32()
        if self.version in [0x300, 0x400]:
            ext_offset = stream.u32()
        string_offset = stream.u32()

        stream.seek(string_offset)
        string_table = StringTableIn()
        string_table.parse(stream)

        stream.seek(data_offset)
        if stream.ascii(4) != "DATA":
            raise ParseError("DATA section has invalid identifier")
        stream.skip(4)

        self.name = string_table.get(stream.u32())
        self.num_output_samples = stream.u32()
        self.type = utils.parse_enum(stream.u8(), AssetType)
        self.num_channels = stream.u8()
        num_tracks = stream.u8()
        self.flags = utils.parse_flags(stream.u8(), Flags)
        self.amplitude_rms = stream.float()
        self.sample_rate = stream.u32()
        self.loop_start = stream.u32()
        self.num_samples = stream.u32()
        self.loudness = stream.float()

        self.stream_tracks = []
        for i in range(8):
            track = StreamTrack()
            track.parse(stream)
            if i < num_tracks:
                self.stream_tracks.append(track)
        
        self.amplitude_peak = 1.0
        if self.version == 0x400:
            self.amplitude_peak = stream.float()
        
        stream.seek(marker_offset)
        if stream.ascii(4) != "MARK":
            raise ParseError("MARK section has invalid identifier")
        stream.skip(4)
        
        self.markers = []
        for i in range(stream.u32()):
            info = MarkerInfo()
            info.id = stream.u32()
            info.name = string_table.get(stream.u32())
            info.start = stream.u32()
            info.length = stream.u32()
            self.markers.append(info)
        
        self.ext = []
        if self.version in [0x300, 0x400]:
            stream.seek(ext_offset)
            if stream.ascii(4) != "EXT_":
                raise ParseError("EXT_ section has invalid identifier")
            stream.skip(4)

            for i in range(stream.u32()):
                entry = ExtEntry()
                entry.name = string_table.get(stream.u32())
                entry.value = stream.float()
                self.ext.append(entry)
    
    def save(self) -> bytes:
        if self.version not in [0x100, 0x300, 0x400]:
            raise SaveError("unsupported version number")

        string_table = StringTableOut()

        data_stream = StreamOut(self.endianness)
        data_stream.ascii("DATA")
        data_stream.u32(0x64 if self.version == 0x400 else 0x60)
        data_stream.u32(string_table.add(self.name))
        data_stream.u32(self.num_output_samples)
        data_stream.u8(self.type)
        data_stream.u8(self.num_channels)
        data_stream.u8(len(self.stream_tracks))
        data_stream.u8(self.flags)
        data_stream.float(self.amplitude_rms)
        data_stream.u32(self.sample_rate)
        data_stream.u32(self.loop_start)
        data_stream.u32(self.num_samples)
        data_stream.float(self.loudness)

        for track in self.stream_tracks:
            track.save(data_stream)
        for i in range(8 - len(self.stream_tracks)):
            track = StreamTrack()
            track.save(data_stream)
        
        if self.version == 0x400:
            data_stream.float(self.amplitude_peak)
        
        mark_stream = StreamOut(self.endianness)
        mark_stream.ascii("MARK")
        mark_stream.u32(0x4 + len(self.markers) * 0x10)
        mark_stream.u32(len(self.markers))
        for marker in self.markers:
            mark_stream.u32(marker.id)
            mark_stream.u32(string_table.add(marker.name))
            mark_stream.u32(marker.start)
            mark_stream.u32(marker.length)
        
        if self.version in [0x300, 0x400]:
            ext_stream = StreamOut(self.endianness)
            ext_stream.ascii("EXT_")
            ext_stream.u32(0x4 + len(self.ext) * 8)
            ext_stream.u32(len(self.ext))
            for entry in self.ext:
                ext_stream.u32(string_table.add(entry.name))
                ext_stream.float(entry.value)

        data_offset = 0x18 if self.version == 0x100 else 0x1C
        mark_offset = data_offset + data_stream.size()
        if self.version in [0x300, 0x400]:
            ext_offset = mark_offset + mark_stream.size()
            string_offset = ext_offset + ext_stream.size()
        else:
            string_offset = mark_offset + mark_stream.size()
        
        file_size = string_offset + string_table.size()
        file_size = (file_size + 3) & ~3

        stream = StreamOut(self.endianness)
        stream.ascii("AMTA")
        stream.u16(0xFEFF)
        stream.u16(self.version)
        stream.u32(file_size)
        stream.u32(data_offset)
        stream.u32(mark_offset)
        if self.version in [0x300, 0x400]:
            stream.u32(ext_offset)
        stream.u32(string_offset)
        stream.write(data_stream.get())
        stream.write(mark_stream.get())
        if self.version in [0x300, 0x400]:
            stream.write(ext_stream.get())
        
        string_table.save(stream)
        stream.align(4)

        return stream.get()
