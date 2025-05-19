# Expressive AST we convert the Lark ast into
from typing import Dict, Optional, Union

from .symbol import Symbol
from .types import BoolType, CharType, FloatType, IntType, StringType, Type


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
        line: The line number of the node
        id: The id of the node
        symbol: The symbol associated with the node
    """

    __slots__ = ["line", "id", "symbol"]

    _next_id = 0  # class variable to track the next available ID

    def __init__(self, line: int) -> None:
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
            raise RuntimeError(f"Node {self.__class__.__name__} has no symbol")
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

    __slots__ = ["name", "line", "id", "symbol"]

    def __init__(self, name: str, line: int) -> None:
        super().__init__(line)
        self.name = name


class ArrayTypeAnnotation(TypeAnnotation):
    """
    A type annotation for an array type

    Attributes:
        elem_type: The type of the elements in the array
    """

    __slots__ = ["elem_type", "line", "id", "symbol"]

    def __init__(self, elem_type: TypeAnnotation, line: int) -> None:
        super().__init__(line)
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

    __slots__ = ["elem_types", "line", "id", "symbol"]

    def __init__(self, elem_types: list[TypeAnnotation], line: int) -> None:
        super().__init__(line)
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

    __slots__ = ["params", "ret_type", "line", "id", "symbol"]

    def __init__(
        self, params: list[TypeAnnotation], ret_type: TypeAnnotation, line: int
    ) -> None:
        super().__init__(line)
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

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for param in self.params:
            pmin, pmax = param.get_span()
            min_line = min(min_line, pmin)
            max_line = max(max_line, pmax)
        rmin, rmax = self.ret_type.get_span()
        min_line = min(min_line, rmin)
        max_line = max(max_line, rmax)
        return (min_line, max_line)


class StructuralTypeAnnotation(TypeAnnotation):
    """
    A type annotation for a structural type

    Attributes:
        fields: The fields of the structural type
    """

    __slots__ = ["fields", "line", "id", "symbol"]

    def __init__(self, fields: Dict[str, TypeAnnotation], line: int) -> None:
        super().__init__(line)
        self.fields = fields

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for field in self.fields.values():
            node = field.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for field in self.fields.values():
            fmin, fmax = field.get_span()
            min_line = min(min_line, fmin)
            max_line = max(max_line, fmax)
        return (min_line, max_line)


class UnionTypeAnnotation(TypeAnnotation):
    """
    A type annotation for a union type

    Attributes:
        types: The types of the union
    """

    __slots__ = ["types", "line", "id", "symbol"]

    def __init__(self, types: list[TypeAnnotation], line: int) -> None:
        super().__init__(line)
        self.types = types

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for type in self.types:
            node = type.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for type in self.types:
            tmin, tmax = type.get_span()
            min_line = min(min_line, tmin)
            max_line = max(max_line, tmax)
        return (min_line, max_line)


class IntersectionTypeAnnotation(TypeAnnotation):
    """
    A type annotation for an intersection type

    Attributes:
        types: The types of the intersection
    """

    __slots__ = ["types", "line", "id", "symbol"]

    def __init__(self, types: list[TypeAnnotation], line: int) -> None:
        super().__init__(line)
        self.types = types

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for type in self.types:
            node = type.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for type in self.types:
            tmin, tmax = type.get_span()
            min_line = min(min_line, tmin)
            max_line = max(max_line, tmax)
        return (min_line, max_line)


class SubtractedTypeAnnotation(TypeAnnotation):
    """
    A type annotation for a subtracted type

    Attributes:
        base_type: The base type
        subtracted_type: The type to subtract from the base type
    """

    __slots__ = ["base_type", "subtracted_type", "line", "id", "symbol"]

    def __init__(
        self, base_type: TypeAnnotation, subtracted_type: TypeAnnotation, line: int
    ) -> None:
        super().__init__(line)
        self.base_type = base_type
        self.subtracted_type = subtracted_type

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.base_type.get_node(id)
        if node is not None:
            return node
        return self.subtracted_type.get_node(id)

    def get_span(self) -> tuple[int, int]:
        bmin, bmax = self.base_type.get_span()
        smin, smax = self.subtracted_type.get_span()
        return (min(bmin, smin), max(bmax, smax))


class FnDecl(Declaration, Statement):
    """A function declaration

    Attributes:
        name: The name of the function
        params: The parameters of the function
        ret_type: The type of the return value of the function
        body: The body of the function
    """

    __slots__ = [
        "name",
        "params",
        "ret_type",
        "body",
        "line",
        "id",
        "symbol",
    ]

    def __init__(
        self,
        name: str,
        params: list["Param"],
        ret_type: TypeAnnotation,
        body: list[Statement],
        line: int,
    ) -> None:
        super().__init__(line)
        self.name: str = name
        self.params: list["Param"] = params
        self.ret_type: TypeAnnotation = ret_type
        self.body: list[Statement] = body

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
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

    __slots__ = ["name", "type_annotation", "line", "id", "symbol"]

    def __init__(self, name: str, type_annotation: TypeAnnotation, line: int) -> None:
        super().__init__(line)
        self.name = name
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)


class StructDecl(Declaration):
    """A struct declaration"""

    __slots__ = ["name", "fields", "line", "id", "symbol"]

    def __init__(
        self,
        name: str,
        fields: list["StructField"],
        line: int,
    ) -> None:
        super().__init__(line)
        self.name = name
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


class StructField(Node):
    """A field of a struct"""

    __slots__ = ["name", "type_annotation", "line", "id", "symbol"]

    def __init__(self, name: str, type_annotation: TypeAnnotation, line: int) -> None:
        super().__init__(line)
        self.name = name
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional["Node"]:
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)

    def get_span(self) -> tuple[int, int]:
        tmin, tmax = self.type_annotation.get_span()
        return (self.line, max(self.line, tmax))


class TypeAliasDecl(Declaration):
    """
    Represents a type alias declaration in the program.

    Attributes:
        name (str): The name of the type alias.
        type_annotation (TypeAnnotation): The type annotation associated with the alias.
        line (int): The line number where the alias is declared.
    """

    def __init__(
        self,
        name: str,
        type_annotation: TypeAnnotation,
        line: int,
    ) -> None:
        """
        Initializes a TypeAliasDecl instance.

        Args:
            name (str): The name of the type alias.
            type_annotation (TypeAnnotation): The type annotation associated with the alias.
            line (int): The line number where the alias is declared.
        """
        super().__init__(line)
        self.name = name
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional[Node]:
        """
        Retrieves a node by its ID.

        Args:
            id (int): The ID of the node to retrieve.

        Returns:
            Optional[Node]: The node with the specified ID, or None if not found.
        """
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)

    def get_span(self) -> tuple[int, int]:
        """
        Gets the span of the type alias declaration.

        Returns:
            tuple[int, int]: A tuple containing the start and end line numbers of the declaration.
        """
        min_line = self.line
        max_line = self.line
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
        super().__init__(line)
        self.mutable = mutable
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
    def __init__(self, line: int, type: Optional[Type] = None) -> None:
        super().__init__(line)
        self.type = type


class AssignableExpr(Expr):
    pass


class Assign(Statement):
    def __init__(self, lhs: AssignableExpr, rhs: "Expr", line: int) -> None:
        super().__init__(line)
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


class Return(Statement):
    def __init__(self, expr: Optional["Expr"], line: int) -> None:
        super().__init__(line)
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
        super().__init__(line)
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
        super().__init__(line)
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
        super().__init__(line)
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
        super().__init__(line)
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
        super().__init__(line)


class Continue(Statement):
    def __init__(self, line: int) -> None:
        super().__init__(line)


class Integer(Expr):
    def __init__(self, value: int, line: int) -> None:
        super().__init__(line, IntType())
        self.value = value


class Float(Expr):
    def __init__(self, value: float, line: int) -> None:
        super().__init__(line, FloatType())
        self.value = value


class String(Expr):
    def __init__(self, value: str, line: int) -> None:
        super().__init__(line, StringType())
        self.value = value


class Char(Expr):
    def __init__(self, value: str, line: int) -> None:
        super().__init__(line, CharType())
        self.value = value


class Bool(Expr):
    def __init__(self, value: bool, line: int) -> None:
        super().__init__(line, BoolType())
        self.value = value


class ArrayExpr(Expr):
    def __init__(self, elems: list[Expr], line: int) -> None:
        super().__init__(line)
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
        super().__init__(line)
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
        super().__init__(line)
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


class Ident(AssignableExpr):
    def __init__(self, name: str, line: int) -> None:
        super().__init__(line)
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
        args: list[Expr],
        line: int,
    ) -> None:
        super().__init__(line)
        self.callee = callee
        self.args = args

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.callee.get_node(id)
        if node is not None:
            return node
        for arg in self.args:
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
        for arg in self.args:
            arg_min, arg_max = arg.get_span()
            min_line = min(min_line, arg_min)
            max_line = max(max_line, arg_max)
        return (min_line, max_line)


class GetIndex(AssignableExpr):
    def __init__(self, obj: Expr, index: Expr, line: int) -> None:
        super().__init__(line)
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
        super().__init__(line)
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


class BinaryOp(Expr):
    def __init__(self, op: str, lhs: Expr, rhs: Expr, line: int) -> None:
        super().__init__(line)
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
        super().__init__(line)
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
