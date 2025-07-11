#include "machine.hpp"

namespace vulpes::vm {
void Machine::run() {
  // TODO: implement
}

void Machine::execute_instruction(Instruction instruction) {
  // TODO: implement
}

void Machine::gc() {
  // gather all root objects
  auto roots = getRoots();
  // mark all objects reachable from roots
  heap_.markFromRoots(roots);
  // sweep unmarked objects
  heap_.sweep();
}

std::vector<BaseObject*> Machine::getRoots() {
  std::vector<BaseObject*> roots;
  // add globals
  for (auto* global : globals_) {
    roots.push_back(global);
  }

  return roots;
}

uint32_t Machine::addGlobal(BaseObject* global) {
  globals_.push_back(global);
  return globals_.size() - 1;
}

BaseObject* Machine::getGlobal(uint32_t index) {
  // TODO: add bound checking
  return globals_[index];
}
}  // namespace vulpes::vm