# Expressive AST we convert the Lark ast into
from typing import Dict, Optional, Union

from .symbol import Symbol
from .types import BoolType, CharType, FloatType, IntType, StringType, Type

# TODO: add docstrings for all nodes
# TODO: add __slots__ to all nodes
# TODO: add generic type annotation node
# TODO: add type param node


class Program:
    """
    Represents a program. A program is a collection of declarations

    Attributes:
        declarations: A list of declarations in the program
        source: The source code of the program
        nodes: A dictionary of nodes by id to improve performance when grabbing nodes by id a lot
    """

    __slots__ = ["declarations", "source", "nodes"]

    def __init__(self, source: Optional[str] = None) -> None:
        self.declarations: list[Declaration] = []
        self.source: Optional[str] = source
        # memoize nodes by id to improve perf when grabbing nodes by id a lot
        self.nodes: Dict[int, Node] = {}

    def push(self, declaration: "Declaration"):
        """Add a declaration to the program"""
        self.declarations.append(declaration)

    # get a node by id
    def get_node(self, id: int) -> Optional["Node"]:
        """Get a node by id. Memoized for performance"""
        # check memoized nodes first
        # saves us time over traversing the entire program
        if id in self.nodes:
            return self.nodes[id]

        # check all declarations
        for declaration in self.declarations:
            node = declaration.get_node(id)
            if node is not None:
                self.nodes[id] = node
                return node
        return None

    # get the top level declaration that contains the node id
    def get_decl(self, id: int) -> Optional["Declaration"]:
        """Get the top level declaration that contains the node id.
        Returns None if the node is not found in any top level declaration"""
        for declaration in self.declarations:
            # while we're here checking out the nodes we add them to the memoized nodes
            if declaration.get_node(id) is not None:
                return declaration
        return None


class Node:
    """
    Base class for all AST nodes

    Attributes:
        kind: The kind of the node
        line: The line number of the node
        id: The id of the node
        symbol: The symbol associated with the node
    """

    __slots__ = ["kind", "line", "id", "symbol"]

    _next_id = 0  # class variable to track the next available ID

    def __init__(self, kind: str, line: int) -> None:
        self.kind = kind
        self.line = line
        self.id = Node._next_id
        # optional symbol associated with the node
        # makes passes a lot easier and more efficient
        self.symbol: Optional[Symbol] = None
        Node._next_id += 1

    def get_node(self, id: int) -> Optional["Node"]:
        """Get a node by id.
        Returns None if the node is not found"""
        if self.id == id:
            return self
        else:
            return None

    def get_span(self) -> tuple[int, int]:
        """Get the span of the node. The span is the line number of the first and last line of the node"""
        return (self.line, self.line)

    def assert_symbol(self) -> Symbol:
        """Safely get the symbol of a node and raise an error if it is not set"""
        if self.symbol is None:
            raise RuntimeError(f"Node {self.kind} has no symbol")
        return self.symbol


class Declaration(Node):
    """Unifies all top level declarations in the program"""

    pass


class Statement(Node):
    """Unifies all statements in the program"""

    pass


class TypeAnnotation(Node):
    """Unifies all type annotations in the program"""

    pass


class NamedTypeAnnotation(TypeAnnotation):
    """
    A simple named type annotation

    Attributes:
        name: The name of the type
    """

    __slots__ = ["name", "kind", "line", "id", "symbol"]

    def __init__(self, name: str, line: int) -> None:
        super().__init__("named_type", line)
        self.name = name


class ArrayTypeAnnotation(TypeAnnotation):
    """
    A type annotation for an array type

    Attributes:
        elem_type: The type of the elements in the array
    """

    __slots__ = ["elem_type", "kind", "line", "id", "symbol"]

    def __init__(self, elem_type: TypeAnnotation, line: int) -> None:
        super().__init__("array_type", line)
        self.elem_type = elem_type

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        else:
            return self.elem_type.get_node(id)


class TupleTypeAnnotation(TypeAnnotation):
    """
    A type annotation for a tuple type

    Attributes:
        elem_types: The types of the elements in the tuple
    """

    __slots__ = ["elem_types", "kind", "line", "id", "symbol"]

    def __init__(self, elem_types: list[TypeAnnotation], line: int) -> None:
        super().__init__("tuple_type", line)
        self.elem_types = elem_types

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        else:
            for elem_type in self.elem_types:
                node = elem_type.get_node(id)
                if node is not None:
                    return node
            return None


