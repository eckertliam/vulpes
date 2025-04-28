# This is a messy prototype of a Cuss compiler.
# It is a loose example of what the final C++ compiler will look like.
# It is not intended to be a full implementation of the language.
# It is only intended to be a minimal proof of concept.

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from lark import Lark, Tree, Token, Transformer
from lark.indenter import Indenter

# TODO: add tuples to the grammar while avoiding collisions
cuss_grammar = r"""
    %import common.INT
    %import common.FLOAT 
    %import common.ESCAPED_STRING -> STRING
    %import common.WS_INLINE
    
    %ignore WS_INLINE
    %declare _INDENT _DEDENT
    
    start: [_NL*] definition_list
    
    definition_list: (definition (_NL* definition)* [_NL*])?
    
    ?definition: fn_def
                | enum_def
                | struct_def
                | type_alias
                | impl_def
                
    statement_list: (statement (_NL* statement)* [_NL*])?
    
    statement: fn_def
             | expr -> expr_stmt
             | "return" expr -> return_stmt
             | const_def
             | let_def
             | assign_stmt
             | if_stmt
             | while_stmt
             | loop_stmt
             | break_stmt
             | continue_stmt

    if_stmt: "if" expr _NL _INDENT statement_list _DEDENT ["else" (if_stmt | _NL _INDENT statement_list _DEDENT)] -> if_stmt
    while_stmt: "while" expr _NL _INDENT statement_list _DEDENT -> while_stmt
    loop_stmt: "loop" _NL _INDENT statement_list _DEDENT -> loop_stmt
    break_stmt: BREAK -> break_stmt
    continue_stmt: CONTINUE -> continue_stmt
    
    const_def: "const" IDENT [":" type_annotation] "=" expr
    let_def: "let" IDENT [":" type_annotation] "=" expr
    assign_stmt: (IDENT | getindex | getattr) "=" expr
    
    type_alias: [PUB] "type" IDENT "=" type_annotation

    fn_def: [PUB] "fn" IDENT "(" param_list ")" "->" type_annotation _NL _INDENT statement_list _DEDENT
    
    param_list: [param ("," param)*]
    
    param: IDENT ":" type_annotation
    
    enum_def: [PUB] "enum" IDENT _NL enum_variant_list
    
    ?enum_variant_list: [_INDENT (enum_variant _NL)* _DEDENT]
    
    enum_tuple_variant: IDENT "(" [type_annotation ("," type_annotation)*] ")"

    enum_unit_variant: IDENT
    
    enum_struct_variant: IDENT "(" enum_struct_field ("," enum_struct_field)* ")"

    enum_struct_field: IDENT ":" type_annotation

    enum_variant: enum_tuple_variant -> tuple_enum_variant
        | enum_unit_variant -> unit_enum_variant
        | enum_struct_variant -> struct_enum_variant

    struct_def: [PUB] "struct" IDENT _NL struct_field_list
    
    ?struct_field_list: [_INDENT (struct_field _NL)* _DEDENT]
    
    struct_field: [PUB] IDENT ":" type_annotation
    
    impl_def: "impl" IDENT _NL _INDENT fn_def (_NL* fn_def)* [_NL*] _DEDENT
    
    type_annotation: IDENT -> named_type
        | "[" type_annotation "]" -> array_type
        | "(" [type_annotation ("," type_annotation)*] ")" -> tuple_type
        | function_type -> function_type
    
    function_type: "(" [type_annotation ("," type_annotation)*] ")" "->" type_annotation
    
    ?expr: logical_or

    ?logical_or: logical_and
        | logical_or "or" logical_and -> or_

    ?logical_and: comparison
        | logical_and "and" comparison -> and_

    ?comparison: sum
        | comparison "<" sum -> lt
        | comparison "<=" sum -> le
        | comparison ">" sum -> gt
        | comparison ">=" sum -> ge
        | comparison "==" sum -> eq
        | comparison "!=" sum -> ne

    ?sum: product
        | sum "+" product -> add
        | sum "-" product -> sub

    ?product: unary
        | product "*" unary -> mul
        | product "/" unary -> div
        | product "%" unary -> mod
    ?unary: "-" unary -> neg
        | "!" unary -> not_
        | molecule

    ?molecule: atom
        | getindex
        | call
        | getattr
        | callattr
        
    call: molecule "(" arglist ")"
    callattr: molecule "." IDENT "(" arglist ")"
    getindex: molecule "[" expr "]"
    getattr: molecule "." IDENT
        
    ?atom: IDENT -> ident
        | FLOAT -> float
        | INT -> int
        | STRING -> string
        | CHAR -> char
        | "(" [expr ("," expr)*] ")" -> paren_expr
        | "true" -> true
        | "false" -> false
        | "[" [expr ("," expr)*] "]" -> array_expr
        | IDENT "{" field_init_list "}" -> struct_expr
        | IDENT "::" IDENT "{" field_init_list "}" -> enum_struct_expr
        | IDENT "::" IDENT "(" [expr ("," expr)*] ")" -> enum_tuple_expr
        | IDENT "::" IDENT -> enum_unit_expr
        
    field_init_list: [ field_init ("," field_init)* ]
    field_init: IDENT ":" expr
        

    arglist: [expr ("," expr)*]
    
    BREAK: "break"
    CONTINUE: "continue"
    PUB: "pub"
    LPAR: "("
    RPAR: ")"
    LSQB: "["
    RSQB: "]"
    LBRACE: "{"
    RBRACE: "}"
    IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
    CHAR: /'(\\.|[^\\'])'/
    _NL: /(\r?\n[ \t]*)+/
"""


# Indentation handling
class CussIndenter(Indenter):
    @property
    def NL_type(self) -> str:
        return "_NL"

    @property
    def OPEN_PAREN_types(self) -> list[str]:
        return ["LPAR", "LSQB", "LBRACE"]

    @property
    def CLOSE_PAREN_types(self) -> list[str]:
        return ["RPAR", "RSQB", "RBRACE"]

    @property
    def INDENT_type(self) -> str:
        return "_INDENT"

    @property
    def DEDENT_type(self) -> str:
        return "_DEDENT"

    @property
    def tab_len(self) -> int:
        return 4


# Expressive AST we convert the Lark ast into
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
        Node._next_id += 1

    def get_node(self, id: int) -> Optional["Node"]:
        if self.id == id:
            return self
        else:
            return None

    def get_span(self) -> tuple[int, int]:
        return (self.line, self.line)


Declaration = Union["FnDecl", "EnumDecl", "StructDecl", "TypeAliasDecl", "ImplDecl"]

Statement = Union[
    "Expr",
    "FnDecl",
    "VarDecl",
    "Assign",
    "Return",
    "If",
    "While",
    "Loop",
    "Break",
    "Continue",
]


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


