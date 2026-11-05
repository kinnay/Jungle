
# This file was generated automatically

from dataclasses import dataclass, field

from jungle.dkctf.common import CObjectId, CQuaternion
from jungle.errors import ParseError
from jungle.streams import StreamIn, StreamOut


class BoolElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> BoolElement:
        return BEConstant()
    
    @staticmethod
    def parse(stream: StreamIn) -> BoolElement:
        type = stream.ascii(4)
        if type == "CNST": return stream.extract(BEConstant)
        raise ParseError(f"unsupported BoolElement type: {type}")
    
    @staticmethod
    def save(value: BoolElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class IntElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> IntElement:
        return IEConstant()
    
    @staticmethod
    def parse(stream: StreamIn) -> IntElement:
        type = stream.ascii(4)
        if type == "CNST": return stream.extract(IEConstant)
        elif type == "IRND": return stream.extract(IEInitialRandom)
        elif type == "PAP0": return stream.extract(IEPAP0)
        elif type == "PAP1": return stream.extract(IEPAP1)
        elif type == "PAP2": return stream.extract(IEPAP2)
        elif type == "PAP3": return stream.extract(IEPAP3)
        elif type == "RAND": return stream.extract(IERandom)
        raise ParseError(f"unsupported IntElement type: {type}")
    
    @staticmethod
    def save(value: IntElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class RealElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> RealElement:
        return REConstant()
    
    @staticmethod
    def parse(stream: StreamIn) -> RealElement:
        type = stream.ascii(4)
        if type == "ADD_": return stream.extract(REAdd)
        elif type == "CHAN": return stream.extract(RETimeChain)
        elif type == "CLTN": return stream.extract(REConditionalLessThan)
        elif type == "CNST": return stream.extract(REConstant)
        elif type == "CRNG": return stream.extract(REConditionalRange)
        elif type == "IRND": return stream.extract(REInitialRandom)
        elif type == "ISWT": return stream.extract(REInitialSwitch)
        elif type == "KEYE": return stream.extract(REKeyframeEmitter)
        elif type == "KEYP": return stream.extract(REKeyframeParticle)
        elif type == "KPIN": return stream.extract(REKeepInitial)
        elif type == "MULT": return stream.extract(REMultiply)
        elif type == "PAP1": return stream.extract(REPAP1)
        elif type == "PAP2": return stream.extract(REPAP2)
        elif type == "PAP3": return stream.extract(REPAP3)
        elif type == "PAP4": return stream.extract(REPAP4)
        elif type == "PAP5": return stream.extract(REPAP5)
        elif type == "PRLW": return stream.extract(REParticleValue_Rotation_LineWidth)
        elif type == "PSA0": return stream.extract(REPSA0)
        elif type == "PSA1": return stream.extract(REPSA1)
        elif type == "PSLL": return stream.extract(REParticleValue_Size_LineLength)
        elif type == "PSSZ": return stream.extract(REParticleValue_SecondarySize)
        elif type == "RAND": return stream.extract(RERandom)
        elif type == "SUB_": return stream.extract(RESubtract)
        elif type == "VMAG": return stream.extract(REVectorMagnitude)
        elif type == "VXTR": return stream.extract(REVectorComponentX)
        elif type == "VYTR": return stream.extract(REVectorComponentY)
        elif type == "VZTR": return stream.extract(REVectorComponentZ)
        raise ParseError(f"unsupported RealElement type: {type}")
    
    @staticmethod
    def save(value: RealElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class ComplexElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> ComplexElement:
        return ComplexWaterProxy()
    
    @staticmethod
    def parse(stream: StreamIn) -> ComplexElement:
        type = stream.ascii(4)
        if type == "KPIN": return stream.extract(ComplexKeepInitial)
        elif type == "WPXY": return stream.extract(ComplexWaterProxy)
        raise ParseError(f"unsupported ComplexElement type: {type}")
    
    @staticmethod
    def save(value: ComplexElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class VectorElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> VectorElement:
        return VEConstant()
    
    @staticmethod
    def parse(stream: StreamIn) -> VectorElement:
        type = stream.ascii(4)
        if type == "AEXT": return stream.extract(VEAEXT)
        elif type == "ANGC": return stream.extract(VEAngleCone)
        elif type == "CIRC": return stream.extract(VECircle)
        elif type == "CNST": return stream.extract(VEConstant)
        elif type == "EXTT": return stream.extract(VEEXTT)
        elif type == "RTOV": return stream.extract(VERealToVector)
        raise ParseError(f"unsupported VectorElement type: {type}")
    
    @staticmethod
    def save(value: VectorElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class RotationElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> RotationElement:
        return ERotationConst()
    
    @staticmethod
    def parse(stream: StreamIn) -> RotationElement:
        type = stream.ascii(4)
        if type == "CNST": return stream.extract(ERotationConst)
        elif type == "EXTR": return stream.extract(ERotationEXTR)
        elif type == "KPIN": return stream.extract(ERotationKeepInitial)
        elif type == "REUL": return stream.extract(ERotationEuler)
        raise ParseError(f"unsupported RotationElement type: {type}")
    
    @staticmethod
    def save(value: RotationElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class ModVectorElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> ModVectorElement:
        return MVEConstant()
    
    @staticmethod
    def parse(stream: StreamIn) -> ModVectorElement:
        type = stream.ascii(4)
        if type == "BNCE": return stream.extract(MVEBounce)
        elif type == "CNST": return stream.extract(MVEConstant)
        elif type == "GRAV": return stream.extract(MVEGravity)
        elif type == "LMPL": return stream.extract(MVELinearImplosion)
        elif type == "WIND": return stream.extract(MVEWind)
        raise ParseError(f"unsupported ModVectorElement type: {type}")
    
    @staticmethod
    def save(value: ModVectorElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class ColorElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> ColorElement:
        return CEConstant()
    
    @staticmethod
    def parse(stream: StreamIn) -> ColorElement:
        type = stream.ascii(4)
        if type == "AEXT": return stream.extract(CEAEXT)
        elif type == "CNST": return stream.extract(CEConstant)
        elif type == "EXTC": return stream.extract(CEEXTC)
        elif type == "MDAO": return stream.extract(CEModifyAlphaOnly)
        elif type == "MULT": return stream.extract(CEMultiply)
        raise ParseError(f"unsupported ColorElement type: {type}")
    
    @staticmethod
    def save(value: ColorElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class EmitterElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> EmitterElement:
        return EEAngleSphere()
    
    @staticmethod
    def parse(stream: StreamIn) -> EmitterElement:
        type = stream.ascii(4)
        if type == "ASPH": return stream.extract(EEAngleSphere)
        elif type == "PLNE": return stream.extract(EEPlane)
        elif type == "SEMR": return stream.extract(EESimpleEmitter)
        raise ParseError(f"unsupported EmitterElement type: {type}")
    
    @staticmethod
    def save(value: EmitterElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class TextureElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> TextureElement:
        return TENone()
    
    @staticmethod
    def parse(stream: StreamIn) -> TextureElement:
        type = stream.ascii(4)
        if type == "ATFB": return stream.extract(TEAnimFlipBookTexture)
        elif type == "CNST": return stream.extract(TEConstant)
        elif type == "NONE": return stream.extract(TENone)
        elif type == "TEXP": return stream.extract(TETexturePalette)
        raise ParseError(f"unsupported TextureElement type: {type}")
    
    @staticmethod
    def save(value: TextureElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class ModelElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> ModelElement:
        return MENone()
    
    @staticmethod
    def parse(stream: StreamIn) -> ModelElement:
        type = stream.ascii(4)
        if type == "CNST": return stream.extract(MEConstant)
        elif type == "NONE": return stream.extract(MENone)
        raise ParseError(f"unsupported ModelElement type: {type}")
    
    @staticmethod
    def save(value: ModelElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class StringElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> StringElement:
        return SEConstant()
    
    @staticmethod
    def parse(stream: StreamIn) -> StringElement:
        type = stream.ascii(4)
        if type == "CNST": return stream.extract(SEConstant)
        raise ParseError(f"unsupported StringElement type: {type}")
    
    @staticmethod
    def save(value: StringElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


class SpawnSystemKeyframeDataElement:
    def type_id(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.type_id()")
    
    def decode(self, stream: StreamIn) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")
    
    def encode(self, stream: StreamOut) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")
    
    @staticmethod
    def default() -> SpawnSystemKeyframeDataElement:
        return SpawnSystemKeyframeData()
    
    @staticmethod
    def parse(stream: StreamIn) -> SpawnSystemKeyframeDataElement:
        type = stream.ascii(4)
        if type == "CNST": return stream.extract(SpawnSystemKeyframeData)
        raise ParseError(f"unsupported SpawnSystemKeyframeDataElement type: {type}")
    
    @staticmethod
    def save(value: SpawnSystemKeyframeDataElement, stream: StreamOut) -> None:
        stream.ascii(value.type_id())
        stream.add(value)


@dataclass
class BEConstant(BoolElement):
    value: bool = False
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = stream.bool()
    
    def encode(self, stream: StreamOut) -> None:
        stream.bool(self.value)


@dataclass
class IEConstant(IntElement):
    value: int = 0
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = stream.s32()
    
    def encode(self, stream: StreamOut) -> None:
        stream.s32(self.value)


@dataclass
class IEInitialRandom(IntElement):
    minimum: IntElement = field(default_factory=IntElement.default)
    maximum: IntElement = field(default_factory=IntElement.default)
    
    def type_id(self) -> str:
        return "IRND"
    
    def decode(self, stream: StreamIn) -> None:
        self.minimum = IntElement.parse(stream)
        self.maximum = IntElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        IntElement.save(self.minimum, stream)
        IntElement.save(self.maximum, stream)


@dataclass
class IEPAP0(IntElement):
    
    def type_id(self) -> str:
        return "PAP0"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class IEPAP1(IntElement):
    
    def type_id(self) -> str:
        return "PAP1"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class IEPAP2(IntElement):
    
    def type_id(self) -> str:
        return "PAP2"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class IEPAP3(IntElement):
    
    def type_id(self) -> str:
        return "PAP3"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class IERandom(IntElement):
    minimum: IntElement = field(default_factory=IntElement.default)
    maximum: IntElement = field(default_factory=IntElement.default)
    
    def type_id(self) -> str:
        return "RAND"
    
    def decode(self, stream: StreamIn) -> None:
        self.minimum = IntElement.parse(stream)
        self.maximum = IntElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        IntElement.save(self.minimum, stream)
        IntElement.save(self.maximum, stream)


@dataclass
class REAdd(RealElement):
    a: RealElement = field(default_factory=RealElement.default)
    b: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "ADD_"
    
    def decode(self, stream: StreamIn) -> None:
        self.a = RealElement.parse(stream)
        self.b = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.a, stream)
        RealElement.save(self.b, stream)


@dataclass
class RETimeChain(RealElement):
    field_C: RealElement = field(default_factory=RealElement.default)
    field_10: RealElement = field(default_factory=RealElement.default)
    field_14: IntElement = field(default_factory=IntElement.default)
    
    def type_id(self) -> str:
        return "CHAN"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = RealElement.parse(stream)
        self.field_10 = RealElement.parse(stream)
        self.field_14 = IntElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.field_C, stream)
        RealElement.save(self.field_10, stream)
        IntElement.save(self.field_14, stream)


@dataclass
class REConditionalLessThan(RealElement):
    field_C: RealElement = field(default_factory=RealElement.default)
    field_10: RealElement = field(default_factory=RealElement.default)
    field_14: RealElement = field(default_factory=RealElement.default)
    field_18: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "CLTN"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = RealElement.parse(stream)
        self.field_10 = RealElement.parse(stream)
        self.field_14 = RealElement.parse(stream)
        self.field_18 = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.field_C, stream)
        RealElement.save(self.field_10, stream)
        RealElement.save(self.field_14, stream)
        RealElement.save(self.field_18, stream)


@dataclass
class REConstant(RealElement):
    value: float = .0
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = stream.float()
    
    def encode(self, stream: StreamOut) -> None:
        stream.float(self.value)


@dataclass
class REConditionalRange(RealElement):
    field_C: RealElement = field(default_factory=RealElement.default)
    field_10: RealElement = field(default_factory=RealElement.default)
    field_14: RealElement = field(default_factory=RealElement.default)
    field_18: RealElement = field(default_factory=RealElement.default)
    field_1C: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "CRNG"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = RealElement.parse(stream)
        self.field_10 = RealElement.parse(stream)
        self.field_14 = RealElement.parse(stream)
        self.field_18 = RealElement.parse(stream)
        self.field_1C = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.field_C, stream)
        RealElement.save(self.field_10, stream)
        RealElement.save(self.field_14, stream)
        RealElement.save(self.field_18, stream)
        RealElement.save(self.field_1C, stream)


@dataclass
class REInitialRandom(RealElement):
    base: RealElement = field(default_factory=RealElement.default)
    span: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "IRND"
    
    def decode(self, stream: StreamIn) -> None:
        self.base = RealElement.parse(stream)
        self.span = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.base, stream)
        RealElement.save(self.span, stream)


@dataclass
class REInitialSwitch(RealElement):
    field_C: RealElement = field(default_factory=RealElement.default)
    field_10: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "ISWT"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = RealElement.parse(stream)
        self.field_10 = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.field_C, stream)
        RealElement.save(self.field_10, stream)


@dataclass
class REKeyframeEmitter(RealElement):
    unk: int = 0
    unk2: int = 0
    unk3: bool = False
    unk4: int = 0
    unk5: int = 0
    unk6: int = 0
    frames: list[float] = field(default_factory=list)
    
    def type_id(self) -> str:
        return "KEYE"
    
    def decode(self, stream: StreamIn) -> None:
        self.unk = stream.u32()
        self.unk2 = stream.u32()
        self.unk3 = stream.bool()
        self.unk4 = stream.u8()
        self.unk5 = stream.u32()
        self.unk6 = stream.u32()
        self.frames = []
        for i in range(stream.u32()):
            frames_value = stream.float()
            self.frames.append(frames_value)
    
    def encode(self, stream: StreamOut) -> None:
        stream.u32(self.unk)
        stream.u32(self.unk2)
        stream.bool(self.unk3)
        stream.u8(self.unk4)
        stream.u32(self.unk5)
        stream.u32(self.unk6)
        stream.u32(len(self.frames))
        for frames_value in self.frames:
            stream.float(frames_value)


@dataclass
class REKeyframeParticle(RealElement):
    unk: int = 0
    unk2: int = 0
    unk3: bool = False
    unk4: int = 0
    unk5: int = 0
    unk6: int = 0
    frames: list[float] = field(default_factory=list)
    
    def type_id(self) -> str:
        return "KEYP"
    
    def decode(self, stream: StreamIn) -> None:
        self.unk = stream.u32()
        self.unk2 = stream.u32()
        self.unk3 = stream.bool()
        self.unk4 = stream.u8()
        self.unk5 = stream.u32()
        self.unk6 = stream.u32()
        self.frames = []
        for i in range(stream.u32()):
            frames_value = stream.float()
            self.frames.append(frames_value)
    
    def encode(self, stream: StreamOut) -> None:
        stream.u32(self.unk)
        stream.u32(self.unk2)
        stream.bool(self.unk3)
        stream.u8(self.unk4)
        stream.u32(self.unk5)
        stream.u32(self.unk6)
        stream.u32(len(self.frames))
        for frames_value in self.frames:
            stream.float(frames_value)


@dataclass
class REKeepInitial(RealElement):
    value: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "KPIN"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.value, stream)


@dataclass
class REMultiply(RealElement):
    a: RealElement = field(default_factory=RealElement.default)
    b: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "MULT"
    
    def decode(self, stream: StreamIn) -> None:
        self.a = RealElement.parse(stream)
        self.b = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.a, stream)
        RealElement.save(self.b, stream)


@dataclass
class REPAP1(RealElement):
    
    def type_id(self) -> str:
        return "PAP1"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REPAP2(RealElement):
    
    def type_id(self) -> str:
        return "PAP2"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REPAP3(RealElement):
    
    def type_id(self) -> str:
        return "PAP3"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REPAP4(RealElement):
    
    def type_id(self) -> str:
        return "PAP4"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REPAP5(RealElement):
    
    def type_id(self) -> str:
        return "PAP5"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REParticleValue_Rotation_LineWidth(RealElement):
    
    def type_id(self) -> str:
        return "PRLW"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REPSA0(RealElement):
    
    def type_id(self) -> str:
        return "PSA0"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REPSA1(RealElement):
    
    def type_id(self) -> str:
        return "PSA1"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REParticleValue_Size_LineLength(RealElement):
    
    def type_id(self) -> str:
        return "PSLL"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class REParticleValue_SecondarySize(RealElement):
    
    def type_id(self) -> str:
        return "PSSZ"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class RERandom(RealElement):
    base: RealElement = field(default_factory=RealElement.default)
    span: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "RAND"
    
    def decode(self, stream: StreamIn) -> None:
        self.base = RealElement.parse(stream)
        self.span = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.base, stream)
        RealElement.save(self.span, stream)


@dataclass
class RESubtract(RealElement):
    a: RealElement = field(default_factory=RealElement.default)
    b: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "SUB_"
    
    def decode(self, stream: StreamIn) -> None:
        self.a = RealElement.parse(stream)
        self.b = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.a, stream)
        RealElement.save(self.b, stream)


@dataclass
class REVectorMagnitude(RealElement):
    vector: VectorElement = field(default_factory=VectorElement.default)
    
    def type_id(self) -> str:
        return "VMAG"
    
    def decode(self, stream: StreamIn) -> None:
        self.vector = VectorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.vector, stream)


@dataclass
class REVectorComponentX(RealElement):
    vector: VectorElement = field(default_factory=VectorElement.default)
    
    def type_id(self) -> str:
        return "VXTR"
    
    def decode(self, stream: StreamIn) -> None:
        self.vector = VectorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.vector, stream)


@dataclass
class REVectorComponentY(RealElement):
    vector: VectorElement = field(default_factory=VectorElement.default)
    
    def type_id(self) -> str:
        return "VYTR"
    
    def decode(self, stream: StreamIn) -> None:
        self.vector = VectorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.vector, stream)


