
from typing import Any
from jungle.error import ParseError, SaveError
from jungle import streams
import struct


MAGIC_NUMBER = struct.unpack(">I", b"PMAA")[0]


class StreamIn(streams.StreamIn):
	"""Memory stream that detects whether strings contain uninitialized bytes.

	In old games, strings with a fixed size contain uninitialized bytes
	behind the null terminator. This stream class detects whether that
	is the case.
	"""

	def __init__(self, data, endianness):
		super().__init__(data, endianness)
		self.string_padding = None
	
	def fixed_string(self, size):
		data = self.read(size)
		if b"\0" not in data or data[-1] != 0:
			raise ParseError("expected null terminator behind string")
		
		string, padding = data.split(b"\0", 1)

		# Detect whether the memory behind the string
		# contains uninitialized bytes
		if len(padding) > 1:
			if padding[0] != self.string_padding and self.string_padding is not None:
				raise ParseError("string has inconsistent padding")
			self.string_padding = padding[0]
		
		return string.decode()


class StreamOut(streams.StreamOut):
	"""Memory stream that writes additional bytes behind a null terminated string.

	In old games, strings with a fixed size contain uninitialized bytes
	behind the null terminator. This stream class mimics that behavior.
	"""

	def __init__(self, endianness, string_padding):
		super().__init__(endianness)
		self.string_padding = string_padding or 0
	
	def fixed_string(self, value, size):
		data = value.encode() + b"\0"
		data = data.ljust(size - 1, bytes([self.string_padding]))
		data = data.ljust(size, b"\0")
		if len(data) != size:
			raise SaveError("string is too large")
		self.write(data)


class ParameterType:
	BOOL = 0
	F32 = 1
	INT = 2
	VEC2 = 3
	VEC3 = 4
	VEC4 = 5
	COLOR = 6
	STRING32 = 7
	STRING64 = 8
	CURVE1 = 9
	CURVE2 = 10
	CURVE3 = 11
	CURVE4 = 12
	BUFFER_INT = 13
	BUFFER_FLOAT = 14
	STRING256 = 15
	QUAT = 16
	U32 = 17
	BUFFER_U32 = 18
	BUFFER_BINARY = 19
	STRING_REF = 20


class Parameter:
	def __init__(self):
		self.hash = 0
		self.type = ParameterType.INT
		self.value = 0
	
	def parse(self, stream):
		end = stream.tell() + stream.u32()
		self.type = stream.u32()
		self.hash = stream.u32()

		if self.type == ParameterType.BOOL: self.value = stream.bool()
		elif self.type == ParameterType.F32: self.value = stream.float()
		elif self.type == ParameterType.INT: self.value = stream.s32()
		elif self.type == ParameterType.VEC2:
			x = stream.float()
			y = stream.float()
			self.value = x, y
		elif self.type == ParameterType.VEC3:
			x = stream.float()
			y = stream.float()
			z = stream.float()
			self.value = x, y, z
		elif self.type == ParameterType.VEC4:
			x = stream.float()
			y = stream.float()
			z = stream.float()
			w = stream.float()
			self.value = x, y, z, w
		elif self.type == ParameterType.COLOR:
			r = stream.float()
			g = stream.float()
			b = stream.float()
			a = stream.float()
			self.value = r, g, b, a
		elif self.type == ParameterType.STRING32: self.value = stream.fixed_string(32)
		elif self.type == ParameterType.STRING64: self.value = stream.fixed_string(64)
		elif self.type == ParameterType.CURVE1:
			self.value = stream.repeat(stream.float, 32)
		elif self.type == ParameterType.CURVE1:
			self.value = stream.repeat(stream.float, 64)
		elif self.type == ParameterType.CURVE1:
			self.value = stream.repeat(stream.float, 96)
		elif self.type == ParameterType.CURVE4:
			self.value = stream.repeat(stream.float, 128)
		else:
			raise ParseError("unsupported parameter type: %i" %self.type)

		if stream.tell() != end:
			raise ParseError("parameter has invalid size")

	def save(self, stream):
		base = stream.reserve(4)
		stream.u32(self.type)
		stream.u32(self.hash)

		if self.type == ParameterType.BOOL: stream.bool(self.value)
		elif self.type == ParameterType.F32: stream.float(self.value)
		elif self.type == ParameterType.INT: stream.s32(self.value)
		elif self.type == ParameterType.VEC2:
			for i in range(2):
				stream.float(self.value[i])
		elif self.type == ParameterType.VEC3:
			for i in range(3):
				stream.float(self.value[i])
		elif self.type == ParameterType.VEC4:
			for i in range(4):
				stream.float(self.value[i])
		elif self.type == ParameterType.COLOR:
			for i in range(4):
				stream.float(self.value[i])
		elif self.type == ParameterType.STRING32: stream.fixed_string(self.value, 32)
		elif self.type == ParameterType.STRING64: stream.fixed_string(self.value, 64)
		elif self.type == ParameterType.CURVE1: stream.repeat(self.value, stream.float)
		elif self.type == ParameterType.CURVE2: stream.repeat(self.value, stream.float)
		elif self.type == ParameterType.CURVE3: stream.repeat(self.value, stream.float)
		elif self.type == ParameterType.CURVE4: stream.repeat(self.value, stream.float)
		else:
			raise ParseError("unsupported parameter type: %i" %self.type)
		
		stream.u32_at(base, stream.tell() - base)


