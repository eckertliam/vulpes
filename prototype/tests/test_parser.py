from prototype.parser import (
    Array,
    Assign,
    BinaryOp,
    Break,
    Call,
    CallAttr,
    Continue,
    Else,
    EnumDecl,
    EnumStructExpr,
    EnumTupleExpr,
    EnumUnitExpr,
    FieldInit,
    GetIndex,
    GetAttr,
    NamedTypeAnnotation,
    String,
    StructExpr,
    StructField,
    Tuple,
    TypeAliasDecl,
    Ident,
    If,
    ImplDecl,
    Loop,
    StructDecl,
    TupleTypeAnnotation,
    TypeAnnotation,
    VarDecl,
    While,
    parse,
    Program,
    FnDecl,
    Statement,
    Return,
    Integer,
)
import pytest
import textwrap


def test_empty_program():
    program = parse("")
    assert isinstance(program, Program)
    assert len(program.declarations) == 0


def test_simple_fn_decl():
    source = textwrap.dedent(
        """
    fn main() -> int
        return 0     
    """
    )
    program = parse(source)
    assert isinstance(program, Program)
    assert len(program.declarations) == 1
    fn_decl = program.declarations[0]
    assert isinstance(fn_decl, FnDecl)
    assert fn_decl.pub == False
    assert fn_decl.name == "main"
    assert isinstance(fn_decl.ret_type, NamedTypeAnnotation)
    assert fn_decl.ret_type.name == "int"
    assert len(fn_decl.body) == 1
    return_stmt = fn_decl.body[0]
    assert isinstance(return_stmt, Return)
    expr = return_stmt.expr
    assert isinstance(expr, Integer)
    assert expr.value == 0


def test_fn_w_params():
    source = textwrap.dedent(
        """
    fn add(a: int, b: int) -> int
        return a + b
    """
    )
    program = parse(source)
    assert isinstance(program, Program)
    assert len(program.declarations) == 1
    fn_decl = program.declarations[0]
    assert isinstance(fn_decl, FnDecl)
    assert fn_decl.pub == False
    assert fn_decl.name == "add"
    assert len(fn_decl.params) == 2
    assert (
        fn_decl.params[0].name == "a"
        and isinstance(fn_decl.params[0].type_annotation, NamedTypeAnnotation)
        and fn_decl.params[0].type_annotation.name == "int"
    )
    assert (
        fn_decl.params[1].name == "b"
        and isinstance(fn_decl.params[1].type_annotation, NamedTypeAnnotation)
        and fn_decl.params[1].type_annotation.name == "int"
    )
    assert (
        isinstance(fn_decl.ret_type, NamedTypeAnnotation)
        and fn_decl.ret_type.name == "int"
    )
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
    source = textwrap.dedent(
        """
    struct Point
        x: int
        y: int
    """
    )
    program = parse(source)
    assert isinstance(program, Program)
    assert len(program.declarations) == 1
    struct_decl = program.declarations[0]
    assert isinstance(struct_decl, StructDecl)
    assert struct_decl.name == "Point"
    assert len(struct_decl.fields) == 2
    assert (
        struct_decl.fields[0].name == "x"
        and isinstance(struct_decl.fields[0].type_annotation, NamedTypeAnnotation)
        and struct_decl.fields[0].type_annotation.name == "int"
    )
    assert (
        struct_decl.fields[1].name == "y"
        and isinstance(struct_decl.fields[1].type_annotation, NamedTypeAnnotation)
        and struct_decl.fields[1].type_annotation.name == "int"
    )


# TODO: test tuple enums
# TODO: test struct enums
def test_simple_enum_decl():
    source = textwrap.dedent(
        """
    enum Color
        Red
        Green
        Blue
    """
    )
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
    source = textwrap.dedent(
        """
    fn main() -> int
        const a = 10
        
        const b = 20
        if a > b
            return a
        else if a < b
            return b
        else
            return 0
    """
    )
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
    assert isinstance(if_stmt.else_body, Else)
    else_stmt = if_stmt.else_body


def test_while_stmt():
    source = textwrap.dedent(
        """
    fn main() -> int
        let a = 10
        while a > 0
            a = a - 1
        return a
    """
    )
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
    source = textwrap.dedent(
        """
    fn main() -> int
        loop
            continue
        return 0
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], Loop)
    loop_body = fn_body[0].body
    assert isinstance(loop_body[0], Continue)


def test_assigns():
    source = textwrap.dedent(
        """
    fn main() -> int
        let a = 10
        a = a + 1
        const b = a
        a = b + 1
        return a
    """
    )
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
    source = textwrap.dedent(
        """
    fn main() -> int
        let a = 10
        loop
            a = a - 1
            if a == 0
                break
        return a
    """
    )
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


def test_array_expr():
    source = textwrap.dedent(
        """
    fn main() -> int
        const a = [1, 2, 3]
        return a[0]
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], VarDecl)
    const_a = fn_body[0]
    assert isinstance(const_a.expr, Array)
    assert len(const_a.expr.elems) == 3
    assert isinstance(const_a.expr.elems[0], Integer)
    assert const_a.expr.elems[0].value == 1
    assert isinstance(const_a.expr.elems[1], Integer)
    assert const_a.expr.elems[1].value == 2
    assert isinstance(const_a.expr.elems[2], Integer)
    assert const_a.expr.elems[2].value == 3
    assert isinstance(fn_body[1], Return)
    return_stmt = fn_body[1]
    assert isinstance(return_stmt.expr, GetIndex)
    assert isinstance(return_stmt.expr.obj, Ident)
    assert return_stmt.expr.obj.name == "a"
    assert isinstance(return_stmt.expr.index, Integer)
    assert return_stmt.expr.index.value == 0


