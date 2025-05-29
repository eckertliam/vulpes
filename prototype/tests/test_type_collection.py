from prototype.ast import (
    ModuleManager,
    Module,
    StructDecl,
    UnionDecl,
    TypeAliasDecl,
    NamedTypeAnnotation,
)
from prototype.types import (
    FloatType,
    IntType,
    TupleType,
    TypeEnv,
    Type,
    TypeAlias,
    StructType,
    UnionType,
    FunctionType,
    PolyFunctionType,
    PolyStructType,
    PolyUnionType,
    PolyTypeAlias,
    MonoFunctionType,
    MonoStructType,
    MonoUnionType,
    MonoTypeAlias,
)
from prototype.module_builder import ModuleBuilder
from prototype.ast.passes import (
    Pipeline,
    module_res_pass,
    name_res_pass,
    export_collection_pass,
    import_linker_pass,
    name_ref_pass,
    type_collection_pass,
)

pipeline = Pipeline(
    [
        module_res_pass,
        name_res_pass,
        export_collection_pass,
        import_linker_pass,
        name_ref_pass,
        type_collection_pass,
    ]
)


def test_simple_struct():
    mb = ModuleBuilder("test")
    struct_decl_builder = mb.build_struct_decl("TestStruct")
    struct_decl_builder.add_field("field1", NamedTypeAnnotation("i64", 0))
    struct_decl_builder.add_field("field2", NamedTypeAnnotation("f64", 0))
    struct_decl_builder.build()
    module_manager = ModuleManager()
    module_manager.add_module(mb.build())
    module_manager, errors = pipeline(module_manager)
    # check that there are no errors
    assert len(errors) == 0
    # check that the module's type env has a mono struct named TestStruct
    # with the expected fields
    module = module_manager.get_module("test")
    assert module is not None
    assert module.type_env is not None
    test_struct = module.type_env.get_struct("TestStruct")
    assert test_struct is not None
    assert isinstance(test_struct, MonoStructType)
    assert test_struct.name == "TestStruct$mono$"
    fields = test_struct.fields
    assert len(fields) == 2
    assert fields["field1"] == IntType()
    assert fields["field2"] == FloatType()


def test_recursive_struct():
    """Test that recursive struct types work correctly.

    This test creates a Node struct that has a field of type Node (self-reference),
    which is a common pattern for linked lists, trees, etc.
    """
    mb = ModuleBuilder("test")

    # Create a recursive struct: struct Node { value: i64, next: Node }
    struct_decl_builder = mb.build_struct_decl("Node")
    struct_decl_builder.add_field("value", NamedTypeAnnotation("i64", 0))
    struct_decl_builder.add_field(
        "next", NamedTypeAnnotation("Node", 0)
    )  # Self-reference
    struct_decl_builder.build()

    module_manager = ModuleManager()
    module_manager.add_module(mb.build())
    module_manager, errors = pipeline(module_manager)

    # Check that there are no errors - recursive types should be handled correctly
    assert len(errors) == 0

    # Check that the module's type env has the Node struct
    module = module_manager.get_module("test")
    assert module is not None
    assert module.type_env is not None

    node_struct = module.type_env.get_struct("Node")
    assert node_struct is not None
    assert isinstance(node_struct, MonoStructType)
    assert node_struct.name == "Node$mono$"

    # Verify the fields
    fields = node_struct.fields
    assert len(fields) == 2
    assert fields["value"] == IntType()

    # The "next" field should reference the Node type itself
    next_field_type = fields["next"]
    assert next_field_type == node_struct  # Should be the same type object


def test_mutually_recursive_structs():
    """Test that mutually recursive struct types work correctly.

    This test creates two structs that reference each other:
    struct A
        b_field: B

    struct B
        a_field: A

    """
    mb = ModuleBuilder("test")

    # Create struct A that references B
    struct_a_builder = mb.build_struct_decl("A")
    struct_a_builder.add_field("b_field", NamedTypeAnnotation("B", 0))
    struct_a_builder.build()

    # Create struct B that references A
    struct_b_builder = mb.build_struct_decl("B")
    struct_b_builder.add_field("a_field", NamedTypeAnnotation("A", 0))
    struct_b_builder.build()

    module_manager = ModuleManager()
    module_manager.add_module(mb.build())
    module_manager, errors = pipeline(module_manager)

    # Check that there are no errors - mutual recursion should be handled
    assert len(errors) == 0

    # Check that both structs exist in the type environment
    module = module_manager.get_module("test")
    assert module is not None
    assert module.type_env is not None

    struct_a = module.type_env.get_struct("A")
    struct_b = module.type_env.get_struct("B")

    assert struct_a is not None
    assert struct_b is not None
    assert isinstance(struct_a, MonoStructType)
    assert isinstance(struct_b, MonoStructType)

    # Verify the cross-references
    assert struct_a.fields["b_field"] == struct_b
    assert struct_b.fields["a_field"] == struct_a


