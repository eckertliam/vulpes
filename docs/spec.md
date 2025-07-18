
# Vulpes Language Specification

**Version**: 0.1 (Draft)

This document defines the syntax and semantics of the **Vulpes** programming language.  
It is the canonical reference for implementers of parsers, compilers, VMs, tooling, and
the standard library.

> **Note** Items marked with `TODO:` are undecided or deferred for a later revision.

---

## 1 · Lexical Structure

### 1.1 Tokens & Separators
* **Whitespace** (space, tab, carriage‑return, newline) separates tokens and has no other
  semantic meaning inside a block.  
* **Comments**  
  * single‑line: `// anything until end‑of‑line`  
  * block comments are **not** supported (simplicity).
* **Semicolons** terminate statements and are **required** (no automatic insertion).

### 1.2 Identifiers

```
Identifier  ::=  /[A-Za-z_][A-Za-z0-9_]*/
```

Identifiers are case‑sensitive Unicode but must start with an ASCII letter or `_`.

### 1.3 Literals

```
IntegerLit  ::=  DecInt
              | "0x" HexDigits
              | "0b" BinDigits

FloatLit    ::=  DecInt "." DecInt [ExponentPart]

StringLit   ::=  '"' { StringChar } '"'
CharLit     ::=  "'" Char "'"
BoolLit     ::=  "true" | "false"
NullLit     ::=  "null"
```

Underscores (`_`) may be inserted for readability: `1_000_000`.

### 1.4 Keywords

```
fn   let  const  struct  class  enum  pub
from import export
if else while for in match return break continue
true false null type
```

The above words are reserved and may not be used as identifiers.

---

## 2 · Grammar (pseudo‑EBNF)

The notation:

* `A?`   optional  
* `A*`   zero or more  
* `A+`   one or more  
* `A | B` alternatives  
* `"tok"` literal token  

```
Program      ::=  Module

Module       ::=  ImportStmt* ExportStmt? TopDecl*

ImportStmt   ::=  "from" ModulePath "import" "{" IdentList "}" ";"
ExportStmt   ::=  "export" "{" IdentList "}" ";"

TopDecl      ::=  ConstDecl
               |  EnumDecl
               |  StructDecl
               |  ClassDecl
               |  FuncDecl
               |  MacroDecl            // TODO: formalise macro grammar
               |  ImportStmt
               |  ExportStmt

ConstDecl    ::=  "const" Identifier "=" Expr ";"

EnumDecl     ::=  "enum" Identifier "{" EnumTagList "}" ";"
EnumTagList  ::=  Identifier ("," Identifier)*

StructDecl   ::=  "struct" Identifier "{" StructFieldList? "}" ";"
StructField  ::=  Identifier ":" TypeAnn
StructFieldList ::= StructField ("," StructField)*

ClassDecl    ::=  "class" Identifier "{" ClassBody* "}" ";"
ClassBody    ::=  FieldDecl | MethodDecl
FieldDecl    ::=  ["pub"] Identifier ":" TypeAnn ";"
MethodDecl   ::=  "fn" Identifier "(" ParamList? ")" ReturnAnn? Block

FuncDecl     ::=  "fn" Identifier "(" ParamList? ")" ReturnAnn? Block
ReturnAnn    ::=  ":" TypeAnn
Param        ::=  Identifier [":" TypeAnn]
ParamList    ::=  Param ("," Param)*

MacroDecl    ::=  "macro" Identifier Block      // TODO: semantics

Block        ::=  "{" Stmt* "}"

Stmt         ::=  LetStmt
               |  ExprStmt
               |  IfStmt
               |  WhileStmt
               |  ForStmt
               |  ReturnStmt
               |  BreakStmt
               |  ContinueStmt
               |  Block

LetStmt      ::=  "let" Identifier ["=" Expr] ";"

ExprStmt     ::=  Expr ";"

IfStmt       ::=  "if" Expr Block ["else" Block]

WhileStmt    ::=  "while" Expr Block

ForStmt      ::=  "for" Identifier "in" Expr Block

ReturnStmt   ::=  "return" [Expr] ";"

BreakStmt    ::=  "break" ";"
ContinueStmt ::=  "continue" ";"

Expr         ::=  Assignment
Assignment   ::=  LogicalOr ["=" Expr]

LogicalOr    ::=  LogicalAnd ("||" LogicalAnd)*
LogicalAnd   ::=  Equality ("&&" Equality)*
Equality     ::=  Comparison ( ("==" | "!=") Comparison )*
Comparison   ::=  Term (("<" | ">" | "<=" | ">=") Term)*
Term         ::=  Factor (("+" | "-") Factor)*
Factor       ::=  Unary (("*" | "/" | "%") Unary)*
Unary        ::=  ("!" | "-" | "+") Unary | Call
Call         ::=  Primary ( CallSuffix )*
CallSuffix   ::=  "(" ArgList? ")"      // function call
               |  "." Identifier        // field / method access
               |  "[" Expr "]"          // indexing
Primary      ::=  Literal
               |  Identifier
               |  "(" Expr ")"

ArgList      ::=  Expr ("," Expr)*
Literal      ::=  IntegerLit | FloatLit | StringLit | CharLit | BoolLit | NullLit
```

---

## 3 · Static Semantics

### 3.1 Scoping & Name Resolution
* **Lexical scope**. Each block `{ … }` introduces a new lexical scope.
* **Shadowing**. An inner scope may redeclare an identifier from an outer scope.
* **Visibility**.  
  * Inside a module, all top‑level names are private unless listed in an `export { … }` clause.  
  * In a `class`, fields are private unless prefixed with `pub`.