class FnDecl(Node):
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
        self.pub = pub
        self.name = name
        self.params = params
        self.ret_type = ret_type
        self.body = body

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
    def __init__(self, name: str, type: TypeAnnotation, line: int) -> None:
        super().__init__("param", line)
        self.name = name
        self.type = type
        self.line = line

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type.get_node(id)


class StructDecl(Node):
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
    def __init__(self, pub: bool, name: str, type: TypeAnnotation, line: int) -> None:
        super().__init__("struct_field", line)
        self.pub = pub
        self.name = name
        self.type = type

    def get_node(self, id: int) -> Optional["Node"]:
        if self.id == id:
            return self
        return self.type.get_node(id)

    def get_span(self) -> tuple[int, int]:
        tmin, tmax = self.type.get_span()
        return (self.line, max(self.line, tmax))


class EnumDecl(Node):
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
        for type in self.types:
            node = type.get_node(id)
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
    def __init__(self, name: str, type: TypeAnnotation, line: int) -> None:
        super().__init__("enum_struct_field", line)
        self.name = name
        self.type = type

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type.get_node(id)

    def get_span(self) -> tuple[int, int]:
        tmin, tmax = self.type.get_span()
        return (self.line, max(self.line, tmax))


class TypeAliasDecl(Node):
    def __init__(self, pub: bool, name: str, type: TypeAnnotation, line: int) -> None:
        super().__init__("type_alias_decl", line)
        self.pub = pub
        self.name = name
        self.type = type

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        return self.type.get_node(id)

    def get_span(self) -> tuple[int, int]:
        tmin, tmax = self.type.get_span()
        return (self.line, max(self.line, tmax))


