from itertools import chain
from typing import List

from prototype.errors import VulpesError
from prototype.prototype.ast.ast import FnDecl
from .pass_types import PassResult
from prototype.result import Result
from prototype.types import Type, TypeHole
from .type_collection import UndefinedType
from prototype.ast import ModuleManager, Module


def type_norm_pass(
    module_manager: ModuleManager, prev_result: List[VulpesError] = []
) -> PassResult:
    """This pass walks the AST and normalizes all type annotations into their internal representations.
    It attaches these types to the symbol of the declaration.
    If a declaration has no type annotation, it attaches a TypeHole to the symbol.

    Args:
        module_manager (ModuleManager): The module manager to normalize types for.
        prev_result (List[VulpesError], optional): The previous result of the pass. Defaults to [].

    Returns:
        PassResult: The result of the pass.
    """
    return module_manager, prev_result + list(
        chain.from_iterable(
            visit_module(module, module_manager)
            for module in module_manager.modules.values()
        )
    )


def visit_module(module: Module, module_manager: ModuleManager) -> List[VulpesError]:
    """This function visits a module and normalizes all type annotations into their internal representations.
    It attaches these types to the symbol of the declaration.
    If a declaration has no type annotation, it attaches a TypeHole to the symbol.

    Args:
        module (Module): The module to visit.
        module_manager (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    return list(chain.from_iterable(visit_fn_decl(top_level_node, module, module_manager) for top_level_node in module.top_level_nodes if isinstance(top_level_node, FnDecl)))


def visit_fn_decl(fn_decl: FnDecl, module: Module, module_manager: ModuleManager) -> List[VulpesError]:
    """This function visits a function declaration and normalizes all type annotations into their internal representations.
    It attaches these types to the symbol of the declaration.
    If a declaration has no type annotation, it attaches a TypeHole to the symbol.

    Args:
        fn_decl (FnDecl): The function declaration to visit.
        module (Module): The module that the function declaration is in.
        module_manager (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    # TODO: Implement this
    raise NotImplementedError("Not implemented")
    
