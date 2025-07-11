#include "integer.hpp"
#include "float.hpp"
#include "vm/machine.hpp"

namespace vulpes::vm::object {

BaseObject* Integer::add(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ +
                                       static_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(value_ +
                                     static_cast<Float*>(other)->value());
    default:
      return nullptr;
  }
}

BaseObject* Integer::sub(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ -
                                       static_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(value_ -
                                     static_cast<Float*>(other)->value());
    default:
      return nullptr;
  }
}

BaseObject* Integer::mul(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ *
                                       static_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(value_ *
                                     static_cast<Float*>(other)->value());
    default:
      return nullptr;
  }
}

BaseObject* Integer::div(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ /
                                       static_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(value_ /
                                     static_cast<Float*>(other)->value());
    default:
      return nullptr;
  }
}

BaseObject* Integer::mod(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() != ObjectType::Integer) {
    return nullptr;
  }
  return machine.allocate<Integer>(value_ %
                                   static_cast<Integer*>(other)->value_);
}

}  // namespace vulpes::vm::object