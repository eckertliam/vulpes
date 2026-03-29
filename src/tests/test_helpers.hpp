#pragma once

#include <iostream>
#include <sstream>
#include <string>

#include "codegen/bytecode_emitter.hpp"
#include "frontend/lexer.hpp"
#include "frontend/parser.hpp"
#include "vm/machine.hpp"
#include "vm/object/base.hpp"

namespace vulpes::test {

// Runs the full pipeline and captures stdout.
inline std::string run_capture(const std::string& source) {
  std::ostringstream captured;
  auto* old_buf = std::cout.rdbuf(captured.rdbuf());

  frontend::Lexer lexer(source);
  frontend::Parser parser(lexer);
  auto statements = parser.parse();

  vm::Machine machine;
  machine.registerBuiltins();

  codegen::BytecodeEmitter emitter(machine);
  auto* entry = emitter.emit_program(statements);

  machine.pushCallFrame(entry);
  machine.run();

  std::cout.rdbuf(old_buf);
  return captured.str();
}

}  // namespace vulpes::test
