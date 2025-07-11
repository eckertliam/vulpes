#pragma once

#include "../frontend/location.hpp"

#include <cstdint>
#include <optional>

namespace vulpes::vm {
using Location = vulpes::frontend::Location;

enum class Opcode : uint8_t {
  // Load a global variable
  // Imm: global index
  LOAD_GLOBAL,
  // Store a global variable
  // Imm: global index
  STORE_GLOBAL,
  // Load a constant
  // Imm: constant index
  LOAD_CONST,
  // Store a local variable
  // Imm: local index
  STORE_LOCAL,
  // Load a local variable
  // Imm: local index
  LOAD_LOCAL,
  // Call a function
  // Imm: function index
  CALL,
  // Return a const from a function
  // Imm: const index
  RETURN_CONST,
  // Return a local variable
  // Imm: local index
  RETURN_LOCAL,
  // Pop a value from the stack and return it
  // Imm: none
  RETURN_VALUE,
  // Make a new class.
  // Consumes a code object and pushes a new class object to the stack
  // Code object contains the methods of the class
  // Imm: none
  // Example:
  // LOAD_CONST 0 (code object index)
  // MAKE_CLASS
  // LOAD_CONST 1 (class name)
  // STORE_NAME 0 (class name)
  MAKE_CLASS,
  // Make a new function.
  // Consumes a code object and pushes a new function object to the stack
  // Imm: none
  // Example:
  // LOAD_CONST 0 (code object index)
  // MAKE_FUNCTION
  // LOAD_CONST 1 (function name)
  // STORE_NAME 0 (function name)
  MAKE_FUNCTION,
};

// Instruction is a struct that represents a single instruction in the VM.
// It contains the opcode, the immediate value, and the source location.
struct Instruction {
  // opcode
  Opcode opcode;
  // immediate value
  uint32_t imm;
  // origin of the instruction
  std::optional<Location> src_loc = std::nullopt;

  Instruction(Opcode opcode, uint32_t imm, Location src_loc)
      : opcode(opcode), imm(imm), src_loc(src_loc) {}

  Instruction(Opcode opcode, Location src_loc)
      : opcode(opcode), imm(0), src_loc(src_loc) {}

  Instruction(Opcode opcode, uint32_t imm) : opcode(opcode), imm(imm) {}

  Instruction(Opcode opcode) : opcode(opcode), imm(0) {}
};
}  // namespace vulpes::vm