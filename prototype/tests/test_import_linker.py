from prototype.ast.passes import import_linker_pass
from prototype.ast.passes.import_linker import ModuleDoesNotExportError
from prototype.ast import ModuleManager, Module, Import
from prototype.ast.symbol import Symbol

def test_valid_imports():
    mm = ModuleManager()
    mod1 = Module("mod1")
    mod2 = Module("mod2")
    mod1.push(Import("mod2", {"foo"}, 0))
    mod2.exports["foo"] = Symbol(name="foo", ast_id=0, parent_scope_id=-1)

    mm.add_module(mod1)
    mm.add_module(mod2)

    _, errors = import_linker_pass(mm)
    assert not errors
    assert mod1.imports["foo"] == Symbol(name="foo", ast_id=0, parent_scope_id=-1)

def test_invalid_imports():
    mm = ModuleManager()
    mod1 = Module("mod1")
    mod2 = Module("mod2")
    mod1.push(Import("mod2", {"foo"}, 0))
    mm.add_module(mod1)
    mm.add_module(mod2)

    _, errors = import_linker_pass(mm)
    assert any(isinstance(e, ModuleDoesNotExportError) for e in errors)
    assert mod1.imports == {}
    assert len(errors) == 1
