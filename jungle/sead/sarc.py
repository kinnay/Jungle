
from jungle.errors import ParseError, SaveError
from jungle import streams

import struct


def calculate_hash(filename, multiplier, sign_extend):
	"""Calculates the hash for the SFAT section.

	In Switch games, each byte of the filename is sign extended.
	This is important if the filename uses non-ascii characters.
	"""
	hash = 0
	for byte in filename.encode():
		if sign_extend and byte & 0x80:
			byte -= 0x100
		hash = hash * multiplier + byte
	return hash & 0xFFFFFFFF

def calculate_alignment(offset):
	"""Calculates the maximum alignment of a given offset."""
	alignment = 1
	while offset % alignment == 0:
		alignment *= 2
	return alignment // 2


class SARCFile:
	def __init__(self):
		self.version = 0x100
		self.endianness = "<"
		self.hash_multiplier = 101
		self.sign_extend = True
		self.alignment = 4
		
		self.files = {}
		self.unnamed_files = {}
	
	def parse(self, data):
		# Determine endianness
		if len(data) < 8:
			raise ParseError("file is too small")

		bom = struct.unpack_from(">H", data, 6)[0]
		self.endianness = ">" if bom == 0xFEFF else "<"

		# Parse SARC header
		stream = streams.StreamIn(data, self.endianness)
		if stream.ascii(4) != "SARC": raise ParseError("magic number is invalid")
		if stream.u16() != 0x14: raise ParseError("header size is invalid")
		if stream.u16() != 0xFEFF: raise ParseError("BOM is invalid")
		if stream.u32() != len(data): raise ParseError("file size is invalid")

		data_offset = stream.u32()

		# Derive the alignment from the data offset
		self.alignment = calculate_alignment(data_offset)

		self.version = stream.u16()
		if self.version != 0x100:
			raise ParseError("unsupported version number")

		stream.pad(2)

		# Parse SFAT header
		if stream.ascii(4) != "SFAT": raise ParseError("SFAT has invalid magic number")
		if stream.u16() != 0xC: raise ParseError("SFAT has invalid header size")

		num_files = stream.u16()
		if num_files > 0x3FFF:
			raise ParseError("too many files")
		
		self.hash_multiplier = stream.u32()

		# Parse SFAT table
		sign_flipped = False
		fnt_offset = stream.tell() + num_files * 16 + 8
		for i in range(num_files):
			hash = stream.u32()
			attribs = stream.u32()
			start_offset = stream.u32()
			end_offset = stream.u32()
			file_data = data[data_offset + start_offset : data_offset + end_offset]

			# This is unlikely, but just to be safe
			alignment = calculate_alignment(data_offset + start_offset)
			if alignment > self.alignment:
				self.alignment = alignment

			if attribs >> 24:
				name = stream.string_at(fnt_offset + (attribs & 0xFFFFFF) * 4)

				# Because we don't know which platform the SARC file is made for
				# we don't know if we should sign extend the filename bytes.
				# 
				# We simply try both hashes and check which one matches. Note that
				# this is only relevant if the filename contains non-ascii characters.
				# If both hashes are wrong, or the sign extension flag was determined
				# before, the file must be corrupted.
				if calculate_hash(name, self.hash_multiplier, self.sign_extend) != hash:
					if sign_flipped or calculate_hash(name, self.hash_multiplier, not self.sign_extend) != hash:
						raise ParseError("file has unexpected hash")
					self.sign_extend = not self.sign_extend
					sign_flipped = True
				
				self.files[name] = file_data
			else:
				# SARC supports unnamed files if exactly one file has the given hash
				if hash in self.unnamed_files:
					raise ParseError("duplicate hash for unnamed file")
				self.unnamed_files[hash] = file_data
	
	def save(self):
		if self.version != 0x100:
			raise SaveError("unsupported version number")

		num_files = len(self.files) + len(self.unnamed_files)
		if num_files > 0x3FFF:
			raise SaveError("too many files")

		fat_stream = streams.StreamOut(self.endianness)
		fat_stream.ascii("SFAT")
		fat_stream.u16(0xC)
		fat_stream.u16(num_files)
		fat_stream.u32(self.hash_multiplier)

		fnt_stream = streams.StreamOut(self.endianness)
		fnt_stream.ascii("SFNT")
		fnt_stream.u16(8)
		fnt_stream.pad(2)

		data_stream = streams.StreamOut(self.endianness)

		hashes = {}
		for name, data in self.files.items():
			hash = calculate_hash(name, self.hash_multiplier, self.sign_extend)

			index = hashes.get(hash, 1)
			if index > 255:
				raise SaveError("too many files with the same hash")
			hashes[hash] = index + 1
			
			data_stream.align(self.alignment)
			data_offset = data_stream.tell()
			data_stream.write(data)

			fnt_offset = fnt_stream.tell() - 8
			fnt_stream.string(name)
			fnt_stream.align(4)

			fat_stream.u32(hash)
			fat_stream.u32((index << 24) | fnt_offset)
			fat_stream.u32(data_offset)
			fat_stream.u32(data_offset + len(data))

		for hash, data in self.unnamed_files.items():
			if hash in hashes:
				raise SaveError("duplicate hash for unnamed file")
			hashes[hash] = 1
			
			data_stream.align(self.alignment)
			data_offset = data_stream.tell()
			data_stream.write(data)

			fat_stream.u32(hash)
			fat_stream.u32(0)
			fat_stream.u32(data_offset)
			fat_stream.u32(data_offset + len(data))

		stream = streams.StreamOut(self.endianness)
		stream.ascii("SARC")
		stream.u16(0x14)
		stream.u16(0xFEFF)
		stream.skip(8)
		stream.u16(self.version)
		stream.pad(2)
		stream.write(fat_stream.get())
		stream.write(fnt_stream.get())
		stream.align(self.alignment)

		data_offset = stream.tell()
		stream.write(data_stream.get())

		stream.seek(8)
		stream.u32(stream.size())
		stream.u32(data_offset)
		return stream.get()
