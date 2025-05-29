# Internal Type Representation
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Set
from uuid import uuid4


class Type(ABC):
    """
    Abstract base class for all types.
    """

    __slots__ = []

    @abstractmethod
    def __str__(self) -> str:
        """
        Returns a string representation of the type.

        Returns:
            str: The string representation of the type.
        """
        pass

    @abstractmethod
    def __eq__(self, other: "Type") -> bool:
        """
        Checks equality of two types.

        Args:
            other (Type): The type to compare with.

        Returns:
            bool: True if the types are equal, False otherwise.
        """
        pass

    def __ne__(self, other: "Type") -> bool:
        """
        Checks inequality of two types.

        Args:
            other (Type): The type to compare with.

        Returns:
            bool: True if the types are not equal, False otherwise.
        """
        return not self.__eq__(other)

    @abstractmethod
    def __hash__(self) -> int:
        """
        Returns a hash value for the type.

        Returns:
            int: The hash value of the type.
        """
        pass


class VoidType(Type):
    """
    Represents the void type, which signifies the absence of a value.
    """

    def __str__(self) -> str:
        return "void"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, VoidType)

    def __hash__(self) -> int:
        return hash("void")


class IntType(Type):
    """
    Represents the integer type, used for whole numbers.
    """

    __slots__ = ["bits", "signed"]

    def __init__(self, bits: int = 64, signed: bool = True) -> None:
        assert bits in [8, 16, 32, 64]
        self.bits = bits
        self.signed = signed

    @property
    def name(self) -> str:
        return f"i{self.bits}" if self.signed else f"u{self.bits}"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, IntType)

    def __hash__(self) -> int:
        return hash(self.name)


class FloatType(Type):
    """
    Represents the float type, used for decimal numbers.
    """

    __slots__ = ["bits"]

    def __init__(self, bits: int = 64) -> None:
        assert bits in [32, 64]
        self.bits = bits

    @property
    def name(self) -> str:
        return f"f{self.bits}"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, FloatType)

    def __hash__(self) -> int:
        return hash(self.name)


class StringType(Type):
    """
    Represents the string type, used for dynamic sequences of characters.
    """

    def __str__(self) -> str:
        return "string"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, StringType)

    def __hash__(self) -> int:
        return hash("string")


class BoolType(Type):
    """
    Represents the boolean type, used for true/false values.
    """

    def __str__(self) -> str:
        return "bool"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, BoolType)

    def __hash__(self) -> int:
        return hash("bool")


class CharType(Type):
    """
    Represents the character type, used for single characters.
    """

    def __str__(self) -> str:
        return "char"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, CharType)

    def __hash__(self) -> int:
        return hash("char")


class ArrayType(Type):
    """
    Represents an array type, which is a collection of elements of the same type.

    Attributes:
        elem_type (Type): The type of elements contained in the array.
        size (int): The size of the array.
    """

    __slots__ = ["elem_type", "size"]

    def __init__(self, elem_type: Type, size: int) -> None:
        """
        Initializes an ArrayType instance.

        Args:
            elem_type (Type): The type of elements contained in the array.
            size (int): The size of the array.
        """
        self.elem_type = elem_type
        self.size = size

    def __str__(self) -> str:
        return f"[{self.elem_type}; {self.size}]"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, ArrayType)
            and self.elem_type == other.elem_type
            and self.size == other.size
        )

    def __hash__(self) -> int:
        return hash(("array", hash(self.elem_type), self.size))


class TupleType(Type):
    """
    Represents a tuple type, which is a fixed-size collection of elements of potentially different types.

    Attributes:
        elem_types (list[Type]): The types of elements contained in the tuple.
    """

    __slots__ = ["elem_types"]

    def __init__(self, elem_types: list[Type]) -> None:
        """
        Initializes a TupleType instance.

        Args:
            elem_types (list[Type]): The types of elements contained in the tuple.
        """
        self.elem_types = elem_types

    def __str__(self) -> str:
        return f"({', '.join(str(t) for t in self.elem_types)})"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, TupleType) and self.elem_types == other.elem_types

    def __hash__(self) -> int:
        return hash(("tuple", tuple(hash(t) for t in self.elem_types)))


