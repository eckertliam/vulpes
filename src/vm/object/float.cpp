#include "float.hpp"
#include "integer.hpp"
#include "../machine.hpp"

namespace vulpes::vm::object {

BaseObject* Float::add(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float:
      return machine.allocate<Float>(value_ +
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::Integer:
      return machine.allocate<Float>(value_ +
                                     static_cast<double>(dynamic_cast<Integer*>(other)->value()));
    default:
      return nullptr;
  }
}

BaseObject* Float::sub(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float:
      return machine.allocate<Float>(value_ -
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::Integer:
      return machine.allocate<Float>(value_ -
                                     static_cast<double>(dynamic_cast<Integer*>(other)->value()));
    default:
      return nullptr;
  }
}

BaseObject* Float::mul(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float:
      return machine.allocate<Float>(value_ *
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::Integer:
      return machine.allocate<Float>(value_ *
                                     static_cast<double>(dynamic_cast<Integer*>((other))->value()));
    default:
      return nullptr;
  }
}

BaseObject* Float::div(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float:
      return machine.allocate<Float>(value_ /
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::Integer:
      return machine.allocate<Float>(value_ /
                                     static_cast<double>(dynamic_cast<Integer*>(other)->value()));
    default:
      return nullptr;
  }
}

BaseObject* Float::mod(vulpes::vm::Machine& machine, BaseObject* other) {
  return nullptr;
}

}  // namespace vulpes::vm::object