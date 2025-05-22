from typing import List, Tuple
from prototype.ast import ModuleManager
from prototype.errors import VulpesError

class DuplicateDefinitionError(VulpesError):
    """Error raised when a name is already in the top level scope"""

    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module
        super().__init__(f"Name {name} in {module} is already in use")
        
    def __str__(self) -> str:
        return f"Name {self.name} in {self.module} is already in use"

def name_res_pass(module_manager: ModuleManager) -> Tuple[ModuleManager, List[VulpesError]]:
    """Name Resolution Pass

    This pass walks the AST and builds the symbol table for each module.

    Args:
        module_manager (ModuleManager): The module manager to walk

    Returns:
        ModuleManager: The module manager with the symbol table populated
    """
    raise NotImplementedError("Not implemented")