class FunctionTypeAnnotation(TypeAnnotation):
    """
    A type annotation for a function type

    Attributes:
        params: The types of the parameters of the function
        ret_type: The type of the return value of the function
    """

    __slots__ = ["params", "ret_type", "kind", "line", "id", "symbol"]

    def __init__(
        self, params: list[TypeAnnotation], ret_type: TypeAnnotation, line: int
    ) -> None:
        super().__init__("function_type", line)
        self.params = params
        self.ret_type = ret_type

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for param in self.params:
            node = param.get_node(id)
            if node is not None:
                return node
        return self.ret_type.get_node(id)


class GenericTypeAnnotation(TypeAnnotation):
    """
    A type annotation for a generic type

    Attributes:
        name: The name of the generic type
        type_args: The type arguments of the generic type
    """

    __slots__ = ["name", "type_args", "kind", "line", "id", "symbol"]

    def __init__(self, name: str, type_args: list[TypeAnnotation], line: int) -> None:
        super().__init__("generic_type", line)
        self.name = name
        self.type_args = type_args

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for type_arg in self.type_args:
            node = type_arg.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for type_arg in self.type_args:
            tmin, tmax = type_arg.get_span()
            min_line = min(min_line, tmin)
            max_line = max(max_line, tmax)
        return (min_line, max_line)


class TypeParam(Node):
    """A type parameter"""

    __slots__ = ["name", "bounds", "kind", "line", "id", "symbol"]

    def __init__(
        self,
        name: str,
        bounds: Optional[list[Union[NamedTypeAnnotation, GenericTypeAnnotation]]],
        line: int,
    ) -> None:
        super().__init__("type_param", line)
        self.name = name
        self.bounds = bounds

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.bounds is not None:
            for bound in self.bounds:
                node = bound.get_node(id)
                if node is not None:
                    return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.bounds is not None:
            for bound in self.bounds:
                bmin, bmax = bound.get_span()
                min_line = min(min_line, bmin)
                max_line = max(max_line, bmax)
        return (min_line, max_line)


class FnDecl(Declaration, Statement):
    """A function declaration

    Attributes:
        pub: Whether the function is public
        name: The name of the function
        params: The parameters of the function
        ret_type: The type of the return value of the function
        body: The body of the function
    """

    __slots__ = [
        "pub",
        "name",
        "type_params",
        "params",
        "ret_type",
        "body",
        "kind",
        "line",
        "id",
        "symbol",
    ]

    def __init__(
        self,
        pub: bool,
        name: str,
        type_params: Optional[list["TypeParam"]],
        params: list["Param"],
        ret_type: TypeAnnotation,
        body: list[Statement],
        line: int,
    ) -> None:
        super().__init__("fn_decl", line)
        self.pub: bool = pub
        self.name: str = name
        self.type_params: Optional[list[TypeParam]] = type_params
        self.params: list["Param"] = params
        self.ret_type: TypeAnnotation = ret_type
        self.body: list[Statement] = body

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        for param in self.params:
            node = param.get_node(id)
            if node is not None:
                return node
        node = self.ret_type.get_node(id)
        if node is not None:
            return node
        for stmt in self.body:
            node = stmt.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line

        if self.type_params is not None:
            for type_param in self.type_params:
                tmin, tmax = type_param.get_span()
                min_line = min(min_line, tmin)
                max_line = max(max_line, tmax)

        for param in self.params:
            pmin, pmax = param.get_span()
            min_line = min(min_line, pmin)
            max_line = max(max_line, pmax)

        ret_min, ret_max = self.ret_type.get_span()
        min_line = min(min_line, ret_min)
        max_line = max(max_line, ret_max)

        for stmt in self.body:
            smin, smax = stmt.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)

        return (min_line, max_line)


class Param(Node):
    """A parameter of a function"""

    __slots__ = ["name", "type_annotation", "kind", "line", "id", "symbol"]

    def __init__(self, name: str, type_annotation: TypeAnnotation, line: int) -> None:
        super().__init__("param", line)
        self.name = name
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)


