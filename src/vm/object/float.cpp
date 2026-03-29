#include "float.hpp"
#include "boolean.hpp"
#include "integer.hpp"
#include "../machine.hpp"

#include <cmath>

namespace vulpes::vm::object {

BaseObject* Float::add(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float:
      return machine.allocate<Float>(value_ +
                                     dynamic_cast<Float*>(other)->value());
    case ObjectType::Integer:
      return machine.allocate<Float>(value_ +
                                     static_cast<double>(dynamic_cast<Integer*>(other)->value()));
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Vec:
    case ObjectType::Map:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
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
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Vec:
    case ObjectType::Map:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
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
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Vec:
    case ObjectType::Map:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

BaseObject* Float::div(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float: {
      auto divisor = dynamic_cast<Float*>(other)->value();
      if (divisor == 0.0) {
        throw std::runtime_error("DivideByZero");
      }
      return machine.allocate<Float>(value_ / divisor);
    }
    case ObjectType::Integer: {
      auto divisor = static_cast<double>(dynamic_cast<Integer*>(other)->value());
      if (divisor == 0.0) {
        throw std::runtime_error("DivideByZero");
      }
      return machine.allocate<Float>(value_ / divisor);
    }
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Vec:
    case ObjectType::Map:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

BaseObject* Float::mod(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() == ObjectType::Float) {
    auto divisor = dynamic_cast<Float*>(other)->value();
    if (divisor == 0.0) throw std::runtime_error("DivideByZero");
    return machine.allocate<Float>(std::fmod(value_, divisor));
  }
  if (other->type() == ObjectType::Integer) {
    auto divisor = static_cast<double>(dynamic_cast<Integer*>(other)->value());
    if (divisor == 0.0) throw std::runtime_error("DivideByZero");
    return machine.allocate<Float>(std::fmod(value_, divisor));
  }
  return nullptr;
}

BaseObject* Float::pow(vulpes::vm::Machine& machine, BaseObject* other) {
  if (other->type() == ObjectType::Float) {
    return machine.allocate<Float>(std::pow(value_, dynamic_cast<Float*>(other)->value()));
  }
  if (other->type() == ObjectType::Integer) {
    return machine.allocate<Float>(std::pow(value_, static_cast<double>(dynamic_cast<Integer*>(other)->value())));
  }
  return nullptr;
}

BaseObject* Float::shl([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) {
  return nullptr;
}

BaseObject* Float::shr([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) {
  return nullptr;
}

BaseObject* Float::bit_and([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) {
  return nullptr;
}

BaseObject* Float::bit_xor([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) {
  return nullptr;
}

BaseObject* Float::bit_or([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) {
  return nullptr;
}

BaseObject* Float::eq(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float: {
      auto diff = value_ - dynamic_cast<Float*>(other)->value();
      return machine.allocate<Boolean>(diff <= 0.0 && diff >= 0.0);
    }
    case ObjectType::Integer: {
      auto diff = value_ - static_cast<double>(dynamic_cast<Integer*>(other)->value());
      return machine.allocate<Boolean>(diff <= 0.0 && diff >= 0.0);
    }
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Vec:
    case ObjectType::Map:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return machine.allocate<Boolean>(false);
  }
}

BaseObject* Float::lt(vulpes::vm::Machine& machine, BaseObject* other) {
  switch (other->type()) {
    case ObjectType::Float:
      return machine.allocate<Boolean>(value_ <
                                       dynamic_cast<Float*>(other)->value());
    case ObjectType::Integer:
      return machine.allocate<Boolean>(value_ <
                                       static_cast<double>(dynamic_cast<Integer*>(other)->value()));
    case ObjectType::String:
    case ObjectType::Char:
    case ObjectType::Boolean:
    case ObjectType::Null:
    case ObjectType::Object:
    case ObjectType::Vec:
    case ObjectType::Map:
    case ObjectType::Function:
    case ObjectType::NativeFunction:
    default:
      return nullptr;
  }
}

bool Float::isTruthy() const { return !(value_ >= 0.0 && value_ <= 0.0); }

BaseObject* Float::negate(vulpes::vm::Machine& machine) {
  return machine.allocate<Float>(-value_);
}

}  // namespace vulpes::vm::object
