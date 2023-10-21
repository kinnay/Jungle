
from jungle.errors import ParseError, SaveError
from jungle import streams

import struct


class CurveType:
	ROLL_OFF = 0
	CUSTOM = 1
	UNIT_DISTANCE = 2


class CurveDescription:
	def __init__(self):
		self.name = ""
		self.type = CurveType.ROLL_OFF


class StringTable:
	def __init__(self):
		self.strings = {}
		self.data = b""
	
	def add(self, string):
		if string not in self.strings:
			self.strings[string] = len(self.data)
			self.data += string.encode() + b"\0"
		return self.strings[string]
	
	def get(self):
		return self.data


class BAATNFile:
	def __init__(self):
		self.version = 1
		self.endianness = "<"

		self.curves = {i: CurveDescription() for i in range(5)}

		self.directivity = ""
		self.culling = ""

		self.listener_enabled = False
		self.occlusion_enabled = False

	def parse(self, data):
		# Determine endianness
		if len(data) < 6:
			raise ParseError("file is too small")
		
		bom = struct.unpack_from(">H", data, 4)[0]
		self.endianness = ">" if bom == 0xFEFF else "<"

		# Parse file
		stream = streams.StreamIn(data, self.endianness)
		if stream.ascii(4) != "AATN": raise ParseError("magic number is invalid")
		if stream.u16() != 0xFEFF: raise ParseError("BOM is invalid")

		self.version = stream.u16()
		if self.version != 1:
			raise ParseError("unsupported version number")

		string_offset = stream.u32()

		self.curves = {}
		for i in range(5):
			curve = CurveDescription()
			curve.name = stream.string_at(string_offset + stream.u32())
			curve.type = stream.u32()
			self.curves[i] = curve
		
		self.directivity = stream.string_at(string_offset + stream.u32())
		self.culling = stream.string_at(string_offset + stream.u32())

		self.listener_enabled = bool(stream.u32())
		self.occlusion_enabled = bool(stream.u32())
	
	def save(self):
		if self.version != 1:
			raise SaveError("unsupported version number")
		
		string_table = StringTable()

		stream = streams.StreamOut(self.endianness)
		stream.ascii("AATN")
		stream.u16(0xFEFF)
		stream.u16(self.version)
		stream.u32(0x44)

		for i in range(5):
			stream.u32(string_table.add(self.curves[i].name))
			stream.u32(self.curves[i].type)

		stream.u32(string_table.add(self.directivity))
		stream.u32(string_table.add(self.culling))		
		stream.u32(self.listener_enabled)
		stream.u32(self.occlusion_enabled)
		stream.write(string_table.get())
		stream.align(4)
		return stream.get()
