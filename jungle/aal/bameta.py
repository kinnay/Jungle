
from jungle.errors import ParseError, SaveError
from jungle import streams

import struct


class AssetType:
    WAVE = 0
    STREAM = 1


class Flags:
    LOOPED = 4


class StreamTrack:
    def __init__(self):
        self.channels = 0
        self.volume = 1.0
    
    def parse(self, stream):
        self.channels = stream.u32()
        self.volume = stream.float()
    
    def save(self, stream):
        stream.u32(self.channels)
        stream.float(self.volume)


class MarkerInfo:
    def __init__(self):
        self.id = 0
        self.name = ""
        self.start = 0
        self.length = 0


class ExtEntry:
    def __init__(self):
        self.name = ""
        self.value = 0


class StringTableIn:
    """A string table that works around a bug from Nintendo's tooling.

    Nintendo's files have wrong string table offsets if a string
    contains non-ascii characters. This string table works around
    that behavior.
    """

    def __init__(self):
        self.strings = {}
    
    def get(self, offset):
        if offset not in self.strings:
            raise ParseError("string table offset is invalid")
        return self.strings[offset]

    def parse(self, stream):
        if stream.ascii(4) != "STRG":
            raise ParseError("STRG section has invalid identifier")
        size = stream.u32()

        offset = 0
        end = stream.tell() + size
        while stream.tell() < end:
            string = stream.string()
            self.strings[offset] = string
            offset += len(string) + 1


class StringTableOut:
    """A string table that mimics a bug from Nintendo's tooling.

    Nintendo's files have wrong string table offsets if a string
    contains non-ascii characters. This string table emulates
    that behavior.
    """

    def __init__(self):
        self.strings = {}
        self.offset = 0
        self.bytes = 0

    def add(self, string):
        if string in self.strings:
            return self.strings[string]

        offset = self.offset
        self.strings[string] = offset
        self.offset += len(string) + 1
        self.bytes += len(string.encode()) + 1
        return offset

    def size(self):
        return 8 + self.bytes
    
    def save(self, stream):
        stream.ascii("STRG")
        stream.u32(self.bytes)
        for string in self.strings:
            stream.string(string)


class BAMETAFile:
    def __init__(self):
        self.version = 0x100
        self.endianness = "<"

        self.name = ""
        self.num_output_samples = 0
        self.type = AssetType.WAVE
        self.num_channels = 1
        self.flags = 0
        self.unk2 = 0
        self.sample_rate = 32000
        self.loop_start = 0
        self.num_samples = 0
        self.decibel = 0.0
        self.stream_tracks = []
        self.amplitude_peak = 1.0

        self.markers = []
        self.ext = []

    def parse(self, data):
        # Determine endianness
        if len(data) < 6:
            raise ParseError("file is too small")
        
        bom = struct.unpack_from(">H", data, 4)[0]
        self.endianness = ">" if bom == 0xFEFF else "<"

        # Parse file
        stream = streams.StreamIn(data, self.endianness)
        if stream.ascii(4) != "AMTA": raise ParseError("magic number is invalid")
        if stream.u16() != 0xFEFF: raise ParseError("BOM is invalid")

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
        self.type = stream.u8()
        self.num_channels = stream.u8()
        num_tracks = stream.u8()
        self.flags = stream.u8()
        self.unk2 = stream.float()
        self.sample_rate = stream.u32()
        self.loop_start = stream.u32()
        self.num_samples = stream.u32()
        self.decibel = stream.float()

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
    
    def save(self):
        if self.version not in [0x100, 0x300, 0x400]:
            raise SaveError("unsupported version number")

        string_table = StringTableOut()

        data_stream = streams.StreamOut(self.endianness)
        data_stream.ascii("DATA")
        data_stream.u32(0x64 if self.version == 0x400 else 0x60)
        data_stream.u32(string_table.add(self.name))
        data_stream.u32(self.num_output_samples)
        data_stream.u8(self.type)
        data_stream.u8(self.num_channels)
        data_stream.u8(len(self.stream_tracks))
        data_stream.u8(self.flags)
        data_stream.float(self.unk2)
        data_stream.u32(self.sample_rate)
        data_stream.u32(self.loop_start)
        data_stream.u32(self.num_samples)
        data_stream.float(self.decibel)

        for track in self.stream_tracks:
            track.save(data_stream)
        for i in range(8 - len(self.stream_tracks)):
            track = StreamTrack()
            track.save(data_stream)
        
        if self.version == 0x400:
            data_stream.float(self.amplitude_peak)
        
        mark_stream = streams.StreamOut(self.endianness)
        mark_stream.ascii("MARK")
        mark_stream.u32(0x4 + len(self.markers) * 0x10)
        mark_stream.u32(len(self.markers))
        for marker in self.markers:
            mark_stream.u32(marker.id)
            mark_stream.u32(string_table.add(marker.name))
            mark_stream.u32(marker.start)
            mark_stream.u32(marker.length)
        
        if self.version in [0x300, 0x400]:
            ext_stream = streams.StreamOut(self.endianness)
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

        stream = streams.StreamOut(self.endianness)
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
