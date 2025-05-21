# Expressive AST we convert the Lark ast into
from typing import Dict, Optional, Union, List, Set

from .symbol import Symbol
from .types import BoolType, CharType, FloatType, IntType, StringType, Type

class Modules:
    """A collection of modules"""
    
    def __init__(self) -> None:
        self.modules: Dict[str, Module] = {}
        self.nodes: Dict[int, Node] = {}
        
    def get_module(self, name: str) -> Optional["Module"]:
        return self.modules.get(name)
    
    def add_module(self, module: "Module") -> None:
        if module.file_path is None:
            raise ValueError("Module has no file path")
        self.modules[module.file_path] = module

    def get_node(self, id: int) -> Optional["Node"]:
        if id in self.nodes:
            return self.nodes[id]
        
        for module in self.modules.values():
            node = module.get_node(id)
            if node is not None:
                self.nodes[id] = node
                return node
        return None

    # get the module that contains the node id
    def get_module_with_node(self, id: int) -> Optional["Module"]:
        for module in self.modules.values():
            if module.get_node(id) is not None:
                return module
        return None


TopLevelNode = Union["Import", "ExportSpec", "Declaration"]

class Module:
    """
    Represents a module. A module is a collection of declarations

    Attributes:
        file_path: The path to the file that the program is in
        top_level_nodes: A list of top level nodes in the program
        source: The source code of the program
        imports: A dictionary of imports by name mapping to their symbol once its set
        exports: A dictionary of exports by name
        nodes: A dictionary of nodes by id to improve performance when grabbing nodes by id a lot
    """

    __slots__ = ["file_path", "top_level_nodes", "source", "imports", "exports", "nodes"]

    def __init__(
        self, source: Optional[str] = None, file_path: Optional[str] = None
    ) -> None:
        self.file_path: Optional[str] = file_path
        self.top_level_nodes: List[TopLevelNode] = []
        self.source: Optional[str] = source
        self.imports: Dict[str, Symbol] = {}
        self.exports: Dict[str, Symbol] = {}
        # memoize nodes by id to improve perf when grabbing nodes by id a lot
        self.nodes: Dict[int, Node] = {}

    def push(self, top_level_node: TopLevelNode):
        """Add a top level node to the program"""
        self.top_level_nodes.append(top_level_node)

    # get a node by id
    def get_node(self, id: int) -> Optional["Node"]:
        """Get a node by id. Memoized for performance"""
        # check memoized nodes first
        # saves us time over traversing the entire program
        if id in self.nodes:
            return self.nodes[id]

        # check all top level nodes
        for top_level_node in self.top_level_nodes:
            node = top_level_node.get_node(id)
            if node is not None:
                self.nodes[id] = node
                return node
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


class Import(Node):
    """Imports a module
    
    Attributes:
        module: The name of the module to import
        targets: The targets to import from the module
    """

    __slots__ = ["module", "targets", "line", "id", "symbol"]
    

    def __init__(self, module: str, targets: List[str], line: int) -> None:
        super().__init__(line)
        self.module = module
        self.targets: List[str] = targets
        


class ExportSpec(Node):
    """A specification of what to export from a module"""

    __slots__ = ["exports", "line", "id", "symbol"]

    def __init__(self, exports: Set[str], line: int) -> None:
        super().__init__(line)
        self.exports = exports


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


class GenericTypeAnnotation(TypeAnnotation):
    """
    A type with generic parameters

    Attributes:
        name: The name of the type
        type_args: The type arguments of the type
    """

    __slots__ = ["name", "type_args", "line", "id", "symbol"]

    def __init__(self, name: str, type_args: List[TypeAnnotation], line: int) -> None:
        super().__init__(line)
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
            pmin, pmax = type_arg.get_span()
            min_line = min(min_line, pmin)
            max_line = max(max_line, pmax)
        return (min_line, max_line)


class ArrayTypeAnnotation(TypeAnnotation):
    """
    A type annotation for an array type

    Attributes:
        elem_type: The type of the elements in the array
    """

    __slots__ = ["elem_type", "line", "id", "symbol"]

    def __init__(self, elem_type: TypeAnnotation, size: "Expr", line: int) -> None:
        super().__init__(line)
        self.elem_type = elem_type
        self.size = size

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.elem_type.get_node(id)
        if node is not None:
            return node
        return self.size.get_node(id)

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        e_min, e_max = self.elem_type.get_span()
        min_line = min(min_line, e_min)
        max_line = max(max_line, e_max)
        return (min_line, max_line)


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


class TypeParam(Node):
    """A type parameter"""

    __slots__ = ["name", "line", "id", "symbol"]

    def __init__(self, name: str, line: int) -> None:
        super().__init__(line)
        self.name = name


