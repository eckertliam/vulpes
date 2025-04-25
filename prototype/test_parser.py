from main import parse, Program, FnDecl, Statement, Return, Integer
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