class VarDecl(Node):
    def __init__(
        self,
        mutable: bool,
        name: str,
        type: Optional[TypeAnnotation],
        expr: "Expr",
        line: int,
    ) -> None:
        kind = "let_decl" if mutable else "const_decl"
        super().__init__(kind, line)
        self.name = name
        self.type = type
        self.expr = expr

    def get_node(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self
        if self.type is not None:
            node = self.type.get_node(id)
            if node is not None:
                return node
        return self.expr.get_node(id)

    def get_span(self) -> tuple[int, int]:
        expr_min, expr_max = self.expr.get_span()
        return (self.line, max(self.line, expr_max))


Assignable = Union["Ident", "GetIndex", "GetAttr"]


class Assign(Node):
    def __init__(self, lhs: Assignable, rhs: "Expr", line: int) -> None:
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


class ImplDecl(Node):
    def __init__(self, name: str, methods: list[FnDecl], line: int) -> None:
        super().__init__("impl_decl", line)
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


class Return(Node):
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


class If(Node):
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
        self.else_body = else_body

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
            for stmt in self.else_body:
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
        if self.else_body is not None:
            for stmt in self.else_body:
                smin, smax = stmt.get_span()
                min_line = min(min_line, smin)
                max_line = max(max_line, smax)
        return (min_line, max_line)


class While(Node):
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


class Loop(Node):
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


class Break(Node):
    def __init__(self, line: int) -> None:
        super().__init__("break", line)


class Continue(Node):
    def __init__(self, line: int) -> None:
        super().__init__("continue", line)


Expr = Union[
    "Integer",
    "Float",
    "String",
    "Char",
    "Bool",
    "Array",
    "Ident",
    "Call",
    "GetIndex",
    "GetAttr",
    "CallAttr",
    "BinaryOp",
    "UnaryOp",
    "Return",
    "StructExpr",
    "EnumStructExpr",
    "EnumTupleExpr",
    "EnumUnitExpr",
]


class Integer(Node):
    def __init__(self, value: int, line: int) -> None:
        super().__init__("integer", line)
        self.value = value


class Float(Node):
    def __init__(self, value: float, line: int) -> None:
        super().__init__("float", line)
        self.value = value


class String(Node):
    def __init__(self, value: str, line: int) -> None:
        super().__init__("string", line)
        self.value = value


class Char(Node):
    def __init__(self, value: str, line: int) -> None:
        super().__init__("char", line)
        self.value = value


class Bool(Node):
    def __init__(self, value: bool, line: int) -> None:
        super().__init__("bool", line)
        self.value = value


class Array(Node):
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


class Tuple(Node):
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


class StructExpr(Node):
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


class EnumStructExpr(Node):
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


class EnumTupleExpr(Node):
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


class EnumUnitExpr(Node):
    def __init__(self, name: str, unit: str, line: int) -> None:
        super().__init__("enum_unit_expr", line)
        self.name = name
        self.unit = unit


class Ident(Node):
    def __init__(self, name: str, line: int) -> None:
        super().__init__("ident", line)
        self.name = name


class Call(Node):
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


class GetIndex(Node):
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


class GetAttr(Node):
    def __init__(self, obj: Expr, attr: str, line: int) -> None:
        super().__init__("getattr", line)
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


class CallAttr(Node):
    def __init__(self, obj: Expr, attr: str, args: list[Expr], line: int) -> None:
        super().__init__("callattr", line)
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


class BinaryOp(Node):
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


class UnaryOp(Node):
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


# Lark to inhouse AST
class ASTTransformer(Transformer):
    """
    Bottom‑up conversion from the raw Lark parse tree to the strongly‑typed
    CUSS AST defined below.  Every method corresponds to a grammar rule.
    """

    # ---------- entry points ----------
    def start(self, items):
        return items[0] if items else Program()

    def definition_list(self, defs):
        program = Program()
        for d in defs:
            program.push(d)
        return program

    # ---------- type annotations ----------
    def named_type(self, items):
        return NamedTypeAnnotation(items[0].value, items[0].line)

    def array_type(self, items):
        (elem_type,) = items
        return ArrayTypeAnnotation(elem_type, elem_type.line)

    def tuple_type(self, items):
        return TupleTypeAnnotation(items, items[0].line)

    def function_type(self, items):
        *params, ret = items
        return FunctionTypeAnnotation(params, ret, ret.line)

    # ---------- parameters / fields ----------
    def param(self, items):
        name_tok, type_ann = items
        return Param(name_tok.value, type_ann, type_ann.line)

    def param_list(self, items):
        return items

    def struct_field(self, items):
        idx = 0
        pub = items[idx] != None and items[idx].type == "PUB"
        idx += 1
        name_tok = items[idx]
        idx += 1
        type_ann = items[idx]
        return StructField(pub, name_tok.value, type_ann, type_ann.line)

    # ---------- enum helpers ----------
    def enum_struct_field(self, items):
        name_tok, type_ann = items
        return EnumStructField(name_tok.value, type_ann, type_ann.line)

    def enum_variant_list(self, items):
        return [it for it in items if not isinstance(it, Token)]

    def struct_field_list(self, items):
        return [it for it in items if not isinstance(it, Token)]

    def unit_enum_variant(self, items):
        # the only item should be a tree with a single IDENT child
        assert len(items) == 1
        assert isinstance(items[0], Tree)
        assert len(items[0].children) == 1
        assert isinstance(items[0].children[0], Token)
        return EnumUnitVariant(items[0].children[0].value, items[0].children[0].line)

    def tuple_enum_variant(self, items):
        # items: IDENT, type_annotation...
        name_tok, *type_list = items
        return EnumTupleVariant(name_tok.value, type_list, name_tok.line)

    def struct_enum_variant(self, items):
        # items: IDENT, struct_field...
        name_tok, *fields = items
        return EnumStructVariant(name_tok.value, fields, name_tok.line)

    # ---------- declarations ----------
    def fn_def(self, items):
        idx = 0
        pub = items[idx] != None and items[idx].type == "PUB"
        idx += 1
        name_tok = items[idx]
        idx += 1
        params = items[idx]
        idx += 1
        ret_type = items[idx]
        idx += 1
        body = items[idx]
        return FnDecl(pub, name_tok.value, params, ret_type, body, name_tok.line)

    def struct_def(self, items):
        idx = 0
        pub = items[idx] != None and items[idx].type == "PUB"
        idx += 1
        name_tok = items[idx]
        idx += 1
        fields = items[idx] if len(items) > idx else []
        return StructDecl(pub, name_tok.value, fields, name_tok.line)

    def enum_def(self, items):
        idx = 0
        pub = items[idx] != None and items[idx].type == "PUB"
        idx += 1
        name_tok = items[idx]
        idx += 1
        variants = items[idx] if len(items) > idx else []
        return EnumDecl(pub, name_tok.value, variants, name_tok.line)

    def type_alias(self, items):
        idx = 0
        pub = items[idx] != None and items[idx].type == "PUB"
        idx += 1
        name_tok = items[idx]
        idx += 1
        type_ann = items[idx]
        return TypeAliasDecl(pub, name_tok.value, type_ann, name_tok.line)

    def impl_def(self, items):
        name_tok = items[0]
        methods = items[1:]
        return ImplDecl(name_tok.value, methods, name_tok.line)

    # ---------- statements ----------
    def statement(self, items):
        return items[0]

    def statement_list(self, items):
        return items

    def const_def(self, items):
        name_tok, *rest = items
        if len(rest) == 2:
            type_ann, expr = rest
        else:
            type_ann, expr = None, rest[0]
        return VarDecl(False, name_tok.value, type_ann, expr, name_tok.line)

    def let_def(self, items):
        name_tok, *rest = items
        if len(rest) == 2:
            type_ann, expr = rest
        else:
            type_ann, expr = None, rest[0]
        return VarDecl(True, name_tok.value, type_ann, expr, name_tok.line)

    def assign_stmt(self, items):
        lhs, rhs = items
        return Assign(lhs, rhs, lhs.line)

    def return_stmt(self, items):
        expr = items[0] if len(items) > 0 else None
        return Return(expr, items[0].line)

    def if_stmt(self, items):
        cond = items[0]
        body = items[1]
        else_body = items[2] if len(items) > 2 else None
        return If(cond, body, else_body, items[0].line)

    def while_stmt(self, items):
        cond = items[0]
        body = items[1]
        return While(cond, body, items[0].line)

    def loop_stmt(self, items):
        body = items[0]
        return Loop(body, body[0].line)

    def break_stmt(self, items):
        return Break(items[0].line)

    def continue_stmt(self, items):
        return Continue(items[0].line)

    def expr_stmt(self, items):
        return items[0]

    # ---------- expressions ----------
    def getindex(self, items):
        obj = items[0]
        index = items[1]
        return GetIndex(obj, index, obj.line)

    def call(self, items):
        callee, args = items
        return Call(callee, args, callee.line)

    def callattr(self, items):
        obj, attr, args = items
        return CallAttr(obj, attr.value, args, obj.line)

    def getattr(self, items):
        obj, attr = items
        return GetAttr(obj, attr, obj.line)

    def or_(self, items):
        lhs, rhs = items
        return BinaryOp("or", lhs, rhs, lhs.line)

    def and_(self, items):
        lhs, rhs = items
        return BinaryOp("and", lhs, rhs, lhs.line)

    def eq(self, items):
        lhs, rhs = items
        return BinaryOp("==", lhs, rhs, lhs.line)

    def ne(self, items):
        lhs, rhs = items
        return BinaryOp("!=", lhs, rhs, lhs.line)

    def lt(self, items):
        lhs, rhs = items
        return BinaryOp("<", lhs, rhs, lhs.line)

    def le(self, items):
        lhs, rhs = items
        return BinaryOp("<=", lhs, rhs, lhs.line)

    def gt(self, items):
        lhs, rhs = items
        return BinaryOp(">", lhs, rhs, lhs.line)

    def ge(self, items):
        lhs, rhs = items
        return BinaryOp(">=", lhs, rhs, lhs.line)

    def add(self, items):
        lhs, rhs = items
        return BinaryOp("+", lhs, rhs, lhs.line)

    def sub(self, items):
        lhs, rhs = items
        return BinaryOp("-", lhs, rhs, lhs.line)

    def mul(self, items):
        lhs, rhs = items
        return BinaryOp("*", lhs, rhs, lhs.line)

    def div(self, items):
        lhs, rhs = items
        return BinaryOp("/", lhs, rhs, lhs.line)

    def neg(self, items):
        operand = items[0]
        return UnaryOp("-", operand, operand.line)

    def not_(self, items):
        operand = items[0]
        return UnaryOp("!", operand, operand.line)

    def ident(self, items):
        return Ident(items[0].value, items[0].line)

    def int(self, items):
        return Integer(int(items[0].value), items[0].line)

    def float(self, items):
        return Float(float(items[0].value), items[0].line)

    def string(self, items):
        return String(items[0][1:-1], items[0].line)

    def char(self, items):
        return Char(items[0].value, items[0].line)

    def true(self, _items):
        return Bool(True, _items[0].line)

    def false(self, _items):
        return Bool(False, _items[0].line)

    def paren_expr(self, items):
        if len(items) == 1:
            return items[0]
        else:
            return Tuple(items, items[0].line)

    def array_expr(self, items):
        return Array(items, items[0].line)

    def field_init(self, items):
        name_tok, expr = items
        return FieldInit(name_tok.value, expr, name_tok.line)

    def field_init_list(self, items):
        return items

    def struct_expr(self, items):
        name_tok, fields = items
        return StructExpr(name_tok.value, fields, name_tok.line)

    def enum_struct_expr(self, items):
        name_tok, unit_tok, fields = items
        return EnumStructExpr(name_tok.value, unit_tok.value, fields, name_tok.line)

    def enum_tuple_expr(self, items):
        name_tok, unit_tok, *elems = items
        return EnumTupleExpr(name_tok.value, unit_tok.value, elems, name_tok.line)

    def enum_unit_expr(self, items):
        name_tok, unit_tok = items
        return EnumUnitExpr(name_tok.value, unit_tok.value, name_tok.line)

    def arglist(self, items):
        return items


parser = Lark(
    cuss_grammar,
    parser="lalr",
    postlex=CussIndenter(),
    transformer=ASTTransformer(),
)


def parse(source: str) -> Program:
    program: Union[Optional[Program], Tree] = parser.parse(source)
    if program is None:
        return Program()
    elif isinstance(program, Program):
        return program
    else:
        raise ValueError("Invalid program")


# Internal Type Representation
class Type:
    def __str__(self) -> str:
        raise NotImplementedError("Subclasses must implement __str__")

    def __eq__(self, other: "Type") -> bool:
        raise NotImplementedError("Subclasses must implement __eq__")

    def __ne__(self, other: "Type") -> bool:
        raise NotImplementedError("Subclasses must implement __ne__")

    def __hash__(self) -> int:
        raise NotImplementedError("Subclasses must implement __hash__")


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
        if name in self.methods:
            raise NameResolutionError(
                f"Method {name} already exists for struct {self.name}", line, ast_id
            )
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
        if name in self.methods:
            raise NameResolutionError(
                f"Method {name} already exists for enum {self.name}", line, ast_id
            )
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
    next_alpha = "a"
    next_numeric = 0

    def __init__(self) -> None:
        self.name = f"T{TypeVar.next_alpha}{TypeVar.next_numeric}"
        if TypeVar.next_numeric == 9:
            TypeVar.next_alpha = chr(ord(TypeVar.next_alpha) + 1)
            TypeVar.next_numeric = 0
        else:
            TypeVar.next_numeric += 1

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: "Type") -> bool:
        return isinstance(other, TypeVar) and self.name == other.name

    def __ne__(self, other: "Type") -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)


