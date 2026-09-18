
from dataclasses import dataclass, field

from jungle.errors import ParseError, SaveError
from jungle.streams import StreamIn, StreamOut

import enum


class BYAMLNodeType(enum.IntEnum):
    HASHMAP = 0x20

    STRING = 0xA0
    BINARY = 0xA1

    ARRAY = 0xC0
    DICT = 0xC1

    STRING_TABLE = 0xC2
    BINARY_TABLE = 0xC3

    BOOL = 0xD0
    INT = 0xD1
    FLOAT = 0xD2
    UINT = 0xD3
    INT64 = 0xD4
    UINT64 = 0xD5
    DOUBLE = 0xD6

    NULL = 0xFF


class BYAMLNode:
    """Base class for BYAML nodes. Should not be instantiated directly."""

    def type(self) -> BYAMLNodeType:
        raise NotImplementedError(f"{self.__class__.__name__}.type()")


@dataclass(eq=False)
class BYAMLHashmap(BYAMLNode):
    value: dict[int, BYAMLNode] = field(default_factory=dict)

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.HASHMAP


@dataclass
class BYAMLString(BYAMLNode):
    value: str = ""

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.STRING


@dataclass
class BYAMLBinary(BYAMLNode):
    value: bytes = b""

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.BINARY


@dataclass(eq=False)
class BYAMLArray(BYAMLNode):
    value: list[BYAMLNode] = field(default_factory=list)

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.ARRAY


@dataclass(eq=False)
class BYAMLDict(BYAMLNode):
    value: dict[str, BYAMLNode] = field(default_factory=dict)

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.DICT


@dataclass
class BYAMLBool(BYAMLNode):
    value: bool = False

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.BOOL


@dataclass
class BYAMLInt(BYAMLNode):
    value: int = 0

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.INT


@dataclass
class BYAMLFloat(BYAMLNode):
    value: float = .0

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.FLOAT


@dataclass
class BYAMLUint(BYAMLNode):
    value: int = 0

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.UINT


@dataclass
class BYAMLInt64(BYAMLNode):
    value: int = 0

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.INT64


@dataclass
class BYAMLUint64(BYAMLNode):
    value: int = 0

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.UINT64


@dataclass
class BYAMLDouble(BYAMLNode):
    value: float = .0

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.DOUBLE


@dataclass
class BYAMLNone(BYAMLNode):
    value: None = None

    def type(self) -> BYAMLNodeType:
        return BYAMLNodeType.NULL


type BYAMLRoot = BYAMLArray | BYAMLDict | BYAMLHashmap