@dataclass
class REVectorComponentZ(RealElement):
    vector: VectorElement = field(default_factory=VectorElement.default)
    
    def type_id(self) -> str:
        return "VZTR"
    
    def decode(self, stream: StreamIn) -> None:
        self.vector = VectorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.vector, stream)


@dataclass
class ComplexKeepInitial(ComplexElement):
    value: ComplexElement = field(default_factory=ComplexElement.default)
    
    def type_id(self) -> str:
        return "KPIN"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = ComplexElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        ComplexElement.save(self.value, stream)


@dataclass
class ComplexWaterProxy(ComplexElement):
    field_C: VectorElement = field(default_factory=VectorElement.default)
    field_10: VectorElement = field(default_factory=VectorElement.default)
    field_14: ColorElement = field(default_factory=ColorElement.default)
    
    def type_id(self) -> str:
        return "WPXY"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = VectorElement.parse(stream)
        self.field_10 = VectorElement.parse(stream)
        self.field_14 = ColorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.field_C, stream)
        VectorElement.save(self.field_10, stream)
        ColorElement.save(self.field_14, stream)


@dataclass
class VEAEXT(VectorElement):
    name: StringElement = field(default_factory=StringElement.default)
    
    def type_id(self) -> str:
        return "AEXT"
    
    def decode(self, stream: StreamIn) -> None:
        self.name = StringElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        StringElement.save(self.name, stream)


