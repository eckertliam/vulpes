# Vulpes 🦊

**Vulpes** (*Vulpes Vulpes*) is a language inspired by Rust and Lisp. Designed for rapid prototyping, clean syntax, instant REPL feedback, and high performance AOT compilation. 

## Development Status

Following a prototype in Python, I am now implementing a performant version in C++ following the roadmap below.

## Roadmap

### Phase 1: Language Semantics + Runtime

- [ ] Handwritten parser and AST
- [ ] REPL with expression evaluation
- [ ] Object model: dynamic values, closures, objects
- [ ] Bytecode interpreter (simple stack machine)
- [ ] Basic standard library (print, math, string ops)
- [ ] Errors with spans and hints

### Phase 2: Type System + Analysis

- [ ] Shallow structural typing for objects
- [ ] Structs (fixed shape, value-type aggregates)
- [ ] Type errors with hints
- [ ] Optional type annotations

### Phase 3: Compilation

- [ ] Lower bytecode to LLVM IR
- [ ] AOT compilation
- [ ] Optimizations (inliner, dead code elimination)

### Phase 4: Metaprogramming

- [ ] Macro system (pattern based + hygienic)
- [ ] Compile-time evaluation hooks
- [ ] Custom DSL embedding (think Racket langs)


## License

Vulpes is licensed under Apache 2.0. See the [LICENSE](LICENSE) file for details.