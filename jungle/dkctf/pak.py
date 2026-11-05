
from dataclasses import dataclass, field

from jungle.dkctf.common import \
    CGuid, CObjectTag, CFormDescriptor, CChunkDescriptor
from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut


@dataclass
class AssetDirectoryEntry:
    type: str = "XXXX"
    id: CGuid = field(default_factory=CGuid)
    offset: int = 0
    size: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.type = stream.ascii(4)
        self.id = stream.extract(CGuid)
        self.offset = stream.u64()
        self.size = stream.u64()

    def encode(self, stream: StreamOut) -> None:
        stream.ascii(self.type)
        stream.add(self.id)
        stream.u64(self.offset)
        stream.u64(self.size)


@dataclass
class MetaDataOffsetEntry:
    id: CGuid = field(default_factory=CGuid)
    offset: int = 0

    def decode(self, stream: StreamIn) -> None:
        self.id = stream.extract(CGuid)
        self.offset = stream.u32()

    def encode(self, stream: StreamOut) -> None:
        stream.add(self.id)
        stream.u32(self.offset)


@dataclass
class NameTagEntry:
    tag: CObjectTag = field(default_factory=CObjectTag)
    name: str = ""

    def decode(self, stream: StreamIn) -> None:
        self.tag = stream.extract(CObjectTag)
        self.name = stream.string()

    def encode(self, stream: StreamOut) -> None:
        stream.add(self.tag)
        stream.string(self.name)


@dataclass
class PAKAsset:
    type: str = "XXXX"
    data: bytes = b""
    metadata: bytes | None = None
    filename: str | None = None


class PAKFile:
    assets: dict[str, PAKAsset]

    def __init__(self):
        self.assets = {}

    def parse(self, data: bytes) -> None:
        self.assets = {}

        pack = CFormDescriptor.fromdata(data, "PACK", 0)
        tocc = CFormDescriptor.fromdata(pack, "TOCC", 1)

        stream = StreamIn(tocc, ">")
        while not stream.eof():
            chunk = stream.extract(CChunkDescriptor)
            if chunk.type == "ADIR":
                if chunk.version != 1:
                    raise ParseError("ADIR chunk has unexpected version number")
                self._parse_asset_directory(data, chunk.data)
            elif chunk.type == "META":
                if chunk.version != 1:
                    raise ParseError("META chunk has unexpected version number")
                self._parse_metadata(chunk.data)
            elif chunk.type == "STRG":
                if chunk.version != 1:
                    raise ParseError("STRG chunk has unexpected version number")
                self._parse_string_table(chunk.data)
            else:
                raise ParseError("Unsupported chunk type")

    def save(self) -> bytes:
        strg = self._save_string_table()

        meta = None
        offset = 32 * 2 + 24 * 2 + 4 + len(self.assets) * 36 + len(strg)
        if any(asset.metadata for asset in self.assets.values()):
            meta = self._save_metadata()
            offset += 24 + len(meta)

        adir = self._save_asset_directory(offset)

        stream = StreamOut(">")
        stream.add(CChunkDescriptor("ADIR", 1, adir))
        if meta is not None:
            stream.add(CChunkDescriptor("META", 1, meta))
        stream.add(CChunkDescriptor("STRG", 1, strg))

        tocc = CFormDescriptor("TOCC", 1, stream.get())

        stream = StreamOut(">")
        stream.add(tocc)
        for asset in self.assets.values():
            stream.write(asset.data)

        pack = CFormDescriptor("PACK", 0, stream.get())

        stream = StreamOut(">")
        stream.add(pack)
        stream.align(32)

        return stream.get()

    def _parse_asset_directory(self, file: bytes, data: bytes) -> None:
        entries = []
        stream = StreamIn(data, ">")
        for i in range(stream.u32()):
            entry = stream.extract(AssetDirectoryEntry)
            entries.append(entry)

        entries.sort(key=lambda entry: entry.offset)
        for entry in entries:
            content = file[entry.offset : entry.offset + entry.size]
            self.assets[entry.id.value] = PAKAsset(entry.type, content)

    def _parse_metadata(self, data: bytes) -> None:
        entries: list[MetaDataOffsetEntry] = []
        stream = StreamIn(data, ">")
        for i in range(stream.u32()):
            entries.append(stream.extract(MetaDataOffsetEntry))

        for entry in entries:
            if entry.id.value not in self.assets:
                raise ParseError("META entry has invalid id")
            
            stream.seek(entry.offset)
            metadata = stream.read(stream.u32())
            self.assets[entry.id.value].metadata = metadata

    def _parse_string_table(self, data: bytes) -> None:
        stream = StreamIn(data, ">")
        for i in range(stream.u32()):
            entry = stream.extract(NameTagEntry)
            tag = entry.tag
            if tag.id.value not in self.assets:
                raise ParseError("STRG entry has invalid asset id")
            if tag.type != self.assets[tag.id.value].type:
                raise ParseError("STRG entry has invalid asset type")
            self.assets[tag.id.value].filename = entry.name

    def _save_asset_directory(self, offset: int) -> bytes:
        entries: list[AssetDirectoryEntry] = []
        for id, asset in self.assets.items():
            entry = AssetDirectoryEntry(
                asset.type, CGuid(id), offset, len(asset.data)
            )
            entries.append(entry)
            offset += len(asset.data)

        entries.sort(key=lambda entry: entry.id.value)

        stream = StreamOut(">")
        stream.u32(len(self.assets))
        for entry in entries:
            stream.add(entry)
        
        return stream.get()

    def _save_metadata(self) -> bytes:
        count = len([asset for asset in self.assets.values() if asset.metadata])
        offset = 4 + 20 * count

        entries: list[MetaDataOffsetEntry] = []
        for id, asset in sorted(self.assets.items()):
            if asset.metadata:
                entry = MetaDataOffsetEntry(CGuid(id), offset)
                entries.append(entry)
                offset += len(asset.metadata) + 4

        stream = StreamOut(">")
        stream.u32(count)
        for entry in entries:
            stream.add(entry)

        for id, asset in sorted(self.assets.items()):
            if asset.metadata:
                stream.u32(len(asset.metadata))
                stream.write(asset.metadata)
        
        return stream.get()

    def _save_string_table(self) -> bytes:
        entries: list[NameTagEntry] = []
        for id, asset in self.assets.items():
            if asset.filename:
                entry = NameTagEntry(
                    CObjectTag(asset.type, CGuid(id)), asset.filename
                )
                entries.append(entry)

        entries.sort(key=lambda entry: entry.tag.id.value)

        stream = StreamOut(">")
        stream.u32(len(entries))
        for entry in entries:
            stream.add(entry)
        return stream.get()
