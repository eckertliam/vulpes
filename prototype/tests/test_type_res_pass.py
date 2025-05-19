from prototype.parser import parse
from prototype.passes.type_res_pass import TypeResolutionPass
from prototype.passes.name_decl_pass import NameDeclarationPass
from prototype.passes.name_ref_pass import NameReferencePass
from prototype.symbol import Symbol
from prototype.types import (
    ArrayType,
    FloatType,
    FunctionType,
    StringType,
    StructType,
    IntType,
    TypeHole,
)
import textwrap


def test_struct_decl():
    source = textwrap.dedent(
        """
    struct Point
        x: int
        y: int
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # ensure no errors up to this point
    assert len(name_ref_pass.errors) == 0
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    # no errors should have been generated
    assert len(type_res_pass.errors) == 0
    # the struct should have been added to the type env
    point_type = type_res_pass.type_env.get_type("Point")
    assert point_type is not None
    assert isinstance(point_type, StructType)
    assert len(point_type.fields) == 2
    assert point_type.fields["x"] == IntType()
    assert point_type.fields["y"] == IntType()


def test_dependent_type_resolution():
    source = textwrap.dedent(
        """
    struct Point
        x: Number
        y: Number
        
    type Number = float
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    # no errors should have been generated
    assert len(type_res_pass.errors) == 0
    # the struct should have been added to the type env
    point_type = type_res_pass.type_env.get_type("Point")
    assert point_type is not None
    assert isinstance(point_type, StructType)
    assert len(point_type.fields) == 2
    assert point_type.fields["x"] == FloatType()
    assert point_type.fields["y"] == FloatType()


def test_array_type_resolution():
    source = textwrap.dedent(
        """
    type Number = float
    type Numbers = [Number; 10]
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    # no errors should have been generated
    assert len(type_res_pass.errors) == 0
    # the type should have been added to the type env
    numbers_type = type_res_pass.type_env.get_type("Numbers")
    assert numbers_type is not None
    assert isinstance(numbers_type, ArrayType)
    assert numbers_type.elem_type == FloatType()
    assert numbers_type.size == 10

def test_recursive_type_alias():
    source = textwrap.dedent(
        """
    type A = B
    type B = A
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    # should produce at least one error due to recursion
    assert len(type_res_pass.errors) > 0
    # A and B should not be added to the type env
    assert type_res_pass.type_env.get_type("A") is None
    assert type_res_pass.type_env.get_type("B") is None


def test_recursive_struct_decl():
    source = textwrap.dedent(
        """
    struct Node
        value: int
        next: Node
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    # no errors should have been generated
    assert len(type_res_pass.errors) == 0
    # the struct should have been added to the type env
    node_type = type_res_pass.type_env.get_type("Node")
    assert node_type is not None
    assert isinstance(node_type, StructType)
    assert len(node_type.fields) == 2
    assert node_type.fields["value"] == IntType()
    assert node_type.fields["next"] == node_type


def test_simple_const():
    source = textwrap.dedent(
        """
    fn test() -> int
        const a: int = 1
        return a
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    # get the id of the fn
    fn_id = program.declarations[0].id
    # lookup the symbol for test and ensure check that it has a type
    symbol = type_res_pass.symbol_table.lookup("test")
    assert symbol is not None
    assert symbol.type == FunctionType([], IntType())
    # enter the fn's scope
    type_res_pass.symbol_table.enter_scope(fn_id)
    # lookup the symbol for a
    symbol = type_res_pass.symbol_table.lookup("a")
    assert symbol is not None
    assert symbol.type == IntType()


def test_type_hole():
    source = textwrap.dedent(
        """
    fn test() -> int
        const a = 1
        return a
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    # get the id of the fn
    fn_id = program.declarations[0].id
    # enter the fn's scope
    type_res_pass.symbol_table.enter_scope(fn_id)
    # lookup the symbol for a
    symbol = type_res_pass.symbol_table.lookup("a")
    assert symbol is not None
    assert isinstance(symbol, Symbol)
    assert isinstance(symbol.type, TypeHole)