@dataclass
class VEAngleCone(VectorElement):
    field_C: RealElement = field(default_factory=RealElement.default)
    field_10: RealElement = field(default_factory=RealElement.default)
    field_14: RealElement = field(default_factory=RealElement.default)
    field_18: RealElement = field(default_factory=RealElement.default)
    field_1C: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "ANGC"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = RealElement.parse(stream)
        self.field_10 = RealElement.parse(stream)
        self.field_14 = RealElement.parse(stream)
        self.field_18 = RealElement.parse(stream)
        self.field_1C = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.field_C, stream)
        RealElement.save(self.field_10, stream)
        RealElement.save(self.field_14, stream)
        RealElement.save(self.field_18, stream)
        RealElement.save(self.field_1C, stream)


@dataclass
class VECircle(VectorElement):
    unk: VectorElement = field(default_factory=VectorElement.default)
    axis: VectorElement = field(default_factory=VectorElement.default)
    unk2: RealElement = field(default_factory=RealElement.default)
    unk3: RealElement = field(default_factory=RealElement.default)
    unk4: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "CIRC"
    
    def decode(self, stream: StreamIn) -> None:
        self.unk = VectorElement.parse(stream)
        self.axis = VectorElement.parse(stream)
        self.unk2 = RealElement.parse(stream)
        self.unk3 = RealElement.parse(stream)
        self.unk4 = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.unk, stream)
        VectorElement.save(self.axis, stream)
        RealElement.save(self.unk2, stream)
        RealElement.save(self.unk3, stream)
        RealElement.save(self.unk4, stream)


