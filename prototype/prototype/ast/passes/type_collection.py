from itertools import chain

from typing import Dict, List, Set, Union
from prototype.errors import VulpesError
from prototype.ast import (
    ModuleManager,
    Module,
    StructDecl,
    UnionDecl,
    TypeAliasDecl,
    NamedTypeAnnotation,
    TypeAnnotation,
    GenericTypeAnnotation,
    ArrayTypeAnnotation,
    TupleTypeAnnotation,
    FunctionTypeAnnotation,
    Expr,
    Integer,
    StructField,
    UnionVariant,
    UnionStructVariant,
    UnionTupleVariant,
    UnionTagVariant,
    TypeParam,
)
from prototype.ast.symbol import Symbol
from prototype.result import Result
from .pass_types import PassResult
from prototype.types import (
    AnonymousFunctionType,
    ArrayType,
    MonoStructType,
    MonoTypeAlias,
    MonoUnionType,
    PolyStructType,
    PolyTypeAlias,
    PolyUnionType,
    Tag,
    TupleType,
    Type,
    TypeVar,
    VoidType,
)


class UndefinedType(VulpesError):
    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module
        super().__init__(f"Undefined type: {name} in module: {module}")


class CannotEvalSize(VulpesError):
    def __init__(self, expr: Expr, module: str):
        self.expr = expr
        self.module = module
        super().__init__(
            f"Cannot evaluate size of array with size expression: {expr} in module: {module}"
        )


class InvalidTypeArity(VulpesError):
    def __init__(self, name: str, expected: int, actual: int):
        self.name = name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Invalid type arity: {name} expected {expected} but got {actual}"
        )


class CyclicType(VulpesError):
    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module
        super().__init__(f"Cyclic type: {name} in module: {module}")


def type_collection_pass(
    module_manager: ModuleManager, prev_result: List[VulpesError] = []
) -> PassResult:
    """
    This pass collects all the types defined in a module and add them to the thier module's symbol table.
    It also attaches the type to the symbol of the definition. So types can cross through imports.

    Args:
        module_manager (ModuleManager): The module manager to collect types from.
        prev_result (List[VulpesError]): The previous result of the pass.

    Returns:
        PassResult: The result of the pass.
    """
    type_cache: Dict[str, Type] = {}
    return module_manager, prev_result + list(
        chain.from_iterable(
            visit_module(module, module_manager, type_cache)
            for module in module_manager.modules.values()
        )
    )


def get_type_from_symbol(
    symbol: Symbol, module: Module, mm: ModuleManager, type_cache: Dict[str, Type]
) -> Result[Type]:
    """Get a type from a symbol.

    Args:
        symbol (Symbol): The symbol to get the type from.
        module (Module): The module that the symbol is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    ty_decl = mm.get_node(symbol.ast_id)
    if (
        isinstance(ty_decl, StructDecl)
        or isinstance(ty_decl, UnionDecl)
        or isinstance(ty_decl, TypeAliasDecl)
    ):
        # get the module that the declaration is in
        ty_decl_mod = mm.get_module_by_id(symbol.module_id)
        if ty_decl_mod is None:
            return Result.err([UndefinedType(symbol.name, module.name)])
        # check if the type is in the module's type env
        if ty_decl.name in ty_decl_mod.type_env.types:
            return Result.ok(ty_decl_mod.type_env.types[ty_decl.name])
        else:
            return visit_type_decl(ty_decl, ty_decl_mod, mm, type_cache)
    return Result.err([UndefinedType(symbol.name, module.name)])


def get_type(
    type_name: str, type_cache: Dict[str, Type], module: Module, mm: ModuleManager
) -> Result[Type]:
    """Get a type from the cache or process it if it's not in the cache.
    This is used to handle recursive types as well as cross-module types where on type needs to be defined to be referenced.

    Args:
        type_name (str): The name of the type to get.
        type_cache (Dict[str, Type]): The cache to use for types.
        module (Module): The module that the type is being referenced from.
        mm (ModuleManager): The module manager to use.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    # first check if the type is in the cache
    if type_name in type_cache:
        return Result.ok(type_cache[type_name])
    # check if the type is in the module's type env
    if type_name in module.type_env.types:
        type_ = module.type_env.types[type_name]
        type_cache[type_name] = type_
        return Result.ok(type_)
    # check if it is in the module's symbol table
    mod_sym = module.symbol_table.lookup_global(type_name)
    if mod_sym is not None:
        res = get_type_from_symbol(mod_sym, module, mm, type_cache)
        if res.is_ok():
            type_cache[type_name] = res.unwrap()
        return res
    # if the symbol does not exist in the symbol table check the module's imports
    import_sym = module.imports.get(type_name)
    if import_sym is not None:
        res = get_type_from_symbol(import_sym, module, mm, type_cache)
        if res.is_ok():
            type_cache[type_name] = res.unwrap()
        return res
    return Result.err([UndefinedType(type_name, module.name)])


