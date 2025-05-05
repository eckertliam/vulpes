# Scope is a helper type that contains the id of the scope, the parent scope id, and the symbols in the scope
from dataclasses import dataclass
from typing import Dict, Optional, Union

from ..ast import Program
from ..errors import CussError, NameResolutionError
from ..symbol import Symbol

# TODO: add docstrings to all methods


@dataclass(slots=True)
class Scope:
    """
    A scope is a collection of symbols.
    Scope IDs are derived from the ast id of the scope they represent.
    """

    id: int
    parent_id: Optional[int]
    symbols: Dict[str, Symbol]


class SymbolTable:
    """
    Maps scope ids to scopes.
    The symbol table is used to store the symbols for a given scope.
    Scope IDs are derived from the ast ids of the scopes.
    """

    __slots__ = ["table", "current_scope_id"]

    def __init__(self) -> None:
        self.table: Dict[int, Scope] = {}
        # We always have a global scope as -1 so it doesnt clash with any ast ids
        self.table[-1] = Scope(-1, None, {})
        # we point current scope to the global scope
        self.current_scope_id = -1

    def enter_scope(self, id: int) -> None:
        # first we check if the scope already exists
        if id in self.table:
            self.current_scope_id = id  # no need to create a new scope
        else:
            self.table[id] = Scope(
                id, self.current_scope_id, {}
            )  # otherwise we create a new scope with the current scope as parent
            self.current_scope_id = id

    def exit_scope(self) -> None:
        parent_id = self.table[
            self.current_scope_id
        ].parent_id  # get the parent scope id
        if (
            parent_id is None
        ):  # if the parent scope id is None, we are already in the global scope
            raise RuntimeError("Cannot exit global scope in symbol table")
        self.current_scope_id = parent_id  # otherwise we exit the current scope and move to the parent scope

    def add_symbol(
        self,
        name: str,
        ast_id: int,
        line: int,
        program: Program,
    ) -> Union[Symbol, CussError]:
        # check for shadowing
        if name in self.table[self.current_scope_id].symbols:
            # get the existing symbol
            existing_symbol = self.table[self.current_scope_id].symbols[name]
            # get the node of the existing symbol
            existing_node = program.get_node(existing_symbol.ast_id)
            if existing_node is None:
                raise RuntimeError("Cannot find node for existing symbol")
            # get the line of the existing symbol
            existing_line = existing_node.line
            # add an error
            return NameResolutionError(
                f"Cannot redeclare {name} in the same scope, {name} is already defined at line {existing_line}",
                line,
                ast_id,
            )
        else:
            symbol = Symbol(name, ast_id, self.current_scope_id)
            self.table[self.current_scope_id].symbols[name] = symbol
            return symbol

    def lookup_local(self, name: str) -> Optional[Symbol]:
        # lookup in only the current scope
        if name in self.table[self.current_scope_id].symbols:
            return self.table[self.current_scope_id].symbols[name]
        else:
            return None

    def lookup(self, name: str) -> Optional[Symbol]:
        # lookup in all scopes beginning with current and going up to global
        current_scope_id: Optional[int] = self.current_scope_id
        while (
            current_scope_id is not None
        ):  # we iterate through and know we've finished global when the current scope is None
            if name in self.table[current_scope_id].symbols:
                return self.table[current_scope_id].symbols[name]
            current_scope_id = self.table[
                current_scope_id
            ].parent_id  # move to the parent scope
        return None

    def lookup_global(self, name: str) -> Optional[Symbol]:
        # lookup in only the global scope
        if name in self.table[-1].symbols:
            return self.table[-1].symbols[name]
        else:
            return None
