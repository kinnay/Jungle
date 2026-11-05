
from dataclasses import dataclass, field
from typing import Callable, NoReturn

import enum
import string


NAME_HEAD_CHARS = string.ascii_letters + "_"
NAME_CHARS = NAME_HEAD_CHARS + string.digits

NUMBER_CHARS = string.digits + string.ascii_lowercase

SPECIAL_CHARS = string.punctuation

CHAR_EOF = "EOF"


class TokenType(enum.Enum):
    Name = enum.auto()
    Symbol = enum.auto()
    Number = enum.auto()
    String = enum.auto()
    EOF = enum.auto()


type TokenValue = str | int | None


@dataclass
class Token:
    type: TokenType
    value: TokenValue
    row: int
    col: int


class Tokenizer:
    _tokens: list[Token]
    _state: Callable[[str], None]

    _row: int
    _col: int

    _token_row: int
    _token_col: int

    _value: str
    _base: int

    def __init__(self):
        self._tokens = []
        self._state = self._state_next

        self._row = 1
        self._col = 1

        self._token_row = 1
        self._token_col = 1

        self._value = ""
        self._base = 10

    def parse(self, data: str) -> list[Token]:
        for char in data:
            self._state(char)

            if char == "\n":
                self._row += 1
                self._col = 1
            else:
                self._col += 1

        self._state(CHAR_EOF)
        self._add(TokenType.EOF, None)
        return self._tokens

    def _raise_error(self, char: str) -> NoReturn:
        raise ValueError(
            f"Unexpected character at {self._row}:{self._col} in "
            f"{self._state.__name__}: {char}"
        )

    def _add(self, type: TokenType, value: TokenValue) -> None:
        token = Token(type, value, self._token_row, self._token_col)
        self._tokens.append(token)

    def _state_next(self, char: str) -> None:
        self._token_row = self._row
        self._token_col = self._col

        if char == '"':
            self._value = ""
            self._state = self._state_string
        elif char == "/":
            self._state = self._state_comment_start
        elif char == "0":
            self._value = ""
            self._state = self._state_number_prefix
        elif char in string.digits:
            self._base = 10
            self._value = char
            self._state = self._state_number
        elif char in NAME_HEAD_CHARS:
            self._value = char
            self._state = self._state_name
        elif char in SPECIAL_CHARS:
            self._add(TokenType.Symbol, char)
        elif char in string.whitespace or char == CHAR_EOF:
            pass
        else:
            self._raise_error(char)

    def _state_comment_start(self, char: str) -> None:
        if char == "/":
            self._state = self._state_comment_line
        elif char == "*":
            self._state = self._state_comment_block
        else:
            self._state = self._state_next
            self._add(TokenType.Symbol, "/")
    
    def _state_comment_line(self, char: str) -> None:
        if char == "\n" or char == CHAR_EOF:
            self._state = self._state_next

    def _state_comment_block(self, char: str) -> None:
        if char == CHAR_EOF:
            self._raise_error(char)
        elif char == "*":
            self._state = self._state_comment_end

    def _state_comment_end(self, char: str) -> None:
        if char == "/":
            self._state = self._state_next
        else:
            self._state = self._state_comment_block
            self._state(char)

    def _state_name(self, char: str) -> None:
        if char in NAME_CHARS:
            self._value += char
        else:
            self._add(TokenType.Name, self._value)
            self._state = self._state_next
            self._state(char)

    def _state_string(self, char: str) -> None:
        if char == CHAR_EOF:
            self._raise_error(char)
        elif char == '"':
            self._add(TokenType.String, self._value)
            self._state = self._state_next
        else:
            self._value += char

    def _state_number(self, char: str) -> None:
        if char.lower() in NUMBER_CHARS[:self._base]:
            self._value += char
        elif self._value:
            self._add(TokenType.Number, int(self._value, self._base))
            self._state = self._state_next
            self._state(char)
        else:
            self._raise_error(char)

    def _state_number_prefix(self, char: str) -> None:
        if char == "x":
            self._base = 16
            self._state = self._state_number
        else:
            self._base = 10
            self._value = "0"
            self._state = self._state_number
            self._state(char)


