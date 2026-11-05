
from jungle.dkctf.common import CAssetHeader, CFormDescriptor, CChunkDescriptor
from jungle.dkctf.codegen import GPSMDescription
from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut


class GENPFile:
    root: GPSMDescription

    def __init__(self):
        self.root = GPSMDescription()

    def parse(self, data: bytes) -> None:
        pack = CFormDescriptor.fromdata(data, "GENP", 15)

        stream = StreamIn(pack, ">")
        chunk = stream.extract(CChunkDescriptor)
        if chunk.type != "DESC" or chunk.version != 0:
            raise ParseError("unsupported chunk type")

        stream = StreamIn(chunk.data, ">")
        header = stream.extract(CAssetHeader)
        if header.type != 0x6E19 or header.version != 1:
            raise ParseError("invalid asset header")

        if stream.ascii(4) != "GPSM":
            raise ParseError("invalid root node")

        self.root = stream.extract(GPSMDescription)

    def save(self) -> bytes:
        header = CAssetHeader(0x6E19, 1)

        stream = StreamOut(">")
        stream.add(header)
        stream.ascii("GPSM")
        stream.add(self.root)

        chunk = CChunkDescriptor("DESC", 0, stream.get())
        stream = StreamOut(">")
        stream.add(chunk)

        form = CFormDescriptor("GENP", 15, stream.get())
        stream = StreamOut(">")
        stream.add(form)
        return stream.get()
