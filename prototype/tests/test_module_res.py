"""Testing module res pass in ast/passes"""

from prototype.ast import Module, ExportSpec, Import, ModuleManager
from prototype.ast.passes import module_res_pass
from prototype.ast.passes.module_res import (
    ModuleDoesNotExist,
    ImportFromSelfError,
    ImportTargetNotFoundError,
)


def test_basic_successful_import():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    module_a.push(ExportSpec(exports={"foo"}, line=1))

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"foo"}, line=1))

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert errors == []


def test_import_from_nonexistent_module():
    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"foo"}, line=1))

    manager = ModuleManager()
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert any(
        isinstance(err, ModuleDoesNotExist) and err.module_name == "A"
        for err in errors
    )


def test_import_from_self():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    module_a.push(Import(module="A", targets={"foo"}, line=1))

    manager = ModuleManager()
    manager.add_module(module_a)

    _, errors = module_res_pass(manager)

    assert any(isinstance(err, ImportFromSelfError) for err in errors)


def test_import_non_exported_name():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    # no ExportSpec means nothing is exported

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"foo"}, line=1))

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert any(
        isinstance(err, ImportTargetNotFoundError) and err.target == "foo"
        for err in errors
    )


def test_import_mixed_valid_and_invalid():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    module_a.push(ExportSpec(exports={"foo"}, line=1))

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"foo", "bar"}, line=1))

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    # should only error on 'bar'
    assert len(errors) == 1
    assert isinstance(errors[0], ImportTargetNotFoundError)
    assert errors[0].target == "bar"


# Additional tests for module_res_pass
def test_import_with_empty_targets():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    module_a.push(ExportSpec(exports={"foo"}, line=1))

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets=set(), line=1))

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert errors == []


def test_import_from_module_with_empty_exports():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    module_a.push(ExportSpec(exports=set(), line=1))

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"foo"}, line=1))

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert any(
        isinstance(err, ImportTargetNotFoundError) and err.target == "foo"
        for err in errors
    )


def test_multiple_imports_with_one_invalid():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    module_a.push(ExportSpec(exports={"foo"}, line=1))

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"foo"}, line=1))
    module_b.push(Import(module="A", targets={"bar"}, line=2))

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert len(errors) == 1
    assert isinstance(errors[0], ImportTargetNotFoundError)
    assert errors[0].target == "bar"


def test_import_from_module_with_no_top_level_nodes():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    # no top-level nodes

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"foo"}, line=1))

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert any(
        isinstance(err, ImportTargetNotFoundError) and err.target == "foo"
        for err in errors
    )


def test_import_case_sensitivity():
    module_a = Module(file_path="a.vlp")
    module_a.name = "A"
    module_a.push(ExportSpec(exports={"foo"}, line=1))

    module_b = Module(file_path="b.vlp")
    module_b.name = "B"
    module_b.push(Import(module="A", targets={"Foo"}, line=1))  # wrong case

    manager = ModuleManager()
    manager.add_module(module_a)
    manager.add_module(module_b)

    _, errors = module_res_pass(manager)

    assert any(
        isinstance(err, ImportTargetNotFoundError) and err.target == "Foo"
        for err in errors
    )
