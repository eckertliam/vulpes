# This is a messy prototype of a Cuss compiler.
# It is a loose example of what the final C++ compiler will look like.
# It is not intended to be a full implementation of the language.
# It is only intended to be a minimal proof of concept.

from typing import Dict, Optional, Union
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
    NL_type = "_NL"
    OPEN_PAREN_types = ["LPAR", "LSQB", "LBRACE"]
    CLOSE_PAREN_types = ["RPAR", "RSQB", "RBRACE"]
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 4


# Expressive AST we convert the Lark ast into
class Program:
    def __init__(self, source: str) -> None:
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


Declaration = Union["FnDecl", "EnumDecl", "StructDecl", "TypeAliasDecl"]

Statement = Union[
    "Expr",
    "FnDecl",
    "EnumDecl",
    "StructDecl",
    "TypeAliasDecl",
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
    program: Optional[Program] = parser.parse(source)
    if program is None:
        return Program()
    return program


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


def resolve_type_alias(type: Type) -> Type:
    while isinstance(type, TypeAliasType):
        type = type.target_type
    return type


class IntType(Type):
    def __str__(self) -> str:
        return "int"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(resolve_type_alias(other), IntType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(resolve_type_alias(other), IntType)

    def __hash__(self) -> int:
        return hash("int")


class FloatType(Type):
    def __str__(self) -> str:
        return "float"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(resolve_type_alias(other), FloatType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(resolve_type_alias(other), FloatType)

    def __hash__(self) -> int:
        return hash("float")


class StringType(Type):
    def __str__(self) -> str:
        return "string"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(resolve_type_alias(other), StringType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(resolve_type_alias(other), StringType)

    def __hash__(self) -> int:
        return hash("string")


class BoolType(Type):
    def __str__(self) -> str:
        return "bool"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(resolve_type_alias(other), BoolType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(resolve_type_alias(other), BoolType)

    def __hash__(self) -> int:
        return hash("bool")


class CharType(Type):
    def __str__(self) -> str:
        return "char"

    def __eq__(self, other: "Type") -> bool:
        return isinstance(resolve_type_alias(other), CharType)

    def __ne__(self, other: "Type") -> bool:
        return not isinstance(resolve_type_alias(other), CharType)

    def __hash__(self) -> int:
        return hash("char")


class ArrayType(Type):
    def __init__(self, elem_type: Type) -> None:
        self.elem_type = elem_type

    def __str__(self) -> str:
        return f"[{self.elem_type}]"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(resolve_type_alias(other), ArrayType)
            and self.elem_type == resolve_type_alias(other).elem_type
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(resolve_type_alias(other), ArrayType)
            or self.elem_type != resolve_type_alias(other).elem_type
        )

    def __hash__(self) -> int:
        return hash(("array", hash(self.elem_type)))


class TupleType(Type):
    def __init__(self, elem_types: list[Type]) -> None:
        self.elem_types = elem_types

    def __str__(self) -> str:
        return f"({', '.join(str(t) for t in self.elem_types)})"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(resolve_type_alias(other), TupleType)
            and self.elem_types == resolve_type_alias(other).elem_types
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(resolve_type_alias(other), TupleType)
            or self.elem_types != resolve_type_alias(other).elem_types
        )

    def __hash__(self) -> int:
        return hash(("tuple", tuple(hash(t) for t in self.elem_types)))


class FunctionType(Type):
    def __init__(self, params: list[Type], ret_type: Type) -> None:
        self.params = params
        self.ret_type = ret_type

    @staticmethod
    def from_fn_decl(decl: FnDecl) -> "FunctionType":
        params = [p.type for p in decl.params]
        ret_type = decl.ret_type
        return FunctionType(params, ret_type)

    def __str__(self) -> str:
        return f"({', '.join(str(t) for t in self.params)}) -> {self.ret_type}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(resolve_type_alias(other), FunctionType)
            and self.params == resolve_type_alias(other).params
            and self.ret_type == resolve_type_alias(other).ret_type
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(resolve_type_alias(other), FunctionType)
            or self.params != resolve_type_alias(other).params
            or self.ret_type != resolve_type_alias(other).ret_type
        )

    def __hash__(self) -> int:
        return hash(("fn", tuple(hash(t) for t in self.params), hash(self.ret_type)))


# Struct Type
class StructType(Type):
    def __init__(self, name: str, fields: Dict[str, Type]) -> None:
        self.name = name
        self.fields = fields

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(f'{k}: {v}' for k, v in self.fields.items())} }}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(resolve_type_alias(other), StructType)
            and self.name == resolve_type_alias(other).name
            and self.fields == resolve_type_alias(other).fields
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(resolve_type_alias(other), StructType)
            or self.name != resolve_type_alias(other).name
            or self.fields != resolve_type_alias(other).fields
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

    def __str__(self) -> str:
        return f"{self.name} {{ {', '.join(str(v) for v in self.variants.values())} }}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(resolve_type_alias(other), EnumType)
            and self.name == resolve_type_alias(other).name
            and self.variants == resolve_type_alias(other).variants
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(resolve_type_alias(other), EnumType)
            or self.name != resolve_type_alias(other).name
            or self.variants != resolve_type_alias(other).variants
        )

    def __hash__(self) -> int:
        return hash(
            (
                "enum",
                self.name,
                tuple(sorted((k, hash(v)) for k, v in self.variants.items())),
            )
        )


