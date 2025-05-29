from itertools import chain
from typing import List, Union

from prototype.errors import VulpesError
from prototype.ast import (
    FnDecl,
    Statement,
    VarDecl,
    If,
    While,
    Loop,
    TypeAnnotation,
    NamedTypeAnnotation,
    GenericTypeAnnotation,
    ArrayTypeAnnotation,
    TupleTypeAnnotation,
    FunctionTypeAnnotation,
)
from .pass_types import PassResult
from prototype.result import Result
from prototype.types import (
    AnonymousFunctionType,
    ArrayType,
    PolyFunctionType,
    PolyStructType,
    PolyTypeAlias,
    PolyUnionType,
    TupleType,
    Type,
    TypeHole,
)
from prototype.ast import ModuleManager, Module
from .type_collection import eval_const_expr


class InvalidTypeApplication(VulpesError):
    """This error is raised when a type application is invalid.
    Such as when a type arg is expected but not provided. Or when a type arg is provided but not expected.
    """

    def __init__(self, assignee: str, type_name: Type, arity: int, module: str):
        self.assignee = assignee
        self.type_name = type_name
        self.arity = arity
        self.module = module
        super().__init__(
            f"Invalid type application for '{assignee}': Expected arity {arity} for type '{type_name}' "
            f"but received incorrect number of arguments. (Module: {module})"
        )


class UnresolvedType(VulpesError):
    """A type annotation refers to a non-existent type."""

    def __init__(self, type_name: str, module: str):
        self.type_name = type_name
        self.module = module
        super().__init__(
            f"Unresolved type name '{type_name}' referenced in module '{module}'. Did you forget to define or import it?"
        )


def type_norm_pass(
    module_manager: ModuleManager, prev_result: List[VulpesError] = []
) -> PassResult:
    """This pass walks the AST and normalizes all type annotations into their internal representations.
    It attaches these types to the symbol of the declaration.
    If a declaration has no type annotation, it attaches a TypeHole to the symbol.

    Args:
        module_manager (ModuleManager): The module manager to normalize types for.
        prev_result (List[VulpesError], optional): The previous result of the pass. Defaults to [].

    Returns:
        PassResult: The result of the pass.
    """
    return module_manager, prev_result + list(
        chain.from_iterable(
            visit_module(module, module_manager)
            for module in module_manager.modules.values()
        )
    )


