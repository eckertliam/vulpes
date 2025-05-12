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
    Char,
    Continue,
    FieldInit,
    Float,
    FnDecl,
    FunctionTypeAnnotation,
    AccessField,
    GetIndex,
    Ident,
    If,
    Integer,
    IntersectionTypeAnnotation,
    Loop,
    NamedTypeAnnotation,
    Param,
    Program,
    Return,
    String,
    StructDecl,
    StructExpr,
    StructField,
    StructuralTypeAnnotation,
    SubtractedTypeAnnotation,
    TupleExpr,
    TupleTypeAnnotation,
    TypeAliasDecl,
    UnaryOp,
    UnionTypeAnnotation,
    VarDecl,
    While,
)

grammar = r"""
    %import common.INT
    %import common.FLOAT 
    %import common.ESCAPED_STRING -> STRING
    %import common.WS_INLINE
    
    %ignore WS_INLINE
    %declare _INDENT _DEDENT
    
    start: [_NL*] definition_list
    
    definition_list: (definition (_NL* definition)* [_NL*])?
    
    ?definition: fn_def
                | struct_def
                | type_alias
                
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
    
    type_alias: "type" IDENT "=" type_annotation

    fn_def: "fn" IDENT "(" param_list ")" "->" type_annotation _NL* _INDENT statement_list _DEDENT
    
    param_list: [param ("," param)*]
    
    param: IDENT ":" type_annotation
    
    struct_def: "struct" IDENT _NL struct_field_list
    
    ?struct_field_list: [_INDENT (struct_field _NL)* _DEDENT]
    
    struct_field: IDENT ":" type_annotation
    
    ?type_annotation: union_type

    ?union_type: intersection_type
        | union_type "|" intersection_type -> union_type

    ?intersection_type: subtracted_type
        | intersection_type "&" subtracted_type -> intersection_type

    ?subtracted_type: base_type
        | base_type "-" base_type -> subtracted_type

    ?base_type: IDENT -> named_type
        | "[" type_annotation "]" -> array_type
        | "(" [type_annotation ("," type_annotation)*] ")" -> tuple_type
        | function_type -> function_type
        | "{" structural_type_list "}" -> structural_type
    
    
    structural_type_list: structural_type_field ("," structural_type_field)* ","?

    structural_type_field: IDENT ":" type_annotation
    
    
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
        
    call: molecule "(" arglist ")"
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
        | "{" field_init_list "}" -> struct_expr
        
    field_init_list: [ field_init ("," field_init)* ]
    field_init: IDENT ":" expr
        

    arglist: [expr ("," expr)*]
    
    TRUE: "true"
    FALSE: "false"
    BREAK: "break"
    CONTINUE: "continue"
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
class VulpesIndenter(Indenter):
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
    AST defined below.  Every method corresponds to a grammar rule.
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

    def structural_type_field(self, items):
        name_tok, type_ann = items
        return (name_tok.value, type_ann)

    def structural_type_list(self, items):
        return items

    def structural_type(self, items):
        fields = {}
        for (name, type_ann) in items[0]:
            fields[name] = type_ann
        return StructuralTypeAnnotation(fields, items[0][0][1].line)

    def subtracted_type(self, items):
        base_type, subtracted_type = items
        return SubtractedTypeAnnotation(base_type, subtracted_type, base_type.line)

    def intersection_type(self, items):
        types = items
        return IntersectionTypeAnnotation(types, types[0].line)

    def union_type(self, items):
        types = items
        return UnionTypeAnnotation(types, types[0].line)

    # ---------- parameters / fields ----------
    def param(self, items):
        name_tok, type_ann = items
        return Param(name_tok.value, type_ann, type_ann.line)

    def param_list(self, items):
        return items

    def struct_field(self, items):
        name_tok, type_ann = items
        return StructField(name_tok.value, type_ann, type_ann.line)

    def struct_field_list(self, items):
        return [it for it in items if not isinstance(it, Token)]

    # ---------- declarations ----------
    def fn_def(self, items):
        idx = 0
        name_tok = items[idx]
        idx += 1
        params = items[idx]
        # filter None from params
        params = [param for param in params if param is not None]
        idx += 1
        ret_type = items[idx]
        idx += 1
        body = items[idx]
        assert isinstance(name_tok.value, str), "name_tok.value is not a str in fn_def"
        return FnDecl(name_tok.value, params, ret_type, body, name_tok.line)

    def struct_def(self, items):
        idx = 0
        name_tok = items[idx]
        idx += 1
        fields = items[idx:] if len(items) > idx else []
        # flatten the fields
        new_fields = []
        for field in fields:
            if isinstance(field, list):
                new_fields.extend(field)
            else:
                new_fields.append(field)
        fields = new_fields
        return StructDecl(name_tok.value, fields, name_tok.line)

    def type_alias(self, items):
        idx = 0
        name_tok = items[idx]
        idx += 1
        type_ann = items[idx]
        return TypeAliasDecl(name_tok.value, type_ann, name_tok.line)

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
        fields = items[0]
        return StructExpr(fields, fields[0].line)

    def arglist(self, items):
        return items


PARSER = Lark(
    grammar,
    parser="lalr",
    postlex=VulpesIndenter(),
    transformer=ASTTransformer(),
)


def parse(source: str) -> Program:
    program: Union[Optional[Program], Tree] = PARSER.parse(source)
    assert isinstance(program, Program)
    program.source = source
    return program