class StructDecl(Declaration):
    """A struct declaration"""

    __slots__ = ["pub", "name", "type_params", "fields", "kind", "line", "id", "symbol"]

    def __init__(
        self,
        pub: bool,
        name: str,
        type_params: Optional[list[TypeParam]],
        fields: list["StructField"],
        line: int,
    ) -> None:
        super().__init__("struct_decl", line)
        self.pub = pub
        self.name = name
        self.type_params = type_params
        self.fields = fields

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        for field in self.fields:
            node = field.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line

        if self.type_params is not None:
            for type_param in self.type_params:
                tmin, tmax = type_param.get_span()
                min_line = min(min_line, tmin)
                max_line = max(max_line, tmax)
        for field in self.fields:
            fmin, fmax = field.get_span()
            min_line = min(min_line, fmin)
            max_line = max(max_line, fmax)
        return (min_line, max_line)


class StructField(Node):
    """A field of a struct"""

    __slots__ = ["pub", "name", "type_annotation", "kind", "line", "id", "symbol"]

    def __init__(
        self, pub: bool, name: str, type_annotation: TypeAnnotation, line: int
    ) -> None:
        super().__init__("struct_field", line)
        self.pub = pub
        self.name = name
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional["Node"]:
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)

    def get_span(self) -> tuple[int, int]:
        tmin, tmax = self.type_annotation.get_span()
        return (self.line, max(self.line, tmax))


class EnumDecl(Declaration):
    """An enum declaration"""

    __slots__ = [
        "pub",
        "name",
        "type_params",
        "variants",
        "kind",
        "line",
        "id",
        "symbol",
    ]

    def __init__(
        self,
        pub: bool,
        name: str,
        type_params: Optional[list[TypeParam]],
        variants: list["EnumVariant"],
        line: int,
    ) -> None:
        super().__init__("enum_decl", line)
        self.pub = pub
        self.name = name
        self.type_params = type_params
        self.variants = variants

    def get_node(self, id: int) -> Optional["Node"]:
        if self.id == id:
            return self
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        for variant in self.variants:
            node = variant.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line

        if self.type_params is not None:
            for type_param in self.type_params:
                tmin, tmax = type_param.get_span()
                min_line = min(min_line, tmin)
                max_line = max(max_line, tmax)

        for variant in self.variants:
            vmin, vmax = variant.get_span()
            min_line = min(min_line, vmin)
            max_line = max(max_line, vmax)
        return (min_line, max_line)


class EnumVariant(Node):
    """An enum variant"""

    __slots__ = ["name", "kind", "line", "id", "symbol"]

    def __init__(self, kind: str, name: str, line: int) -> None:
        super().__init__(kind, line)
        self.name = name


class EnumUnitVariant(EnumVariant):
    """An enum unit variant"""

    def __init__(self, name: str, line: int) -> None:
        super().__init__("enum_unit_variant", name, line)


class EnumTupleVariant(EnumVariant):
    """An enum tuple variant"""

    __slots__ = ["types", "name", "kind", "line", "id", "symbol"]

    def __init__(self, name: str, types: list[TypeAnnotation], line: int) -> None:
        super().__init__("enum_tuple_variant", name, line)
        self.types = types

    def get_node(self, id: int) -> Optional["Node"]:
        if self.id == id:
            return self
        for type_annotation in self.types:
            node = type_annotation.get_node(id)
            if node is not None:
                return node
        return None


class EnumStructVariant(EnumVariant):
    def __init__(self, name: str, fields: list["EnumStructField"], line: int) -> None:
        super().__init__("enum_struct_variant", name, line)
        self.fields = fields

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for field in self.fields:
            node = field.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for field in self.fields:
            fmin, fmax = field.get_span()
            min_line = min(min_line, fmin)
            max_line = max(max_line, fmax)
        return (min_line, max_line)


class EnumStructField(Node):
    def __init__(self, name: str, type_annotation: TypeAnnotation, line: int) -> None:
        super().__init__("enum_struct_field", line)
        self.name = name
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)

    def get_span(self) -> tuple[int, int]:
        tmin, tmax = self.type_annotation.get_span()
        return (self.line, max(self.line, tmax))


