from main import Assign, BinaryOp, Break, Continue, EnumDecl, Ident, If, Loop, StructDecl, VarDecl, While, parse, Program, FnDecl, Statement, Return, Integer
import pytest
import textwrap

def test_empty_program():
    program = parse("")
    assert isinstance(program, Program)
    assert len(program.declarations) == 0


def test_simple_fn_decl():
    source = textwrap.dedent('''
    fn main() -> int
        return 0     
    ''')
    program = parse(source)
    assert isinstance(program, Program)
    assert len(program.declarations) == 1
    fn_decl = program.declarations[0]
    assert isinstance(fn_decl, FnDecl)
    assert fn_decl.pub == False
    assert fn_decl.name == "main"
    assert fn_decl.ret_type.name == "int"
    assert len(fn_decl.body) == 1
    return_stmt = fn_decl.body[0]
    assert isinstance(return_stmt, Return)
    expr = return_stmt.expr
    assert isinstance(expr, Integer)
    assert expr.value == 0
    
def test_fn_w_params():
    source = textwrap.dedent('''
    fn add(a: int, b: int) -> int
        return a + b
    ''')
    program = parse(source)
    assert isinstance(program, Program)
    assert len(program.declarations) == 1
    fn_decl = program.declarations[0]
    assert isinstance(fn_decl, FnDecl)
    assert fn_decl.pub == False
    assert fn_decl.name == "add"
    assert len(fn_decl.params) == 2
    assert fn_decl.params[0].name == "a" and fn_decl.params[0].type.name == "int"
    assert fn_decl.params[1].name == "b" and fn_decl.params[1].type.name == "int"
    assert fn_decl.ret_type.name == "int"
    assert len(fn_decl.body) == 1
    return_stmt = fn_decl.body[0]
    assert isinstance(return_stmt, Return)
    expr = return_stmt.expr
    assert isinstance(expr, BinaryOp)
    assert expr.op == "+"
    assert isinstance(expr.lhs, Ident)
    assert expr.lhs.name == "a"
    assert isinstance(expr.rhs, Ident)
    assert expr.rhs.name == "b"
    
def test_struct_decl():
    source = textwrap.dedent('''
    struct Point
        x: int
        y: int
    ''')
    program = parse(source)
    assert isinstance(program, Program)
    assert len(program.declarations) == 1
    struct_decl = program.declarations[0]
    assert isinstance(struct_decl, StructDecl)
    assert struct_decl.name == "Point"
    assert len(struct_decl.fields) == 2
    assert struct_decl.fields[0].name == "x" and struct_decl.fields[0].type.name == "int"
    assert struct_decl.fields[1].name == "y" and struct_decl.fields[1].type.name == "int"
    
    
def test_simple_enum_decl():
    source = textwrap.dedent('''
    enum Color
        Red
        Green
        Blue
    ''')
    program = parse(source)
    assert isinstance(program, Program)
    assert len(program.declarations) == 1
    enum_decl = program.declarations[0]
    assert isinstance(enum_decl, EnumDecl)
    assert enum_decl.name == "Color"
    assert len(enum_decl.variants) == 3
    assert enum_decl.variants[0].name == "Red"
    assert enum_decl.variants[1].name == "Green"
    assert enum_decl.variants[2].name == "Blue"
    
def test_if_stmt():
    source = textwrap.dedent('''
    fn main() -> int
        const a = 10
        const b = 20
        if a > b
            return a
        else if a < b
            return b
        else
            return 0
    ''')
    program = parse(source)
    fn_body = program.declarations[0].body
    const_a = fn_body[0]
    assert isinstance(const_a, VarDecl)
    assert const_a.name == "a"
    assert isinstance(const_a.expr, Integer)
    assert const_a.expr.value == 10
    const_b = fn_body[1]
    assert isinstance(const_b, VarDecl)
    assert const_b.name == "b"
    assert isinstance(const_b.expr, Integer)
    assert const_b.expr.value == 20
    if_stmt = fn_body[2]
    assert isinstance(if_stmt, If)
    assert isinstance(if_stmt.cond, BinaryOp)
    assert if_stmt.cond.op == ">"
    ret_on_true = if_stmt.body[0]
    assert isinstance(ret_on_true, Return)
    assert isinstance(if_stmt.else_body, If)
    else_if_stmt = if_stmt.else_body
    assert isinstance(else_if_stmt.cond, BinaryOp)
    assert else_if_stmt.cond.op == "<"
    ret_on_else_if = else_if_stmt.body[0]
    assert isinstance(ret_on_else_if, Return)
    assert isinstance(else_if_stmt.else_body, list)
    ret_on_else = else_if_stmt.else_body[0]
    assert isinstance(ret_on_else, Return)
    assert isinstance(ret_on_else.expr, Integer)
    assert ret_on_else.expr.value == 0
    
def test_while_stmt():
    source = textwrap.dedent('''
    fn main() -> int
        let a = 10
        while a > 0
            a = a - 1
        return a
    ''')
    program = parse(source)
    fn_body = program.declarations[0].body
    while_stmt = fn_body[1]
    assert isinstance(while_stmt, While)
    assert isinstance(while_stmt.cond, BinaryOp)
    assert while_stmt.cond.op == ">"
    assert isinstance(while_stmt.body, list)
    assert len(while_stmt.body) == 1
    assert isinstance(while_stmt.body[0], Assign)
    assert isinstance(fn_body[2], Return)

def test_continue_stmt():
    source = textwrap.dedent('''
    fn main() -> int
        loop
            continue
        return 0
    ''')
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], Loop)
    loop_body = fn_body[0].body
    assert isinstance(loop_body[0], Continue)
    
    

def test_assigns():
    source = textwrap.dedent('''
    fn main() -> int
        let a = 10
        a = a + 1
        const b = a
        a = b + 1
        return a
    ''')
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], VarDecl)
    assert fn_body[0].name == "a"
    assert isinstance(fn_body[0].expr, Integer)
    assert fn_body[0].expr.value == 10
    assert isinstance(fn_body[1], Assign)
    assert isinstance(fn_body[2], VarDecl)
    assert isinstance(fn_body[3], Assign)
    
def test_loop():
    source = textwrap.dedent('''
    fn main() -> int
        let a = 10
        loop
            a = a - 1
            if a == 0
                break
        return a
    ''')
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], VarDecl)
    assert isinstance(fn_body[1], Loop)
    loop_body = fn_body[1].body
    assert isinstance(loop_body[0], Assign)
    assert isinstance(loop_body[1], If)
    if_stmt = loop_body[1]
    assert isinstance(if_stmt.cond, BinaryOp)
    assert isinstance(if_stmt.body[0], Break)
    assert isinstance(fn_body[2], Return)

