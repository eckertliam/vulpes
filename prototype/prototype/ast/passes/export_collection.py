from typing import List, Tuple
from prototype.ast import ModuleManager
from prototype.errors import VulpesError


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


def export_collection_pass(
    module_manager: ModuleManager,
) -> Tuple[ModuleManager, List[VulpesError]]:
    """This pass populates each module's exports table based on its ExportSpec
    It performs the following steps:
    - Reads each module's ExportSpec
    - Validates that all specified names are defined in the module's symbol table
    - Adds each named symbol to the module's exports table

    Args:
        module_manager (ModuleManager): The module manager to walk

    Returns:
        Tuple[ModuleManager, List[VulpesError]]: The module manager with the exports table populated
    """
    raise NotImplementedError("Export collection pass not implemented")
