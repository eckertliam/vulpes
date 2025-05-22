
import pytest

from prototype.ast import Module, ModuleManager
from prototype.ast.ast import FnDecl, TypeAnnotation, Param, TypeParam, Integer
from prototype.ast.passes.name_res import name_res_pass, DuplicateDefinitionError


def make_fn(name: str, line: int = 1) -> FnDecl:
    return FnDecl(
        name=name,
        type_params=[],
        params=[],
        ret_type=TypeAnnotation(line),
        body=[],
        line=line,
    )


def test_duplicate_function_declaration():
    module = Module()
    module.push(make_fn("foo"))
    module.push(make_fn("foo"))  # Duplicate

    manager = ModuleManager()
    manager.add_module(module)

    _, errors = name_res_pass(manager)
    assert len(errors) == 1
    assert "foo" in str(errors[0])


def test_unique_function_declarations():
    module = Module()
    module.push(make_fn("foo"))
    module.push(make_fn("bar"))

    manager = ModuleManager()
    manager.add_module(module)

    _, errors = name_res_pass(manager)
    assert len(errors) == 0


def test_duplicate_struct_and_function_names():
    from prototype.ast.ast import StructDecl, StructField, NamedTypeAnnotation

    struct = StructDecl(
        name="Thing",
        type_params=[],
        fields=[
            StructField(name="x", type_annotation=NamedTypeAnnotation("int", 1), line=1)
        ],
        line=1,
    )

    fn = make_fn("Thing", line=2)

    module = Module()
    module.push(struct)
    module.push(fn)  # Same name as struct

    manager = ModuleManager()
    manager.add_module(module)

    _, errors = name_res_pass(manager)
    assert len(errors) == 1
    assert "Thing" in str(errors[0])



from prototype.ast.ast import VarDecl, Ident, Integer, If, Bool

def make_var(name: str, line: int = 1) -> VarDecl:
    return VarDecl(
        mutable=False,
        name=name,
        type_annotation=None,
        expr=Integer(0, line),
        line=line,
    )

def test_duplicate_variable_in_same_scope():
    fn = make_fn("foo")
    fn.body.extend([
        make_var("x", 1),
        make_var("x", 2),  # Duplicate in same scope
    ])

    module = Module()
    module.push(fn)

    manager = ModuleManager()
    manager.add_module(module)

    _, errors = name_res_pass(manager)
    assert len(errors) == 1
    assert "x" in str(errors[0])


def test_variable_shadowing_in_nested_scope():
    inner_if = If(
        cond=Bool(True, 2),
        body=[make_var("x", 3)],  # Inner scope
        else_body=None,
        line=2,
    )

    fn = make_fn("foo")
    fn.body.extend([
        make_var("x", 1),  # Outer scope
        inner_if
    ])

    module = Module()
    module.push(fn)

    manager = ModuleManager()
    manager.add_module(module)

    _, errors = name_res_pass(manager)
    assert len(errors) == 0
