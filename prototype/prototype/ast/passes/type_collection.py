from itertools import chain
from typing import List
from prototype.errors import VulpesError
from prototype.ast import ModuleManager, Module
from .pass_types import PassResult

class UndefinedType(VulpesError):
    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module
        super().__init__(f"Undefined type: {name} in module: {module}")


def type_collection_pass(module_manager: ModuleManager, prev_result: List[VulpesError] = []) -> PassResult:
    """
    This pass collects all the types defined in a module and add them to the thier module's symbol table.
    It also attaches the type to the symbol of the definition. So types can cross through imports.

    Args:
        module_manager (ModuleManager): The module manager to collect types from.
        prev_result (List[VulpesError]): The previous result of the pass.

    Returns:
        PassResult: The result of the pass.
    """
    return module_manager, prev_result + list(
        chain.from_iterable(
            visit_module(module) for module in module_manager.modules.values()
        )
    )
    

def visit_module(module: Module) -> List[VulpesError]:
    """Visit a module and collect all the types defined in it.

    Args:
        module (Module): The module to visit.

    Returns:
        List[VulpesError]: The errors found in the module.
    """
    # TODO: Implement this
    raise NotImplementedError("Not implemented")