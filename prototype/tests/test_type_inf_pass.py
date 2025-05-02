import textwrap

from prototype.parser import parse
from prototype.passes.name_decl_pass import NameDeclarationPass
from prototype.passes.name_ref_pass import NameReferencePass
from prototype.passes.type_res_pass import TypeResolutionPass
from prototype.passes.type_infer_pass import TypeInferencePass
from prototype.types import IntType
from prototype.symbol import Symbol


def test_simple_type_inf():
    source = textwrap.dedent(
        """
    fn test(a: int) -> int
        const b = a
        return b
    """
    )
    program = parse(source)
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    type_res_pass = TypeResolutionPass(name_ref_pass)
    type_res_pass.run()
    type_inf_pass = TypeInferencePass(type_res_pass)
    type_inf_pass.run()
    assert len(type_inf_pass.errors) == 0
    # enter the fn's scope
    type_inf_pass.symbol_table.enter_scope(program.declarations[0].id)
    # lookup the symbol for b
    symbol = type_inf_pass.symbol_table.lookup("b")
    assert symbol is not None
    assert isinstance(symbol, Symbol)
    assert symbol.type == IntType()
