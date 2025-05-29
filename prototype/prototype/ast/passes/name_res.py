from itertools import chain
from typing import List, Optional, Tuple, Union
from prototype.errors import VulpesError
from prototype.ast import (
    Else,
    FnDecl,
    If,
    Loop,
    Param,
    Statement,
    TypeAliasDecl,
    UnionDecl,
    VarDecl,
    While,
    ModuleManager,
    Module,
    TopLevelNode,
    StructDecl,
)
from .pass_types import PassResult


class DuplicateDefinitionError(VulpesError):
    """Error raised when a name is already in the top level scope"""

    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module
        super().__init__(f"{name} is already defined in {module}")

    def __str__(self) -> str:
        return f"{self.name} is already defined in {self.module}"


def name_res_pass(
    module_manager: ModuleManager,
    prev_result: List[VulpesError] = [],
) -> PassResult:
    """Name Resolution Pass

    This pass walks the AST and builds the symbol table for each module.

    Args:
        module_manager (ModuleManager): The module manager to walk
        prev_result (List[VulpesError]): A list of errors from previous passes

    Returns:
        ModuleManager: The module manager with the symbol table populated
    """
    return module_manager, prev_result + list(
        chain.from_iterable(
            visit_module(module) for module in module_manager.modules.values()
        )
    )


def visit_module(module: Module) -> List[VulpesError]:
    """Visit a module and add its symbols to the symbol table

    Args:
        module (Module): The module to visit
    """
    return list(
        chain.from_iterable(
            visit_top_level_node(node, module) for node in module.top_level_nodes
        )
    )


def add_global_symbol(
    node: Union[StructDecl, UnionDecl, TypeAliasDecl], module: Module
) -> List[VulpesError]:
    """Add a global symbol to the symbol table and set the node's symbol attribute

    Args:
        node (Union[StructDecl, UnionDecl, TypeAliasDecl]): The node to add the symbol to
        module (Module): The module to add the symbol to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    if module.symbol_table.lookup_global(node.name) is not None:
        return [DuplicateDefinitionError(node.name, module.name)]
    symbol = module.symbol_table.add_symbol(node.name, node.id, module.id)
    node.symbol = symbol
    return []


def add_local_symbol(node: Union[Param, VarDecl], module: Module) -> List[VulpesError]:
    """Add a local symbol to the symbol table and set the node's symbol attribute

    Args:
        node (Union[Param, VarDecl]): The node to add the symbol to
        module (Module): The module to add the symbol to

    Returns:
        List[VulpesError]: A duplicate definition error if the symbol already exists, otherwise an empty list
    """
    if module.symbol_table.lookup_local(node.name) is not None:
        return [DuplicateDefinitionError(node.name, module.name)]
    symbol = module.symbol_table.add_symbol(node.name, node.id, module.id)
    node.symbol = symbol
    return []


def visit_top_level_node(node: TopLevelNode, module: Module) -> List[VulpesError]:
    """Visit a top level node and add its symbols to the symbol table

    Args:
        node (TopLevelNode): The top level node to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    if (
        isinstance(node, StructDecl)
        or isinstance(node, UnionDecl)
        or isinstance(node, TypeAliasDecl)
    ):
        return add_global_symbol(node, module)

    if isinstance(node, FnDecl):
        return visit_fn_decl(node, module)

    # imports and exports arent touched during name resolution
    return []


def visit_fn_decl(fn_decl: FnDecl, module: Module) -> List[VulpesError]:
    """Visit a function declaration and add its symbols to the symbol table

    Args:
        fn_decl (FnDecl): The function declaration to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    # check if the function is already in the symbol table
    if module.symbol_table.lookup_global(fn_decl.name) is not None:
        return [DuplicateDefinitionError(fn_decl.name, module.name)]
    # if its not add it
    fn_symbol = module.symbol_table.add_symbol(fn_decl.name, fn_decl.id, module.id)
    # attach the function's symbol to the declaration
    fn_decl.symbol = fn_symbol
    # enter the function scope
    with module.symbol_table.scoped(fn_symbol.ast_id):
        # add the parameters to the symbol table
        param_res: List[VulpesError] = list(
            chain.from_iterable(
                add_local_symbol(param, module) for param in fn_decl.params
            )
        )
        # visit the body of the function
        body_res: List[VulpesError] = visit_block(fn_decl.body, module)
    return param_res + body_res


def visit_block(block: List[Statement], module: Module) -> List[VulpesError]:
    """Visit a block of statements and add their symbols to the symbol table
    This function expects you have already entered the proper scope.

    Args:
        block (List[Statement]): The block of statements to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    return list(chain.from_iterable(visit_stmt(stmt, module) for stmt in block))


def visit_body(body: List[Statement], ast_id: int, module: Module) -> List[VulpesError]:
    """Visit a body of statements and add their symbols to the symbol table
    This function enters the scope of the body and then visits the body.
    It then exits the scope of the body.

    Args:
        body (List[Statement]): The body of statements to visit
        ast_id (int): The AST ID of the body

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    with module.symbol_table.scoped(ast_id):
        return visit_block(body, module)


def visit_stmt(stmt: Statement, module: Module) -> List[VulpesError]:
    """Visit a statement and add its symbols to the symbol table if it is a declaration

    Args:
        stmt (Statement): The statement to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    if isinstance(stmt, VarDecl):
        return visit_var_decl(stmt, module)
    if isinstance(stmt, If):
        return visit_if(stmt, module)
    if isinstance(stmt, While):
        return visit_while(stmt, module)
    if isinstance(stmt, Loop):
        return visit_loop(stmt, module)
    return []


def visit_loop(loop: Loop, module: Module) -> List[VulpesError]:
    """Visit a loop statement, enter its scope, and visit the body

    Args:
        loop (Loop): The loop statement to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    return visit_body(loop.body, loop.id, module)


def visit_while(while_stmt: While, module: Module) -> List[VulpesError]:
    """Visit a while statement, enter its scope, and visit the body

    Args:
        while_stmt (While): The while statement to visit
        module (Module): The module to add the symbols to
    """
    return visit_body(while_stmt.body, while_stmt.id, module)


def visit_var_decl(var_decl: VarDecl, module: Module) -> List[VulpesError]:
    """Visit a variable declaration and add its symbols to the symbol table

    Args:
        var_decl (VarDecl): The variable declaration to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    return add_local_symbol(var_decl, module)


def visit_if(if_stmt: If, module: Module) -> List[VulpesError]:
    """Visit an if statement, enter its scope, and visit the body

    Args:
        if_stmt (If): The if statement to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    body_res: List[VulpesError] = visit_body(if_stmt.body, if_stmt.id, module)
    # visit the else body if it exists
    if if_stmt.else_body is not None:
        else_res: List[VulpesError] = visit_else(if_stmt.else_body, module)
        return body_res + else_res
    return body_res


def visit_else(else_stmt: Else, module: Module) -> List[VulpesError]:
    """Visit an else statement, enter its scope, and visit the body

    Args:
        else_stmt (Else): The else statement to visit
        module (Module): The module to add the symbols to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    if len(else_stmt.body) > 0 and isinstance(else_stmt.body[0], If):
        # skip over the else body and just enter the if scope
        return visit_if(else_stmt.body[0], module)
    else:
        return visit_body(else_stmt.body, else_stmt.id, module)
