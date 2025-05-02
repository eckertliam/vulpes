from typing import Optional
from ..ast import (
    Else,
    EnumDecl,
    FnDecl,
    If,
    ImplDecl,
    Loop,
    NamedTypeAnnotation,
    Param,
    Program,
    Statement,
    StructDecl,
    TypeAliasDecl,
    VarDecl,
    While,
)
from ..errors import CussError, NameResolutionError
from .base_pass import Pass
from .symbol_table import Symbol


# Pass 1: Name Declaration Pass
# This pass enters all variable declarations into their respective scopes in a symbol table
class NameDeclarationPass(Pass):
    def __init__(self, program: Program) -> None:
        super().__init__(program=program)

    def add_symbol(self, name: str, ast_id: int, line: int) -> Optional[Symbol]:
        res = self.symbol_table.add_symbol(name, ast_id, line, self.program)
        if isinstance(res, CussError):
            self.errors.append(res)
            return None
        else:
            return res

    def run(self) -> None:
        # first we add all defined data structs to the symbol table
        # we do this so that we can then add their impls to their scopes
        for declaration in self.program.declarations:
            if isinstance(declaration, StructDecl):
                res = self.add_symbol(
                    declaration.name, declaration.id, declaration.line
                )
                if res is None:
                    return
                # add the symbol to the struct declaration node
                declaration.symbol = res
            elif isinstance(declaration, EnumDecl):
                res = self.add_symbol(
                    declaration.name, declaration.id, declaration.line
                )
                if res is None:
                    return
                # add the symbol to the enum declaration node
                declaration.symbol = res
            elif isinstance(declaration, TypeAliasDecl):
                res = self.add_symbol(
                    declaration.name, declaration.id, declaration.line
                )
                if res is None:
                    return
                # add the symbol to the type alias declaration node
                declaration.symbol = res

        # now we add all impls and fns to the symbol table
        for declaration in self.program.declarations:
            if isinstance(declaration, ImplDecl):
                self.impl_decl(declaration)
            elif isinstance(declaration, FnDecl):
                self.fn_decl(declaration)

        # check for any errors that may have been added
        if len(self.errors) > 0:
            for error in self.errors:
                error.report(self.program)

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
        res = self.add_symbol(method.name, method.id, method.line)
        if res is None:
            return
        # add the symbol to the method's declaration node
        method.symbol = res
        # we enter the method's scope
        self.symbol_table.enter_scope(method.id)
        # we add the self param
        self_type_annotation = NamedTypeAnnotation(impl_type.name, method.line)
        param = Param("self", self_type_annotation, method.line)
        method.params.insert(0, param)
        # we add all the params to the method's scope
        for param in method.params:
            res = self.add_symbol(param.name, param.id, param.line)
            if res is None:
                return
            # add the symbol to the param node
            param.symbol = res
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in method.body:
            self.statement(statement)
        # we exit the method's scope
        self.symbol_table.exit_scope()

    def fn_decl(self, fn: FnDecl) -> None:
        # we add the fn to the current scope
        res = self.add_symbol(fn.name, fn.id, fn.line)
        if res is None:
            return
        # add the symbol to the fn's declaration node
        fn.symbol = res
        # we enter the fn's scope
        self.symbol_table.enter_scope(fn.id)
        # we add all the params to the fn's scope
        for param in fn.params:
            res = self.add_symbol(param.name, param.id, param.line)
            if res is None:
                return
            # add the symbol to the param node
            param.symbol = res
        # we iterate through the body and all child bodys and add all vars to the symbol table
        for statement in fn.body:
            self.statement(statement)
        # we exit the fn's scope
        self.symbol_table.exit_scope()

    def statement(self, statement: Statement) -> None:
        # we only really care about vars and statements with bodies
        if isinstance(statement, VarDecl):
            res = self.add_symbol(statement.name, statement.id, statement.line)
            if res is None:
                return
            # add the symbol to the var's declaration node
            statement.symbol = res
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