def test_binary_expr_chaining():
    source = textwrap.dedent(
        """
    fn main() -> int
        const result = 1 + 2 * 3
        return result
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    const_result = fn_body[0]
    assert isinstance(const_result, VarDecl)
    expr = const_result.expr
    assert isinstance(expr, BinaryOp)
    assert expr.op == "+"
    assert isinstance(expr.lhs, Integer)
    assert expr.lhs.value == 1
    assert isinstance(expr.rhs, BinaryOp)
    assert expr.rhs.op == "*"
    assert isinstance(expr.rhs.lhs, Integer)
    assert expr.rhs.lhs.value == 2
    assert isinstance(expr.rhs.rhs, Integer)
    assert expr.rhs.rhs.value == 3
    return_stmt = fn_body[1]
    assert isinstance(return_stmt, Return)
    assert isinstance(return_stmt.expr, Ident)
    assert return_stmt.expr.name == "result"


def test_paren_expr_binding():
    source = textwrap.dedent(
        """
    fn main() -> int
        const result = (1 + 2) * 3
        return result
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    const_result = fn_body[0]
    assert isinstance(const_result, VarDecl)
    expr = const_result.expr
    assert isinstance(expr, BinaryOp)
    assert expr.op == "*"
    assert isinstance(expr.lhs, BinaryOp)
    assert expr.lhs.op == "+"
    assert isinstance(expr.lhs.lhs, Integer)
    assert expr.lhs.lhs.value == 1
    assert isinstance(expr.lhs.rhs, Integer)
    assert expr.lhs.rhs.value == 2
    assert isinstance(expr.rhs, Integer)
    assert expr.rhs.value == 3
    return_stmt = fn_body[1]
    assert isinstance(return_stmt, Return)
    assert isinstance(return_stmt.expr, Ident)
    assert return_stmt.expr.name == "result"


def test_impl():
    source = textwrap.dedent(
        """
    impl Animal
        fn make_sound() -> str
            return "Woof"

        fn move() -> void
            print("Moving")
    """
    )
    program = parse(source)
    impl_decl = program.declarations[0]
    assert isinstance(impl_decl, ImplDecl)
    assert impl_decl.name == "Animal"
    assert len(impl_decl.methods) == 2
    method = impl_decl.methods[0]
    assert isinstance(method, FnDecl)
    assert method.name == "make_sound"
    assert isinstance(method.ret_type, NamedTypeAnnotation)
    assert method.ret_type.name == "str"
    method = impl_decl.methods[1]
    assert isinstance(method, FnDecl)
    assert method.name == "move"
    assert isinstance(method.ret_type, NamedTypeAnnotation)
    assert method.ret_type.name == "void"


def test_type_aliases():
    source = textwrap.dedent(
        """
    type Coord = (int, int)
    
    """
    )
    program = parse(source)
    type_alias = program.declarations[0]
    assert isinstance(type_alias, TypeAliasDecl)
    assert type_alias.name == "Coord"
    assert isinstance(type_alias.type_annotation, TupleTypeAnnotation)
    assert len(type_alias.type_annotation.elem_types) == 2
    assert isinstance(type_alias.type_annotation.elem_types[0], TypeAnnotation)
    assert isinstance(type_alias.type_annotation.elem_types[1], TypeAnnotation)


# TODO: test tuples SEE main.py first
# TODO: test struct exprs
def test_struct_exprs():
    source = textwrap.dedent(
        """
    fn main() -> int
        const p = Point { x: 1, y: 2 }
        return p.x
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], VarDecl)
    const_p = fn_body[0]
    assert isinstance(const_p.expr, StructExpr)
    assert isinstance(const_p.expr.fields[0], FieldInit)
    assert isinstance(const_p.expr.fields[1], FieldInit)
    assert isinstance(fn_body[1], Return)
    assert isinstance(fn_body[1].expr, GetAttr)


# TODO: test enum exprs
def test_enum_exprs():
    source = textwrap.dedent(
        """
    fn main() -> int
        const c = Color::Red
        const c2 = Animal::Dog { name: "Fido" }
        const c3 = Coordinates::Point(1, 2)
        return c
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], VarDecl)
    color_enum = fn_body[0].expr
    assert isinstance(color_enum, EnumUnitExpr)
    assert color_enum.name == "Color"
    assert color_enum.unit == "Red"
    assert isinstance(fn_body[1], VarDecl)
    dog_enum = fn_body[1].expr
    assert isinstance(dog_enum, EnumStructExpr)
    assert dog_enum.name == "Animal"
    assert dog_enum.unit == "Dog"
    assert len(dog_enum.fields) == 1
    assert isinstance(dog_enum.fields[0], FieldInit)
    assert isinstance(fn_body[2], VarDecl)
    point_enum = fn_body[2].expr
    assert isinstance(point_enum, EnumTupleExpr)
    assert point_enum.name == "Coordinates"
    assert point_enum.unit == "Point"
    assert len(point_enum.elems) == 2
    assert isinstance(point_enum.elems[0], Integer)
    assert point_enum.elems[0].value == 1
    assert isinstance(point_enum.elems[1], Integer)
    assert point_enum.elems[1].value == 2


