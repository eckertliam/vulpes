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

  // Set base directory for module imports
  std::string source_path = argv[1];
  auto last_slash = source_path.find_last_of('/');
  if (last_slash != std::string::npos) {
    machine.setBaseDir(source_path.substr(0, last_slash));
  } else {
    machine.setBaseDir(".");
  }

  // Set up module loader
  machine.setModuleLoader([](vulpes::vm::Machine& m, const std::string& module_path) -> bool {
    std::string full_path = m.getBaseDir() + "/" + module_path + ".vx";

    if (m.isModuleLoaded(full_path)) return true;

    if (m.isModuleLoading(full_path)) {
      throw std::runtime_error("ImportCycle: circular dependency detected for module '" + module_path + "'");
    }

    std::ifstream file(full_path);
    if (!file.is_open()) {
      throw std::runtime_error("ImportError: could not open module '" + module_path + "' at " + full_path);
    }
    std::stringstream ss;
    ss << file.rdbuf();
    std::string mod_source = ss.str();

    m.markModuleLoading(full_path);

    vulpes::frontend::Lexer mod_lexer(mod_source);
    vulpes::frontend::Parser mod_parser(mod_lexer);
    auto mod_statements = mod_parser.parse();

    vulpes::codegen::BytecodeEmitter mod_emitter(m);
    auto* mod_entry = mod_emitter.emit_program(mod_statements);
    m.pushCallFrame(mod_entry);
    m.run();

    m.unmarkModuleLoading(full_path);
    m.markModuleLoaded(full_path);
    return true;
  });

  vulpes::codegen::BytecodeEmitter emitter(machine);
  auto* entry = emitter.emit_program(statements);

  machine.pushCallFrame(entry);
  machine.run();

  return 0;
}
