from prototype.ast import (
    ModuleManager,
    NamedTypeAnnotation,
    VarDecl,
    Integer,
    Return,
    Ident,
    BinaryOp,
)
from prototype.ast.passes import (
    name_ref_pass,
    Pipeline,
    module_res_pass,
    name_res_pass,
    export_collection_pass,
    import_linker_pass,
)
from prototype.ast.passes.name_ref import UndefinedSymbolError
from prototype.module_builder import ModuleBuilder

pipeline = Pipeline(
    [
        module_res_pass,
        name_res_pass,
        export_collection_pass,
        import_linker_pass,
        name_ref_pass,
    ]
)


def test_valid_name_ref():
    builder = ModuleBuilder("test_mod")
    i64 = NamedTypeAnnotation("i64", 1)
    fn_builder = builder.build_fn_decl("test_fn").add_param("t", i64)
    fn_builder.set_ret_type(i64)
    fn_builder.add_statement(VarDecl(False, "x", i64, Integer(1, 1), 1))
    fn_builder.add_statement(VarDecl(False, "y", i64, Integer(2, 1), 1))
    fn_builder.add_statement(VarDecl(False, "z", i64, Integer(3, 1), 1))
    fn_builder.add_statement(Return(BinaryOp("+", Ident("x", 1), Ident("y", 1), 1), 1))
    fn_builder.build()
    module = builder.build()
    mm = ModuleManager()
    mm.add_module(module)
    mm, errors = pipeline(mm)
    assert len(errors) == 0


def test_invalid_name_ref():
    builder = ModuleBuilder("test_mod")
    i64 = NamedTypeAnnotation("i64", 1)
    fn_builder = builder.build_fn_decl("test_fn").add_param("t", i64)
    fn_builder.set_ret_type(i64)
    fn_builder.add_statement(VarDecl(False, "x", i64, Integer(1, 1), 1))
    fn_builder.add_statement(VarDecl(False, "y", i64, Ident("z", 1), 1))
    fn_builder.add_statement(VarDecl(False, "z", i64, Integer(3, 1), 1))
    fn_builder.add_statement(Return(BinaryOp("+", Ident("a", 1), Ident("y", 1), 1), 1))
    fn_builder.build()
    module = builder.build()
    mm = ModuleManager()
    mm.add_module(module)
    mm, errors = pipeline(mm)
    assert len(errors) == 1
    assert isinstance(errors[0], UndefinedSymbolError)