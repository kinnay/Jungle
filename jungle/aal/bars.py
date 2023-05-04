
from jungle.error import ParseError, SaveError
from jungle import streams

import struct


class Asset:
	def __init__(self):
		self.metadata = b""
		self.data = b""


class BARSFile:
	def __init__(self):
		self.version = 0x101
		self.endianness = "<"

		self.name = ""
		self.assets = {}
	
	def parse(self, data):
		# Determine endianness
		if len(data) < 10:
			raise ParseError("file is too small")
		
		bom = struct.unpack_from(">H", data, 8)[0]
		self.endianness = ">" if bom == 0xFEFF else "<"

		# Parse file
		stream = streams.StreamIn(data, self.endianness)
		if stream.ascii(4) != "BARS": raise ParseError("magic number is invalid")
		if stream.u32() != len(data): raise ParseError("file size is invalid")
		if stream.u16() != 0xFEFF: raise ParseError("BOM is invalid")

		self.version = stream.u16()
		if self.version != 0x101:
			raise ValueError("unsupported version number")

		num_assets = stream.u32()

		hashes = stream.repeat(stream.u32, num_assets)

		self.assets = {}
		for i in range(num_assets):
			metadata_offset = stream.u32()
			data_offset = stream.u32()

			metadata_size = stream.u32_at(metadata_offset + 8)
			data_size = stream.u32_at(data_offset + 12)

			asset = Asset()
			asset.metadata = data[metadata_offset:metadata_offset+metadata_size]
			asset.data = data[data_offset:data_offset+data_size]
			self.assets[hashes[i]] = asset
	
	def save(self):
		if self.version != 0x101:
			raise SaveError("unsupported version number")

		offset = 0x10 + len(self.assets) * 0xC
		metadata_offsets = {}
		for hash, asset in sorted(self.assets.items()):
			metadata_offsets[hash] = offset
			offset += len(asset.metadata)
		
		data_offsets = {}
		for hash, asset in sorted(self.assets.items()):
			offset = (offset + 63) & ~63
			data_offsets[hash] = offset
			offset += len(asset.data)

		stream = streams.StreamOut(self.endianness)
		stream.ascii("BARS")
		stream.u32(offset)
		stream.u16(0xFEFF)
		stream.u16(self.version)
		stream.u32(len(self.assets))

		for hash in sorted(self.assets):
			stream.u32(hash)
		
		for hash, asset in sorted(self.assets.items()):
			stream.u32(metadata_offsets[hash])
			stream.u32(data_offsets[hash])
		
		for hash, asset in sorted(self.assets.items()):
			stream.write(asset.metadata)
		
		for hash, asset in sorted(self.assets.items()):
			stream.align(64)
			stream.write(asset.data)
		
		return stream.get()
