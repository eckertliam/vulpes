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


def test_impl_decl():
    source = textwrap.dedent(
        """
    struct Dog
        name: str
        age: int

    impl Dog
        fn bark() -> str
            return "Woof!"
            
        fn grow() -> int
            self.age = self.age + 1
            return self.age
    """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    assert decl_pass.symbol_table.table[-1].symbols["Dog"] is not None
    # get Dog struct scope and check bark fn is in it
    dog_id = decl_pass.symbol_table.table[-1].symbols["Dog"].ast_id
    # check bark fn is in the dog scope
    assert decl_pass.symbol_table.table[dog_id].symbols["bark"] is not None
    # check grow fn is in the dog scope
    assert decl_pass.symbol_table.table[dog_id].symbols["grow"] is not None
    grow_id = decl_pass.symbol_table.table[dog_id].symbols["grow"].ast_id
    # check self param is in the grow fn scope
    assert decl_pass.symbol_table.table[grow_id].symbols["self"] is not None


def test_bad_impl():
    source = textwrap.dedent(
        """
    struct Dog
        name: str
        age: int
        
    impl Cat
        fn bark() -> str
            return "Meow!"
    """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 1
    assert isinstance(decl_pass.errors[0], NameResolutionError)


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


def test_trait_decl():
    source = textwrap.dedent(
        """
    trait Animal
        fn make_sound() -> str
    """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    assert decl_pass.symbol_table.table[-1].symbols["Animal"] is not None
    animal_id = decl_pass.symbol_table.table[-1].symbols["Animal"].ast_id
    assert decl_pass.symbol_table.table[animal_id].symbols["make_sound"] is not None


def test_trait_impl_decl():
    source = textwrap.dedent(
        """
    trait Animal
        fn make_sound() -> str
    
    struct Dog
        name: str
        age: int
        
    impl Animal for Dog
        fn make_sound() -> str
            return "Woof!"
    """
    )
    program = parse(source)
    decl_pass = NameDeclarationPass(program)
    decl_pass.run()
    assert len(decl_pass.errors) == 0
    assert decl_pass.symbol_table.table[-1].symbols["Dog"] is not None
    dog_id = decl_pass.symbol_table.table[-1].symbols["Dog"].ast_id
    assert decl_pass.symbol_table.table[dog_id].symbols["make_sound"] is not None
    make_sound_id = decl_pass.symbol_table.table[dog_id].symbols["make_sound"].ast_id
    assert decl_pass.symbol_table.table[make_sound_id].symbols["self"] is not None
