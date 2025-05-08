# Internal Type Representation
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Union

from .symbol import Symbol


class Type(ABC):
    """Abstract base class for all types"""

    __slots__ = []

    @abstractmethod
    def __str__(self) -> str:
        """Returns a string representation of the type"""
        pass

    @abstractmethod
    def __eq__(self, other: "Type") -> bool:
        """Check equality of two types"""
        pass

    def __ne__(self, other: "Type") -> bool:
        """Check inequality of two types"""
        return not self.__eq__(other)

    @abstractmethod
    def __hash__(self) -> int:
        """Returns a hash value for the type"""
        pass


class VoidType(Type):
    """Represents the void type"""

    def __str__(self) -> str:
        return "void"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, VoidType)

    def __hash__(self) -> int:
        return hash("void")


class IntType(Type):
    """Represents the int type"""

    def __str__(self) -> str:
        return "int"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, IntType)

    def __hash__(self) -> int:
        return hash("int")


class FloatType(Type):
    """Represents the float type"""

    def __str__(self) -> str:
        return "float"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, FloatType)

    def __hash__(self) -> int:
        return hash("float")


class StringType(Type):
    """Represents the string type"""

    def __str__(self) -> str:
        return "string"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, StringType)

    def __hash__(self) -> int:
        return hash("string")


class BoolType(Type):
    """Represents the bool type"""

    def __str__(self) -> str:
        return "bool"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, BoolType)

    def __hash__(self) -> int:
        return hash("bool")


class CharType(Type):
    """Represents the char type"""

    def __str__(self) -> str:
        return "char"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, CharType)

    def __hash__(self) -> int:
        return hash("char")


class ArrayType(Type):
    """Represents an array type"""

    __slots__ = ["elem_type"]

    def __init__(self, elem_type: Type) -> None:
        self.elem_type = elem_type

    def __str__(self) -> str:
        return f"[{self.elem_type}]"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, ArrayType) and self.elem_type == other.elem_type

    def __hash__(self) -> int:
        return hash(("array", hash(self.elem_type)))


class TupleType(Type):
    """Represents a tuple type"""

    __slots__ = ["elem_types"]

    def __init__(self, elem_types: list[Type]) -> None:
        self.elem_types = elem_types

    def __str__(self) -> str:
        return f"({', '.join(str(t) for t in self.elem_types)})"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, TupleType) and self.elem_types == other.elem_types

    def __hash__(self) -> int:
        return hash(("tuple", tuple(hash(t) for t in self.elem_types)))


class FunctionType(Type):
    """Represents a function type"""

    __slots__ = ["type_vars", "params", "ret_type"]

    def __init__(
        self, type_vars: Dict[str, "TypeVar"], params: list[Type], ret_type: Type
    ) -> None:
        self.type_vars = type_vars
        self.params = params
        self.ret_type = ret_type

    def __str__(self) -> str:
        tvs = (
            f"<{', '.join(str(t) for t in self.type_vars.values())}>"
            if self.type_vars
            else ""
        )
        return f"{tvs}({', '.join(str(t) for t in self.params)}) -> {self.ret_type}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, FunctionType)
            and self.type_vars == other.type_vars
            and self.params == other.params
            and self.ret_type == other.ret_type
        )

    def __hash__(self) -> int:
        return hash(
            (
                "fn",
                tuple(hash(t) for t in self.params),
                hash(self.ret_type),
                tuple(hash(t) for t in self.type_vars.values()),
            )
        )


class SelfType(Type):
    """
    Self type is used inside trait declarations to refer to the type of the implementing type
    This is useful for traits such as add that take a second Self as a parameter
    """

    def __str__(self) -> str:
        return "Self"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, SelfType)

    def __hash__(self) -> int:
        return hash("Self")


# Struct Type
class StructType(Type):
    """Represents a struct type. Tracks methods and traits implemented by the struct"""

    __slots__ = ["name", "type_vars", "fields", "methods", "traits"]

    def __init__(
        self, name: str, type_vars: Dict[str, "TypeVar"], fields: Dict[str, Type]
    ) -> None:
        self.name = name
        self.type_vars = type_vars
        self.fields = fields
        self.methods: Dict[str, Symbol] = {}
        self.traits: Dict[str, Trait] = {}

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(f'{k}: {v}' for k, v in self.fields.items())} }}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, StructType)
            and self.name == other.name
            and self.fields == other.fields
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
class EnumVariantType(ABC):
    """Abstract base class for all enum variant types"""

    __slots__ = ["name"]

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other: "EnumVariantType") -> bool:
        pass

    def __ne__(self, other: "EnumVariantType") -> bool:
        return not self.__eq__(other)

    @abstractmethod
    def __hash__(self) -> int:
        pass


class EnumUnitVariantType(EnumVariantType):
    """Represents a unit variant type"""

    __slots__ = ["name"]

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def __eq__(self, other: "EnumVariantType") -> bool:
        return isinstance(other, EnumUnitVariantType) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("enum_unit", self.name))

    def __str__(self) -> str:
        return self.name


class EnumTupleVariantType(EnumVariantType):
    """Represents a tuple variant type"""

    __slots__ = ["name", "types"]

    def __init__(self, name: str, types: list[Type]) -> None:
        super().__init__(name)
        self.types = types

    def __eq__(self, other: "EnumVariantType") -> bool:
        return (
            isinstance(other, EnumTupleVariantType)
            and self.name == other.name
            and self.types == other.types
        )

    def __hash__(self) -> int:
        return hash(("enum_tuple", self.name, tuple(hash(t) for t in self.types)))

    def __str__(self) -> str:
        return f"{self.name} ({', '.join(str(t) for t in self.types)})"


