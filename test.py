
from jungle.aal import baatn, bameta, bars, barslist
from jungle.agl import pmaa
from jungle.cas import baev
from jungle.common import byaml
from jungle.gfd import gfx2
from jungle.lms import msbp
from jungle.nw import bfwav
from jungle.sead import sarc, yaz0
from jungle.xlink import slink
import os
import sys


RED = chr(0x1F534)
GREEN = chr(0x1F7E2)
YELLOW = chr(0x1F7E1)


crash = "--error" in sys.argv
formats = [arg for arg in sys.argv[1:] if not arg.startswith("--")]


def test_basic(cls):
    file = cls()
    file.save()

def test_format(name, cls):
    if formats and name not in formats:
        return

    print("%s:" %name)

    test_basic(cls)

    if not os.path.isdir(os.path.join("files", name)):
        return

    paths = []
    for dirpath, dirnames, filenames in os.walk(os.path.join("files", name)):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            paths.append(filepath)
    
    for path in sorted(paths):
        filename = os.path.basename(path)

        with open(path, "rb") as f:
            data = f.read()
        
        file = cls()
        try:
            file.parse(data)
            saved = file.save()
        except Exception as e:
            if crash:
                raise
            print(f"    {RED} {filename}: {e}")
            continue
        
        if saved != data:
            print(f"    {YELLOW} {filename}: mismatch")
            os.makedirs("files/mismatch", exist_ok=True)
            with open(os.path.join("files/mismatch", filename), "wb") as f:
                f.write(saved)
        else:
            print(f"    {GREEN} {filename}")
    print()


test_format("baatn", baatn.BAATNFile)
test_format("baev", baev.BAEVFile)
test_format("bameta", bameta.BAMETAFile)
test_format("bars", bars.BARSFile)
test_format("barslist", barslist.BARSLISTFile)
test_format("bfwav", bfwav.BFWAVFile)
test_format("byaml", byaml.BYAMLFile)
test_format("gsh", gfx2.Gfx2File)
test_format("gtx", gfx2.Gfx2File)
test_format("msbp", msbp.MSBPFile)
test_format("pmaa", pmaa.PMAAFile)
test_format("sarc", sarc.SARCFile)
test_format("slink", slink.SLINKFile)
test_format("yaz0", yaz0.Yaz0File)
