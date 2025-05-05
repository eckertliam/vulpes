from typing import Dict, Optional, Set, Union

from ..errors import TypeInferenceError
from .name_ref_pass import NameReferencePass
from .base_pass import Pass
from ..ast import (
    ArrayTypeAnnotation,
    Else,
    EnumDecl,
    EnumStructVariant,
    EnumTupleVariant,
    EnumUnitVariant,
    FnDecl,
    FunctionTypeAnnotation,
    If,
    ImplDecl,
    Loop,
    NamedTypeAnnotation,
    Statement,
    StructDecl,
    TraitDecl,
    TupleTypeAnnotation,
    TypeAliasDecl,
    TypeAnnotation,
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
    StructType,
    TupleType,
    Type,
    TypeVar,
)


# This pass adds type definitions to the type env
# it then attaches types to ast nodes that are typed
# it adds type vars to ast nodes that will need to be inferred in the next pass
class TypeResolutionPass(Pass):
    def __init__(self, previous_pass: NameReferencePass):
        super().__init__(previous_pass=previous_pass)
        # we need to keep track of the type aliases, enums, and structs
        # we sometimes need to jump around the ast to add types to the type env
        # so we need to keep track of what we have already visited
        self.visited_type_aliases: Set[int] = set()
        self.visited_enums: Set[int] = set()
        self.visited_structs: Set[int] = set()

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
            return FunctionType(param_types, ret_type)
        else:
            raise RuntimeError(f"Unknown type annotation {type_annotation}")

    def run(self) -> None:
        # first we again need to iterate through all top level declarations
        # it is important that we add all aliases, enums, and structs to the type env
        # before we do any type resolution
        for declaration in self.program.declarations:
            self.visit_type_decl(declaration)

        # now we can go through the function and impl declarations
        # and add types to the ast nodes that need them
        for declaration in self.program.declarations:
            if isinstance(declaration, FnDecl):
                self.visit_fn_decl(declaration)
            elif isinstance(declaration, ImplDecl):
                self.visit_impl_decl(declaration)

    def visit_type_decl(
        self, type_decl: Union[TypeAliasDecl, EnumDecl, StructDecl, TraitDecl]
    ) -> None:
        if isinstance(type_decl, TypeAliasDecl):
            self.visit_type_alias_decl(type_decl)
        elif isinstance(type_decl, EnumDecl):
            self.visit_enum_decl(type_decl)
        elif isinstance(type_decl, StructDecl):
            self.visit_struct_decl(type_decl)
        elif isinstance(type_decl, TraitDecl):
            self.visit_trait_decl(type_decl)

    def visit_trait_decl(self, trait_decl: TraitDecl) -> None:
        # TODO: implement trait_decl
        # NOTE: we need to handle params with the Self type
        raise NotImplementedError("TraitDecl not implemented in type_res_pass")

    def visit_type_alias_decl(self, type_alias_decl: TypeAliasDecl) -> None:
        # check if this alias is already being visited (i.e. recursion)
        if type_alias_decl.id in self.visited_type_aliases:
            self.errors.append(
                TypeInferenceError(
                    f"Recursive type alias detected for {type_alias_decl.name}",
                    type_alias_decl.line,
                    type_alias_decl.id,
                )
            )
            return
        # mark as being visited
        self.visited_type_aliases.add(type_alias_decl.id)
        # we convert the type annotation
        type_annotation = self.convert_type_annotation_top_level(
            type_alias_decl.type_annotation, type_alias_decl.line, type_alias_decl.id
        )
        if type_annotation is None:
            # the attempt to convert the type annotation will have added an error
            self.visited_type_aliases.remove(type_alias_decl.id)
            return None
        # we add the type to the type env
        self.type_env.add_type(type_alias_decl.name, type_annotation)
        # remove the alias ID from the visited set
        self.visited_type_aliases.remove(type_alias_decl.id)

    def visit_enum_decl(self, enum_decl: EnumDecl) -> None:
        # make sure we have not already visited this enum
        if enum_decl.id in self.visited_enums:
            return
        # mark as being visited
        self.visited_enums.add(enum_decl.id)
        # we create the enum type
        enum_type = EnumType(enum_decl.name, [])
        # and add it to the type env
        self.type_env.add_type(enum_decl.name, enum_type)
        # we add the enum to the visited set
        self.visited_enums.add(enum_decl.id)
        # we need to convert the enum variants
        variants: Dict[str, EnumVariantType] = {}
        for variant in enum_decl.variants:
            if isinstance(variant, EnumUnitVariant):
                variants[variant.name] = EnumUnitVariantType(variant.name)
            elif isinstance(variant, EnumTupleVariant):
                tuple_types: list[Type] = []
                for elem_type in variant.types:
                    elem_type = self.convert_type_annotation_top_level(
                        elem_type, variant.line, variant.id
                    )
                    if elem_type is None:
                        return
                    tuple_types.append(elem_type)
                variants[variant.name] = EnumTupleVariantType(variant.name, tuple_types)
            elif isinstance(variant, EnumStructVariant):
                field_types: Dict[str, Type] = {}
                for field in variant.fields:
                    field_type = self.convert_type_annotation_top_level(
                        field.type_annotation, variant.line, variant.id
                    )
                    if field_type is None:
                        return
                    field_types[field.name] = field_type
                variants[variant.name] = EnumStructVariantType(
                    variant.name, field_types
                )
            else:
                raise RuntimeError(f"Unknown enum variant {variant}")
        # now we set the variants on the enum type
        enum_type.variants = variants
        # and add it to the type env
        self.type_env.add_type(enum_decl.name, enum_type)

    def visit_struct_decl(self, struct_decl: StructDecl) -> None:
        # make sure we have not already visited this struct
        if struct_decl.id in self.visited_structs:
            return
        # we create the struct type
        struct_type = StructType(struct_decl.name, {})
        # and add it to the type env
        self.type_env.add_type(struct_decl.name, struct_type)
        # we add the struct to the visited set
        self.visited_structs.add(struct_decl.id)

        # we convert the struct fields
        field_types: Dict[str, Type] = {}
        for field in struct_decl.fields:
            field_type = self.convert_type_annotation_top_level(
                field.type_annotation, field.line, field.id
            )
            if field_type is None:
                # the attempt to convert the field type will have added an error
                return
            field_types[field.name] = field_type
        # now we set the fields on the struct type
        struct_type.fields = field_types
        # this allows recursive structs

    def visit_fn_decl(self, fn_decl: FnDecl) -> None:
        # first we get the function's type signature
        # we go through the params and convert them to a list of types
        param_types: list[Type] = []
        for param in fn_decl.params:
            param_type = self.convert_type_annotation_top_level(
                param.type_annotation, param.line, param.id
            )
            if param_type is None:
                # the attempt to convert the parameter type will have added an error
                return
            param_types.append(param_type)
            # add the param_type to the param's symbol
            if param.symbol is None:  # this should never happen
                raise RuntimeError("Parameter has no symbol")
            param.symbol.type = param_type
        # we convert the return type
        ret_type = self.convert_type_annotation_top_level(
            fn_decl.ret_type, fn_decl.line, fn_decl.id
        )
        if ret_type is None:
            # the attempt to convert the return type will have added an error
            return
        fn_type = FunctionType(param_types, ret_type)
        # add the function type to the function's symbol
        if fn_decl.symbol is None:  # this should never happen
            raise RuntimeError("Function declaration has no symbol")
        fn_decl.symbol.type = fn_type
        # now we enter the fn's scope
        self.symbol_table.enter_scope(fn_decl.id)
        # now we visit the body
        for statement in fn_decl.body:
            self.visit_statement(statement)
        # now we exit the fn's scope
        self.symbol_table.exit_scope()

    def visit_impl_decl(self, impl_decl: ImplDecl) -> None:
        # TODO: add trait handling we need to get the trait from the type env and validate that the impl is implementing all the methods required by the trait and also that the impl is not implementing any methods that are not required by the trait
        # we need to get the type the impl is implementing
        # we do this by looking up the type in the type env
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
        # like functions we need to get the method's type signature
        # we go through the params and convert them to a list of types
        param_types: list[Type] = []
        for param in method_decl.params:
            param_type = self.convert_type_annotation_top_level(
                param.type_annotation, param.line, param.id
            )
            if param_type is None:
                # the attempt to convert the parameter type will have added an error
                return
            param_types.append(param_type)
            # add the param_type to the param's symbol
            if param.symbol is None:  # this should never happen
                raise RuntimeError("Parameter has no symbol")
            param.symbol.type = param_type
        # we convert the return type
        ret_type = self.convert_type_annotation_top_level(
            method_decl.ret_type, method_decl.line, method_decl.id
        )
        if ret_type is None:
            # the attempt to convert the return type will have added an error
            return
        method_type = FunctionType(param_types, ret_type)
        # add the method type to the method's symbol
        if method_decl.symbol is None:  # this should never happen
            raise RuntimeError("Method declaration has no symbol")
        method_decl.symbol.type = method_type
        # make sure the impl type doesnt already have a method with this name
        if method_decl.name in impl_type.methods:
            self.errors.append(
                TypeInferenceError(
                    f"Method {method_decl.name} already exists in impl type {impl_type.name}",
                    method_decl.line,
                    method_decl.id,
                )
            )
            return
        # add the method's symbol to the impl type
        impl_type.methods[method_decl.name] = method_decl.symbol
        # now we enter the method's scope
        self.symbol_table.enter_scope(method_decl.id)
        # now we visit the body
        for statement in method_decl.body:
            self.visit_statement(statement)
        # now we exit the method's scope
        self.symbol_table.exit_scope()

    def visit_statement(self, statement: Statement) -> None:
        # we only care about var decls and statements with bodies
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
        # if the var has a type annotation we need to convert it
        if var_decl.type_annotation is not None:
            type_annotation = self.convert_type_annotation_top_level(
                var_decl.type_annotation, var_decl.line, var_decl.id
            )
            if type_annotation is None:
                # the attempt to convert the type annotation will have added an error
                return
            # we add the type to the var's symbol
            if var_decl.symbol is None:  # this should never happen
                raise RuntimeError("Variable declaration has no symbol")
            var_decl.symbol.type = type_annotation
        else:  # the var has no type annotation so we need to infer it
            # for now we just add a type var which lets the next pass know this var needs to be inferred
            if var_decl.symbol is None:  # this should never happen
                raise RuntimeError("Variable declaration has no symbol")
            var_decl.symbol.type = TypeVar()

    def visit_if_stmt(self, if_stmt: If) -> None:
        # we need to enter the if's scope
        self.symbol_table.enter_scope(if_stmt.id)
        # we visit the body
        for statement in if_stmt.body:
            self.visit_statement(statement)
        # we exit the if's scope
        self.symbol_table.exit_scope()
        # we visit the else body if it exists
        if if_stmt.else_body is not None:
            self.visit_else_stmt(if_stmt.else_body)

    def visit_else_stmt(self, else_stmt: Else) -> None:
        # we need to enter the else's scope
        self.symbol_table.enter_scope(else_stmt.id)
        # we visit the body
        for statement in else_stmt.body:
            self.visit_statement(statement)
        # we exit the else's scope
        self.symbol_table.exit_scope()

    def visit_while_stmt(self, while_stmt: While) -> None:
        # we need to enter the while's scope
        self.symbol_table.enter_scope(while_stmt.id)
        # we visit the body
        for statement in while_stmt.body:
            self.visit_statement(statement)
        # we exit the while's scope
        self.symbol_table.exit_scope()

    def visit_loop_stmt(self, loop_stmt: Loop) -> None:
        # we need to enter the loop's scope
        self.symbol_table.enter_scope(loop_stmt.id)
        # we visit the body
        for statement in loop_stmt.body:
            self.visit_statement(statement)
        # we exit the loop's scope
        self.symbol_table.exit_scope()
