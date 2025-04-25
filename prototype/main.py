# This is a messy prototype of a Cuss compiler.
# It is a loose example of what the final C++ compiler will look like.
# It is not intended to be a full implementation of the language.
# It is only intended to be a minimal proof of concept.

from typing import Dict, Optional, Union, List
from lark import Lark, Tree, Token, Transformer
from lark.indenter import Indenter

cuss_grammar = r"""
    %import common.INT
    %import common.FLOAT 
    %import common.ESCAPED_STRING -> STRING
    %import common.WS_INLINE
    
    %ignore WS_INLINE
    %declare _INDENT _DEDENT
    
    ?start: [_NL] program
    
    ?program: definition_list
    
    ?definition_list: definition (_NL definition)* [_NL]
    
    ?definition: fn_def
                | enum_def
                | struct_def
                | type_alias
                | impl_def
                
    ?statement_list: statement (_NL statement)* [_NL]
    
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
    break_stmt: "break" -> break_stmt
    continue_stmt: "continue" -> continue_stmt
    
    const_def: "const" IDENT [":" type_annotation] "=" expr
    let_def: "let" IDENT [":" type_annotation] "=" expr
    assign_stmt: IDENT "=" expr
    
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
    
    impl_def: "impl" IDENT _NL _INDENT method_list _DEDENT
    
    method_list: (method _NL)* method [_NL]
    
    method: fn_def
    
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

    ?product: molecule
        | product "*" molecule -> mul
        | product "/" molecule -> div

    ?molecule: atom
        | molecule LSQB expr RSQB -> getindex
        | molecule LPAR arglist RPAR -> call
        | molecule "." IDENT -> getattr
        | molecule "." IDENT LPAR arglist RPAR -> callattr

    ?atom: IDENT -> ident
        | FLOAT -> float
        | INT -> int
        | STRING -> string
        | CHAR -> char
        | LPAR expr RPAR -> paren_expr
        | LSQB [expr ("," expr)*] RSQB -> list_expr
        | LBRACE [expr ":" expr ("," expr ":" expr)*] RBRACE -> dict_expr
        | "true" -> true
        | "false" -> false

    arglist: [expr ("," expr)*]
    
    PUB: "pub"
    LPAR: "("
    RPAR: ")"
    LSQB: "["
    RSQB: "]"
    LBRACE: "{"
    RBRACE: "}"
    IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
    CHAR: /'(\\.|[^\\'])'/
    _NL: /\r?\n[\t ]*/
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
    def __init__(self) -> None:
        self.declarations = []

    def push(self, declaration: "Declaration"):
        self.declarations.append(declaration)


class Node:
    def __init__(self, kind: str, line: int) -> None:
        self.kind = kind
        self.line = line


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
    "IfStmt",
    "WhileStmt",
    "LoopStmt",
    "BreakStmt",
    "ContinueStmt",
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


class TupleTypeAnnotation(TypeAnnotation):
    def __init__(self, elem_types: list[TypeAnnotation], line: int) -> None:
        super().__init__("tuple_type", line)
        self.elem_types = elem_types


class FunctionTypeAnnotation(TypeAnnotation):
    def __init__(
        self, params: list[TypeAnnotation], ret_type: TypeAnnotation, line: int
    ) -> None:
        super().__init__("function_type", line)
        self.params = params
        self.ret_type = ret_type


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


class Param:
    def __init__(self, name: str, type: TypeAnnotation, line: int) -> None:
        self.name = name
        self.type = type
        self.line = line


class StructDecl(Node):
    def __init__(
        self, pub: bool, name: str, fields: list["StructField"], line: int
    ) -> None:
        super().__init__("struct_decl", line)
        self.pub = pub
        self.name = name
        self.fields = fields


class StructField(Node):
    def __init__(self, pub: bool, name: str, type: TypeAnnotation, line: int) -> None:
        super().__init__("struct_field", line)
        self.pub = pub
        self.name = name
        self.type = type


class EnumDecl(Node):
    def __init__(
        self, pub: bool, name: str, variants: list["EnumVariant"], line: int
    ) -> None:
        super().__init__("enum_decl", line)
        self.pub = pub
        self.name = name
        self.variants = variants


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


class EnumStructVariant(EnumVariant):
    def __init__(self, name: str, fields: list["EnumStructField"], line: int) -> None:
        super().__init__("enum_struct_variant", name, line)
        self.fields = fields


class EnumStructField(Node):
    def __init__(self, name: str, type: TypeAnnotation, line: int) -> None:
        super().__init__("enum_struct_field", line)
        self.name = name
        self.type = type


class TypeAliasDecl(Node):
    def __init__(self, pub: bool, name: str, type: TypeAnnotation, line: int) -> None:
        super().__init__("type_alias_decl", line)
        self.pub = pub
        self.name = name
        self.type = type


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


class Assign(Node):
    def __init__(self, name: str, expr: "Expr", line: int) -> None:
        super().__init__("assign_decl", line)
        self.name = name
        self.expr = expr


class ImplDecl(Node):
    def __init__(self, name: str, methods: list[FnDecl], line: int) -> None:
        super().__init__("impl_decl", line)
        self.name = name
        self.methods = methods


class Return(Node):
    def __init__(self, expr: "Expr", line: int) -> None:
        super().__init__("return", line)
        self.expr = expr


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


class While(Node):
    def __init__(self, cond: "Expr", body: list[Statement], line: int) -> None:
        super().__init__("while", line)
        self.cond = cond
        self.body = body


class Loop(Node):
    def __init__(self, body: list[Statement], line: int) -> None:
        super().__init__("loop", line)
        self.body = body


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


class Ident(Node):
    def __init__(self, name: str, line: int) -> None:
        super().__init__("ident", line)
        self.name = name


class Call(Node):
    def __init__(self, name: str, args: list[Expr], line: int) -> None:
        super().__init__("call", line)
        self.name = name
        self.args = args


class GetIndex(Node):
    def __init__(self, obj: Expr, index: Expr, line: int) -> None:
        super().__init__("getindex", line)
        self.obj = obj
        self.index = index


class GetAttr(Node):
    def __init__(self, obj: Expr, attr: str, line: int) -> None:
        super().__init__("getattr", line)
        self.obj = obj
        self.attr = attr


class CallAttr(Node):
    def __init__(self, obj: Expr, attr: str, args: list[Expr], line: int) -> None:
        super().__init__("callattr", line)
        self.obj = obj
        self.attr = attr
        self.args = args


class BinaryOp(Node):
    def __init__(self, op: str, lhs: Expr, rhs: Expr, line: int) -> None:
        super().__init__("binary_op", line)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs


class UnaryOp(Node):
    def __init__(self, op: str, operand: Expr, line: int) -> None:
        super().__init__("unary_op", line)
        self.op = op
        self.operand = operand


# Lark to inhouse AST
class ASTTransformer(Transformer):
    """
    Bottom‑up conversion from the raw Lark parse tree to the strongly‑typed
    CUSS AST defined below.  Every method corresponds to a grammar rule.
    """

    # ---------- entry points ----------
    def start(self, items):
        # start : [_NL] program
        return items[-1]

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
        name_tok, expr = items
        return Assign(name_tok.value, expr, name_tok.line)

    def return_stmt(self, items):
        expr = items[0] if len(items) > 0 else None
        return Return(expr, items[0].line)

    def if_stmt(self, items):
        cond = items[0]
        body = items[1]
        else_body = items[2] if len(items) > 2 else None
        return If(cond, body, else_body, items[0].meta.line)

    def while_stmt(self, items):
        cond = items[0]
        body = items[1]
        return While(cond, body, items[0].line)

    def loop_stmt(self, items):
        body = items[0]
        return Loop(body, items[0].line)

    def break_stmt(self, items):
        return Break(items[0].meta.line)

    def continue_stmt(self, items):
        return Continue(items[0].meta.line)

    # ---------- expressions ----------
    # TODO: add support for array indexing
    # TODO: add support for function calls
    # TODO: add support for attribute access
    # TODO: add support for method calls
    # TODO: add support for field access
    # TODO: add support for binary operations
    # TODO: add support for unary operations
    
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
    def __init__(self, message: str, line: int) -> None:
        super().__init__(f"[Line {line}] {message}")
        self.message = message
        self.line = line

    def __str__(self) -> str:
        return f"[Line {self.line}] {self.message}"

    def report(self, source: str) -> None:
        lines = source.splitlines()
        print(self)
        # print the line with the error
        print(lines[self.line - 1])
        # print the error line
        print(" " * (len(str(self.line)) + 2) + "^")


# Type mismatch etc
class TypeError(CussError):
    pass


# Syntax errors
class SyntaxError(CussError):
    pass


# Attempting to mutate a constant
class MutabilityError(CussError):
    pass


# Attempting to use an undefined name
class NameError(CussError):
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
            raise NameError(f"Duplicate parameter name: {param.name}")
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
    parser = Lark(
        cuss_grammar,
        parser="lalr",
        postlex=CussIndenter(),
        transformer=ASTTransformer(),
    )
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
        print(f"Error parsing: {e}")
