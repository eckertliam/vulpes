#include "function.hpp"

namespace vulpes::vm::object {
void Function::trace(const std::function<void(BaseObject*)>& visit) {
  visit(this);
  for (auto* constant : constants_)
    visit(constant);
  for (auto* local : locals_)
    visit(local);
}

BaseObject* Function::getConstant(size_t index) const {
  if (index >= constants_.size()) {
    return nullptr;
  }
  return constants_[index];
}

BaseObject* Function::getLocal(size_t index) const {
  if (index >= locals_.size()) {
    return nullptr;
  }
  return locals_[index];
}

uint32_t Function::addLocal(BaseObject* value) {
  locals_.push_back(value);
  return locals_.size() - 1;
}
}  // namespace vulpes::vm::object