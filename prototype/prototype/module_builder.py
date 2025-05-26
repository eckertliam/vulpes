"""
This module provides builder classes for constructing AST nodes for modules, functions,
structs, unions, and type aliases in a program. These builder classes allow for
incremental and chainable construction of complex AST structures, which is useful
for programmatically generating code or during parsing.
"""

from typing import Set
from prototype.ast import (
    Module,
    TypeAnnotation,
    FnDecl,
    StructDecl,
    UnionDecl,
    TypeAliasDecl,
    Import,
    ExportSpec,
    Statement,
    StructField,
    UnionStructVariant,
    UnionTupleVariant,
    UnionTagVariant,
    TypeParam,
    Param,
)


class ModuleBuilder:
    """
    Builder for constructing a Module AST node and its top-level declarations.
    """

    def __init__(self, file_name: str):
        """
        Initialize the ModuleBuilder.

        Args:
            file_name (str): The file name for the module.
        """
        self.module: Module = Module(file_name)

    def build(self) -> Module:
        """
        Finalize the module and return it.
        Returns:
            Module: The constructed module.
        """
        return self.module

    def build_fn_decl(self, name: str) -> "FnDeclBuilder":
        """
        Begin building a function declaration and add it to the module.

        Args:
            name (str): The name of the function.
        Returns:
            FnDeclBuilder: Builder to further construct the function declaration.
        """
        fn_decl = FnDecl(name, [], [], TypeAnnotation(0), [], 0)
        self.module.top_level_nodes.append(fn_decl)
        return FnDeclBuilder(fn_decl, self)

    def build_struct_decl(self, name: str) -> "StructDeclBuilder":
        """
        Begin building a struct declaration and add it to the module.

        Args:
            name (str): The name of the struct.
        Returns:
            StructDeclBuilder: Builder to further construct the struct declaration.
        """
        struct_decl = StructDecl(name, [], [], 0)
        self.module.top_level_nodes.append(struct_decl)
        return StructDeclBuilder(struct_decl, self)

    def build_union_decl(self, name: str) -> "UnionDeclBuilder":
        """
        Begin building a union declaration and add it to the module.

        Args:
            name (str): The name of the union.
        Returns:
            UnionDeclBuilder: Builder to further construct the union declaration.
        """
        union_decl = UnionDecl(name, [], [], 0)
        self.module.top_level_nodes.append(union_decl)
        return UnionDeclBuilder(union_decl, self)

    def build_type_alias_decl(self, name: str) -> "TypeAliasDeclBuilder":
        """
        Begin building a type alias declaration and add it to the module.

        Args:
            name (str): The name of the type alias.
        Returns:
            TypeAliasDeclBuilder: Builder to further construct the type alias declaration.
        """
        type_alias_decl = TypeAliasDecl(name, [], TypeAnnotation(0), 0)
        self.module.top_level_nodes.append(type_alias_decl)
        return TypeAliasDeclBuilder(type_alias_decl, self)

    def add_import(self, module: str, targets: Set[str] = set()) -> "ModuleBuilder":
        """
        Add an import statement to the module.

        Args:
            module (str): The name of the module to import.
            targets (Set[str], optional): Specific targets to import from the module. Defaults to an empty set, which means import the entire module.

        Returns:
            ModuleBuilder: The builder itself, allowing for method chaining.
        """
        self.module.top_level_nodes.append(Import(module, targets, 0))
        return self

    def add_export_spec(self, exports: Set[str]) -> "ModuleBuilder":
        """
        Add an export specification to the module.

        Args:
            exports (Set[str]): A set of names to be exported from the module.

        Returns:
            ModuleBuilder: The builder itself, allowing for method chaining.
        """
        self.module.top_level_nodes.append(ExportSpec(exports, 0))
        return self


