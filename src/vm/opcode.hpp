#pragma once

#include <cstdint>

namespace vulpes::vm {
    enum class OpCode : uint8_t {
        // Stack
        // Flag: empty
        // Imm: empty
        Nop,
        Pop,
        Dup,
        Swap,

        // Arithmetic
        // Flag: Type
        // Imm: empty
        Add,
        Sub,
        Mul,
        Div,
        Mod,

        // Comparison
        // Flag: Type
        // Imm: empty
        Eq,
        Neq,
        Lt,
        Gt,
        Lte,
        Gte,

        // Control Flow
        // Flag: empty
        // Imm: offset from current instruction
        Jump,
        JumpIf,
        JumpIfNot,

        // Const pool, function level constants
        // Loads a constant from the const pool and pushes it to the stack
        // Flag: empty
        // Imm: constant index
        LoadConst,

        // Function handling
        Call,   // Flag: empty, Imm: function index
        Return, // Flag: empty, Imm: empty

        // Object Instantiation
        // Flag: empty
        // Imm: empty
        MakeString,
        MakeList,
        MakeTuple,
        MakeTable,

        // VM
        Halt, // Flag: empty, Imm: empty
    };
} // namespace vulpes::vm