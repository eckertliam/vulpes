from typing import Optional, Union
from lark import Lark, Tree, Token
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
    
    ?definition_list: definition _NL definition_list | definition [_NL]
    
    ?definition: fn_def
                | enum_def
                | struct_def
                | type_alias
    
    ?statement_list: statement (_NL statement)* [_NL]
    
    statement: fn_def
             | expr -> expr_stmt
             | enum_def
             | struct_def
             | "return" expr -> return_stmt
             | type_alias
             | const_def
             | let_def
             | impl_def
    
    const_def: "const" IDENT [":" type_annotation] "=" expr
    let_def: "let" IDENT [":" type_annotation] "=" expr
    
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

    enum_variant: enum_tuple_variant -> tuple
        | enum_unit_variant -> unit
        | enum_struct_variant -> struct

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
    NL_type = '_NL'
    OPEN_PAREN_types = ['LPAR', 'LSQB', 'LBRACE']
    CLOSE_PAREN_types = ['RPAR', 'RSQB', 'RBRACE']
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 4
    
# Expressive AST we convert the Lark ast into
class Program:
    def __init__(self) -> None:
        self.declarations = []
        
    def push(self, declaration: 'Declaration'):
        self.declarations.append(declaration)
        
class Declaration:
    def __init__(self, kind: str, pub: bool = False) -> None:
        self.kind = kind
        self.pub = pub
        
class TypeAnnotation:
    pass

class NamedType(TypeAnnotation):
    def __init__(self, name: str) -> None:
        self.name = name
        
class ArrayType(TypeAnnotation):
    def __init__(self, elem_type: TypeAnnotation) -> None:
        self.elem_type = elem_type
        
class TupleType(TypeAnnotation):
    def __init__(self, elem_types: list[TypeAnnotation]) -> None:
        self.elem_types = elem_types
        
Statement = Union['Expr', 'FnDecl', 'EnumDecl', 'StructDecl', 'TypeAliasDecl', 'VarDecl']
        
class FunctionType(TypeAnnotation):
    def __init__(self, params: list[TypeAnnotation], ret_type: TypeAnnotation) -> None:
        self.params = params
        self.ret_type = ret_type
        
class FnDecl(Declaration):
    def __init__(self, pub: bool, name: str, params: list['Param'], ret_type: TypeAnnotation, body: list[Statement]) -> None:
        super().__init__("fn_decl", pub)
        self.name = name
        self.params = params
        self.ret_type = ret_type
        self.body = body
        
class Param:
    def __init__(self, name: str, type: TypeAnnotation) -> None:
        self.name = name
        self.type = type
        
    
class StructDecl(Declaration):
    def __init__(self, pub: bool, name: str, fields: list['StructField']) -> None:
        super().__init__("struct_decl", pub)
        self.name = name
        self.fields = fields
        
class StructField:
    def __init__(self, name: str, type: TypeAnnotation) -> None:
        self.name = name
        self.type = type
        
class EnumDecl(Declaration):
    def __init__(self, pub: bool, name: str, variants: list['EnumVariant']) -> None:
        super().__init__("enum_decl", pub)
        self.name = name
        self.variants = variants
        
class EnumVariant:
    pass

class EnumUnitVariant(EnumVariant):
    def __init__(self, name: str) -> None:
        self.name = name
        
class EnumTupleVariant(EnumVariant):
    def __init__(self, name: str, types: list[TypeAnnotation]) -> None:
        self.name = name
        self.types = types
        
class EnumStructVariant(EnumVariant):
    def __init__(self, name: str, fields: list['EnumStructField']) -> None:
        self.name = name
        self.fields = fields
        
class EnumStructField:
    def __init__(self, name: str, type: TypeAnnotation) -> None:
        self.name = name
        self.type = type

class TypeAliasDecl(Declaration):
    def __init__(self, pub: bool, name: str, type: TypeAnnotation) -> None:
        super().__init__("type_alias_decl", pub)
        self.name = name
        self.type = type
        
class VarDecl(Declaration):
    def __init__(self, mutable: bool, name: str, type: Optional[TypeAnnotation] = None, expr: Optional['Expr'] = None) -> None:
        if mutable:
            super().__init__("let_decl", False)
        else:
            super().__init__("const_decl", False)
        self.name = name
        self.type = type
        self.expr = expr
class ImplDecl(Declaration):
    def __init__(self, name: str, methods: list[FnDecl]) -> None:
        super().__init__("impl_decl", False)
        self.name = name
        self.methods = methods