class TypeVar(Type):
    """Represents a type param

    Attributes:
        name (str): The name of the type variable.
        _id (uuid4): A unique identifier for the type variable. Allowing for interacting types to have the same Type param names.
    """

    __slots__ = ["name", "_id"]

    def __init__(self, name: str) -> None:
        self.name = name
        self._id = uuid4()

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, TypeVar)
            and self.name == other.name
            and self._id == other._id
        )

    def __hash__(self) -> int:
        return hash(("type_var", self.name, self._id))


class TypeHole(Type):
    """Represents a type hole, which is a placeholder for a type that is not yet known.

    Attributes:
        _id (uuid4): A unique identifier for the type hole.
    """

    __slots__ = ["_id"]

    def __init__(self) -> None:
        self._id = uuid4()

    def __str__(self) -> str:
        return f"TypeHole({self._id})"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, TypeHole) and self._id == other._id

    def __hash__(self) -> int:
        return hash(("type_hole", self._id))


def monomorphize_type(type: Type, ty_param_arg_map: Dict[TypeVar, Type]) -> Type:
    """
    Monomorphizes a type by substituting type variables with their corresponding type arguments.

    Args:
        type (Type): The type to monomorphize.
        ty_param_arg_map (Dict[TypeVar, Type]): A dictionary mapping type variables to their corresponding type arguments.

    Returns:
        Type: The monomorphized type.
    """
    if isinstance(type, TypeVar):
        if type in ty_param_arg_map:
            return ty_param_arg_map[type]
        else:
            return type
    elif isinstance(type, TupleType):
        return TupleType(
            [
                monomorphize_type(elem_type, ty_param_arg_map)
                for elem_type in type.elem_types
            ]
        )
    elif isinstance(type, PolyFunctionType):
        return type.monomorphize(list(ty_param_arg_map.values()))
    elif isinstance(type, PolyStructType):
        return type.monomorphize(list(ty_param_arg_map.values()))
    elif isinstance(type, ArrayType):
        return ArrayType(monomorphize_type(type.elem_type, ty_param_arg_map), type.size)
    elif isinstance(type, PolyUnionType):
        return type.monomorphize(list(ty_param_arg_map.values()))
    elif isinstance(type, PolyTypeAlias):
        return type.monomorphize(list(ty_param_arg_map.values()))
    else:
        return type


def mangle_type_name(name: str, type_args: List[Type]) -> str:
    """
    Mangles a type name to include type arguments

    Args:
        name (str): The name of the type.
        type_args (List[Type]): The type arguments of the type.

    Returns:
        str: The mangled type name.
    """
    return f"{name}$mono${'$'.join(str(t) for t in type_args)}"


class FunctionType(Type):
    """Represents a function type"""

    pass


class PolyFunctionType(FunctionType):
    """
    Represents a polymorphic function type, which includes parameter types and a return type.

    Attributes:
        name (str): The name of the function.
        type_params (Set[TypeVar]): The type parameters of the function.
        params (list[Type]): The types of parameters the function accepts.
        ret_type (Type): The return type of the function.
    """

    __slots__ = ["name", "type_params", "params", "ret_type"]

    def __init__(
        self, name: str, type_params: Set[TypeVar], params: list[Type], ret_type: Type
    ) -> None:
        self.name = name
        self.params = params
        self.ret_type = ret_type
        self.type_params = type_params

    def __str__(self) -> str:
        return f"{self.name}<{', '.join(str(t) for t in self.type_params)}>({', '.join(str(t) for t in self.params)}) -> {self.ret_type}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, PolyFunctionType)
            and self.name == other.name
            and self.type_params == other.type_params
            and self.params == other.params
            and self.ret_type == other.ret_type
        )

    def __hash__(self) -> int:
        return hash(
            (
                "fn",
                self.name,
                tuple(hash(t) for t in self.type_params),
                tuple(hash(t) for t in self.params),
                hash(self.ret_type),
            )
        )

    def monomorphize(self, type_args: List[Type]) -> "MonoFunctionType":
        # ensure the same len
        if len(type_args) != len(self.type_params):
            raise ValueError(
                f"Expected {len(self.type_params)} type arguments, got {len(type_args)}"
            )

        # zip the type args and the type params
        type_args_map: Dict[TypeVar, Type] = {
            param: arg for param, arg in zip(self.type_params, type_args)
        }

        # sub the type vars out of the params
        mono_params: List[Type] = [
            monomorphize_type(param, type_args_map) for param in self.params
        ]

        # sub the type vars out of the ret type
        mono_ret_type = monomorphize_type(self.ret_type, type_args_map)

        # return the monomorphized function type
        return MonoFunctionType(self.name, type_args, mono_params, mono_ret_type, self)


