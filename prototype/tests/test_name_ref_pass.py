from prototype.passes import NameDeclarationPass, NameReferencePass
from prototype.parser import Program, parse
import textwrap

from prototype.errors import NameResolutionError


def test_valid_ident():
    source = textwrap.dedent(
        """
    fn main() -> int
        const x = 1
        return x
    """
    )
    program = parse(source)
    assert len(program.declarations) == 1
    # pass through the name declaration pass
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    assert len(name_decl_pass.errors) == 0
    # pass through the name reference pass
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # check that there are no errors
    assert len(name_ref_pass.errors) == 0

def test_invalid_ident():
    source = textwrap.dedent(
        """
    fn main() -> int
        const x = 1
        return y
    """
    )
    program = parse(source)
    assert len(program.declarations) == 1
    # pass through the name declaration pass
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    assert len(name_decl_pass.errors) == 0
    # pass through the name reference pass
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # check that there are errors
    assert len(name_ref_pass.errors) == 1
    assert isinstance(name_ref_pass.errors[0], NameResolutionError)
    
def test_valid_assign():
    source = textwrap.dedent(
        """
    fn main() -> int
        const x = 1
        let y = 2
        y = x + y
        return y
    """
    )
    program = parse(source)
    assert len(program.declarations) == 1
    # pass through the name declaration pass
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    assert len(name_decl_pass.errors) == 0
    # pass through the name reference pass
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # check that there are no errors
    assert len(name_ref_pass.errors) == 0
    
def test_invalid_assign():
    source = textwrap.dedent(
        """
    fn main() -> int
        let x = 1
        x = y
        return y
    """
    )
    program = parse(source)
    assert len(program.declarations) == 1
    # pass through the name declaration pass
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    assert len(name_decl_pass.errors) == 0
    # pass through the name reference pass
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # check that there are errors
    # there should be two one for undefined assign and one for undefined return
    assert len(name_ref_pass.errors) == 2
    assert isinstance(name_ref_pass.errors[0], NameResolutionError)
    assert isinstance(name_ref_pass.errors[1], NameResolutionError)
    
def test_if_stmt():
    source = textwrap.dedent(
        """
    fn main() -> int
        const x: bool = true
        if x 
            return 1
        else
            return 0
    """
    )
    program = parse(source)
    assert len(program.declarations) == 1
    # pass through the name declaration pass
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    assert len(name_decl_pass.errors) == 0
    # pass through the name reference pass
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # check that there are no errors
    assert len(name_ref_pass.errors) == 0
    
def test_while_stmt():
    source = textwrap.dedent(
        """
    fn main() -> int
        const x = 1000
        let y = 0
        while x > y
            y = y + 1
        return y
    """
    )
    program = parse(source)
    assert len(program.declarations) == 1
    # pass through the name declaration pass
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    assert len(name_decl_pass.errors) == 0
    # pass through the name reference pass
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # check that there are no errors
    assert len(name_ref_pass.errors) == 0
    

def test_loop_stmt():
    source = textwrap.dedent(
        """
    fn main() -> int
        let y = 0
        loop
            if y > 1000
                break
            y = y + 1
        return y
    """
    )
    program = parse(source)
    assert len(program.declarations) == 1
    # pass through the name declaration pass
    name_decl_pass = NameDeclarationPass(program)
    name_decl_pass.run()
    assert len(name_decl_pass.errors) == 0
    # pass through the name reference pass
    name_ref_pass = NameReferencePass(name_decl_pass)
    name_ref_pass.run()
    # check that there are no errors
    assert len(name_ref_pass.errors) == 0
