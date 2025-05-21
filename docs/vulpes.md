# Vulpes

**Author**: Liam Eckert  
**Email**: liameckert17@gmail.com

This document outlines the vision and design philosophy for the Vulpes programming language. Vulpes is currently in the prototyping phase, and many components are subject to change as the language evolves.

## Overview

Vulpes is a nominally typed programming language that supports both interpretation and ahead-of-time compilation. It is designed to be elegant, clean, and eventually fast—balancing ease of prototyping with high runtime performance and a smooth developer experience.

Vulpes targets systems programming, aiming to offer the safety guarantees of languages like Rust, but without the verbosity and strictness of a borrow checker. If you can write it, it should just work—this is the guiding philosophy.

The name comes from *Vulpes vulpes*, the scientific name for the red fox.

## Design Goals

- **Simplicity**  
  Vulpes avoids unnecessary complexity. It provides a small, consistent set of features that compose well and prioritize readability and clarity.

- **Nominal Typing**  
  Types in Vulpes are distinct by name, not by structure. This reinforces intentional design and prevents accidental compatibility between unrelated types.

- **Algebraic Data Types (ADTs)**  
  Structs and tagged unions form the backbone of the type system, enabling expressive modeling without special-case mechanisms.

- **Generics Done Right**  
  Vulpes supports parametric polymorphism in a clean and predictable way—without falling into the trap of overly complex templates or trait-bound contortions.

- **“It Just Works”**  
  The guiding philosophy is that valid-looking code should behave as expected without endless negotiation with the compiler. If it compiles, it runs.

- **No Borrow Checker, No Footguns**  
  Vulpes does not use a borrow checker, but it also avoids common pitfalls of manual memory management. The goal is safe and intuitive ownership without needing a PhD in lifetimes.

- **Optimized for Prototyping and Performance**  
  Vulpes supports fast iteration through an interpreter and scalable performance through AOT compilation. Prototyping and production are part of the same workflow.

- **Readable Error Messages**  
  Error messages should teach, not punish. Vulpes aims to provide clear, concise diagnostics that guide rather than frustrate.

- **Zero-Cost Abstractions**  
  High-level language features are designed to compile down to efficient low-level code without overhead—what you don’t use, you don’t pay for.