class Expr:
    def __init__(self, kind: str) -> None:
        self.kind = kind

class Integer(Expr):
    def __init__(self, value: int) -> None:
        super().__init__("integer")
        self.value = value
        
class Float(Expr):
    def __init__(self, value: float) -> None:
        super().__init__("float")
        self.value = value
        
class String(Expr):
    def __init__(self, value: str) -> None:
        super().__init__("string")
        self.value = value
        
class Char(Expr):
    def __init__(self, value: str) -> None:
        super().__init__("char")
        self.value = value
        
class Bool(Expr):
    def __init__(self, value: bool) -> None:
        super().__init__("bool")
        self.value = value
        
class List(Expr):
    def __init__(self, elems: list[Expr]) -> None:
        super().__init__("list")
        self.elems = elems
        
class Ident(Expr):
    def __init__(self, name: str) -> None:
        super().__init__("ident")
        self.name = name
        
class Call(Expr):
    def __init__(self, name: str, args: list[Expr]) -> None:
        super().__init__("call")
        self.name = name
        self.args = args
        
class GetIndex(Expr):
    def __init__(self, obj: Expr, index: Expr) -> None:
        super().__init__("getindex")
        self.obj = obj
        self.index = index
        
class GetAttr(Expr):
    def __init__(self, obj: Expr, attr: str) -> None:
        super().__init__("getattr")
        self.obj = obj
        self.attr = attr
        
class CallAttr(Expr):
    def __init__(self, obj: Expr, attr: str, args: list[Expr]) -> None:
        super().__init__("callattr")
        self.obj = obj
        self.attr = attr
        self.args = args
  
class BinaryOp(Expr):
    def __init__(self, op: str, lhs: Expr, rhs: Expr) -> None:
        super().__init__("binary_op")
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        
class UnaryOp(Expr):
    def __init__(self, op: str, operand: Expr) -> None:
        super().__init__("unary_op")
        self.op = op
        self.operand = operand
        
# Lark to inhouse AST
def lark_to_ast(lark_ast: Tree) -> Program:
    assert isinstance(lark_ast, Tree)
    # right now top level is always a definition list
    assert lark_ast.data == "definition_list"
    program = Program()
    
    for child in lark_ast.children:
        match child.data:
            case "fn_def":
                program.push(parse_fn_def(child))
            case "enum_def":
                program.push(parse_enum_def(child))
            case "struct_def":
                program.push(parse_struct_def(child))
            case "type_alias":
                program.push(parse_type_alias(child))
            case "impl_def":
                # TODO: Implement impl def parsing
                raise NotImplementedError("Impl def parsing not implemented")
            case _:
                raise ValueError(f"Unknown definition type: {child.data}")
                
    return program

def parse_fn_def(lark_ast: Tree) -> FnDecl:
    assert lark_ast.data == "fn_def"
    
    offset: int = 0
    
    pub: bool = lark_ast.children[offset].value == "pub"
    if pub: offset += 1
    name: str = lark_ast.children[offset].value
    offset += 1
    
    params: list[Param] = parse_param_list(lark_ast.children[offset])
    offset += 1
    
    ret_type: TypeAnnotation = parse_type_annotation(lark_ast.children[offset])
    offset += 1
    
    body: list[Statement] = []
    
    assert lark_ast.children[offset].data == "statement_list"
    
    for child in lark_ast.children[offset].children:
        body.append(parse_statement(child))
        
    return FnDecl(pub, name, params, ret_type, body)

def parse_param_list(lark_ast: Tree) -> Param:
    assert lark_ast.data == "param_list"
    
    params: list[Param] = []
    
    for child in lark_ast.children:
        assert child.data == "param"
        name: str = child.children[0].value
        type: TypeAnnotation = parse_type_annotation(child.children[1])
        params.append(Param(name, type))
        
    return params
            

def parse_enum_def(lark_ast: Tree) -> EnumDecl:
    assert lark_ast.data == "enum_def"
    
    offset: int = 0
    
    pub: bool = lark_ast.children[offset].data == "pub"
    if pub: offset += 1
    name: str = lark_ast.children[offset].value
    
    offset += 1
    
    variants: list[EnumVariant] = []
    
    for child in lark_ast.children[offset].children:
        match child.data:
            case "enum_tuple_variant":
                # TODO: Implement tuple variant parsing
                raise NotImplementedError("Tuple variants not implemented")
            case "enum_unit_variant":
                variants.append(EnumUnitVariant(child.value))
            case "enum_struct_variant":
                # TODO: Implement struct variant parsing
                raise NotImplementedError("Struct variants not implemented")
            case _:
                raise ValueError(f"Unknown variant type: {child.data}")

    return EnumDecl(pub, name, variants)