class TypeAliasDecl(Declaration):
    def __init__(
        self,
        pub: bool,
        name: str,
        type_params: Optional[list[TypeParam]],
        type_annotation: TypeAnnotation,
        line: int,
    ) -> None:
        super().__init__("type_alias_decl", line)
        self.pub = pub
        self.name = name
        self.type_params = type_params
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        return self.type_annotation.get_node(id)

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_params is not None:
            for type_param in self.type_params:
                tmin, tmax = type_param.get_span()
                min_line = min(min_line, tmin)
                max_line = max(max_line, tmax)
        tmin, tmax = self.type_annotation.get_span()
        min_line = min(min_line, tmin)
        max_line = max(max_line, tmax)
        return (min_line, max_line)


class VarDecl(Statement):
    def __init__(
        self,
        mutable: bool,
        name: str,
        type_annotation: Optional[TypeAnnotation],
        expr: "Expr",
        line: int,
    ) -> None:
        kind = "let_decl" if mutable else "const_decl"
        super().__init__(kind, line)
        self.name = name
        self.type_annotation = type_annotation
        self.expr = expr

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_annotation is not None:
            node = self.type_annotation.get_node(id)
            if node is not None:
                return node
        return self.expr.get_node(id)

    def get_span(self) -> tuple[int, int]:
        expr_min, expr_max = self.expr.get_span()

        return (self.line, max(self.line, expr_max))


class Expr(Statement):
    def __init__(self, kind: str, line: int, type: Optional[Type] = None) -> None:
        super().__init__(kind, line)
        self.type = type


class AssignableExpr(Expr):
    pass


class Assign(Statement):
    def __init__(self, lhs: AssignableExpr, rhs: "Expr", line: int) -> None:
        super().__init__("assign", line)
        self.lhs = lhs
        self.rhs = rhs

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.lhs.get_node(id) or self.rhs.get_node(id)

    def get_span(self) -> tuple[int, int]:
        lhs_min, lhs_max = self.lhs.get_span()
        rhs_min, rhs_max = self.rhs.get_span()
        return (min(lhs_min, rhs_min), max(lhs_max, rhs_max))


class ImplDecl(Declaration):
    def __init__(
        self,
        type_params: Optional[list[TypeParam]],
        trait: Optional[Union[NamedTypeAnnotation, GenericTypeAnnotation]],
        impl_type: Union[NamedTypeAnnotation, GenericTypeAnnotation],
        methods: list[FnDecl],
        line: int,
    ) -> None:
        super().__init__("impl_decl", line)
        self.impl_type = impl_type
        self.methods = methods
        self.trait = trait
        self.type_params = type_params

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        node = self.impl_type.get_node(id)
        if node is not None:
            return node
        for method in self.methods:
            node = method.get_node(id)
            if node is not None:
                return node
        if self.trait is not None:
            node = self.trait.get_node(id)
            if node is not None:
                return node
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_params is not None:
            for type_param in self.type_params:
                tmin, tmax = type_param.get_span()
                min_line = min(min_line, tmin)
                max_line = max(max_line, tmax)
        tmin, tmax = self.impl_type.get_span()
        min_line = min(min_line, tmin)
        max_line = max(max_line, tmax)
        for method in self.methods:
            mmin, mmax = method.get_span()
            min_line = min(min_line, mmin)
            max_line = max(max_line, mmax)
        if self.trait is not None:
            tmin, tmax = self.trait.get_span()
            min_line = min(min_line, tmin)
            max_line = max(max_line, tmax)
        return (min_line, max_line)


class PartialTraitMethod(Declaration):
    """A partial trait method is a method with only a type signaure provided.
    Must be implemented by impls of the trait. Example:

    trait Animal
        fn noise() -> string

    struct Dog
        name: string
        age: int

    impl Animal for Dog
        fn noise() -> string
            return "woof"
    """

    def __init__(
        self,
        pub: bool,
        name: str,
        type_params: Optional[list[TypeParam]],
        params: list[Param],
        ret_type: TypeAnnotation,
        line: int,
    ) -> None:
        super().__init__("partial_trait_method", line)
        self.pub = pub
        self.name = name
        self.type_params = type_params
        self.params = params
        self.ret_type = ret_type

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        for param in self.params:
            node = param.get_node(id)
            if node is not None:
                return node
        return self.ret_type.get_node(id)

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_params is not None:
            for type_param in self.type_params:
                tmin, tmax = type_param.get_span()
                min_line = min(min_line, tmin)
                max_line = max(max_line, tmax)
        for param in self.params:
            pmin, pmax = param.get_span()
            min_line = min(min_line, pmin)
            max_line = max(max_line, pmax)
        ret_min, ret_max = self.ret_type.get_span()
        min_line = min(min_line, ret_min)
        max_line = max(max_line, ret_max)
        return (min_line, max_line)


