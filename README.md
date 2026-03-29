# Vulpes 🦊

**Vulpes** (*Vulpes Vulpes*) is a statically-typed, dynamically-dispatched language inspired by Rust and Lisp. Designed for rapid prototyping, clean syntax, instant REPL feedback, and high-performance AOT compilation.

## Development Status

Following a prototype in Python, the compiler and VM are now being implemented in C++23. Current progress:

- **Lexer** — complete tokenization of all keywords, operators, and literals
- **Parser** — recursive descent parser with full operator precedence, function declarations, and variable bindings
- **Bytecode emitter** — AST-to-bytecode compilation for arithmetic, variables, and function calls
- **VM** — stack-based virtual machine with garbage collection, function call frames, and integer/float arithmetic

For the full language spec see [docs/spec.md](docs/spec.md).

## Building

Requires [Bazel](https://bazel.build/) 8+.

```sh
# Build everything
bazel build //src/...

# Run tests
bazel test //src:vulpes_tests
```

Or use the Makefile shortcuts: `make`, `make test`, `make clean`.

## License

Vulpes is licensed under Apache 2.0. See the [LICENSE](LICENSE) file for details.