def visit_module(module: Module, module_manager: ModuleManager) -> List[VulpesError]:
    """This function visits a module and normalizes all type annotations into their internal representations.
    It attaches these types to the symbol of the declaration.
    If a declaration has no type annotation, it attaches a TypeHole to the symbol.

    Args:
        module (Module): The module to visit.
        module_manager (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    return list(
        chain.from_iterable(
            visit_fn_decl(top_level_node, module, module_manager)
            for top_level_node in module.top_level_nodes
            if isinstance(top_level_node, FnDecl)
        )
    )


def visit_fn_decl(
    fn_decl: FnDecl, module: Module, module_manager: ModuleManager
) -> List[VulpesError]:
    """This function visits a function declaration and normalizes all type annotations into their internal representations.

    Args:
        fn_decl (FnDecl): The function declaration to visit.
        module (Module): The module that the function declaration is in.
        module_manager (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    return visit_block(fn_decl.body, module, module_manager)


def visit_block(
    block: List[Statement], module: Module, mm: ModuleManager
) -> List[VulpesError]:
    """Iterates over a block and normalizes all type annotations into their internal representations attaching them to the symbols of the declarations.

    Args:
        block (List[Statement]): The block to visit.
        module (Module): The module that the block is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    return list(chain.from_iterable(visit_stmt(stmt, module, mm) for stmt in block))


def visit_stmt(stmt: Statement, module: Module, mm: ModuleManager) -> List[VulpesError]:
    """Dispatches to the appropriate visit function for the statement.

    Args:
        stmt (Statement): The statement to visit.
        module (Module): The module that the statement is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    if isinstance(stmt, VarDecl):
        return visit_var_decl(stmt, module, mm)
    elif isinstance(stmt, If):
        return visit_if(stmt, module, mm)
    elif isinstance(stmt, While):
        return visit_while(stmt, module, mm)
    elif isinstance(stmt, Loop):
        return visit_loop(stmt, module, mm)
    else:
        return []


def visit_var_decl(
    var_decl: VarDecl, module: Module, mm: ModuleManager
) -> List[VulpesError]:
    """Visits a variable declaration and normalizes the type annotation into its internal representation or generates a TypeHole.
    Attaches the type to the symbol of the declaration.

    Args:
        var_decl (VarDecl): The variable declaration to visit.
        module (Module): The module that the variable declaration is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    assert (
        var_decl.symbol is not None
    ), f"Variable declaration {var_decl.name} has no symbol"
    if var_decl.type_annotation is None:
        var_decl.symbol.type = TypeHole()
    else:
        type_res = visit_type_annotation(var_decl.type_annotation, module, mm)
        if type_res.is_err():
            return type_res.unwrap_err()
        var_decl.symbol.type = type_res.unwrap()
    return []


def visit_if(if_stmt: If, module: Module, mm: ModuleManager) -> List[VulpesError]:
    """Visits all statements in the if and else bodies.

    Args:
        if_stmt (If): The if statement to visit.
        module (Module): The module that the if statement is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    return visit_block(if_stmt.body, module, mm) + (
        visit_block(if_stmt.else_body.body, module, mm)
        if if_stmt.else_body is not None
        else []
    )


def visit_while(
    while_stmt: While, module: Module, mm: ModuleManager
) -> List[VulpesError]:
    """Visits all statements in the while body.

    Args:
        while_stmt (While): The while statement to visit.
        module (Module): The module that the while statement is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    return visit_block(while_stmt.body, module, mm)


def visit_loop(loop_stmt: Loop, module: Module, mm: ModuleManager) -> List[VulpesError]:
    """Visits all statements in the loop body.

    Args:
        loop_stmt (Loop): The loop statement to visit.
        module (Module): The module that the loop statement is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        List[VulpesError]: The errors encountered during the visit.
    """
    return visit_block(loop_stmt.body, module, mm)


def visit_type_annotation(
    type_annotation: TypeAnnotation, module: Module, mm: ModuleManager
) -> Result[Type]:
    """Visits a type annotation and dispatches to the appropriate visit function to normalize it.

    Args:
        type_annotation (TypeAnnotation): The type annotation to visit.
        module (Module): The module that the type annotation is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        Result[Type]: The type of the type annotation or an error if the type annotation is invalid.
    """
    if isinstance(type_annotation, NamedTypeAnnotation):
        return visit_named_type_annotation(type_annotation, module, mm)
    elif isinstance(type_annotation, GenericTypeAnnotation):
        return visit_generic_type_annotation(type_annotation, module, mm)
    elif isinstance(type_annotation, ArrayTypeAnnotation):
        return visit_array_type_annotation(type_annotation, module, mm)
    elif isinstance(type_annotation, TupleTypeAnnotation):
        return visit_tuple_type_annotation(type_annotation, module, mm)
    elif isinstance(type_annotation, FunctionTypeAnnotation):
        return visit_function_type_annotation(type_annotation, module, mm)
    else:
        raise NotImplementedError(f"Type annotation {type_annotation} not implemented")


def visit_named_type_annotation(
    type_annotation: NamedTypeAnnotation, module: Module, mm: ModuleManager
) -> Result[Type]:
    """Visits a named type annotation and returns the type of the type annotation.

    Args:
        type_annotation (NamedTypeAnnotation): The named type annotation to visit.
        module (Module): The module that the named type annotation is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        Result[Type]: The type of the named type annotation or an error if the type annotation is invalid.
    """
    # first check if the type is defined in the module's type env
    type_res = module.type_env.get_type(type_annotation.name)
    if type_res is not None:
        return Result.ok(type_res)
    # if the type is not defined in the module's type env
    # check the module's imports
    type_symbol = module.imports.get(type_annotation.name)
    if type_symbol is not None:
        # check that the type symbol has a type attached to it
        type_res = type_symbol.type
        if type_res is not None:
            return Result.ok(type_res)
    # if all else fails, return an error
    return Result.err([UnresolvedType(type_annotation.name, module.name)])


def is_poly_type(type: Type) -> bool:
    """Checks if a type is a poly type.

    Args:
        type (Type): The type to check.

    Returns:
        bool: True if the type is a poly type, False otherwise.
    """
    return (
        isinstance(type, PolyFunctionType)
        or isinstance(type, PolyStructType)
        or isinstance(type, PolyUnionType)
        or isinstance(type, PolyTypeAlias)
    )


def visit_generic_type_annotation(
    type_annotation: GenericTypeAnnotation, module: Module, mm: ModuleManager
) -> Result[Type]:
    """Visits a generic type annotation and returns the type of the type annotation.

    Args:
        type_annotation (GenericTypeAnnotation): The generic type annotation to visit.
        module (Module): The module that the generic type annotation is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        Result[Type]: The type of the generic type annotation or an error if the type annotation is invalid.
    """
    # first treat the name as a named type annotation
    named_type_res = visit_named_type_annotation(
        NamedTypeAnnotation(type_annotation.name, 0), module, mm
    )
    if named_type_res.is_err():
        return named_type_res
    named_type = named_type_res.unwrap()
    # make sure the type is a poly type
    if is_poly_type(named_type):
        assert (
            isinstance(named_type, PolyFunctionType)
            or isinstance(named_type, PolyStructType)
            or isinstance(named_type, PolyUnionType)
            or isinstance(named_type, PolyTypeAlias)
        )
        # check that the arity of the type is the same as the number of type arguments
        if len(type_annotation.type_args) == len(named_type.type_params):
            # convert the type arguments to types
            type_args: List[Type] = []
            for type_arg in type_annotation.type_args:
                type_arg_res = visit_type_annotation(type_arg, module, mm)
                if type_arg_res.is_err():
                    return type_arg_res
                type_args.append(type_arg_res.unwrap())
            # monomorphize the type
            return Result.ok(named_type.monomorphize(type_args))
        else:
            return Result.err(
                [
                    InvalidTypeApplication(
                        type_annotation.name,
                        named_type,
                        len(named_type.type_params),
                        module.name,
                    )
                ]
            )
    else:
        return Result.err([UnresolvedType(type_annotation.name, module.name)])


def visit_array_type_annotation(
    type_annotation: ArrayTypeAnnotation, module: Module, mm: ModuleManager
) -> Result[Type]:
    """Visits an array type annotation and returns the type of the type annotation.

    Args:
        type_annotation (ArrayTypeAnnotation): The array type annotation to visit.
        module (Module): The module that the array type annotation is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        Result[Type]: The type of the array type annotation or an error if the type annotation is invalid.
    """
    # first attempt to evaluate the size expression
    size_res = eval_const_expr(type_annotation.size, module)
    if size_res.is_err():
        return Result.err(size_res.unwrap_err())
    size = size_res.unwrap()
    # visit the element type
    elem_type_res = visit_type_annotation(type_annotation.elem_type, module, mm)
    if elem_type_res.is_err():
        return elem_type_res
    elem_type = elem_type_res.unwrap()
    # return the array type
    return Result.ok(ArrayType(elem_type, size))


def visit_tuple_type_annotation(
    type_annotation: TupleTypeAnnotation, module: Module, mm: ModuleManager
) -> Result[Type]:
    """Visits a tuple type annotation and returns the type of the type annotation

    Args:
        type_annotation (TupleTypeAnnotation): The tuple type annotation to visit
        module (Module): The module that the tuple type annotation is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        Result[Type]: The type of the tuple type annotation or an error if the type annotation is invalid.
    """
    # visit the element types
    elem_types: List[Type] = []
    for elem_type in type_annotation.elem_types:
        elem_type_res = visit_type_annotation(elem_type, module, mm)
        if elem_type_res.is_err():
            return elem_type_res
        elem_types.append(elem_type_res.unwrap())
    # return the tuple type
    return Result.ok(TupleType(elem_types))


def visit_function_type_annotation(
    type_annotation: FunctionTypeAnnotation, module: Module, mm: ModuleManager
) -> Result[Type]:
    """Visits a function type annotation and returns the type of the type annotation.

    Args:
        type_annotation (FunctionTypeAnnotation): The function type annotation to visit.
        module (Module): The module that the function type annotation is in.
        mm (ModuleManager): The module manager to normalize types for.

    Returns:
        Result[Type]: The type of the function type annotation or an error if the type annotation is invalid.
    """
    # visit the parameter types
    param_types: List[Type] = []
    for param_type in type_annotation.params:
        param_type_res = visit_type_annotation(param_type, module, mm)
        if param_type_res.is_err():
            return param_type_res
        param_types.append(param_type_res.unwrap())
    # visit the return type
    ret_type_res = visit_type_annotation(type_annotation.ret_type, module, mm)
    if ret_type_res.is_err():
        return ret_type_res
    ret_type = ret_type_res.unwrap()
    # return the function type
    return Result.ok(AnonymousFunctionType(param_types, ret_type))