class TraitDecl(Declaration):
    def __init__(
        self,
        pub: bool,
        name: str,
        type_params: Optional[list[TypeParam]],
        bounds: Optional[list[Union[NamedTypeAnnotation, GenericTypeAnnotation]]],
        methods: list[Union[FnDecl, PartialTraitMethod]],
        line: int,
    ) -> None:
        super().__init__("trait_decl", line)
        self.pub = pub
        self.name = name
        self.type_params = type_params
        self.bounds = bounds
        self.methods = methods

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_params is not None:
            for type_param in self.type_params:
                node = type_param.get_node(id)
                if node is not None:
                    return node
        for method in self.methods:
            node = method.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_params is not None:
            for type_param in self.type_params:
                tmin, tmax = type_param.get_span()
                min_line = min(min_line, tmin)
                max_line = max(max_line, tmax)
        for method in self.methods:
            mmin, mmax = method.get_span()
            min_line = min(min_line, mmin)
            max_line = max(max_line, mmax)
        return (min_line, max_line)


class Return(Statement):
    def __init__(self, expr: Optional["Expr"], line: int) -> None:
        super().__init__("return", line)
        self.expr = expr

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.expr.get_node(id) if self.expr is not None else None

    def get_span(self) -> tuple[int, int]:
        if self.expr is None:
            return (self.line, self.line)
        return self.expr.get_span()


class Else(Statement):
    def __init__(self, body: list[Statement], line: int) -> None:
        super().__init__("else", line)
        self.body = body

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for stmt in self.body:
            node = stmt.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for stmt in self.body:
            smin, smax = stmt.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class If(Statement):
    def __init__(
        self,
        cond: "Expr",
        body: list[Statement],
        else_body: Optional[list[Statement]],
        line: int,
    ) -> None:
        super().__init__("if", line)
        self.cond = cond
        self.body = body
        if else_body is not None:
            self.else_body = Else(else_body, line)
        else:
            self.else_body = None

    # get node by id
    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.cond.get_node(id)
        if node is not None:
            return node
        for stmt in self.body:
            node = stmt.get_node(id)
            if node is not None:
                return node
        if self.else_body is not None:
            node = self.else_body.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for stmt in self.body:
            smin, smax = stmt.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        if self.else_body is not None:
            smin, smax = self.else_body.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class While(Statement):
    def __init__(self, cond: "Expr", body: list[Statement], line: int) -> None:
        super().__init__("while", line)
        self.cond = cond
        self.body = body

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.cond.get_node(id)
        if node is not None:
            return node
        for stmt in self.body:
            node = stmt.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for stmt in self.body:
            smin, smax = stmt.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class Loop(Statement):
    def __init__(self, body: list[Statement], line: int) -> None:
        super().__init__("loop", line)
        self.body = body

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for stmt in self.body:
            node = stmt.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for stmt in self.body:
            smin, smax = stmt.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class Break(Statement):
    def __init__(self, line: int) -> None:
        super().__init__("break", line)


class Continue(Statement):
    def __init__(self, line: int) -> None:
        super().__init__("continue", line)


class Integer(Expr):
    def __init__(self, value: int, line: int) -> None:
        super().__init__("integer", line, IntType())
        self.value = value


class Float(Expr):
    def __init__(self, value: float, line: int) -> None:
        super().__init__("float", line, FloatType())
        self.value = value


class String(Expr):
    def __init__(self, value: str, line: int) -> None:
        super().__init__("string", line, StringType())
        self.value = value


class Char(Expr):
    def __init__(self, value: str, line: int) -> None:
        super().__init__("char", line, CharType())
        self.value = value


class Bool(Expr):
    def __init__(self, value: bool, line: int) -> None:
        super().__init__("bool", line, BoolType())
        self.value = value