def add_type(
    name: str,
    type: Type,
    decl: Union[StructDecl, UnionDecl, TypeAliasDecl],
    module: Module,
    type_cache: Dict[str, Type],
) -> None:
    """Add the type to the module's type env.
    Attach the type to the symbol of the definition.
    Add the type to the type cache.

    Args:
        name (str): The name of the type.
        type (Type): The type to add.
        decl (Declaration): The declaration that defines the type.
        module (Module): The module that the type is being referenced from.
        type_cache (Dict[str, Type]): The cache to use for types.
    """
    # attach the type to the symbol of the definition
    assert decl.symbol is not None, f"Declaration {decl.name} has no symbol"
    decl.symbol.type = type
    # add the type to the module's type env
    module.type_env.set_type(name, type)
    # add the type to the type cache
    type_cache[name] = type


def visit_module(
    module: Module, mm: ModuleManager, type_cache: Dict[str, Type]
) -> List[VulpesError]:
    """Visit a module and collect all the types defined in it.

    Args:
        module (Module): The module to visit.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        List[VulpesError]: The errors found in the module.
    """
    errors: List[VulpesError] = []
    for ty_decl in module.top_level_nodes:
        if (
            isinstance(ty_decl, StructDecl)
            or isinstance(ty_decl, UnionDecl)
            or isinstance(ty_decl, TypeAliasDecl)
        ):
            res = visit_type_decl(ty_decl, module, mm, type_cache)
            if res.is_err():
                errors.extend(res.unwrap_err())
    return errors


