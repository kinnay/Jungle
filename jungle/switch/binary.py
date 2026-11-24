
from dataclasses import dataclass, field

from jungle.errors import ParseError, SaveError
from jungle.streams import StreamIn, StreamOut
from jungle import utils

import enum
import struct


class BinaryFileFlags(enum.IntFlag):
    IsRelocated = 1


@dataclass
class BinaryFileHeader:
    magic: str = " " * 8
    major_version: int = 0
    minor_version: int = 0
    micro_version: int = 0
    alignment: int = 0
    address_size: int = 64
    filename_offset: int = 0
    flags: BinaryFileFlags = BinaryFileFlags(0)
    first_section_offset: int = 0
    relocation_table_offset: int = 0
    filesize: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.magic = stream.ascii(8)
        self.micro_version = stream.u8()
        self.minor_version = stream.u8()
        self.major_version = stream.u16()

        if stream.u16() != 0xFEFF:
            raise ParseError("invalid byte order mark")

        self.alignment = stream.u8()
        self.address_size = stream.u8()
        self.filename_offset = stream.u32()
        self.flags = utils.parse_flags(stream.u16(), BinaryFileFlags)
        self.first_section_offset = stream.u16()
        self.relocation_table_offset = stream.u32()
        self.filesize = stream.u32()

    def encode(self, stream: StreamOut) -> None:
        if len(self.magic) != 8:
            raise SaveError("magic number must contain 8 characters")
        
        stream.ascii(self.magic)
        stream.u8(self.micro_version)
        stream.u8(self.minor_version)
        stream.u16(self.major_version)
        stream.u16(0xFEFF)
        stream.u8(self.alignment)
        stream.u8(self.address_size)
        stream.u32(self.filename_offset)
        stream.u16(self.flags)
        stream.u16(self.first_section_offset)
        stream.u32(self.relocation_table_offset)
        stream.u32(self.filesize)


@dataclass
class BinaryBlockHeader:
    type: str = "XXXX"
    offset: int = 0
    size: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.type = stream.ascii(4)
        self.offset = stream.u32()
        self.size = stream.u32()
        stream.pad(4)

    def encode(self, stream: StreamOut) -> None:
        stream.ascii(self.type)
        stream.u32(self.offset)
        stream.u32(self.size)
        stream.pad(4)


@dataclass
class BinaryFile:
    magic: str = " " * 8
    major_version: int = 0
    minor_version: int = 0
    micro_version: int = 0
    endianness: str = "<"
    alignment: int = 0
    address_size: int = 64
    filename_offset: int = 0
    flags: BinaryFileFlags = BinaryFileFlags(0)

    header: bytes = b""
    blocks: list[tuple[str, bytes]] = field(default_factory=list)
    relocation_table: RelocationTable | None = None
    body: bytes = b""
    
    def parse(self, data: bytes) -> None:
        if len(data) < 32:
            raise ParseError("file is too small")

        bom = struct.unpack_from(">H", data, 12)[0]
        self.endianness = ">" if bom == 0xFEFF else "<"

        stream = StreamIn(data, self.endianness)

        header = BinaryFileHeader()
        header.decode(stream)

        if header.filesize > len(data):
            raise ParseError("file size is invalid")

        self.magic = header.magic
        self.major_version = header.major_version
        self.minor_version = header.minor_version
        self.micro_version = header.micro_version
        self.alignment = header.alignment
        self.address_size = header.address_size
        self.filename_offset = header.filename_offset
        self.flags = header.flags

        self.header = stream.read(header.first_section_offset - stream.tell())

        self.blocks = []
        stream.seek(header.first_section_offset)
        while True:
            position = stream.tell()

            block = BinaryBlockHeader()
            block.decode(stream)

            body = stream.read(block.size - 16)
            self.blocks.append((block.type, body))

            if block.offset == 0:
                break

            stream.seek(position + block.offset)

        self.relocation_table = None
        if header.relocation_table_offset:
            stream.seek(header.relocation_table_offset)
            self.relocation_table = stream.extract(RelocationTable)

        stream.seek(header.filesize)
        self.body = stream.readall()

    def save(self) -> bytes:
        relocation_table_offset = 0x20 + len(self.header)
        for type, block in self.blocks:
            relocation_table_offset += 16 + len(block)

        relocation_table = b""
        if self.relocation_table:
            self.relocation_table.offset = relocation_table_offset

            stream = StreamOut(self.endianness)
            stream.add(self.relocation_table)
            relocation_table = stream.get()

        header = BinaryFileHeader()
        header.magic = self.magic
        header.major_version = self.major_version
        header.minor_version = self.minor_version
        header.micro_version = self.micro_version
        header.alignment = self.alignment
        header.address_size = self.address_size
        header.filename_offset = self.filename_offset
        header.flags = self.flags
        header.first_section_offset = 0x20 + len(self.header)
        if self.relocation_table:
            header.relocation_table_offset = relocation_table_offset
        header.filesize = relocation_table_offset + len(relocation_table)
        
        stream = StreamOut(self.endianness)
        stream.add(header)
        stream.write(self.header)

        for i, (type, content) in enumerate(self.blocks):
            block_header = BinaryBlockHeader(
                type,
                len(content) + 16 if i != len(self.blocks) - 1 else 0,
                len(content) + 16
            )
            stream.add(block_header)
            stream.write(content)
        
        stream.write(relocation_table)
        stream.write(self.body)
        return stream.get()

    def count(self, type: str) -> int:
        count = 0
        for block_type, block_data in self.blocks:
            if type == block_type:
                count += 1
        return count


