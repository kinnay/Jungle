
from jungle.errors import ParseError, SaveError
from jungle import streams

import struct


class Resource:
    def __init__(self):
        self.name = ""
        self.unk = [0, 0, 0, 0]
        self.sounds = []
        self.actions = []


class CallTable:
    def __init__(self):
        self.name = ""
        self.unk = 0
        self.select_by_properties = False
        self.select_randomly = False
        self.items = []


class Sound:
    def __init__(self):
        self.index = 0
        self.property_name1 = ""
        self.property_id1 = 0
        self.property_name2 = ""
        self.property_id2 = 0
        self.item_name = ""
        self.filename = ""
        self.min_volume = 0
        self.max_volume = 0
        self.min_pitch = 0
        self.max_pitch = 0
        self.min_lpf = 0
        self.max_lpf = 0
        self.min_pan = 0
        self.max_pan = 0
        self.min_surround_pan = 0
        self.max_surround_pan = 0
        self.min_delay = 0
        self.max_delay = 0
        self.bone_name = ""
        self.is_hold = False
        self.is_follow = False
        self.use_property_ids = False


class Action:
    def __init__(self):
        self.index = 0
        self.sound_index = 0
        self.unk1 = 0
        self.unk2 = 0
        self.flags = 0
        self.unk3 = 0
        self.min_volume = 0
        self.max_volume = 0
        self.min_pitch = 0
        self.max_pitch = 0
        self.min_lpf = 0
        self.max_lpf = 0
        self.min_pan = 0
        self.max_pan = 0
        self.min_surround_pan = 0
        self.max_surround_pan = 0
        self.min_delay = 0
        self.max_delay = 0


