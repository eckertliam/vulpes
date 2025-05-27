from itertools import chain
from typing import List
from prototype.ast import ModuleManager, Declaration, ExportSpec, Module
from prototype.errors import VulpesError
from .pass_types import PassResult


class UndefinedExportError(VulpesError):
    """An error that occurs when an export is not found in the module's symbol table

    Attributes:
        export_name (str): The name of the export that is undefined
        module_name (str): The name of the module that the export is undefined in
    """

    def __init__(self, export_name: str, module_name: str):
        self.export_name = export_name
        self.module_name = module_name
        super().__init__(f"Undefined export: {export_name} in module: {module_name}")


class DuplicateExportError(VulpesError):
    """An error that occurs when a duplicate export is found in the module's export spec

    Attributes:
        export_name (str): The name of the export that is duplicated
        module_name (str): The name of the module that the export is duplicated in
    """

    def __init__(self, export_name: str, module_name: str):
        self.export_name = export_name
        self.module_name = module_name
        super().__init__(f"Duplicate export: {export_name} in module: {module_name}")


class MultipleExportSpecsError(VulpesError):
    """An error that occurs when a module has multiple export specs"""

    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"Multiple export specs in module: {module_name}")


class InvalidExportTargetError(VulpesError):
    """An error that occurs when an export target is not valid"""

    def __init__(self, name: str, module_name: str):
        self.name = name
        self.module_name = module_name
        super().__init__(f"Invalid export target: {name} in module: {module_name}")


def export_collection_pass(
    module_manager: ModuleManager,
    prev_result: List[VulpesError] = [],
) -> PassResult:
    """This pass populates each module's exports table based on its ExportSpec
    It performs the following steps:
    - Reads each module's ExportSpec
    - Validates that all specified names are defined in the module's symbol table
    - Adds each named symbol to the module's exports table

    Args:
        module_manager (ModuleManager): The module manager to walk
        prev_result (List[VulpesError]): A list of errors from previous passes

    Returns:
        Tuple[ModuleManager, List[VulpesError]]: The module manager with the exports table populated
    """
    return module_manager, prev_result + list(
        chain.from_iterable(
            visit_module(module) for module in module_manager.modules.values()
        )
    )


def visit_module(module: Module) -> List[VulpesError]:
    """Visit a module and collect its exports

    Args:
        module (Module): The module to visit

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    export_specs = [
        node for node in module.top_level_nodes if isinstance(node, ExportSpec)
    ]
    # if there is more than one export spec, return an error
    if len(export_specs) > 1:
        return [MultipleExportSpecsError(module.name)]
    # if there is no export spec, return an empty list
    if len(export_specs) == 0:
        return []
    # if there is one export spec, visit it
    return visit_export_spec(export_specs[0], module)


def visit_export_spec(export_spec: ExportSpec, module: Module) -> List[VulpesError]:
    """Visit an export spec and collect its exports
    Validates that all exports exist, are exportable, and are not duplicated

    Args:
        export_spec (ExportSpec): The export spec to visit
        module (Module): The module that the export spec belongs to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    return list(
        chain.from_iterable(
            visit_export_target(name, module) for name in export_spec.exports
        )
    )


def visit_export_target(name: str, module: Module) -> List[VulpesError]:
    """Visit an export target and add it to the module's exports table
    Validates that the symbol is defined, exportable, and not duplicated

    Args:
        name (str): The name of the export target
        module (Module): The module that the export target belongs to

    Returns:
        List[VulpesError]: A list of errors that occurred during the visit
    """
    if name in module.exports:  # check for duplicates
        return [DuplicateExportError(name, module.name)]

    symbol = module.symbol_table.lookup_global(name)
    if symbol is None:  # check if the symbol is defined
        return [UndefinedExportError(name, module.name)]

    if not is_exportable(symbol.ast_id, module):  # check if the symbol is exportable
        return [InvalidExportTargetError(name, module.name)]

    module.exports[name] = symbol  # add the symbol to the module's exports table
    return []


def is_exportable(ast_id: int, module: Module) -> bool:
    """Check if a symbol is exportable
    Retrieve the node using the symbol's ast_id
    If the node is a Declaration, it is exportable

    Args:
        ast_id (int): The ast_id of the symbol to check
        module (Module): The module that the symbol belongs to

    Returns:
        bool: True if the symbol is exportable, False otherwise
    """
    node = module.get_node(ast_id)
    return isinstance(node, Declaration)