def visit_type_decl(
    ty_decl: Union[StructDecl, UnionDecl, TypeAliasDecl],
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a type declaration and collect the type.

    Args:
        ty_decl (Declaration): The type declaration to visit.
        module (Module): The module that the type is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Union[Type, List[VulpesError]]: The type or an error if the type is not found.
    """
    if isinstance(ty_decl, StructDecl):
        return visit_struct_decl(ty_decl, module, mm, type_cache)
    elif isinstance(ty_decl, UnionDecl):
        return visit_union_decl(ty_decl, module, mm, type_cache)
    elif isinstance(ty_decl, TypeAliasDecl):
        return visit_type_alias_decl(ty_decl, module, mm, type_cache)


def collect_type_params(type_params: List[TypeParam]) -> Set[TypeVar]:
    """Convert a list of type parameters to a set of type variables.

    Args:
        type_params (List[TypeParam]): The type parameters to collect.

    Returns:
        Set[TypeVar]: The type variables.
    """
    return {TypeVar(ty_param.name) for ty_param in type_params}


def visit_struct_decl(
    struct_decl: StructDecl,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a struct declaration and collect the type.
    Attach the type to the symbol of the definition.
    Add the type to the module's type env.
    Add the type to the type cache.

    Args:
        struct_decl (StructDecl): The struct declaration to visit.
        module (Module): The module that the struct is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    # immediately create the type to support recursive types
    struct_type = (
        MonoStructType(struct_decl.name, [], {})
        if len(struct_decl.type_params) == 0
        else PolyStructType(
            struct_decl.name, collect_type_params(struct_decl.type_params), {}
        )
    )
    add_type(struct_decl.name, struct_type, struct_decl, module, type_cache)
    # collect the type parameters
    ty_params: Set[TypeVar] = collect_type_params(struct_decl.type_params)
    # add the type params to the type
    if isinstance(struct_type, PolyStructType):
        struct_type.type_params = ty_params
    # collect the fields
    fields: Dict[str, Type] = {}
    for field in struct_decl.fields:
        field_type = visit_type_annotation(
            field.type_annotation, module, mm, type_cache
        )
        if field_type.is_err():
            return field_type
        fields[field.name] = field_type.unwrap()
    struct_type.fields = fields
    return Result.ok(struct_type)


def visit_struct_fields(
    fields: List[StructField],
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Dict[str, Type]]:
    """Visit a list of struct fields and collect the types.

    Args:
        fields (List[StructField]): The struct fields to visit.
        module (Module): The module that the struct fields are being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Union[Dict[str, Type], List[VulpesError]]: The types of the struct fields or an error if the type is not found.
    """
    field_types: Dict[str, Type] = {}
    for field in fields:
        result = visit_struct_field(field, module, mm, type_cache)
        if result.is_err():
            return Result.err(result.unwrap_err())
        field_types[field.name] = result.unwrap()
    return Result.ok(field_types)


def visit_struct_field(
    field: StructField, module: Module, mm: ModuleManager, type_cache: Dict[str, Type]
) -> Result[Type]:
    """Visit a struct field and return the type.

    Args:
        field (StructField): The struct field to visit.
        module (Module): The module that the struct field is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Union[Type, List[VulpesError]]: The type of the field or an error if the type is not found.
    """
    field_type = visit_type_annotation(field.type_annotation, module, mm, type_cache)
    # check for errors
    if field_type.is_err():
        return field_type
    return Result.ok(field_type.unwrap())


def visit_union_decl(
    union_decl: UnionDecl,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a union declaration and collect the type.

    Args:
        union_decl (UnionDecl): The union declaration to visit.
        module (Module): The module that the union is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Union[Type, List[VulpesError]]: The type or an error if the type is not found.
    """
    # immediately create the type to support recursive types
    union_type = (
        MonoUnionType(union_decl.name, [], {})
        if len(union_decl.type_params) == 0
        else PolyUnionType(
            union_decl.name, collect_type_params(union_decl.type_params), {}
        )
    )
    add_type(union_decl.name, union_type, union_decl, module, type_cache)
    # collect the type parameters
    ty_params: Set[TypeVar] = collect_type_params(union_decl.type_params)
    # add the type params to the type
    if isinstance(union_type, PolyUnionType):
        union_type.type_params = ty_params
    # collect the variants
    variants: Dict[str, Type] = {}
    for variant in union_decl.variants:
        result = visit_union_variant(variant, module, mm, type_cache)
        if result.is_err():
            return Result.err(result.unwrap_err())
        variants[variant.name] = result.unwrap()
    union_type.variants = variants
    return Result.ok(union_type)


def visit_union_variant(
    variant: UnionVariant,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a union variant and return a tuple of the name and type.

    Args:
        variant (UnionVariant): The union variant to visit.
        module (Module): The module that the union variant is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Union[Tuple[str, Type], List[VulpesError]]: The name and type of the variant or an error if the type is not found.
    """
    if isinstance(variant, UnionStructVariant):
        return visit_struct_variant(variant, module, mm, type_cache)
    elif isinstance(variant, UnionTupleVariant):
        return visit_tuple_variant(variant, module, mm, type_cache)
    elif isinstance(variant, UnionTagVariant):
        return visit_tag_variant(variant)
    else:
        raise ValueError(f"Unknown union variant: {variant}")


def visit_struct_variant(
    variant: UnionStructVariant,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a struct variant and return a tuple of the name and type.

    Args:
        variant (UnionStructVariant): The struct variant to visit.
        module (Module): The module that the struct variant is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Union[Tuple[str, Type], List[VulpesError]]: The name and type of the variant or an error if the type is not found.
    """
    # get the name of the variant
    name = variant.name
    # get the fields
    fields = visit_struct_fields(variant.fields, module, mm, type_cache)
    if fields.is_err():
        return Result.err(fields.unwrap_err())
    return Result.ok(MonoStructType(name, [], fields.unwrap()))


def visit_tuple_variant(
    variant: UnionTupleVariant,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a tuple variant and return a tuple of the name and type.

    Args:
        variant (UnionTupleVariant): The tuple variant to visit.
        module (Module): The module that the tuple variant is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type of the variant or an error if the type is not found.
    """
    res = visit_tuple_elems(variant.types, module, mm, type_cache)
    if res.is_err():
        return Result.err(res.unwrap_err())
    return Result.ok(TupleType(res.unwrap()))


def visit_tag_variant(variant: UnionTagVariant) -> Result[Type]:
    """Visit a tag variant and return a tuple of the name and type.

    Args:
        variant (UnionTagVariant): The tag variant to visit.

    Returns:
        Result[Type]: The type of the variant or an error if the type is not found.
    """
    return Result.ok(Tag(variant.name))


def visit_type_alias_decl(
    type_alias_decl: TypeAliasDecl,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a type alias declaration and collect the type.

    Args
        type_alias_decl (TypeAliasDecl): The type alias declaration to visit.
        module (Module): The module that the type alias is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    # immediately create the type to support recursive types
    type_alias_type = (
        MonoTypeAlias(type_alias_decl.name, [], VoidType())
        if len(type_alias_decl.type_params) == 0
        else PolyTypeAlias(
            type_alias_decl.name,
            collect_type_params(type_alias_decl.type_params),
            VoidType(),
        )
    )
    add_type(type_alias_decl.name, type_alias_type, type_alias_decl, module, type_cache)
    type_params: Set[TypeVar] = collect_type_params(type_alias_decl.type_params)
    # add the type params to the type
    if isinstance(type_alias_type, PolyTypeAlias):
        type_alias_type.type_params = type_params
    # visit the type annotation
    res = visit_type_annotation(type_alias_decl.type_annotation, module, mm, type_cache)
    if res.is_err():
        return Result.err(res.unwrap_err())
    type_alias_type.type = res.unwrap()
    return Result.ok(type_alias_type)


def visit_type_annotation(
    type_ann: TypeAnnotation,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a type annotation and return the type.

    Args:
        type_ann (TypeAnnotation): The type annotation to visit.
        module (Module): The module that the type annotation is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    if isinstance(type_ann, NamedTypeAnnotation):
        return get_type(type_ann.name, type_cache, module, mm)
    elif isinstance(type_ann, GenericTypeAnnotation):
        return visit_generic_type_annotation(type_ann, module, mm, type_cache)
    elif isinstance(type_ann, ArrayTypeAnnotation):
        return visit_array_type_annotation(type_ann, module, mm, type_cache)
    elif isinstance(type_ann, TupleTypeAnnotation):
        return visit_tuple_type_annotation(type_ann, module, mm, type_cache)
    elif isinstance(type_ann, FunctionTypeAnnotation):
        return visit_function_type_annotation(type_ann, module, mm, type_cache)
    else:
        raise ValueError(f"Unknown type annotation: {type_ann}")


def visit_generic_type_annotation(
    type_ann: GenericTypeAnnotation,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a generic type annotation and return the type.

    Args:
        type_ann (GenericTypeAnnotation): The generic type annotation to visit.
        module (Module): The module that the generic type annotation is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    # get the name of the generic type
    name = type_ann.name
    # get the type
    type_res = get_type(name, type_cache, module, mm)
    if type_res.is_err():
        return type_res
    poly_type = type_res.unwrap()
    if (
        isinstance(poly_type, PolyStructType)
        or isinstance(poly_type, PolyUnionType)
        or isinstance(poly_type, PolyTypeAlias)
    ):
        # make the mono type using the type args
        # first make sure check arity between the type args of the generic type
        # and the type params of the poly type
        if len(type_ann.type_args) != len(poly_type.type_params):
            return Result.err(
                [
                    InvalidTypeArity(
                        type_ann.name,
                        len(poly_type.type_params),
                        len(type_ann.type_args),
                    )
                ]
            )
        # convert the type args to types
        type_args: List[Type] = []
        for type_arg in type_ann.type_args:
            res = visit_type_annotation(type_arg, module, mm, type_cache)
            if res.is_err():
                return Result.err(res.unwrap_err())
            type_args.append(res.unwrap())
        # make the mono type using the type args
        if isinstance(poly_type, PolyStructType):
            return Result.ok(poly_type.monomorphize(type_args))
        elif isinstance(poly_type, PolyUnionType):
            return Result.ok(poly_type.monomorphize(type_args))
        elif isinstance(poly_type, PolyTypeAlias):
            return Result.ok(poly_type.monomorphize(type_args))
        else:
            raise ValueError(f"Unknown poly type: {poly_type}")
    else:
        return Result.err([UndefinedType(name, module.name)])


def visit_array_type_annotation(
    type_ann: ArrayTypeAnnotation,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit an array type annotation and return the type.

    Args:
        type_ann (ArrayTypeAnnotation): The array type annotation to visit.
        module (Module): The module that the array type annotation is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Union[Type, List[VulpesError]]: The type or a list of errors if the type is not found.
    """
    res = visit_type_annotation(type_ann.elem_type, module, mm, type_cache)
    if res.is_err():
        return res
    size_res = eval_const_expr(type_ann.size, module)
    if size_res.is_err():
        return Result.err(size_res.unwrap_err())
    return Result.ok(ArrayType(res.unwrap(), size_res.unwrap()))


def eval_const_expr(expr: Expr, module: Module) -> Result[int]:
    """Evaluate a constant expression and return the result.

    Args:
        expr (Expr): The expression to evaluate.
        module (Module): The module that the expression is being evaluated in.

    Returns:
        Result[int]: The result of the expression.
    """
    # TODO: This is an incredibly simple implementation that only supports integer literals
    # Eventually we will need to support more complex expressions
    if isinstance(expr, Integer):
        return Result.ok(expr.value)
    else:
        return Result.err([CannotEvalSize(expr, module.name)])


def visit_tuple_type_annotation(
    type_ann: TupleTypeAnnotation,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a tuple type annotation and return the type.

    Args:
        type_ann (TupleTypeAnnotation): The tuple type annotation to visit.
        module (Module): The module that the tuple type annotation is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    res = visit_tuple_elems(type_ann.elem_types, module, mm, type_cache)
    if res.is_err():
        return Result.err(res.unwrap_err())
    return Result.ok(TupleType(res.unwrap()))


def visit_tuple_elems(
    types: List[TypeAnnotation],
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[List[Type]]:
    """Visit a list of type annotations and return the types.

    Args:
        types (List[TypeAnnotation]): _description_
        module (Module): _description_
        mm (ModuleManager): _description_
        type_cache (Dict[str, Type]): _description_

    Returns:
        Result[List[Type]]: The types or an error if the types are not found.
    """
    elem_types: List[Type] = []
    for elem_ann in types:
        res = visit_type_annotation(elem_ann, module, mm, type_cache)
        if res.is_err():
            return Result.err(res.unwrap_err())
        elem_types.append(res.unwrap())
    return Result.ok(elem_types)


def visit_function_type_annotation(
    type_ann: FunctionTypeAnnotation,
    module: Module,
    mm: ModuleManager,
    type_cache: Dict[str, Type],
) -> Result[Type]:
    """Visit a function type annotation and return the type.

    Args:
        type_ann (FunctionTypeAnnotation): The function type annotation to visit.
        module (Module): The module that the function type annotation is being referenced from.
        mm (ModuleManager): The module manager to use.
        type_cache (Dict[str, Type]): The cache to use for types.

    Returns:
        Result[Type]: The type or an error if the type is not found.
    """
    params: List[Type] = []
    for param_ann in type_ann.params:
        res = visit_type_annotation(param_ann, module, mm, type_cache)
        if res.is_err():
            return res
        params.append(res.unwrap())
    res = visit_type_annotation(type_ann.ret_type, module, mm, type_cache)
    if res.is_err():
        return res
    return Result.ok(AnonymousFunctionType(params, res.unwrap()))
