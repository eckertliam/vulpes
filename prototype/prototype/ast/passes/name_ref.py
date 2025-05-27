from itertools import chain
from typing import List, Optional
from prototype.errors import VulpesError
from prototype.ast import (
    Assign,
    Else,
    Expr,
    FnDecl,
    If,
    Loop,
    Return,
    Statement,
    TopLevelNode,
    VarDecl,
    While,
    Module,
    ModuleManager,
    Ident,
    AccessField,
    ArrayExpr,
    BinaryOp,
    Call,
    GetIndex,
    StructExpr,
    UnaryOp,
)
from prototype.ast.symbol import Symbol
from .pass_types import PassResult


class UndefinedSymbolError(VulpesError):
    def __init__(self, name: str, module: str):
        super().__init__(f"Undefined symbol: {name} in module: {module}")


def name_ref_pass(
    module_manager: ModuleManager,
    prev_result: List[VulpesError] = [],
) -> PassResult:
    """The name reference pass walks the AST and verifies that all names are valid references to symbols.

    Args:
        module_manager (ModuleManager): The module manager to run the pass on.
        prev_result (List[VulpesError]): A list of errors from previous passes

    Returns:
        Tuple[ModuleManager, List[VulpesError]]: The module manager with the pass run and a list of errors.
    """
    return module_manager, prev_result + list(
        chain.from_iterable(
            visit_module(module) for module in module_manager.modules.values()
        )
    )


def visit_module(module: Module) -> List[VulpesError]:
    """Visit each top level node in the module and verifies that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    return list(
        chain.from_iterable(
            visit_top_level_node(node, module) for node in module.top_level_nodes
        )
    )


def visit_top_level_node(node: TopLevelNode, module: Module) -> List[VulpesError]:
    """If the top level node is a function declaration, visit the function declaration.
    Otherwise, return an empty list.

    Args:
        node (TopLevelNode): The top level node to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    if isinstance(node, FnDecl):
        return visit_fn_decl(node, module)
    else:
        return []


def visit_fn_decl(fn_decl: FnDecl, module: Module) -> List[VulpesError]:
    """Visit all expressions in the function declaration and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        fn_decl (FnDecl): The function declaration to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    with module.symbol_table.scoped(fn_decl.id):
        return list(
            chain.from_iterable(visit_stmt(stmt, module) for stmt in fn_decl.body)
        )


def visit_stmt(stmt: Statement, module: Module) -> List[VulpesError]:
    """Visit a statement and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        stmt (Statement): The statement to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    if isinstance(stmt, VarDecl):
        return visit_expr(stmt.expr, module)
    elif isinstance(stmt, If):
        return visit_if(stmt, module)
    elif isinstance(stmt, While):
        return visit_while(stmt, module)
    elif isinstance(stmt, Loop):
        return visit_loop(stmt, module)
    elif isinstance(stmt, Assign):
        return visit_assign(stmt, module)
    elif isinstance(stmt, Return):
        return visit_return(stmt, module)
    elif isinstance(stmt, Expr):
        return visit_expr(stmt, module)
    else:
        return []


def visit_expr(expr: Expr, module: Module) -> List[VulpesError]:
    """Visit an expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        expr (Expr): The expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    if isinstance(expr, Ident):
        return visit_ident(expr, module)
    elif isinstance(expr, Call):
        return visit_call(expr, module)
    elif isinstance(expr, GetIndex):
        return visit_get_index(expr, module)
    elif isinstance(expr, AccessField):
        return visit_access_field(expr, module)
    elif isinstance(expr, BinaryOp):
        return visit_binary_op(expr, module)
    elif isinstance(expr, UnaryOp):
        return visit_unary_op(expr, module)
    elif isinstance(expr, StructExpr):
        return visit_struct_expr(expr, module)
    elif isinstance(expr, ArrayExpr):
        return visit_array_expr(expr, module)
    else:
        return []


def visit_if(if_stmt: If, module: Module) -> List[VulpesError]:
    """Visit an if statement and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        if_stmt (If): The if statement to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the condition
    errors = visit_expr(if_stmt.cond, module)
    # visit the then block
    with module.symbol_table.scoped(if_stmt.id):
        errors.extend(
            list(chain.from_iterable(visit_stmt(stmt, module) for stmt in if_stmt.body))
        )
    # if there is an else block, visit the else block
    if if_stmt.else_body is not None:
        errors.extend(visit_else(if_stmt.else_body, module))
    return errors