@dataclass
class VEConstant(VectorElement):
    x: RealElement = field(default_factory=RealElement.default)
    y: RealElement = field(default_factory=RealElement.default)
    z: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.x = RealElement.parse(stream)
        self.y = RealElement.parse(stream)
        self.z = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.x, stream)
        RealElement.save(self.y, stream)
        RealElement.save(self.z, stream)


@dataclass
class VEEXTT(VectorElement):
    
    def type_id(self) -> str:
        return "EXTT"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class VERealToVector(VectorElement):
    value: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "RTOV"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.value, stream)


@dataclass
class ERotationConst(RotationElement):
    quaternion: CQuaternion = field(default_factory=CQuaternion)
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.quaternion = stream.extract(CQuaternion)
    
    def encode(self, stream: StreamOut) -> None:
        stream.add(self.quaternion)


@dataclass
class ERotationEXTR(RotationElement):
    
    def type_id(self) -> str:
        return "EXTR"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class ERotationKeepInitial(RotationElement):
    value: RotationElement = field(default_factory=RotationElement.default)
    
    def type_id(self) -> str:
        return "KPIN"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = RotationElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RotationElement.save(self.value, stream)


@dataclass
class ERotationEuler(RotationElement):
    field_C: RealElement = field(default_factory=RealElement.default)
    field_10: RealElement = field(default_factory=RealElement.default)
    field_14: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "REUL"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = RealElement.parse(stream)
        self.field_10 = RealElement.parse(stream)
        self.field_14 = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.field_C, stream)
        RealElement.save(self.field_10, stream)
        RealElement.save(self.field_14, stream)


@dataclass
class MVEBounce(ModVectorElement):
    unk1: VectorElement = field(default_factory=VectorElement.default)
    axis: VectorElement = field(default_factory=VectorElement.default)
    unk2: RealElement = field(default_factory=RealElement.default)
    unk3: RealElement = field(default_factory=RealElement.default)
    unk4: BoolElement = field(default_factory=BoolElement.default)
    
    def type_id(self) -> str:
        return "BNCE"
    
    def decode(self, stream: StreamIn) -> None:
        self.unk1 = VectorElement.parse(stream)
        self.axis = VectorElement.parse(stream)
        self.unk2 = RealElement.parse(stream)
        self.unk3 = RealElement.parse(stream)
        self.unk4 = BoolElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.unk1, stream)
        VectorElement.save(self.axis, stream)
        RealElement.save(self.unk2, stream)
        RealElement.save(self.unk3, stream)
        BoolElement.save(self.unk4, stream)


@dataclass
class MVEConstant(ModVectorElement):
    x: RealElement = field(default_factory=RealElement.default)
    y: RealElement = field(default_factory=RealElement.default)
    z: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.x = RealElement.parse(stream)
        self.y = RealElement.parse(stream)
        self.z = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.x, stream)
        RealElement.save(self.y, stream)
        RealElement.save(self.z, stream)


@dataclass
class MVEGravity(ModVectorElement):
    value: VectorElement = field(default_factory=VectorElement.default)
    
    def type_id(self) -> str:
        return "GRAV"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = VectorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.value, stream)


@dataclass
class MVELinearImplosion(ModVectorElement):
    unk: VectorElement = field(default_factory=VectorElement.default)
    unk2: RealElement = field(default_factory=RealElement.default)
    unk3: RealElement = field(default_factory=RealElement.default)
    unk4: RealElement = field(default_factory=RealElement.default)
    unk5: BoolElement = field(default_factory=BoolElement.default)
    
    def type_id(self) -> str:
        return "LMPL"
    
    def decode(self, stream: StreamIn) -> None:
        self.unk = VectorElement.parse(stream)
        self.unk2 = RealElement.parse(stream)
        self.unk3 = RealElement.parse(stream)
        self.unk4 = RealElement.parse(stream)
        self.unk5 = BoolElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.unk, stream)
        RealElement.save(self.unk2, stream)
        RealElement.save(self.unk3, stream)
        RealElement.save(self.unk4, stream)
        BoolElement.save(self.unk5, stream)


@dataclass
class MVEWind(ModVectorElement):
    direction: VectorElement = field(default_factory=VectorElement.default)
    strength: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "WIND"
    
    def decode(self, stream: StreamIn) -> None:
        self.direction = VectorElement.parse(stream)
        self.strength = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.direction, stream)
        RealElement.save(self.strength, stream)


@dataclass
class CEAEXT(ColorElement):
    name: StringElement = field(default_factory=StringElement.default)
    
    def type_id(self) -> str:
        return "AEXT"
    
    def decode(self, stream: StreamIn) -> None:
        self.name = StringElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        StringElement.save(self.name, stream)


@dataclass
class CEConstant(ColorElement):
    red: RealElement = field(default_factory=RealElement.default)
    green: RealElement = field(default_factory=RealElement.default)
    blue: RealElement = field(default_factory=RealElement.default)
    alpha: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.red = RealElement.parse(stream)
        self.green = RealElement.parse(stream)
        self.blue = RealElement.parse(stream)
        self.alpha = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        RealElement.save(self.red, stream)
        RealElement.save(self.green, stream)
        RealElement.save(self.blue, stream)
        RealElement.save(self.alpha, stream)


@dataclass
class CEEXTC(ColorElement):
    
    def type_id(self) -> str:
        return "EXTC"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class CEModifyAlphaOnly(ColorElement):
    color: ColorElement = field(default_factory=ColorElement.default)
    value: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "MDAO"
    
    def decode(self, stream: StreamIn) -> None:
        self.color = ColorElement.parse(stream)
        self.value = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        ColorElement.save(self.color, stream)
        RealElement.save(self.value, stream)


@dataclass
class CEMultiply(ColorElement):
    a: ColorElement = field(default_factory=ColorElement.default)
    b: ColorElement = field(default_factory=ColorElement.default)
    
    def type_id(self) -> str:
        return "MULT"
    
    def decode(self, stream: StreamIn) -> None:
        self.a = ColorElement.parse(stream)
        self.b = ColorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        ColorElement.save(self.a, stream)
        ColorElement.save(self.b, stream)


