#pragma once

#include "../frontend/location.hpp"

#include <cstdint>
#include <optional>

namespace vulpes::vm {
using Location = vulpes::frontend::Location;

enum class Opcode : uint8_t {
  // End the program
  // Imm: none
  EOP,
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
  // Imm: none
  STORE_LOCAL,
  // Load a local variable
  // Imm: local index
  LOAD_LOCAL,
  // Call a function
  // Imm: none
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
  // Add two values
  // Imm: none
  ADD,
  // Subtract two values
  // Imm: none
  SUB,
  // Multiply two values
  // Imm: none
  MUL,
  // Divide two values
  // Imm: none
  DIV,
  // Modulo two values
  // Imm: none
  MOD,
  // Pop a value from the stack and discard it
  // Imm: none
  POP,
  // Comparison operators — pop two values, push Boolean result
  // Unary operators
  NEGATE,
  NOT,
  // Control flow
  // Imm: instruction index to jump to
  JUMP,
  // Pop value, jump if falsy
  // Imm: instruction index to jump to
  JUMP_IF_FALSE,
  // Power
  POW,
  // Bitwise operators
  SHL,
  SHR,
  BIT_AND,
  BIT_XOR,
  BIT_OR,
  // Field access — imm is constant index holding the field name string
  GET_FIELD,
  SET_FIELD,
  // Index access — pop index and object, push result
  INDEX_GET,
  INDEX_SET,
  // Upvalue access for closures
  LOAD_UPVALUE,
  STORE_UPVALUE,
  // Create a closure: pop function, attach upvalues from current frame
  // imm = number of upvalue descriptors that follow
  MAKE_CLOSURE,
  // Comparison operators — pop two values, push Boolean result
  EQ,
  NEQ,
  LT,
  GT,
  LTE,
  GTE,
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