class ArrayExpr(Expr):
    def __init__(self, elems: list[Expr], line: int) -> None:
        super().__init__("array", line)
        self.elems = elems

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for elem in self.elems:
            node = elem.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for elem in self.elems:
            emin, emax = elem.get_span()
            min_line = min(min_line, emin)
            max_line = max(max_line, emax)
        return (min_line, max_line)


class TupleExpr(Expr):
    def __init__(self, elems: list[Expr], line: int) -> None:
        super().__init__("tuple", line)
        self.elems = elems

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for elem in self.elems:
            node = elem.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for elem in self.elems:
            emin, emax = elem.get_span()
            min_line = min(min_line, emin)
            max_line = max(max_line, emax)
        return (min_line, max_line)


class FieldInit(Node):
    def __init__(self, name: str, expr: Expr, line: int) -> None:
        super().__init__("field_init", line)
        self.name = name
        self.expr = expr

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.expr.get_node(id)

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        expr_min, expr_max = self.expr.get_span()
        return (min(min_line, expr_min), max(max_line, expr_max))


class StructExpr(Expr):
    def __init__(
        self,
        name: str,
        type_args: Optional[list[TypeAnnotation]],
        fields: list[FieldInit],
        line: int,
    ) -> None:
        super().__init__("struct_expr", line)
        self.name = name
        self.type_args = type_args
        self.fields = fields

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_args is not None:
            for type_arg in self.type_args:
                node = type_arg.get_node(id)
                if node is not None:
                    return node
        for field in self.fields:
            node = field.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_args is not None:
            for type_arg in self.type_args:
                type_arg_min, type_arg_max = type_arg.get_span()
                min_line = min(min_line, type_arg_min)
                max_line = max(max_line, type_arg_max)
        for field in self.fields:
            smin, smax = field.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class EnumStructExpr(Expr):
    def __init__(
        self,
        name: str,
        type_args: Optional[list[TypeAnnotation]],
        unit: str,
        fields: list[FieldInit],
        line: int,
    ) -> None:
        super().__init__("enum_struct_expr", line)
        self.name = name
        self.type_args = type_args
        self.unit = unit
        self.fields = fields

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_args is not None:
            for type_arg in self.type_args:
                node = type_arg.get_node(id)
                if node is not None:
                    return node
        for field in self.fields:
            node = field.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_args is not None:
            for type_arg in self.type_args:
                type_arg_min, type_arg_max = type_arg.get_span()
                min_line = min(min_line, type_arg_min)
                max_line = max(max_line, type_arg_max)
        for field in self.fields:
            smin, smax = field.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class EnumTupleExpr(Expr):
    def __init__(
        self,
        name: str,
        type_args: Optional[list[TypeAnnotation]],
        unit: str,
        elems: list[Expr],
        line: int,
    ) -> None:
        super().__init__("enum_tuple_expr", line)
        self.name = name
        self.type_args = type_args
        self.unit = unit
        self.elems = elems

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_args is not None:
            for type_arg in self.type_args:
                node = type_arg.get_node(id)
                if node is not None:
                    return node
        for elem in self.elems:
            node = elem.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_args is not None:
            for type_arg in self.type_args:
                type_arg_min, type_arg_max = type_arg.get_span()
                min_line = min(min_line, type_arg_min)
                max_line = max(max_line, type_arg_max)
        for elem in self.elems:
            emin, emax = elem.get_span()
            min_line = min(min_line, emin)
            max_line = max(max_line, emax)
        return (min_line, max_line)


class EnumUnitExpr(Expr):
    def __init__(
        self, name: str, type_args: Optional[list[TypeAnnotation]], unit: str, line: int
    ) -> None:
        super().__init__("enum_unit_expr", line)
        self.name = name
        self.type_args = type_args
        self.unit = unit

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type_args is not None:
            for type_arg in self.type_args:
                node = type_arg.get_node(id)
                if node is not None:
                    return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        if self.type_args is not None:
            for type_arg in self.type_args:
                type_arg_min, type_arg_max = type_arg.get_span()
                min_line = min(min_line, type_arg_min)
                max_line = max(max_line, type_arg_max)
        return (min_line, max_line)


class Ident(AssignableExpr):
    def __init__(self, name: str, line: int) -> None:
        super().__init__("ident", line)
        self.name = name

    @property
    def type(
        self,
    ) -> Optional[Type]:
        return self.symbol.type if self.symbol else None

    @type.setter
    def type(self, type: Type) -> None:
        if self.symbol:
            self.symbol.type = type


