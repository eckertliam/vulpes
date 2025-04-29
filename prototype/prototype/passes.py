# Passes are used to transform and validate the AST
# This is the base class for all passes
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from .errors import CussError, NameResolutionError, TypeInferenceError
from .parser import (
    ArrayTypeAnnotation,
    Declaration,
    Else,
    EnumDecl,
    FnDecl,
    FunctionTypeAnnotation,
    If,
    ImplDecl,
    Loop,
    NamedTypeAnnotation,
    Param,
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
    def __init__(self, program: Optional[Program] = None, previous_pass: Optional["Pass"] = None):
        if program:
            self.program = program
            self.symbol_table = SymbolTable()
            self.errors: List[CussError] = []
        elif previous_pass:
            self.program = previous_pass.program
            self.symbol_table = previous_pass.symbol_table
            self.errors = previous_pass.errors
        else:
            raise ValueError("Either program or previous_pass must be provided")
        
        
    @abstractmethod
    def run(self) -> None:
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
        self,
        name: str,
        ast_id: int,
        line: int,
        program: Program,
        type: Optional[Type] = None,
    ) -> Optional[CussError]:
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
    def __init__(self, program: Program) -> None:
        super().__init__(program=program)

    def add_symbol(self, name: str, ast_id: int, line: int) -> None:
        res = self.symbol_table.add_symbol(name, ast_id, line, self.program)
        if res is not None:
            self.errors.append(res)

    def run(self) -> None:
        # first we add all defined data structs to the symbol table
        # we do this so that we can then add their impls to their scopes
        for declaration in self.program.declarations:
            if isinstance(declaration, StructDecl):
                self.add_symbol(declaration.name, declaration.id, declaration.line)
            elif isinstance(declaration, EnumDecl):
                self.add_symbol(declaration.name, declaration.id, declaration.line)
            elif isinstance(declaration, TypeAliasDecl):
                self.add_symbol(declaration.name, declaration.id, declaration.line)

        # now we add all impls and fns to the symbol table
        for declaration in self.program.declarations:
            if isinstance(declaration, ImplDecl):
                self.impl_decl(declaration)
            elif isinstance(declaration, FnDecl):
                self.fn_decl(declaration)

    def impl_decl(self, impl: ImplDecl) -> None:
        # we look up the impl's type in the symbol table
        # and enter its scope
        impl_type: Optional[Symbol] = self.symbol_table.lookup(impl.name)
        # if the impl's type is not found we add an error and exit
        if impl_type is None:
            self.errors.append(
                NameResolutionError(
                    f"Cannot impl on undefined type {impl.name}", impl.line, impl.id
                )
            )
            return
        # we enter the impl's scope
        self.symbol_table.enter_scope(impl_type.ast_id)
        # we add all the methods to the impl's scope
        for method in impl.methods:
            self.method_decl(method, impl_type)
        # we exit the impl's scope
        self.symbol_table.exit_scope()

    def method_decl(self, method: FnDecl, impl_type: Symbol) -> None:
        # we add the method to the current scope
        self.add_symbol(method.name, method.id, method.line)
        # we enter the method's scope
        self.symbol_table.enter_scope(method.id)
        # we add the self param
        self_type_annotation = NamedTypeAnnotation(impl_type.name, method.line)
        param = Param("self", self_type_annotation, method.line)
        method.params.insert(0, param)
        # we add all the params to the method's scope
        for param in method.params:
            self.add_symbol(param.name, param.id, param.line)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in method.body:
            self.statement(statement)
        # we exit the method's scope
        self.symbol_table.exit_scope()

    def fn_decl(self, fn: FnDecl) -> None:
        # we add the fn to the current scope
        self.add_symbol(fn.name, fn.id, fn.line)
        # we enter the fn's scope
        self.symbol_table.enter_scope(fn.id)
        # we add all the params to the fn's scope
        for param in fn.params:
            self.add_symbol(param.name, param.id, param.line)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in fn.body:
            self.statement(statement)
        # we exit the fn's scope
        self.symbol_table.exit_scope()

    def statement(self, statement: Statement) -> None:
        # we only really care about vars and statements with bodies
        if isinstance(statement, VarDecl):
            self.add_symbol(statement.name, statement.id, statement.line)
        elif isinstance(statement, FnDecl):
            self.fn_decl(statement)
        elif isinstance(statement, If):
            self.if_stmt(statement)
        elif isinstance(statement, While):
            self.while_stmt(statement)
        elif isinstance(statement, Loop):
            self.loop_stmt(statement)

    def if_stmt(self, if_stmt: If) -> None:
        # we enter the if's scope
        self.symbol_table.enter_scope(if_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in if_stmt.body:
            self.statement(statement)
        # we exit the if's scope
        self.symbol_table.exit_scope()
        # if there is an else body we iterate through it
        if if_stmt.else_body is not None:
            self.else_stmt(if_stmt.else_body)

    def else_stmt(self, else_stmt: Else) -> None:
        # we enter the else's scope
        self.symbol_table.enter_scope(else_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in else_stmt.body:
            self.statement(statement)
        # we exit the else's scope
        self.symbol_table.exit_scope()

    def while_stmt(self, while_stmt: While) -> None:
        # we enter the while's scope
        self.symbol_table.enter_scope(while_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in while_stmt.body:
            self.statement(statement)
        # we exit the while's scope
        self.symbol_table.exit_scope()

    def loop_stmt(self, loop_stmt: Loop) -> None:
        # we enter the loop's scope
        self.symbol_table.enter_scope(loop_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in loop_stmt.body:
            self.statement(statement)
        # we exit the loop's scope
        self.symbol_table.exit_scope()

# TODO: implement NameReferencePass
# This pass checks that all variable references, fn calls, method calls, etc are valid
class NameReferencePass(Pass):
    def __init__(self, previous_pass: NameDeclarationPass):
        self.symbol_table = previous_pass.symbol_table
        # reset the symbol table to global scope
        self.symbol_table.current_scope_id = -1
        self.errors: List[CussError] = []
        self.program = previous_pass.program
        
    def run(self) -> Program:
        # TODO: implement
        return self.program
    

# TODO: implement TypeResolutionPass
# This pass converts all type annotations into concrete types using the symbol table
# We add a TypeVar to any Symbol that does not have a type annotation
class TypeResolutionPass(Pass):
    def __init__(self, previous_pass: NameReferencePass):
        super().__init__(previous_pass=previous_pass)
        
    def run(self) -> None:
        # TODO: implement
        raise NotImplementedError("TypeResolutionPass not implemented")
    
# TODO: implement TypeInferencePass
# This pass checks for TypeVars and infers them from the context
class TypeInferencePass(Pass):
    def __init__(self, previous_pass: TypeResolutionPass):
        super().__init__(previous_pass=previous_pass)
        
    def run(self) -> None:
        # TODO: implement
        raise NotImplementedError("TypeInferencePass not implemented")
    
# TODO: implement TypeCheckingPass
# This pass checks that all types are valid
class TypeCheckingPass(Pass):
    def __init__(self, previous_pass: TypeInferencePass):
        super().__init__(previous_pass=previous_pass)
        
    def run(self) -> None:
        # TODO: implement
        raise NotImplementedError("TypeCheckingPass not implemented")