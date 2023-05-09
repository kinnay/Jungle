
from typing import Any
from jungle.error import ParseError, SaveError
from jungle import streams
import struct


MAGIC_NUMBER = struct.unpack(">I", b"PMAA")[0]


class StreamIn(streams.StreamIn):
	"""Memory stream that detects quirks of Nintendo's tooling.

	In some games, strings with a fixed size contain uninitialized bytes
	behind the null terminator. This stream class detects whether that
	is the case.

	In some games, strings with a fixed size always use the maximum
	number of bytes. In other games, they only use the necessary
	number of bytes. This class detects that.
	"""

	def __init__(self, data, endianness):
		super().__init__(data, endianness)
		self.minimize_strings = None
		self.string_padding = None
	
	def fixed_string(self, size, max_size=None):
		data = self.read(size)
		if b"\0" not in data:
			raise ParseError("expected null terminator behind string")
		
		string, padding = data.split(b"\0", 1)

		# Detect whether the memory behind the string
		# contains uninitialized bytes
		if len(padding) > 1:
			self.string_padding = padding[0]
		
		# Detect whether the string uses the necessary or the
		# maximum number of bytes.
		if self.minimize_strings is None and max_size is not None:
			if size != max_size:
				self.minimize_strings = True
			elif padding:
				self.minimize_strings = False

		return string.decode()


class StreamOut(streams.StreamOut):
	"""Memory stream that reproduces quirks of Nintendo's tooling.

	In some games, strings with a fixed size contain uninitialized bytes
	behind the null terminator. This stream class mimics that behavior.

	In some games, strings with a fixed size always use the maximum
	number of bytes. In other games, they only use the necessary
	number of bytes. This class mimics the desired behavior.
	"""

	def __init__(self, endianness, minimize_strings, string_padding):
		super().__init__(endianness)
		self.minimize_strings = minimize_strings or False
		self.string_padding = string_padding or 0
	
	def fixed_string(self, value, size, allow_minize=True):
		data = value.encode() + b"\0"
		if not allow_minize or not self.minimize_strings:
			data = data.ljust(size - 1, bytes([self.string_padding]))
			data = data.ljust(size, b"\0")
		if len(data) > size:
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


class CurveType:
	LINEAR = 0
	HERMIT = 1
	STEP = 2
	SIN = 3
	COS = 4
	SIN_POW2 = 5
	LINEAR_2D = 6
	HERMIT_2D = 7
	STEP_2D = 8
	NONUNIFORM_SPLINE = 9
	HERMIT_2D_SMOOTH = 10


class Curve:
	def __init__(self):
		self.type = CurveType.HERMIT_2D
		self.values = [.0, .0, .5, .5, .5, .5, 1., 1., .5]
	
	def parse(self, stream):
		num_values = stream.u32()
		if num_values > 30:
			raise ParseError("curve has too many points")

		self.type = stream.u32()
		self.values = stream.repeat(stream.float, num_values)
		stream.skip(4 * (30 - num_values))
	
	def save(self, stream):
		stream.u32(len(self.values))
		stream.u32(self.type)
		stream.repeat(self.values, stream.float)
		for i in range(30 - len(self.values)):
			stream.float(1.)


class Parameter:
	def __init__(self):
		self.hash = 0
		self.type = ParameterType.INT
		self.value = 0
	
	def parse(self, stream):
		base = stream.tell()
		size = stream.u32()
		self.type = stream.u32()
		self.hash = stream.u32()

		data_size = size - 12

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
		elif self.type == ParameterType.STRING32: self.value = stream.fixed_string(data_size, 32)
		elif self.type == ParameterType.STRING64: self.value = stream.fixed_string(data_size, 64)
		elif self.type == ParameterType.CURVE1:
			self.value = Curve()
			self.value.parse(stream)
		elif self.type == ParameterType.CURVE1:
			self.value = []
			for i in range(2):
				curve = Curve()
				curve.parse(stream)
				self.value.append(curve)
		elif self.type == ParameterType.CURVE1:
			self.value = []
			for i in range(3):
				curve = Curve()
				curve.parse(stream)
				self.value.append(curve)
		elif self.type == ParameterType.CURVE4:
			self.value = []
			for i in range(4):
				curve = Curve()
				curve.parse(stream)
				self.value.append(curve)
		else:
			raise ParseError("unsupported parameter type: %i" %self.type)

		if stream.tell() != base + size:
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
		elif self.type == ParameterType.CURVE1: self.value.save(stream)
		elif self.type == ParameterType.CURVE2:
			for curve in self.value:
				curve.save(stream)
		elif self.type == ParameterType.CURVE3:
			for curve in self.value:
				curve.save(stream)
		elif self.type == ParameterType.CURVE4:
			for curve in self.value:
				curve.save(stream)
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

		# These are inconsistent quirks of
		# Nintendo's tooling
		self.align = True
		self.minimize_strings = False
		self.string_padding = 0

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

		self.align = stream.tell() & 3 == 0

		self.root = ParameterList()
		self.root.parse(stream)

		self.minimize_strings = stream.minimize_strings
		self.string_padding = stream.string_padding
	
	def save(self):
		if self.version != 1:
			raise SaveError("unsupported version number")
		
		stream = StreamOut(self.endianness, self.minimize_strings, self.string_padding)
		stream.u32(MAGIC_NUMBER)
		stream.u32(self.version)
		stream.u32(1 if self.endianness == "<" else 0)
		stream.skip(4)
		stream.u32(self.effect_version)

		type_length = len(self.effect_type) + 1
		if self.align:
			type_length = (type_length + 3) & ~3
		
		stream.u32(type_length)
		stream.fixed_string(self.effect_type, type_length, False)

		self.root.save(stream)

		stream.seek(12)
		stream.u32(stream.size())
		return stream.get()