# Error handling
class CussError(Exception):
    def __init__(self, message: str, line: int, ast_id: int) -> None:
        super().__init__(f"[Line {line}] {message}")
        self.message = message
        self.line = line
        self.ast_id = ast_id

    def __str__(self) -> str:
        return f"[Line {self.line}] {self.message}"

    def report(self, program: Program) -> None:
        # get the declaration of the node
        decl = program.get_decl(self.ast_id)
        if decl is None:
            raise RuntimeError(f"Declaration not found for ast_id: {self.ast_id}")
        # print the error
        print(f"Error: {self}")
        # get the span of the declaration
        span = decl.get_span()
        # get the source code
        source = program.source
        if source is None:
            raise RuntimeError(f"Source code not found for ast_id: {self.ast_id}")
        # split the source code into lines
        lines = source.splitlines()
        # print the lines with the error
        for i in range(span[0], span[1]):
            if i == self.line:
                print(f"{i} | > {lines[i]}")
            else:
                print(f"{i} |   {lines[i]}")


# Cannot infer type
class TypeInferenceError(CussError):
    pass


# Cannot resolve name
class NameResolutionError(CussError):
    pass


# Passes are used to transform and validate the AST
# This is the base class for all passes
class Pass(ABC):
    @abstractmethod
    def run(self, program: Program) -> Program:
        pass


# Pass utils
# Scopes map identifiers to types
class Scope:
    def __init__(self, parent_id: Optional[int] = None) -> None:
        self.identifiers: dict[str, Type] = {}
        self.parent_id = parent_id

    # adds an identifier to the scope
    def add_identifier(self, name: str, type: Type) -> None:
        self.identifiers[name] = type

    # only looks in the current scope
    def lookup(self, name: str) -> Optional[Type]:
        return self.identifiers.get(name)


# The symbol table maps ast ids to scopes
# SymbolTable persists across passes.
# Each AST node ID maps to the scope visible at that node's entry point.
# Scopes are never deleted.
class SymbolTable:
    def __init__(self) -> None:
        self.scopes: dict[int, Scope] = {}
        # add global scope -1
        self.scopes[-1] = Scope()
        self.current_scope_id: int = -1

    # creates a new scope and makes it the current scope
    def enter_scope(self, id: int) -> None:
        if id in self.scopes:
            self.current_scope_id = id
        else:
            self.scopes[id] = Scope(self.current_scope_id)
            self.current_scope_id = id

    # pops the current scope and makes the parent scope the current scope if it exists
    # returns the id of the parent scope
    def pop_scope(self) -> int:
        if self.current_scope_id == -1:
            raise RuntimeError("Cannot exit global scope")
        parent_id = self.scopes[self.current_scope_id].parent_id
        if parent_id is None:
            raise RuntimeError("Cannot exit global scope")
        self.current_scope_id = parent_id
        return parent_id

    # adds an identifier to the current scope
    def add_identifier(self, name: str, type: Type, line: int, ast_id: int) -> None:
        # make sure no ident shadower exists
        if self.lookup_local(name) is not None:
            raise NameResolutionError(
                f"Identifier {name} already exists in current scope", line, ast_id
            )
        self.scopes[self.current_scope_id].add_identifier(name, type)

    def set_identifier_type(self, name: str, type: Type) -> None:
        if name not in self.scopes[self.current_scope_id].identifiers:
            raise RuntimeError(f"Identifier {name} does not exist in current scope")
        # set the type of an existing identifier
        # used to resolve type variables
        self.scopes[self.current_scope_id].identifiers[name] = type

    # looks up an identifier in the current scope
    def lookup_local(self, name: str) -> Optional[Type]:
        return self.scopes[self.current_scope_id].lookup(name)

    # looks up ident in current scope and any parent scopes
    def lookup(self, name: str) -> Optional[Type]:
        scope = self.scopes[self.current_scope_id]
        while True:
            type = scope.lookup(name)
            if type is not None:
                return type
            # we will break if we hit global and return a check to that scope
            if scope.parent_id == -1 or scope.parent_id is None:
                break
            scope = self.scopes[scope.parent_id]
        # check global scope
        return self.scopes[-1].lookup(name)


# Type scope is a map of type names to types
# It is used to resolve type aliases and ensure no type shadowing
class TypeScope:
    def __init__(self, parent_id: Optional[int] = None) -> None:
        self.types: dict[str, Type] = {}
        self.parent_id = parent_id

    def lookup(self, name: str) -> Optional[Type]:
        return self.types.get(name)

    def add_type(self, name: str, type: Type) -> None:
        self.types[name] = type


