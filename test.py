
from jungle.aal import bamta, bars, barslist
from jungle.nw import bfwav
from jungle.sead import sarc, yaz0
import os
import sys


crash = "--error" in sys.argv


def test_basic(cls):
	file = cls()
	file.save()

def test_format(name, cls):
	print("%s:" %name)

	test_basic(cls)

	if not os.path.isdir("files/%s" %name):
		return
	
	for filename in sorted(os.listdir("files/%s" %name)):
		print("    %s: " %filename, end="")
		
		with open("files/%s/%s" %(name, filename), "rb") as f:
			data = f.read()
		
		file = cls()
		try:
			file.parse(data)
		except Exception as e:
			if crash:
				raise
			print(e)
			continue
		
		try:
			saved = file.save()
		except Exception as e:
			if crash:
				raise
			print(e)
			continue
		
		if saved != data:
			print("mismatch")
			os.makedirs("files/mismatch", exist_ok=True)
			with open("files/mismatch/%s" %filename, "wb") as f:
				f.write(saved)
		else:
			print("ok")


test_format("bamta", bamta.BAMTAFile)
test_format("bars", bars.BARSFile)
test_format("barslist", barslist.BARSLISTFile)
test_format("bfwav", bfwav.BFWAVFile)
test_format("sarc", sarc.SARCFile)
test_format("yaz0", yaz0.Yaz0File)