class AnonymousFunctionType(FunctionType):
    """Represents an anonymous function type

    Attributes:
        params (List[Type]): The types of parameters the function accepts.
        ret_type (Type): The return type of the function.
    """

    __slots__ = ["params", "ret_type"]

    def __init__(self, params: List[Type], ret_type: Type) -> None:
        self.params = params
        self.ret_type = ret_type

    def __str__(self) -> str:
        return f"fn({', '.join(str(t) for t in self.params)}) -> {self.ret_type}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, AnonymousFunctionType)
            and self.params == other.params
            and self.ret_type == other.ret_type
        )

    def __hash__(self) -> int:
        return hash(("anonymous_fn", tuple(self.params), self.ret_type))


class MonoFunctionType(FunctionType):
    """Represents a monomorphized function type

    Attributes:
        name (str): The name of the function.
        type_args (List[Type]): The type arguments of the function.
        params (List[Type]): The types of parameters the function accepts.
        ret_type (Type): The return type of the function.
        poly_type (Optional[PolyFunctionType]): The polymorphic function type.
    """

    __slots__ = ["name", "type_args", "params", "ret_type", "poly_type"]

    def __init__(
        self,
        name: str,
        type_args: List[Type],
        params: List[Type],
        ret_type: Type,
        poly_type: Optional[PolyFunctionType] = None,
    ) -> None:
        self.name = mangle_type_name(name, type_args)
        self.type_args = type_args
        self.params = params
        self.ret_type = ret_type
        self.poly_type = poly_type

    def __str__(self) -> str:
        type_args_str = (
            f"<{', '.join(str(t) for t in self.type_args)}>" if self.type_args else ""
        )
        return f"{self.name}{type_args_str}({', '.join(str(t) for t in self.params)}) -> {self.ret_type}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, MonoFunctionType)
            and self.name == other.name
            and self.type_args == other.type_args
            and self.params == other.params
            and self.ret_type == other.ret_type
            and self.poly_type == other.poly_type
        )

    def __hash__(self) -> int:
        return hash(
            (
                "monomorphized_fn",
                self.name,
                tuple(self.type_args),
                tuple(self.params),
                self.ret_type,
                self.poly_type,
            )
        )


class StructType(Type):
    """
    Represents a struct type, which is a collection of fields of potentially different types.
    """

    pass


class PolyStructType(StructType):
    """
    Represents a polymorphic struct type

    Attributes:
        name (str): The name of the struct.
        type_params (Set[TypeVar]): The type parameters of the struct.
        fields (Dict[str, Type]): A dictionary of the fields of the struct.
    """

    __slots__ = ["name", "type_params", "fields"]

    def __init__(
        self, name: str, type_params: Set[TypeVar], fields: Dict[str, Type]
    ) -> None:
        self.name = name
        self.type_params = type_params
        self.fields = fields

    def __str__(self) -> str:
        return f"struct {self.name}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, PolyStructType)
            and self.name == other.name
            and self.type_params == other.type_params
            and self.fields == other.fields
        )

    def __hash__(self) -> int:
        return hash(
            ("struct", self.name, tuple(self.type_params), tuple(self.fields.items()))
        )

    def monomorphize(self, type_args: List[Type]) -> "MonoStructType":
        # ensure the same len
        if len(type_args) != len(self.type_params):
            raise ValueError(
                f"Expected {len(self.type_params)} type arguments, got {len(type_args)}"
            )

        type_args_map: Dict[TypeVar, Type] = {
            param: arg for param, arg in zip(self.type_params, type_args)
        }

        mono_fields: Dict[str, Type] = {
            name: monomorphize_type(field_type, type_args_map)
            for name, field_type in self.fields.items()
        }

        # return the monomorphized struct type
        return MonoStructType(self.name, type_args, mono_fields, self)