### 3.2 Bindings
* `let` declares a **mutable** binding.
* `const` declares an **immutable** binding that **must** be initialized.
* Struct values are *always* immutable; attempts to mutate produce a compile‑time error.

### 3.3 Types
Vulpes is **duck‑typed** at runtime.  
Optional type annotations (`: TypeExpr`) are currently **ignored by the runtime** but:

1. Serve as documentation.
2. May be expanded to run‑time guards via macros in a future release.
3. Enable future optimizations in the AOT backend.

The core type universe comprises:

| Kind     | Notes                                                                                                                       |
|----------|-----------------------------------------------------------------------------------------------------------------------------|
| `int`    | arbitrary precision integer                                                                                                 |
| `float`  | IEEE‑754 double                                                                                                             |
| `bool`   | `true` / `false`                                                                                                            |
| `char`   | Unicode scalar value                                                                                                        |
| `byte`   | unsigned 8‑bit                                                                                                              |
| `string` | UTF‑8                                                                                                                       |
| `list`   | sequence preserving, mutable, linked-list                                                                                   |
| `vec`    | Contiguous growable array—semantics match amortized push/pop at end, O(1) indexed access, capacity doubles on reallocation. |
| `map`    | associative table                                                                                                           |
| `null`   | sentinel “no value”                                                                                                         |

User‑defined composites:

* **Structs** immutable records, all fields public.  
* **Classes** mutable objects with methods; fields private by default.  
* **Enums**    tagged unions backed by integers (`enum E { A, B }` ⇒ `A == 0`, `B == 1`).  

---

## 4 · Dynamic Semantics

### 4.1 Evaluation Strategy
* The default evaluation order for sub‑expressions is **left‑to‑right**.
* **Function arguments are *lazy***: each argument expression is wrapped in a thunk and
  evaluated on first use inside the callee.  
  *The order in which thunks evaluate is implementation‑defined but each is evaluated at most once.*

### 4.2 Call Semantics
* Parameters are **pass‑by‑reference** (the value is a reference to the object).
* Functions may be **named** or **anonymous** (`fn(a) { … }`).
* **Closures** capture outer variables **by reference**, reflecting subsequent mutations.

### 4.3 Control‑Flow
* `if / else` chooses exactly one branch.
* `while` evaluates its condition before each iteration.
* `for x in expr` iterates over the iterator obtained from `expr`.
* `break` exits the nearest enclosing loop; `continue` skips to the next iteration.
* `return` immediately exits the current function.

### 4.4 Tail Calls
Tail‑call elimination is **best‑effort**; programmers must not depend on it for
stack‑safety.

### 4.5 Memory Management
A **tracing garbage collector** reclaims unreachable objects. Finalization order is undefined.

---

## 5 · Runtime Errors

| Error condition                  | Raised when…                                        |
|----------------------------------|-----------------------------------------------------|
| `DivideByZero`                   | integer or float division by 0                      |
| `NullAccess`                     | member/index access on `null`                       |
| `IndexOutOfBounds`               | list/vec/map index outside valid range              |
| `UninitialisedVariable`          | read before initialisation (should be compile‑time) |
| `TypeError`                      | illegal operation for operand types                 |
| `ValueError`                     | domain error (e.g. negative sqrt)                   |
| `ImportCycle`                    | detected circular module dependency                 |

Errors propagate as **exceptions**. Use standard library function `throw_err(msg)` to raise a user‑defined error.
Catching uses the `match` form (semantics – TODO).

---

## 6 · Standard Library Built‑ins

| Function    | Description                      | Example                                 |
|-------------|----------------------------------|-----------------------------------------|
| `print`     | prints arguments without newline | `print("Hi ", x)`                       |
| `println`   | prints arguments with newline    | `println("Hello")`                      |
| `type`      | returns type name of object      | `println(type(123))` → `int`            |
 | `throw_err` | throws an error with a message   | `throw_err("Expected a valid integer")` |
---

## 7 · Open Questions (`TODO`)

* **Concurrency model** (async/await, threads, message‑passing).
* **Pattern matching semantics** (`match`) and exhaustiveness checks.
* **`Result` structure** and error‑handling sugar.
* **Operator overloading** rules and resolution order.
* **Attribute/annotation grammar** (e.g. `@inline`).
* **Macro system** – precise syntax and hygiene rules.

---

## Appendix A · Operator Precedence (highest → lowest)

| Level | Operators / Constructs              |
|-------|-------------------------------------|
| 14    | `.` `[]` `()` (call/index/member)   |
| 13    | unary `+ - !`                       |
| 12    | `**`                                |
| 11    | `* / %`                             |
| 10    | `+ -`                               |
| 9     | `<< >>`                             |
| 8     | `&`                                 |
| 7     | `^`                                 |
| 6     | `                                   |`                               |
| 5     | `< <= > >=`                         |
| 4     | `== !=`                             |
| 3     | `&&`                                |
| 2     | `                                   ||`                              |
| 1     | `=` (assignment, right‑associative) |

---

### Example – Putting It All Together

```vulpes
// file: hello.vx
export { main }

const GREETING = "Hello"

fn main() {
    let name = "World"
    println(GREETING + ", " + name + "!")
}
```

Running `vulpes hello.vx` prints:

```
Hello, World!
```

