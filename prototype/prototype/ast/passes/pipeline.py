from functools import reduce
from typing import List
from prototype.ast import ModuleManager
from prototype.errors import VulpesError
from .pass_types import Pass, PassResult


def compose_passes(passes: List[Pass]) -> Pass:
    def compose(acc: Pass, p: Pass) -> Pass:
        def new_func(
            mm: ModuleManager, prev_result: List[VulpesError] = []
        ) -> PassResult:
            mm, errs = acc(mm, prev_result)
            return p(mm, errs)

        return new_func

    return reduce(compose, passes)


class Pipeline:
    def __init__(self, passes: List[Pass]):
        self._passes = passes
        self._composed_pass = compose_passes(passes)

    def __call__(
        self, mm: ModuleManager, prev_result: List[VulpesError] = []
    ) -> PassResult:
        return self._composed_pass(mm, prev_result)

    def insert_pass(self, index: int, p: Pass):
        self._passes.insert(index, p)
        self._composed_pass = compose_passes(self._passes)

    def remove_pass(self, index: int):
        self._passes.pop(index)
        self._composed_pass = compose_passes(self._passes)

    def append_pass(self, p: Pass):
        self._passes.append(p)
        self._composed_pass = compose_passes(self._passes)
