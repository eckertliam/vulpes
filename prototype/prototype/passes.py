# Passes are used to transform and validate the AST
# This is the base class for all passes
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Union

from .errors import CussError, NameResolutionError, TypeInferenceError
from .parser import (
    ArrayTypeAnnotation,
    Declaration,
    EnumDecl,
    FnDecl,
    FunctionTypeAnnotation,
    If,
    ImplDecl,
    Loop,
    NamedTypeAnnotation,
    Program,
    Statement,
    StructDecl,
    TupleTypeAnnotation,
    TypeAliasDecl,
    TypeAnnotation,
    VarDecl,
    While,
    Tuple,
)
from .types import (
    ArrayType,
    EnumType,
    FunctionType,
    StructType,
    TupleType,
    Type,
    TypeVar,
)


# Pass base class
class Pass(ABC):
    @abstractmethod
    def run(self, program: Program) -> Program:
        pass


# Pass 1: Name Declaration Pass
# This pass enters all variable declarations into their respective scopes in a symbol table


# Symbol is a helper type that contains the name of a variable, its ast id, and its parent scope id
@dataclass
class Symbol:
    name: str
    ast_id: int
    parent_scope_id: int
    type: Optional[Type] = None


# Scope is a helper type that contains the id of the scope, the parent scope id, and the symbols in the scope
@dataclass
class Scope:
    id: int
    parent_id: Optional[int]
    symbols: Dict[str, Symbol]


# The symbol table is a dictionary that maps scope ids to scopes
class SymbolTable:
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
        self, name: str, ast_id: int, line: int, type: Optional[Type] = None
    ) -> Optional[CussError]:
        # check for shadowing
        if name in self.table[self.current_scope_id].symbols:
            return NameResolutionError(
                f"Shadowing variable {name} in scope {self.current_scope_id}",
                line,
                ast_id,
            )
        else:
            self.table[self.current_scope_id].symbols[name] = Symbol(
                name, ast_id, self.current_scope_id, type
            )
            return None

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


class NameDeclarationPass(Pass):
    def __init__(self):
        self.symbol_table = SymbolTable()

    def run(self, program: Program) -> Program:
        return program
