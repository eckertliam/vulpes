from prototype.parser import Program, parse
from prototype.passes import TypeResolutionPass, NameDeclarationPass, NameReferencePass
from prototype.types import StructType, IntType
import textwrap

def test_struct_decl():
    source = textwrap.dedent("""
    struct Point
        x: int
        y: int
    """)
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
    source = textwrap.dedent("""
    struct Point
        x: Number
        y: Number
        
    type Number = float
    """)
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