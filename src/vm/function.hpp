#pragma once

#include "instruction.hpp"
#include "value.hpp"

#include <vector>

namespace vulpes::vm {
    struct Function {
        std::vector<Instruction> instructions;
        std::vector<Value> constants;
        size_t arity;
        size_t call_count;

        Function(std::vector<Instruction> instructions, std::vector<Value> constants, size_t arity)
            : instructions(instructions), constants(constants), arity(arity), call_count(0) {}
    };
} // namespace vulpes::vm