
from jungle.error import ParseError

import contextlib
import struct


class StreamIn:
	def __init__(self, data, endian):
		self.endian = endian
		self.data = data
		self.pos = 0
		self.stack = []
	
	# General functions
	def set_endian(self, endian): self.endian = endian
	
	def push(self): self.stack.append(self.pos)
	def pop(self): self.pos = self.stack.pop()

	@contextlib.contextmanager
	def jump(self, pos):
		self.push()
		self.seek(pos)
		yield
		self.pop()
		
	def get(self): return self.data
	def size(self): return len(self.data)
	
	def tell(self): return self.pos
	def seek(self, pos):
		if pos > self.size():
			raise ParseError("buffer overflow")
		self.pos = pos
	
	def skip(self, num): self.seek(self.pos + num)
	def align(self, num): self.skip((num - self.pos % num) % num)
	def eof(self): return self.pos == len(self.data)
	def available(self): return len(self.data) - self.pos
	
	# Parsing functions
	def peek(self, num):
		if self.available() < num:
			raise ParseError("buffer overflow")
		return self.data[self.pos : self.pos + num]
		
	def read(self, num):
		data = self.peek(num)
		self.skip(num)
		return data
		
	def readall(self):
		return self.read(self.available())
		
	def pad(self, num, char=b"\0"):
		if self.read(num) != char * num:
			raise ParseError("incorrect padding")
			
	def ascii(self, num):
		return self.read(num).decode("ascii")
		
	def u8(self): return self.read(1)[0]
	def u16(self): return struct.unpack(self.endian + "H", self.read(2))[0]
	def u32(self): return struct.unpack(self.endian + "I", self.read(4))[0]
	def u64(self): return struct.unpack(self.endian + "Q", self.read(8))[0]
	
	def s8(self): return struct.unpack("b", self.read(1))[0]
	def s16(self): return struct.unpack(self.endian + "h", self.read(2))[0]
	def s32(self): return struct.unpack(self.endian + "i", self.read(4))[0]
	def s64(self): return struct.unpack(self.endian + "q", self.read(8))[0]
	
	def u24(self):
		if self.endian == ">":
			return (self.u16() << 8) | self.u8()
		return self.u8() | (self.u16() << 8)
	
	def float(self): return struct.unpack(self.endian + "f", self.read(4))[0]
	def double(self): return struct.unpack(self.endian + "d", self.read(8))[0]
	
	def bool(self): return bool(self.u8())
	def char(self): return chr(self.u8())
	def wchar(self): return chr(self.u16())
	
	def chars(self, num): return "".join(self.repeat(self.char, num))
	def wchars(self, num): return "".join(self.repeat(self.wchar, num))

	def string(self):
		data = []
		byte = self.u8()
		while byte != 0:
			data.append(byte)
			byte = self.u8()
		return bytes(data).decode()
	
	def repeat(self, func, count):
		return [func() for i in range(count)]

	# Parsing functions at specific position
	def string_at(self, pos):
		with self.jump(pos):
			return self.string()
