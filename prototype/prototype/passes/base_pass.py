# Pass base class
from abc import ABC, abstractmethod
from typing import Optional, List

from ..types import TypeEnv

from ..errors import CussError

from ..ast import Program
from .symbol_table import SymbolTable


class Pass(ABC):
    __slots__ = ["program", "symbol_table", "errors", "type_env"]

    def __init__(
        self, program: Optional[Program] = None, previous_pass: Optional["Pass"] = None
    ):
        if program:
            self.program = program
            self.symbol_table = SymbolTable()
            self.errors: List[CussError] = []
            self.type_env = TypeEnv()
        elif previous_pass:
            self.program = previous_pass.program
            self.symbol_table = previous_pass.symbol_table
            # reset symbol table to global scope
            self.symbol_table.current_scope_id = -1
            self.errors = previous_pass.errors
            self.type_env = previous_pass.type_env
        else:
            raise ValueError("Either program or previous_pass must be provided")

    @abstractmethod
    def run(self) -> None:
        pass
