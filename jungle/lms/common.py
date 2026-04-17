
from jungle.errors import ParseError
from jungle import streams
import struct


def determine_bucket(label, num_buckets):
    hash = 0
    for char in label:
        hash = hash * 0x492 + ord(char)
    return (hash & 0xFFFFFFFF) % num_buckets


class Encoding:
    UTF8 = 0
    UTF16 = 1
    UTF32 = 2


class MessageFile:
    def __init__(self):
        self.magic = "xxxxxxxx"
        self.endianness = "<"
        self.encoding = Encoding.UTF8
        self.version = 0
        self.blocks = {}
        
    def parse(self, data):
        # Determine endianness
        if len(data) < 10:
            raise ParseError("file is too small")
        
        bom = struct.unpack_from(">H", data, 8)[0]
        self.endianness = ">" if bom == 0xFEFF else "<"

        # Parse file
        stream = streams.StreamIn(data, self.endianness)
        self.magic = stream.ascii(8)

        if stream.u16() != 0xFEFF:
            raise ParseError("BOM is invalid")
        
        stream.pad(2)

        self.encoding = stream.u8()
        if self.encoding not in [Encoding.UTF8, Encoding.UTF16, Encoding.UTF32]:
            raise ParseError("text encoding is invalid")
        
        self.version = stream.u8()

        num_blocks = stream.u16()
        stream.pad(2)

        if stream.u32() != len(data):
            raise ParseError("file size is invalid")
        
        stream.pad(10)

        for i in range(num_blocks):
            type = stream.ascii(4)
            size = stream.u32()
            stream.pad(8)
            self.blocks[type] = stream.read(size)
            stream.pad((16 - size % 16) % 16, b"\xAB")
    
    def parse_labels(self, data):
        stream = streams.StreamIn(data, self.endianness)

        labels = {}
        for i in range(stream.u32()):
            count = stream.u32()
            offset = stream.u32()
            with stream.jump(offset):
                for j in range(count):
                    label = stream.ascii(stream.u8())
                    index = stream.u32()
                    labels[label] = index
        return labels

    def save(self):
        file_size = 0x20
        for block in self.blocks.values():
            file_size += 16 + (len(block) + 15) & ~15
        
        stream = streams.StreamOut(self.endianness)
        stream.ascii(self.magic)
        stream.u16(0xFEFF)
        stream.pad(2)
        stream.u8(self.encoding)
        stream.u8(self.version)
        stream.u16(len(self.blocks))
        stream.pad(2)
        stream.u32(file_size)
        stream.pad(10)

        for type, data in self.blocks.items():
            stream.ascii(type)
            stream.u32(len(data))
            stream.pad(8)
            stream.write(data)
            stream.pad((16 - len(data) % 16) % 16, b"\xAB")
        return stream.get()
    
    def save_labels(self, labels, num_buckets):
        buckets = [[] for i in range(num_buckets)]
        sizes = [0] * num_buckets
        
        for label, index in labels.items():
            bucket = determine_bucket(label, num_buckets)
            buckets[bucket].append((label, index))
            sizes[bucket] += 5 + len(label)
        
        stream = streams.StreamOut(self.endianness)
        stream.u32(num_buckets)

        offset = 4 + num_buckets * 8
        for i in range(num_buckets):
            stream.u32(len(buckets[i]))
            stream.u32(offset)
            offset += sizes[i]
        
        for bucket in buckets:
            for label, index in bucket:
                stream.u8(len(label))
                stream.ascii(label)
                stream.u32(index)
        return stream.get()