class FnDeclBuilder:
    """
    Builder for constructing a function declaration (FnDecl).
    """

    def __init__(self, fn_decl: FnDecl, module_builder: ModuleBuilder):
        """
        Initialize the FnDeclBuilder.

        Args:
            fn_decl (FnDecl): The function declaration AST node.
            module_builder (ModuleBuilder): The parent module builder.
        """
        self.fn_decl = fn_decl
        self.module_builder = module_builder
        self.ret_type_set = False

    def build(self) -> ModuleBuilder:
        """
        Finalize the function declaration and return to the module builder.
        Returns:
            ModuleBuilder: The parent module builder.
        Raises:
            ValueError: If the return type is not set.
        """
        if not self.ret_type_set:
            raise ValueError("Return type not set for function declaration")
        return self.module_builder

    def add_type_param(self, name: str) -> "FnDeclBuilder":
        """
        Add a type parameter to the function.
        Args:
            name (str): The name of the type parameter.
        Returns:
            FnDeclBuilder: The builder itself.
        """
        self.fn_decl.type_params.append(TypeParam(name, 0))
        return self

    def add_param(self, name: str, type: TypeAnnotation) -> "FnDeclBuilder":
        """
        Add a parameter to the function.
        Args:
            name (str): The parameter name.
            type (TypeAnnotation): The type annotation of the parameter.
        Returns:
            FnDeclBuilder: The builder itself.
        """
        self.fn_decl.params.append(Param(name, type, 0))
        return self

    def set_ret_type(self, type: TypeAnnotation) -> "FnDeclBuilder":
        """
        Set the return type of the function.
        Args:
            type (TypeAnnotation): The return type annotation.
        Returns:
            FnDeclBuilder: The builder itself.
        """
        self.fn_decl.ret_type = type
        self.ret_type_set = True
        return self

    def add_statement(self, statement: Statement) -> "FnDeclBuilder":
        """
        Add a statement to the function body.
        Args:
            statement (Statement): A statement node.
        Returns:
            FnDeclBuilder: The builder itself.
        """
        self.fn_decl.body.append(statement)
        return self


class StructDeclBuilder:
    """
    Builder for constructing a struct declaration (StructDecl).
    """

    def __init__(self, struct_decl: StructDecl, module_builder: ModuleBuilder):
        """
        Initialize the StructDeclBuilder.

        Args:
            struct_decl (StructDecl): The struct declaration AST node.
            module_builder (ModuleBuilder): The parent module builder.
        """
        self.struct_decl = struct_decl
        self.module_builder = module_builder

    def build(self) -> ModuleBuilder:
        """
        Finalize the struct declaration and return to the module builder.
        Returns:
            ModuleBuilder: The parent module builder.
        """
        return self.module_builder

    def add_type_param(self, name: str) -> "StructDeclBuilder":
        """
        Add a type parameter to the struct.
        Args:
            name (str): The name of the type parameter.
        Returns:
            StructDeclBuilder: The builder itself.
        """
        self.struct_decl.type_params.append(TypeParam(name, 0))
        return self

    def add_field(self, name: str, type: TypeAnnotation) -> "StructDeclBuilder":
        """
        Add a field to the struct.
        Args:
            name (str): The field name.
            type (TypeAnnotation): The type annotation of the field.
        Returns:
            StructDeclBuilder: The builder itself.
        """
        self.struct_decl.fields.append(StructField(name, type, 0))
        return self


class UnionDeclBuilder:
    """
    Builder for constructing a union declaration (UnionDecl).
    """

    def __init__(self, union_decl: UnionDecl, module_builder: ModuleBuilder):
        """
        Initialize the UnionDeclBuilder.

        Args:
            union_decl (UnionDecl): The union declaration AST node.
            module_builder (ModuleBuilder): The parent module builder.
        """
        self.union_decl = union_decl
        self.module_builder = module_builder

    def build(self) -> ModuleBuilder:
        """
        Finalize the union declaration and return to the module builder.
        Returns:
            ModuleBuilder: The parent module builder.
        """
        return self.module_builder

    def add_type_param(self, name: str) -> "UnionDeclBuilder":
        """
        Add a type parameter to the union.
        Args:
            name (str): The name of the type parameter.
        Returns:
            UnionDeclBuilder: The builder itself.
        """
        self.union_decl.type_params.append(TypeParam(name, 0))
        return self

    def build_struct_variant(self, name: str) -> "UnionStructVariantBuilder":
        """
        Begin building a struct variant for the union.
        Args:
            name (str): The variant name.
        Returns:
            UnionStructVariantBuilder: Builder for the struct variant.
        """
        union_struct_variant = UnionStructVariant(name, [], 0)
        self.union_decl.fields.append(union_struct_variant)
        return UnionStructVariantBuilder(union_struct_variant, self)

    def build_tuple_variant(self, name: str) -> "UnionTupleVariantBuilder":
        """
        Begin building a tuple variant for the union.
        Args:
            name (str): The variant name.
        Returns:
            UnionTupleVariantBuilder: Builder for the tuple variant.
        """
        union_tuple_variant = UnionTupleVariant(name, [], 0)
        self.union_decl.fields.append(union_tuple_variant)
        return UnionTupleVariantBuilder(union_tuple_variant, self)

    def add_tag_variant(self, name: str) -> "UnionDeclBuilder":
        """
        Add a tag variant to the union.
        Args:
            name (str): The tag variant name.
        Returns:
            UnionDeclBuilder: The builder itself.
        """
        self.union_decl.fields.append(UnionTagVariant(name, 0))
        return self