class MonoStructType(StructType):
    """Represents a monomorphized struct type

    Attributes:
        name (str): The name of the struct.
        type_args (List[Type]): The type arguments of the struct.
        fields (Dict[str, Type]): A dictionary of the fields of the struct.
        poly_type (Optional[PolyStructType]): The polymorphic struct type.
    """

    __slots__ = ["name", "type_args", "fields", "poly_type"]

    def __init__(
        self,
        name: str,
        type_args: List[Type],
        fields: Dict[str, Type],
        poly_type: Optional[PolyStructType] = None,
    ) -> None:
        self.name = mangle_type_name(name, type_args)
        self.type_args = type_args
        self.fields = fields
        self.poly_type = poly_type

    def __str__(self) -> str:
        return f"struct {self.name}<{', '.join(str(t) for t in self.type_args)}>"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, MonoStructType)
            and self.name == other.name
            and self.type_args == other.type_args
            and self.fields == other.fields
            and self.poly_type == other.poly_type
        )

    def __hash__(self) -> int:
        return hash(
            (
                "monomorphized_struct",
                self.name,
                tuple(self.type_args),
                tuple(self.fields.items()),
                hash(self.poly_type),
            )
        )


class UnionType(Type):
    """
    Represents a union type, which is a collection of variants of potentially different types.
    """

    pass


class Tag(Type):
    """Represents a tag type within a union

    Attributes:
        name (str): The name of the tag.
    """

    __slots__ = ["name"]

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"tag {self.name}"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, Tag) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("tag", self.name))


class PolyUnionType(UnionType):
    """Represents a polymorphic union type

    Attributes:
        name (str): The name of the union.
        type_params (Set[TypeVar]): The type parameters of the union.
        variants (Dict[str, Type]): A dictionary of the variants of the union.
    """

    __slots__ = ["name", "type_params", "variants"]

    def __init__(
        self, name: str, type_params: Set[TypeVar], variants: Dict[str, Type]
    ) -> None:
        self.name = name
        self.type_params = type_params
        self.variants = variants

    def __str__(self) -> str:
        return f"union {self.name}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, PolyUnionType)
            and self.name == other.name
            and self.type_params == other.type_params
            and self.variants == other.variants
        )

    def __hash__(self) -> int:
        return hash(
            ("union", self.name, tuple(self.type_params), tuple(self.variants.items()))
        )

    def monomorphize(self, type_args: List[Type]) -> "MonoUnionType":
        # ensure the same len
        if len(type_args) != len(self.type_params):
            raise ValueError(
                f"Expected {len(self.type_params)} type arguments, got {len(type_args)}"
            )

        type_args_map: Dict[TypeVar, Type] = {
            param: arg for param, arg in zip(self.type_params, type_args)
        }

        mono_variants: Dict[str, Type] = {
            name: monomorphize_type(field_type, type_args_map)
            for name, field_type in self.variants.items()
        }

        # return the monomorphized union type
        return MonoUnionType(self.name, type_args, mono_variants, self)


class MonoUnionType(UnionType):
    """Represents a monomorphized union type

    Attributes:
        name (str): The name of the union.
        type_args (List[Type]): The type arguments of the union.
        variants (Dict[str, Type]): A dictionary of the variants of the union.
        poly_type (Optional[PolyUnionType]): The polymorphic union type.
    """

    __slots__ = ["name", "type_args", "variants", "poly_type"]

    def __init__(
        self,
        name: str,
        type_args: List[Type],
        variants: Dict[str, Type],
        poly_type: Optional[PolyUnionType] = None,
    ) -> None:
        self.name = mangle_type_name(name, type_args)
        self.type_args = type_args
        self.variants = variants
        self.poly_type = poly_type

    def __str__(self) -> str:
        return f"union {self.name}<{', '.join(str(t) for t in self.type_args)}>"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, MonoUnionType)
            and self.name == other.name
            and self.type_args == other.type_args
            and self.variants == other.variants
            and self.poly_type == other.poly_type
        )

    def __hash__(self) -> int:
        return hash(
            (
                "monomorphized_union",
                self.name,
                tuple(self.type_args),
                tuple(self.variants.items()),
                hash(self.poly_type),
            )
        )


class TypeAlias(Type):
    """
    Represents a type alias, which is a name for a type.
    """

    pass