class EnumStructVariantType(EnumVariantType):
    """Represents a struct variant type"""

    __slots__ = ["name", "fields"]

    def __init__(self, name: str, fields: Dict[str, Type]) -> None:
        super().__init__(name)
        self.fields = fields

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(f'{k}: {v}' for k, v in self.fields.items())} }}"

    def __eq__(self, other: "EnumVariantType") -> bool:
        return (
            isinstance(other, EnumStructVariantType)
            and self.name == other.name
            and self.fields == other.fields
        )

    def __hash__(self) -> int:
        return hash(
            (
                "enum_struct",
                self.name,
                tuple(sorted((k, hash(v)) for k, v in self.fields.items())),
            )
        )


# Enum Type
class EnumType(Type):
    """Represents an enum type. Tracks methods and traits implemented by the enum"""

    __slots__ = ["name", "type_vars", "variants", "methods", "traits"]

    def __init__(
        self,
        name: str,
        type_vars: Dict[str, "TypeVar"],
        variants: list[EnumVariantType],
    ) -> None:
        self.name = name
        self.type_vars = type_vars
        self.variants: Dict[str, EnumVariantType] = {v.name: v for v in variants}
        self.methods: Dict[str, Symbol] = {}
        self.traits: Dict[str, Trait] = {}

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(str(v) for v in self.variants.values())} }}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, EnumType)
            and self.name == other.name
            and self.variants == other.variants
        )

    def __hash__(self) -> int:
        return hash(
            (
                "enum",
                self.name,
                tuple(sorted((k, hash(v)) for k, v in self.variants.items())),
            )
        )


class GenericType(Type):
    """Represents an instantiation of a generic type, will be monomorphized during type checking"""

    __slots__ = ["base_type", "type_args"]

    def __init__(self, base_type: Union[StructType, EnumType], type_args: List[Type]) -> None:
        self.base_type = base_type
        self.type_args = type_args

    def __str__(self) -> str:
        return f"{self.base_type.name}<{', '.join(str(t) for t in self.type_args)}>"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, GenericType)
            and self.base_type == other.base_type
            and self.type_args == other.type_args
        )

    def __hash__(self) -> int:
        return hash(("generic", self.base_type, tuple(hash(t) for t in self.type_args)))


class TypeHole(Type):
    """Represents a type hole. A unique identifier for a type that is not known until type inference"""

    __slots__ = ["name"]

    _next_alpha = "a"
    _next_numeric = 0

    def __init__(self) -> None:
        self.name = f"{TypeHole._next_alpha}{TypeHole._next_numeric}"
        if TypeHole._next_numeric == 9:
            TypeHole._next_alpha = chr(ord(TypeHole._next_alpha) + 1)
            TypeHole._next_numeric = 0
        else:
            TypeHole._next_numeric += 1

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, TypeHole) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class TraitBound(Type):
    """Represents a trait bound. A trait bound is a type that is a trait"""

    __slots__ = ["name", "type_args"]

    def __init__(self, name: str, type_args: Optional[List[Type]] = None) -> None:
        self.name = name
        self.type_args = type_args

    def __str__(self) -> str:
        tas = f"<{', '.join(str(t) for t in self.type_args)}>" if self.type_args else ""
        return f"{self.name}{tas}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, TraitBound)
            and self.name == other.name
            and self.type_args == other.type_args
        )

    def __hash__(self) -> int:
        if self.type_args:
            return hash(("trait_bound", self.name, tuple(hash(t) for t in self.type_args)))
        else:
            return hash(("trait_bound", self.name))


class TypeVar(Type):
    """Represent a type variable. Derived from type parameters, contains trait bounds and a name"""

    __slots__ = ["name", "bounds"]

    def __init__(self, name: str, bounds: Dict[str, TraitBound]) -> None:
        self.name = name
        self.bounds = bounds

    def __str__(self) -> str:
        return f"{self.name} : {', '.join(str(b) for b in self.bounds)}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, TypeVar)
            and self.name == other.name
            and self.bounds == other.bounds
        )

    def __hash__(self) -> int:
        return hash(("type_var", self.name, tuple(hash(b) for b in self.bounds.values())))


class Trait:
    """Represents a trait. A trait is a collection of methods that can be implemented by a type"""

    __slots__ = ["name", "type_vars", "bounds", "methods", "partial_methods"]

    def __init__(self, name: str) -> None:
        self.name = name
        self.type_vars: Dict[str, TypeVar] = {}
        self.bounds: Dict[str, TraitBound] = {}
        self.methods: Dict[str, FunctionType] = {}
        self.partial_methods: Dict[str, FunctionType] = {}

    def add_method(self, name: str, fn_type: FunctionType) -> None:
        self.methods[name] = fn_type

    def get_method(self, name: str) -> Optional[FunctionType]:
        return self.methods.get(name)

    def add_partial_method(self, name: str, fn_type: FunctionType) -> None:
        self.partial_methods[name] = fn_type

    def get_partial_method(self, name: str) -> Optional[FunctionType]:
        return self.partial_methods.get(name)


class TypeEnv:
    """Contains a mapping of type name to their corresponding type"""

    __slots__ = ["types", "traits"]

    def __init__(self) -> None:
        self.types: Dict[str, Type] = {
            "int": IntType(),
            "float": FloatType(),
            "string": StringType(),
            "bool": BoolType(),
            "char": CharType(),
            "void": VoidType(),
        }
        self.traits: Dict[str, Trait] = {}

    def add_type(self, name: str, type: Type) -> None:
        self.types[name] = type

    def get_type(self, name: str) -> Optional[Type]:
        return self.types.get(name)

    def add_trait(self, name: str, trait: Trait) -> None:
        self.traits[name] = trait

    def get_trait(self, name: str) -> Optional[Trait]:
        return self.traits.get(name)