@dataclass
class EEAngleSphere(EmitterElement):
    field_C: VectorElement = field(default_factory=VectorElement.default)
    field_10: RealElement = field(default_factory=RealElement.default)
    field_14: RealElement = field(default_factory=RealElement.default)
    field_18: RealElement = field(default_factory=RealElement.default)
    field_1C: RealElement = field(default_factory=RealElement.default)
    field_20: RealElement = field(default_factory=RealElement.default)
    field_24: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "ASPH"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = VectorElement.parse(stream)
        self.field_10 = RealElement.parse(stream)
        self.field_14 = RealElement.parse(stream)
        self.field_18 = RealElement.parse(stream)
        self.field_1C = RealElement.parse(stream)
        self.field_20 = RealElement.parse(stream)
        self.field_24 = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.field_C, stream)
        RealElement.save(self.field_10, stream)
        RealElement.save(self.field_14, stream)
        RealElement.save(self.field_18, stream)
        RealElement.save(self.field_1C, stream)
        RealElement.save(self.field_20, stream)
        RealElement.save(self.field_24, stream)


@dataclass
class EEPlane(EmitterElement):
    unk: VectorElement = field(default_factory=VectorElement.default)
    axis: VectorElement = field(default_factory=VectorElement.default)
    unk2: VectorElement = field(default_factory=VectorElement.default)
    unk3: RealElement = field(default_factory=RealElement.default)
    unk4: RealElement = field(default_factory=RealElement.default)
    spread_angle: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "PLNE"
    
    def decode(self, stream: StreamIn) -> None:
        self.unk = VectorElement.parse(stream)
        self.axis = VectorElement.parse(stream)
        self.unk2 = VectorElement.parse(stream)
        self.unk3 = RealElement.parse(stream)
        self.unk4 = RealElement.parse(stream)
        self.spread_angle = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.unk, stream)
        VectorElement.save(self.axis, stream)
        VectorElement.save(self.unk2, stream)
        RealElement.save(self.unk3, stream)
        RealElement.save(self.unk4, stream)
        RealElement.save(self.spread_angle, stream)


@dataclass
class EESimpleEmitter(EmitterElement):
    field_C: VectorElement = field(default_factory=VectorElement.default)
    field_10: VectorElement = field(default_factory=VectorElement.default)
    
    def type_id(self) -> str:
        return "SEMR"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_C = VectorElement.parse(stream)
        self.field_10 = VectorElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        VectorElement.save(self.field_C, stream)
        VectorElement.save(self.field_10, stream)


@dataclass
class TEAnimFlipBookTexture(TextureElement):
    id: CObjectId = field(default_factory=CObjectId)
    unk: IntElement = field(default_factory=IntElement.default)
    unk2: BoolElement = field(default_factory=BoolElement.default)
    
    def type_id(self) -> str:
        return "ATFB"
    
    def decode(self, stream: StreamIn) -> None:
        self.id = stream.extract(CObjectId)
        self.unk = IntElement.parse(stream)
        self.unk2 = BoolElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        stream.add(self.id)
        IntElement.save(self.unk, stream)
        BoolElement.save(self.unk2, stream)


@dataclass
class TEConstant(TextureElement):
    id: CObjectId = field(default_factory=CObjectId)
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.id = stream.extract(CObjectId)
    
    def encode(self, stream: StreamOut) -> None:
        stream.add(self.id)


@dataclass
class TENone(TextureElement):
    
    def type_id(self) -> str:
        return "NONE"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class TETexturePalette(TextureElement):
    id: CObjectId = field(default_factory=CObjectId)
    size_x: IntElement = field(default_factory=IntElement.default)
    size_y: IntElement = field(default_factory=IntElement.default)
    unk: RealElement = field(default_factory=RealElement.default)
    
    def type_id(self) -> str:
        return "TEXP"
    
    def decode(self, stream: StreamIn) -> None:
        self.id = stream.extract(CObjectId)
        self.size_x = IntElement.parse(stream)
        self.size_y = IntElement.parse(stream)
        self.unk = RealElement.parse(stream)
    
    def encode(self, stream: StreamOut) -> None:
        stream.add(self.id)
        IntElement.save(self.size_x, stream)
        IntElement.save(self.size_y, stream)
        RealElement.save(self.unk, stream)


@dataclass
class MEConstant(ModelElement):
    id: CObjectId = field(default_factory=CObjectId)
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.id = stream.extract(CObjectId)
    
    def encode(self, stream: StreamOut) -> None:
        stream.add(self.id)


@dataclass
class MENone(ModelElement):
    
    def type_id(self) -> str:
        return "NONE"
    
    def decode(self, stream: StreamIn) -> None:
        pass
    
    def encode(self, stream: StreamOut) -> None:
        pass


@dataclass
class SEConstant(StringElement):
    value: str = ""
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.value = stream.string()
    
    def encode(self, stream: StreamOut) -> None:
        stream.string(self.value)


@dataclass
class SpawnSystemKeyframeData(SpawnSystemKeyframeDataElement):
    field_0: int = 0
    field_4: int = 0
    field_8: int = 0
    field_C: int = 0
    info: list[tuple[int, list[SpawnSystemKeyFrameInfo]]] = field(default_factory=list)
    
    def type_id(self) -> str:
        return "CNST"
    
    def decode(self, stream: StreamIn) -> None:
        self.field_0 = stream.u32()
        self.field_4 = stream.u32()
        self.field_8 = stream.u32()
        self.field_C = stream.u32()
        self.info = []
        for i in range(stream.u32()):
            info_value_first = stream.s32()
            info_value_second = []
            for i in range(stream.u32()):
                info_value_second_value = stream.extract(SpawnSystemKeyFrameInfo)
                info_value_second.append(info_value_second_value)
            info_value = (info_value_first, info_value_second)
            self.info.append(info_value)
    
    def encode(self, stream: StreamOut) -> None:
        stream.u32(self.field_0)
        stream.u32(self.field_4)
        stream.u32(self.field_8)
        stream.u32(self.field_C)
        stream.u32(len(self.info))
        for info_value in self.info:
            info_value_first, info_value_second = info_value
            stream.s32(info_value_first)
            stream.u32(len(info_value_second))
            for info_value_second_value in info_value_second:
                stream.add(info_value_second_value)


@dataclass
class SpawnSystemKeyFrameInfo():
    object_id: CObjectId = field(default_factory=CObjectId)
    resource_type: int = 0
    
    def type_id(self) -> str:
        return ""
    
    def decode(self, stream: StreamIn) -> None:
        self.object_id = stream.extract(CObjectId)
        self.resource_type = stream.u32()
    
    def encode(self, stream: StreamOut) -> None:
        stream.add(self.object_id)
        stream.u32(self.resource_type)


