from functools import lru_cache
from itertools import chain
from typing import List, Set, Tuple
from prototype.errors import VulpesError
from prototype.ast import ModuleManager, Import, Module, ExportSpec, TopLevelNode


class ModuleDoesNotExist(VulpesError):
    """Error raised when a module cannot be found

    Attributes:
        module_name (str): The name of the module that was not found
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"Module {module_name} not found")


class ImportFromSelfError(VulpesError):
    """Error raised when a module imports from itself

    Attributes:
        module_name (str): The name of the module that is importing from itself
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"Module {module_name} cannot import from itself")


class ImportTargetNotFoundError(VulpesError):
    """Error raised when an import target is not found

    Attributes:
        importing_module (str): The name of the module that is importing
        imported_module (str): The name of the module that is being imported from
        target (str): The name of the target that was not found
    """

    def __init__(self, importing_module: str, imported_module: str, target: str):
        self.importing_module = importing_module
        self.imported_module = imported_module
        self.target = target
        super().__init__(
            f"Import target {target} not found in module {imported_module} when importing from {importing_module}"
        )


def module_res_pass(
    module_manager: ModuleManager,
) -> Tuple[ModuleManager, List[VulpesError]]:
    """Module Resolution Pass

    This pass ensures that all imports are valid and present.

    Args:
        module_manager (ModuleManager): The module manager to pass through

    Returns:
        ModuleManager: The module manager with all imports resolved
        List[VulpesError]: A list of errors
    """
    resolved_modules: List[List[VulpesError]] = [
        resolve_module(mod, module_manager) for mod in module_manager.modules.values()
    ]
    errors: List[VulpesError] = list(chain.from_iterable(resolved_modules))
    return module_manager, errors


def resolve_module(module: Module, module_manager: ModuleManager) -> List[VulpesError]:
    resolved_top_level_nodes: List[List[VulpesError]] = [
        resolve_top_level_node(node, module, module_manager)
        for node in module.top_level_nodes
    ]
    return list(chain.from_iterable(resolved_top_level_nodes))


def resolve_top_level_node(
    node: TopLevelNode, module: Module, module_manager: ModuleManager
) -> List[VulpesError]:
    if isinstance(node, Import):
        # guard against importing from self
        if node.module == module.name:
            return [ImportFromSelfError(module.name)]
        # check if the module exists
        elif node.module not in module_manager.modules:
            return [ModuleDoesNotExist(node.module)]
        elif len(node.targets) > 0:
            return resolve_import_targets(
                node.targets, module_manager.modules[node.module], module
            )

    return []


@lru_cache(maxsize=None)
def get_export_spec(module: Module) -> Set[str]:
    return next(
        (
            node.exports
            for node in module.top_level_nodes
            if isinstance(node, ExportSpec)
        ),
        set(),
    )


def resolve_import_targets(
    import_targets: Set[str], imported_module: Module, importing_module: Module
) -> List[VulpesError]:
    exports: Set[str] = get_export_spec(imported_module)
    return [
        ImportTargetNotFoundError(importing_module.name, imported_module.name, target)
        for target in import_targets
        if target not in exports
    ]
