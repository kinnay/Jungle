
"""Implements the MSBP file format."""

from dataclasses import dataclass, field

from jungle.errors import ParseError, SaveError
from jungle.lms import common
from jungle.streams import StreamIn, StreamOut

import enum


class ValueType(enum.IntEnum):
    Int8 = 0
    Uint8 = 1
    Int16 = 2
    Uint16 = 3
    Int32 = 4
    Uint32 = 5
    Float = 6
    Double = 7
    String = 8
    Enum = 9


@dataclass
class Attribute:
    type: ValueType = ValueType.Int8
    offset: int = 0
    labels: list[str] = field(default_factory=list)


@dataclass
class Parameter:
    name: str = ""
    type: ValueType = ValueType.Int8
    labels: list[str] = field(default_factory=list)


@dataclass
class Tag:
    name: str = ""
    parameters: list[Parameter] = field(default_factory=list)


@dataclass
class TagGroup:
    name: str = ""
    tags: list[Tag] = field(default_factory=list)


@dataclass
class Style:
    region_width: int = 0
    line_num: int = 0
    font_index: int = 0
    base_color_index: int = 0


class MSBPFile:
    endianness: str
    encoding: common.Encoding
    version: int

    colors: dict[str, tuple[int, int, int, int]] | None
    attributes: dict[str, Attribute] | None
    tag_groups: dict[int, TagGroup] | None
    styles: dict[str, Style] | None
    filenames: list[str] | None

    def __init__(self):
        self.endianness = "<"
        self.encoding = common.Encoding.UTF8
        self.version = 3

        self.colors = None
        self.attributes = None
        self.tag_groups = None
        self.styles = None
        self.filenames = None

    def parse(self, data: bytes) -> None:
        # Parse header and blocks
        file = common.MessageFile()
        file.parse(data)

        # Verify magic number
        if file.magic != "MsgPrjBn":
            raise ParseError("magic number is invalid")

        # Read header info
        self.endianness = file.endianness
        self.encoding = file.encoding
        self.version = file.version
        if self.version not in [3, 4]:
            raise ParseError("unsupported version number")
        
        # Verify blocks
        supported_blocks = [
            "CLR1", "CLB1", "ATI2", "ALB1", "ALI2",
            "TGG2", "TAG2", "TGP2", "TGL2", "SYL3",
            "SLB1", "CTI1"
        ]
        for type in file.blocks:
            if type not in supported_blocks:
                raise ParseError(f"unsupported block: {type}")

        # Parse blocks
        self.colors = None
        if "CLR1" in file.blocks:
            colors = self.parse_colors(file.blocks["CLR1"])
            if colors:
                if "CLB1" not in file.blocks:
                    raise ParseError("CLB1 block is missing")
                
                labels = file.parse_labels(file.blocks["CLB1"])
                self.colors = {
                    label: colors[index] for label, index in \
                        sorted(labels.items(), key=lambda x: x[1])
                }
            else:
                self.colors = {}
        
        self.attributes = None
        if "ATI2" in file.blocks:
            if "ALI2" not in file.blocks:
                raise ParseError("ALI2 block is missing")
            enums = self.parse_attribute_enums(file.blocks["ALI2"])
            attributes = self.parse_attributes(file.blocks["ATI2"], enums)
            labels = file.parse_labels(file.blocks["ALB1"])
            self.attributes = {
                label: attributes[index] for label, index in \
                    sorted(labels.items(), key=lambda x: x[1])
            }
        
        self.tag_groups = None
        if "TGG2" in file.blocks:
            for name in ["TGL2", "TGP2", "TAG2"]:
                if name not in file.blocks:
                    raise ParseError(f"{name} block is missing")
            strings = self.parse_tag_strings(file.blocks["TGL2"])
            parameters = self.parse_tag_parameters(file.blocks["TGP2"], strings)
            tags = self.parse_tags(file.blocks["TAG2"], parameters)
            self.tag_groups = self.parse_tag_groups(file.blocks["TGG2"], tags)
        
        self.styles = None
        if "SYL3" in file.blocks:
            if "SLB1" not in file.blocks:
                raise ParseError("SLB1 block is missing")
            styles = self.parse_styles(file.blocks["SYL3"])
            labels = file.parse_labels(file.blocks["SLB1"])
            self.styles = {
                label: styles[index] for label, index in \
                    sorted(labels.items(), key=lambda x: x[1])
            }
        
        self.filenames = None
        if "CTI1" in file.blocks:
            stream = StreamIn(file.blocks["CTI1"], self.endianness)
            offsets = stream.repeat(stream.u32, stream.u32())
            self.filenames = [stream.string_at(offset) for offset in offsets]
    
    def parse_colors(self, data: bytes) -> list[tuple[int, int, int, int]]:
        stream = StreamIn(data, self.endianness)

        colors = []
        for i in range(stream.u32()):
            colors.append((stream.u8(), stream.u8(), stream.u8(), stream.u8()))
        return colors
    
    def parse_attributes(
        self, data: bytes, enums: list[list[str]]
    ) -> list[Attribute]:
        stream = StreamIn(data, self.endianness)

        attributes = []
        for i in range(stream.u32()):
            type = stream.u8()
            stream.pad(1)
            enum_id = stream.u16()
            offset = stream.u32()

            if type not in ValueType:
                raise ParseError(f"unsupported attribute type: {type}")

            attribute = Attribute()
            attribute.type = ValueType(type)
            attribute.offset = offset
            if type == ValueType.Enum:
                attribute.labels = enums[enum_id]
            attributes.append(attribute)
        return attributes
    
    def parse_attribute_enums(self, data: bytes) -> list[list[str]]:
        stream = StreamIn(data, self.endianness)

        lists = []
        offsets = stream.repeat(stream.u32, stream.u32())
        for offset in offsets:
            stream.seek(offset)
            lists.append(self.parse_attribute_enum(stream))
        return lists
    
    def parse_attribute_enum(self, stream: StreamIn) -> list[str]:
        base = stream.tell()
        offsets = stream.repeat(stream.u32, stream.u32())
        return [stream.string_at(base + offset) for offset in offsets]
    
    def parse_tag_groups(
        self, data: bytes, tags: list[Tag]
    ) -> dict[int, TagGroup]:
        stream = StreamIn(data, self.endianness)

        count = stream.u16()
        stream.pad(2)
        offsets = stream.repeat(stream.u32, count)

        groups = {}
        for id, offset in enumerate(offsets):
            stream.seek(offset)

            if self.version == 4:
                id = stream.u16()
            
            indices = stream.repeat(stream.u16, stream.u16())

            group = TagGroup()
            group.tags = [tags[index] for index in indices]
            group.name = stream.string()

            groups[id] = group
        return groups

    def parse_tags(self, data: bytes, parameters: list[Parameter]) -> list[Tag]:
        stream = StreamIn(data, self.endianness)

        count = stream.u16()
        stream.pad(2)
        offsets = stream.repeat(stream.u32, count)

        tags = []
        for offset in offsets:
            stream.seek(offset)
            indices = stream.repeat(stream.u16, stream.u16())

            tag = Tag()
            tag.name = stream.string()
            tag.parameters = [parameters[index] for index in indices]
            tags.append(tag)
        return tags

    def parse_tag_parameters(
        self, data: bytes, strings: list[str]
    ) -> list[Parameter]:
        stream = StreamIn(data, self.endianness)

        count = stream.u16()
        stream.pad(2)
        offsets = stream.repeat(stream.u32, count)

        parameters = []
        for offset in offsets:
            stream.seek(offset)

            type = stream.u8()
            if type not in ValueType:
                raise ParseError(f"unsupported parameter type: {type}")

            parameter = Parameter()
            parameter.type = ValueType(type)
            if parameter.type == ValueType.Enum:
                stream.pad(1)
                indices = stream.repeat(stream.u16, stream.u16())
                parameter.labels = [strings[index] for index in indices]
            parameter.name = stream.string()
            parameters.append(parameter)
        return parameters
    
    def parse_tag_strings(self, data: bytes) -> list[str]:
        stream = StreamIn(data, self.endianness)

        count = stream.u16()
        stream.pad(2)
        offsets = stream.repeat(stream.u32, count)

        return [stream.string_at(offset) for offset in offsets]

    def parse_styles(self, data: bytes) -> list[Style]:
        stream = StreamIn(data, self.endianness)

        styles = []
        for i in range(stream.u32()):
            style = Style()
            style.region_width = stream.u32()
            style.line_num = stream.u32()
            style.font_index = stream.u32()
            style.base_color_index = stream.s32()
            styles.append(style)
        return styles

    def save(self) -> bytes:
        if self.version not in [3, 4]:
            raise SaveError("unsupported version number")
        
        file = common.MessageFile()
        file.magic = "MsgPrjBn"
        file.endianness = self.endianness
        file.encoding = self.encoding
        file.version = self.version
        file.blocks = {}

        if self.colors is not None:
            labels = {name: index for index, name in enumerate(self.colors)}
            file.blocks["CLR1"] = self.save_colors()
            if self.colors:
                file.blocks["CLB1"] = file.save_labels(labels, 29)
        
        if self.attributes is not None:
            labels = {name: index for index, name in enumerate(self.attributes)}
            file.blocks["ATI2"] = self.save_attributes()
            file.blocks["ALB1"] = file.save_labels(labels, 29)
            file.blocks["ALI2"] = self.save_attribute_enums()
        
        if self.tag_groups is not None:
            file.blocks["TGG2"] = self.save_tag_groups()
            file.blocks["TAG2"] = self.save_tags()
            file.blocks["TGP2"] = self.save_tag_parameters()
            file.blocks["TGL2"] = self.save_tag_strings()
        
        if self.styles is not None:
            labels = {name: index for index, name in enumerate(self.styles)}
            file.blocks["SYL3"] = self.save_styles()
            file.blocks["SLB1"] = file.save_labels(labels, 29)
        
        if self.filenames is not None:
            file.blocks["CTI1"] = self.save_filenames()

        return file.save()
    
    def save_colors(self) -> bytes:
        assert self.colors is not None

        colors = list(self.colors.values())

        stream = StreamOut(self.endianness)
        stream.u32(len(colors))
        for color in colors:
            stream.repeat(color, stream.u8)
        return stream.get()

    def save_attributes(self) -> bytes:
        assert self.attributes is not None

        stream = StreamOut(self.endianness)
        stream.u32(len(self.attributes))

        index = 0
        for attribute in self.attributes.values():
            stream.u8(attribute.type)
            stream.pad(1)
            if attribute.type == ValueType.Enum:
                stream.u16(index)
                index += 1
            else:
                stream.u16(0)
            stream.u32(attribute.offset)
        return stream.get()

    def save_attribute_enums(self) -> bytes:
        assert self.attributes is not None

        enums = []
        for attribute in self.attributes.values():
            if attribute.type == ValueType.Enum:
                enums.append(attribute.labels)

        stream = StreamOut(self.endianness)
        stream.u32(len(enums))

        offset = 4 + 4 * len(enums)
        for enum in enums:
            stream.u32(offset)
            offset += 4 + 4 * len(enum)
            for label in enum:
                offset += len(label) + 1
            offset = (offset + 3) & ~3
        
        for enum in enums:
            stream.u32(len(enum))
            offset = 4 + 4 * len(enum)
            for label in enum:
                stream.u32(offset)
                offset += len(label) + 1
            for label in enum:
                stream.string(label)
            stream.align(4)
        
        return stream.get()

    def save_tag_groups(self) -> bytes:
        assert self.tag_groups is not None

        stream = StreamOut(self.endianness)
        stream.u16(len(self.tag_groups))
        stream.pad(2)

        offset = 4 + 4 * len(self.tag_groups)
        for group in self.tag_groups.values():
            stream.u32(offset)
            offset += 2 + 2 * len(group.tags)
            offset += len(group.name) + 1
            if self.version == 4:
                offset += 2
            offset = (offset + 3) & ~3
        
        index = 0
        for id, group in self.tag_groups.items():
            if self.version == 4:
                stream.u16(id)
            stream.u16(len(group.tags))
            for i in range(len(group.tags)):
                stream.u16(index)
                index += 1
            stream.string(group.name)
            stream.align(4)
        return stream.get()

    def save_tags(self) -> bytes:
        assert self.tag_groups is not None

        tags = []
        for group in self.tag_groups.values():
            tags += group.tags
        
        stream = StreamOut(self.endianness)
        stream.u16(len(tags))
        stream.pad(2)

        offset = 4 + 4 * len(tags)
        for tag in tags:
            stream.u32(offset)
            offset += 2 + 2 * len(tag.parameters)
            offset += len(tag.name) + 1
            offset = (offset + 3) & ~3
        
        index = 0
        for tag in tags:
            stream.u16(len(tag.parameters))
            for i in range(len(tag.parameters)):
                stream.u16(index)
                index += 1
            stream.string(tag.name)
            stream.align(4)
        return stream.get()
    
    def save_tag_parameters(self) -> bytes:
        assert self.tag_groups is not None

        parameters = []
        for group in self.tag_groups.values():
            for tag in group.tags:
                parameters += tag.parameters
        
        stream = StreamOut(self.endianness)
        stream.u16(len(parameters))
        stream.pad(2)

        offset = 4 + 4 * len(parameters)
        for parameter in parameters:
            stream.u32(offset)
            offset += 2 + len(parameter.name)
            if parameter.type == ValueType.Enum:
                offset += 3 + 2 * len(parameter.labels)
            offset = (offset + 3) & ~3
        
        index = 0
        for parameter in parameters:
            stream.u8(parameter.type)
            if parameter.type == ValueType.Enum:
                stream.pad(1)
                stream.u16(len(parameter.labels))
                for label in parameter.labels:
                    stream.u16(index)
                    index += 1
            stream.string(parameter.name)
            stream.align(4)
        return stream.get()

    def save_tag_strings(self) -> bytes:
        assert self.tag_groups is not None

        strings = []
        for group in self.tag_groups.values():
            for tag in group.tags:
                for parameter in tag.parameters:
                    if parameter.type == ValueType.Enum:
                        strings += parameter.labels

        stream = StreamOut(self.endianness)
        stream.u16(len(strings))
        stream.pad(2)

        offset = 4 + 4 * len(strings)
        for string in strings:
            stream.u32(offset)
            offset += len(string) + 1
        
        for string in strings:
            stream.string(string)
        return stream.get()

    def save_styles(self) -> bytes:
        assert self.styles is not None

        stream = StreamOut(self.endianness)
        stream.u32(len(self.styles))
        for style in self.styles.values():
            stream.u32(style.region_width)
            stream.u32(style.line_num)
            stream.u32(style.font_index)
            stream.s32(style.base_color_index)
        return stream.get()

    def save_filenames(self) -> bytes:
        assert self.filenames is not None
        
        stream = StreamOut(self.endianness)
        stream.u32(len(self.filenames))

        offset = 4 + 4 * len(self.filenames)
        for filename in self.filenames:
            stream.u32(offset)
            offset += len(filename) + 1
        
        for filename in self.filenames:
            stream.string(filename)
        return stream.get()