class TokenStream:
    """
    The TokenStream class provides a stream to consume a list of tokens.

    The following methods are provided:
        * read_*(): reads a specific type of token from the stream
        * parse_*(): reads a specific type of token from the stream and returns
          its value
        * check_*(): checks whether the next token in the stream has a specific
          type and returns it if that is the case.
        * skip_*(value): enforces that the next token in the stream has a
          specific type and value and skips it.
    """

    _tokens: list[Token]
    _index: int

    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._index = 0

    def read(self) -> Token:
        token = self._tokens[self._index]
        self._index += 1
        return token

    def peek(self) -> Token:
        return self._tokens[self._index]

    def rewind(self) -> None:
        self._index -= 1

    def error(self, token: Token) -> NoReturn:
        if token.type == TokenType.EOF:
            message = "Unexpected end of file"
        else:
            message = f"Unexpected token at {token.row}:{token.col}: " \
                f"{token.value}"
        raise ValueError(message)

    def read_token(self, type: TokenType) -> Token:
        token = self.read()
        if token.type != type:
            self.error(token)
        return token

    def parse_token(self, type: TokenType) -> TokenValue:
        return self.read_token(type).value

    def parse_token_string(self, type: TokenType) -> str:
        token = self.read_token(type)
        if token.type != type or not isinstance(token.value, str):
            self.error(token)
        return token.value

    def has_token(self, type: TokenType) -> bool:
        return self.peek().type == type

    def skip_token(self, type: TokenType, value: TokenValue) -> None:
        token = self.read()
        if token.type != type or token.value != value:
            self.error(token)

    def check_token(self, type: TokenType, value: TokenValue) -> bool:
        token = self.peek()
        if token.type == type and token.value == value:
            self._index += 1
            return True
        return False

    def read_name(self) -> Token: return self.read_token(TokenType.Name)
    def read_symbol(self) -> Token: return self.read_token(TokenType.Symbol)

    def parse_name(self) -> str: return self.parse_token_string(TokenType.Name)
    def parse_symbol(self) -> str:
        return self.parse_token_string(TokenType.Symbol)

    def has_name(self) -> bool: return self.has_token(TokenType.Name)

    def check_name(self, value: str) -> bool:
        return self.check_token(TokenType.Name, value)

    def check_symbol(self, value: str) -> bool:
        return self.check_token(TokenType.Symbol, value)
    
    def check_eof(self) -> bool:
        return self.check_token(TokenType.EOF, None)

    def skip_symbol(self, value: str) -> None:
        self.skip_token(TokenType.Symbol, value)


class CodeGenerator:
    _code: str
    _tabs: int

    def __init__(self):
        self._code = ""
        self._tabs = 0

    def get(self) -> str:
        return self._code

    def indent(self) -> None: self._tabs += 1
    def unindent(self) -> None: self._tabs -= 1

    def write(self, text: str) -> None:
        self._code += text

    def writeline(self, text: str = "") -> None:
        self.beginline()
        self.endline(text)

    def beginline(self, text: str = "") -> None:
        self.write("    " * self._tabs + text)

    def endline(self, text: str = "") -> None:
        self.write(text + "\n")

    def blank(self, count: int = 1) -> None:
        blank = 0
        for char in self._code[::-1]:
            if char == "\n":
                blank += 1
            elif char not in string.whitespace:
                break

        for i in range(count - blank + 1):
            self.writeline()


BASIC_TYPES = [
    "uint8", "uint32", "int32", "float", "bool", "string"
]

BUILTIN_TYPES = [
    "CObjectId", "CQuaternion"
]


