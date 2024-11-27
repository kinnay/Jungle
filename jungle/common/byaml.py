
from jungle.errors import ParseError, SaveError
from jungle import streams


class NodeType:
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
	def __init__(self, type=NodeType.NULL, value=None):
		self.type = type
		self.value = value


class BYAMLParser:
	def __init__(self):
		self.endianness = ">"
		self.version = 1
		self.has_binary_table = False
		self.root = BYAMLNode(NodeType.DICT, {})

		self.dictionary_keys = []
		self.string_table = []
		self.binary_table = []

		self.nodes = {}
	
	def parse(self, data):
		if len(data) < 2:
			raise ParseError("file is too small")
		
		magic = data[:2]
		if magic == b"BY": self.endianness = ">"
		elif magic == b"YB": self.endianness = "<"
		else:
			raise ParseError("magic number is invalid")

		stream = streams.StreamIn(data, self.endianness)
		stream.skip(2)

		self.version = stream.u16()

		if not 1 <= self.version <= 7:
			raise ParseError("unsupported version number")
		
		dictionary_table_offs = stream.u32()
		string_table_offs = stream.u32()

		# The binary table only appears in Mario Kart 8
		binary_table_offs = stream.u32()
		if binary_table_offs == 0 or stream.u8_at(binary_table_offs) == NodeType.BINARY_TABLE:
			self.has_binary_table = True
			root_node_offs = stream.u32()
		else:
			root_node_offs = binary_table_offs
		
		self.dictionary_keys = self.parse_string_table(stream, dictionary_table_offs)
		self.string_table = self.parse_string_table(stream, string_table_offs)
		if self.has_binary_table:
			self.binary_table = self.parse_binary_table(stream, binary_table_offs)

		stream.seek(root_node_offs)
		type = stream.peek(1)[0]
		if type == NodeType.ARRAY: self.root = self.parse_array(stream)
		elif type == NodeType.DICT: self.root = self.parse_dictionary(stream)
		elif type == NodeType.HASHMAP: self.root = self.parse_hashmap(stream)
		else:
			raise ParseError("root node must be an array or dictionary")
	
	def parse_node(self, stream, type):
		if type == NodeType.ARRAY:
			with stream.jump(stream.u32()):
				return self.parse_array(stream)
		elif type == NodeType.DICT:
			with stream.jump(stream.u32()):
				return self.parse_dictionary(stream)
		else:
			value = self.parse_value(stream, type)
			return BYAMLNode(type, value)
	
	def parse_value(self, stream, type):
		if type == NodeType.STRING:
			index = stream.u32()
			if index < len(self.string_table):
				return self.string_table[index]
			raise ParseError("string index out of range")
		elif type == NodeType.BINARY:
			if self.has_binary_table:
				index = stream.u32()
				if index < len(self.binary_table):
					return self.binary_table[index]
				raise ParseError("binary index out of range")
			else:
				with stream.jump(stream.u32()):
					return stream.read(stream.u32())
		
		elif type == NodeType.BOOL: return bool(stream.u32())
		elif type == NodeType.INT: return stream.s32()
		elif type == NodeType.FLOAT: return stream.float()
		elif type == NodeType.UINT: return stream.u32()

		elif type == NodeType.INT64: return stream.s64_at(stream.u32())
		elif type == NodeType.UINT64: return stream.u64_at(stream.u32())
		elif type == NodeType.DOUBLE: return stream.double_at(stream.u32())

		elif type == NodeType.NULL:
			stream.pad(4)
			return None

		raise ParseError("unsupported node type: 0x%X" %type)
	
	def parse_array(self, stream):
		if stream.u8() != NodeType.ARRAY:
			raise ParseError("expected an array node")
		
		pos = stream.tell()
		if pos not in self.nodes:
			array = []
			count = stream.u24()
			types = stream.repeat(stream.u8, count)
			stream.align(4)
			for type in types:
				array.append(self.parse_node(stream, type))
			self.nodes[pos] = BYAMLNode(NodeType.ARRAY, array)
		return self.nodes[pos]
	
	def parse_dictionary(self, stream):
		"""
		Parses a dictionary node. While the keys are always sorted alphabetically,
		the child nodes may be stored in a different order in the file. We take
		special care to preserve this order. We also make sure that we do not enter
		an infinite loop when the file contains a cycle.
		"""

		if stream.u8() != NodeType.DICT:
			raise ParseError("expected a dictionary node")
		
		pos = stream.tell()
		if pos not in self.nodes:
			elements = []
			count = stream.u24()
			for i in range(count):
				key_index = stream.u24()
				if key_index >= len(self.dictionary_keys):
					raise ParseError("dictionary key index out of range")
				key = self.dictionary_keys[key_index]
				type = stream.u8()
				value = stream.peek_u32() # Read offset to preserve order
				elements.append((key, value, self.parse_node(stream, type)))
			dictionary = {key: node for key, _, node in sorted(elements, key=lambda element: element[1])}
			self.nodes[pos] = BYAMLNode(NodeType.DICT, dictionary)
		return self.nodes[pos]

	def parse_hashmap(self, stream):
		if stream.u8() != NodeType.HASHMAP:
			raise ParseError("expected a hashmap node")

		pos = stream.tell()
		if pos not in self.nodes:
			count = stream.u24()
			with stream.jump(stream.tell() + count * 8):
				types = stream.repeat(stream.u8, count)
			map = {}
			for i in range(count):
				hash = stream.u32()
				map[hash] = self.parse_node(stream, types[i])
			self.nodes[pos] = BYAMLNode(NodeType.HASHMAP, map)
			self.nodes[pos].address = pos - 1
		return self.nodes[pos]
	
	def parse_string_table(self, stream, base):
		if not base:
			return []
		
		stream.seek(base)
		if stream.u8() != NodeType.STRING_TABLE:
			raise ParseError("expected a string table")
		
		count = stream.u24()
		offsets = stream.repeat(stream.u32, count + 1)

		strings = []
		for offset in offsets[:-1]:
			stream.seek(base + offset)
			strings.append(stream.string())
		return strings
	
	def parse_binary_table(self, stream, base):
		if not base:
			return []
		
		stream.seek(base)
		if stream.u8() != NodeType.BINARY_TABLE:
			raise ParseError("expected a binary table")
		
		count = stream.u24()
		offsets = stream.repeat(stream.u32, count + 1)

		data = []
		stream.seek(base + offsets[0])
		for i in range(len(offsets) - 1):
			data.append(stream.read(offsets[i + 1] - offsets[i]))
		return data