class Call(Expr):
    def __init__(
        self,
        callee: Expr,
        type_args: Optional[list[TypeAnnotation]],
        args: list[Expr],
        line: int,
    ) -> None:
        super().__init__("call", line)
        self.callee = callee
        self.type_args = type_args
        self.args = args

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.callee.get_node(id)
        if node is not None:
            return node
        if self.type_args is not None:
            for type_arg in self.type_args:
                node = type_arg.get_node(id)
                if node is not None:
                    return node
        for arg in self.args:
            node = arg.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        callee_min, callee_max = self.callee.get_span()
        min_line = min(min_line, callee_min)
        max_line = max(max_line, callee_max)
        if self.type_args is not None:
            for type_arg in self.type_args:
                type_arg_min, type_arg_max = type_arg.get_span()
                min_line = min(min_line, type_arg_min)
                max_line = max(max_line, type_arg_max)
        for arg in self.args:
            arg_min, arg_max = arg.get_span()
            min_line = min(min_line, arg_min)
            max_line = max(max_line, arg_max)
        return (min_line, max_line)


class GetIndex(AssignableExpr):
    def __init__(self, obj: Expr, index: Expr, line: int) -> None:
        super().__init__("getindex", line)
        self.obj = obj
        self.index = index

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.obj.get_node(id)
        if node is not None:
            return node
        node = self.index.get_node(id)
        if node is not None:
            return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        obj_min, obj_max = self.obj.get_span()
        min_line = min(min_line, obj_min)
        max_line = max(max_line, obj_max)
        index_min, index_max = self.index.get_span()
        min_line = min(min_line, index_min)
        max_line = max(max_line, index_max)
        return (min_line, max_line)


class AccessField(AssignableExpr):
    def __init__(self, obj: Expr, attr: str, line: int) -> None:
        super().__init__("access_field", line)
        self.obj = obj
        self.attr = attr

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.obj.get_node(id)
        if node is not None:
            return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        obj_min, obj_max = self.obj.get_span()
        min_line = min(min_line, obj_min)
        max_line = max(max_line, obj_max)
        return (min_line, max_line)


class CallMethod(Expr):
    def __init__(
        self,
        obj: Expr,
        type_args: Optional[list[TypeAnnotation]],
        attr: str,
        args: list[Expr],
        line: int,
    ) -> None:
        super().__init__("call_method", line)
        self.obj = obj
        self.type_args = type_args
        self.attr = attr
        self.args = args

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.obj.get_node(id)
        if node is not None:
            return node
        if self.type_args is not None:
            for type_arg in self.type_args:
                node = type_arg.get_node(id)
                if node is not None:
                    return node
        for arg in self.args:
            node = arg.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        obj_min, obj_max = self.obj.get_span()
        min_line = min(min_line, obj_min)
        max_line = max(max_line, obj_max)
        if self.type_args is not None:
            for type_arg in self.type_args:
                type_arg_min, type_arg_max = type_arg.get_span()
                min_line = min(min_line, type_arg_min)
                max_line = max(max_line, type_arg_max)
        for arg in self.args:
            arg_min, arg_max = arg.get_span()
            min_line = min(min_line, arg_min)
            max_line = max(max_line, arg_max)
        return (min_line, max_line)


class BinaryOp(Expr):
    def __init__(self, op: str, lhs: Expr, rhs: Expr, line: int) -> None:
        super().__init__("binary_op", line)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.lhs.get_node(id)
        if node is not None:
            return node
        return self.rhs.get_node(id)

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        lhs_min, lhs_max = self.lhs.get_span()
        min_line = min(min_line, lhs_min)
        max_line = max(max_line, lhs_max)
        rhs_min, rhs_max = self.rhs.get_span()
        min_line = min(min_line, rhs_min)
        max_line = max(max_line, rhs_max)
        return (min_line, max_line)


class UnaryOp(Expr):
    def __init__(self, op: str, operand: Expr, line: int) -> None:
        super().__init__("unary_op", line)
        self.op = op
        self.operand = operand

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.operand.get_node(id)

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        operand_min, operand_max = self.operand.get_span()
        min_line = min(min_line, operand_min)
        max_line = max(max_line, operand_max)
        return (min_line, max_line)