class TypeAliasType(Type):
    def __init__(self, name: str, target_type: Type) -> None:
        self.name = name
        self.target_type = target_type

    def __str__(self) -> str:
        return f"{self.name} = {self.target_type}"

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(resolve_type_alias(other), TypeAliasType)
            and self.name == resolve_type_alias(other).name
            and self.target_type == resolve_type_alias(other).target_type
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(resolve_type_alias(other), TypeAliasType)
            or self.name != resolve_type_alias(other).name
            or self.target_type != resolve_type_alias(other).target_type
        )


# For type inference
class TypeVar(Type):
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: "Type") -> bool:
        return (
            isinstance(resolve_type_alias(other), TypeVar)
            and self.name == resolve_type_alias(other).name
        )

    def __ne__(self, other: "Type") -> bool:
        return (
            not isinstance(resolve_type_alias(other), TypeVar)
            or self.name != resolve_type_alias(other).name
        )

    def __hash__(self) -> int:
        return hash(("typevar", self.name))


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
        decl = program.get_declaration(self.ast_id)
        if decl is None:
            raise RuntimeError(f"Declaration not found for ast_id: {self.ast_id}")
        # print the error
        print(f"Error: {self}")
        # get the span of the declaration
        span = decl.get_span()
        # split the source code into lines
        lines = program.source.splitlines()
        # print the lines with the error
        for i in range(span[0], span[1]):
            if i == self.line:
                print(f"{i} | > {lines[i]}")
            else:
                print(f"{i} |   {lines[i]}")


# Type mismatch etc
class CussTypeError(CussError):
    pass


# Syntax errors
class CussSyntaxError(CussError):
    pass


# Attempting to mutate a constant
class CussMutabilityError(CussError):
    pass


# Attempting to use an undefined name
class CussNameError(CussError):
    pass


# Runtime errors
class CussRuntimeError(CussError):
    pass


# Track type and mutability of variables
class VarBinding:
    def __init__(self, mutable: bool, type: Type) -> None:
        self.mutable = mutable
        self.type = type


