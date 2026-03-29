#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "../machine.hpp"

#include <string>

namespace vulpes::vm::object {

class Char final : public BaseObject {
 private:
  char value_;

 public:
  explicit Char(char value) : BaseObject(ObjectType::Char), value_(value) {}

  [[nodiscard]] char value() const { return value_; }

  void trace(const std::function<void(BaseObject*)>& /*visit*/) override {}

  [[nodiscard]] std::string toString() const override {
    return std::string(1, value_);
  }

  BaseObject* add([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* sub([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* mul([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* div([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* mod([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* pow([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* shl([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* shr([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* bit_and([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* bit_xor([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* bit_or([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  BaseObject* eq(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Char) {
      return machine.allocate<Boolean>(value_ == dynamic_cast<Char*>(other)->value());
    }
    return machine.allocate<Boolean>(false);
  }

  [[nodiscard]] bool isTruthy() const override { return value_ != '\0'; }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }

  BaseObject* lt(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Char) {
      return machine.allocate<Boolean>(value_ < dynamic_cast<Char*>(other)->value());
    }
    return nullptr;
  }
};

}  // namespace vulpes::vm::object
