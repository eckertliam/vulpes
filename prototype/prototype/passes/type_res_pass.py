from typing import Dict, List, Optional, Set, Tuple, Union

from ..errors import TypeInferenceError
from .name_ref_pass import NameReferencePass
from .base_pass import Pass
from ..ast import (
    ArrayTypeAnnotation,
    Declaration,
    Else,
    EnumDecl,
    EnumStructField,
    EnumStructVariant,
    EnumTupleVariant,
    EnumUnitVariant,
    FnDecl,
    FunctionTypeAnnotation,
    GenericTypeAnnotation,
    If,
    ImplDecl,
    Loop,
    NamedTypeAnnotation,
    PartialTraitMethod,
    Statement,
    StructDecl,
    StructField,
    TraitDecl,
    TupleTypeAnnotation,
    TypeAliasDecl,
    TypeAnnotation,
    TypeParam,
    VarDecl,
    While,
)
from ..types import (
    ArrayType,
    EnumStructVariantType,
    EnumTupleVariantType,
    EnumType,
    EnumUnitVariantType,
    EnumVariantType,
    FunctionType,
    GenericType,
    StructType,
    Trait,
    TraitBound,
    TupleType,
    Type,
    TypeAlias,
    TypeHole,
    TypeVar,
)


# TODO: add docstrings to all methods
# TODO: add type param handling and resolution


