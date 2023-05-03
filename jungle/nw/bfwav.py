
from jungle.error import ParseError, SaveError
from jungle.nw import sound
from jungle import streams


class SampleFormat:
	PCM_8 = 0
	PCM_16 = 1
	ADPCM = 2


def calc_channel_size(format, samples):
	if format == SampleFormat.PCM_8: return samples
	if format == SampleFormat.PCM_16: return samples * 2

	# ADPCM
	size = samples // 14 * 8
	if samples % 14:
		size += (samples % 14 + 1) // 2 + 1
	return size


class ADPCMContext:
	def __init__(self):
		self.header = 0
		self.hist1 = 0
		self.hist2 = 0
	
	def parse(self, stream):
		self.header = stream.u16()
		self.hist1 = stream.s16()
		self.hist2 = stream.s16()
	
	def save(self, stream):
		stream.u16(self.header)
		stream.s16(self.hist1)
		stream.s16(self.hist2)


class ADPCMInfo:
	def __init__(self):
		self.coefs = [0] * 16
		self.main_context = ADPCMContext()
		self.loop_context = ADPCMContext()
	
	def parse(self, stream):
		self.coefs = stream.repeat(stream.s16, 16)
		self.main_context.parse(stream)
		self.loop_context.parse(stream)
	
	def save(self, stream):
		stream.repeat(self.coefs, stream.s16)
		self.main_context.save(stream)
		self.loop_context.save(stream)


class ChannelInfo:
	def __init__(self):
		self.data_ref = sound.SectionReference()
		self.adpcm_ref = sound.SectionReference()
	
	def parse(self, stream):
		self.data_ref.parse(stream)
		self.adpcm_ref.parse(stream)
		stream.pad(4)
	
	def save(self, stream):
		self.data_ref.save(stream)
		self.adpcm_ref.save(stream)
		stream.pad(4)


class BFWAVChannel:
	def __init__(self):
		self.data = b""
		self.adpcm_info = None


class BFWAVFile:
	def __init__(self):
		self.endianness = "<"
		self.version = 0x10100

		self.sample_format = SampleFormat.ADPCM
		self.sample_rate = 32000

		self.is_looped = False
		self.loop_start = 0
		self.num_samples = 0
		self.channels = []
	
	def parse(self, data):
		# Parse header and blocks
		file = sound.SoundFile()
		file.parse(data)

		# Verify magic number
		if file.magic != "FWAV":
			raise ParseError("magic number is invalid")

		# Read header info
		self.endianness = file.endianness
		self.version = file.version
		if self.version != 0x10100:
			raise ParseError("unsupported version number")
		
		# Parse the DATA block
		stream = streams.StreamIn(file.blocks[0x7001], self.endianness)
		if stream.ascii(4) != "DATA": raise ParseError("DATA block has invalid identifier")
		if stream.u32() != stream.size(): raise ParseError("DATA block has invalid size")
		data = stream.readall()

		# Parse the INFO block
		stream = streams.StreamIn(file.blocks[0x7000], self.endianness)
		if stream.ascii(4) != "INFO": raise ParseError("INFO block has invalid identifier")
		if stream.u32() != stream.size(): raise ParseError("INFO block has invalid size")
		
		self.sample_format = stream.u8()
		self.is_looped = stream.bool()
		stream.pad(2)

		self.sample_rate = stream.u32()
		self.loop_start = stream.u32()
		self.num_samples = stream.u32()
		stream.pad(4)

		base = stream.tell()
		channel_refs = []
		for i in range(stream.u32()):
			ref = sound.SectionReference()
			ref.parse(stream)
			channel_refs.append(ref)

		# How many bytes does the channel use in the DATA section
		channel_size = calc_channel_size(self.sample_format, self.num_samples)

		self.channels = []
		for ref in channel_refs:
			stream.seek(base + ref.offset)

			info = ChannelInfo()
			info.parse(stream)

			channel = BFWAVChannel()
			channel.data = data[info.data_ref.offset:info.data_ref.offset+channel_size]
			if info.adpcm_ref.valid():
				stream.seek(base + ref.offset + info.adpcm_ref.offset)
				channel.adpcm_info = ADPCMInfo()
				channel.adpcm_info.parse(stream)
			self.channels.append(channel)
	
	def save(self):
		if self.version != 0x10100:
			raise SaveError("unsupported version number")
		
		info_stream = streams.StreamOut(self.endianness)
		info_stream.ascii("INFO")
		info_stream.skip(4) # Block size
		info_stream.u8(self.sample_format)
		info_stream.bool(self.is_looped)
		info_stream.pad(2)
		info_stream.u32(self.sample_rate)
		info_stream.u32(self.loop_start)
		info_stream.u32(self.num_samples)
		info_stream.pad(4)
		info_stream.u32(len(self.channels))

		data_stream = streams.StreamOut(self.endianness)
		data_stream.ascii("DATA")
		data_stream.skip(4) # Block size

		offset = 4 + 8 * len(self.channels)
		channel_stream = streams.StreamOut(self.endianness)
		for channel in self.channels:
			ref = sound.SectionReference()
			ref.type = 0x7100
			ref.offset = offset + channel_stream.tell()
			ref.save(info_stream)

			data_stream.align(32)

			channel_info = ChannelInfo()
			channel_info.data_ref = sound.SectionReference()
			channel_info.data_ref.type = 0x1F00
			channel_info.data_ref.offset = data_stream.tell() - 8
			if channel.adpcm_info:
				channel_info.adpcm_ref = sound.SectionReference()
				channel_info.adpcm_ref.type = 0x300
				channel_info.adpcm_ref.offset = 0x14
			
			channel_info.save(channel_stream)
			if channel.adpcm_info:
				channel.adpcm_info.save(channel_stream)
			
			data_stream.write(channel.data)

		info_stream.write(channel_stream.get())
		info_stream.align(32)

		info_stream.seek(4); info_stream.u32(info_stream.size())
		data_stream.seek(4); data_stream.u32(data_stream.size())

		file = sound.SoundFile()
		file.magic = "FWAV"
		file.endianness = self.endianness
		file.version = self.version
		file.blocks = {
			0x7000: info_stream.get(),
			0x7001: data_stream.get()
		}
		return file.save()