class FnDecl(Declaration, Statement):
    """A function declaration

    Attributes:
        name: The name of the function
        type_params: The generic parameters of the function
        params: The parameters of the function
        ret_type: The type of the return value of the function
        body: The body of the function
    """

    __slots__ = [
        "name",
        "type_params",
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
        type_params: List[TypeParam],
        params: List["Param"],
        ret_type: TypeAnnotation,
        body: List[Statement],
        line: int,
    ) -> None:
        super().__init__(line)
        self.name: str = name
        self.type_params: List[TypeParam] = type_params
        self.params: List["Param"] = params
        self.ret_type: TypeAnnotation = ret_type
        self.body: List[Statement] = body

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for param in self.type_params:
            node = param.get_node(id)
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


class StructDecl(Declaration):
    """A struct declaration"""

    __slots__ = ["name", "type_params", "fields", "line", "id", "symbol"]

    def __init__(
        self,
        name: str,
        type_params: List[TypeParam],
        fields: List[StructField],
        line: int,
    ) -> None:
        super().__init__(line)
        self.name = name
        self.type_params = type_params
        self.fields = fields

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for param in self.type_params:
            node = param.get_node(id)
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

        for param in self.type_params:
            pmin, pmax = param.get_span()
            min_line = min(min_line, pmin)
            max_line = max(max_line, pmax)

        for field in self.fields:
            fmin, fmax = field.get_span()
            min_line = min(min_line, fmin)
            max_line = max(max_line, fmax)
        return (min_line, max_line)


class UnionField(Node):
    """A super type for all union fields"""

    pass


class UnionStructVariant(UnionField):
    """A union field that is a struct variant"""

    __slots__ = ["name", "fields", "line", "id", "symbol"]

    def __init__(self, name: str, fields: List[StructField], line: int) -> None:
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


class UnionTupleVariant(UnionField):
    """A union field that is a tuple variant"""

    __slots__ = ["name", "types", "line", "id", "symbol"]

    def __init__(self, name: str, types: List[TypeAnnotation], line: int) -> None:
        super().__init__(line)
        self.name = name
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


class UnionTagVariant(UnionField):
    """A union field that is a tag variant"""

    __slots__ = ["name", "line", "id", "symbol"]

    def __init__(self, name: str, line: int) -> None:
        super().__init__(line)
        self.name = name


class UnionDecl(Declaration):
    """A union declaration"""

    __slots__ = ["name", "type_params", "fields", "line", "id", "symbol"]

    def __init__(
        self,
        name: str,
        type_params: List[TypeParam],
        fields: List[UnionField],
        line: int,
    ) -> None:
        super().__init__(line)
        self.name = name
        self.type_params = type_params
        self.fields = fields

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for param in self.type_params:
            node = param.get_node(id)
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
        for param in self.type_params:
            pmin, pmax = param.get_span()
            min_line = min(min_line, pmin)
            max_line = max(max_line, pmax)

        for field in self.fields:
            fmin, fmax = field.get_span()
            min_line = min(min_line, fmin)
            max_line = max(max_line, fmax)
        return (min_line, max_line)


class TypeAliasDecl(Declaration):
    """
    Represents a type alias declaration in the program.

    Attributes:
        name (str): The name of the type alias.
        type_annotation (TypeAnnotation): The type annotation associated with the alias.
        type_params (List[TypeParam]): The generic parameters of the type alias.
        line (int): The line number where the alias is declared.
    """

    def __init__(
        self,
        name: str,
        type_params: List[TypeParam],
        type_annotation: TypeAnnotation,
        line: int,
    ) -> None:
        """
        Initializes a TypeAliasDecl instance.

        Args:
            name (str): The name of the type alias.
            type_annotation (TypeAnnotation): The type annotation associated with the alias.
            generic_params (List[GenericParam]): The generic parameters of the type alias.
            line (int): The line number where the alias is declared.
        """
        super().__init__(line)
        self.name = name
        self.type_params = type_params
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
        for param in self.type_params:
            node = param.get_node(id)
            if node is not None:
                return node
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
        for param in self.type_params:
            pmin, pmax = param.get_span()
            min_line = min(min_line, pmin)
            max_line = max(max_line, pmax)
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
        type_args: List[TypeAnnotation],
        args: List[Expr],
        line: int,
    ) -> None:
        super().__init__(line)
        self.callee = callee
        self.type_args = type_args
        self.args = args

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.callee.get_node(id)
        if node is not None:
            return node
        for type_arg in self.type_args:
            node = type_arg.get_node(id)
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


class FieldInit(Node):
    def __init__(self, name: str, expr: Expr, line: int) -> None:
        super().__init__(line)
        self.name = name
        self.expr = expr

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.expr.get_node(id)


class StructExpr(Expr):
    def __init__(self, fields: List[FieldInit], line: int) -> None:
        super().__init__(line)
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
