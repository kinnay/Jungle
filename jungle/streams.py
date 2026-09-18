
from typing import Callable, Generator, Iterable

from jungle.errors import ParseError

import contextlib
import struct


Float = float


class StreamIn:
    """
    Implements a memory input stream.

    When an error occurs, such as advancing the stream past the end of its
    buffer, incorrect padding bytes, or a string encoding issue, ParseError is
    raised.
    """

    _endian: str
    _data: bytes
    _pos: int
    _stack: list[int]

    def __init__(self, data: bytes, endian: str):
        self._endian = endian
        self._data = data
        self._pos = 0
        self._stack = []
    
    def set_endianness(self, endianness: str) -> None:
        """Changes the current endianness of the stream."""
        self._endian = endianness
    
    def push(self) -> None:
        """Pushes the current position of the stream onto a stack."""
        self._stack.append(self._pos)
    
    def pop(self) -> None:
        """Pops the position of the stream from the stack."""
        self._pos = self._stack.pop()

    @contextlib.contextmanager
    def jump(self, pos: int) -> Generator[None]:
        """
        This context manager jumps to the given position, and jumps back to the
        original position when the context manager exits.
        """
        self.push()
        self.seek(pos)
        yield
        self.pop()
        
    def get(self) -> bytes:
        """Returns the memory buffer of the input stream."""
        return self._data
    
    def size(self) -> int:
        """Returns the size of the input stream."""
        return len(self._data)
    
    def tell(self) -> int:
        """Returns the current position of the input stream."""
        return self._pos
    
    def seek(self, pos: int) -> None:
        """
        Changes the current position of the input stream. Raises ParseError
        if the stream is moved past the end of the memory buffer.
        """
        if pos > self.size():
            raise ParseError("buffer overflow")
        self._pos = pos
    
    def skip(self, num: int) -> None:
        """Skip num bytes in the input stream."""
        self.seek(self._pos + num)
    
    def align(self, num: int) -> None:
        """Advances the current position until it is a multiple of num."""
        self.skip((num - self._pos % num) % num)
    
    def eof(self) -> bool:
        """Returns whether the stream is currently at the end of the buffer."""
        return self._pos == len(self._data)
    
    def available(self) -> int:
        """
        Returns the number of bytes between the current position and the end of
        the input buffer.
        """
        return len(self._data) - self._pos
    
    def peek(self, num: int) -> bytes:
        """
        Returns num bytes from the input buffer without advancing the position.
        """
        if self.available() < num:
            raise ParseError("buffer overflow")
        return self._data[self._pos : self._pos + num]
        
    def read(self, num: int) -> bytes:
        """
        Returns num bytes from the input buffer and advances the current
        position.
        """
        data = self.peek(num)
        self.skip(num)
        return data
        
    def readall(self) -> bytes:
        """Reads all remaining bytes from the input buffer."""
        return self.read(self.available())
        
    def pad(self, num: int, char: bytes = b"\0") -> None:
        """
        Reads num bytes from the input buffer. If any of the read bytes is
        different from char, ValueError is raised.
        """
        if self.read(num) != char * num:
            raise ParseError("incorrect padding")
            
    def ascii(self, num: int) -> str:
        """Reads num ascii characters from the stream."""
        try:
            return self.read(num).decode("ascii")
        except UnicodeDecodeError:
            raise ParseError("ascii decoding failed")
        
    def u8(self) -> int:
        "Reads an 8-bit unsigned integer from the stream."
        return self.read(1)[0]
    
    def u16(self) -> int:
        """Reads a 16-bit unsigned integer from the stream."""
        return struct.unpack(self._endian + "H", self.read(2))[0]
    
    def u32(self) -> int:
        """Reads a 32-bit unsigned integer from the stream."""
        return struct.unpack(self._endian + "I", self.read(4))[0]
    
    def u64(self) -> int:
        """Reads a 64-bit unsigned integer from the stream."""
        return struct.unpack(self._endian + "Q", self.read(8))[0]
    
    def s8(self) -> int:
        """Reads an 8-bit signed integer from the stream."""
        return struct.unpack("b", self.read(1))[0]
    
    def s16(self) -> int:
        """Reads a 16-bit signed integer from the stream."""
        return struct.unpack(self._endian + "h", self.read(2))[0]
    
    def s32(self) -> int:
        """Reads a 32-bit signed integer from the stream."""
        return struct.unpack(self._endian + "i", self.read(4))[0]
    
    def s64(self) -> int:
        """Reads a 64-bit signed integer from the stream."""
        return struct.unpack(self._endian + "q", self.read(8))[0]
    
    def u24(self) -> int:
        """Reads a 24-bit unsigned integer from the stream."""
        if self._endian == ">":
            return (self.u16() << 8) | self.u8()
        return self.u8() | (self.u16() << 8)
    
    def float(self) -> Float:
        """Reads a 32-bit floating point value from the stream."""
        return struct.unpack(self._endian + "f", self.read(4))[0]
    
    def double(self) -> Float:
        """Reads a 64-bit floating point value from the stream."""
        return struct.unpack(self._endian + "d", self.read(8))[0]
    
    def bool(self) -> bool:
        """
        Reads an 8-bit integer from the stream and returns whether it is
        non-zero.
        """
        return bool(self.u8())
    
    def char(self) -> str:
        """Reads an 8-bit unicode character from the stream."""
        return chr(self.u8())
    
    def wchar(self) -> str:
        """Reads a 16-bit unicode character from the stream."""
        return chr(self.u16())
    
    def chars(self, num: int) -> str:
        """Reads num 8-bit unicode characters from the stream."""
        return "".join(self.repeat(self.char, num))
    
    def wchars(self, num: int) -> str:
        """Reads num 16-bit unicode characters from the stream."""
        return "".join(self.repeat(self.wchar, num))

    def string(self, encoding: str = "utf-8") -> str:
        """
        Reads a null-terminated string from the stream and decodes it using the
        given character encoding.
        """

        data = []
        byte = self.u8()
        while byte != 0:
            data.append(byte)
            byte = self.u8()
        
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            raise ParseError("string decoding failed")
    
    def repeat[T](self, func: Callable[[], T], count: int) -> list[T]:
        """
        Invokes func count times and aggregates the results. This method can be
        used to read a list of values from the stream.
        """
        return [func() for i in range(count)]

    def peek_u32(self):
        """
        Reads an unsigned 32-bit integer from the stream without advancing the
        position
        ."""
        return struct.unpack(self._endian + "I", self.peek(4))[0]
    
    def peek_at(self, pos: int, size: int) -> bytes:
        """Reads size bytes at a fixed position in the stream."""
        with self.jump(pos):
            return self.peek(size)
    
    def read_at(self, pos: int, size: int) -> bytes:
        """Reads size bytes at a fixed position in the stream."""
        return self.peek_at(pos, size)

    def string_at(self, pos: int, encoding: str = "utf-8") -> str:
        """
        Reads a null-terminated string with the given character encoding at a
        fixed position in the stream.
        """
        with self.jump(pos):
            return self.string(encoding)
    
    def u8_at(self, pos: int) -> int:
        """
        Reads an unsigned 8-bit integer at the given position in the stream.
        """
        return self.read_at(pos, 1)[0]
    
    def u32_at(self, pos: int) -> int:
        """
        Reads an unsigned 32-bit integer at the given position in the stream.
        """
        return struct.unpack(self._endian + "I", self.read_at(pos, 4))[0]
    
    def u64_at(self, pos: int) -> int:
        """
        Reads an unsigned 64-bit integer at the given position in the stream.
        """
        return struct.unpack(self._endian + "Q", self.read_at(pos, 8))[0]
    
    def s64_at(self, pos: int) -> int:
        """Reads a signed 64-bit integer at the given position in the stream."""
        return struct.unpack(self._endian + "q", self.read_at(pos, 8))[0]
    
    def double_at(self, pos: int) -> Float:
        """
        Reads a 64-bit floating point value at the given position in the stream.
        """
        return struct.unpack(self._endian + "d", self.read_at(pos, 8))[0]