class StringTableBuilder:
    _base: int
    _strings: list[str]
    _offsets: dict[str, int]
    _dirty: bool

    def __init__(self, address: int = 0):
        self._base = address
        self._strings = []
        self._offsets = {}
        self._dirty = False

    def encode(self, stream: StreamOut) -> None:
        self._update_offsets()

        stream.u32(len(self._strings))
        stream.pad(4)
        for string in self._strings:
            stream.u16(len(string))
            stream.ascii(string)
            stream.pad(1)
            stream.align(2)
        stream.align(8)

    def update_address(self, address: int) -> None:
        self._base = address

    def add(self, string: str) -> None:
        if string not in self._strings:
            self._strings.append(string)
            self._dirty = True

    def address(self, string: str) -> int:
        self._update_offsets()
        return self._base + self._offsets[string]

    def size(self) -> int:
        """
        Calculates the total size of the string pool, including the block
        header.
        """
        size = 24
        for string in self._strings:
            size += 2 + len(string) + 1
            size = (size + 1) & ~1
        return (size + 7) & ~7

    def _update_offsets(self) -> None:
        if not self._dirty:
            return
        
        self._strings.sort(key=self._reverse_bits)

        self._offsets = {"": 20}

        offset = 24
        for string in self._strings:
            self._offsets[string] = offset
            offset += 2 + len(string) + 1
            offset = (offset + 1) & ~1

        self._dirty = False

    def _reverse_bits(self, string: str) -> bytes:
        string = string[::-1]

        data = []
        for char in string.encode():
            bits = f"{char:08b}"[::-1]
            data.append(int(bits, 2))
        return bytes(data)


@dataclass
class DictionaryNode:
    bit_index: int = 0
    left_index: int = 0
    right_index: int = 0
    address: int = 0

    def encode(self, stream: StreamOut) -> None:
        stream.s32(self.bit_index)
        stream.u16(self.left_index)
        stream.u16(self.right_index)
        stream.u64(self.address)

    def decode(self, stream: StreamIn) -> None:
        self.bit_index = stream.s32()
        self.left_index = stream.u16()
        self.right_index = stream.u16()
        self.address = stream.u64()