class BYAMLSaver:
	def __init__(self):
		self.endianness = ">"
		self.version = 1
		self.has_binary_table = False
		self.root = BYAMLNode(NodeType.DICT, {})

		self.visited = set()
		self.dictionary_keys = set()
		self.strings = set()
		self.binaries = set()

		self.dictionary_key_table = {}
		self.string_table = {}
		self.binary_table = {}

		self.data_size = 0
		self.data_offset = 0

		self.nodes = {}
	
	def save(self):
		if not 1 <= self.version <= 7:
			raise SaveError("unsupported version number")
		
		self.preprocess(self.root)

		self.dictionary_key_table = {v: i for i, v in enumerate(sorted(self.dictionary_keys))}
		self.string_table = {v: i for i, v in enumerate(sorted(self.strings))}
		self.binary_table = {v: i for i, v in enumerate(sorted(self.binaries))}

		stream = streams.StreamOut(self.endianness)
		if self.endianness == ">":
			stream.ascii("BY")
		else:
			stream.ascii("YB")
		stream.u16(self.version)
		if self.has_binary_table:
			stream.u32(0x14 if self.dictionary_key_table else 0)
			stream.skip(12)
		else:
			stream.u32(0x10 if self.dictionary_key_table else 0)
			stream.skip(8)

		if self.dictionary_key_table:
			self.save_string_table(stream, self.dictionary_key_table)
			stream.align(4)
		
		stream.u32_at(8, stream.tell() if self.string_table else 0)
		
		if self.string_table:
			self.save_string_table(stream, self.string_table)
			stream.align(4)
		
		if self.has_binary_table:
			stream.u32_at(12, stream.tell() if self.binary_table else 0)
			if self.binary_table:
				self.save_binary_table(stream, self.binary_table)
				stream.align(4)

		self.data_offset = stream.tell()
		stream.skip(self.data_size)

		if self.has_binary_table:
			stream.u32_at(16, stream.tell())
		else:
			stream.u32_at(12, stream.tell())

		if self.root.type == NodeType.ARRAY: self.save_array(stream, self.root)
		elif self.root.type == NodeType.DICT: self.save_dictionary(stream, self.root)
		elif self.root.type == NodeType.HASHMAP: self.save_hashmap(stream, self.root)
		else:
			raise SaveError("root node must be an array or dictionary")

		return stream.get()
	
	def save_array(self, stream, node):
		self.nodes[node] = stream.tell()

		stream.u8(NodeType.ARRAY)
		stream.u24(len(node.value))
		for child in node.value:
			stream.u8(child.type)
		stream.align(4)
		
		stream.push()
		stream.skip(len(node.value) * 4)
		stream.pop()
		
		for child in node.value:
			self.save_node(stream, child)
	
	def save_dictionary(self, stream, node):
		self.nodes[node] = stream.tell()

		stream.u8(NodeType.DICT)
		stream.u24(len(node.value))

		base = stream.tell()
		stream.skip(len(node.value) * 8)

		keys = sorted(node.value)
		for key, child in node.value.items():
			stream.seek(base + keys.index(key) * 8)
			stream.u24(self.dictionary_key_table[key])
			stream.u8(child.type)
			self.save_node(stream, child)
	
	def save_hashmap(self, stream, node):
		self.nodes[node] = stream.tell()

		stream.u8(NodeType.HASHMAP)
		stream.u24(len(node.value))

		stream.push()
		stream.skip(len(node.value) * 8)
		for child in node.value.values():
			stream.u8(child.type)
		stream.align(4)
		stream.pop()

		for key, child in node.value.items():
			stream.u32(key)
			self.save_node(stream, child)
	
	def save_string_table(self, stream, table):
		offset = 8 + 4 * len(table)

		addresses = [offset]
		strings = b""
		for string in table.keys():
			strings += string.encode() + b"\0"
			addresses.append(offset + len(strings))

		stream.u8(NodeType.STRING_TABLE)
		stream.u24(len(table))
		stream.repeat(addresses, stream.u32)
		stream.write(strings)

	def save_binary_table(self, stream, table):
		offset = 8 + 4 * len(table)

		addresses = [offset]
		binaries = b""
		for binary in table.keys():
			binaries += binary
			addresses.append(offset + len(binaries))
		
		stream.u8(NodeType.BINARY_TABLE)
		stream.u24(len(table))
		stream.repeat(addresses, stream.u32)
		stream.write(binaries)

	def save_node(self, stream, node):
		if node.type == NodeType.STRING:
			stream.u32(self.string_table[node.value])
		elif node.type == NodeType.BINARY:
			stream.u32(self.data_offset)
			with stream.jump(self.data_offset):
				stream.u32(len(node.value))
				stream.write(node.value)
			self.data_offset += 4 + len(node.value)
		
		elif node.type == NodeType.ARRAY:
			if node in self.nodes:
				stream.u32(self.nodes[node])
			else:
				stream.u32(stream.size())
				with stream.jump(stream.size()):
					self.save_array(stream, node)
		elif node.type == NodeType.DICT:
			if node in self.nodes:
				stream.u32(self.nodes[node])
			else:
				stream.u32(stream.size())
				with stream.jump(stream.size()):
					self.save_dictionary(stream, node)
		
		elif node.type == NodeType.BOOL: stream.u32(1 if node.value else 0)
		elif node.type == NodeType.INT: stream.s32(node.value)
		elif node.type == NodeType.FLOAT: stream.float(node.value)
		elif node.type == NodeType.UINT: stream.u32(node.value)

		elif node.type == NodeType.INT64:
			stream.u32(self.data_offset)
			stream.s64_at(self.data_offset, node.value)
			self.data_offset += 8
		elif node.type == NodeType.UINT64:
			stream.u32(self.data_offset)
			stream.u64_at(self.data_offset, node.value)
			self.data_offset += 8
		elif node.type == NodeType.DOUBLE:
			stream.u32(self.data_offset)
			stream.double_at(self.data_offset, node.value)
			self.data_offset += 8
		
		elif node.type == NodeType.NULL:
			stream.u32(0)
		
		else:
			raise SaveError("unsupported node type: 0x%X" %node.type)

	def preprocess(self, node):
		"""
		Walks through all nodes to generate the string and dictionary key tables,
		and calculate the size of the additional binary data.
		"""

		if node.type == NodeType.ARRAY and node not in self.visited:
			self.visited.add(node)
			for element in node.value:
				self.preprocess(element)
		elif node.type == NodeType.DICT and node not in self.visited:
			self.visited.add(node)
			for key, value in node.value.items():
				self.dictionary_keys.add(key)
				self.preprocess(value)
		elif node.type == NodeType.HASHMAP and node not in self.visited:
			self.visited.add(node)
			for element in node.value.values():
				self.preprocess(element)
		elif node.type == NodeType.STRING:
			self.strings.add(node.value)
		elif node.type == NodeType.BINARY:
			if self.has_binary_table:
				self.binaries.add(node.value)
			else:
				self.data_size += 4 + len(node.value)
		elif node.type in [NodeType.INT64, NodeType.UINT64, NodeType.DOUBLE]:
			self.data_size += 8


class BYAMLFile:
	def __init__(self):
		self.endianness = ">"
		self.version = 1
		self.has_binary_table = False
		self.root = BYAMLNode(NodeType.DICT, {})
	
	def parse(self, data):
		parser = BYAMLParser()
		parser.parse(data)

		self.endianness = parser.endianness
		self.version = parser.version
		self.has_binary_table = parser.has_binary_table
		self.root = parser.root
	
	def save(self):
		saver = BYAMLSaver()
		saver.endianness = self.endianness
		saver.version = self.version
		saver.has_binary_table = self.has_binary_table
		saver.root = self.root
		return saver.save()
