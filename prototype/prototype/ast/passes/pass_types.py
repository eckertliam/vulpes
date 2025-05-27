from typing import Callable, List, Optional, Tuple

from prototype.ast import ModuleManager
from prototype.errors import VulpesError

PassResult = Tuple[ModuleManager, List[VulpesError]]
Pass = Callable[[ModuleManager, List[VulpesError]], PassResult]