class DictionaryBuilder:
    _string_table: StringTableBuilder
    _strings: list[str]

    def __init__(self, string_table: StringTableBuilder):
        self._string_table = string_table
        self._strings = []

    def encode(self, stream: StreamOut) -> None:
        root = DictionaryNode(-1, 0, 0, self._string_table.address(""))

        nodes = [root]
        strings = [""] + self._strings
        for string in self._strings:
            # This loop searches for the edge where we have to insert the new
            # node.
            parent_index = 0
            while True:
                parent = nodes[parent_index]

                bit = self._extract_bit(string, parent.bit_index)
                child_index = parent.right_index if bit else parent.left_index

                differing_bit_index = self._find_differing_bit_index(
                    string, strings[child_index]
                )

                child_bit_index = nodes[child_index].bit_index
                if child_bit_index <= parent.bit_index or \
                   child_bit_index > differing_bit_index:
                    break

                parent_index = child_index

            if bit:
                parent.right_index = len(nodes)
            else:
                parent.left_index = len(nodes)

            differing_bit = self._extract_bit(string, differing_bit_index)
            address = self._string_table.address(string)
            if differing_bit:
                node = DictionaryNode(
                    differing_bit_index, child_index, len(nodes), address
                )
            else:
                node = DictionaryNode(
                    differing_bit_index, len(nodes), child_index, address
                )
            nodes.append(node)

        stream.ascii("_DIC")
        stream.u32(len(self._strings))
        for node in nodes:
            stream.add(node)

    def add(self, string: str) -> None:
        self._strings.append(string)

    def update_relocations(
        self, base: int, relocator: RelocationTableSection
    ) -> None:
        for i in range(len(self._strings) + 1):
            relocator.add(base + 16 + i * 16)

    def _extract_bit(self, string: str, bit: int) -> int:
        if bit == -1:
            return 0

        byte = ord(string[-(bit // 8) - 1])
        return (byte >> (bit & 7)) & 1

    def _find_differing_bit_index(self, a: str, b: str) -> int:
        index = 0
        limit = min(len(a), len(b)) * 8
        while index < limit:
            if self._extract_bit(a, index) != self._extract_bit(b, index):
                return index
            index += 1
        return index


@dataclass
class RelocationTableEntry:
    offset: int = 0
    repetitions: int = 0
    relocated_words: int = 0
    skipped_words: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.offset = stream.u32()
        self.repetitions = stream.u16()
        self.relocated_words = stream.u8()
        self.skipped_words = stream.u8()

    def encode(self, stream: StreamOut) -> None:
        stream.u32(self.offset)
        stream.u16(self.repetitions)
        stream.u8(self.relocated_words)
        stream.u8(self.skipped_words)


@dataclass
class RelocationTableSection:
    offset: int = 0
    size: int = 0
    relocations: list[int] = field(default_factory=list)

    def add(self, offset: int) -> None:
        if offset not in self.relocations:
            self.relocations.append(offset)

    def make_entries(self) -> list[RelocationTableEntry]:
        if not self.relocations:
            return []

        sorted_relocations = sorted(self.relocations)

        groups = {}
        count = 0
        base = sorted_relocations[0]
        for offset in sorted_relocations:
            if offset == base + count * 8 and count < 255:
                count += 1
            else:
                groups[base] = count
                base = offset
                count = 1
        groups[base] = count

        groups_by_count: dict[int, list[int]] = {}
        for base, count in groups.items():
            if count not in groups_by_count:
                groups_by_count[count] = []
            groups_by_count[count].append(base)

        entries = []
        for count, offsets in groups_by_count.items():
            while offsets:
                entry = RelocationTableEntry(offsets.pop(0), 1, count)

                if not offsets:
                    entries.append(entry)
                    break

                skips = (offsets[0] - entry.offset) // 8 - count
                if skips > 255:
                    entries.append(entry)
                    continue

                entry.skipped_words = skips

                stride = entry.relocated_words + entry.skipped_words
                while entry.repetitions < 0xFFFF:
                    next = entry.offset + entry.repetitions * stride * 8
                    if next not in offsets:
                        break

                    entry.repetitions += 1
                    offsets.remove(next)

                entries.append(entry)

        return sorted(entries, key=lambda entry: entry.offset)


@dataclass
class RelocationTable:
    offset: int = 0
    sections: list[RelocationTableSection] = field(default_factory=list)

    def decode(self, stream: StreamIn) -> None:
        if stream.ascii(4) != "_RLT":
            raise ParseError("relocation table has incorrect magic number")

        self.offset = stream.u32()
        section_count = stream.u32()
        stream.pad(4)

        self.sections = []
        ranges: list[tuple[int, int]] = []
        total_count = 0
        for i in range(section_count):
            section = RelocationTableSection()
            stream.pad(8)
            section.offset = stream.u32()
            section.size = stream.u32()
            base_index = stream.u32()
            entry_count = stream.u32()
            total_count = max(total_count, base_index + entry_count)
            ranges.append((base_index, entry_count))

        entries: list[RelocationTableEntry] = []
        for i in range(total_count):
            entries.append(stream.extract(RelocationTableEntry))

        for (base, count), section in zip(ranges, self.sections):
            for entry in entries[base : base + count]:
                stride = (entry.relocated_words + entry.skipped_words) * 8
                for repetition in range(entry.repetitions):
                    repetition_base = base + stride * repetition
                    for i in range(entry.relocated_words):
                        section.add(repetition_base + i * 8)

    def encode(self, stream: StreamOut) -> None:
        stream.ascii("_RLT")
        stream.u32(self.offset)
        stream.u32(len(self.sections))
        stream.pad(4)

        entries: list[RelocationTableEntry] = []
        for section in self.sections:
            current = section.make_entries()
            stream.pad(8)
            stream.u32(section.offset)
            stream.u32(section.size)
            stream.u32(len(entries))
            stream.u32(len(current))
            entries += current

        for entry in entries:
            stream.add(entry)

    def add_section(self, offset: int, size: int) -> RelocationTableSection:
        section = RelocationTableSection(offset, size)
        self.sections.append(section)
        return section
