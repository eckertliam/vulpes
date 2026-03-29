#pragma once

#include "base.hpp"

namespace vulpes::vm::object {

// An Upvalue is a shared mutable cell used for closure captures.
// Multiple closures (and the enclosing scope) can share the same Upvalue
// so that mutations are reflected everywhere (capture by reference).
class Upvalue final : public BaseObject {
 private:
  BaseObject* value_;

 public:
  explicit Upvalue(BaseObject* value)
      : BaseObject(ObjectType::Upvalue), value_(value) {}

  [[nodiscard]] BaseObject* get() const { return value_; }
  void set(BaseObject* value) { value_ = value; }

  void trace(const std::function<void(BaseObject*)>& visit) override {
    if (value_) visit(value_);
  }

  [[nodiscard]] std::string toString() const override {
    return "upvalue(" + (value_ ? value_->toString() : "null") + ")";
  }

  BaseObject* add([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* sub([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* mul([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* div([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* mod([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* pow([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shl([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shr([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_and([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_xor([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_or([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* eq([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  [[nodiscard]] bool isTruthy() const override { return value_ && value_->isTruthy(); }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }
  BaseObject* lt([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
};

}  // namespace vulpes::vm::object