class ParameterObject:
	def __init__(self):
		self.hash = 0
		self.group_hash = 0
		self.parameters = []
	
	def parse(self, stream):
		stream.skip(4)
		num_parameters = stream.u32()

		self.hash = stream.u32()
		self.group_hash = stream.u32()

		self.parameters = []
		for i in range(num_parameters):
			parameter = Parameter()
			parameter.parse(stream)
			self.parameters.append(parameter)
	
	def save(self, stream):
		base = stream.reserve(4)
		stream.u32(len(self.parameters))
		stream.u32(self.hash)
		stream.u32(self.group_hash)
		for parameter in self.parameters:
			parameter.save(stream)
		stream.u32_at(base, stream.tell() - base)


class ParameterList:
	def __init__(self):
		self.hash = 0
		self.children = []
		self.objects = []
	
	def parse(self, stream):
		stream.skip(4)
		self.hash = stream.u32()

		num_children = stream.u32()
		num_objects = stream.u32()

		self.children = []
		for i in range(num_children):
			child = ParameterList()
			child.parse(stream)
			self.children.append(child)
		
		self.objects = []
		for i in range(num_objects):
			object = ParameterObject()
			object.parse(stream)
			self.objects.append(object)
	
	def save(self, stream):
		base = stream.reserve(4)
		stream.u32(self.hash)
		stream.u32(len(self.children))
		stream.u32(len(self.objects))
		for child in self.children:
			child.save(stream)
		for object in self.objects:
			object.save(stream)
		stream.u32_at(base, stream.tell() - base)


class PMAAFile:
	def __init__(self):
		self.endianness = "<"
		self.version = 1

		self.effect_version = 0
		self.effect_type = "aglenv"

		self.align = True
		self.string_padding = None

		self.root = ParameterList()

	def parse(self, data):
		# Determine endianness
		if len(data) < 12:
			raise ParseError("file is too small")
		
		bom = struct.unpack_from("I", data, 8)[0]
		self.endianness = "<" if bom else ">"

		# Parse file
		stream = StreamIn(data, self.endianness)
		if stream.u32() != MAGIC_NUMBER:
			raise ParseError("magic number is invalid")
		
		self.version = stream.u32()
		if self.version != 1:
			raise ParseError("unsupported version number")
		
		if stream.u32() != 1: raise ParseError("BOM is invalid")
		if stream.u32() != len(data): raise ParseError("file size is invalid")

		self.effect_version = stream.u32()
		self.effect_type = stream.fixed_string(stream.u32())

		self.align = stream.tell() & 7 == 0

		self.root = ParameterList()
		self.root.parse(stream)

		self.string_padding = stream.string_padding
	
	def save(self):
		if self.version != 1:
			raise SaveError("unsupported version number")
		
		stream = StreamOut(self.endianness, self.string_padding)
		stream.u32(MAGIC_NUMBER)
		stream.u32(self.version)
		stream.u32(1 if self.endianness == "<" else 0)
		stream.skip(4)
		stream.u32(self.effect_version)

		type_length = len(self.effect_type) + 1
		if self.align:
			type_length = (type_length + 7) & ~7
		
		stream.u32(type_length)
		stream.fixed_string(self.effect_type, type_length)

		self.root.save(stream)

		stream.seek(12)
		stream.u32(stream.size())
		return stream.get()
