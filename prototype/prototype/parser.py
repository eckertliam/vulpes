from typing import Optional, Union
from lark import Lark, Tree, Token, Transformer
from lark.indenter import Indenter

from .ast import (
    ArrayExpr,
    ArrayTypeAnnotation,
    Assign,
    BinaryOp,
    Bool,
    Break,
    Call,
    CallMethod,
    Char,
    Continue,
    EnumDecl,
    EnumStructExpr,
    EnumStructField,
    EnumStructVariant,
    EnumTupleExpr,
    EnumTupleVariant,
    EnumUnitExpr,
    EnumUnitVariant,
    FieldInit,
    Float,
    FnDecl,
    FunctionTypeAnnotation,
    AccessField,
    GetIndex,
    Ident,
    If,
    ImplDecl,
    Integer,
    Loop,
    NamedTypeAnnotation,
    Param,
    Program,
    Return,
    String,
    StructDecl,
    StructExpr,
    StructField,
    TraitDecl,
    TupleExpr,
    TupleTypeAnnotation,
    TypeAliasDecl,
    UnaryOp,
    VarDecl,
    While,
)

from .types import BoolType, CharType, FloatType, IntType, StringType, Type

from .symbol import Symbol

# TODO: add partial trait methods
# TODO: add trait impls
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
    assign_stmt: (IDENT | getindex | get_field) "=" expr
    
    type_alias: [PUB] "type" IDENT "=" type_annotation

    fn_def: [PUB] "fn" IDENT "(" param_list ")" "->" type_annotation _NL _INDENT statement_list _DEDENT
    
    param_list: [param ("," param)*]
    
    param: IDENT ":" type_annotation
    
    enum_def: [PUB] "enum" IDENT _NL enum_variant_list
    
    ?enum_variant_list: [_INDENT (enum_variant _NL)* _DEDENT]
    
    enum_tuple_variant: IDENT "(" [type_annotation ("," type_annotation)*] ")"

    enum_unit_variant: IDENT
    
    enum_struct_variant: IDENT "{" enum_struct_field ("," enum_struct_field)* "}"

    enum_struct_field: IDENT ":" type_annotation

    enum_variant: enum_tuple_variant -> tuple_enum_variant
        | enum_unit_variant -> unit_enum_variant
        | enum_struct_variant -> struct_enum_variant

    struct_def: [PUB] "struct" IDENT _NL struct_field_list
    
    ?struct_field_list: [_INDENT (struct_field _NL)* _DEDENT]
    
    struct_field: [PUB] IDENT ":" type_annotation
    
    impl_def: "impl" IDENT _NL _INDENT fn_def (_NL* fn_def)* [_NL*] _DEDENT
    
    trait_def: [PUB] "trait" IDENT _NL _INDENT fn_def (_NL* fn_def)* [_NL*] _DEDENT
    
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
        | get_field
        | call_method
        
    call: molecule "(" arglist ")"
    call_method: molecule "." IDENT "(" arglist ")"
    getindex: molecule "[" expr "]"
    get_field: molecule "." IDENT
        
    ?atom: IDENT -> ident
        | FLOAT -> float
        | INT -> int
        | STRING -> string
        | CHAR -> char
        | "(" [expr ("," expr)*] ")" -> paren_expr
        | TRUE -> true
        | FALSE -> false
        | "[" [expr ("," expr)*] "]" -> array_expr
        | IDENT "{" field_init_list "}" -> struct_expr
        | IDENT "::" IDENT "{" field_init_list "}" -> enum_struct_expr
        | IDENT "::" IDENT "(" [expr ("," expr)*] ")" -> enum_tuple_expr
        | IDENT "::" IDENT -> enum_unit_expr
        
    field_init_list: [ field_init ("," field_init)* ]
    field_init: IDENT ":" expr
        

    arglist: [expr ("," expr)*]
    
    TRUE: "true"
    FALSE: "false"
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
        name_tok, *type_list = items[0].children
        return EnumTupleVariant(name_tok.value, type_list, name_tok.line)

    def struct_enum_variant(self, items):
        name_tok, *fields = items[0].children
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

    def trait_def(self, items):
        idx = 0
        pub = items[idx] != None and items[idx].type == "PUB"
        idx += 1
        name_tok = items[idx]
        idx += 1
        methods = items[idx:]
        return TraitDecl(pub, name_tok.value, methods, name_tok.line)

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
        if isinstance(lhs, Token):
            assert lhs.type == "IDENT"
            assert lhs.line is not None
            lhs = Ident(lhs.value, lhs.line)
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

    def call_method(self, items):
        obj, attr, args = items
        return CallMethod(obj, attr.value, args, obj.line)

    def get_field(self, items):
        obj, attr = items
        return AccessField(obj, attr, obj.line)

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
        token = items[0]
        assert isinstance(token, Token)
        assert token.line is not None
        return Ident(token.value, token.line)

    def int(self, items):
        return Integer(int(items[0].value), items[0].line)

    def float(self, items):
        return Float(float(items[0].value), items[0].line)

    def string(self, items):
        return String(items[0][1:-1], items[0].line)

    def char(self, items):
        return Char(items[0].value, items[0].line)

    def true(self, items):
        return Bool(True, items[0].line)

    def false(self, items):
        return Bool(False, items[0].line)

    def paren_expr(self, items):
        if len(items) == 1:
            return items[0]
        else:
            return TupleExpr(items, items[0].line)

    def array_expr(self, items):
        return ArrayExpr(items, items[0].line)

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
    program.source = source
    return program