class UnionStructVariantBuilder:
    """
    Builder for constructing a struct variant within a union declaration.
    """

    def __init__(
        self,
        union_struct_variant: UnionStructVariant,
        union_decl_builder: UnionDeclBuilder,
    ):
        """
        Initialize the UnionStructVariantBuilder.

        Args:
            union_struct_variant (UnionStructVariant): The struct variant AST node.
            union_decl_builder (UnionDeclBuilder): The parent union declaration builder.
        """
        self.union_struct_variant = union_struct_variant
        self.union_decl_builder = union_decl_builder

    def build(self) -> UnionDeclBuilder:
        """
        Finalize the struct variant and return to the union declaration builder.
        Returns:
            UnionDeclBuilder: The parent union declaration builder.
        """
        return self.union_decl_builder

    def add_field(self, name: str, type: TypeAnnotation) -> "UnionStructVariantBuilder":
        """
        Add a field to the struct variant.
        Args:
            name (str): The field name.
            type (TypeAnnotation): The type annotation of the field.
        Returns:
            UnionStructVariantBuilder: The builder itself.
        """
        self.union_struct_variant.fields.append(StructField(name, type, 0))
        return self


class UnionTupleVariantBuilder:
    """
    Builder for constructing a tuple variant within a union declaration.
    """

    def __init__(
        self,
        union_tuple_variant: UnionTupleVariant,
        union_decl_builder: UnionDeclBuilder,
    ):
        """
        Initialize the UnionTupleVariantBuilder.

        Args:
            union_tuple_variant (UnionTupleVariant): The tuple variant AST node.
            union_decl_builder (UnionDeclBuilder): The parent union declaration builder.
        """
        self.union_tuple_variant = union_tuple_variant
        self.union_decl_builder = union_decl_builder

    def build(self) -> UnionDeclBuilder:
        """
        Finalize the tuple variant and return to the union declaration builder.
        Returns:
            UnionDeclBuilder: The parent union declaration builder.
        """
        return self.union_decl_builder

    def add_type(self, type: TypeAnnotation) -> "UnionTupleVariantBuilder":
        """
        Add a type annotation to the tuple variant.
        Args:
            type (TypeAnnotation): The type annotation to add.
        Returns:
            UnionTupleVariantBuilder: The builder itself.
        """
        self.union_tuple_variant.types.append(type)
        return self


class TypeAliasDeclBuilder:
    """
    Builder for constructing a type alias declaration (TypeAliasDecl).
    """

    def __init__(self, type_alias_decl: TypeAliasDecl, module_builder: ModuleBuilder):
        """
        Initialize the TypeAliasDeclBuilder.

        Args:
            type_alias_decl (TypeAliasDecl): The type alias declaration AST node.
            module_builder (ModuleBuilder): The parent module builder.
        """
        self.type_alias_decl = type_alias_decl
        self.type_set = False
        self.module_builder = module_builder

    def build(self) -> ModuleBuilder:
        """
        Finalize the type alias declaration and return to the module builder.
        Returns:
            ModuleBuilder: The parent module builder.
        Raises:
            ValueError: If the type for the alias is not set.
        """
        if not self.type_set:
            raise ValueError("Type not set for type alias declaration")
        return self.module_builder

    def add_type_param(self, name: str) -> "TypeAliasDeclBuilder":
        """
        Add a type parameter to the type alias.
        Args:
            name (str): The name of the type parameter.
        Returns:
            TypeAliasDeclBuilder: The builder itself.
        """
        self.type_alias_decl.type_params.append(TypeParam(name, 0))
        return self

    def set_type(self, type: TypeAnnotation) -> "TypeAliasDeclBuilder":
        """
        Set the type annotation for the type alias.
        Args:
            type (TypeAnnotation): The type annotation to set.
        Returns:
            TypeAliasDeclBuilder: The builder itself.
        """
        self.type_alias_decl.type_annotation = type
        self.type_set = True
        return self
