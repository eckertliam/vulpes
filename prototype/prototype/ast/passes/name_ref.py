from itertools import chain
from typing import List, Tuple
from prototype.errors import VulpesError
from prototype.ast import Module, ModuleManager


class UndefinedSymbolError(VulpesError):
    def __init__(self, name: str, module: str):
        super().__init__(f"Undefined symbol: {name} in module: {module}")


def name_ref_pass(
    module_manager: ModuleManager,
) -> Tuple[ModuleManager, List[VulpesError]]:
    """The name reference pass walks the AST and verifies that all names are valid references to symbols.

    Args:
        module_manager (ModuleManager): The module manager to run the pass on.

    Returns:
        Tuple[ModuleManager, List[VulpesError]]: The module manager with the pass run and a list of errors.
    """
    return module_manager, list(
        chain.from_iterable(
            visit_module(module) for module in module_manager.modules.values()
        )
    )

def visit_module(module: Module) -> List[VulpesError]:
    """Visit each top level node in the module and verifies that all symbols are defined.

    Args:
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: A list of errors.
    """
    # TODO: Implement the visit_module function
    return []
