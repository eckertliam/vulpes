# Expressive AST we convert the Lark ast into
from typing import Dict, Optional, Union

from .symbol import Symbol
from .types import BoolType, CharType, FloatType, IntType, StringType, Type


class Program:
    def __init__(self, source: Optional[str] = None) -> None:
        self.declarations = []
        self.source = source
        # memoize nodes by id to improve perf when grabbing nodes by id a lot
        self.nodes: Dict[int, Node] = {}

    def push(self, declaration: "Declaration"):
        self.declarations.append(declaration)

    # get a node by id
    def get_node(self, id: int) -> Optional["Node"]:
        # check memoized nodes first
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
        for declaration in self.declarations:
            if declaration.get_node(id) is not None:
                return declaration
        return None


class Node:
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
        if self.id == id:
            return self
        else:
            return None

    def get_span(self) -> tuple[int, int]:
        return (self.line, self.line)


class Declaration(Node):
    pass


class Statement(Node):
    pass


class TypeAnnotation(Node):
    pass


class NamedTypeAnnotation(TypeAnnotation):
    def __init__(self, name: str, line: int) -> None:
        super().__init__("named_type", line)
        self.name = name


class ArrayTypeAnnotation(TypeAnnotation):
    def __init__(self, elem_type: TypeAnnotation, line: int) -> None:
        super().__init__("array_type", line)
        self.elem_type = elem_type

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        else:
            return self.elem_type.get_node(id)


class TupleTypeAnnotation(TypeAnnotation):
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


class FnDecl(Declaration, Statement):
    def __init__(
        self,
        pub: bool,
        name: str,
        params: list["Param"],
        ret_type: TypeAnnotation,
        body: list[Statement],
        line: int,
    ) -> None:
        super().__init__("fn_decl", line)
        self.pub: bool = pub
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
    def __init__(self, name: str, type_annotation: TypeAnnotation, line: int) -> None:
        super().__init__("param", line)
        self.name = name
        self.type_annotation = type_annotation
        self.line = line

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)


class StructDecl(Declaration):
    def __init__(
        self, pub: bool, name: str, fields: list["StructField"], line: int
    ) -> None:
        super().__init__("struct_decl", line)
        self.pub = pub
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
    def __init__(
        self, pub: bool, name: str, variants: list["EnumVariant"], line: int
    ) -> None:
        super().__init__("enum_decl", line)
        self.pub = pub
        self.name = name
        self.variants = variants

    def get_node(self, id: int) -> Optional["Node"]:
        if self.id == id:
            return self
        for variant in self.variants:
            node = variant.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for variant in self.variants:
            vmin, vmax = variant.get_span()
            min_line = min(min_line, vmin)
            max_line = max(max_line, vmax)
        return (min_line, max_line)


class EnumVariant(Node):
    def __init__(self, kind: str, name: str, line: int) -> None:
        super().__init__(kind, line)
        self.name = name


class EnumUnitVariant(EnumVariant):
    def __init__(self, name: str, line: int) -> None:
        super().__init__("enum_unit_variant", name, line)


class EnumTupleVariant(EnumVariant):
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
        self, pub: bool, name: str, type_annotation: TypeAnnotation, line: int
    ) -> None:
        super().__init__("type_alias_decl", line)
        self.pub = pub
        self.name = name
        self.type_annotation = type_annotation

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type_annotation.get_node(id)

    def get_span(self) -> tuple[int, int]:
        tmin, tmax = self.type_annotation.get_span()
        return (self.line, max(self.line, tmax))


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
    def __init__(self, name: str, methods: list[FnDecl], line: int, trait: Optional[str] = None) -> None:
        super().__init__("impl_decl", line)
        self.name = name
        self.methods = methods
        self.trait = trait

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for method in self.methods:
            node = method.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
        for method in self.methods:
            mmin, mmax = method.get_span()
            min_line = min(min_line, mmin)
            max_line = max(max_line, mmax)
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
        self, pub: bool, name: str, params: list[Param], ret_type: TypeAnnotation, line: int
    ) -> None:
        super().__init__("partial_trait_method", line)
        self.pub = pub
        self.name = name
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
        ret_min, ret_max = self.ret_type.get_span()
        min_line = min(min_line, ret_min)
        max_line = max(max_line, ret_max)
        return (min_line, max_line)


class TraitDecl(Declaration):
    def __init__(
        self,
        pub: bool,
        name: str,
        methods: list[Union[FnDecl, PartialTraitMethod]],
        line: int,
    ) -> None:
        super().__init__("trait_decl", line)
        self.pub = pub
        self.name = name
        self.methods = methods

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        for method in self.methods:
            node = method.get_node(id)
            if node is not None:
                return node
        return None

    def get_span(self) -> tuple[int, int]:
        min_line = self.line
        max_line = self.line
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
    def __init__(self, name: str, fields: list[FieldInit], line: int) -> None:
        super().__init__("struct_expr", line)
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
            smin, smax = field.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class EnumStructExpr(Expr):
    def __init__(
        self, name: str, unit: str, fields: list[FieldInit], line: int
    ) -> None:
        super().__init__("enum_struct_expr", line)
        self.name = name
        self.unit = unit
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
            smin, smax = field.get_span()
            min_line = min(min_line, smin)
            max_line = max(max_line, smax)
        return (min_line, max_line)


class EnumTupleExpr(Expr):
    def __init__(self, name: str, unit: str, elems: list[Expr], line: int) -> None:
        super().__init__("enum_tuple_expr", line)
        self.name = name
        self.unit = unit
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


class EnumUnitExpr(Expr):
    def __init__(self, name: str, unit: str, line: int) -> None:
        super().__init__("enum_unit_expr", line)
        self.name = name
        self.unit = unit


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
    def __init__(self, callee: Expr, args: list[Expr], line: int) -> None:
        super().__init__("call", line)
        self.callee = callee
        self.args = args

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.callee.get_node(id)
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
    def __init__(self, obj: Expr, attr: str, args: list[Expr], line: int) -> None:
        super().__init__("call_method", line)
        self.obj = obj
        self.attr = attr
        self.args = args

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        node = self.obj.get_node(id)
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
