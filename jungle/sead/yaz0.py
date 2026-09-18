
from jungle.errors import ParseError
from jungle import streams


class Yaz0File:
    alignment: int
    size: int
    data: bytes

    def __init__(self):
        self.alignment = 0
        self.size = 0
        self.data = b""
    
    def parse(self, data: bytes) -> None:
        stream = streams.StreamIn(data, ">")
        if stream.ascii(4) != "Yaz0":
            raise ParseError("magic number is invalid")

        self.size = stream.u32()
        self.alignment = stream.u32()
        stream.pad(4)

        self.data = stream.readall()
    
    def save(self) -> bytes:
        stream = streams.StreamOut(">")
        stream.ascii("Yaz0")
        stream.u32(self.size)
        stream.u32(self.alignment)
        stream.pad(4)

        stream.write(self.data)
        return stream.get()