class StreamOut:
    """
    Implements a memory output stream.

    When the stream is moved past the end of its current buffer, the buffer size
    is increased and padded with null bytes if applicable.
    """
    
    _endian: str
    _data: bytearray
    _pos: int
    _stack: list[int]

    def __init__(self, endian: str):
        self._endian = endian
        self._data = bytearray()
        self._pos = 0
        self._stack = []
        
    def push(self) -> None:
        """Pushes the current position of the stream onto a stack."""
        self._stack.append(self._pos)
    
    def pop(self) -> None:
        """Pops the position of the stream from the stack."""
        self._pos = self._stack.pop()
    
    @contextlib.contextmanager
    def jump(self, pos: int) -> Generator[None]:
        """
        This context manager jumps to the given position, and jumps back to the
        original position when the context manager exits.
        """
        self.push()
        self.seek(pos)
        yield
        self.pop()
        
    def get(self) -> bytes:
        """Returns the current memory buffer of the output stream."""
        return bytes(self._data)
    
    def size(self) -> int:
        """Returns the current size of the output stream."""
        return len(self._data)
    
    def tell(self) -> int:
        """Returns the current position of the output stream."""
        return self._pos

    def seek(self, pos: int) -> None:
        """
        Changes the current position of the input stream. Expands the output
        buffer if the stream is moved past the end of the memory buffer.
        """
        if pos > len(self._data):
            self._data += bytes(pos - len(self._data))
        self._pos = pos
    
    def skip(self, num: int) -> None:
        """
        Skips num bytes in the output stream, inserting zeros if the stream is
        moved past the end of the buffer.
        """
        self.seek(self._pos + num)
    
    def align(self, num: int) -> None:
        """Advances the current position until it is a multiple of num."""
        self.skip((num - self._pos % num) % num)

    def available(self) -> int:
        """
        Returns the number of bytes between the current position and the end of
        the output buffer.
        """
        return len(self._data) - self._pos
    
    def eof(self) -> bool:
        """Returns whether the stream is at the end of the output buffer."""
        return self._pos >= len(self._data)

    def reserve(self, num: int) -> int:
        """
        Skips ahead by num bytes and returns the position of the region that was
        skipped.
        """
        pos = self.tell()
        self.skip(num)
        return pos
        
    def write(self, data: bytes) -> None:
        """
        Writes data to the output buffer and advances the current position.
        """
        self._data[self._pos : self._pos + len(data)] = data
        self._pos += len(data)
        
    def pad(self, num: int, char: bytes = b"\0") -> None:
        """Writes num copies of char to the output stream."""
        self.write(char * num)
        
    def ascii(self, data: str) -> None:
        """Writes ASCII data to the output stream."""
        self.write(data.encode("ascii"))
        
    def u8(self, value: int) -> None:
        """Writes an 8-bit unsigned integer to the stream."""
        self.write(bytes([value]))
    
    def u16(self, value: int) -> None:
        """Writes a 16-bit unsigned integer to the stream."""
        self.write(struct.pack(self._endian + "H", value))
    
    def u32(self, value: int) -> None:
        """Writes a 32-bit unsigned integer to the stream."""
        self.write(struct.pack(self._endian + "I", value))

    def u64(self, value: int) -> None:
        """Writes a 64-bit unsigned integer to the stream."""
        self.write(struct.pack(self._endian + "Q", value))

    def s8(self, value: int) -> None:
        """Writes an 8-bit signed integer to the stream."""
        self.write(struct.pack("b", value))
    
    def s16(self, value: int) -> None:
        """Writes a 16-bit signed integer to the stream."""
        self.write(struct.pack(self._endian + "h", value))
    
    def s32(self, value: int) -> None:
        """Writes a 32-bit signed integer to the stream."""
        self.write(struct.pack(self._endian + "i", value))
    
    def s64(self, value: int) -> None:
        """Writes a 64-bit signed integer to the stream."""
        self.write(struct.pack(self._endian + "q", value))
    
    def u24(self, value: int) -> None:
        """Writes a 24-bit unsigned integer to the stream."""
        if self._endian == ">":
            self.u16(value >> 8)
            self.u8(value & 0xFF)
        else:
            self.u8(value & 0xFF)
            self.u16(value >> 8)
    
    def float(self, value: Float) -> None:
        """Writes a 32-bit floating point value to the stream."""
        self.write(struct.pack(self._endian + "f", value))
    
    def double(self, value: Float) -> None:
        """Writes a 64-bit floating point value to the stream."""
        self.write(struct.pack(self._endian + "d", value))
    
    def bool(self, value: bool) -> None:
        """Writes a boolean to the stream as an 8-bit integer (0 or 1)."""
        self.u8(1 if value else 0)
    
    def char(self, value: str) -> None:
        """Writes an 8-bit unicode character to the stream."""
        self.u8(ord(value))
    
    def wchar(self, value: str) -> None:
        """Writes a 16-bit unicode character to the stream."""
        self.u16(ord(value))
    
    def chars(self, data: str) -> None:
        """Writes a sequence of 8-bit unicode characters to the stream."""
        self.repeat(data, self.char)
    
    def wchars(self, data: str) -> None:
        """Writes a sequence of 16-bit unicode characters to the stream."""
        self.repeat(data, self.wchar)

    def string(self, data: str, encoding: str = "utf-8") -> None:
        """
        Writes a null-terminated string to the stream using the given character
        encoding.
        """
        self.write(data.encode(encoding) + b"\0")
    
    def repeat[T](self, list: Iterable[T], func: Callable[[T], None]) -> None:
        """
        Invokes func on each element of list. This method can be used to write
        a list of values of a specific type to the stream.
        """
        for value in list:
            func(value)
    
    def u32_at(self, pos: int, value: int) -> None:
        """
        Writes a 32-bit unsigned integer at the given position in the stream.
        """
        with self.jump(pos):
            self.u32(value)
    
    def u64_at(self, pos, value):
        """
        Writes a 64-bit unsigned integer at the given position in the stream.
        """
        with self.jump(pos):
            self.u64(value)
    
    def s64_at(self, pos, value):
        """
        Writes a 64-bit signed integer at the given position in the stream.
        """
        with self.jump(pos):
            self.s64(value)
    
    def double_at(self, pos, value):
        """
        Writes a 64-bit floating point value at the given position in the
        stream.
        """
        with self.jump(pos):
            self.double(value)