def visit_else(else_stmt: Else, module: Module) -> List[VulpesError]:
    """Visit an else statement and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        else_stmt (Else): The else statement to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # if the else body is an if statement, visit the if statement
    if len(else_stmt.body) > 0 and isinstance(else_stmt.body[0], If):
        return visit_if(else_stmt.body[0], module)

    with module.symbol_table.scoped(else_stmt.id):
        return list(
            chain.from_iterable(visit_stmt(stmt, module) for stmt in else_stmt.body)
        )


def visit_while(while_stmt: While, module: Module) -> List[VulpesError]:
    """Visit a while statement and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        while_stmt (While): The while statement to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the condition
    errors = visit_expr(while_stmt.cond, module)
    # visit the body
    with module.symbol_table.scoped(while_stmt.id):
        return errors + list(
            chain.from_iterable(visit_stmt(stmt, module) for stmt in while_stmt.body)
        )


def visit_loop(loop: Loop, module: Module) -> List[VulpesError]:
    """Visit a loop statement and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        loop (Loop): The loop statement to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the body
    with module.symbol_table.scoped(loop.id):
        return list(chain.from_iterable(visit_stmt(stmt, module) for stmt in loop.body))


def visit_assign(assign: Assign, module: Module) -> List[VulpesError]:
    """Visit an assign statement and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        assign (Assign): The assign statement to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the lhs, we just need to verify it exists, dont care about anything else
    lhs_errs = visit_expr(assign.lhs, module)
    # visit the rhs
    rhs_errs = visit_expr(assign.rhs, module)
    return lhs_errs + rhs_errs


def visit_return(return_stmt: Return, module: Module) -> List[VulpesError]:
    """Visit a return statement and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        return_stmt (Return): The return statement to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    if return_stmt.expr is not None:
        return visit_expr(return_stmt.expr, module)
    return []


def visit_ident(ident: Ident, module: Module) -> List[VulpesError]:
    """Visit an identifier and verify that it is defined.

    Args:
        ident (Ident): The identifier to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # retrieve the symbol from the module, if it does not exist, return an error
    symbol = lookup_symbol(ident.name, module)
    if symbol is None:
        return [UndefinedSymbolError(ident.name, module.name)]
    # attach the symbol to the identifier
    ident.symbol = symbol
    return []


def lookup_symbol(name: str, module: Module) -> Optional[Symbol]:
    """Lookup a symbol in the symbol table.

    Args:
        name (str): The name of the symbol to lookup.
        module (Module): The module to lookup the symbol in.

    Returns:
        Optional[Symbol]: The symbol if it exists, otherwise None.
    """
    # try looking up the symbol in the symbol table
    symbol = module.symbol_table.lookup(name)
    if symbol is None:
        # try looking up the symbol in the module imports
        return module.imports.get(name)
    return symbol


def visit_call(call: Call, module: Module) -> List[VulpesError]:
    """Visit a call expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        call (Call): The call expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    callee_errs = visit_expr(call.callee, module)
    arg_errs = list(chain.from_iterable(visit_expr(arg, module) for arg in call.args))
    return callee_errs + arg_errs


def visit_get_index(get_index: GetIndex, module: Module) -> List[VulpesError]:
    """Visit a get index expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        get_index (GetIndex): The get index expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the object
    obj_errs = visit_expr(get_index.obj, module)
    # visit the index
    index_errs = visit_expr(get_index.index, module)
    return obj_errs + index_errs


def visit_access_field(access_field: AccessField, module: Module) -> List[VulpesError]:
    """Visit an access field expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        access_field (AccessField): The access field expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the object
    return visit_expr(access_field.obj, module)


def visit_binary_op(binary_op: BinaryOp, module: Module) -> List[VulpesError]:
    """Visit a binary operation expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        binary_op (BinaryOp): The binary operation expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the lhs
    lhs_errs = visit_expr(binary_op.lhs, module)
    # visit the rhs
    rhs_errs = visit_expr(binary_op.rhs, module)
    return lhs_errs + rhs_errs


def visit_unary_op(unary_op: UnaryOp, module: Module) -> List[VulpesError]:
    """Visit a unary operation expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        unary_op (UnaryOp): The unary operation expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    return visit_expr(unary_op.operand, module)


def visit_struct_expr(struct_expr: StructExpr, module: Module) -> List[VulpesError]:
    """Visit a struct expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        struct_expr (StructExpr): The struct expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # visit the fields
    return list(
        chain.from_iterable(
            visit_expr(field.expr, module) for field in struct_expr.fields
        )
    )


def visit_array_expr(array_expr: ArrayExpr, module: Module) -> List[VulpesError]:
    """Visit an array expression and verify that all symbols are defined.
    Attach the symbol to the reference node.

    Args:
        array_expr (ArrayExpr): The array expression to visit.
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    return list(
        chain.from_iterable(visit_expr(elem, module) for elem in array_expr.elems)
    )