# Type resolver is a map of type names to types
# It is used to resolve type aliases and ensure no type shadowing
class TypeResolver:
    def __init__(self) -> None:
        self.type_scopes: dict[int, TypeScope] = {}
        # global scope
        self.type_scopes[-1] = TypeScope()
        self.current_scope_id: int = -1

    def enter_scope(self, id: int) -> None:
        if id in self.type_scopes:
            self.current_scope_id = id
        else:
            self.type_scopes[id] = TypeScope(self.current_scope_id)
            self.current_scope_id = id

    def pop_scope(self) -> int:
        if self.current_scope_id == -1:
            raise RuntimeError("Cannot exit global scope")
        parent_id = self.type_scopes[self.current_scope_id].parent_id
        if parent_id is None:
            raise RuntimeError("Cannot exit global scope")
        self.current_scope_id = parent_id
        return parent_id

    def lookup(self, name: str) -> Optional[Type]:
        scope = self.type_scopes[self.current_scope_id]
        while True:
            type = scope.lookup(name)
            if type is not None:
                return type
            # we will break if we hit global and return a check to that scope
            if scope.parent_id == -1 or scope.parent_id is None:
                break
            scope = self.type_scopes[scope.parent_id]
        # check global scope
        return self.type_scopes[-1].lookup(name)

    def add_type(self, name: str, type: Type, line: int, ast_id: int) -> None:
        if self.lookup(name) is not None:
            raise TypeInferenceError(f"Type {name} already defined", line, ast_id)
        self.type_scopes[self.current_scope_id].add_type(name, type)

    def update_type(self, name: str, type: Type, line: int, ast_id: int) -> None:
        if self.lookup(name) is None:
            raise TypeInferenceError(f"Type {name} not defined", line, ast_id)
        self.type_scopes[self.current_scope_id].types[name] = type


# Micropasses


