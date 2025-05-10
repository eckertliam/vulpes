from typing import Dict, List, Optional, Set, Tuple, Union

from ..errors import TypeInferenceError
from .name_ref_pass import NameReferencePass
from .base_pass import Pass
from ..ast import (
    ArrayTypeAnnotation,
    Declaration,
    Else,
    FnDecl,
    FunctionTypeAnnotation,
    If,
    Loop,
    NamedTypeAnnotation,
    Statement,
    StructDecl,
    StructField,
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
    GenericType,
    Impl,
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
        """
        Executes the type resolution pass for the program.
        This pass first collects and registers all top-level type declarations (aliases, structs)
        into the type environment, ensuring that all types are available for later resolution.
        Then, it processes function declarations to resolve their types and attach them
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
        elif isinstance(type_decl, StructDecl):
            self.visit_struct_decl(type_decl)
        else:
            pass  # just ignore other declarations

    def resolve_field_annotations(
        self,
        fields: List[StructField],
        decl_name: str,
        decl_line: int,
        decl_id: int,
    ) -> Optional[Dict[str, TypeAnnotation]]:
        """This function resolves the type annotations of the fields of a struct or enum

        Args:
            fields (List[StructField]): The fields to resolve the type annotations of
            decl_name (str): The name of the declaration
            decl_line (int): The line number of the declaration
            decl_id (int): The id of the declaration

        Returns:
            Optional[Dict[str, TypeAnnotation]]: A dict of field names and their resolved type annotations or None if an error occurs
        """
        field_types: Dict[str, TypeAnnotation] = {}
        for field in fields:
            field_type = self.convert_type_annotation_top_level(
                field.type_annotation, decl_line, decl_id
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
        # resolve the type annotation
        type_ = self.convert_type_annotation_top_level(
            type_alias_decl.type_annotation, type_alias_decl.line, type_alias_decl.id
        )
        if type_ is None:
            return  # error already recorded
        # create the type alias
        type_alias = TypeAlias(type_alias_name, type_, type_alias_decl.assert_symbol())
        # now make sure there is not a type alias cycle and that no other type holds the name
        if self.type_env.find_type(type_alias_name) is not None:
            self.errors.append(
                TypeInferenceError(
                    f"Type alias {type_alias_name} using name of existing type",
                    type_alias_decl.line,
                    type_alias_decl.id,
                )
            )
            return
        # check for type alias cycles
        if self.type_env.detect_cycle(type_alias_name, type_):
            self.errors.append(
                TypeInferenceError(
                    f"Type alias {type_alias_name} has a cycle",
                    type_alias_decl.line,
                    type_alias_decl.id,
                )
            )
        # add the type alias to the type env
        self.type_env.add_type_alias(type_alias)

    def visit_struct_decl(self, struct_decl: StructDecl) -> None:
        """
        Processes a struct declaration, resolves its all field types,
        and registers the struct in the type environment. Supports recursive struct types.
        Args:
            struct_decl (StructDecl): The struct declaration node.
        Side effects:
            - Adds the struct and its resolved fields to the type environment.
            - Accumulates errors for invalid field types or type parameter issues.
        """
        if struct_decl.id in self.visited_structs:
            return
        struct_type = StructType(struct_decl.name, {})
        self.type_env.add_type(struct_decl.name, struct_type)
        self.visited_structs.add(struct_decl.id)
        # Resolve all struct field types.
        field_types: Dict[str, Type] = self.resolve_field_annotations(
            struct_decl.fields,
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
        Processes a standalone function declaration (not a method), resolving its parameter types,
        and return type, and attaches the resulting type to the function's symbol.
        Enters the function's scope to process its body statements.
        Args:
            fn_decl (FnDecl): The function declaration node.
        Side effects:
            - Attaches a FunctionType to the function's symbol.
            - Assigns types to parameter symbols.
            - Enters/exits the function's symbol table scope.
            - Accumulates errors for invalid types or missing symbols.
        """
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
        fn_type = FunctionType(param_types, ret_type)
        fn_decl.assert_symbol().type = fn_type
        # Enter function scope and process body statements.
        self.symbol_table.enter_scope(fn_decl.id)
        for statement in fn_decl.body:
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
