#pragma once

#include <cstdint>

namespace vulpes::vm {
    enum class OpCode : uint8_t {
        // Stack
        // Flag: empty
        // Imm: empty
        Nop,
        Push,
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
        // Flag: empty
        // Imm: constant index
        LoadConst,

        // Global variables
        // Flag: empty
        // Imm: global index
        LoadGlobal,
        StoreGlobal,

        // Local variables
        // Flag: empty
        // Imm: local index
        LoadLocal,
        StoreLocal,

        // Function handling
        Call,   // Flag: empty, Imm: function index
        Return, // Flag: empty, Imm: empty

        // VM
        Halt, // Flag: empty, Imm: empty
    };
} // namespace vulpes::vm