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
    """

    __slots__ = ["elem_type"]

    def __init__(self, elem_type: Type) -> None:
        """
        Initializes an ArrayType instance.

        Args:
            elem_type (Type): The type of elements contained in the array.
        """
        self.elem_type = elem_type

    def __str__(self) -> str:
        return f"[{self.elem_type}]"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, ArrayType) and self.elem_type == other.elem_type

    def __hash__(self) -> int:
        return hash(("array", hash(self.elem_type)))


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
        type_vars (Dict[str, TypeVar]): Type variables used in the function.
        params (list[Type]): The types of parameters the function accepts.
        ret_type (Type): The return type of the function.
    """

    __slots__ = ["type_vars", "params", "ret_type"]

    def __init__(
        self, type_vars: Dict[str, "TypeVar"], params: list[Type], ret_type: Type
    ) -> None:
        """
        Initializes a FunctionType instance.

        Args:
            type_vars (Dict[str, TypeVar]): Type variables used in the function.
            params (list[Type]): The types of parameters the function accepts.
            ret_type (Type): The return type of the function.
        """
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
    Represents the 'Self' type used in trait declarations to refer to the implementing type.
    """

    def __str__(self) -> str:
        return "Self"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, SelfType)

    def __hash__(self) -> int:
        return hash("Self")


# Struct Type
class StructType(Type):
    """
    Represents a struct type, which is a composite data type with named fields.

    Attributes:
        name (str): The name of the struct.
        type_vars (Dict[str, TypeVar]): Type variables used in the struct.
        fields (Dict[str, Type]): The fields of the struct and their types.
    """

    __slots__ = ["name", "type_vars", "fields"]

    def __init__(
        self, name: str, type_vars: Dict[str, "TypeVar"], fields: Dict[str, Type]
    ) -> None:
        """
        Initializes a StructType instance.

        Args:
            name (str): The name of the struct.
            type_vars (Dict[str, TypeVar]): Type variables used in the struct.
            fields (Dict[str, Type]): The fields of the struct and their types.
        """
        self.name = name
        self.type_vars = type_vars
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


# Handling enum variant types
class EnumVariantType(ABC):
    """
    Abstract base class for all enum variant types.

    Attributes:
        name (str): The name of the enum variant.
    """

    __slots__ = ["name"]

    def __init__(self, name: str) -> None:
        """
        Initializes an EnumVariantType instance.

        Args:
            name (str): The name of the enum variant.
        """
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
    """
    Represents a unit variant type, which is an enum variant with no associated data.
    """

    __slots__ = ["name"]

    def __init__(self, name: str) -> None:
        """
        Initializes an EnumUnitVariantType instance.

        Args:
            name (str): The name of the unit variant.
        """
        super().__init__(name)

    def __eq__(self, other: "EnumVariantType") -> bool:
        return isinstance(other, EnumUnitVariantType) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("enum_unit", self.name))

    def __str__(self) -> str:
        return self.name


class EnumTupleVariantType(EnumVariantType):
    """
    Represents a tuple variant type, which is an enum variant with a tuple of associated data types.

    Attributes:
        types (list[Type]): The types of elements in the tuple variant.
    """

    __slots__ = ["name", "types"]

    def __init__(self, name: str, types: list[Type]) -> None:
        """
        Initializes an EnumTupleVariantType instance.

        Args:
            name (str): The name of the tuple variant.
            types (list[Type]): The types of elements in the tuple variant.
        """
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
    """
    Represents a struct variant type, which is an enum variant with named fields.

    Attributes:
        fields (Dict[str, Type]): The fields of the struct variant and their types.
    """

    __slots__ = ["name", "fields"]

    def __init__(self, name: str, fields: Dict[str, Type]) -> None:
        """
        Initializes an EnumStructVariantType instance.

        Args:
            name (str): The name of the struct variant.
            fields (Dict[str, Type]): The fields of the struct variant and their types.
        """
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
    """
    Represents an enum type, which is a type with multiple named variants.

    Attributes:
        name (str): The name of the enum.
        type_vars (Dict[str, TypeVar]): Type variables used in the enum.
        variants (list[EnumVariantType]): The variants of the enum.
    """

    __slots__ = ["name", "type_vars", "variants"]

    def __init__(
        self,
        name: str,
        type_vars: Dict[str, "TypeVar"],
        variants: list[EnumVariantType],
    ) -> None:
        """
        Initializes an EnumType instance.

        Args:
            name (str): The name of the enum.
            type_vars (Dict[str, TypeVar]): Type variables used in the enum.
            variants (list[EnumVariantType]): The variants of the enum.
        """
        self.name = name
        self.type_vars = type_vars
        self.variants: Dict[str, EnumVariantType] = {v.name: v for v in variants}

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
    """
    Represents an instantiation of a generic type, which will be monomorphized during type checking.

    Attributes:
        base_type (Union[StructType, EnumType]): The base type being instantiated.
        type_args (List[Type]): The type arguments for the generic type.
    """

    __slots__ = ["base_type", "type_args"]

    def __init__(
        self, base_type: Union[StructType, EnumType], type_args: List[Type]
    ) -> None:
        """
        Initializes a GenericType instance.

        Args:
            base_type (Union[StructType, EnumType]): The base type being instantiated.
            type_args (List[Type]): The type arguments for the generic type.
        """
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


class TraitBound(Type):
    """
    Represents a trait bound, which is a type that is a trait.

    Attributes:
        name (str): The name of the trait bound.
        type_args (Optional[List[Type]]): The type arguments for the trait bound.
    """

    __slots__ = ["name", "type_args"]

    def __init__(self, name: str, type_args: Optional[List[Type]] = None) -> None:
        """
        Initializes a TraitBound instance.

        Args:
            name (str): The name of the trait bound.
            type_args (Optional[List[Type]]): The type arguments for the trait bound.
        """
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
            return hash(
                ("trait_bound", self.name, tuple(hash(t) for t in self.type_args))
            )
        else:
            return hash(("trait_bound", self.name))


class TypeVar(Type):
    """
    Represents a type variable, which is derived from type parameters and contains trait bounds and a name.

    Attributes:
        name (str): The name of the type variable.
        bounds (Dict[str, TraitBound]): The trait bounds associated with the type variable.
    """

    __slots__ = ["name", "bounds"]

    def __init__(self, name: str, bounds: Dict[str, TraitBound]) -> None:
        """
        Initializes a TypeVar instance.

        Args:
            name (str): The name of the type variable.
            bounds (Dict[str, TraitBound]): The trait bounds associated with the type variable.
        """
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
        return hash(
            ("type_var", self.name, tuple(hash(b) for b in self.bounds.values()))
        )


class Trait:
    """
    Represents a trait, which is a collection of methods that can be implemented by a type.

    Attributes:
        name (str): The name of the trait.
        symbol (Symbol): The symbol representing the trait declaration.
        type_vars (Dict[str, TypeVar]): Type variables used in the trait.
        bounds (Dict[str, TraitBound]): Trait bounds associated with the trait.
        methods (Dict[str, FunctionType]): Methods defined in the trait.
        partial_methods (Dict[str, FunctionType]): Partial methods defined in the trait.

    Methods:
        add_method: Adds a method to the trait.
        get_method: Retrieves a method from the trait by name.
        add_partial_method: Adds a partial method to the trait.
        get_partial_method: Retrieves a partial method from the trait by name.
    """

    __slots__ = ["name", "symbol", "type_vars", "bounds", "methods", "partial_methods"]

    def __init__(self, name: str, symbol: Symbol) -> None:
        """
        Initializes a Trait instance.

        Args:
            name (str): The name of the trait.
        """
        self.name = name
        self.symbol = symbol
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


class Impl:
    """
    Represents a collection of methods implemented by a type.

    Attributes:
        target (Type): The type for which the methods are implemented.
        trait (Trait): The trait that the methods implement.
        methods (Dict[str, Symbol]): A dictionary mapping method names to their corresponding Symbol objects.
        symbol (Symbol): The symbol representing the implementation.
        type_vars (Dict[str, TypeVar]): A dictionary of type variables used in the implementation.
    """

    __slots__ = ["target", "trait", "methods", "symbol", "type_vars"]

    def __init__(
        self, target: Type, trait: Trait, symbol: Symbol, type_vars: Dict[str, TypeVar]
    ) -> None:
        """
        Initializes an Impl instance.

        Args:
            target (Type): The type for which the methods are implemented.
            trait (Trait): The trait that the methods implement.
            symbol (Symbol): The symbol representing the implementation.
            type_vars (Dict[str, TypeVar]): A dictionary of type variables used in the implementation.
        """
        self.target = target
        self.trait = trait
        self.symbol = symbol
        self.type_vars = type_vars
        self.methods: Dict[str, Symbol] = {}

    def add_method(self, name: str, method: Symbol) -> None:
        """
        Adds a method to the implementation.

        Args:
            name (str): The name of the method to add.
            method (Symbol): The Symbol object representing the method.
        """
        self.methods[name] = method

    def get_method(self, name: str) -> Optional[Symbol]:
        """
        Retrieves a method from the implementation by name.

        Args:
            name (str): The name of the method to retrieve.

        Returns:
            Optional[Symbol]: The Symbol object representing the method, or None if the method is not found.
        """
        return self.methods.get(name)


class TypeAlias:
    """
    Represents a type alias, which is a name for a type.

    Attributes:
        name (str): The name of the type alias.
        type_vars (Dict[str, TypeVar]): Type variables used in the type alias.
        type (Type): The type that the alias represents.
        symbol (Symbol): The symbol representing the type alias declaration.
    """

    __slots__ = ["name", "type_vars", "type", "symbol"]

    def __init__(
        self, name: str, type_vars: Dict[str, TypeVar], type: Type, symbol: Symbol
    ) -> None:
        """
        Initializes a TypeAlias instance.

        Args:
            name (str): The name of the type alias.
            type_vars (Dict[str, TypeVar]): Type variables used in the type alias.
            type (Type): The type that the alias represents.
            symbol (Symbol): The symbol representing the type alias declaration.
        """
        self.name = name
        self.type_vars = type_vars
        self.type = type
        self.symbol = symbol

    def __eq__(self, other: "TypeAlias") -> bool:
        return (
            isinstance(other, TypeAlias)
            and self.name == other.name
            and self.type_vars == other.type_vars
            and self.type == other.type
        )

    def __hash__(self) -> int:
        return hash(
            ("type_alias", self.name, tuple(hash(t) for t in self.type_vars), self.type)
        )


class TypeEnv:
    """
    Contains a mapping of type names to their corresponding types and traits.

    Attributes:
        types (Dict[str, Type]): A dictionary mapping type names to Type objects.
        traits (Dict[str, Trait]): A dictionary mapping trait names to Trait objects.
        impls (Dict[Type, List[Impl]]): A dictionary mapping types to their implementations.
        type_aliases (Dict[str, TypeAlias]): A dictionary mapping type alias names to TypeAlias objects.
    Methods:
        add_type: Adds a type to the environment.
        get_type: Retrieves a type from the environment by name.
        add_trait: Adds a trait to the environment.
        get_trait: Retrieves a trait from the environment by name.
        add_impl: Adds an implementation to the environment.
        type_impls_trait: Checks if a type implements a specific trait and returns the trait if it does.
        type_impls_method: Checks if a type implements a specific method and returns the method symbol if it does.
        detect_cycle: Detects if adding a type alias would create a cycle.
        add_type_alias: Adds a type alias to the environment
        get_type_alias: Retrieves a type alias from the environment by name.
        find_type: Searches for a type by name in both the types and type_aliases fields.
    """

    __slots__ = ["types", "traits", "impls", "type_aliases"]

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
        self.traits: Dict[str, Trait] = {}
        self.impls: Dict[Type, List[Impl]] = {}
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

    def add_trait(self, name: str, trait: Trait) -> None:
        """
        Adds a trait to the environment.

        Args:
            name (str): The name of the trait.
            trait (Trait): The trait object to add.
        """
        self.traits[name] = trait

    def get_trait(self, name: str) -> Optional[Trait]:
        """
        Retrieves a trait from the environment by name.

        Args:
            name (str): The name of the trait to retrieve.

        Returns:
            Optional[Trait]: The trait object if found, None otherwise.
        """
        return self.traits.get(name)

    def add_impl(self, type_: Type, impl: Impl) -> None:
        """
        Adds an implementation to the environment.

        Args:
            type_ (Type): The type for which the implementation is added.
            impl (Impl): The implementation to add.
        """
        if type_ not in self.impls:
            self.impls[type_] = []
        self.impls[type_].append(impl)

    def type_impls_trait(self, type_: Type, trait_name: str) -> Optional[Trait]:
        """
        Checks if a type implements a specific trait and returns the trait if it does.

        Args:
            type_ (Type): The type to check.
            trait_name (str): The name of the trait.

        Returns:
            Optional[Trait]: The trait if the type implements it, None otherwise.
        """
        for impl in self.impls.get(type_, []):
            if impl.trait.name == trait_name:
                return impl.trait
        return None

    def type_impls_method(self, type_: Type, method_name: str) -> Optional[Symbol]:
        """
        Checks if a type implements a specific method and returns the method symbol if it does.

        Args:
            type_ (Type): The type to check.
            method_name (str): The name of the method.

        Returns:
            Optional[Symbol]: The method symbol if the type implements it, None otherwise.
        """
        for impl in self.impls.get(type_, []):
            if method_name in impl.methods:
                return impl.methods[method_name]
        return None

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