# Pass 1: Name resolution
class NameResolver(Pass):
    def __init__(self) -> None:
        super().__init__()
        self.symbol_table = SymbolTable()
        self.type_resolver = TypeResolver()
        self.errors: list[CussError] = []
        # nodes that need to be revisited after the first pass
        # this is used to resolve methods in case their type is not resolved yet
        self.back_tracks: list[int] = []

    def enter_scope(self, id: int) -> None:
        self.type_resolver.enter_scope(id)
        self.symbol_table.enter_scope(id)

    def pop_scope(self) -> int:
        self.type_resolver.pop_scope()
        return self.symbol_table.pop_scope()

    def push_symbol(self, name: str, type: Type, line: int, ast_id: int) -> None:
        try:
            self.symbol_table.add_identifier(name, type, line, ast_id)
        except NameResolutionError as e:
            self.errors.append(e)

    def add_type(self, name: str, type: Type, line: int, ast_id: int) -> None:
        try:
            self.type_resolver.add_type(name, type, line, ast_id)
        except TypeInferenceError as e:
            self.errors.append(e)

    def resolve_type_annotation(
        self, type_annotation: TypeAnnotation
    ) -> Optional[Type]:
        match type_annotation.kind:
            case "named_type":
                assert isinstance(type_annotation, NamedTypeAnnotation)
                return self.type_resolver.lookup(type_annotation.name)
            case "array_type":
                assert isinstance(type_annotation, ArrayTypeAnnotation)
                elem_type = self.resolve_type_annotation(type_annotation.elem_type)
                if elem_type is None:
                    return None
                return ArrayType(elem_type)
            case "tuple_type":
                assert isinstance(type_annotation, TupleTypeAnnotation)
                elem_types = [
                    self.resolve_type_annotation(t) for t in type_annotation.elem_types
                ]
                if any(t is None for t in elem_types):
                    return None
                elem_types = [
                    t for t in elem_types if t is not None
                ]  # done to please the type checker
                return TupleType(elem_types)
            case "function_type":
                assert isinstance(type_annotation, FunctionTypeAnnotation)
                params = [
                    self.resolve_type_annotation(p) for p in type_annotation.params
                ]
                if any(p is None for p in params):
                    return None
                params = [
                    p for p in params if p is not None
                ]  # done to please the type checker
                ret_type = self.resolve_type_annotation(type_annotation.ret_type)
                if ret_type is None:
                    return None
                return FunctionType(params, ret_type)
            case _:
                raise NameResolutionError(
                    f"Unknown type annotation: {type_annotation.kind}",
                    type_annotation.line,
                    type_annotation.id,
                )

    def run(self, program: Program) -> Program:
        for decl in program.declarations:
            self.resolve_decl(decl)
        if len(self.back_tracks) > 0:
            for id in self.back_tracks:
                decl = program.get_decl(id)
                if decl is None:
                    raise RuntimeError(f"Declaration not found: {id}")
                self.resolve_decl(decl, True)
        if len(self.errors) > 0:
            for error in self.errors:
                error.report(program)
        return program

    def resolve_decl(self, decl: Declaration, back_track: bool = False) -> None:
        if isinstance(decl, FnDecl):
            self.resolve_fn_decl(decl, back_track)
        elif isinstance(decl, ImplDecl):
            self.resolve_impl_decl(decl, back_track)
        elif isinstance(decl, StructDecl):
            self.resolve_struct_decl(decl, back_track)
        elif isinstance(decl, EnumDecl):
            self.resolve_enum_decl(decl, back_track)
        elif isinstance(decl, TypeAliasDecl):
            self.resolve_type_alias_decl(decl, back_track)

    def resolve_struct_decl(self, decl: StructDecl, back_track: bool = False) -> None:
        # convert the type annotations in the fields to types
        typed_fields = {}
        for field in decl.fields:
            type = self.resolve_type_annotation(field.type)
            if type is None:
                if back_track:
                    # if we are back tracking we have no tolerance for unresolved types
                    self.errors.append(
                        TypeInferenceError(
                            f"Struct field {field.name} has an unresolved type {field.type}",
                            field.line,
                            field.id,
                        )
                    )
                else:
                    # add to the back tracks and return out of the struct decl
                    self.back_tracks.append(decl.id)
                    return None
            # check that the field name is not already in use
            elif field.name in typed_fields:
                self.errors.append(
                    NameResolutionError(
                        f"Struct field {field.name} already defined in {decl.name}",
                        field.line,
                        field.id,
                    )
                )
            else:
                typed_fields[field.name] = type
        struct_type = StructType(decl.name, typed_fields)
        self.add_type(decl.name, struct_type, decl.line, decl.id)

    def resolve_enum_decl(self, decl: EnumDecl, back_track: bool = False) -> None:
        # TODO: implement this
        raise NotImplementedError("Enum declarations not implemented")

    def resolve_type_alias_decl(self, decl: TypeAliasDecl, back_track: bool = False) -> None:
        type = self.resolve_type_annotation(decl.type)
        if type is None:
            if back_track:
                # if we are back tracking we have no tolerance for unresolved types
                self.errors.append(
                    TypeInferenceError(
                        f"Type alias {decl.name} has an unresolved type {decl.type}",
                        decl.line,
                        decl.id,
                    )
                )
            else:
                # add to the back tracks and return out of the type alias decl
                self.back_tracks.append(decl.id)
                return None
        else:
            self.add_type(decl.name, type, decl.line, decl.id)

    def resolve_impl_decl(self, decl: ImplDecl, back_track: bool = False) -> None:
        # get the type of the object being implemented on
        obj_type = self.type_resolver.lookup(decl.name)
        
        if obj_type is None:
            if back_track:
                # if we are back tracking we have no tolerance for unresolved types
                self.errors.append(
                    TypeInferenceError(
                        f"Cannot find type {decl.name} to implement on",
                        decl.line,
                        decl.id,
                    )
                )
            else:
                # if object type is not resolved, we need to revisit this node
                self.back_tracks.append(decl.id)
                return None
        # check that the object type is a struct or enum
        if not isinstance(obj_type, (StructType, EnumType)):
            self.errors.append(
                TypeInferenceError(
                    f"Cannot implement on {decl.name} because it is not a struct or enum",
                    decl.line,
                    decl.id,
                )
            )
            return
        # resolve the methods
        for method in decl.methods:
            obj_type = self.resolve_method_decl(method, obj_type)
            if obj_type is None:
                if back_track:
                    # if we are back tracking and the method type is unresolved
                    # it already added an error so we can just return
                    return
                else:
                    # add to the back tracks and return out of the impl decl
                    self.back_tracks.append(decl.id)
                    return None
        # update the type of the object since we stayed in the global scope
        self.type_resolver.update_type(decl.name, obj_type, decl.line, decl.id)

    def resolve_method_decl(
        self, decl: FnDecl, obj_type: Union[StructType, EnumType], back_track: bool = False
    ) -> Optional[Union[StructType, EnumType]]:
        # convert the type annotations in the params to types
        typed_params: Dict[str, Type] = {}
        for param in decl.params:
            type = self.resolve_type_annotation(param.type)
            if type is None:
                if back_track:
                    self.errors.append(
                        TypeInferenceError(
                            f"Method {decl.name}'s parameter {param.name} has an unresolved type {param.type}",
                            decl.line,
                            decl.id,
                        )
                    )
                    return
                else:
                    # add to the back tracks and return out of the method decl
                    self.back_tracks.append(decl.id)
                    return None
            elif param.name in typed_params:
                self.errors.append(
                    NameResolutionError(
                        f"Method {decl.name}'s parameter {param.name} already defined in {decl.name}",
                        param.line,
                        param.id,
                    )
                )
            else:
                typed_params[param.name] = type
        # add self param to the fn params
        typed_params["self"] = obj_type
        # get the return type
        ret_type = self.resolve_type_annotation(decl.ret_type)
        if ret_type is None:
            # add to the back tracks and return out of the method decl
            self.back_tracks.append(decl.id)
            return None
        # create the function type
        fn_type = FunctionType(list(typed_params.values()), ret_type)
        # enter the new scope
        self.enter_scope(decl.id)
        # add params to the symbol table
        for param in typed_params.items():
            self.push_symbol(param[0], param[1], decl.line, decl.id)
        # go over the body and resolve each statement
        for stmt in decl.body:
            self.resolve_stmt(stmt)
        # exit the scope
        self.pop_scope()
        # add the method to the object type
        try:
            obj_type.add_method(decl.name, fn_type, decl.line, decl.id)
        except CussError as e:
            self.errors.append(e)
        return obj_type

    def resolve_fn_decl(self, decl: FnDecl, back_track: bool = False) -> None:
        # get the type of the fn
        # first convert the type annotations in the params to types
        typed_params: Dict[str, Type] = {}
        for param in decl.params:
            type = self.resolve_type_annotation(param.type)
            if type is None:
                if back_track:
                    self.errors.append(
                        TypeInferenceError(
                            f"Function {decl.name}'s parameter {param.name} has an unresolved type {param.type}",
                            decl.line,
                            decl.id,
                        )
                    )
                else:
                    # add to the back tracks and return out of the fn decl
                    self.back_tracks.append(decl.id)
                    return None
            elif param.name in typed_params:
                self.errors.append(
                    NameResolutionError(
                        f"Function {decl.name}'s parameter {param.name} already defined in {decl.name}",
                        param.line,
                        param.id,
                    )
                )
            else:
                typed_params[param.name] = type
        # get the return type
        ret_type = self.resolve_type_annotation(decl.ret_type)
        if ret_type is None:
            # add to the back tracks and return out of the method decl
            self.back_tracks.append(decl.id)
            return None
        # create the function type
        fn_type = FunctionType(list(typed_params.values()), ret_type)
        # add the fn type to the symbol table
        self.push_symbol(decl.name, fn_type, decl.line, decl.id)
        # enter the new scope
        self.enter_scope(decl.id)
        # add params to the symbol table
        for param in typed_params.items():
            self.push_symbol(param[0], param[1], decl.line, decl.id)
        # go over the body and resolve each statement
        for stmt in decl.body:
            self.resolve_stmt(stmt)
        # exit the scope
        self.pop_scope()

    def resolve_stmt(self, stmt: Statement, back_track: bool = False) -> None:
        if isinstance(stmt, FnDecl):
            self.resolve_fn_decl(stmt, back_track)
        elif isinstance(stmt, VarDecl):
            self.resolve_var_decl(stmt, back_track)
        elif isinstance(stmt, If):
            self.resolve_if(stmt, back_track)
        elif isinstance(stmt, While):
            self.resolve_while(stmt, back_track)
        elif isinstance(stmt, Loop):
            self.resolve_loop(stmt, back_track)
        else:
            pass  # only bodied statements need to be resolvedp

    def resolve_var_decl(self, stmt: VarDecl, back_track: bool = False) -> None:
        # check if the decl has a type
        if stmt.type is not None:
            type = self.resolve_type_annotation(stmt.type)
            if type is None:
                if back_track:
                    # add to the back tracks and return out of the method decl
                    self.back_tracks.append(stmt.id)
                    return None
                else:
                    # add to the back tracks and return out of the method decl
                    self.back_tracks.append(stmt.id)
                    return None
            else:
                self.push_symbol(stmt.name, type, stmt.line, stmt.id)
        else:
            # no type, so we need to infer it, for now we will use a type variable
            self.push_symbol(stmt.name, TypeVar(), stmt.line, stmt.id)

    def resolve_if(self, stmt: If, back_track: bool = False) -> None:
        # enter the new scope
        self.enter_scope(stmt.id)
        # do not touch the cond
        # resolve the body
        for item in stmt.body:
            self.resolve_stmt(item, back_track)
        # exit the scope
        self.pop_scope()
        # resolve the else body if it exists
        if stmt.else_body is not None:
            for item in stmt.else_body:
                self.resolve_stmt(item, back_track)

    def resolve_while(self, stmt: While, back_track: bool = False) -> None:
        # enter the new scope
        self.enter_scope(stmt.id)
        # do not touch the cond
        # resolve the body
        for item in stmt.body:
            self.resolve_stmt(item, back_track)
        # exit the scope
        self.pop_scope()

    def resolve_loop(self, stmt: Loop, back_track: bool = False) -> None:
        # enter the new scope
        self.enter_scope(stmt.id)
        # resolve the body
        for item in stmt.body:
            self.resolve_stmt(item, back_track)
        # exit the scope
        self.pop_scope()


