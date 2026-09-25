
"""Implements the MSBT file format."""

from dataclasses import dataclass, field

from jungle.errors import ParseError, SaveError
from jungle.lms import common
from jungle.streams import StreamIn, StreamOut


@dataclass
class Tag:
    group: int = 0
    tag: int = 0
    parameters: bytes = b""


@dataclass
class Message:
    content: list[str | Tag] = field(default_factory=list)
    attributes: bytes = b""
    style: int | None = None


class MSBTFile:
    endianness: str
    encoding: common.Encoding
    version: int

    messages: dict[str, Message]
    buckets: int

    def __init__(self):
        self.endianness = "<"
        self.encoding = common.Encoding.UTF8
        self.version = 3

        self.messages = {}
        self.buckets = 101

    def parse(self, data: bytes) -> None:
        # Parse header and blocks
        file = common.MessageFile()
        file.parse(data)

        # Verify magic number
        if file.magic != "MsgStdBn":
            raise ParseError("magic number is invalid")

        # Read header info
        self.endianness = file.endianness
        self.encoding = file.encoding
        self.version = file.version
        if self.version != 3:
            raise ParseError("unsupported version number")
        
        # Verify blocks
        supported_blocks = ["LBL1", "ATR1", "TSY1", "TXT2"]
        for type in file.blocks:
            if type not in supported_blocks:
                raise ParseError(f"unsupported block: {type}")

        required_blocks = ["LBL1", "ATR1", "TXT2"]
        for type in required_blocks:
            if type not in file.blocks:
                raise ParseError(f"{type} block is missing")

        # Parse blocks
        labels, self.buckets = file.parse_labels(file.blocks["LBL1"])

        contents = self._parse_contents(file.blocks["TXT2"])

        styles = None
        if "TSY1" in file.blocks:
            styles = self._parse_styles(file.blocks["TSY1"])

        atr1_stream = StreamIn(file.blocks["ATR1"], file.endianness)

        if atr1_stream.u32() != len(labels):
            raise ParseError(f"ATR1 block has unexpected number of entries")

        attribute_size = atr1_stream.u32()

        self.messages = {}
        for label, index in sorted(labels.items(), key=lambda x: x[1]):
            attributes = atr1_stream.read(attribute_size)
            style = styles[index] if styles is not None else None

            message = Message(contents[index], attributes, style)
            self.messages[label] = message

    def _parse_styles(self, data: bytes) -> list[int]:
        if len(data) % 4:
            raise ParseError("TSY1 section size must be a multiple of 4")
        
        stream = StreamIn(data, self.endianness)
        return stream.repeat(stream.s32, stream.size() // 4)

    def _parse_contents(self, data: bytes) -> list[list[str | Tag]]:
        stream = StreamIn(data, self.endianness)

        contents = []
        offsets = stream.repeat(stream.u32, stream.u32())
        for offset in offsets:
            stream.seek(offset)
            contents.append(self._parse_text(stream))
        return contents

    def _parse_text(self, stream: StreamIn) -> list[str | Tag]:
        if self.encoding == common.Encoding.UTF8: func = stream.u8
        if self.encoding == common.Encoding.UTF16: func = stream.u16
        else:
            func = stream.u32
            
        content = []
        text = ""
        while True:
            char = func()

            if char in [0, 14] and text:
                content.append(text)
                text = ""

            if char == 0:
                return content
            elif char == 14:
                group_id = stream.u16()
                tag_id = stream.u16()
                parameters = stream.read(stream.u16())
                tag = Tag(group_id, tag_id, parameters)
                content.append(tag)
            else:
                text += chr(char)

    def save(self) -> bytes:
        if self.version != 3:
            raise SaveError("unsupported version number")
        
        file = common.MessageFile()
        file.magic = "MsgStdBn"
        file.endianness = self.endianness
        file.encoding = self.encoding
        file.version = self.version
        file.blocks = {}

        labels = {name: index for index, name in enumerate(self.messages)}
        file.blocks["LBL1"] = file.save_labels(labels, self.buckets)

        file.blocks["ATR1"] = self._save_attributes()

        styles = [message.style for message in self.messages.values()]
        if any(style is not None for style in styles):
            file.blocks["TSY1"] = self._save_styles()
        
        file.blocks["TXT2"] = self._save_messages()
        return file.save()

    def _save_attributes(self) -> bytes:
        attribute_size = 0
        if self.messages:
            message = list(self.messages.values())[0]
            attribute_size = len(message.attributes)

        stream = StreamOut(self.endianness)
        stream.u32(len(self.messages))
        stream.u32(attribute_size)
        for message in self.messages.values():
            stream.write(message.attributes)
        return stream.get()

    def _save_styles(self) -> bytes:
        stream = StreamOut(self.endianness)
        for message in self.messages.values():
            if message.style is None:
                raise SaveError("styles must either all be None or not None")
            stream.s32(message.style)
        return stream.get()

    def _save_messages(self) -> bytes:
        stream = StreamOut(self.endianness)
        stream.u32(len(self.messages))

        message_stream = StreamOut(self.endianness)
        for message in self.messages.values():
            stream.u32(4 + 4 * len(self.messages) + message_stream.size())
            self._save_content(message.content, message_stream)
        stream.write(message_stream.get())
        return stream.get()

    def _save_content(
        self, content: list[str | Tag], stream: StreamOut
    ) -> None:
        if self.encoding == common.Encoding.UTF8: func = stream.u8
        if self.encoding == common.Encoding.UTF16: func = stream.u16
        else:
            func = stream.u32
        
        for component in content:
            if isinstance(component, str):
                for char in component:
                    func(ord(char))
            else:
                func(14)
                stream.u16(component.group)
                stream.u16(component.tag)
                stream.u16(len(component.parameters))
                stream.write(component.parameters)

        func(0)
