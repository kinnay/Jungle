
from jungle.errors import ParseError

import contextlib
import struct


class StreamIn:
    def __init__(self, data, endianness):
        self.endianness = endianness
        self.data = data
        self.pos = 0
        self.stack = []
    
    # General functions
    def set_endianness(self, endianness):
        self.endianness = endianness
    
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
        try:
            return self.read(num).decode("ascii")
        except UnicodeDecodeError:
            raise ParseError("ascii decoding failed")
        
    def u8(self): return self.read(1)[0]
    def u16(self): return struct.unpack(self.endianness + "H", self.read(2))[0]
    def u32(self): return struct.unpack(self.endianness + "I", self.read(4))[0]
    def u64(self): return struct.unpack(self.endianness + "Q", self.read(8))[0]
    
    def s8(self): return struct.unpack("b", self.read(1))[0]
    def s16(self): return struct.unpack(self.endianness + "h", self.read(2))[0]
    def s32(self): return struct.unpack(self.endianness + "i", self.read(4))[0]
    def s64(self): return struct.unpack(self.endianness + "q", self.read(8))[0]
    
    def u24(self):
        if self.endianness == ">":
            return (self.u16() << 8) | self.u8()
        return self.u8() | (self.u16() << 8)
    
    def float(self): return struct.unpack(self.endianness + "f", self.read(4))[0]
    def double(self): return struct.unpack(self.endianness + "d", self.read(8))[0]
    
    def bool(self): return bool(self.u8())
    def char(self): return chr(self.u8())
    def wchar(self): return chr(self.u16())
    
    def chars(self, num): return "".join(self.repeat(self.char, num))
    def wchars(self, num): return "".join(self.repeat(self.wchar, num))

    def string(self, encoding="utf-8"):
        data = []
        byte = self.u8()
        while byte != 0:
            data.append(byte)
            byte = self.u8()
        
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            raise ParseError("string decoding failed")
    
    def repeat(self, func, count):
        return [func() for i in range(count)]

    def peek_u32(self): return struct.unpack(self.endianness + "I", self.peek(4))[0]
    
    def peek_at(self, pos, size):
        with self.jump(pos):
            return self.peek(size)
    
    def read_at(self, pos, size):
        return self.peek_at(pos, size)

    def string_at(self, pos, encoding="utf-8"):
        with self.jump(pos):
            return self.string(encoding)
    
    def u8_at(self, pos): return self.read_at(pos, 1)[0]
    def u32_at(self, pos): return struct.unpack(self.endianness + "I", self.read_at(pos, 4))[0]
    def u64_at(self, pos): return struct.unpack(self.endianness + "Q", self.read_at(pos, 8))[0]
    
    def s64_at(self, pos): return struct.unpack(self.endianness + "q", self.read_at(pos, 8))[0]
    
    def double_at(self, pos): return struct.unpack(self.endianness + "d", self.read_at(pos, 8))[0]


class StreamOut:
    def __init__(self, endianness):
        self.endianness = endianness
        self.data = bytearray()
        self.pos = 0
        self.stack = []
        
    def push(self): self.stack.append(self.pos)
    def pop(self): self.pos = self.stack.pop()
    
    @contextlib.contextmanager
    def jump(self, pos):
        self.push()
        self.seek(pos)
        yield
        self.pop()
        
    def get(self): return bytes(self.data)
    def size(self): return len(self.data)
    def tell(self): return self.pos
    def seek(self, pos):
        if pos > len(self.data):
            self.data += bytes(pos - len(self.data))
        self.pos = pos
    def skip(self, num): self.seek(self.pos + num)
    def align(self, num): self.skip((num - self.pos % num) % num)
    def available(self): return len(self.data) - self.pos
    def eof(self): return self.pos >= len(self.data)

    def reserve(self, num):
        pos = self.tell()
        self.skip(num)
        return pos
        
    def write(self, data):
        self.data[self.pos : self.pos + len(data)] = data
        self.pos += len(data)
        
    def pad(self, num, char=b"\0"):
        self.write(char * num)
        
    def ascii(self, data):
        self.write(data.encode("ascii"))
        
    def u8(self, value): self.write(bytes([value]))
    def u16(self, value): self.write(struct.pack(self.endianness + "H", value))
    def u32(self, value): self.write(struct.pack(self.endianness + "I", value))
    def u64(self, value): self.write(struct.pack(self.endianness + "Q", value))
    
    def s8(self, value): self.write(struct.pack("b", value))
    def s16(self, value): self.write(struct.pack(self.endianness + "h", value))
    def s32(self, value): self.write(struct.pack(self.endianness + "i", value))
    def s64(self, value): self.write(struct.pack(self.endianness + "q", value))
    
    def u24(self, value):
        if self.endianness == ">":
            self.u16(value >> 8)
            self.u8(value & 0xFF)
        else:
            self.u8(value & 0xFF)
            self.u16(value >> 8)
            
    def float(self, value): self.write(struct.pack(self.endianness + "f", value))
    def double(self, value): self.write(struct.pack(self.endianness + "d", value))
    
    def bool(self, value): self.u8(1 if value else 0)
    def char(self, value): self.u8(ord(value))
    def wchar(self, value): self.u16(ord(value))
    
    def chars(self, data): self.repeat(data, self.char)
    def wchars(self, data): self.repeat(data, self.wchar)
    
    def string(self, data):
        self.write(data.encode() + b"\0")
    
    def repeat(self, list, func):
        for value in list:
            func(value)
    
    def u32_at(self, pos, value):
        with self.jump(pos): self.u32(value)
    def u64_at(self, pos, value):
        with self.jump(pos): self.u64(value)
    
    def s64_at(self, pos, value):
        with self.jump(pos): self.s64(value)
    
    def double_at(self, pos, value):
        with self.jump(pos): self.double(value)
