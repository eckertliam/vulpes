from dataclasses import dataclass

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from prototype.types import Type


@dataclass(slots=True)
class Symbol:
    name: str
    ast_id: int
    parent_scope_id: int
    type: Optional["Type"] = None


@dataclass(slots=True)
class Scope:
    """
    A scope is a collection of symbols.
    Scope IDs are derived from the ast id of the scope they represent.

    Attributes:
        scope_id (int): The id of the scope
        parent_id (Optional[int]): The id of the parent scope
        symbols (Dict[str, Symbol]): The symbols in the scope
    """

    scope_id: int
    parent_id: Optional[int]
    symbols: Dict[str, Symbol]


class SymbolTable:
    """
    Maps scope ids to scopes.
    The symbol table is used to store the symbols for a given scope.
    Scope IDs are derived from the ast ids of the scopes.

    Attributes:
        table (Dict[int, Scope]): The table of scopes
        current_scope_id (int): The id of the current scope
    """

    def __init__(self) -> None:
        self.table: Dict[int, Scope] = {}
        # We always have a global scope as -1 so it doesnt clash with any ast ids
        self.table[-1] = Scope(-1, None, {})
        # we point current scope to the global scope
        self.current_scope_id = -1

    def enter_scope(self, scope_id: int) -> None:
        """Enter a new scope.
        If the scope already exists, move the current scope to the new scope.
        Otherwise, create a new scope and move the current scope to it.

        Args:
            scope_id (int): The id of the scope to enter
        """
        if scope_id in self.table:
            self.current_scope_id = scope_id  # no need to create a new scope
        else:
            self.table[scope_id] = Scope(
                scope_id, self.current_scope_id, {}
            )  # otherwise we create a new scope with the current scope as parent
            self.current_scope_id = scope_id

    def exit_scope(self) -> None:
        """Exit the current scope and move to the parent scope.
        If the current scope is the global scope, raise an error.
        """
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
    ) -> Symbol:
        """Add a symbol to the current scope.
        If the symbol already exists in the current scope or the top level scope, return None.
        Otherwise, add the symbol to the current scope and return the symbol.

        Args:
            name (str): The name of the symbol
            ast_id (int): The ast id of the symbol

        Returns:
            Symbol: The symbol if it was added, otherwise raises a RuntimeError
        """
        if name in self.table[self.current_scope_id].symbols or name in self.table[-1].symbols:
            raise RuntimeError("Name already in use")
        else:
            symbol = Symbol(name, ast_id, self.current_scope_id)
            self.table[self.current_scope_id].symbols[name] = symbol
            return symbol

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Lookup a symbol in the current scope.

        Args:
            name (str): The name of the symbol

        Returns:
            Optional[Symbol]: The symbol if it exists, otherwise None
        """
        if name in self.table[self.current_scope_id].symbols:
            return self.table[self.current_scope_id].symbols[name]
        else:
            return None

    def lookup(self, name: str) -> Optional[Symbol]:
        """Lookup a symbol in all scopes beginning with current and going up to global.

        Args:
            name (str): The name of the symbol

        Returns:
            Optional[Symbol]: The symbol if it exists, otherwise None
        """
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
        """Lookup a symbol in the global scope.

        Args:
            name (str): The name of the symbol

        Returns:
            Optional[Symbol]: The symbol if it exists, otherwise None
        """
        if name in self.table[-1].symbols:
            return self.table[-1].symbols[name]
        else:
            return None

    def __contains__(self, name: str) -> bool:
        """Check if a symbol exists in the symbol table.

        Args:
            name (str): The name of the symbol
        """
        return self.lookup(name) is not None