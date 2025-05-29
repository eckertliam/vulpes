import prototype.ast as ast
from prototype.types import (
    IntType,
)
from prototype.module_builder import ModuleBuilder
from prototype.ast.passes import (
    Pipeline,
    module_res_pass,
    name_res_pass,
    export_collection_pass,
    import_linker_pass,
    name_ref_pass,
    type_collection_pass,
    type_norm_pass,
)

pipeline = Pipeline(
    [
        module_res_pass,
        name_res_pass,
        export_collection_pass,
        import_linker_pass,
        name_ref_pass,
        type_collection_pass,
        type_norm_pass,
    ]
)

def test_simple_type_norm():
    mb = ModuleBuilder("test")
    fn_decl_builder = mb.build_fn_decl("test_fn")
    fn_decl_builder.add_param("x", ast.NamedTypeAnnotation("i64", 0))
    fn_decl_builder.set_ret_type(ast.NamedTypeAnnotation("i64", 0))
    fn_decl_builder.add_statement(ast.VarDecl(False, "t", None, ast.Ident("x", 1), 1))
    fn_decl_builder.add_statement(ast.Return(ast.Ident("t", 2), 2))
    fn_decl_builder.build()
    module_manager = ast.ModuleManager()
    module_manager.add_module(mb.build())
    mm, errors = pipeline(module_manager)
    assert len(errors) == 0
    test_mod = mm.get_module("test")
    assert test_mod is not None, "Test module not found"
    test_fn_sym = test_mod.symbol_table.lookup_global("test_fn")
    assert test_fn_sym is not None, "Test function not found in module's symbol table"
    test_fn_decl = test_mod.get_node(test_fn_sym.ast_id)
    assert test_fn_decl is not None, "Test function not found in module's AST"
    assert isinstance(test_fn_decl, ast.FnDecl), "Test function is not a function declaration"
    fn_params = test_fn_decl.params
    assert len(fn_params) == 1, "Test function has incorrect number of parameters"
    assert fn_params[0].name == "x", "Test function has incorrect parameter name"
    assert fn_params[0].symbol is not None, "Test function has incorrect parameter type"
    assert fn_params[0].symbol.type == IntType(), "Test function has incorrect parameter type"
    fn_ret_type = test_fn_decl.ret_type
    assert fn_ret_type is not None, "Test function has incorrect return type"
    assert fn_ret_type.symbol is not None, "Test function has incorrect return type" 
    assert fn_ret_type.symbol.type == IntType(), "Test function has incorrect return type"
    fn_body = test_fn_decl.body
    assert len(fn_body) == 2, "Test function has incorrect number of statements"
    var_decl = fn_body[0]
    assert isinstance(var_decl, ast.VarDecl), "Test function has incorrect statement type"
    assert var_decl.expr.symbol is not None, "Test function has incorrect variable expression"
    assert var_decl.expr.symbol.type == IntType(), "Test function has incorrect variable expression type"
    return_stmt = fn_body[1]
    assert isinstance(return_stmt, ast.Return), "Test function has incorrect statement type"
    assert return_stmt.expr is not None, "Test function has incorrect return expression"
    assert return_stmt.expr.symbol is not None, "Test function has incorrect return expression"
    assert return_stmt.expr.symbol.type == IntType(), "Test function has incorrect return expression type"
    
    