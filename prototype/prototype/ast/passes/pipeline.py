from dataclasses import dataclass
from typing import List, TYPE_CHECKING
from prototype.ast import ModuleManager

if TYPE_CHECKING:
    from ..passes import Pass, PassResult



@dataclass
class Pipeline:
    passes: List["Pass"]
    
    def __call__(self, mm: ModuleManager) -> "PassResult":
        errs = []
        for p in self.passes:
            mm, n_errs = p(mm)
            errs.extend(n_errs)
        return mm, errs