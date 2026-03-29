#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "codegen/bytecode_emitter.hpp"
#include "frontend/lexer.hpp"
#include "frontend/parser.hpp"
#include "vm/machine.hpp"

int main(int argc, char* argv[]) {
  std::string source;

  if (argc > 1) {
    std::ifstream file(argv[1]);
    if (!file.is_open()) {
      std::cerr << "Error: could not open file '" << argv[1] << "'\n";
      return 1;
    }
    std::stringstream ss;
    ss << file.rdbuf();
    source = ss.str();
  } else {
    std::cerr << "Usage: vulpes <source-file>\n";
    return 1;
  }

  vulpes::frontend::Lexer lexer(source);
  vulpes::frontend::Parser parser(lexer);
  auto statements = parser.parse();

  vulpes::vm::Machine machine;
  machine.registerBuiltins();

  vulpes::codegen::BytecodeEmitter emitter(machine);
  auto* entry = emitter.emit_program(statements);

  machine.pushCallFrame(entry);
  machine.run();

  return 0;
}
