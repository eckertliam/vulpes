from itertools import chain
from typing import List, Tuple
from prototype.errors import VulpesError
from prototype.ast import ModuleManager, Module, Import
from prototype.ast.symbol import Symbol


class ModuleDoesNotExportError(VulpesError):
    def __init__(self, importing_module: str, exporting_module: str, export_name: str):
        self.importing_module = importing_module
        self.exporting_module = exporting_module
        self.export_name = export_name
        super().__init__(
            f"Module {importing_module} is trying to import {export_name} from {exporting_module}, but {exporting_module} does not export it"
        )

    def __str__(self):
        return f"Module {self.importing_module} is trying to import {self.export_name} from {self.exporting_module}, but {self.exporting_module} does not export it"


def import_linker_pass(
    module_manager: ModuleManager,
) -> Tuple[ModuleManager, List[VulpesError]]:
    """This pass populates the imports table for each module with the corresponding
    symbols from the exporting module.

    Args:
        module_manager (ModuleManager): The module manager to populate the imports table for

    Returns:
        Tuple[ModuleManager, List[VulpesError]]: The module manager with the imports table populated, and a list of errors
    """
    return module_manager, list(
        chain.from_iterable(
            visit_module(module, module_manager)
            for module in module_manager.modules.values()
        )
    )


def visit_module(module: Module, module_manager: ModuleManager) -> List[VulpesError]:
    """This function visits a module and populates the imports table for it.

    Args:
        module (Module): The module to visit
        module_manager (ModuleManager): The module manager to populate the imports table for

    Returns:
        Tuple[ModuleManager, List[VulpesError]]: The module manager with the imports table populated, and a list of errors
    """
    return list(
        chain.from_iterable(
            visit_import(node, module, module_manager)
            for node in module.top_level_nodes
            if isinstance(node, Import)
        )
    )


def visit_import(
    import_node: Import, importing_module: Module, module_manager: ModuleManager
) -> List[VulpesError]:
    """This function visits an import node
    checks that the exporting module exports the symbol
    then adds the symbol to the importing module's imports table.

    Args:
        import_node (Import): The import node to visit
        importing_module (Module): The module that the import node is in
        module_manager (ModuleManager): The module manager to populate the imports table for

    Returns:
        List[VulpesError]: A list of errors
    """
    exporting_module = module_manager.get_module(import_node.module)
    # this should never happen we check for this in the module res pass
    assert exporting_module is not None, f"Module {import_node.module} not found"
    # check if import targets is a subset of the exporting module's exports
    if import_node.targets.issubset(exporting_module.exports):
        importing_module.imports.update(
            {target: exporting_module.exports[target] for target in import_node.targets}
        )
        return []
    else:
        return [
            ModuleDoesNotExportError(
                importing_module.name, exporting_module.name, target
            )
            for target in import_node.targets
            if target not in exporting_module.exports
        ]
