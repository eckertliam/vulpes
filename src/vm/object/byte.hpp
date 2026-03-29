#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "../machine.hpp"

#include <string>

namespace vulpes::vm::object {

class Byte final : public BaseObject {
 private:
  uint8_t value_;

 public:
  explicit Byte(uint8_t value) : BaseObject(ObjectType::Byte), value_(value) {}

  [[nodiscard]] uint8_t value() const { return value_; }

  void trace(const std::function<void(BaseObject*)>& /*visit*/) override {}

  [[nodiscard]] std::string toString() const override {
    return std::to_string(value_);
  }

  BaseObject* add(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ + dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }
  BaseObject* sub(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ - dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }
  BaseObject* mul(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ * dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }
  BaseObject* div(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      auto divisor = dynamic_cast<Byte*>(other)->value();
      if (divisor == 0) throw std::runtime_error("DivideByZero");
      return machine.allocate<Byte>(static_cast<uint8_t>(value_ / divisor));
    }
    return nullptr;
  }
  BaseObject* mod(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      auto divisor = dynamic_cast<Byte*>(other)->value();
      if (divisor == 0) throw std::runtime_error("DivideByZero");
      return machine.allocate<Byte>(static_cast<uint8_t>(value_ % divisor));
    }
    return nullptr;
  }
  BaseObject* pow([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shl(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ << dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }
  BaseObject* shr(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ >> dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }
  BaseObject* bit_and(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ & dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }
  BaseObject* bit_xor(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ ^ dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }
  BaseObject* bit_or(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Byte>(
          static_cast<uint8_t>(value_ | dynamic_cast<Byte*>(other)->value()));
    }
    return nullptr;
  }

  BaseObject* eq(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Boolean>(value_ == dynamic_cast<Byte*>(other)->value());
    }
    return machine.allocate<Boolean>(false);
  }

  [[nodiscard]] bool isTruthy() const override { return value_ != 0; }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }

  BaseObject* lt(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Byte) {
      return machine.allocate<Boolean>(value_ < dynamic_cast<Byte*>(other)->value());
    }
    return nullptr;
  }
};

}  // namespace vulpes::vm::object
