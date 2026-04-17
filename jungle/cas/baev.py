
from dataclasses import dataclass, field
from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut
import enum


CLASS_NAME = "Nintendo.AnimationEvent.ResourceConverter.Resource." \
    "AnimationEventArchiveResData"


class ParameterType(enum.IntEnum):
    Integer = 0
    Float = 1
    Vec3 = 3
    String = 5


ParameterSizes = {
    ParameterType.Integer: 4,
    ParameterType.Float: 4,
    ParameterType.Vec3: 12,
    ParameterType.String: 8
}


class BAEVSection:
    def __init__(self, data: bytes, alignment: int):
        self.data = data
        self.alignment = alignment


@dataclass
class BAEVParameter:
    type: ParameterType = ParameterType.Integer
    value: int | float | list[float] | str = 0

    def size(self) -> int:
        return ParameterSizes[self.type]


@dataclass
class BAEVTrigger:
    parameters: list[BAEVParameter] = field(default_factory=list)
    start_frame: float = 0
    end_frame: float = 0


@dataclass
class BAEVAnimation:
    name: str = ""
    trigger: list[BAEVTrigger] = field(default_factory=list)
    hold: list[BAEVTrigger] = field(default_factory=list)
    unk1: int = 0
    unk2: int = 0


@dataclass
class BAEVAction:
    name_hash: int = 0
    unk: int = 0
    animations: list[BAEVAnimation] = field(default_factory=list)


