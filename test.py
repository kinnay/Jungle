
from jungle.aal import baatn, bameta, bars, barslist
from jungle.agl import pmaa
from jungle.common import byaml
from jungle.gfd import gfx2
from jungle.nw import bfwav
from jungle.sead import sarc, yaz0
import os
import sys


RED = chr(0x1F534)
GREEN = chr(0x1F7E2)
YELLOW = chr(0x1F7E1)


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
		with open("files/%s/%s" %(name, filename), "rb") as f:
			data = f.read()
		
		file = cls()
		try:
			file.parse(data)
			saved = file.save()
		except Exception as e:
			if crash:
				raise
			print("    " + RED + " " + filename + ": " + str(e))
			continue
		
		if saved != data:
			print("    " + YELLOW + " " + filename + ": mismatch")
			os.makedirs("files/mismatch", exist_ok=True)
			with open("files/mismatch/%s" %filename, "wb") as f:
				f.write(saved)
		else:
			print("    " + GREEN + " " + filename)
	print()


test_format("baatn", baatn.BAATNFile)
test_format("bameta", bameta.BAMETAFile)
test_format("bars", bars.BARSFile)
test_format("barslist", barslist.BARSLISTFile)
test_format("bfwav", bfwav.BFWAVFile)
test_format("byaml", byaml.BYAMLFile)
test_format("gsh", gfx2.Gfx2File)
test_format("gtx", gfx2.Gfx2File)
test_format("pmaa", pmaa.PMAAFile)
test_format("sarc", sarc.SARCFile)
test_format("yaz0", yaz0.Yaz0File)
