#pragma once

#include "opcode.hpp"

#include <cstdint>

namespace vulpes::vm {
    struct Instruction {
        OpCode opcode;
        uint16_t flags;
        uint16_t imm0;
        uint16_t imm1;

        Instruction(OpCode opcode, uint16_t flags, uint16_t imm0, uint16_t imm1)
            : opcode(opcode), flags(flags), imm0(imm0), imm1(imm1) {}
    };
} // namespace vulpes::vm