class BAEVFile:
    events: dict[int, list[int]]
    actions: list[BAEVAction]

    def __init__(self):
        self.events = {}
        self.actions = []

    def parse(self, data: bytes) -> None:
        stream = StreamIn(data, "<")
        
        if stream.ascii(4) != "BFFH":
            raise ParseError("magic number is invalid")
        stream.pad(4)
        if stream.u32() != stream.size():
            raise ParseError("file size is invalid")
        if stream.u32() != 8:
            raise ParseError("alignment is invalid")
        
        section_header_offset = stream.u64()
        section_header_count = stream.u32()
        section_header_size = stream.u32()
        if section_header_size != 0x28:
            raise ParseError("section header size is invalid")

        stream.skip(8) # data section pointer

        if stream.ascii(128).rstrip("\0") != CLASS_NAME:
            raise ParseError("class name is invalid")

        sections: dict[str, BAEVSection] = {}

        stream.seek(section_header_offset)
        for i in range(section_header_count):
            if stream.ascii(4) != "BFSI":
                raise ParseError("section header magic number is invalid")
            
            offset = stream.u32()
            size = stream.u32()
            alignment = stream.u32()
            pointer = stream.u64()

            if offset != pointer:
                raise ParseError("offset / pointer mismatch in section header")
            
            name = stream.ascii(16).rstrip("\0")
            data = stream.read_at(offset, size)

            sections[name] = BAEVSection(data, alignment)
        
        if "Default" not in sections:
            raise ParseError("default section is missing")
        
        substream = StreamIn(sections["Default"].data, "<")
        substream.pad(8)
        if substream.u8() != 0: raise ParseError("unsupported micro version")
        if substream.u8() != 1: raise ParseError("unsupported minor version")
        if substream.u16() != 2: raise ParseError("unsupported major version")
        substream.pad(4)
        substream.skip(8) # string pool pointer

        event_offset = substream.u64()
        event_count = substream.u32()
        event_size = substream.u32()
        if event_size != 0x18:
            raise ParseError("event size is invalid")
        
        action_offset = substream.u64()
        action_count = substream.u32()
        action_size = substream.u32()
        if action_size != 0x18:
            raise ParseError("action size is invalid")
        
        self.events = {}
        
        stream.seek(event_offset)
        for i in range(event_count):
            name_hash = stream.u32()
            stream.pad(4)

            index_offset = stream.u64()
            index_count = stream.u32()
            index_size = stream.u32()
            if index_size != 4:
                raise ParseError("index size is invalid")
            
            with stream.jump(index_offset):
                indices = stream.repeat(stream.u32, index_count)
            
            self.events[name_hash] = indices
        
        self.actions = []

        stream.seek(action_offset)
        for i in range(action_count):
            self.actions.append(self._parse_action(stream))
    
    def _parse_action(self, stream: StreamIn) -> BAEVAction:
        animation_offset = stream.u64()
        animation_count = stream.u32()
        animation_size = stream.u32()
        if animation_size != 0x30:
            raise ParseError("invalid animation size")
        
        animations = []
        with stream.jump(animation_offset):
            for i in range(animation_count):
                animations.append(self._parse_animation(stream))
        
        action = BAEVAction()
        action.name_hash = stream.u32()
        action.unk = stream.u32()
        action.animations = animations
        return action
    
    def _parse_animation(self, stream: StreamIn) -> BAEVAnimation:
        animation = BAEVAnimation()
        animation.name = stream.string_at(stream.u64())

        trigger_offset = stream.u64()
        trigger_count = stream.u32()
        trigger_size = stream.u32()
        if trigger_count and trigger_size != 0x18:
            raise ValueError("invalid trigger size")
        
        hold_offset = stream.u64()
        hold_count = stream.u32()
        hold_size = stream.u32()
        if hold_size != 0x18:
            raise ValueError("invalid hold size")
        
        animation.unk1 = stream.u32()
        animation.unk2 = stream.u32()

        triggers = []
        with stream.jump(trigger_offset):
            for i in range(trigger_count):
                triggers.append(self._parse_trigger(stream))
        
        hold = []
        with stream.jump(hold_offset):
            for i in range(hold_count):
                hold.append(self._parse_trigger(stream))
        
        animation.trigger = triggers
        animation.hold = hold

        return animation
    
    def _parse_trigger(self, stream: StreamIn) -> BAEVTrigger:
        param_offset = stream.u64()
        param_count = stream.u32()
        param_size = stream.u32()
        if param_size != 8:
            raise ParseError("invalid parameter pointer size")
        
        parameters = []
        with stream.jump(param_offset):
            pointers = stream.repeat(stream.u64, param_count)
            for pointer in pointers:
                stream.seek(pointer)
                parameters.append(self._parse_parameter(stream))
        
        trigger = BAEVTrigger()
        trigger.parameters = parameters
        trigger.start_frame = stream.float()
        trigger.end_frame = stream.float()
        return trigger
    
    def _parse_parameter(self, stream: StreamIn) -> BAEVParameter:
        type = stream.u32()
        stream.pad(4)

        if type == ParameterType.Integer: value = stream.u32()
        elif type == ParameterType.Float: value = stream.float()
        elif type == ParameterType.Vec3: value = stream.repeat(stream.float, 3)
        elif type == ParameterType.String: value = stream.string_at(stream.u64())
        else:
            raise ParameterType(f"unsupported parameter type: {type}")

        parameter = BAEVParameter()
        parameter.type = type
        parameter.value = value
        return parameter
    
    def save(self) -> bytes:
        default_size = self._calculate_default_size()

        strings = self._collect_strings()
        string_table_offset = 0xF8 + default_size
        string_offsets = {}
        string_table = b""
        for string in strings:
            string_offsets[string] = string_table_offset + len(string_table)
            string_table += string.encode() + b"\0"

        file_size = string_table_offset + len(string_table)

        stream = StreamOut("<")
        stream.ascii("BFFH")
        stream.pad(4)
        stream.u32(file_size)
        stream.u32(8) # alignment

        stream.u64(0xA8) # section header offset
        stream.u32(2) # section header count
        stream.u32(0x28) # section header size

        stream.u64(0xF8)
        stream.ascii(CLASS_NAME.ljust(128, "\0"))

        # Encode default section header
        stream.ascii("BFSI")
        stream.u32(0xF8)
        stream.u32(default_size)
        stream.u32(8) # alignment
        stream.u64(0xF8)
        stream.ascii("Default".ljust(16, "\0"))

        # Encode string pool section header
        stream.ascii("BFSI")
        stream.u32(string_table_offset)
        stream.u32(len(string_table))
        stream.u32(1) # alignment
        stream.u64(string_table_offset)
        stream.ascii("StringPool".ljust(16, "\0"))

        # Encode default section
        index_table_offset = 0x130 + len(self.events) * 0x18
        action_table_offset = index_table_offset + len(self.actions) * 4
        action_table_offset += -action_table_offset % 8

        stream.pad(8) # file header pointer
        stream.u8(0) # micro version
        stream.u8(1) # minor version
        stream.u16(2) # major version
        stream.pad(4)
        stream.u64(string_table_offset)
        stream.u64(0x130)
        stream.u32(len(self.events))
        stream.u32(0x18)
        stream.u64(action_table_offset)
        stream.u32(len(self.actions))
        stream.u32(0x18)

        all_indices = []
        for hash, indices in self.events.items():
            stream.u32(hash)
            stream.pad(4)
            stream.u64(index_table_offset + len(all_indices) * 4)
            stream.u32(len(indices))
            stream.u32(4)
            all_indices += indices
        
        stream.repeat(all_indices, stream.u32)
        stream.align(8)

        animation_table_offset = action_table_offset + len(self.actions) * 0x18
        for action in self.actions:
            stream.u64(animation_table_offset)
            stream.u32(len(action.animations))
            stream.u32(0x30)
            stream.u32(action.name_hash)
            stream.u32(action.unk)
            
            with stream.jump(animation_table_offset):
                animation_table_offset = self._save_animation_table(
                    stream, action.animations, string_offsets
                )

        # Write string table
        stream.seek(string_table_offset)
        stream.write(string_table)
        
        return stream.get()
    
    def _save_animation_table(
        self, stream: StreamOut, animations: list[BAEVAnimation],
        string_offsets: dict[str, int]
    ) -> int:
        trigger_offset = stream.tell() + len(animations) * 0x30
        for animation in animations:
            stream.u64(string_offsets[animation.name])

            trigger_pointer = stream.reserve(8)
            stream.u32(len(animation.trigger))
            stream.u32(0x18 if animation.trigger else 0)

            hold_pointer = stream.reserve(8)
            stream.u32(len(animation.hold))
            stream.u32(0x18 if animation.hold else 0)
            
            stream.u32(animation.unk1)
            stream.u32(animation.unk2)

            if animation.trigger:
                stream.u64_at(trigger_pointer, trigger_offset)
            
            with stream.jump(trigger_offset):
                trigger_offset = self._save_trigger_table(
                    stream, animation.trigger, string_offsets
                )
            
            if animation.hold:
                stream.u64_at(hold_pointer, trigger_offset)
            
            with stream.jump(trigger_offset):
                trigger_offset = self._save_trigger_table(
                    stream, animation.hold, string_offsets
                )
            
        return trigger_offset
    
    def _save_trigger_table(
        self, stream: StreamOut, triggers: list[BAEVTrigger],
        string_offsets: dict[str, int]
    ) -> int:
        parameter_offset = stream.tell() + len(triggers) * 0x18
        for trigger in triggers:
            stream.u64(parameter_offset)
            stream.u32(len(trigger.parameters))
            stream.u32(8)
            stream.float(trigger.start_frame)
            stream.float(trigger.end_frame)

            with stream.jump(parameter_offset):
                value_offset = parameter_offset + 8 * len(trigger.parameters)
                for parameter in trigger.parameters:
                    stream.u64(value_offset)
                    with stream.jump(value_offset):
                        value_offset = self._save_parameter(
                            stream, parameter, string_offsets
                        )
                parameter_offset = value_offset
        return parameter_offset
    
    def _save_parameter(
        self, stream: StreamOut, parameter: BAEVParameter,
        string_offsets: dict[str, int]
    ) -> int:
        stream.u32(parameter.type)
        stream.pad(4)

        if parameter.type == ParameterType.Integer:
            stream.u32(parameter.value)
        elif parameter.type == ParameterType.Float:
            stream.float(parameter.value)
        elif parameter.type == ParameterType.Vec3:
            stream.repeat(parameter.value, stream.float)
        elif parameter.type == ParameterType.String:
            stream.u64(string_offsets[parameter.value])
        stream.align(8)
        return stream.tell()
    
    def _calculate_default_size(self) -> int:
        size = 0x38
        size += 0x18 * len(self.events) + 4 * len(self.actions)
        size += -size % 8

        for action in self.actions:
            size += 0x18
            for animation in action.animations:
                size += 0x30
                for trigger in animation.trigger + animation.hold:
                    size += 0x18 + 8 * len(trigger.parameters)
                    for parameter in trigger.parameters:
                        size += 8 + parameter.size()
                        size += -size % 8
        return size
    
    def _collect_strings(self) -> list[str]:
        strings = [""]

        for action in self.actions:
            for animation in action.animations:
                if animation.name not in strings:
                    strings.append(animation.name)
                
                for trigger in animation.trigger + animation.hold:
                    for parameter in trigger.parameters:
                        if isinstance(parameter.value, str):
                            if parameter.value not in strings:
                                strings.append(parameter.value)
    
        return sorted(strings)
