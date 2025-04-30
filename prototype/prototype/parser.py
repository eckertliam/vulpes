from typing import Dict, Optional, Union
from lark import Lark, Tree, Token, Transformer
from lark.indenter import Indenter

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


class TypeAliasDecl(Declaration):
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


class VarDecl(Statement):
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


class Expr(Statement):
    pass


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
        super().__init__("integer", line)
        self.value = value


class Float(Expr):
    def __init__(self, value: float, line: int) -> None:
        super().__init__("float", line)
        self.value = value


class String(Expr):
    def __init__(self, value: str, line: int) -> None:
        super().__init__("string", line)
        self.value = value


class Char(Expr):
    def __init__(self, value: str, line: int) -> None:
        super().__init__("char", line)
        self.value = value


class Bool(Expr):
    def __init__(self, value: bool, line: int) -> None:
        super().__init__("bool", line)
        self.value = value


class Array(Expr):
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


class Tuple(Expr):
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


class GetAttr(AssignableExpr):
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


class CallAttr(Expr):
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
        # filter None from params
        params = [param for param in params if param is not None]
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
        else_body = items[2:] if len(items) > 2 else None
        # flatten the else body
        if else_body is not None:
            new_else_body = []
            for item in else_body:
                if isinstance(item, list):
                    new_else_body.extend(item)
                else:
                    new_else_body.append(item)
            else_body = new_else_body
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


PARSER = Lark(
    cuss_grammar,
    parser="lalr",
    postlex=CussIndenter(),
    transformer=ASTTransformer(),
)


def parse(source: str) -> Program:
    program: Union[Optional[Program], Tree] = PARSER.parse(source)
    assert isinstance(program, Program)
    return program
