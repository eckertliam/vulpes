from lark import Lark
from lark.indenter import Indenter

cuss_grammar = r"""
    %import common.INT
    %import common.FLOAT 
    %import common.ESCAPED_STRING -> STRING
    %import common.WS_INLINE
    
    %ignore WS_INLINE
    %declare _INDENT _DEDENT
    
    ?start: [_NL] program
    
    ?program: statement_list | 
    
    ?statement_list: statement _NL statement_list | statement [_NL]
    
    statement: fn_def
             | expr
             | enum
             | struct
             | "return" expr -> return_stmt
             
    fn_def: "fn" IDENT LPAR [param_list] RPAR "->" type_annotation _NL _INDENT statement_list _DEDENT
    
    param_list: [param ("," param)*]
    
    param: IDENT ":" type_annotation
    
    enum: ["pub"] "enum" IDENT _NL enum_variant_list
    
    ?enum_variant_list: [_INDENT (enum_variant _NL)* _DEDENT]
    
    enum_tuple_variant: IDENT "(" [type_annotation ("," type_annotation)*] ")"

    enum_unit_variant: IDENT
    
    enum_struct_variant: IDENT "(" enum_struct_field ("," enum_struct_field)* ")"

    enum_struct_field: IDENT ":" type_annotation

    enum_variant: enum_tuple_variant -> tuple
        | enum_unit_variant -> unit
        | enum_struct_variant -> struct

    struct: ["pub"] "struct" IDENT _NL struct_field_list
    
    ?struct_field_list: [_INDENT (struct_field _NL)* _DEDENT]
    
    struct_field: ["pub"] IDENT ":" type_annotation
    
    type_annotation: IDENT
        | "[" type_annotation "]" -> array
        | "(" [type_annotation ("," type_annotation)*] ")" -> tuple_type
        | "(" type_annotation ")" "->" type_annotation -> function_type
    
    ?expr: logical_or
        | call

    call: IDENT LPAR [arglist] RPAR -> call_expr

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
    
# Ast
class Program:
    def __init__(self) -> None:
        self.declarations = []
        
    def push(self, declaration: 'Declaration'):
        self.declarations.append(declaration)
        
class Declaration:
    def __init__(self, kind: str) -> None:
        self.kind = None
        
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
        
class FunctionType(TypeAnnotation):
    def __init__(self, params: list[TypeAnnotation], ret_type: TypeAnnotation) -> None:
        self.params = params
        self.ret_type = ret_type
        
class FnDecl(Declaration):
    def __init__(self, name: str, params: list['Param'], ret_type: TypeAnnotation) -> None:
        super().__init__("fn_del")
        self.name = name
        self.params = params
        self.ret_type = ret_type
        
class Param:
    def __init__(self, name: str, type: TypeAnnotation) -> None:
        self.name = name
        self.type = type
        
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

if __name__ == "__main__":
    parser = Lark(cuss_grammar, parser='lalr', postlex=CussIndenter())
    try:
        # Check if example.cuss exists, create a basic one if it doesn't
        import os
        if not os.path.exists("example.cuss"):
            with open("example.cuss", "w") as f:
                f.write("true")
            print("Created example.cuss with a simple 'true' value")
            
        with open("example.cuss", "r") as f:
            content = f.read()
            if not content.strip():
                print("Warning: example.cuss is empty. Parsing empty file.")
            print(parser.parse(content))
    except FileNotFoundError:
        print("Error: example.cuss file not found")
    except Exception as e:
        print(f"Error parsing: {e}")