class TypeResolutionPass(Pass):
    """
    This pass adds type definitions to the type env
    it then attaches types to ast nodes that are typed
    it adds type vars to ast nodes that will need to be inferred in the next pass
    """

    def __init__(self, previous_pass: NameReferencePass):
        super().__init__(previous_pass=previous_pass)
        # we need to keep track of the type aliases, enums, and structs
        # we sometimes need to jump around the ast to add types to the type env
        # so we need to keep track of what we have already visited
        self.visited_type_aliases: Set[int] = set()
        self.visited_enums: Set[int] = set()
        self.visited_structs: Set[int] = set()
        self.visited_traits: Set[int] = set()

    def convert_type_annotation_top_level(
        self, type_annotation: TypeAnnotation, decl_line: int, decl_id: int
    ) -> Optional[Type]:
        # used to convert type annotations that are at the top level
        # this means converting type annotations for structs, enums, and type aliases
        if isinstance(type_annotation, NamedTypeAnnotation):
            existing_type = self.type_env.get_type(type_annotation.name)
            if existing_type is None:
                # we need to go to the ast node of the type declaration and add it
                # then come back here and convert the type annotation
                # we search global for the name
                type_decl = self.symbol_table.lookup_global(type_annotation.name)
                if type_decl is None:
                    self.errors.append(
                        TypeInferenceError(
                            f"Undefined type {type_annotation.name}",
                            decl_line,
                            decl_id,
                        )
                    )
                    return None
                # get the node of the type declaration
                type_decl_node = self.program.get_node(type_decl.ast_id)
                if type_decl_node is None:
                    raise RuntimeError("Cannot find node for type declaration")
                # check if the type declaration is a type alias, enum, or struct
                if not (
                    isinstance(type_decl_node, TypeAliasDecl)
                    or isinstance(type_decl_node, EnumDecl)
                    or isinstance(type_decl_node, StructDecl)
                ):
                    self.errors.append(
                        TypeInferenceError(
                            f"Type {type_annotation.name} is not a type alias, enum, or struct",
                            decl_line,
                            decl_id,
                        )
                    )
                    return None
                # run type resolution on the type declaration
                self.visit_type_decl(type_decl_node)
                # we refetch the type
                existing_type = self.type_env.get_type(type_annotation.name)
                # if it still doesnt exist something went wrong
                if existing_type is None:
                    self.errors.append(
                        TypeInferenceError(
                            f"Type {type_annotation.name} is not defined",
                            decl_line,
                            decl_id,
                        )
                    )
                    return None
            # existing type is defined so we return it
            return existing_type
        elif isinstance(type_annotation, ArrayTypeAnnotation):
            # we need to convert the element type
            elem_type = self.convert_type_annotation_top_level(
                type_annotation.elem_type, decl_line, decl_id
            )
            if elem_type is None:
                # if somehting went wrong we return None
                # the attempt to convert the element type will have added an error
                return None
            # we return the array type
            return ArrayType(elem_type)
        elif isinstance(type_annotation, TupleTypeAnnotation):
            # we need to convert the element types
            elem_types = [
                self.convert_type_annotation_top_level(elem_type, decl_line, decl_id)
                for elem_type in type_annotation.elem_types
            ]
            for elem_type in elem_types:
                if elem_type is None:
                    # if somehting went wrong we return None
                    # the attempt to convert the element type will have added an error
                    return None
            # to please the type checker we need to filter out None types even though we know there are none
            elem_types = [t for t in elem_types if t is not None]
            # we return the tuple type
            return TupleType(elem_types)
        elif isinstance(type_annotation, FunctionTypeAnnotation):
            # we need to convert the parameter types
            param_types = [
                self.convert_type_annotation_top_level(param_type, decl_line, decl_id)
                for param_type in type_annotation.params
            ]
            for param_type in param_types:
                if param_type is None:
                    # if somehting went wrong we return None
                    # the attempt to convert the parameter type will have added an error
                    return None
            # please the type checker
            param_types = [t for t in param_types if t is not None]
            # we convert the return type
            ret_type = self.convert_type_annotation_top_level(
                type_annotation.ret_type, decl_line, decl_id
            )
            if ret_type is None:
                return None
            # we return the function type
            return FunctionType({}, param_types, ret_type)
        elif isinstance(type_annotation, GenericTypeAnnotation):
            # we treat the name of the generic type as a NamedTypeAnnotation
            existing_type = self.convert_type_annotation_top_level(
                NamedTypeAnnotation(type_annotation.name, decl_line), decl_line, decl_id
            )
            if existing_type is None:
                return None  # the attempt to convert the type annotation will have added an error
            # make sure the type is a struct or enum that takes generic parameters
            if not (
                isinstance(existing_type, StructType)
                or isinstance(existing_type, EnumType)
            ):
                self.errors.append(
                    TypeInferenceError(
                        f"Type {type_annotation.name} is not a struct or enum cannot take generic parameters",
                        decl_line,
                        decl_id,
                    )
                )
                return None
            type_args: List[Type] = []
            for type_arg in type_annotation.type_args:
                type_arg_type = self.convert_type_annotation_top_level(
                    type_arg, decl_line, decl_id
                )
                if type_arg_type is None:
                    return None  # the attempt to convert the type argument will have added an error
                type_args.append(type_arg_type)
            # we now have to check the arity of the generic type
            if len(type_args) != len(existing_type.type_vars):
                self.errors.append(
                    TypeInferenceError(
                        f"Generic type {type_annotation.name} expects {len(existing_type.type_vars)} parameters but got {len(type_args)}",
                        decl_line,
                        decl_id,
                    )
                )
                return None
            return GenericType(existing_type, type_args)
        else:
            raise RuntimeError(f"Unknown type annotation {type_annotation}")

    def run(self) -> None:
        """
        Executes the type resolution pass for the program.
        This pass first collects and registers all top-level type declarations (aliases, enums, structs, traits)
        into the type environment, ensuring that all types are available for later resolution.
        Then, it processes function and implementation declarations to resolve their types and attach them
        to AST nodes, preparing the program for type inference in subsequent passes.
        Side effects:
            - Populates the type environment with all type definitions.
            - Attaches types or type variables to relevant AST nodes.
            - Accumulates errors for unresolved or invalid types.
        """
        # First, iterate through all top-level declarations to register types.
        for declaration in self.program.declarations:
            self.visit_type_decl(declaration)

        # Next, process functions and implementations to resolve types for their components.
        for declaration in self.program.declarations:
            if isinstance(declaration, FnDecl):
                self.visit_fn_decl(declaration)
            elif isinstance(declaration, ImplDecl):
                self.visit_impl_decl(declaration)

    def visit_type_decl(self, type_decl: Declaration) -> None:
        """
        Dispatches a top-level type declaration to the appropriate handler.
        Supported declarations: TypeAliasDecl, EnumDecl, StructDecl, TraitDecl.
        Ignores other declaration types.
        Args:
            type_decl (Declaration): The top-level declaration node to process.
        Side effects:
            - Registers the type in the type environment, if applicable.
            - May recursively resolve referenced types.
        """
        if isinstance(type_decl, TypeAliasDecl):
            self.visit_type_alias_decl(type_decl)
        elif isinstance(type_decl, EnumDecl):
            self.visit_enum_decl(type_decl)
        elif isinstance(type_decl, StructDecl):
            self.visit_struct_decl(type_decl)
        elif isinstance(type_decl, TraitDecl):
            self.visit_trait_decl(type_decl)
        else:
            pass  # just ignore other declarations

    def resolve_trait_bound(
        self,
        bound: Union[NamedTypeAnnotation, GenericTypeAnnotation],
        decl_line: int,
        decl_id: int,
    ) -> Optional[TraitBound]:
        bound_trait = self.type_env.get_trait(bound.name)
        if bound_trait is None:
            # look the bound up in the global scope
            trait_symbol = self.symbol_table.lookup_global(bound.name)
            if trait_symbol is None:
                self.errors.append(
                    TypeInferenceError(
                        f"Undefined trait {bound.name}",
                        decl_line,
                        decl_id,
                    )
                )
                return None
            # get the ast node of the trait declaration
            trait_decl_node = self.program.get_node(trait_symbol.ast_id)
            if trait_decl_node is None:
                raise RuntimeError("Cannot find node for trait declaration")
            if not isinstance(trait_decl_node, TraitDecl):
                self.errors.append(
                    TypeInferenceError(
                        f"Trait {bound.name} is not a trait",
                        decl_line,
                        decl_id,
                    )
                )
                return None
            # run visit_trait_decl on it
            self.visit_trait_decl(trait_decl_node)
            bound_trait = self.type_env.get_trait(bound.name)
            if bound_trait is None:
                self.errors.append(
                    TypeInferenceError(
                        f"Trait {bound.name} cannot be resolved",
                        decl_line,
                        decl_id,
                    )
                )
                return None
        type_args: List[Type] = []
        if isinstance(bound, GenericTypeAnnotation):
            for type_arg in bound.type_args:
                type_arg_type = self.convert_type_annotation_top_level(
                    type_arg, decl_line, decl_id
                )
                if type_arg_type is None:
                    return None  # error already appended
                type_args.append(type_arg_type)
        return TraitBound(bound.name, type_args)

    def resolve_type_var(
        self,
        annotation: TypeAnnotation,
        type_vars: Dict[str, TypeVar],
        decl_line: int,
        decl_id: int,
    ) -> Optional[Type]:
        """This function attempts to resolve a type into a TypeVar from its local scope and if it passes the type to convert_type_annotation_top_level

        Args:
            annotation (TypeAnnotation): The type annotation to resolve
            type_vars (Dict[str, TypeVar]): The type vars in the local scope
            decl_line (int): The line number of the declaration
            decl_id (int): The declaration id

        Returns:
            Optional[Type]: The resolved type or None if it is not a type var and cannot be resolved by convert_type_annotation_top_level
        """
        if isinstance(annotation, NamedTypeAnnotation):
            return type_vars.get(annotation.name)
        else:
            return self.convert_type_annotation_top_level(
                annotation, decl_line, decl_id
            )

    def instantiate_type_vars(
        self,
        type_params: Optional[List[TypeParam]],
        decl_name: str,
        decl_line: int,
        decl_id: int,
    ) -> Optional[Dict[str, TypeVar]]:
        """This function builds a dict of type vars from a list of type params

        Args:
            type_params (List[TypeParam]): The type params to instantiate
            decl_name (str): The name of the declaration
            decl_line (int): The line number of the declaration
            decl_id (int): The declaration id

        Returns:
            Optional[Dict[str, TypeVar]]: A dict of type vars with the type param name as the key or None if an error occurs
        """
        type_vars: Dict[str, TypeVar] = {}
        if type_params is not None:
            for type_param in type_params:
                type_var = self.visit_type_param(type_param)
                if type_var is None:
                    return None  # the attempt to instantiate the type var will have added an error
                if type_var.name in type_vars:
                    self.errors.append(
                        TypeInferenceError(
                            f"{decl_name} has multiple type params with the same name {type_var.name}",
                            decl_line,
                            decl_id,
                        )
                    )
                    return None
                type_vars[type_var.name] = type_var
        return type_vars

    def visit_type_param(self, type_param: TypeParam) -> Optional[TypeVar]:
        """This function visits a type param and instantiates a TypeVar from it

        Args:
            type_param (TypeParam): The type param to visit

        Returns:
            Optional[TypeVar]: The instantiated type var or None if it is not a type var and cannot be resolved by resolve_type_var
        """
        # we need to instantiate the type var from the type param
        type_var = TypeVar(type_param.name, {})
        # we need to instantiate the trait bounds
        trait_bounds: Dict[str, TraitBound] = {}
        if type_param.bounds is not None:
            for bound in type_param.bounds:
                resolved_bound = self.resolve_trait_bound(
                    bound, type_param.line, type_param.id
                )
                if resolved_bound is not None:
                    trait_bounds[bound.name] = resolved_bound
                else:
                    return None  # the attempt to resolve the trait bound will have added an error
        type_var.bounds = trait_bounds
        return type_var

    def resolve_field_annotations(
        self,
        fields: Union[List[StructField], List[EnumStructField]],
        type_vars: Dict[str, TypeVar],
        decl_name: str,
        decl_line: int,
        decl_id: int,
    ) -> Optional[Dict[str, TypeAnnotation]]:
        """This function resolves the type annotations of the fields of a struct or enum

        Args:
            fields (Union[List[StructField], List[EnumStructField]]): The fields to resolve the type annotations of
            type_vars (Dict[str, TypeVar]): The type vars in the local scope

        Returns:
            Optional[Dict[str, TypeAnnotation]]: A dict of field names and their resolved type annotations or None if an error occurs
        """
        field_types: Dict[str, TypeAnnotation] = {}
        for field in fields:
            field_type = self.resolve_type_var(
                field.type_annotation, type_vars, decl_line, decl_id
            )
            if field_type is None:
                return None  # the attempt to resolve the field type will have added an error
            if field.name in field_types:
                self.errors.append(
                    TypeInferenceError(
                        f"Struct {decl_name} has multiple fields with the same name {field.name}",
                        decl_line,
                        decl_id,
                    )
                )
        return field_types

    def visit_trait_decl(self, trait_decl: TraitDecl) -> None:
        """
        Processes a trait declaration, resolving its type parameters and trait bounds,
        and registers it in the type environment. Enters the trait's scope to process
        method signatures.
        Args:
            trait_decl (TraitDecl): The trait declaration node.
        Side effects:
            - Adds the trait and its type vars/bounds to the type environment.
            - Enters/exits the trait's symbol table scope.
            - Accumulates errors for duplicate bounds or type param issues.
        """
        # make sure we have not already visited this trait
        if trait_decl.id in self.visited_traits:
            return
        # mark as being visited
        self.visited_traits.add(trait_decl.id)
        # we create the trait
        trait = Trait(trait_decl.name)
        # we add the trait to the type env
        self.type_env.add_trait(trait_decl.name, trait)
        # instantiate the type vars from the type params
        type_vars = self.instantiate_type_vars(
            trait_decl.type_params, trait_decl.name, trait_decl.line, trait_decl.id
        )
        if type_vars is None:
            return  # error already recorded
        # add type vars to trait
        trait.type_vars = type_vars
        # instantiate trait bounds
        trait_bounds: Dict[str, TraitBound] = {}
        # resolve and check trait bounds
        if trait_decl.bounds is not None:
            for bound in trait_decl.bounds:
                resolved_bound = self.resolve_trait_bound(
                    bound, trait_decl.line, trait_decl.id
                )
                if resolved_bound is not None:
                    if resolved_bound.name in trait_bounds:
                        self.errors.append(
                            TypeInferenceError(
                                f"Trait {trait_decl.name} has multiple bounds with the same name {resolved_bound.name}",
                                trait_decl.line,
                                trait_decl.id,
                            )
                        )
                        return
                    trait_bounds[resolved_bound.name] = resolved_bound
        trait.bounds = trait_bounds

        # Enter trait scope and process each method signature.
        self.symbol_table.enter_scope(trait_decl.id)
        for method in trait_decl.methods:
            self.visit_trait_method(method, trait)
        self.symbol_table.exit_scope()

    def visit_trait_method(
        self, method: Union[FnDecl, PartialTraitMethod], trait: Trait
    ) -> None:
        """
        Handles trait method declarations within a trait.
        This is a stub for handling trait methods; actual implementation should
        resolve method signatures and attach them to the trait as needed.
        Args:
            method (FnDecl | PartialTraitMethod): The method node within the trait.
            trait (Trait): The trait object being built.
        Raises:
            NotImplementedError: Always, as trait method handling is not yet implemented.
        """
        # TODO: add trait method handling
        raise NotImplementedError("Trait method handling not implemented")

    def visit_type_alias_decl(self, type_alias_decl: TypeAliasDecl) -> None:
        """
        Resolves a type alias declaration and registers it in the type environment.
        Protects against recursive type aliases by tracking visitation.
        Args:
            type_alias_decl (TypeAliasDecl): The type alias declaration node.
        Side effects:
            - Adds the alias to the type environment.
            - Accumulates errors for recursion or invalid types.
        """
        if type_alias_decl.id in self.visited_type_aliases:
            return
        self.visited_type_aliases.add(type_alias_decl.id)
        # get the name of the type alias
        type_alias_name = type_alias_decl.name
        # instantiate the type vars from the type params
        type_vars = self.instantiate_type_vars(
            type_alias_decl.type_params, type_alias_name, type_alias_decl.line, type_alias_decl.id
        )
        if type_vars is None:
            return  # error already recorded
        # resolve the type annotation
        type_ = self.resolve_type_var(
            type_alias_decl.type_annotation, type_vars, type_alias_decl.line, type_alias_decl.id
        )
        if type_ is None:
            return  # error already recorded
        # create the type alias
        type_alias = TypeAlias(type_alias_name, type_vars, type_, type_alias_decl.assert_symbol())
        # now make sure there is not a type alias cycle and that no other type holds the name
        if self.type_env.find_type(type_alias_name) is not None:
            self.errors.append(
                TypeInferenceError(
                    f"Type alias {type_alias_name} using name of existing type",
                    type_alias_decl.line,
                    type_alias_decl.id
                )
            )
            return
        # check for type alias cycles
        if self.type_env.detect_cycle(type_alias_name, type_):
            self.errors.append(
                TypeInferenceError(
                    f"Type alias {type_alias_name} has a cycle",
                    type_alias_decl.line,
                    type_alias_decl.id
                )
            )
        # add the type alias to the type env
        self.type_env.add_type_alias(type_alias)

    def visit_enum_decl(self, enum_decl: EnumDecl) -> None:
        """
        Processes an enum declaration, resolves its type parameters and each variant's type,
        and registers the enum in the type environment. Protects against repeated visits.
        Args:
            enum_decl (EnumDecl): The enum declaration node.
        Side effects:
            - Adds the enum and its instantiated variants to the type environment.
            - Accumulates errors for invalid types or duplicate variants.
        """
        if enum_decl.id in self.visited_enums:
            return
        self.visited_enums.add(enum_decl.id)
        # Create and register the enum type.
        enum_type = EnumType(enum_decl.name, {}, [])
        self.type_env.add_type(enum_decl.name, enum_type)
        # Instantiate type variables from type parameters.
        type_vars: Dict[str, TypeVar] = self.instantiate_type_vars(
            enum_decl.type_params, enum_decl.name, enum_decl.line, enum_decl.id
        )
        if type_vars is None:
            return
        enum_type.type_vars = type_vars
        # Resolve and register all enum variants.
        variants: Dict[str, EnumVariantType] = {}
        for variant in enum_decl.variants:
            if isinstance(variant, EnumUnitVariant):
                variants[variant.name] = EnumUnitVariantType(variant.name)
            elif isinstance(variant, EnumTupleVariant):
                tuple_types: list[Type] = []
                for elem_type in variant.types:
                    elem_type = self.resolve_type_var(
                        elem_type, type_vars, variant.line, variant.id
                    )
                    if elem_type is None:
                        return
                    tuple_types.append(elem_type)
                variants[variant.name] = EnumTupleVariantType(variant.name, tuple_types)
            elif isinstance(variant, EnumStructVariant):
                field_types: Dict[str, Type] = self.resolve_field_annotations(
                    variant.fields,
                    type_vars,
                    enum_decl.name,
                    enum_decl.line,
                    enum_decl.id,
                )
                if field_types is None:
                    return
                variants[variant.name] = EnumStructVariantType(
                    variant.name, field_types
                )
            else:
                raise RuntimeError(f"Unknown enum variant {variant}")
        enum_type.variants = variants
        self.type_env.add_type(enum_decl.name, enum_type)

    def visit_struct_decl(self, struct_decl: StructDecl) -> None:
        """
        Processes a struct declaration, resolves its type parameters and all field types,
        and registers the struct in the type environment. Supports recursive struct types.
        Args:
            struct_decl (StructDecl): The struct declaration node.
        Side effects:
            - Adds the struct and its resolved fields to the type environment.
            - Accumulates errors for invalid field types or type parameter issues.
        """
        if struct_decl.id in self.visited_structs:
            return
        struct_type = StructType(struct_decl.name, {}, {})
        self.type_env.add_type(struct_decl.name, struct_type)
        self.visited_structs.add(struct_decl.id)
        # Instantiate type variables from type parameters.
        type_vars: Dict[str, TypeVar] = self.instantiate_type_vars(
            struct_decl.type_params, struct_decl.name, struct_decl.line, struct_decl.id
        )
        if type_vars is None:
            return
        struct_type.type_vars = type_vars
        # Resolve all struct field types.
        field_types: Dict[str, Type] = self.resolve_field_annotations(
            struct_decl.fields,
            type_vars,
            struct_decl.name,
            struct_decl.line,
            struct_decl.id,
        )
        if field_types is None:
            return
        struct_type.fields = field_types
        # This supports recursive struct definitions.

    def visit_fn_decl(self, fn_decl: FnDecl) -> None:
        """
        Processes a standalone function declaration (not a method), resolving its type parameters,
        parameter types, and return type, and attaches the resulting type to the function's symbol.
        Enters the function's scope to process its body statements.
        Args:
            fn_decl (FnDecl): The function declaration node.
        Side effects:
            - Attaches a FunctionType to the function's symbol.
            - Assigns types to parameter symbols.
            - Enters/exits the function's symbol table scope.
            - Accumulates errors for invalid types or missing symbols.
        """
        type_vars: Dict[str, TypeVar] = self.instantiate_type_vars(
            fn_decl.type_params, fn_decl.name, fn_decl.line, fn_decl.id
        )
        if type_vars is None:
            return
        param_types: list[Type] = []
        for param in fn_decl.params:
            param_type = self.convert_type_annotation_top_level(
                param.type_annotation, param.line, param.id
            )
            if param_type is None:
                return
            param_types.append(param_type)
            # Attach type to parameter symbol.
            if param.symbol is None:  # this should never happen
                raise RuntimeError("Parameter has no symbol")
            param.symbol.type = param_type
        ret_type = self.convert_type_annotation_top_level(
            fn_decl.ret_type, fn_decl.line, fn_decl.id
        )
        if ret_type is None:
            return
        fn_type = FunctionType(type_vars, param_types, ret_type)
        fn_decl.assert_symbol().type = fn_type
        # Enter function scope and process body statements.
        self.symbol_table.enter_scope(fn_decl.id)
        for statement in fn_decl.body:
            self.visit_statement(statement)
        self.symbol_table.exit_scope()

    def visit_impl_decl(self, impl_decl: ImplDecl) -> None:
        # TODO: add impl type and impls: Dict[Type, List[Impl]] to the type env and rewrite this method
        impl_type = self.type_env.get_type(impl_decl.name)
        if impl_type is None:
            self.errors.append(
                TypeInferenceError(
                    f"Type {impl_decl.name} is not defined",
                    impl_decl.line,
                    impl_decl.id,
                )
            )
            return
        elif not isinstance(impl_type, (StructType, EnumType)):
            self.errors.append(
                TypeInferenceError(
                    f"Type {impl_decl.name} is not a struct or enum cannot implement methods",
                    impl_decl.line,
                    impl_decl.id,
                )
            )
            return
        # now we need to visit the methods
        for method in impl_decl.methods:
            self.visit_method_decl(method, impl_type)

    def visit_method_decl(
        self, method_decl: FnDecl, impl_type: Union[StructType, EnumType]
    ) -> None:
        """
        Processes a method declaration within an impl block, resolving its type parameters,
        parameter types, and return type, and attaches the resulting type to the method's symbol.
        Adds the method to the implementation type's method map.
        Differs from visit_fn_decl in that it uses resolve_type_var for parameters (to support type vars).
        Enters the method's scope to process its body statements.
        Args:
            method_decl (FnDecl): The method declaration node.
            impl_type (StructType | EnumType): The type being implemented.
        Side effects:
            - Attaches a FunctionType to the method's symbol.
            - Registers the method in the impl type's method dictionary.
            - Assigns types to parameter symbols.
            - Enters/exits the method's symbol table scope.
            - Accumulates errors for duplicate methods or invalid types.
        """
        type_vars: Dict[str, TypeVar] = self.instantiate_type_vars(
            method_decl.type_params, method_decl.name, method_decl.line, method_decl.id
        )
        if type_vars is None:
            return
        param_types: list[Type] = []
        for param in method_decl.params:
            param_type = self.resolve_type_var(
                param.type_annotation, type_vars, param.line, param.id
            )
            if param_type is None:
                return
            param_types.append(param_type)
            param.assert_symbol().type = param_type
        ret_type = self.convert_type_annotation_top_level(
            method_decl.ret_type, method_decl.line, method_decl.id
        )
        if ret_type is None:
            return
        method_type = FunctionType(type_vars, param_types, ret_type)
        method_decl.assert_symbol().type = method_type
        # Prevent duplicate method names in the impl type.
        if method_decl.name in impl_type.methods:
            self.errors.append(
                TypeInferenceError(
                    f"Method {method_decl.name} already exists in impl type {impl_type.name}",
                    method_decl.line,
                    method_decl.id,
                )
            )
            return
        impl_type.methods[method_decl.name] = method_decl.assert_symbol()
        # Enter method scope and process body statements.
        self.symbol_table.enter_scope(method_decl.id)
        for statement in method_decl.body:
            self.visit_statement(statement)
        self.symbol_table.exit_scope()

    def visit_statement(self, statement: Statement) -> None:
        """
        Processes a statement node, dispatching to the appropriate handler.
        Only variable declarations, functions, and statements with bodies are processed.
        Args:
            statement (Statement): The statement AST node.
        Side effects:
            - May assign types or type holes to variable symbols.
            - May process nested statements within blocks.
        """
        if isinstance(statement, VarDecl):
            self.visit_var_decl(statement)
        elif isinstance(statement, FnDecl):
            self.visit_fn_decl(statement)
        elif isinstance(statement, If):
            self.visit_if_stmt(statement)
        elif isinstance(statement, Else):
            self.visit_else_stmt(statement)
        elif isinstance(statement, While):
            self.visit_while_stmt(statement)
        elif isinstance(statement, Loop):
            self.visit_loop_stmt(statement)

    def visit_var_decl(self, var_decl: VarDecl) -> None:
        """
        Processes a variable declaration. If a type annotation is present, resolves it
        and attaches it to the variable's symbol; otherwise, assigns a type hole for inference.
        Args:
            var_decl (VarDecl): The variable declaration node.
        Side effects:
            - Assigns a resolved type or a type hole to the variable's symbol.
            - Accumulates errors for invalid type annotations.
        """
        if var_decl.type_annotation is not None:
            type_annotation = self.convert_type_annotation_top_level(
                var_decl.type_annotation, var_decl.line, var_decl.id
            )
            if type_annotation is None:
                return
            var_decl.assert_symbol().type = type_annotation
        else:
            # No annotation: insert a type hole for later inference.
            var_decl.assert_symbol().type = TypeHole()

    def visit_if_stmt(self, if_stmt: If) -> None:
        """
        Processes an if statement, entering its scope and processing its body.
        If an else body exists, it is processed as well.
        Args:
            if_stmt (If): The if statement node.
        Side effects:
            - Enters/exits the if's symbol table scope.
            - Processes nested statements in the if and else bodies.
        """
        self.visit_block_with_scope(if_stmt.id, if_stmt.body)
        if if_stmt.else_body is not None:
            self.visit_else_stmt(if_stmt.else_body)

    def visit_else_stmt(self, else_stmt: Else) -> None:
        """
        Processes an else statement, entering its scope and processing its body.
        Args:
            else_stmt (Else): The else statement node.
        Side effects:
            - Enters/exits the else's symbol table scope.
            - Processes nested statements in the else body.
        """
        self.visit_block_with_scope(else_stmt.id, else_stmt.body)

    def visit_while_stmt(self, while_stmt: While) -> None:
        """
        Processes a while loop, entering its scope and processing its body.
        Args:
            while_stmt (While): The while statement node.
        Side effects:
            - Enters/exits the while's symbol table scope.
            - Processes nested statements in the while body.
        """
        self.visit_block_with_scope(while_stmt.id, while_stmt.body)

    def visit_loop_stmt(self, loop_stmt: Loop) -> None:
        """
        Processes a loop statement, entering its scope and processing its body.
        Args:
            loop_stmt (Loop): The loop statement node.
        Side effects:
            - Enters/exits the loop's symbol table scope.
            - Processes nested statements in the loop body.
        """
        self.visit_block_with_scope(loop_stmt.id, loop_stmt.body)

    def visit_block_with_scope(self, block_id: int, body: List[Statement]) -> None:
        """
        Utility method to enter a new symbol table scope, visit a list of statements,
        and then exit the scope. Used for block-based statements such as if, else,
        while, and loop.
        Args:
            block_id (int): The unique ID of the block, used for scoping.
            body (List[Statement]): The list of statements within the block.
        Side effects:
            - Enters and exits a symbol table scope.
            - Visits each statement in the block.
        """
        self.symbol_table.enter_scope(block_id)
        for statement in body:
            self.visit_statement(statement)
        self.symbol_table.exit_scope()
