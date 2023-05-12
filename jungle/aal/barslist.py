
from jungle.error import ParseError, SaveError
from jungle import streams

import struct


class BARSLISTFile:
	def __init__(self):
		self.version = 1
		self.endianness = "<"

		self.name = ""
		self.resources = []
	
	def parse(self, data):
		# Determine endianness
		if len(data) < 6:
			raise ParseError("file is too small")
		
		bom = struct.unpack_from(">H", data, 4)[0]
		self.endianness = ">" if bom == 0xFEFF else "<"

		# Parse file
		stream = streams.StreamIn(data, self.endianness)
		if stream.ascii(4) != "ARSL": raise ParseError("magic number is invalid")
		if stream.u16() != 0xFEFF: raise ParseError("BOM is invalid")

		self.version = stream.u16()
		if self.version != 1:
			raise ValueError("unsupported version number")

		name_offset = stream.u32()
		resource_offsets = stream.repeat(stream.u32, stream.u32())

		base = stream.tell()

		self.name = stream.string_at(base + name_offset)
		for offset in resource_offsets:
			self.resources.append(stream.string_at(base + offset))
	
	def save(self):
		if self.version != 1:
			raise SaveError("unsupported version number")

		string_stream = streams.StreamOut(self.endianness)

		stream = streams.StreamOut(self.endianness)
		stream.ascii("ARSL")
		stream.u16(0xFEFF)
		stream.u16(self.version)

		stream.u32(string_stream.tell())
		string_stream.string(self.name)

		stream.u32(len(self.resources))
		for resource in self.resources:
			stream.u32(string_stream.tell())
			string_stream.string(resource)
		
		stream.write(string_stream.get())
		return stream.get()