def parse_struct_def(lark_ast: Tree) -> StructDecl:
    assert lark_ast.data == "struct_def"
    
    offset: int = 0
    
    pub: bool = lark_ast.children[offset].data == "pub"
    if pub: offset += 1
    name: str = lark_ast.children[offset].value
    
    offset += 1
    
    fields: list[StructField] = []
    
    for child in lark_ast.children[offset].children:
        if child.data == "struct_field":
            fields.append(parse_struct_field(child))
        else:
            raise ValueError(f"Unknown field type: {child.data}")
    
    return StructDecl(pub, name, fields)
   
def parse_struct_field(lark_ast: Tree) -> StructField:
    assert lark_ast.data == "struct_field"
    
    offset: int = 0
    
    pub: bool = lark_ast.children[offset].data == "pub"
    if pub: offset += 1
    name: str = lark_ast.children[offset].value
    
    offset += 1
    
    type: TypeAnnotation = parse_type_annotation(lark_ast.children[offset])
    
    return StructField(name, type)

def parse_type_annotation(lark_ast: Tree) -> TypeAnnotation:
    assert lark_ast.data == "type_annotation"
    
    match lark_ast.data:
        case "named_type":
            return NamedType(lark_ast.children[0].value)
        case "array_type":
            # TODO: make sure this is correct with some examples
            return ArrayType(parse_type_annotation(lark_ast.children[0]))
        case "tuple_type":
            # TODO: make sure this is correct with some examples
            types: list[TypeAnnotation] = []
            for child in lark_ast.children[0].children:
                types.append(parse_type_annotation(child))
            return TupleType(types)
        case "function_type":
            # TODO: Implement function type parsing
            raise NotImplementedError("Function types not implemented")
        case _:
            raise ValueError(f"Unknown type annotation: {lark_ast.children[0].data}")
            

def parse_type_alias(lark_ast: Tree) -> TypeAliasDecl:
    assert lark_ast.data == "type_alias"
    
    offset: int = 0
    
    pub: bool = lark_ast.children[offset].data == "pub"
    if pub: offset += 1
    name: str = lark_ast.children[offset].value
    
    offset += 1
    
    type: TypeAnnotation = parse_type_annotation(lark_ast.children[offset])
    
    return TypeAliasDecl(pub, name, type)

def parse_statement(lark_ast: Tree) -> Statement:
    assert lark_ast.data == "statement"
    
    # TODO: add support for impls, expression statements, and return statements
    match lark_ast.children[0].data:
        case "const_def" | "let_def":
            return parse_var_def(lark_ast)
        case "fn_def":
            return parse_fn_def(lark_ast)
        case "enum_def":
            return parse_enum_def(lark_ast)
        case "struct_def":
            return parse_struct_def(lark_ast)
        case "type_alias":
            return parse_type_alias(lark_ast)
        case _:
            raise ValueError(f"Unknown statement type: {lark_ast.children[0].data}")
    
def parse_var_def(lark_ast: Tree) -> VarDecl:
    assert lark_ast.data == "const_def" or lark_ast.data == "let_def"
    
    mutable: bool = lark_ast.data == "let_def"
    name: str = lark_ast.children[0].value
    
    type: Optional[TypeAnnotation] = None
    if lark_ast.children[1] != None:
        type = parse_type_annotation(lark_ast.children[1])
        
    expr: Expr = parse_expr(lark_ast.children[2])

    return VarDecl(mutable, name, type, expr)

def parse_expr(lark_ast: Tree) -> Expr:
    assert lark_ast.data == "expr"
    
    # TODO: Implement expression parsing
    raise NotImplementedError("Expression parsing not implemented")

if __name__ == "__main__":
    parser = Lark(cuss_grammar, parser='lalr', postlex=CussIndenter())
    try:
        with open("example.cuss", "r") as f:
            content = f.read()
            if not content.strip():
                print("Warning: example.cuss is empty. Parsing empty file.")
            print(parser.parse(content).children[1].children[1])
    except FileNotFoundError:
        print("Error: example.cuss file not found")
    except Exception as e:
        print(f"Error parsing: {e}")