@dataclass
class GPSMDescription:
    emitter: EmitterElement | None = None
    system_lifetime: IntElement | None = None
    inherited_velocity_factor: RealElement | None = None
    seed: IntElement | None = None
    max_particles: IntElement | None = None
    emitter_rate: RealElement | None = None
    particle_lifetime: IntElement | None = None
    sprite_size: RealElement | None = None
    sprite_rotation: RealElement | None = None
    sprite_orientation: BoolElement | None = None
    particle_color: ColorElement | None = None
    particle_blend_mode: IntElement | None = None
    depth_write_enabled: BoolElement | None = None
    sorting_enabled: BoolElement | None = None
    lighting_enabled: BoolElement | None = None
    texture: TextureElement | None = None
    color_indirect_texture: BoolElement | None = None
    effect_bounds_radius: RealElement | None = None
    render_camera_facing_sprite: BoolElement | None = None
    sprite_center: IntElement | None = None
    silhouette_enabled: BoolElement | None = None
    disable_fog: BoolElement | None = None
    particle_model_rotation_euler: VectorElement | None = None
    particle_model_scale: VectorElement | None = None
    render_transformed_quad: BoolElement | None = None
    inherit_object_orientation: BoolElement | None = None
    initial_orientation: BoolElement | None = None
    particle_model_lighting: BoolElement | None = None
    apply_velocity_modifiers_on_particle_creation: BoolElement | None = None
    modify_velocity_locally_1: BoolElement | None = None
    modify_velocity_globally_1: BoolElement | None = None
    velocity_modifier_1: ModVectorElement | None = None
    modify_velocity_locally_2: BoolElement | None = None
    modify_velocity_globally_2: BoolElement | None = None
    velocity_modifier_2: ModVectorElement | None = None
    modify_velocity_locally_3: BoolElement | None = None
    modify_velocity_globally_3: BoolElement | None = None
    velocity_modifier_3: ModVectorElement | None = None
    modify_velocity_locally_4: BoolElement | None = None
    modify_velocity_globally_4: BoolElement | None = None
    velocity_modifier_4: ModVectorElement | None = None
    light_type: IntElement | None = None
    light_color: ColorElement | None = None
    light_intensity: RealElement | None = None
    light_offset: VectorElement | None = None
    light_direction: VectorElement | None = None
    light_falloff_type: IntElement | None = None
    light_falloff_rate: RealElement | None = None
    spotlight_cutoff_angle: RealElement | None = None
    system_var_real_0: RealElement | None = None
    system_var_real_1: RealElement | None = None
    system_var_real_2: RealElement | None = None
    system_var_real_3: RealElement | None = None
    system_var_real_4: RealElement | None = None
    particle_var_real_1: RealElement | None = None
    particle_var_real_2: RealElement | None = None
    particle_var_real_3: RealElement | None = None
    particle_var_real_4: RealElement | None = None
    particle_var_real_9: RealElement | None = None
    particle_var_int_0: IntElement | None = None
    particle_var_int_1: IntElement | None = None
    particle_var_int_2: IntElement | None = None
    particle_var_int_3: IntElement | None = None
    sprite_size_secondary: RealElement | None = None
    model: ModelElement | None = None
    keyframe_data: SpawnSystemKeyframeDataElement | None = None
    transform_mode: IntElement | None = None
    internal_rotation: RotationElement | None = None
    internal_translation: VectorElement | None = None
    internal_scale: VectorElement | None = None
    child_system_color: ColorElement | None = None
    water_sort_type: IntElement | None = None
    complex_variable: ComplexElement | None = None
    shader_type: IntElement | None = None
    defx: BoolElement | None = None
    particle_model_rotation: RotationElement | None = None
    
    def decode(self, stream: StreamIn) -> None:
        while True:
            type = stream.ascii(4)
            if type == "_END":
                break
            elif type == "EMTR":
                self.emitter = EmitterElement.parse(stream)
            elif type == "PSLT":
                self.system_lifetime = IntElement.parse(stream)
            elif type == "ISVF":
                self.inherited_velocity_factor = RealElement.parse(stream)
            elif type == "SEED":
                self.seed = IntElement.parse(stream)
            elif type == "MAXP":
                self.max_particles = IntElement.parse(stream)
            elif type == "GRTE":
                self.emitter_rate = RealElement.parse(stream)
            elif type == "LTME":
                self.particle_lifetime = IntElement.parse(stream)
            elif type == "SIZE":
                self.sprite_size = RealElement.parse(stream)
            elif type == "ROTA":
                self.sprite_rotation = RealElement.parse(stream)
            elif type == "ORNT":
                self.sprite_orientation = BoolElement.parse(stream)
            elif type == "COLR":
                self.particle_color = ColorElement.parse(stream)
            elif type == "PBDM":
                self.particle_blend_mode = IntElement.parse(stream)
            elif type == "ZBUF":
                self.depth_write_enabled = BoolElement.parse(stream)
            elif type == "SORT":
                self.sorting_enabled = BoolElement.parse(stream)
            elif type == "LIT_":
                self.lighting_enabled = BoolElement.parse(stream)
            elif type == "TEXR":
                self.texture = TextureElement.parse(stream)
            elif type == "CIND":
                self.color_indirect_texture = BoolElement.parse(stream)
            elif type == "FXBR":
                self.effect_bounds_radius = RealElement.parse(stream)
            elif type == "RDOP":
                self.render_camera_facing_sprite = BoolElement.parse(stream)
            elif type == "SCTR":
                self.sprite_center = IntElement.parse(stream)
            elif type == "SCNV":
                self.silhouette_enabled = BoolElement.parse(stream)
            elif type == "DFOG":
                self.disable_fog = BoolElement.parse(stream)
            elif type == "PMRT":
                self.particle_model_rotation_euler = VectorElement.parse(stream)
            elif type == "PMSC":
                self.particle_model_scale = VectorElement.parse(stream)
            elif type == "PMUS":
                self.render_transformed_quad = BoolElement.parse(stream)
            elif type == "PMOO":
                self.inherit_object_orientation = BoolElement.parse(stream)
            elif type == "ORTC":
                self.initial_orientation = BoolElement.parse(stream)
            elif type == "PMLT":
                self.particle_model_lighting = BoolElement.parse(stream)
            elif type == "VMPC":
                self.apply_velocity_modifiers_on_particle_creation = BoolElement.parse(stream)
            elif type == "VMD1":
                self.modify_velocity_locally_1 = BoolElement.parse(stream)
            elif type == "VGD1":
                self.modify_velocity_globally_1 = BoolElement.parse(stream)
            elif type == "VEL1":
                self.velocity_modifier_1 = ModVectorElement.parse(stream)
            elif type == "VMD2":
                self.modify_velocity_locally_2 = BoolElement.parse(stream)
            elif type == "VGD2":
                self.modify_velocity_globally_2 = BoolElement.parse(stream)
            elif type == "VEL2":
                self.velocity_modifier_2 = ModVectorElement.parse(stream)
            elif type == "VMD3":
                self.modify_velocity_locally_3 = BoolElement.parse(stream)
            elif type == "VGD3":
                self.modify_velocity_globally_3 = BoolElement.parse(stream)
            elif type == "VEL3":
                self.velocity_modifier_3 = ModVectorElement.parse(stream)
            elif type == "VMD4":
                self.modify_velocity_locally_4 = BoolElement.parse(stream)
            elif type == "VGD4":
                self.modify_velocity_globally_4 = BoolElement.parse(stream)
            elif type == "VEL4":
                self.velocity_modifier_4 = ModVectorElement.parse(stream)
            elif type == "LTYP":
                self.light_type = IntElement.parse(stream)
            elif type == "LCLR":
                self.light_color = ColorElement.parse(stream)
            elif type == "LINT":
                self.light_intensity = RealElement.parse(stream)
            elif type == "LOFF":
                self.light_offset = VectorElement.parse(stream)
            elif type == "LDIR":
                self.light_direction = VectorElement.parse(stream)
            elif type == "LFOT":
                self.light_falloff_type = IntElement.parse(stream)
            elif type == "LFOR":
                self.light_falloff_rate = RealElement.parse(stream)
            elif type == "LSLA":
                self.spotlight_cutoff_angle = RealElement.parse(stream)
            elif type == "SVR0":
                self.system_var_real_0 = RealElement.parse(stream)
            elif type == "SVR1":
                self.system_var_real_1 = RealElement.parse(stream)
            elif type == "SVR2":
                self.system_var_real_2 = RealElement.parse(stream)
            elif type == "SVR3":
                self.system_var_real_3 = RealElement.parse(stream)
            elif type == "SVR4":
                self.system_var_real_4 = RealElement.parse(stream)
            elif type == "ADV1":
                self.particle_var_real_1 = RealElement.parse(stream)
            elif type == "ADV2":
                self.particle_var_real_2 = RealElement.parse(stream)
            elif type == "ADV3":
                self.particle_var_real_3 = RealElement.parse(stream)
            elif type == "ADV4":
                self.particle_var_real_4 = RealElement.parse(stream)
            elif type == "ADV5":
                self.particle_var_real_9 = RealElement.parse(stream)
            elif type == "IAV0":
                self.particle_var_int_0 = IntElement.parse(stream)
            elif type == "IAV1":
                self.particle_var_int_1 = IntElement.parse(stream)
            elif type == "IAV2":
                self.particle_var_int_2 = IntElement.parse(stream)
            elif type == "IAV3":
                self.particle_var_int_3 = IntElement.parse(stream)
            elif type == "SSZE":
                self.sprite_size_secondary = RealElement.parse(stream)
            elif type == "PMDL":
                self.model = ModelElement.parse(stream)
            elif type == "KSSM":
                self.keyframe_data = SpawnSystemKeyframeDataElement.parse(stream)
            elif type == "XFMD":
                self.transform_mode = IntElement.parse(stream)
            elif type == "INTR":
                self.internal_rotation = RotationElement.parse(stream)
            elif type == "INTT":
                self.internal_translation = VectorElement.parse(stream)
            elif type == "INTS":
                self.internal_scale = VectorElement.parse(stream)
            elif type == "SPCL":
                self.child_system_color = ColorElement.parse(stream)
            elif type == "WSTP":
                self.water_sort_type = IntElement.parse(stream)
            elif type == "SCX0":
                self.complex_variable = ComplexElement.parse(stream)
            elif type == "PSTP":
                self.shader_type = IntElement.parse(stream)
            elif type == "DEFX":
                self.defx = BoolElement.parse(stream)
            elif type == "PMRQ":
                self.particle_model_rotation = RotationElement.parse(stream)
            else:
                raise ParseError(f"Unsupported GPSMDescription field: {type}")
    
    def encode(self, stream: StreamOut) -> None:
        if self.emitter is not None:
            stream.ascii("EMTR")
            EmitterElement.save(self.emitter, stream)
        if self.system_lifetime is not None:
            stream.ascii("PSLT")
            IntElement.save(self.system_lifetime, stream)
        if self.inherited_velocity_factor is not None:
            stream.ascii("ISVF")
            RealElement.save(self.inherited_velocity_factor, stream)
        if self.seed is not None:
            stream.ascii("SEED")
            IntElement.save(self.seed, stream)
        if self.max_particles is not None:
            stream.ascii("MAXP")
            IntElement.save(self.max_particles, stream)
        if self.emitter_rate is not None:
            stream.ascii("GRTE")
            RealElement.save(self.emitter_rate, stream)
        if self.particle_lifetime is not None:
            stream.ascii("LTME")
            IntElement.save(self.particle_lifetime, stream)
        if self.sprite_size is not None:
            stream.ascii("SIZE")
            RealElement.save(self.sprite_size, stream)
        if self.sprite_rotation is not None:
            stream.ascii("ROTA")
            RealElement.save(self.sprite_rotation, stream)
        if self.sprite_orientation is not None:
            stream.ascii("ORNT")
            BoolElement.save(self.sprite_orientation, stream)
        if self.particle_color is not None:
            stream.ascii("COLR")
            ColorElement.save(self.particle_color, stream)
        if self.particle_blend_mode is not None:
            stream.ascii("PBDM")
            IntElement.save(self.particle_blend_mode, stream)
        if self.depth_write_enabled is not None:
            stream.ascii("ZBUF")
            BoolElement.save(self.depth_write_enabled, stream)
        if self.sorting_enabled is not None:
            stream.ascii("SORT")
            BoolElement.save(self.sorting_enabled, stream)
        if self.lighting_enabled is not None:
            stream.ascii("LIT_")
            BoolElement.save(self.lighting_enabled, stream)
        if self.texture is not None:
            stream.ascii("TEXR")
            TextureElement.save(self.texture, stream)
        if self.color_indirect_texture is not None:
            stream.ascii("CIND")
            BoolElement.save(self.color_indirect_texture, stream)
        if self.effect_bounds_radius is not None:
            stream.ascii("FXBR")
            RealElement.save(self.effect_bounds_radius, stream)
        if self.render_camera_facing_sprite is not None:
            stream.ascii("RDOP")
            BoolElement.save(self.render_camera_facing_sprite, stream)
        if self.sprite_center is not None:
            stream.ascii("SCTR")
            IntElement.save(self.sprite_center, stream)
        if self.silhouette_enabled is not None:
            stream.ascii("SCNV")
            BoolElement.save(self.silhouette_enabled, stream)
        if self.disable_fog is not None:
            stream.ascii("DFOG")
            BoolElement.save(self.disable_fog, stream)
        if self.particle_model_rotation_euler is not None:
            stream.ascii("PMRT")
            VectorElement.save(self.particle_model_rotation_euler, stream)
        if self.particle_model_scale is not None:
            stream.ascii("PMSC")
            VectorElement.save(self.particle_model_scale, stream)
        if self.render_transformed_quad is not None:
            stream.ascii("PMUS")
            BoolElement.save(self.render_transformed_quad, stream)
        if self.inherit_object_orientation is not None:
            stream.ascii("PMOO")
            BoolElement.save(self.inherit_object_orientation, stream)
        if self.initial_orientation is not None:
            stream.ascii("ORTC")
            BoolElement.save(self.initial_orientation, stream)
        if self.particle_model_lighting is not None:
            stream.ascii("PMLT")
            BoolElement.save(self.particle_model_lighting, stream)
        if self.apply_velocity_modifiers_on_particle_creation is not None:
            stream.ascii("VMPC")
            BoolElement.save(self.apply_velocity_modifiers_on_particle_creation, stream)
        if self.modify_velocity_locally_1 is not None:
            stream.ascii("VMD1")
            BoolElement.save(self.modify_velocity_locally_1, stream)
        if self.modify_velocity_globally_1 is not None:
            stream.ascii("VGD1")
            BoolElement.save(self.modify_velocity_globally_1, stream)
        if self.velocity_modifier_1 is not None:
            stream.ascii("VEL1")
            ModVectorElement.save(self.velocity_modifier_1, stream)
        if self.modify_velocity_locally_2 is not None:
            stream.ascii("VMD2")
            BoolElement.save(self.modify_velocity_locally_2, stream)
        if self.modify_velocity_globally_2 is not None:
            stream.ascii("VGD2")
            BoolElement.save(self.modify_velocity_globally_2, stream)
        if self.velocity_modifier_2 is not None:
            stream.ascii("VEL2")
            ModVectorElement.save(self.velocity_modifier_2, stream)
        if self.modify_velocity_locally_3 is not None:
            stream.ascii("VMD3")
            BoolElement.save(self.modify_velocity_locally_3, stream)
        if self.modify_velocity_globally_3 is not None:
            stream.ascii("VGD3")
            BoolElement.save(self.modify_velocity_globally_3, stream)
        if self.velocity_modifier_3 is not None:
            stream.ascii("VEL3")
            ModVectorElement.save(self.velocity_modifier_3, stream)
        if self.modify_velocity_locally_4 is not None:
            stream.ascii("VMD4")
            BoolElement.save(self.modify_velocity_locally_4, stream)
        if self.modify_velocity_globally_4 is not None:
            stream.ascii("VGD4")
            BoolElement.save(self.modify_velocity_globally_4, stream)
        if self.velocity_modifier_4 is not None:
            stream.ascii("VEL4")
            ModVectorElement.save(self.velocity_modifier_4, stream)
        if self.light_type is not None:
            stream.ascii("LTYP")
            IntElement.save(self.light_type, stream)
        if self.light_color is not None:
            stream.ascii("LCLR")
            ColorElement.save(self.light_color, stream)
        if self.light_intensity is not None:
            stream.ascii("LINT")
            RealElement.save(self.light_intensity, stream)
        if self.light_offset is not None:
            stream.ascii("LOFF")
            VectorElement.save(self.light_offset, stream)
        if self.light_direction is not None:
            stream.ascii("LDIR")
            VectorElement.save(self.light_direction, stream)
        if self.light_falloff_type is not None:
            stream.ascii("LFOT")
            IntElement.save(self.light_falloff_type, stream)
        if self.light_falloff_rate is not None:
            stream.ascii("LFOR")
            RealElement.save(self.light_falloff_rate, stream)
        if self.spotlight_cutoff_angle is not None:
            stream.ascii("LSLA")
            RealElement.save(self.spotlight_cutoff_angle, stream)
        if self.system_var_real_0 is not None:
            stream.ascii("SVR0")
            RealElement.save(self.system_var_real_0, stream)
        if self.system_var_real_1 is not None:
            stream.ascii("SVR1")
            RealElement.save(self.system_var_real_1, stream)
        if self.system_var_real_2 is not None:
            stream.ascii("SVR2")
            RealElement.save(self.system_var_real_2, stream)
        if self.system_var_real_3 is not None:
            stream.ascii("SVR3")
            RealElement.save(self.system_var_real_3, stream)
        if self.system_var_real_4 is not None:
            stream.ascii("SVR4")
            RealElement.save(self.system_var_real_4, stream)
        if self.particle_var_real_1 is not None:
            stream.ascii("ADV1")
            RealElement.save(self.particle_var_real_1, stream)
        if self.particle_var_real_2 is not None:
            stream.ascii("ADV2")
            RealElement.save(self.particle_var_real_2, stream)
        if self.particle_var_real_3 is not None:
            stream.ascii("ADV3")
            RealElement.save(self.particle_var_real_3, stream)
        if self.particle_var_real_4 is not None:
            stream.ascii("ADV4")
            RealElement.save(self.particle_var_real_4, stream)
        if self.particle_var_real_9 is not None:
            stream.ascii("ADV5")
            RealElement.save(self.particle_var_real_9, stream)
        if self.particle_var_int_0 is not None:
            stream.ascii("IAV0")
            IntElement.save(self.particle_var_int_0, stream)
        if self.particle_var_int_1 is not None:
            stream.ascii("IAV1")
            IntElement.save(self.particle_var_int_1, stream)
        if self.particle_var_int_2 is not None:
            stream.ascii("IAV2")
            IntElement.save(self.particle_var_int_2, stream)
        if self.particle_var_int_3 is not None:
            stream.ascii("IAV3")
            IntElement.save(self.particle_var_int_3, stream)
        if self.sprite_size_secondary is not None:
            stream.ascii("SSZE")
            RealElement.save(self.sprite_size_secondary, stream)
        if self.model is not None:
            stream.ascii("PMDL")
            ModelElement.save(self.model, stream)
        if self.keyframe_data is not None:
            stream.ascii("KSSM")
            SpawnSystemKeyframeDataElement.save(self.keyframe_data, stream)
        if self.transform_mode is not None:
            stream.ascii("XFMD")
            IntElement.save(self.transform_mode, stream)
        if self.internal_rotation is not None:
            stream.ascii("INTR")
            RotationElement.save(self.internal_rotation, stream)
        if self.internal_translation is not None:
            stream.ascii("INTT")
            VectorElement.save(self.internal_translation, stream)
        if self.internal_scale is not None:
            stream.ascii("INTS")
            VectorElement.save(self.internal_scale, stream)
        if self.child_system_color is not None:
            stream.ascii("SPCL")
            ColorElement.save(self.child_system_color, stream)
        if self.water_sort_type is not None:
            stream.ascii("WSTP")
            IntElement.save(self.water_sort_type, stream)
        if self.complex_variable is not None:
            stream.ascii("SCX0")
            ComplexElement.save(self.complex_variable, stream)
        if self.shader_type is not None:
            stream.ascii("PSTP")
            IntElement.save(self.shader_type, stream)
        if self.defx is not None:
            stream.ascii("DEFX")
            BoolElement.save(self.defx, stream)
        if self.particle_model_rotation is not None:
            stream.ascii("PMRQ")
            RotationElement.save(self.particle_model_rotation, stream)
        stream.ascii("_END")
