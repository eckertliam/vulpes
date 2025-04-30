# Internal Type Representation
from typing import Dict, Optional


class Type:
    def __str__(self) -> str:
        raise NotImplementedError("Subclasses must implement __str__")

    def __eq__(self, other: "Type") -> bool:
        raise NotImplementedError("Subclasses must implement __eq__")

    def __ne__(self, other: "Type") -> bool:
        raise NotImplementedError("Subclasses must implement __ne__")

    def __hash__(self) -> int:
        raise NotImplementedError("Subclasses must implement __hash__")


class VoidType(Type):
    def __str__(self) -> str:
        return "void"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, VoidType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, VoidType)

    def __hash__(self) -> int:
        return hash("void")


class IntType(Type):
    def __str__(self) -> str:
        return "int"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, IntType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, IntType)

    def __hash__(self) -> int:
        return hash("int")


class FloatType(Type):
    def __str__(self) -> str:
        return "float"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, FloatType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, FloatType)

    def __hash__(self) -> int:
        return hash("float")


class StringType(Type):
    def __str__(self) -> str:
        return "string"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, StringType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, StringType)

    def __hash__(self) -> int:
        return hash("string")


class BoolType(Type):
    def __str__(self) -> str:
        return "bool"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, BoolType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, BoolType)

    def __hash__(self) -> int:
        return hash("bool")


class CharType(Type):
    def __str__(self) -> str:
        return "char"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, CharType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, CharType)

    def __hash__(self) -> int:
        return hash("char")


class ArrayType(Type):
    def __init__(self, elem_type: Type) -> None:
        self.elem_type = elem_type

    def __str__(self) -> str:
        return f"[{self.elem_type}]"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, ArrayType) and self.elem_type == other.elem_type

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, ArrayType) or self.elem_type != other.elem_type

    def __hash__(self) -> int:
        return hash(("array", hash(self.elem_type)))


class TupleType(Type):
    def __init__(self, elem_types: list[Type]) -> None:
        self.elem_types = elem_types

    def __str__(self) -> str:
        return f"({', '.join(str(t) for t in self.elem_types)})"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, TupleType) and self.elem_types == other.elem_types

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(other, TupleType) or self.elem_types != other.elem_types

    def __hash__(self) -> int:
        return hash(("tuple", tuple(hash(t) for t in self.elem_types)))


class FunctionType(Type):
    def __init__(self, params: list[Type], ret_type: Type) -> None:
        self.params = params
        self.ret_type = ret_type

    def __str__(self) -> str:
        return f"({', '.join(str(t) for t in self.params)}) -> {self.ret_type}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, FunctionType)
            and self.params == other.params
            and self.ret_type == other.ret_type
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(other, FunctionType)
            or self.params != other.params
            or self.ret_type != other.ret_type
        )

    def __hash__(self) -> int:
        return hash(("fn", tuple(hash(t) for t in self.params), hash(self.ret_type)))


# Struct Type
class StructType(Type):
    def __init__(self, name: str, fields: Dict[str, Type]) -> None:
        self.name = name
        self.fields = fields
        self.methods: Dict[str, FunctionType] = {}

    def add_method(
        self, name: str, method: FunctionType, line: int, ast_id: int
    ) -> None:
        self.methods[name] = method

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(f'{k}: {v}' for k, v in self.fields.items())} }}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, StructType)
            and self.name == other.name
            and self.fields == other.fields
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(other, StructType)
            or self.name != other.name
            or self.fields != other.fields
        )

    def __hash__(self) -> int:
        return hash(
            (
                "struct",
                self.name,
                tuple(sorted((k, hash(v)) for k, v in self.fields.items())),
            )
        )


# Handling enum variant types
class EnumVariantType:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, EnumVariantType)
            and self.name == other.name
            and self.__dict__ == other.__dict__
        )

    def __ne__(self, other: object) -> bool:
        return (
            not isinstance(other, EnumVariantType)
            or self.name != other.name
            or self.__dict__ != other.__dict__
        )

    def __hash__(self) -> int:
        return hash(
            (self.__class__.__name__, self.name, tuple(sorted(self.__dict__.items())))
        )


class EnumUnitVariantType(EnumVariantType):
    def __init__(self, name: str) -> None:
        super().__init__(name)


class EnumTupleVariantType(EnumVariantType):
    def __init__(self, name: str, types: list[Type]) -> None:
        super().__init__(name)
        self.types = types

    def __str__(self) -> str:
        return f"{self.name} ({', '.join(str(t) for t in self.types)})"


class EnumStructVariantType(EnumVariantType):
    def __init__(self, name: str, fields: Dict[str, Type]) -> None:
        super().__init__(name)
        self.fields = fields

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(f'{k}: {v}' for k, v in self.fields.items())} }}"


# Enum Type
class EnumType(Type):
    def __init__(self, name: str, variants: list[EnumVariantType]) -> None:
        self.name = name
        self.variants: Dict[str, EnumVariantType] = {v.name: v for v in variants}
        self.methods: Dict[str, FunctionType] = {}

    def add_method(
        self, name: str, method: FunctionType, line: int, ast_id: int
    ) -> None:
        self.methods[name] = method

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(str(v) for v in self.variants.values())} }}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, EnumType)
            and self.name == other.name
            and self.variants == other.variants
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(other, EnumType)
            or self.name != other.name
            or self.variants != other.variants
        )

    def __hash__(self) -> int:
        return hash(
            (
                "enum",
                self.name,
                tuple(sorted((k, hash(v)) for k, v in self.variants.items())),
            )
        )


class TypeVar(Type):
    _next_alpha = "a"
    _next_numeric = 0

    def __init__(self) -> None:
        self.name = f"T{TypeVar._next_alpha}{TypeVar._next_numeric}"
        if TypeVar._next_numeric == 9:
            TypeVar._next_alpha = chr(ord(TypeVar._next_alpha) + 1)
            TypeVar._next_numeric = 0
        else:
            TypeVar._next_numeric += 1

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, TypeVar) and self.name == other.name

    def __ne__(self, other: "Type") -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)

# Type Env is a helper type that contains a mapping of type name to their corresponding type
class TypeEnv:
    def __init__(self) -> None:
        self.types: Dict[str, Type] = {
            "int": IntType(),
            "float": FloatType(),
            "string": StringType(),
            "bool": BoolType(),
            "char": CharType(),
            "void": VoidType(),
        }

    def add_type(self, name: str, type: Type) -> None:
        self.types[name] = type
        
    def get_type(self, name: str) -> Optional[Type]:
        return self.types.get(name)
    