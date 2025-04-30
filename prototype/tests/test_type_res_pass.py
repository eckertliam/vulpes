from prototype.parser import Program, parse
from prototype.passes import TypeResolutionPass, NameDeclarationPass, NameReferencePass
from prototype.types import ArrayType, FloatType, StructType, IntType
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
    type Numbers = [Number]
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