class BYAMLParser:
    """Implements a parser for the BYAML file format."""

    _file: BYAMLFile

    _dictionary_keys: list[str]
    _string_table: list[str]
    _binary_table: list[bytes]

    _array_nodes: dict[int, BYAMLArray]
    _dict_nodes: dict[int, BYAMLDict]
    _hashmap_nodes: dict[int, BYAMLHashmap]

    def __init__(self, file: BYAMLFile):
        self._file = file

        self._dictionary_keys = []
        self._string_table = []
        self._binary_table = []

        self._array_nodes = {}
        self._dict_nodes = {}
        self._hashmap_nodes = {}
    
    def parse(self, data: bytes) -> None:
        if len(data) < 2:
            raise ParseError("file is too small")
        
        magic = data[:2]
        if magic == b"BY": self._file.endianness = ">"
        elif magic == b"YB": self._file.endianness = "<"
        else:
            raise ParseError("magic number is invalid")

        stream = StreamIn(data, self._file.endianness)
        stream.skip(2)

        self._file.version = stream.u16()

        if not 1 <= self._file.version <= 7:
            raise ParseError("unsupported version number")
        
        dictionary_table_offs = stream.u32()
        string_table_offs = stream.u32()

        # The binary table only appears in Mario Kart 8
        binary_table_offs = stream.u32()
        if binary_table_offs == 0 or \
           stream.u8_at(binary_table_offs) == BYAMLNodeType.BINARY_TABLE:
            self._file.has_binary_table = True
            root_node_offs = stream.u32()
        else:
            root_node_offs = binary_table_offs
        
        self._dictionary_keys = \
            self._parse_string_table(stream, dictionary_table_offs)
        self._string_table = \
            self._parse_string_table(stream, string_table_offs)
        
        if self._file.has_binary_table:
            self._binary_table = \
                self._parse_binary_table(stream, binary_table_offs)

        stream.seek(root_node_offs)
        self._file.root = self._parse_root_node(stream)

    def _parse_root_node(self, stream: StreamIn) -> BYAMLRoot:
        type = stream.peek(1)[0]
        if type == BYAMLNodeType.ARRAY: return self._parse_array(stream)
        elif type == BYAMLNodeType.DICT: return self._parse_dictionary(stream)
        elif type == BYAMLNodeType.HASHMAP: return self._parse_hashmap(stream)
        else:
            raise ParseError("root node must be an array or dictionary")
    
    def _parse_node(self, stream: StreamIn, type: int) -> BYAMLNode:
        if type == BYAMLNodeType.ARRAY:
            with stream.jump(stream.u32()):
                return self._parse_array(stream)
        elif type == BYAMLNodeType.DICT:
            with stream.jump(stream.u32()):
                return self._parse_dictionary(stream)
        else:
            return self._parse_scalar(stream, type)
    
    def _parse_scalar(self, stream: StreamIn, type: int) -> BYAMLNode:
        if type == BYAMLNodeType.STRING:
            index = stream.u32()
            if index < len(self._string_table):
                return BYAMLString(self._string_table[index])
            raise ParseError("string index out of range")
        elif type == BYAMLNodeType.BINARY:
            if self._file.has_binary_table:
                index = stream.u32()
                if index < len(self._binary_table):
                    return BYAMLBinary(self._binary_table[index])
                raise ParseError("binary index out of range")
            else:
                with stream.jump(stream.u32()):
                    return BYAMLBinary(stream.read(stream.u32()))
        
        elif type == BYAMLNodeType.BOOL: return BYAMLBool(bool(stream.u32()))
        elif type == BYAMLNodeType.INT: return BYAMLInt(stream.s32())
        elif type == BYAMLNodeType.FLOAT: return BYAMLFloat(stream.float())
        elif type == BYAMLNodeType.UINT: return BYAMLUint(stream.u32())

        elif type == BYAMLNodeType.INT64:
            return BYAMLInt64(stream.s64_at(stream.u32()))
        elif type == BYAMLNodeType.UINT64:
            return BYAMLUint64(stream.u64_at(stream.u32()))
        elif type == BYAMLNodeType.DOUBLE:
            return BYAMLDouble(stream.double_at(stream.u32()))

        elif type == BYAMLNodeType.NULL:
            stream.pad(4)
            return BYAMLNone()

        raise ParseError(f"unsupported node type: 0x{type:X}")
    
    def _parse_array(self, stream: StreamIn) -> BYAMLArray:
        if stream.u8() != BYAMLNodeType.ARRAY:
            raise ParseError("expected an array node")
        
        pos = stream.tell()
        if pos not in self._array_nodes:
            array = []
            count = stream.u24()
            types = stream.repeat(stream.u8, count)
            
            stream.align(4)
            for type in types:
                array.append(self._parse_node(stream, type))
            self._array_nodes[pos] = BYAMLArray(array)
        
        return self._array_nodes[pos]
    
    def _parse_dictionary(self, stream: StreamIn) -> BYAMLDict:
        """
        Parses a dictionary node. While the keys are always sorted
        alphabetically, the child nodes may be stored in a different order in
        the file. We take special care to preserve this order. We also make sure
        that we do not enter an infinite loop when the file contains a cycle.
        """

        if stream.u8() != BYAMLNodeType.DICT:
            raise ParseError("expected a dictionary node")
        
        pos = stream.tell()
        if pos not in self._dict_nodes:
            elements = []
            count = stream.u24()
            for i in range(count):
                key_index = stream.u24()
                if key_index >= len(self._dictionary_keys):
                    raise ParseError("dictionary key index out of range")
                key = self._dictionary_keys[key_index]
                type = stream.u8()
                value = stream.peek_u32() # Read offset to preserve order
                elements.append((key, value, self._parse_node(stream, type)))

            elements.sort(key = lambda element: element[1])

            dictionary = {key: node for key, _, node in elements}
            self._dict_nodes[pos] = BYAMLDict(dictionary)
        
        return self._dict_nodes[pos]

    def _parse_hashmap(self, stream: StreamIn) -> BYAMLHashmap:
        if stream.u8() != BYAMLNodeType.HASHMAP:
            raise ParseError("expected a hashmap node")

        pos = stream.tell()
        if pos not in self._hashmap_nodes:
            count = stream.u24()
            with stream.jump(stream.tell() + count * 8):
                types = stream.repeat(stream.u8, count)
            map = {}
            for i in range(count):
                hash = stream.u32()
                map[hash] = self._parse_node(stream, types[i])
            self._hashmap_nodes[pos] = BYAMLHashmap(map)
        
        return self._hashmap_nodes[pos]
    
    def _parse_string_table(self, stream: StreamIn, base: int) -> list[str]:
        if not base:
            return []
        
        stream.seek(base)
        if stream.u8() != BYAMLNodeType.STRING_TABLE:
            raise ParseError("expected a string table")
        
        count = stream.u24()
        offsets = stream.repeat(stream.u32, count + 1)

        strings = []
        for offset in offsets[:-1]:
            stream.seek(base + offset)
            strings.append(stream.string())
        return strings
    
    def _parse_binary_table(self, stream: StreamIn, base: int) -> list[bytes]:
        if not base:
            return []
        
        stream.seek(base)
        if stream.u8() != BYAMLNodeType.BINARY_TABLE:
            raise ParseError("expected a binary table")
        
        count = stream.u24()
        offsets = stream.repeat(stream.u32, count + 1)

        data = []
        stream.seek(base + offsets[0])
        for i in range(len(offsets) - 1):
            data.append(stream.read(offsets[i + 1] - offsets[i]))
        return data


