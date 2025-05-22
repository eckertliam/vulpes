# AST Passes

This document outlines the AST passes that are used to verify and transform the AST.

## Module Resolution Pass

The Module Resolution Pass ensures that all imported modules exist, have been successfully loaded into the compilation environment, and that the imported names are valid exports of those modules.

It performs the following steps:

- Reads the import statements from each module’s AST.
- Confirms that each referenced module is present in the `ModuleManager`.
- Verifies that each imported name exists in the export set of the referenced module.
- Reports an error if any import cannot be resolved.

This pass guarantees that all modules and their imported names are available and valid for later passes, but it does not analyze or validate usage of those symbols.

## Name Resolution Pass

The Name Resolution Pass walks each module and builds its local symbol table. It resolves all identifiers declared within the module itself (functions, structs, variables, types, etc.).

It performs the following steps:

- Walks top-level declarations and binds their names to symbols.
- Adds all locally declared symbols to the module’s symbol table.
- Resolves all references to those names within the module body.
- Does not link imported names to external symbols—that happens in a later import linking step.

## Export Collection Pass

The Export Collection Pass populates each module’s `exports` table based on its `ExportSpec` nodes. This pass runs after name resolution, when all local symbols have been defined.

It performs the following steps:

- Reads each module’s `ExportSpec`.
- Validates that all specified names are defined in the module’s symbol table.
- Adds each named symbol to the module’s `exports` table.
- Logs errors if any name listed in the export spec is undefined.

This pass ensures that each module declares exactly which symbols are visible to other modules.

## Import Linking Pass

The Import Linking Pass resolves imported names in each module to actual symbols from other modules’ export tables. It connects each imported identifier to its corresponding symbol, assuming module resolution and export collection have already completed.

It performs the following steps:

- For each import in the module, look up the referenced module in the `ModuleManager`.
- Verify that the referenced module exports the requested names.
- Populate the importing module’s `imports` table with those resolved symbols.
- Report an error if any requested name is not found in the target module’s `exports`.

This pass allows imported identifiers to participate in later semantic analysis just like local names.

## Type Collection Pass

The Type Collection Pass collects all the type declarations in the program and adds them to the module's `TypeEnv`.

It performs the following steps:

- Walks all top-level type declarations in the AST and registers their definitions in the module’s `TypeEnv`.
- Recursively processes dependent type declarations to ensure all referenced types are available.
- Detects and reports cycles in type aliases to prevent infinite recursion during type resolution.
- Adds imported types to the `TypeEnv` if they are referenced in type annotations.

This pass must run before the Type Normalization Pass, as it ensures all type names are resolved to their internal representations.

## Type Normalization Pass

The Type Normalization Pass walks the AST and converts all type annotations to their internal representations attaching that internal type to the variable, or function parameter. It also attaches `TypeHole` to variables that require type inference.

It performs the following steps:

- Walks the AST and converts all type annotations to their internal representations attaching that internal type to the variable, or function parameter.
- Attaches `TypeHole` to variables that require type inference.
- Attaches `TypeHole` to function calls with generics that have no annotations and requires type inference.
- Attaches `TypeHole` to union instantiations (calls) that have no annotations and requires type inference.
- Logs errors if any type annotation is invalid.

This pass must run after the Type Collection Pass, as it ensures all type names are resolved to their internal representations.

## Type Inference Pass

The Type Inference Pass walks the AST and performs type inference by gathering type constraints involving `TypeHole`s and resolving them via unification. This pass determines the type of every expression and fills in the type of all previously unannotated variables and expressions.

It performs the following steps:

- Walks the AST and, for each expression:
  - Gathers type constraints based on how expressions are used.
  - Example: a function call `f(x)` introduces a constraint that `f` has function type and `x` matches its parameter type.
- Builds a constraint graph between all relevant types (including holes).
- Applies unification to resolve constraints and assign concrete types to all `TypeHole`s.
- Attaches the resolved type to each expression node in the AST.
- Logs errors for failed unifications (e.g. type mismatches, unsolved type holes).

This pass must run after the Type Normalization Pass, which ensures that every variable and expression has a type (concrete or hole). After this pass all types must be concrete to move forward.

## Type Checking Pass

The Type Checking Pass validates that all inferred and annotated types are consistent, ensuring that the final AST contains only well-typed expressions. While type inference assigns types, type checking confirms their correctness against user-specified expectations and language constraints.

It performs the following steps:

- Walks the AST, validating that all expressions conform to their expected types.
- Checks that all type annotations match the inferred types attached during the Type Inference Pass.
  - Example: if a variable is annotated as `int` but inferred to be `bool`, an error is reported.
- Ensures that function return types match the declared return type annotations, if any.
- Ensures that all `TypeHole`s have been resolved. Reports an error if any remain.
- Enforces type-specific rules, such as:
  - Operands to arithmetic operators must be numeric types.
  - Conditions in control flow must be `bool`.
  - Struct field accesses must refer to valid fields.
- Confirms that all function calls are made with the correct number and types of arguments (arity and compatibility).

This pass guarantees that the final AST is type-safe and fully concrete, and prepares the program for subsequent lowering or code generation.

