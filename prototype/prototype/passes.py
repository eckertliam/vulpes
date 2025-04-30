# Passes are used to transform and validate the AST
# This is the base class for all passes
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Union

from .symbol import Symbol

from .errors import CussError, NameResolutionError, TypeInferenceError
from .parser import (
    ArrayTypeAnnotation,
    Assign,
    BinaryOp,
    Call,
    CallAttr,
    Declaration,
    Else,
    EnumDecl,
    Expr,
    FnDecl,
    FunctionTypeAnnotation,
    GetAttr,
    GetIndex,
    Ident,
    If,
    ImplDecl,
    Loop,
    NamedTypeAnnotation,
    Param,
    Program,
    Return,
    Statement,
    StructDecl,
    TupleTypeAnnotation,
    TypeAliasDecl,
    TypeAnnotation,
    UnaryOp,
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
    def __init__(
        self, program: Optional[Program] = None, previous_pass: Optional["Pass"] = None
    ):
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
                name, ast_id, self.current_scope_id
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

    def lookup_global(self, name: str) -> Optional[Symbol]:
        # lookup in only the global scope
        if name in self.table[-1].symbols:
            return self.table[-1].symbols[name]
        else:
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


# This pass checks that all variable references, fn calls, method calls, etc are valid
# This means checking that names are defined prior to their use
# and that field accesses, method calls, are accessing valid fields/methods
class NameReferencePass(Pass):
    def __init__(self, previous_pass: NameDeclarationPass):
        super().__init__(previous_pass=previous_pass)

    def run(self) -> Program:
        for declaration in self.program.declarations:
            if isinstance(declaration, FnDecl):
                self.visit_fn_decl(declaration)
            elif isinstance(declaration, ImplDecl):
                self.visit_impl_decl(declaration)
        return self.program

    def visit_fn_decl(self, fn_decl: FnDecl) -> None:
        # enter the fn's scope
        self.symbol_table.enter_scope(fn_decl.id)
        # iterate through the body and all child bodys and add all vars to the symbol table
        for statement in fn_decl.body:
            self.visit_statement(statement)
        # exit the fn's scope
        self.symbol_table.exit_scope()

    def visit_impl_decl(self, impl_decl: ImplDecl) -> None:
        # dont enter the impl's scope
        # all the impl's functions are scoped to their respective type's namespace
        # so we dont need to do anything
        # just loop through the methods and visit them
        for method in impl_decl.methods:
            self.visit_fn_decl(method)

    def visit_statement(self, statement: Statement) -> None:
        if isinstance(statement, FnDecl):
            self.visit_fn_decl(statement)
        elif isinstance(statement, VarDecl):
            self.visit_var_decl(statement)
        elif isinstance(statement, Assign):
            self.visit_assign(statement)
        elif isinstance(statement, Return):
            self.visit_return(statement)
        elif isinstance(statement, If):
            self.visit_if_stmt(statement)
        elif isinstance(statement, While):
            self.visit_while_stmt(statement)
        elif isinstance(statement, Loop):
            self.visit_loop_stmt(statement)
        elif isinstance(statement, Expr):
            self.visit_expr(statement)
        else:
            pass

    def visit_var_decl(self, var_decl: VarDecl) -> None:
        # we need to check that the expression is valid
        # we do this by visiting the expression
        self.visit_expr(var_decl.expr)

    def visit_assign(self, assign: Assign) -> None:
        # we need to visit the lhs and rhs
        self.visit_expr(assign.lhs)
        self.visit_expr(assign.rhs)

    def visit_return(self, return_stmt: Return) -> None:
        # we need to visit the return expression
        if return_stmt.expr is not None:
            self.visit_expr(return_stmt.expr)

    def visit_if_stmt(self, if_stmt: If) -> None:
        # we need to visit the cond and body
        self.visit_expr(if_stmt.cond)
        # then we enter the if's scope
        self.symbol_table.enter_scope(if_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in if_stmt.body:
            self.visit_statement(statement)
        # we exit the if's scope
        self.symbol_table.exit_scope()
        # if there is an else body we visit it
        if if_stmt.else_body is not None:
            self.visit_else_stmt(if_stmt.else_body)

    def visit_else_stmt(self, else_stmt: Else) -> None:
        # we need to enter the else's scope
        self.symbol_table.enter_scope(else_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in else_stmt.body:
            self.visit_statement(statement)
        # we exit the else's scope
        self.symbol_table.exit_scope()

    def visit_while_stmt(self, while_stmt: While) -> None:
        # we need to visit the cond and body
        self.visit_expr(while_stmt.cond)
        # then we enter the while's scope
        self.symbol_table.enter_scope(while_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in while_stmt.body:
            self.visit_statement(statement)
        # we exit the while's scope
        self.symbol_table.exit_scope()

    def visit_loop_stmt(self, loop_stmt: Loop) -> None:
        # we need to visit the body
        self.symbol_table.enter_scope(loop_stmt.id)
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in loop_stmt.body:
            self.visit_statement(statement)
        # we exit the loop's scope
        self.symbol_table.exit_scope()

    def visit_expr(self, expr: Expr) -> None:
        if isinstance(expr, Ident):
            self.visit_ident(expr)
        elif isinstance(expr, GetAttr):
            self.visit_get_attr(expr)
        elif isinstance(expr, Call):
            self.visit_call(expr)
        elif isinstance(expr, CallAttr):
            self.visit_call_attr(expr)
        elif isinstance(expr, GetIndex):
            self.visit_get_index(expr)
        elif isinstance(expr, BinaryOp):
            self.visit_binary_op(expr)
        elif isinstance(expr, UnaryOp):
            self.visit_unary_op(expr)
        # TODO: add remaining expr types

    def visit_get_attr(self, get_attr: GetAttr) -> None:
        # TODO: implement
        raise NotImplementedError("NameReferencePass not implemented")

    def visit_call(self, call: Call) -> None:
        # TODO: implement
        raise NotImplementedError("NameReferencePass not implemented")

    def visit_call_attr(self, call_attr: CallAttr) -> None:
        # TODO: implement
        raise NotImplementedError("NameReferencePass not implemented")

    def visit_get_index(self, get_index: GetIndex) -> None:
        # TODO: implement
        raise NotImplementedError("NameReferencePass not implemented")

    def visit_binary_op(self, binary_op: BinaryOp) -> None:
        # this is simple we just visit the left and right operands
        self.visit_expr(binary_op.lhs)
        self.visit_expr(binary_op.rhs)

    def visit_unary_op(self, unary_op: UnaryOp) -> None:
        # we need to visit the operand
        self.visit_expr(unary_op.operand)

    def visit_ident(self, ident: Ident) -> None:
        # we need to make sure the ident is defined prior to its use
        # we do this by looking up the ident in the symbol table
        symbol = self.symbol_table.lookup(ident.name)
        if symbol is None:
            self.errors.append(
                NameResolutionError(
                    f"Undefined variable {ident.name}", ident.line, ident.id
                )
            )
            return
        # if its defined we check the line of the definition
        # and compare it to the line of the use
        decl_node = self.program.get_node(symbol.ast_id)
        if decl_node is None:  # this should never happen
            raise RuntimeError("Cannot find node for symbol")
        decl_line = decl_node.line
        if decl_line >= ident.line:
            self.errors.append(
                NameResolutionError(
                    f"Variable {ident.name} is used before it is defined",
                    ident.line,
                    ident.id,
                )
            )
            return
        # we are all good here if the use occurs after the definition
        # we just add the symbol to the ident for later passes
        ident.symbol = symbol


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
