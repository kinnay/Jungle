
import binascii
import pkg_resources


class RainbowTable:
	def __init__(self):
		self.crc32_table = None
	
	def wordlist(self):
		filename = pkg_resources.resource_filename("jungle", "files/wordlist.txt")
		with open(filename) as f:
			return f.read().splitlines()
	
	def generate(self, func):
		table = {}
		for word in self.wordlist():
			table[func(word.encode())] = word
		return table

	def crc32(self, hash):
		if self.crc32_table is None:
			self.crc32_table = self.generate(binascii.crc32)
		return self.crc32_table.get(hash)

table = RainbowTable()


def crc32(hash):
	return table.crc32(hash)
