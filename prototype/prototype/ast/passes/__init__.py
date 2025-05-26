
from typing import Callable, List, Tuple

from prototype.ast import ModuleManager
from prototype.errors import VulpesError

from .module_res import module_res_pass
from .name_res import name_res_pass
from .export_collection import export_collection_pass
from .import_linker import import_linker_pass
from .name_ref import name_ref_pass
from .pipeline import Pipeline


PassResult = Tuple[ModuleManager, List[VulpesError]]
Pass = Callable[[ModuleManager], PassResult]