# Pass 2: Type inference
class TypeInferencePass(Pass):
    # takes prebuilt symbol table from name resolution pass
    def __init__(self, symbol_table: SymbolTable) -> None:
        super().__init__()
        self.type_resolver: TypeResolver = TypeResolver.top()
        self.symbol_table: SymbolTable = symbol_table
        # node ids that need to be revisited with more information
        # this makes it so types can be used before they are defined
        self.backtracks: list[int] = []
        self.errors: list[TypeInferenceError] = []

    def run(self, program: Program) -> Program:
        for decl in program.declarations:
            self.infer_decl(decl)
        return program

    def push_type(self, name: str, type: Type, line: int, ast_id: int) -> None:
        try:
            self.type_resolver.add_type(name, type, line, ast_id)
        except TypeInferenceError as e:
            self.errors.append(e)

    def get_type(self, name: str) -> Optional[Type]:
        return self.type_resolver.lookup(name)

    def get_identifier_type(self, name: str) -> Optional[Type]:
        return self.symbol_table.lookup(name)

    def set_identifier_type(
        self, name: str, type: Type, line: int, ast_id: int
    ) -> None:
        self.symbol_table.set_identifier_type(name, type, line, ast_id)

    def enter_scope(self, id: int) -> None:
        self.type_resolver.enter_scope(id)
        self.symbol_table.enter_scope(id)

    def pop_scope(self) -> int:
        self.symbol_table.pop_scope()
        return self.type_resolver.pop_scope()

    # infer the types of the declarations
    def infer_decl(self, decl: Declaration) -> None:
        match decl.kind:
            case "fn_decl":
                self.infer_fn_decl(decl)
            case "struct_decl":
                self.infer_struct_decl(decl)
            case "enum_decl":
                self.infer_enum_decl(decl)
            case "type_alias_decl":
                self.infer_type_alias_decl(decl)
            case "impl_decl":
                self.infer_impl_decl(decl)
            case _:
                raise RuntimeError(f"Unknown declaration kind: {decl.kind}")

    def infer_fn_decl(self, decl: FnDecl) -> None:
        # enter the scope
        self.enter_scope(decl.id)
        # go over the body and infer the types of the statements
        for stmt in decl.body:
            self.infer_stmt(stmt)
        # exit the scope
        self.pop_scope()

    def infer_struct_decl(self, decl: StructDecl) -> None:
        # enter the struct into the type resolver
        self.push_type(decl.name, StructType(decl.fields), decl.line, decl.id)

    def infer_enum_decl(self, decl: EnumDecl) -> None:
        # enter the enum into the type resolver
        self.push_type(decl.name, EnumType(decl.variants), decl.line, decl.id)

    def infer_type_alias_decl(self, decl: TypeAliasDecl) -> None:
        # enter the type alias into the type resolver
        self.push_type(decl.name, decl.type, decl.line, decl.id)

    def infer_impl_decl(self, decl: ImplDecl) -> None:
        # enter the impl into the type resolver
        self.enter_scope(decl.id)
        # go over the body and infer the types of the statements
        for method in decl.methods:
            self.infer_fn_decl(method)
        # exit the scope
        self.pop_scope()

    def infer_stmt(self, stmt: Statement) -> None:
        match stmt.kind:
            case "fn_decl":
                self.infer_fn_decl(stmt)
            case "const_decl" | "let_decl":
                self.infer_var_decl(stmt)
            case "if":
                self.infer_if(stmt)
            case "while":
                self.infer_while(stmt)
            case "loop":
                self.infer_loop(stmt)
            case _:  # other statements dont need type inference
                pass

    def infer_var_decl(self, stmt: VarDecl) -> None:
        # retrieve the type of the identifier from the symbol table
        type = self.get_identifier_type(stmt.name)
        # if it is a type variable, we need to infer it
        if isinstance(type, TypeVar):
            # we need to infer the type of the expression
            expr_type = self.infer_expr(stmt.expr)
            if expr_type is None:
                # we need to backtrack
                self.backtracks.append(stmt.id)
                return
            # if we know the type, set it
            self.set_identifier_type(stmt.name, expr_type, stmt.line, stmt.id)
        # otherwise, the type is already known

    def infer_if(self, stmt: If) -> None:
        # enter the scope
        self.enter_scope(stmt.id)
        # do not touch the cond
        # perform type inference on the body
        for stmt in stmt.body:
            self.infer_stmt(stmt)
        # exit the scope
        self.pop_scope()
        # resolve the else body if it exists
        if stmt.else_body is not None:
            for stmt in stmt.else_body:
                self.infer_stmt(stmt)

    def infer_while(self, stmt: While) -> None:
        # enter the scope
        self.enter_scope(stmt.id)
        # do not touch the cond
        # perform type inference on the body
        for stmt in stmt.body:
            self.infer_stmt(stmt)
        # exit the scope
        self.pop_scope()

    def infer_loop(self, stmt: Loop) -> None:
        # enter the scope
        self.enter_scope(stmt.id)
        # perform type inference on the body
        for stmt in stmt.body:
            self.infer_stmt(stmt)
        # exit the scope
        self.pop_scope()

    def infer_expr(self, expr: Expr) -> Optional[Type]:
        if isinstance(expr, Integer):
            return IntType()
        elif isinstance(expr, Float):
            return FloatType()
        elif isinstance(expr, String):
            return StringType()
        elif isinstance(expr, Bool):
            return BoolType()
        elif isinstance(expr, Char):
            return CharType()
        elif isinstance(expr, Array):
            return ArrayType(self.infer_expr(expr.elem_type))
        elif isinstance(expr, Tuple):
            return TupleType(self.infer_expr(expr.elem_type))
        elif isinstance(expr, StructExpr):
            return self.infer_struct_expr(expr)
        elif isinstance(expr, EnumStructExpr) or isinstance(expr, EnumTupleExpr) or isinstance(expr, EnumUnitExpr):
            return self.infer_enum_expr(expr)
        elif isinstance(expr, Ident):
            return self.infer_ident(expr)
        elif isinstance(expr, Call):
            return self.infer_call(expr)
        elif isinstance(expr, GetIndex):
            return self.infer_get_index(expr)
        elif isinstance(expr, GetAttr):
            return self.infer_get_attr(expr)
        elif isinstance(expr, CallAttr):
            return self.infer_callattr(expr)
        elif isinstance(expr, BinaryOp):
            return self.infer_binary_op(expr)
        elif isinstance(expr, UnaryOp):
            return self.infer_unary_op(expr)
        
    def infer_array(self, expr: Array) -> Optional[Type]:
        elem_types: List[Type] = []
        for elem in expr.elems:
            elem_type = self.infer_expr(elem)
            if elem_type is None:
                return None
            elem_types.append(elem_type)
        # TODO: check if all the types are the same
        return ArrayType(elem_types)
        
        
    def infer_struct_expr(self, expr: StructExpr) -> Optional[Type]:
        # lookup the struct in the type resolver
        struct_type = self.get_type(expr.name)
        # if the type is not yet known we will need to backtrack
        # hopefully it is defined below this point in source code
        if struct_type is None:
            # return none and the type inference will backtrack
            return None
        # otherwise we figured out the type
        return struct_type

    def infer_enum_expr(
        self, expr: Union[EnumStructExpr, EnumTupleExpr, EnumUnitExpr]
    ) -> Optional[Type]:
        # lookup the enum in the type resolver
        enum_type = self.get_type(expr.name)
        # if the type is not yet known we will need to backtrack
        # hopefully it is defined below this point in source code
        if enum_type is None:
            # return none and the type inference will backtrack
            return None
        # otherwise we figured out the type
        return enum_type

    def infer_ident(self, expr: Ident) -> Optional[Type]:
        # lookup the identifier in the symbol table
        ident_type = self.get_identifier_type(expr.name)
        # if the ident type is not yet known thats not okay
        # idents need to be defined and typed before they are used
        if ident_type is None:
            raise TypeInferenceError(
                f"Identifier {expr.name} is not defined", expr.line, expr.id
            )
        # we also need to check if the type is a type variable
        # it shouldnt be but edge cases are possible
        if isinstance(ident_type, TypeVar):
            # we will return none and hope that the type variable is resolved later
            return None
        # otherwise we figured out the type
        return ident_type

    def infer_call(self, expr: Call) -> Type:
        # lookup the function in the symbol table
        fn_type = self.get_identifier_type(expr.name)
        # if the type is not in the symbol table this is problematic
        # it should have been entered during name resolution
        if fn_type is None:
            raise TypeInferenceError(f"Function {expr.name} is not defined", expr.line, expr.id)
        # otherwise get the return type of the function
        return fn_type.ret_type

    def infer_get_index(self, expr: GetIndex) -> Type:
        # check what obj we are indexing it should be an array, ident, or string
        obj_type = self.infer_expr(expr.obj)
        # the obj type should resolve to an array, string, or type variable
        # otherwise this is an error
        if isinstance(obj_type, ArrayType):
            return obj_type.elem_type
        elif isinstance(obj_type, StringType):
            return CharType()
        elif isinstance(obj_type, TypeVar):
            # we will return none and hope that the type variable is resolved later
            return None
        else:
            raise TypeInferenceError(
                f"Cannot index expression of type {obj_type}", expr.line
            )

    def infer_get_attr(self, expr: GetAttr) -> Type:
        # lookup the type of the object
        obj_type = self.infer_expr(expr.obj)
        # the obj type should resolve to a struct, enum, or type variable
        # otherwise this is an error
        if isinstance(obj_type, StructType):
            # get the field type
            field_type = obj_type.fields[expr.attr]
            # if the type is none that means the field does not exist
            if field_type is None:
                raise TypeInferenceError(
                    f"Field {expr.attr} does not exist in struct {expr.obj.name}",
                    expr.line,
                )
            # otherwise we figured out the type
            return field_type
        elif isinstance(obj_type, EnumType):
            # TODO: we need to add support for field access on enums
            # right now this is an error
            raise NotImplementedError("Field access on enums not implemented")
        elif isinstance(obj_type, TypeVar):
            # we will return none and hope that the type variable is resolved later
            return None
        else:
            raise TypeInferenceError(
                f"Cannot get attribute of type {obj_type}", expr.line
            )

    def infer_callattr(self, expr: CallAttr) -> Type:
        # TODO: we need to add support for method calls somehow attach the method to the type
        raise NotImplementedError("Method calls not implemented")

    def infer_binary_op(self, expr: BinaryOp) -> Type:
        lhs_type = self.infer_expr(expr.lhs)
        rhs_type = self.infer_expr(expr.rhs)
        match expr.op:
            case "+":
                return self.infer_arith(lhs_type, rhs_type, expr.line)
            case "-":
                return self.infer_arith(lhs_type, rhs_type, expr.line)
            case "*":
                return self.infer_arith(lhs_type, rhs_type, expr.line)
            case "/":
                return self.infer_arith(lhs_type, rhs_type, expr.line)
            case "%":
                return self.infer_arith(lhs_type, rhs_type, expr.line)
            case "==":
                return self.infer_eq(lhs_type, rhs_type, expr.line)
            case "!=":
                return self.infer_eq(lhs_type, rhs_type, expr.line)
            case "<":
                return self.infer_cmp(lhs_type, rhs_type, expr.line)
            case ">":
                return self.infer_cmp(lhs_type, rhs_type, expr.line)
            case "<=":
                return self.infer_cmp(lhs_type, rhs_type, expr.line)
            case ">=":
                return self.infer_cmp(lhs_type, rhs_type, expr.line)
            case "and":
                return self.infer_logic(lhs_type, rhs_type, expr.line)
            case "or":
                return self.infer_logic(lhs_type, rhs_type, expr.line)
            case _:
                raise TypeInferenceError(
                    f"Unknown binary operator: {expr.op}", expr.line
                )

    def infer_arith(self, lhs: Type, rhs: Type, line: int) -> Type:
        # TODO: implement
        raise NotImplementedError(
            "Type inference for arithmetic operations not implemented"
        )

    def infer_eq(self, lhs: Type, rhs: Type, line: int) -> Type:
        # TODO: implement
        raise NotImplementedError(
            "Type inference for equality operations not implemented"
        )

    def infer_cmp(self, lhs: Type, rhs: Type, line: int) -> Type:
        # TODO: implement
        raise NotImplementedError(
            "Type inference for comparison operations not implemented"
        )

    def infer_logic(self, lhs: Type, rhs: Type, line: int) -> Type:
        # TODO: implement
        raise NotImplementedError(
            "Type inference for logical operations not implemented"
        )

    def infer_unary_op(self, expr: UnaryOp) -> Type:
        # TODO: implement
        raise NotImplementedError("Unary operation expressions not implemented")