# Context for type checking, type inference, etc.
class Context:
    def __init__(self) -> None:
        # top level type scope
        self.named_types: Dict[str, Type] = {}
        # track type bindings over scopes
        self.var_bindings: list[Dict[str, VarBinding]] = [{}]
        # function bindings
        self.fn_bindings: Dict[str, FunctionType] = {}
        # impl bindings struct -> method -> function type
        self.impl_bindings: Dict[str, Dict[str, FunctionType]] = {}

    def enter_scope(self) -> None:
        self.var_bindings.append({})

    def exit_scope(self) -> None:
        if len(self.var_bindings) > 1:
            self.var_bindings.pop()
        else:
            raise RuntimeError("Cannot exit top scope")

    def bind_var(self, name: str, mutable: bool, type: Type) -> None:
        self.var_bindings[-1][name] = VarBinding(mutable, type)

    def get_var(self, name: str) -> Optional[VarBinding]:
        for scope in reversed(self.var_bindings):
            if name in scope:
                return scope[name]
        return None

    def add_type(self, name: str, type: Type) -> None:
        self.named_types[name] = type

    def get_type(self, name: str) -> Optional[Type]:
        return self.named_types.get(name)

    def bind_fn(self, name: str, fn_type: FunctionType) -> None:
        self.fn_bindings[name] = fn_type

    def get_fn(self, name: str) -> Optional[FunctionType]:
        return self.fn_bindings.get(name)

    def bind_impl(self, name: str, method_name: str, fn_type: FunctionType) -> None:
        if name not in self.impl_bindings:
            self.impl_bindings[name] = {}
        self.impl_bindings[name][method_name] = fn_type

    def get_impl(self, name: str, method_name: str) -> Optional[FunctionType]:
        return self.impl_bindings.get(name, {}).get(method_name, None)


# Semantic analysis
class SemanticAnalyzer:
    def __init__(self) -> None:
        self.context = Context()

    def check_program(self, program: Program, source: str) -> None:
        errors: list[CussError] = []
        for decl in program.declarations:
            try:
                self.check_declaration(decl)
            except CussError as e:
                errors.append(e)
        if errors:
            for error in errors:
                error.report(source)
            exit(1)

    def check_declaration(self, decl: Declaration) -> None:
        match decl.kind:
            case "fn_decl":
                self.check_fn_decl(decl)
            case "struct_decl":
                self.check_struct_decl(decl)
            case "enum_decl":
                self.check_enum_decl(decl)
            case "type_alias_decl":
                self.check_type_alias_decl(decl)
            case "impl_decl":
                self.check_impl_decl(decl)
            case _:
                raise RuntimeError(f"Unknown declaration kind: {decl.kind}")

    def check_fn_decl(self, decl: FnDecl) -> None:
        assert isinstance(decl, FnDecl)
        # enter scope
        self.context.enter_scope()
        # check params
        for param in decl.params:
            self.check_param(param)
        # check body
        self.check_fn_body(decl.body, decl.ret_type)
        # if everything checks out, bind the function
        fn_type = FunctionType.from_fn_decl(decl)
        self.context.bind_fn(decl.name, fn_type)
        # exit scope
        self.context.exit_scope()

    def check_param(self, param: Param) -> None:
        # we are already in the scope of the function
        # so we just make sure the name is unique and bind the type
        if param.name in self.context.var_bindings[-1]:
            raise CussNameError(
                f"Duplicate parameter name: {param.name}", param.line, param.ast_id
            )
        # parameters are immutable so we set mutable to False
        self.context.bind_var(param.name, False, param.type)

    def check_fn_body(self, body: list[Statement], expected_ret_type: Type) -> None:
        # TODO: implement function body checking
        raise NotImplementedError("Function body checking not implemented")

    def check_struct_decl(self, decl: StructDecl) -> None:
        # TODO: implement struct declaration checking
        raise NotImplementedError("Struct declaration checking not implemented")

    def check_enum_decl(self, decl: EnumDecl) -> None:
        # TODO: implement enum declaration checking
        raise NotImplementedError("Enum declaration checking not implemented")

    def check_type_alias_decl(self, decl: TypeAliasDecl) -> None:
        # TODO: implement type alias declaration checking
        raise NotImplementedError("Type alias declaration checking not implemented")

    def check_impl_decl(self, decl: ImplDecl) -> None:
        # TODO: implement impl declaration checking
        raise NotImplementedError("Impl declaration checking not implemented")


if __name__ == "__main__":
    try:
        with open("example.cuss", "r") as f:
            content = f.read()
            if not content.strip():
                print("Warning: example.cuss is empty. Parsing empty file.")
            ast = parser.parse(content)
            for decl in ast.declarations:
                print(decl)
    except FileNotFoundError:
        print("Error: example.cuss file not found")
    except Exception as e:
        # traceback
        import traceback

        tb = traceback.extract_tb(e.__traceback__)
        last_frame = tb[-1]
        print(f"Error parsing: {e}")
        print(f"File: {last_frame.filename}, Line: {last_frame.lineno}")
