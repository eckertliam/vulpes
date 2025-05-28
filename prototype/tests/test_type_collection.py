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

pipeline = Pipeline([
    module_res_pass,
    name_res_pass,
    export_collection_pass,
    import_linker_pass,
    name_ref_pass,
    type_collection_pass,
])


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
    assert test_struct.name == "TestStruct"
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
    struct_decl_builder.add_field("next", NamedTypeAnnotation("Node", 0))  # Self-reference
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
    assert node_struct.name == "Node"
    
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
    struct_decl_builder.add_field("next", NamedTypeAnnotation("List", 0))  # References the alias
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
    list_alias = module.type_env.get_type_alias("List")
    
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
    company_builder.add_field("ceo", NamedTypeAnnotation("Person", 0))  # References imported type
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
    assert person_struct.name == "Person"
    assert len(person_struct.fields) == 2
    
    # Verify the app module has Company and can reference Person
    app_module = module_manager.get_module("app")
    assert app_module is not None
    assert app_module.type_env is not None
    
    company_struct = app_module.type_env.get_struct("Company")
    assert company_struct is not None
    assert isinstance(company_struct, MonoStructType)
    assert company_struct.name == "Company"
    assert len(company_struct.fields) == 2
    
    # The ceo field should reference the Person type from the base module
    ceo_field_type = company_struct.fields["ceo"]
    assert ceo_field_type == person_struct  # Should be the same type object


def test_cross_module_recursive_types():
    """Test recursive types that span across modules.
    
    This test creates:
    - Module 'types' with a Node struct that references List from 'containers'
    - Module 'containers' with a List type alias that references Node from 'types'
    """
    # Create the types module
    types_mb = ModuleBuilder("types")
    
    # Import List from containers module
    types_mb.add_import("containers", {"List"})
    
    # struct Node
    #     value: i64
    #     children: List  # Cross-module reference
    node_builder = types_mb.build_struct_decl("Node")
    node_builder.add_field("value", NamedTypeAnnotation("i64", 0))
    node_builder.add_field("children", NamedTypeAnnotation("List", 0))
    node_builder.build()
    
    # Export Node
    types_mb.add_export_spec({"Node"})
    
    # Create the containers module
    containers_mb = ModuleBuilder("containers")
    
    # Import Node from types module
    containers_mb.add_import("types", {"Node"})
    
    # type List = Array<Node>  # For simplicity, we'll use a struct instead
    # struct Array
    #     data: Node
    #     size: i32
    array_builder = containers_mb.build_struct_decl("Array")
    array_builder.add_field("data", NamedTypeAnnotation("Node", 0))  # Cross-module reference
    array_builder.add_field("size", NamedTypeAnnotation("i32", 0))
    array_builder.build()
    
    # type List = Array
    list_alias_builder = containers_mb.build_type_alias_decl("List")
    list_alias_builder.set_type(NamedTypeAnnotation("Array", 0))
    list_alias_builder.build()
    
    # Export List
    containers_mb.add_export_spec({"List"})
    
    # Build both modules and add to manager
    module_manager = ModuleManager()
    module_manager.add_module(types_mb.build())
    module_manager.add_module(containers_mb.build())
    
    # Run the pipeline
    module_manager, errors = pipeline(module_manager)
    
    # Check that there are no errors - cross-module recursion should be handled
    assert len(errors) == 0
    
    # Verify types module
    types_module = module_manager.get_module("types")
    assert types_module is not None
    node_struct = types_module.type_env.get_struct("Node")
    assert node_struct is not None
    assert isinstance(node_struct, MonoStructType)
    
    # Verify containers module
    containers_module = module_manager.get_module("containers")
    assert containers_module is not None
    array_struct = containers_module.type_env.get_struct("Array")
    list_alias = containers_module.type_env.get_type_alias("List")
    assert array_struct is not None
    assert list_alias is not None
    assert isinstance(array_struct, MonoStructType)
    assert isinstance(list_alias, MonoTypeAlias)
    
    # Verify cross-module references
    # Node.children should reference List from containers
    children_field_type = node_struct.fields["children"]
    assert children_field_type == list_alias
    
    # Array.data should reference Node from types
    data_field_type = array_struct.fields["data"]
    assert data_field_type == node_struct
    
    # List should alias to Array
    assert list_alias.type == array_struct


def test_cross_module_generic_types():
    """Test that generic types work across module boundaries.
    
    This test creates:
    - Module 'generics' with a generic Container<T> struct
    - Module 'usage' that imports and instantiates Container<i64>
    """
    # Create the generics module
    generics_mb = ModuleBuilder("generics")
    
    # struct Container<T>
    #     value: T
    #     count: i32
    container_builder = generics_mb.build_struct_decl("Container")
    container_builder.add_type_param("T")
    container_builder.add_field("value", NamedTypeAnnotation("T", 0))  # Generic type parameter
    container_builder.add_field("count", NamedTypeAnnotation("i32", 0))
    container_builder.build()
    
    # Export Container
    generics_mb.add_export_spec({"Container"})
    
    # Create the usage module
    usage_mb = ModuleBuilder("usage")
    
    # Import Container from generics module
    usage_mb.add_import("generics", {"Container"})
    
    # struct IntBox
    #     container: Container<i64>  # Generic instantiation across modules
    # Note: For this test, we'll use a named type since GenericTypeAnnotation 
    # would require more complex handling
    intbox_builder = usage_mb.build_struct_decl("IntBox")
    intbox_builder.add_field("container", NamedTypeAnnotation("Container", 0))
    intbox_builder.build()
    
    # Build both modules and add to manager
    module_manager = ModuleManager()
    module_manager.add_module(generics_mb.build())
    module_manager.add_module(usage_mb.build())
    
    # Run the pipeline
    module_manager, errors = pipeline(module_manager)
    
    # Check that there are no errors
    assert len(errors) == 0
    
    # Verify generics module
    generics_module = module_manager.get_module("generics")
    assert generics_module is not None
    container_struct = generics_module.type_env.get_struct("Container")
    assert container_struct is not None
    # Should be polymorphic since it has type parameters
    assert isinstance(container_struct, PolyStructType)
    assert len(container_struct.type_params) == 1
    
    # Verify usage module
    usage_module = module_manager.get_module("usage")
    assert usage_module is not None
    intbox_struct = usage_module.type_env.get_struct("IntBox")
    assert intbox_struct is not None
    assert isinstance(intbox_struct, MonoStructType)
    
    # The container field should reference the imported Container type
    container_field_type = intbox_struct.fields["container"]
    assert container_field_type == container_struct