def test_recursive_type_alias():
    """Test that recursive type aliases work correctly.

    This test creates a type alias that references itself:
    type List = Node
    struct Node
        value: i64
        next: List
    """
    mb = ModuleBuilder("test")

    # Create the Node struct first
    struct_decl_builder = mb.build_struct_decl("Node")
    struct_decl_builder.add_field("value", NamedTypeAnnotation("i64", 0))
    struct_decl_builder.add_field(
        "next", NamedTypeAnnotation("List", 0)
    )  # References the alias
    struct_decl_builder.build()

    # Create a type alias that points to Node
    alias_builder = mb.build_type_alias_decl("List")
    alias_builder.set_type(NamedTypeAnnotation("Node", 0))
    alias_builder.build()

    module_manager = ModuleManager()
    module_manager.add_module(mb.build())
    module_manager, errors = pipeline(module_manager)

    # Check that there are no errors
    assert len(errors) == 0

    # Check that both the struct and alias exist
    module = module_manager.get_module("test")
    assert module is not None
    assert module.type_env is not None

    node_struct = module.type_env.get_struct("Node")
    list_alias = module.type_env.get_alias("List")

    assert node_struct is not None
    assert list_alias is not None
    assert isinstance(node_struct, MonoStructType)
    assert isinstance(list_alias, MonoTypeAlias)

    # The alias should resolve to the Node type
    assert list_alias.type == node_struct

    # The Node's next field should reference the List alias
    assert node_struct.fields["next"] == list_alias


def test_cross_module_types():
    """Test that types can be properly referenced across module boundaries.

    This test creates two modules:
    - Module 'base' defines a Person struct
    - Module 'app' imports Person and defines a Company struct that uses Person
    """
    # Create the base module with Person struct
    base_mb = ModuleBuilder("base")

    # struct Person
    #     name: string
    #     age: i32
    person_builder = base_mb.build_struct_decl("Person")
    person_builder.add_field("name", NamedTypeAnnotation("string", 0))
    person_builder.add_field("age", NamedTypeAnnotation("i32", 0))
    person_builder.build()

    # Export the Person type
    base_mb.add_export_spec({"Person"})

    # Create the app module that imports and uses Person
    app_mb = ModuleBuilder("app")

    # Import Person from base module
    app_mb.add_import("base", {"Person"})

    # struct Company
    #     name: string
    #     ceo: Person  # Cross-module type reference
    company_builder = app_mb.build_struct_decl("Company")
    company_builder.add_field("name", NamedTypeAnnotation("string", 0))
    company_builder.add_field(
        "ceo", NamedTypeAnnotation("Person", 0)
    )  # References imported type
    company_builder.build()

    # Build both modules and add to manager
    module_manager = ModuleManager()
    module_manager.add_module(base_mb.build())
    module_manager.add_module(app_mb.build())

    # Run the pipeline
    module_manager, errors = pipeline(module_manager)

    # Check that there are no errors
    assert len(errors) == 0

    # Verify the base module has Person
    base_module = module_manager.get_module("base")
    assert base_module is not None
    assert base_module.type_env is not None

    person_struct = base_module.type_env.get_struct("Person")
    assert person_struct is not None
    assert isinstance(person_struct, MonoStructType)
    assert person_struct.name == "Person$mono$"
    assert len(person_struct.fields) == 2

    # Verify the app module has Company and can reference Person
    app_module = module_manager.get_module("app")
    assert app_module is not None
    assert app_module.type_env is not None

    company_struct = app_module.type_env.get_struct("Company")
    assert company_struct is not None
    assert isinstance(company_struct, MonoStructType)
    assert company_struct.name == "Company$mono$"
    assert len(company_struct.fields) == 2

    # The ceo field should reference the Person type from the base module
    ceo_field_type = company_struct.fields["ceo"]
    assert ceo_field_type == person_struct  # Should be the same type object


def test_recursive_union():
    """Test that recursive unions work correctly.

    This test creates a union that references itself:
    union Expr
        Int(i64)
        Add(Expr, Expr)
    """
    mb = ModuleBuilder("test")

    # Create the Expr union
    union_builder = mb.build_union_decl("Expr")
    tuple_variant = union_builder.build_tuple_variant("Integer")
    tuple_variant.add_type(NamedTypeAnnotation("i64", 0))
    tuple_variant.build()

    tuple_variant = union_builder.build_tuple_variant("Add")
    tuple_variant.add_type(NamedTypeAnnotation("Expr", 0))
    tuple_variant.add_type(NamedTypeAnnotation("Expr", 0))
    tuple_variant.build()

    module_manager = ModuleManager()
    module_manager.add_module(mb.build())
    module_manager, errors = pipeline(module_manager)

    # Check that there are no errors
    assert len(errors) == 0

    # Check that the module's type env has the Expr union
    module = module_manager.get_module("test")
    assert module is not None
    assert module.type_env is not None
    expr_union = module.type_env.get_union("Expr")
    assert expr_union is not None
    assert isinstance(expr_union, MonoUnionType)
    assert expr_union.name == "Expr$mono$"
    assert len(expr_union.variants) == 2
    assert expr_union.variants["Integer"] == TupleType([IntType()])
    assert expr_union.variants["Add"] == TupleType([expr_union, expr_union])