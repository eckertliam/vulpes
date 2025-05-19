# Internal Type Representation
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Union

from .symbol import Symbol


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

    def __str__(self) -> str:
        return "int"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, IntType)

    def __hash__(self) -> int:
        return hash("int")


class FloatType(Type):
    """
    Represents the float type, used for decimal numbers.
    """

    def __str__(self) -> str:
        return "float"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, FloatType)

    def __hash__(self) -> int:
        return hash("float")


class StringType(Type):
    """
    Represents the string type, used for sequences of characters.
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


class FunctionType(Type):
    """
    Represents a function type, which includes parameter types and a return type.

    Attributes:
        params (list[Type]): The types of parameters the function accepts.
        ret_type (Type): The return type of the function.
    """

    __slots__ = ["params", "ret_type"]

    def __init__(self, params: list[Type], ret_type: Type) -> None:
        """
        Initializes a FunctionType instance.

        Args:
            params (list[Type]): The types of parameters the function accepts.
            ret_type (Type): The return type of the function.
        """
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

    def __hash__(self) -> int:
        return hash(
            (
                "fn",
                tuple(hash(t) for t in self.params),
                hash(self.ret_type),
            )
        )


# Struct Type
class StructType(Type):
    """
    Represents a struct type, which is a composite data type with named fields.

    Attributes:
        name (str): The name of the struct.
        fields (Dict[str, Type]): The fields of the struct and their types.
    """

    __slots__ = ["name", "fields"]

    def __init__(self, name: str, fields: Dict[str, Type]) -> None:
        """
        Initializes a StructType instance.

        Args:
            name (str): The name of the struct.
            fields (Dict[str, Type]): The fields of the struct and their types.
        """
        self.name = name
        self.fields = fields

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


class TypeHole(Type):
    """
    Represents a type hole, which is a placeholder for a type that is not known until type inference.

    Attributes:
        name (str): The unique identifier for the type hole.
    """

    __slots__ = ["name"]

    _next_alpha = "a"
    _next_numeric = 0

    def __init__(self) -> None:
        """
        Initializes a TypeHole instance with a unique identifier.
        """
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


class TypeAlias:
    """
    Represents a type alias, which is a name for a type.

    Attributes:
        name (str): The name of the type alias.
        type (Type): The type that the alias represents.
        symbol (Symbol): The symbol representing the type alias declaration.
    """

    __slots__ = ["name", "type", "symbol"]

    def __init__(self, name: str, type: Type, symbol: Symbol) -> None:
        """
        Initializes a TypeAlias instance.

        Args:
            name (str): The name of the type alias.
            type (Type): The type that the alias represents.
            symbol (Symbol): The symbol representing the type alias declaration.
        """
        self.name = name
        self.type = type
        self.symbol = symbol

    def __eq__(self, other: "TypeAlias") -> bool:
        return (
            isinstance(other, TypeAlias)
            and self.name == other.name
            and self.type == other.type
        )

    def __hash__(self) -> int:
        return hash(("type_alias", self.name, self.type))


class TypeEnv:
    """
    Contains a mapping of type names to their corresponding types and traits.

    Attributes:
        types (Dict[str, Type]): A dictionary mapping type names to Type objects.
        type_aliases (Dict[str, TypeAlias]): A dictionary mapping type alias names to TypeAlias objects.
    Methods:
        add_type: Adds a type to the environment.
        get_type: Retrieves a type from the environment by name.
        detect_cycle: Detects if adding a type alias would create a cycle.
        add_type_alias: Adds a type alias to the environment
        get_type_alias: Retrieves a type alias from the environment by name.
        find_type: Searches for a type by name in both the types and type_aliases fields.
    """

    __slots__ = ["types", "type_aliases"]

    def __init__(self) -> None:
        """
        Initializes a TypeEnv instance with predefined types.
        """
        self.types: Dict[str, Type] = {
            "int": IntType(),
            "float": FloatType(),
            "string": StringType(),
            "bool": BoolType(),
            "char": CharType(),
            "void": VoidType(),
        }
        self.type_aliases: Dict[str, TypeAlias] = {}

    def add_type(self, name: str, type: Type) -> None:
        """
        Adds a type to the environment.

        Args:
            name (str): The name of the type.
            type (Type): The type object to add.
        """
        self.types[name] = type

    def get_type(self, name: str) -> Optional[Type]:
        """
        Retrieves a type from the environment by name.

        Args:
            name (str): The name of the type to retrieve.

        Returns:
            Optional[Type]: The type object if found, None otherwise.
        """
        return self.types.get(name)

    def detect_cycle(self, alias_name: str, type_: Type) -> bool:
        """
        Detects if adding a type alias would create a cycle.

        Args:
            alias_name (str): The name of the type alias being added.
            type_ (Type): The type that the alias represents.

        Returns:
            bool: True if a cycle is detected, False otherwise.
        """
        visited = set()
        return self._has_cycle(alias_name, type_, visited)

    def add_type_alias(self, type_alias: TypeAlias) -> None:
        """
        Adds a type alias to the environment.

        Args:
            name (str): The name of the type alias.
            type_vars (Dict[str, TypeVar]): Type variables used in the type alias.
            type_ (Type): The type that the alias represents.

        Note:
            Before adding a type alias check if it would cause a cycle
        """
        self.type_aliases[type_alias.name] = type_alias

    def get_type_alias(self, name: str) -> Optional[TypeAlias]:
        """
        Retrieves a type alias from the environment by name.

        Args:
            name (str): The name of the type alias to retrieve.
        """
        return self.type_aliases.get(name)

    def _has_cycle(self, alias_name: str, type_: Type, visited: set) -> bool:
        """
        Helper method to recursively check for cycles in type aliases.

        Args:
            alias_name (str): The name of the type alias being checked.
            type_ (Type): The current type being checked.
            visited (set): A set of visited type alias names.

        Returns:
            bool: True if a cycle is detected, False otherwise.
        """
        if alias_name in visited:
            return True
        visited.add(alias_name)
        if isinstance(type_, TypeAlias):
            return self._has_cycle(type_.name, type_.type, visited)
        return False

    def find_type(self, name: str) -> Optional[Union[Type, TypeAlias]]:
        """
        Searches for a type by name in both the types and type_aliases fields.

        Args:
            name (str): The name of the type or type alias to search for.

        Returns:
            Optional[Union[Type, TypeAlias]]: The type or type alias if found, None otherwise.
        """
        type_ = self.types.get(name)
        if type_ is not None:
            return type_
        return self.type_aliases.get(name)
