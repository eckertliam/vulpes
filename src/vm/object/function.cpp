#include "function.hpp"

namespace vulpes::vm::object {

void Function::trace(const std::function<void(BaseObject*)>& visit) {
  visit(this);
  for (auto* constant : constants_)
    visit(constant);
  for (auto* local : locals_)
    visit(local);
}

BaseObject* Function::getConstant(const uint32_t index) const {
  const auto idx = static_cast<size_t>(index);
  if (idx >= constants_.size()) {
    return nullptr;
  }
  return constants_[idx];
}

BaseObject* Function::getLocal(const uint32_t index) const {
  if (index >= locals_.size()) {
    return nullptr;
  }
  return locals_[index];
}
}  // namespace vulpes::vm::object