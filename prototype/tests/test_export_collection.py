from prototype.ast import Module, ModuleManager, ExportSpec, Symbol, Declaration
from prototype.ast.passes.export_collection import (
    export_collection_pass,
    DuplicateExportError,
    UndefinedExportError,
)


class DummyDecl(Declaration):
    def __init__(self):
        super().__init__(line=0)


def add_declared_symbol(module: Module, name: str, decl: Declaration):
    module.nodes[decl.id] = decl
    module.symbol_table.table[-1].symbols[name] = Symbol(
        name=name, ast_id=decl.id, parent_scope_id=-1
    )
    module.top_level_nodes.append(decl)


def test_valid_exports():
    mm = ModuleManager()
    mod = Module("mod1.vlp")
    d1 = DummyDecl()
    d2 = DummyDecl()
    add_declared_symbol(mod, "foo", d1)
    add_declared_symbol(mod, "bar", d2)
    mod.top_level_nodes.append(ExportSpec({"foo", "bar"}, 0))
    mm.add_module(mod)

    _, errors = export_collection_pass(mm)
    assert not errors
    assert set(mod.exports.keys()) == {"foo", "bar"}


def test_undefined_export_error():
    mm = ModuleManager()
    mod = Module("mod2.vlp")
    decl = DummyDecl()
    add_declared_symbol(mod, "foo", decl)
    mod.top_level_nodes.append(ExportSpec({"foo", "baz"}, 0))
    mm.add_module(mod)

    _, errors = export_collection_pass(mm)
    assert any(
        isinstance(e, UndefinedExportError) and e.export_name == "baz" for e in errors
    )
    assert "foo" in mod.exports
    assert "baz" not in mod.exports


def test_duplicate_export_error():
    mm = ModuleManager()
    mod = Module("mod3.vlp")
    decl = DummyDecl()
    add_declared_symbol(mod, "x", decl)
    mod.top_level_nodes.append(ExportSpec({"x"}, 0))
    mod.top_level_nodes.append(ExportSpec({"x"}, 1))
    mm.add_module(mod)

    _, errors = export_collection_pass(mm)
    assert any(
        isinstance(e, DuplicateExportError) and e.export_name == "x" for e in errors
    )
    assert list(mod.exports.keys()).count("x") == 1


def test_exports_across_multiple_modules_are_independent():
    mm = ModuleManager()

    mod_a = Module("a.vlp")
    mod_b = Module("b.vlp")

    decl_a = DummyDecl()
    decl_b = DummyDecl()
    add_declared_symbol(mod_a, "x", decl_a)
    add_declared_symbol(mod_b, "x", decl_b)

    mod_a.top_level_nodes.append(ExportSpec({"x"}, 0))
    mod_b.top_level_nodes.append(ExportSpec({"x"}, 0))

    mm.add_module(mod_a)
    mm.add_module(mod_b)

    _, errors = export_collection_pass(mm)
    assert not errors
    assert "x" in mod_a.exports
    assert "x" in mod_b.exports


def test_no_exports_specified():
    mm = ModuleManager()
    mod = Module("empty.vlp")
    decl = DummyDecl()
    add_declared_symbol(mod, "foo", decl)
    # no ExportSpec
    mm.add_module(mod)

    _, errors = export_collection_pass(mm)
    assert not errors
    assert mod.exports == {}
