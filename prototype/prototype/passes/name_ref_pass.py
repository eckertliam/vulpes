from ..ast import (
    AccessField,
    ArrayExpr,
    Assign,
    BinaryOp,
    Call,
    CallMethod,
    Else,
    EnumStructExpr,
    EnumTupleExpr,
    Expr,
    FieldInit,
    FnDecl,
    GetIndex,
    Ident,
    If,
    ImplDecl,
    Loop,
    Return,
    Statement,
    StructExpr,
    TupleExpr,
    UnaryOp,
    VarDecl,
    While,
)
from ..errors import NameResolutionError
from .base_pass import Pass
from .name_decl_pass import NameDeclarationPass


# This pass checks that all variable references, fn calls, method calls, etc are valid
# This means checking that names are defined prior to their use
# and that field accesses, method calls, are accessing valid fields/methods
class NameReferencePass(Pass):
    def __init__(self, previous_pass: NameDeclarationPass):
        super().__init__(previous_pass=previous_pass)

    def run(self) -> None:
        for declaration in self.program.declarations:
            if isinstance(declaration, FnDecl):
                self.visit_fn_decl(declaration)
            elif isinstance(declaration, ImplDecl):
                self.visit_impl_decl(declaration)

        # check for any errors that may have been added
        if len(self.errors) > 0:
            for error in self.errors:
                error.report(self.program)

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
        elif isinstance(expr, AccessField):
            self.visit_access_field(expr)
        elif isinstance(expr, Call):
            self.visit_call(expr)
        elif isinstance(expr, CallMethod):
            self.visit_call_method(expr)
        elif isinstance(expr, GetIndex):
            self.visit_get_index(expr)
        elif isinstance(expr, BinaryOp):
            self.visit_binary_op(expr)
        elif isinstance(expr, UnaryOp):
            self.visit_unary_op(expr)
        elif isinstance(expr, StructExpr):
            self.visit_struct_expr(expr)
        elif isinstance(expr, TupleExpr):
            self.visit_tuple_expr(expr)
        elif isinstance(expr, EnumStructExpr):
            self.visit_enum_struct_expr(expr)
        elif isinstance(expr, EnumTupleExpr):
            self.visit_enum_tuple_expr(expr)
        elif isinstance(expr, ArrayExpr):
            self.visit_array_expr(expr)

    def visit_struct_expr(self, struct_expr: StructExpr) -> None:
        # we need to visit all the fields
        for field in struct_expr.fields:
            self.visit_field_init(field)

    def visit_field_init(self, field_init: FieldInit) -> None:
        # we need to visit the expr
        self.visit_expr(field_init.expr)

    def visit_tuple_expr(self, tuple_expr: TupleExpr) -> None:
        # we need to visit all the elements
        for elem in tuple_expr.elems:
            self.visit_expr(elem)

    def visit_enum_struct_expr(self, enum_struct_expr: EnumStructExpr) -> None:
        # we visit all the field inits just like a struct expr
        for field in enum_struct_expr.fields:
            self.visit_field_init(field)

    def visit_enum_tuple_expr(self, enum_tuple_expr: EnumTupleExpr) -> None:
        # we visit all the elements just like a tuple expr
        for elem in enum_tuple_expr.elems:
            self.visit_expr(elem)

    def visit_array_expr(self, array_expr: ArrayExpr) -> None:
        # we visit all the elements just like a tuple expr
        for elem in array_expr.elems:
            self.visit_expr(elem)

    def visit_access_field(self, access_field: AccessField) -> None:
        # we need to ensure the object is defined
        self.visit_expr(access_field.obj)

    def visit_call(self, call: Call) -> None:
        # in name reference pass we dont care if the callee is actually callable
        # for now we just need to ensure that the callee is defined
        self.visit_expr(call.callee)
        # then we visit all the args
        for arg in call.args:
            self.visit_expr(arg)

    def visit_call_method(self, call_attr: CallMethod) -> None:
        # we need to ensure the object is defined
        # NOTE: in later passes we will check if the object is an object that contains the method
        self.visit_expr(call_attr.obj)
        # then we visit all the args
        for arg in call_attr.args:
            self.visit_expr(arg)

    def visit_get_index(self, get_index: GetIndex) -> None:
        # we need to ensure the object is defined
        self.visit_expr(get_index.obj)
        # then we visit the index
        self.visit_expr(get_index.index)

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