class BYAMLSaver:
    """Implements a serializer for the BYAML file format."""

    _file: BYAMLFile

    _visited: set[BYAMLNode]
    _dictionary_keys: set[str]
    _strings: set[str]
    _binaries: set[bytes]

    _dictionary_key_table: dict[str, int]
    _string_table: dict[str, int]
    _binary_table: dict[bytes, int]

    _data_size: int
    _data_offset: int

    _nodes: dict[BYAMLNode, int]

    def __init__(self, file: BYAMLFile):
        self._file = file

        self._visited = set()
        self._dictionary_keys = set()
        self._strings = set()
        self._binaries = set()

        self._dictionary_key_table = {}
        self._string_table = {}
        self._binary_table = {}

        self._data_size = 0
        self._data_offset = 0

        self._nodes = {}
    
    def save(self) -> bytes:
        if not 1 <= self._file.version <= 7:
            raise SaveError("unsupported version number")
        
        self._preprocess(self._file.root)

        self._dictionary_key_table = {
            v: i for i, v in enumerate(sorted(self._dictionary_keys))
        }
        self._string_table = {
            v: i for i, v in enumerate(sorted(self._strings))
        }
        self._binary_table = {
            v: i for i, v in enumerate(sorted(self._binaries))
        }

        stream = StreamOut(self._file.endianness)
        if self._file.endianness == ">":
            stream.ascii("BY")
        else:
            stream.ascii("YB")
        stream.u16(self._file.version)
        if self._file.has_binary_table:
            stream.u32(0x14 if self._dictionary_key_table else 0)
            stream.skip(12)
        else:
            stream.u32(0x10 if self._dictionary_key_table else 0)
            stream.skip(8)

        if self._dictionary_key_table:
            self._save_string_table(stream, self._dictionary_key_table)
            stream.align(4)
        
        stream.u32_at(8, stream.tell() if self._string_table else 0)
        
        if self._string_table:
            self._save_string_table(stream, self._string_table)
            stream.align(4)
        
        if self._file.has_binary_table:
            stream.u32_at(12, stream.tell() if self._binary_table else 0)
            if self._binary_table:
                self._save_binary_table(stream, self._binary_table)
                stream.align(4)

        self._data_offset = stream.tell()
        stream.skip(self._data_size)

        if self._file.has_binary_table:
            stream.u32_at(16, stream.tell())
        else:
            stream.u32_at(12, stream.tell())

        self._save_root_node(stream, self._file.root)
        return stream.get()

    def _save_root_node(self, stream: StreamOut, node: BYAMLRoot) -> None:
        if isinstance(node, BYAMLArray): self._save_array(stream, node)        
        elif isinstance(node, BYAMLDict): self._save_dictionary(stream, node)
        elif isinstance(node, BYAMLHashmap): self._save_hashmap(stream, node)
        else:
            raise SaveError("root node must be an array, dictionary or hashmap")
    
    def _save_array(self, stream: StreamOut, node: BYAMLArray) -> None:
        self._nodes[node] = stream.tell()

        stream.u8(node.type())
        stream.u24(len(node.value))
        for child in node.value:
            stream.u8(child.type())
        stream.align(4)
        
        stream.push()
        stream.skip(len(node.value) * 4)
        stream.pop()
        
        for child in node.value:
            self._save_node(stream, child)
    
    def _save_dictionary(self, stream: StreamOut, node: BYAMLDict) -> None:
        self._nodes[node] = stream.tell()

        stream.u8(node.type())
        stream.u24(len(node.value))

        base = stream.tell()
        stream.skip(len(node.value) * 8)

        keys = sorted(node.value)
        for key, child in node.value.items():
            stream.seek(base + keys.index(key) * 8)
            stream.u24(self._dictionary_key_table[key])
            stream.u8(child.type())
            self._save_node(stream, child)
    
    def _save_hashmap(self, stream: StreamOut, node: BYAMLHashmap) -> None:
        self._nodes[node] = stream.tell()

        stream.u8(node.type())
        stream.u24(len(node.value))

        stream.push()
        stream.skip(len(node.value) * 8)
        for child in node.value.values():
            stream.u8(child.type())
        stream.align(4)
        stream.pop()

        for key, child in node.value.items():
            stream.u32(key)
            self._save_node(stream, child)
    
    def _save_string_table(
        self, stream: StreamOut, table: dict[str, int]
    ) -> None:
        offset = 8 + 4 * len(table)

        addresses = [offset]
        strings = b""
        for string in table.keys():
            strings += string.encode() + b"\0"
            addresses.append(offset + len(strings))

        stream.u8(BYAMLNodeType.STRING_TABLE)
        stream.u24(len(table))
        stream.repeat(addresses, stream.u32)
        stream.write(strings)

    def _save_binary_table(
        self, stream: StreamOut, table: dict[bytes, int]
    ) -> None:
        offset = 8 + 4 * len(table)

        addresses = [offset]
        binaries = b""
        for binary in table.keys():
            binaries += binary
            addresses.append(offset + len(binaries))
        
        stream.u8(BYAMLNodeType.BINARY_TABLE)
        stream.u24(len(table))
        stream.repeat(addresses, stream.u32)
        stream.write(binaries)

    def _save_node(self, stream: StreamOut, node: BYAMLNode) -> None:
        if isinstance(node, BYAMLString):
            stream.u32(self._string_table[node.value])
        elif isinstance(node, BYAMLBinary):
            stream.u32(self._data_offset)
            with stream.jump(self._data_offset):
                stream.u32(len(node.value))
                stream.write(node.value)
            self._data_offset += 4 + len(node.value)
        
        elif isinstance(node, BYAMLArray):
            if node in self._nodes:
                stream.u32(self._nodes[node])
            else:
                stream.u32(stream.size())
                with stream.jump(stream.size()):
                    self._save_array(stream, node)
        
        elif isinstance(node, BYAMLDict):
            if node in self._nodes:
                stream.u32(self._nodes[node])
            else:
                stream.u32(stream.size())
                with stream.jump(stream.size()):
                    self._save_dictionary(stream, node)
        
        elif isinstance(node, BYAMLBool): stream.u32(node.value)
        elif isinstance(node, BYAMLInt): stream.s32(node.value)
        elif isinstance(node, BYAMLFloat): stream.float(node.value)
        elif isinstance(node, BYAMLUint): stream.u32(node.value)

        elif isinstance(node, BYAMLInt64):
            stream.u32(self._data_offset)
            stream.s64_at(self._data_offset, node.value)
            self._data_offset += 8
        elif isinstance(node, BYAMLUint64):
            stream.u32(self._data_offset)
            stream.u64_at(self._data_offset, node.value)
            self._data_offset += 8
        elif isinstance(node, BYAMLDouble):
            stream.u32(self._data_offset)
            stream.double_at(self._data_offset, node.value)
            self._data_offset += 8
        
        elif isinstance(node, BYAMLNone):
            stream.u32(0)
        
        else:
            raise SaveError(f"unsupported node type: 0x{node.type():X}")

    def _preprocess(self, node: BYAMLNode) -> None:
        """
        Walks through all nodes to generate the string and dictionary key
        tables, and calculate the size of the additional binary data.
        """

        if isinstance(node, BYAMLArray) and node not in self._visited:
            self._visited.add(node)
            for element in node.value:
                self._preprocess(element)
        elif isinstance(node, BYAMLDict) and node not in self._visited:
            self._visited.add(node)
            for key, value in node.value.items():
                self._dictionary_keys.add(key)
                self._preprocess(value)
        elif isinstance(node, BYAMLHashmap) and node not in self._visited:
            self._visited.add(node)
            for element in node.value.values():
                self._preprocess(element)
        elif isinstance(node, BYAMLString):
            self._strings.add(node.value)
        elif isinstance(node, BYAMLBinary):
            if self._file.has_binary_table:
                self._binaries.add(node.value)
            else:
                self._data_size += 4 + len(node.value)
        elif isinstance(node, (BYAMLInt64, BYAMLUint64, BYAMLDouble)):
            self._data_size += 8


class BYAMLFile:
    endianness: str
    version: int
    has_binary_table: bool
    root: BYAMLRoot

    def __init__(self):
        self.endianness = ">"
        self.version = 1
        self.has_binary_table = False
        self.root = BYAMLDict()
    
    def parse(self, data: bytes) -> None:
        parser = BYAMLParser(self)
        parser.parse(data)
    
    def save(self) -> bytes:
        saver = BYAMLSaver(self)
        return saver.save()
