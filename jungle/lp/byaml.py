
from jungle.errors import ParseError, SaveError
from jungle import streams


class NodeType:
	STRING = 0xA0
	BINARY = 0xA1

	ARRAY = 0xC0
	DICT = 0xC1
	STRING_TABLE = 0xC2

	BOOL = 0xD0
	S32 = 0xD1
	FLOAT = 0xD2
	U32 = 0xD3
	S64 = 0xD4
	U64 = 0xD5
	DOUBLE = 0xD6

	NULL = 0xFF


class BYAMLNode:
	def __init__(self, type=NodeType.NULL, value=None):
		self.type = type
		self.value = value


class BYAMLParser:
	def __init__(self):
		self.endianness = "<"
		self.version = 5
		self.root = BYAMLNode(NodeType.DICT, {})

		self.dictionary_keys = []
		self.string_table = []

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
		
		dictionary_table_offs = stream.u32()
		string_table_offs = stream.u32()
		root_node_offs = stream.u32()

		if not 2 <= self.version <= 7:
			raise ParseError("unsupported version number")
		
		self.dictionary_keys = self.parse_string_table(stream, dictionary_table_offs)
		self.string_table = self.parse_string_table(stream, string_table_offs)

		stream.seek(root_node_offs)
		type = stream.peek(1)[0]
		if type == NodeType.ARRAY: self.root = self.parse_array(stream)
		elif type == NodeType.DICT: self.root = self.parse_dictionary(stream)
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
			with stream.jump(stream.u32()):
				return stream.read(stream.u32())
		
		elif type == NodeType.BOOL: return bool(stream.u32())
		elif type == NodeType.S32: return stream.s32()
		elif type == NodeType.FLOAT: return stream.float()
		elif type == NodeType.U32: return stream.u32()

		elif type == NodeType.S64: return stream.s64_at(stream.u32())
		elif type == NodeType.U64: return stream.u64_at(stream.u32())
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
		if stream.u8() != NodeType.DICT:
			raise ParseError("expected a dictionary node")
		
		pos = stream.tell()
		if pos not in self.nodes:
			dictionary = {}
			count = stream.u24()
			for i in range(count):
				key_index = stream.u24()
				if key_index >= len(self.dictionary_keys):
					raise ParseError("dictionary key index out of range")
				key = self.dictionary_keys[key_index]
				dictionary[key] = self.parse_node(stream, stream.u8())
			self.nodes[pos] = BYAMLNode(NodeType.DICT, dictionary)
		return self.nodes[pos]
	
	def parse_string_table(self, stream, base):
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
		

class BYAMLSaver:
	def __init__(self):
		self.endianness = "<"
		self.version = 5
		self.root = BYAMLNode(NodeType.DICT, {})

		self.dictionary_key_table = []
		self.string_table = []

		self.nodes = {}
	
	def save(self):
		if not 2 <= self.version <= 7:
			raise SaveError("unsupported version number")
		
		self.generate_tables()

		stream = streams.StreamOut(self.endianness)
		if self.endianness == ">":
			stream.ascii("BY")
		else:
			stream.ascii("YB")
		stream.u16(self.version)
		stream.u32(0x10)
		stream.skip(8)

		self.save_string_table(stream, self.dictionary_key_table)
		stream.align(4)
		stream.u32_at(8, stream.tell())

		self.save_string_table(stream, self.string_table)
		stream.align(4)
		stream.u32_at(12, stream.tell())

		if self.root.type == NodeType.ARRAY:
			self.save_array(stream, self.root)
		elif self.root.type == NodeType.DICT:
			self.save_dictionary(stream, self.root)
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

		stream.push()
		stream.skip(len(node.value) * 8)
		stream.pop()

		for key, child in node.value.items():
			stream.u24(self.dictionary_key_table.index(key))
			stream.u8(child.type)
			self.save_node(stream, child)
	
	def save_string_table(self, stream, table):
		offset = 8 + 4 * len(table)

		addresses = [offset]
		strings = b""
		for string in table:
			strings += string.encode() + b"\0"
			addresses.append(offset + len(strings))

		stream.u8(NodeType.STRING_TABLE)
		stream.u24(len(table))
		stream.repeat(addresses, stream.u32)
		stream.write(strings)
	
	def save_node(self, stream, node):
		if node.type == NodeType.STRING:
			stream.u32(self.string_table.index(node.value))
		elif node.type == NodeType.BINARY:
			stream.u32(stream.size())
			with stream.jump(stream.size()):
				stream.u32(len(node.value))
				stream.write(node.value)
				stream.align(4)
		
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
		elif node.type == NodeType.S32: stream.s32(node.value)
		elif node.type == NodeType.FLOAT: stream.float(node.value)
		elif node.type == NodeType.U32: stream.u32(node.value)

		elif node.type == NodeType.S64:
			stream.u32(stream.size())
			stream.s64_at(stream.size(), node.value)
		elif node.type == NodeType.U64:
			stream.u32(stream.size())
			stream.u64_at(stream.size(), node.value)
		elif node.type == NodeType.DOUBLE:
			stream.u32(stream.size())
			stream.double_at(stream.size(), node.value)
		
		elif node.type == NodeType.NULL:
			stream.u32(0)
		
		else:
			raise SaveError("unsupported node type: 0x%X" %node.type)

	def generate_tables(self):
		"""Walks through all nodes to generate the string and dictionary key tables"""

		visited = []
		todo = [self.root]
		while todo:
			node = todo.pop()
			if node in visited:
				continue
			visited.append(node)

			if node.type == NodeType.ARRAY:
				for element in node.value:
					todo.append(element)
			elif node.type == NodeType.DICT:
				for key, value in node.value.items():
					if key not in self.dictionary_key_table:
						self.dictionary_key_table.append(key)
					todo.append(value)
			elif node.type == NodeType.STRING:
				if node.type not in self.string_table:
					self.string_table.append(node.value)
		
		self.dictionary_key_table.sort()
		self.string_table.sort()


class BYAMLFile:
	def __init__(self):
		self.endianness = "<"
		self.version = 5
		self.root = BYAMLNode(NodeType.DICT, {})
	
	def parse(self, data):
		parser = BYAMLParser()
		parser.parse(data)

		self.endianness = parser.endianness
		self.version = parser.version
		self.root = parser.root
	
	def save(self):
		saver = BYAMLSaver()
		saver.endianness = self.endianness
		saver.version = self.version
		saver.root = self.root
		return saver.save()