class PolyTypeAlias(TypeAlias):
    """Represents a polymorphic type alias

    Attributes:
        name (str): The name of the type alias.
        type_params (Set[TypeVar]): The type parameters of the type alias.
        type (Type): The type of the type alias.
    """

    __slots__ = ["name", "type_params", "type"]

    def __init__(self, name: str, type_params: Set[TypeVar], type: Type) -> None:
        self.name = name
        self.type_params = type_params
        self.type = type

    def __str__(self) -> str:
        return f"type {self.name}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, PolyTypeAlias)
            and self.name == other.name
            and self.type_params == other.type_params
            and self.type == other.type
        )

    def __hash__(self) -> int:
        return hash(("type_alias", self.name, tuple(self.type_params), self.type))

    def monomorphize(self, type_args: List[Type]) -> "MonoTypeAlias":
        # ensure the same len
        if len(type_args) != len(self.type_params):
            raise ValueError(
                f"Expected {len(self.type_params)} type arguments, got {len(type_args)}"
            )

        type_args_map: Dict[TypeVar, Type] = {
            param: arg for param, arg in zip(self.type_params, type_args)
        }

        mono_type = monomorphize_type(self.type, type_args_map)

        return MonoTypeAlias(self.name, type_args, mono_type, self)


class MonoTypeAlias(TypeAlias):
    """Represents a monomorphized type alias

    Attributes:
        name (str): The name of the type alias.
        type_args (List[Type]): The type arguments of the type alias.
        type (Type): The type of the type alias.
        poly_type (Optional[PolyTypeAlias]): The polymorphic type alias.
    """

    __slots__ = ["name", "type_args", "type", "poly_type"]

    def __init__(
        self,
        name: str,
        type_args: List[Type],
        type: Type,
        poly_type: Optional[PolyTypeAlias] = None,
    ) -> None:
        self.name = mangle_type_name(name, type_args)
        self.type_args = type_args
        self.type = type
        self.poly_type = poly_type

    def __str__(self) -> str:
        return f"type {self.name}<{', '.join(str(t) for t in self.type_args)}>"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(other, MonoTypeAlias)
            and self.name == other.name
            and self.type_args == other.type_args
            and self.type == other.type
            and self.poly_type == other.poly_type
        )

    def __hash__(self) -> int:
        return hash(
            (
                "monomorphized_type_alias",
                self.name,
                tuple(self.type_args),
                self.type,
                self.poly_type,
            )
        )


PRIMITIVE_TYPES: Dict[str, Type] = {
    "void": VoidType(),
    "i8": IntType(8),
    "i16": IntType(16),
    "i32": IntType(32),
    "i64": IntType(64),
    "u8": IntType(8, False),
    "u16": IntType(16, False),
    "u32": IntType(32, False),
    "u64": IntType(64, False),
    "f32": FloatType(32),
    "f64": FloatType(64),
    "bool": BoolType(),
    "char": CharType(),
    "string": StringType(),
}


class TypeEnv:
    """
    Represents a type environment

    Attributes:
        types (Dict[str, Type]): A dictionary of all types in the program.
        type_aliases (Dict[str, TypeAlias]): A dictionary of all type aliases in the program.
        structs (Dict[str, StructType]): A dictionary of all structs in the program.
        unions (Dict[str, UnionType]): A dictionary of all unions in the program.
        functions (Dict[str, FunctionType]): A dictionary of all functions in the program.
    """

    __slots__ = ["types", "type_aliases", "structs", "unions", "functions"]

    def __init__(self) -> None:
        self.types: Dict[str, Type] = PRIMITIVE_TYPES.copy()
        self.type_aliases: Dict[str, TypeAlias] = {}
        self.structs: Dict[str, StructType] = {}
        self.unions: Dict[str, UnionType] = {}
        self.functions: Dict[str, FunctionType] = {}

    def set_type(self, name: str, type: Type) -> None:
        self.types[name] = type

        if isinstance(type, TypeAlias):
            self.type_aliases[name] = type
        elif isinstance(type, StructType):
            self.structs[name] = type
        elif isinstance(type, UnionType):
            self.unions[name] = type
        elif isinstance(type, FunctionType):
            self.functions[name] = type

    def get_type(self, name: str) -> Optional[Type]:
        return self.types.get(name)

    def get_struct(self, name: str) -> Optional[StructType]:
        return self.structs.get(name)

    def get_union(self, name: str) -> Optional[UnionType]:
        return self.unions.get(name)

    def get_function(self, name: str) -> Optional[FunctionType]:
        return self.functions.get(name)

    def get_alias(self, name: str) -> Optional[TypeAlias]:
        return self.type_aliases.get(name)

    def __getitem__(self, name: str) -> Optional[Type]:
        return self.get_type(name)

    def __setitem__(self, name: str, type: Type) -> None:
        self.set_type(name, type)

    def __delitem__(self, name: str) -> None:
        del self.types[name]
