
from jungle.errors import ParseError, SaveError
from jungle import streams


class Yaz0File:
	def __init__(self):
		self.alignment = 0
		self.size = 0
		self.data = b""
	
	def parse(self, data):
		stream = streams.StreamIn(data, ">")
		if stream.ascii(4) != "Yaz0":
			raise ParseError("magic number is invalid")

		self.size = stream.u32()
		self.alignment = stream.u32()
		stream.pad(4)

		self.data = stream.readall()
	
	def save(self):
		stream = streams.StreamOut(">")
		stream.ascii("Yaz0")
		stream.u32(self.size)
		stream.u32(self.alignment)
		stream.pad(4)

		stream.write(self.data)
		return stream.get()
