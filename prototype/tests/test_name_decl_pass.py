from prototype.parser import parse
import textwrap

from prototype.errors import NameResolutionError
from prototype.passes.name_decl_pass import NameDeclarationPass


def test_struct_decl():
    source = textwrap.dedent(
        """
    struct Point
        x: int
        y: int
    """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    assert len(decl_pass.symbol_table.table) == 1
    assert decl_pass.symbol_table.table[-1].symbols["Point"] is not None


def test_fn_decl():
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
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    assert decl_pass.symbol_table.table[-1].symbols["main"] is not None
    main_id = decl_pass.symbol_table.table[-1].symbols["main"].ast_id
    assert decl_pass.symbol_table.table[main_id].symbols["a"] is not None


def test_fn_in_fn():
    source = textwrap.dedent(
        """
    fn outer(a: int) -> int
        fn inner() -> int
            return a * 2
        return inner()
    """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    assert decl_pass.symbol_table.table[-1].symbols["outer"] is not None
    outer_id = decl_pass.symbol_table.table[-1].symbols["outer"].ast_id
    assert decl_pass.symbol_table.table[outer_id].symbols["a"] is not None
    assert decl_pass.symbol_table.table[outer_id].symbols["inner"] is not None


def test_var_shadowing_error():
    source = textwrap.dedent(
        """
    fn main() -> int
        let x = 5
        let x = 10
        return x
    """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 1
    assert isinstance(decl_pass.errors[0], NameResolutionError)


def test_union_decl():
    source = textwrap.dedent(
        """
        union Option
            Some(int)
            None
        """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    assert "Option" in decl_pass.symbol_table.table[-1].symbols
    option_symbol = decl_pass.symbol_table.table[-1].symbols["Option"]
    assert option_symbol is not None


def test_multiple_unions():
    source = textwrap.dedent(
        """
        union Result
            Ok(int)
            Err(string)

        union Status
            Pending
            Done
        """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    symbols = decl_pass.symbol_table.table[-1].symbols
    assert "Result" in symbols
    assert "Status" in symbols
    assert symbols["Result"] is not None
    assert symbols["Status"] is not None