class SLINKFile:
    def __init__(self):
        self.version = 0x45
        self.resources = []
        self.unused_strings = []
    
    def parse(self, data):
        stream = streams.StreamIn(data, ">")
        if stream.ascii(4) != "SLNK": raise ParseError("magic number is invalid")
        if stream.u32() != len(data): raise ParseError("file size is invalid")
        if stream.u32() != 0x45: raise ParseError("unsupported version number")

        offsets = stream.repeat(stream.u32, stream.u32())
        string_table = stream.tell()

        self.resources = []
        for offset in offsets:
            stream.seek(offset)
            self.resources.append(self.parse_resource(stream, string_table))
        
        strings = self.find_strings()

        stream.seek(string_table)
        string_table_end = offsets[0] if offsets else stream.size()

        self.unused_strings = []
        while stream.tell() < string_table_end:
            string = stream.string("shift-jis")
            if string and string not in strings:
                self.unused_strings.append(string)
    
    def parse_resource(self, stream, string_table):
        stream.skip(8)

        resource = Resource()
        resource.name = stream.string_at(string_table + stream.u32(), "shift-jis")
        
        num_sound_call_tables = stream.u32()
        num_action_call_tables = stream.u32()
        num_sounds = stream.u32()
        num_actions = stream.u32()
        stream.skip(4)

        resource.unk = stream.repeat(stream.float, 4)

        sounds = []
        actions = []

        stream.push()
        stream.skip((num_sound_call_tables + num_action_call_tables) * 0x14)
        for i in range(num_sounds):
            sounds.append(self.parse_sound(stream, string_table))
        for i in range(num_actions):
            actions.append(self.parse_action(stream))
        stream.pop()

        for i in range(num_sound_call_tables):
            call_table = self.parse_call_table(stream, string_table, sounds)
            resource.sounds.append(call_table)
        
        for i in range(num_action_call_tables):
            call_table = self.parse_call_table(stream, string_table, actions)
            resource.actions.append(call_table)
        return resource
    
    def parse_call_table(self, stream, string_table, items):
        call_table = CallTable()
        call_table.name = stream.string_at(string_table + stream.u32())
        stream.pad(8)
        call_table.unk = stream.u8()
        call_table.select_by_properties = stream.bool()
        call_table.select_randomly = stream.bool()
        stream.pad(1)
        call_table.items = items[stream.u16():stream.u16()+1]
        return call_table
        
    def parse_sound(self, stream, string_table):
        sound = Sound()
        sound.index = stream.u32()
        stream.pad(4)
        sound.property_name1 = stream.string_at(string_table + stream.u32())
        sound.property_id1 = stream.u32()
        sound.property_name2 = stream.string_at(string_table + stream.u32())
        sound.property_id2 = stream.u32()
        sound.item_name = stream.string_at(string_table + stream.u32())
        stream.pad(4)
        sound.filename = stream.string_at(string_table + stream.u32())
        stream.pad(4)
        sound.min_volume = stream.float()
        sound.max_volume = stream.float()
        sound.min_pitch = stream.float()
        sound.max_pitch = stream.float()
        sound.min_lpf = stream.float()
        sound.max_lpf = stream.float()
        sound.min_pan = stream.float()
        sound.max_pan = stream.float()
        sound.min_surround_pan = stream.float()
        sound.max_surround_pan = stream.float()
        sound.min_delay = stream.u16()
        sound.max_delay = stream.u16()
        sound.bone_name = stream.string_at(string_table + stream.u32())
        sound.is_hold = stream.bool()
        sound.is_follow = stream.bool()
        sound.use_property_ids = stream.bool()
        stream.pad(1)
        return sound

    def parse_action(self, stream):
        action = Action()
        action.index = stream.u32()
        stream.pad(4)
        action.sound_index = stream.u32()
        stream.pad(4)
        action.unk1 = stream.u32()
        action.unk2 = stream.u32()
        action.flags = stream.u16()
        action.unk3 = stream.u16()
        action.min_volume = stream.float()
        action.max_volume = stream.float()
        action.min_pitch = stream.float()
        action.max_pitch = stream.float()
        action.min_lpf = stream.float()
        action.max_lpf = stream.float()
        action.min_pan = stream.float()
        action.max_pan = stream.float()
        action.min_surround_pan = stream.float()
        action.max_surround_pan = stream.float()
        action.min_delay = stream.u16()
        action.max_delay = stream.u16()
        stream.pad(4)
        return action
    
    def save(self):
        if self.version != 0x45:
            raise SaveError("unsupported version number")
        
        strings = self.find_strings()
        for string in self.unused_strings:
            strings.add(string)
        
        string_table = {}
        string_data = b""
        for string in sorted(strings):
            string_table[string] = len(string_data)
            string_data += string.encode("shift-jis") + b"\0"
        string_data += bytes((4 - len(string_data) % 4) % 4)

        offsets = []
        offset = 0x10 + 4 * len(self.resources) + len(string_data)
        for resource in self.resources:
            offsets.append(offset)
            offset += self.calc_resource_size(resource)

        stream = streams.StreamOut(">")
        stream.ascii("SLNK")
        stream.u32(offset)
        stream.u32(self.version)
        stream.u32(len(self.resources))
        stream.repeat(offsets, stream.u32)
        stream.write(string_data)
        for resource in self.resources:
            self.save_resource(stream, resource, string_table)
        return stream.get()
    
    def save_resource(self, stream, resource, string_table):
        size = self.calc_resource_size(resource)
        stream.u32(1)
        stream.u32(size)
        stream.u32(string_table[resource.name])
        stream.u32(len(resource.sounds))
        stream.u32(len(resource.actions))
        stream.u32(sum(len(sound.items) for sound in resource.sounds))
        stream.u32(sum(len(action.items) for action in resource.actions))
        stream.u32(size - 4)
        stream.repeat(resource.unk, stream.float)
        self.save_call_tables(stream, resource.sounds, string_table)
        self.save_call_tables(stream, resource.actions, string_table)
        for sound in resource.sounds:
            for item in sound.items:
                self.save_sound(stream, item, string_table)
        for action in resource.actions:
            for item in action.items:
                self.save_action(stream, item)
        stream.pad(4)
    
    def save_call_tables(self, stream, call_tables, string_table):
        index = 0
        for call_table in call_tables:
            stream.u32(string_table[call_table.name])
            stream.pad(8)
            stream.u8(call_table.unk)
            stream.bool(call_table.select_by_properties)
            stream.bool(call_table.select_randomly)
            stream.pad(1)
            stream.u16(index)
            stream.u16(index + len(call_table.items) - 1)
            index += len(call_table.items)
    
    def save_sound(self, stream, sound, string_table):
        stream.u32(sound.index)
        stream.pad(4)
        stream.u32(string_table[sound.property_name1])
        stream.u32(sound.property_id1)
        stream.u32(string_table[sound.property_name2])
        stream.u32(sound.property_id2)
        stream.u32(string_table[sound.item_name])
        stream.pad(4)
        stream.u32(string_table[sound.filename])
        stream.pad(4)
        stream.float(sound.min_volume)
        stream.float(sound.max_volume)
        stream.float(sound.min_pitch)
        stream.float(sound.max_pitch)
        stream.float(sound.min_lpf)
        stream.float(sound.max_lpf)
        stream.float(sound.min_pan)
        stream.float(sound.max_pan)
        stream.float(sound.min_surround_pan)
        stream.float(sound.max_surround_pan)
        stream.u16(sound.min_delay)
        stream.u16(sound.max_delay)
        stream.u32(string_table[sound.bone_name])
        stream.bool(sound.is_hold)
        stream.bool(sound.is_follow)
        stream.bool(sound.use_property_ids)
        stream.pad(1)
    
    def save_action(self, stream, action):
        stream.u32(action.index)
        stream.pad(4)
        stream.u32(action.sound_index)
        stream.pad(4)
        stream.u32(action.unk1)
        stream.u32(action.unk2)
        stream.u16(action.flags)
        stream.u16(action.unk3)
        stream.float(action.min_volume)
        stream.float(action.max_volume)
        stream.float(action.min_pitch)
        stream.float(action.max_pitch)
        stream.float(action.min_lpf)
        stream.float(action.max_lpf)
        stream.float(action.min_pan)
        stream.float(action.max_pan)
        stream.float(action.min_surround_pan)
        stream.float(action.max_surround_pan)
        stream.u16(action.min_delay)
        stream.u16(action.max_delay)
        stream.pad(4)
    
    def find_strings(self):
        strings = set()
        for resource in self.resources:
            strings.add(resource.name)
            for sound in resource.sounds:
                strings.add(sound.name)
                for item in sound.items:
                    strings.add(item.property_name1)
                    strings.add(item.property_name2)
                    strings.add(item.item_name)
                    strings.add(item.filename)
                    strings.add(item.bone_name)
            for action in resource.actions:
                strings.add(action.name)
        return strings

    def calc_resource_size(self, resource):
        size = 0x30
        size += 20 * len(resource.sounds)
        size += 20 * len(resource.actions)
        for sound in resource.sounds:
            size += 92 * len(sound.items)
        for action in resource.actions:
            size += 76 * len(action.items)
        size += 4
        return size
