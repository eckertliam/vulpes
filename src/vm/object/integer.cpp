#include "integer.hpp"
#include "boolean.hpp"
#include "float.hpp"
#include "../machine.hpp"

#include <cmath>

namespace vulpes::vm::object {

BaseObject* Integer::add(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ +
                                       dynamic_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(static_cast<double>(value_) +
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

BaseObject* Integer::sub(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ -
                                       dynamic_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(static_cast<double>(value_) -
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

BaseObject* Integer::mul(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ *
                                       dynamic_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(static_cast<double>(value_) *
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

BaseObject* Integer::div(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Integer>(value_ /
                                       dynamic_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Float>(static_cast<double>(value_) /
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

BaseObject* Integer::mod(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() != ObjectType::Integer) {
    return nullptr;
  }
  return machine.allocate<Integer>(value_ %
                                   dynamic_cast<Integer*>(other)->value_);
}

BaseObject* Integer::pow(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() == ObjectType::Integer) {
    auto exp = dynamic_cast<Integer*>(other)->value_;
    int64_t result = 1;
    int64_t base = value_;
    bool negative_exp = exp < 0;
    if (negative_exp) exp = -exp;
    while (exp > 0) {
      if (exp & 1) result *= base;
      base *= base;
      exp >>= 1;
    }
    if (negative_exp) {
      return machine.allocate<Float>(1.0 / static_cast<double>(result));
    }
    return machine.allocate<Integer>(result);
  }
  if (other->type() == ObjectType::Float) {
    return machine.allocate<Float>(
        std::pow(static_cast<double>(value_), dynamic_cast<Float*>(other)->value()));
  }
  return nullptr;
}

BaseObject* Integer::shl(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() != ObjectType::Integer) return nullptr;
  return machine.allocate<Integer>(value_ << dynamic_cast<Integer*>(other)->value_);
}

BaseObject* Integer::shr(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() != ObjectType::Integer) return nullptr;
  return machine.allocate<Integer>(value_ >> dynamic_cast<Integer*>(other)->value_);
}

BaseObject* Integer::bit_and(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() != ObjectType::Integer) return nullptr;
  return machine.allocate<Integer>(value_ & dynamic_cast<Integer*>(other)->value_);
}

BaseObject* Integer::bit_xor(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() != ObjectType::Integer) return nullptr;
  return machine.allocate<Integer>(value_ ^ dynamic_cast<Integer*>(other)->value_);
}

BaseObject* Integer::bit_or(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() != ObjectType::Integer) return nullptr;
  return machine.allocate<Integer>(value_ | dynamic_cast<Integer*>(other)->value_);
}

BaseObject* Integer::eq(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Boolean>(value_ ==
                                       dynamic_cast<Integer*>(other)->value_);
    case ObjectType::Float: {
      auto diff = static_cast<double>(value_) - dynamic_cast<Float*>(other)->value();
      return machine.allocate<Boolean>(diff <= 0.0 && diff >= 0.0);
    }
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return machine.allocate<Boolean>(false);
  }
}

BaseObject* Integer::lt(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Integer:
      return machine.allocate<Boolean>(value_ <
                                       dynamic_cast<Integer*>(other)->value_);
    case ObjectType::Float:
      return machine.allocate<Boolean>(static_cast<double>(value_) <
                                       dynamic_cast<Float*>(other)->value());
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

bool Integer::isTruthy() const { return value_ != 0; }

BaseObject* Integer::negate(vulpes::vm::Machine& machine) {
  return machine.allocate<Integer>(-value_);
}

}  // namespace vulpes::vm::object