class Type:
    def decode(self, name: str, writer: CodeGenerator) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.decode()")

    def encode(self, name: str, writer: CodeGenerator) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.encode()")

    def typehint(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.typehint()")

    def default_field(self) -> str:
        return self.default_value()

    def default_value(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.default_value()")


@dataclass
class Type_Basic(Type):
    name: str

    def encoder(self) -> str:
        encoders = {
            "uint8": "stream.u8",
            "uint32": "stream.u32",

            "int32": "stream.s32",

            "float": "stream.float",

            "bool": "stream.bool",

            "string": "stream.string"
        }
        return encoders[self.name]

    def decode(self, name: str, writer: CodeGenerator) -> None:
        writer.writeline(f"{name} = {self.encoder()}()")

    def encode(self, name: str, writer: CodeGenerator) -> None:
        writer.writeline(f"{self.encoder()}({name})")

    def typehint(self) -> str:
        if self.name in ["uint8", "uint32", "int32"]: return "int"
        elif self.name == "float": return "float"
        elif self.name == "bool": return "bool"
        elif self.name == "string": return "str"
        else:
            raise ValueError(f"Unsupported basic type: {self.name}")

    def default_value(self) -> str:
        type = self.typehint()
        if type == "int": return "0"
        elif type == "float": return ".0"
        elif type == "bool": return "False"
        elif type == "str": return '""'
        else:
            raise ValueError(f"Unsupported basic type: {self.name}")


@dataclass
class Type_List(Type):
    subtype: Type

    def decode(self, name: str, writer: CodeGenerator) -> None:
        tempname = f"{name.split(".")[-1]}_value"
        writer.writeline(f"{name} = []")
        writer.writeline(f"for i in range(stream.u32()):")
        writer.indent()
        self.subtype.decode(tempname, writer)
        writer.writeline(f"{name}.append({tempname})")
        writer.unindent()

    def encode(self, name: str, writer: CodeGenerator) -> None:
        tempname = f"{name.split(".")[-1]}_value"
        writer.writeline(f"stream.u32(len({name}))")
        writer.writeline(f"for {tempname} in {name}:")
        writer.indent()
        self.subtype.encode(tempname, writer)
        writer.unindent()

    def typehint(self) -> str:
        return f"list[{self.subtype.typehint()}]"

    def default_field(self) -> str:
        return "field(default_factory=list)"

    def default_value(self) -> str:
        return "[]"


@dataclass
class Type_Pair(Type):
    first: Type
    second: Type

    def decode(self, name: str, writer: CodeGenerator) -> None:
        firstname = f"{name.split(".")[-1]}_first"
        secondname = f"{name.split(".")[-1]}_second"
        self.first.decode(firstname, writer)
        self.second.decode(secondname, writer)
        writer.writeline(f"{name} = ({firstname}, {secondname})")

    def encode(self, name: str, writer: CodeGenerator) -> None:
        firstname = f"{name.split(".")[-1]}_first"
        secondname = f"{name.split(".")[-1]}_second"
        writer.writeline(f"{firstname}, {secondname} = {name}")
        self.first.encode(firstname, writer)
        self.second.encode(secondname, writer)

    def typehint(self) -> str:
        return f"tuple[{self.first.typehint()}, {self.second.typehint()}]"
    
    def default_field(self) -> str:
        return f"field(default_factory=lambda: {self.default_value()})"

    def default_value(self) -> str:
        return f"({self.first.default_value()}, {self.second.default_value()})"


@dataclass
class Type_Element(Type):
    name: str

    def decode(self, name: str, writer: CodeGenerator) -> None:
        writer.writeline(f"{name} = {self.name}.parse(stream)")

    def encode(self, name: str, writer: CodeGenerator) -> None:
        writer.writeline(f"{self.name}.save({name}, stream)")

    def typehint(self) -> str:
        return self.name

    def default_field(self) -> str:
        return f"field(default_factory={self.name}.default)"

    def default_value(self) -> str:
        return f"{self.name}.default()"


@dataclass
class Type_Struct(Type):
    name: str

    def decode(self, name: str, writer: CodeGenerator) -> None:
        writer.writeline(f"{name} = stream.extract({self.name})")

    def encode(self, name: str, writer: CodeGenerator) -> None:
        writer.writeline(f"stream.add({name})")

    def typehint(self) -> str:
        return self.name

    def default_field(self) -> str:
        return f"field(default_factory={self.name})"

    def default_value(self) -> str:
        return f"{self.name}()"


@dataclass
class ParticleFile:
    descriptions: dict[str, ParticleDescription] = field(default_factory=dict)
    elements: dict[str, ParticleElement] = field(default_factory=dict)
    structs: dict[str, ParticleStruct] = field(default_factory=dict)


@dataclass
class ParticleDescription:
    name: str = ""
    fields: dict[str, tuple[str, Type]] = field(default_factory=dict)


@dataclass
class ParticleElement:
    name: str = ""
    default: str = ""
    types: dict[str, str] = field(default_factory=dict)


@dataclass
class ParticleStruct:
    id: str = ""
    parent: str = ""

    name: str = ""
    fields: dict[str, Type] = field(default_factory=dict)


class ParticleParser:
    _file: ParticleFile

    _descriptions: list[str]
    _elements: list[str]
    _structs: list[str]

    def __init__(self):
        self._file = ParticleFile()

        self._descriptions = []
        self._elements = []
        self._structs = []

    def parse(self, tokens: list[Token]) -> ParticleFile:
        stream = TokenStream(tokens)

        level = 0
        while not stream.check_eof():
            if stream.check_symbol("{"): level += 1
            elif stream.check_symbol("}"): level -= 1
            else:
                token = stream.read()
                if token.type == TokenType.Name and level == 0:
                    if token.value == "description":
                        self._descriptions.append(stream.parse_name())
                    elif token.value == "element":
                        self._elements.append(stream.parse_name())
                    elif token.value == "struct":
                        self._structs.append(stream.parse_name())

        stream = TokenStream(tokens)
        while not stream.check_eof():
            token = stream.read_name()
            if token.value == "description": self._parse_description(stream)
            elif token.value == "element": self._parse_element(stream)
            elif token.value == "struct": self._parse_struct(stream)
            else:
                stream.error(token)
        return self._file

    def _parse_description(self, stream: TokenStream) -> None:
        description = ParticleDescription()
        description.name = stream.parse_name()
        stream.skip_symbol("{")
        while not stream.check_symbol("}"):
            id = stream.parse_name()
            type = self._parse_type(stream)
            name = stream.parse_name()
            description.fields[id] = (name, type)
            stream.skip_symbol(";")
        
        self._file.descriptions[description.name] = description

    def _parse_element(self, stream: TokenStream) -> None:
        element = ParticleElement()
        element.name = stream.parse_name()
        stream.skip_symbol("{")
        while not stream.check_symbol("}"):
            id = stream.parse_name()
            type = stream.parse_name()
            if id == "default":
                element.default = type
            else:
                element.types[id] = type
            stream.skip_symbol(";")

        self._file.elements[element.name] = element

    def _parse_struct(self, stream: TokenStream) -> None:
        struct = ParticleStruct()
        struct.name = stream.parse_name()
        stream.skip_symbol("{")
        while not stream.check_symbol("}"):
            type = self._parse_type(stream)
            name = stream.parse_name()
            struct.fields[name] = type
            stream.skip_symbol(";")

        self._file.structs[struct.name] = struct

    def _parse_type(self, stream: TokenStream) -> Type:
        name = stream.parse_name()
        if name in BASIC_TYPES:
            return Type_Basic(name)
        elif name == "list":
            stream.skip_symbol("<")
            subtype = self._parse_type(stream)
            stream.skip_symbol(">")
            return Type_List(subtype)
        elif name == "pair":
            stream.skip_symbol("<")
            first = self._parse_type(stream)
            stream.skip_symbol(",")
            second = self._parse_type(stream)
            stream.skip_symbol(">")
            return Type_Pair(first, second)
        elif name in self._elements:
            return Type_Element(name)
        elif name in self._structs or name in BUILTIN_TYPES:
            return Type_Struct(name)
        else:
            raise ValueError(f"Undefined type: {name}")


class ParticleAnalyzer:
    def analyze(self, file: ParticleFile) -> None:
        for element in file.elements.values():
            if element.default not in file.structs:
                raise ValueError(f"Undefined type: {type}")
            for id, type in element.types.items():
                struct = file.structs.get(type)
                if struct is None:
                    raise ValueError(f"Undefined type: {type}")
                if struct.id:
                    raise ValueError(f"Duplicate struct reference: {type}")
                struct.id = id
                struct.parent = element.name


class ParticleGenerator:
    _file: ParticleFile

    def __init__(self, file: ParticleFile):
        self._file = file

    def generate(self) -> str:
        writer = CodeGenerator()
        writer.writeline()
        writer.writeline("# This file was generated automatically")
        writer.writeline()
        writer.writeline("from dataclasses import dataclass, field")
        writer.writeline()
        writer.writeline(
            "from jungle.dkctf.common import CObjectId, CQuaternion"
        )
        writer.writeline("from jungle.errors import ParseError")
        writer.writeline("from jungle.streams import StreamIn, StreamOut")

        for name, element in self._file.elements.items():
            writer.blank(2)
            writer.writeline(f"class {name}:")
            writer.indent()

            writer.writeline("def type_id(self) -> str:")
            writer.indent()
            writer.writeline(
                'raise NotImplementedError(f"{self.__class__.__name__}'
                '.type_id()")'
            )
            writer.unindent()
            writer.writeline()

            writer.writeline("def decode(self, stream: StreamIn) -> None:")
            writer.indent()
            writer.writeline(
                'raise NotImplementedError(f"{self.__class__.__name__}'
                '.decode()")'
            )
            writer.unindent()
            writer.writeline()

            writer.writeline("def encode(self, stream: StreamOut) -> None:")
            writer.indent()
            writer.writeline(
                'raise NotImplementedError(f"{self.__class__.__name__}'
                '.encode()")'
            )
            writer.unindent()
            writer.writeline()

            writer.writeline("@staticmethod")
            writer.writeline(f"def default() -> {name}:")
            writer.indent()
            writer.writeline(f"return {element.default}()")
            writer.unindent()
            writer.writeline()

            writer.writeline("@staticmethod")
            writer.writeline(f"def parse(stream: StreamIn) -> {name}:")
            writer.indent()
            writer.writeline("type = stream.ascii(4)")

            statement = "if"
            for id, typename in element.types.items():
                writer.beginline(f'{statement} type == "{id}": ')
                writer.endline(f"return stream.extract({typename})")
                statement = "elif"
            
            writer.writeline(
                f'raise ParseError(f"unsupported {name} type: {{type}}")'
            )
            writer.unindent()
            writer.writeline()

            writer.writeline("@staticmethod")
            writer.writeline(
                f"def save(value: {name}, stream: StreamOut) -> None:"
            )
            writer.indent()
            writer.writeline("stream.ascii(value.type_id())")
            writer.writeline("stream.add(value)")
            writer.unindent()
            writer.unindent()

        for name, struct in self._file.structs.items():
            writer.blank(2)
            writer.writeline("@dataclass")
            writer.writeline(f"class {name}({struct.parent}):")
            writer.indent()
            for field, type in struct.fields.items():
                typehint = type.typehint()
                default = type.default_field()
                writer.writeline(f"{field}: {typehint} = {default}")

            writer.blank()

            writer.writeline("def type_id(self) -> str:")
            writer.indent()
            writer.writeline(f'return "{struct.id}"')
            writer.unindent()

            writer.blank()

            writer.writeline("def decode(self, stream: StreamIn) -> None:")
            writer.indent()
            if struct.fields:
                for field, type in struct.fields.items():
                    type.decode(f"self.{field}", writer)
            else:
                writer.writeline("pass")
            writer.unindent()

            writer.blank()

            writer.writeline("def encode(self, stream: StreamOut) -> None:")
            writer.indent()
            if struct.fields:
                for field, type in struct.fields.items():
                    type.encode(f"self.{field}", writer)
            else:
                writer.writeline("pass")
            writer.unindent()
            writer.unindent()

        for class_name, description in self._file.descriptions.items():
            writer.blank(2)
            writer.writeline("@dataclass")
            writer.writeline(f"class {class_name}:")
            writer.indent()

            for name, type in description.fields.values():
                typehint = type.typehint()
                writer.writeline(f"{name}: {typehint} | None = None")
            
            writer.blank()

            writer.writeline("def decode(self, stream: StreamIn) -> None:")
            writer.indent()
            writer.writeline("while True:")
            writer.indent()
            writer.writeline("type = stream.ascii(4)")
            writer.writeline('if type == "_END":')
            writer.indent()
            writer.writeline("break")
            writer.unindent()

            for id, (name, type) in description.fields.items():
                writer.writeline(f'elif type == "{id}":')
                writer.indent()
                type.decode(f"self.{name}", writer)
                writer.unindent()

            writer.writeline("else:")
            writer.indent()
            writer.writeline(
                f'raise ParseError(f"Unsupported {class_name} field: {{type}}")'
            )
            writer.unindent()

            writer.unindent()
            writer.unindent()

            writer.blank()

            writer.writeline("def encode(self, stream: StreamOut) -> None:")
            writer.indent()
            for id, (name, type) in description.fields.items():
                field = f"self.{name}"
                writer.writeline(f"if {field} is not None:")
                writer.indent()
                writer.writeline(f'stream.ascii("{id}")')
                type.encode(field, writer)
                writer.unindent()
            writer.writeline('stream.ascii("_END")')
            writer.unindent()

            writer.unindent()

        return writer.get()


def main() -> None:
    with open("ddl/dkctf/particle.def") as f:
        text = f.read()

    tokens = Tokenizer().parse(text)
    file = ParticleParser().parse(tokens)
    ParticleAnalyzer().analyze(file)
    code = ParticleGenerator(file).generate()

    with open("jungle/dkctf/codegen.py", "w") as f:
        f.write(code)


if __name__ == "__main__":
    main()