# TODO: test method calls
def test_method_calls():
    source = textwrap.dedent(
        """
    fn main() -> int
        const p = Point { x: 1, y: 2 }
        return p.move(1, 1)
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    return_stmt = fn_body[1]
    assert isinstance(return_stmt, Return)
    assert isinstance(return_stmt.expr, CallAttr)
    call_attr = return_stmt.expr
    assert isinstance(call_attr.obj, Ident)
    assert call_attr.obj.name == "p"
    assert call_attr.attr == "move"
    assert len(call_attr.args) == 2
    assert isinstance(call_attr.args[0], Integer)
    assert call_attr.args[0].value == 1
    assert isinstance(call_attr.args[1], Integer)
    assert call_attr.args[1].value == 1


def test_fn_calls():
    source = textwrap.dedent(
        """
    fn main() -> int
        return add(1, 2)
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], Return)
    assert isinstance(fn_body[0].expr, Call)
    call = fn_body[0].expr
    assert isinstance(call.callee, Ident)
    assert call.callee.name == "add"
    assert len(call.args) == 2
    assert isinstance(call.args[0], Integer)
    assert call.args[0].value == 1
    assert isinstance(call.args[1], Integer)
    assert call.args[1].value == 2


def test_field_chaining():
    source = textwrap.dedent(
        """
    fn main() -> int
        return x.y.z
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], Return)
    assert isinstance(fn_body[0].expr, GetAttr)
    get_attr = fn_body[0].expr
    assert isinstance(get_attr.obj, GetAttr)
    assert isinstance(get_attr.obj.obj, Ident)
    assert get_attr.obj.obj.name == "x"
    assert get_attr.obj.attr == "y"
    assert isinstance(get_attr.obj.obj, Ident)
    assert get_attr.obj.obj.name == "x"


def test_expr_stmt():
    source = textwrap.dedent(
        """
    fn main() -> int
        a + b + c
        return 0
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], BinaryOp)
    binary_op = fn_body[0]
    assert isinstance(binary_op.lhs, BinaryOp)
    assert isinstance(binary_op.rhs, Ident)
    assert isinstance(binary_op.lhs.lhs, Ident)
    assert binary_op.lhs.lhs.name == "a"
    assert isinstance(binary_op.lhs.rhs, Ident)
    assert binary_op.lhs.rhs.name == "b"
    assert isinstance(binary_op.rhs, Ident)
    assert binary_op.rhs.name == "c"


# test a function that returns a function and is called
def test_fn_ret_fn():
    source = textwrap.dedent(
        """
    fn main() -> int
        return macro_fn("+")(1, 2)
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], Return)
    assert isinstance(fn_body[0].expr, Call)
    outer_call = fn_body[0].expr
    assert isinstance(outer_call.callee, Call)
    inner_call = outer_call.callee
    assert isinstance(inner_call.callee, Ident)
    assert inner_call.callee.name == "macro_fn"
    assert len(inner_call.args) == 1
    assert isinstance(inner_call.args[0], String)
    assert inner_call.args[0].value == "+"
    assert len(outer_call.args) == 2
    assert isinstance(outer_call.args[0], Integer)
    assert outer_call.args[0].value == 1
    assert isinstance(outer_call.args[1], Integer)
    assert outer_call.args[1].value == 2


def test_tuple_expr():
    source = textwrap.dedent(
        """
    fn main() -> int
        return (1, 2)
    """
    )
    program = parse(source)
    fn_body = program.declarations[0].body
    assert isinstance(fn_body[0], Return)
    assert isinstance(fn_body[0].expr, Tuple)
    tuple_expr = fn_body[0].expr
    assert len(tuple_expr.elems) == 2
    assert isinstance(tuple_expr.elems[0], Integer)
    assert tuple_expr.elems[0].value == 1
    assert isinstance(tuple_expr.elems[1], Integer)
    assert tuple_expr.elems[1].value == 2
