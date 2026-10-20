
from dataclasses import dataclass, field

from jungle.errors import ParseError, SaveError
from jungle.nw import sound
from jungle.streams import StreamIn, StreamOut
from jungle import utils

import enum


class SampleFormat(enum.IntEnum):
    PCM8 = 0
    PCM16 = 1
    ADPCM = 2


def calc_channel_size(format: SampleFormat, samples: int) -> int:
    if format == SampleFormat.PCM8: return samples
    if format == SampleFormat.PCM16: return samples * 2

    # ADPCM
    size = (samples + 13) // 14
    size += (samples + 1) // 2
    return size + 1


@dataclass
class ADPCMContext:
    header: int = 0
    hist1: int = 0
    hist2: int = 0

    def parse(self, stream: StreamIn) -> None:
        self.header = stream.u16()
        self.hist1 = stream.s16()
        self.hist2 = stream.s16()
    
    def save(self, stream: StreamOut) -> None:
        stream.u16(self.header)
        stream.s16(self.hist1)
        stream.s16(self.hist2)


@dataclass
class ADPCMInfo:
    coefs: list[int] = field(default_factory=lambda: [0] * 16)
    main_context: ADPCMContext = field(default_factory=ADPCMContext)
    loop_context: ADPCMContext = field(default_factory=ADPCMContext)
    
    def parse(self, stream: StreamIn) -> None:
        self.coefs = stream.repeat(stream.s16, 16)
        self.main_context.parse(stream)
        self.loop_context.parse(stream)
        stream.pad(2)
    
    def save(self, stream: StreamOut) -> None:
        stream.repeat(self.coefs, stream.s16)
        self.main_context.save(stream)
        self.loop_context.save(stream)
        stream.pad(2)


@dataclass
class ChannelInfo:
    data_ref: sound.SectionReference = \
        field(default_factory=sound.SectionReference)
    adpcm_ref: sound.SectionReference = \
        field(default_factory=sound.SectionReference)
    
    def parse(self, stream: StreamIn) -> None:
        self.data_ref.parse(stream)
        self.adpcm_ref.parse(stream)
        stream.pad(4)
    
    def save(self, stream: StreamOut) -> None:
        self.data_ref.save(stream)
        self.adpcm_ref.save(stream)
        stream.pad(4)


@dataclass
class BFWAVChannel:
    data: bytes = b""
    adpcm_info: ADPCMInfo | None = None


class BFWAVFile:
    endianness: str
    version: int

    sample_format: SampleFormat
    sample_rate: int

    is_looped: bool
    loop_start: int
    num_samples: int
    adjusted_loop_start: int
    channels: list[BFWAVChannel]

    def __init__(self):
        self.endianness = "<"
        self.version = 0x10100

        self.sample_format = SampleFormat.ADPCM
        self.sample_rate = 32000

        self.is_looped = False
        self.loop_start = 0
        self.num_samples = 0
        self.adjusted_loop_start = 0
        self.channels = []
    
    def parse(self, data: bytes) -> None:
        # Parse header and blocks
        file = sound.SoundFile()
        file.parse(data)

        # Verify magic number
        if file.magic != "FWAV":
            raise ParseError("magic number is invalid")

        # Read header info
        self.endianness = file.endianness
        self.version = file.version
        if self.version not in [0x10100, 0x10200]:
            raise ParseError("unsupported version number")
        
        # Parse the DATA block
        stream = StreamIn(file.blocks[0x7001], self.endianness)
        if stream.ascii(4) != "DATA": raise ParseError("DATA block has invalid identifier")
        if stream.u32() != stream.size(): raise ParseError("DATA block has invalid size")
        data = stream.readall()

        # Parse the INFO block
        stream = StreamIn(file.blocks[0x7000], self.endianness)
        if stream.ascii(4) != "INFO": raise ParseError("INFO block has invalid identifier")
        if stream.u32() != stream.size(): raise ParseError("INFO block has invalid size")
        
        self.sample_format = utils.parse_enum(stream.u8(), SampleFormat)
        self.is_looped = stream.bool()
        stream.pad(2)

        self.sample_rate = stream.u32()
        self.loop_start = stream.u32()
        self.num_samples = stream.u32()
        if self.version == 0x10200:
            self.adjusted_loop_start = stream.u32()
        else:
            stream.pad(4)

        base = stream.tell()
        channel_refs = []
        for i in range(stream.u32()):
            ref = sound.SectionReference()
            ref.parse(stream)
            channel_refs.append(ref)

        # How many bytes does the channel use in the DATA section
        channel_size = calc_channel_size(self.sample_format, self.num_samples)

        self.channels = []
        for ref in channel_refs:
            stream.seek(base + ref.offset)

            info = ChannelInfo()
            info.parse(stream)

            channel = BFWAVChannel()
            channel.data = data[info.data_ref.offset:info.data_ref.offset+channel_size]
            if info.adpcm_ref.valid():
                stream.seek(base + ref.offset + info.adpcm_ref.offset)
                channel.adpcm_info = ADPCMInfo()
                channel.adpcm_info.parse(stream)
            self.channels.append(channel)
    
    def save(self) -> bytes:
        if self.version not in [0x10100, 0x10200]:
            raise SaveError("unsupported version number")
        
        info_stream = StreamOut(self.endianness)
        info_stream.ascii("INFO")
        info_stream.skip(4) # Block size
        info_stream.u8(self.sample_format)
        info_stream.bool(self.is_looped)
        info_stream.pad(2)
        info_stream.u32(self.sample_rate)
        info_stream.u32(self.loop_start)
        info_stream.u32(self.num_samples)
        if self.version == 0x10200:
            info_stream.u32(self.adjusted_loop_start)
        else:
            info_stream.pad(4)
        info_stream.u32(len(self.channels))

        data_stream = StreamOut(self.endianness)
        data_stream.ascii("DATA")
        data_stream.skip(4) # Block size

        channel_base = 4 + len(self.channels) * 8
        adpcm_base = channel_base + len(self.channels) * 0x14

        channel_stream = StreamOut(self.endianness)
        adpcm_stream = StreamOut(self.endianness)
        for channel in self.channels:
            channel_offset = channel_base + channel_stream.tell()

            ref = sound.SectionReference()
            ref.type = 0x7100
            ref.offset = channel_offset
            ref.save(info_stream)

            if self.version == 0x10100:
                data_stream.align(32)
            else:
                data_stream.align(64)

            channel_info = ChannelInfo()
            channel_info.data_ref = sound.SectionReference()
            channel_info.data_ref.type = 0x1F00
            channel_info.data_ref.offset = data_stream.tell() - 8
            if channel.adpcm_info:
                adpcm_offset = adpcm_base + adpcm_stream.tell()
                channel.adpcm_info.save(adpcm_stream)

                channel_info.adpcm_ref = sound.SectionReference()
                channel_info.adpcm_ref.type = 0x300
                channel_info.adpcm_ref.offset = adpcm_offset - channel_offset
            
            channel_info.save(channel_stream)
            
            data_stream.write(channel.data)
        data_stream.align(8)

        info_stream.write(channel_stream.get())
        info_stream.write(adpcm_stream.get())
        info_stream.align(32)

        info_stream.seek(4); info_stream.u32(info_stream.size())
        data_stream.seek(4); data_stream.u32(data_stream.size())

        file = sound.SoundFile()
        file.magic = "FWAV"
        file.endianness = self.endianness
        file.version = self.version
        file.blocks = {
            0x7000: info_stream.get(),
            0x7001: data_stream.get()
        }
        return file.save()
