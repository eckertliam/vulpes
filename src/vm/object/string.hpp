#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "../machine.hpp"

#include <string>
#include <utility>

namespace vulpes::vm::object {

class String final : public BaseObject {
 private:
  std::string value_;

 public:
  explicit String(std::string value)
      : BaseObject(ObjectType::String), value_(std::move(value)) {}

  [[nodiscard]] const std::string& value() const { return value_; }

  void trace(const std::function<void(BaseObject*)>& /*visit*/) override {}

  [[nodiscard]] std::string toString() const override { return value_; }

  BaseObject* add(vulpes::vm::Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::String) {
      return machine.allocate<String>(value_ + dynamic_cast<String*>(other)->value());
    }
    return nullptr;
  }
  BaseObject* sub([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* mul([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* div([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* mod([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  BaseObject* eq(vulpes::vm::Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::String) {
      return machine.allocate<Boolean>(value_ == dynamic_cast<String*>(other)->value());
    }
    return machine.allocate<Boolean>(false);
  }

  [[nodiscard]] bool isTruthy() const override { return !value_.empty(); }
  BaseObject* negate([[maybe_unused]] vulpes::vm::Machine& machine) override { return nullptr; }

  BaseObject* lt(vulpes::vm::Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::String) {
      return machine.allocate<Boolean>(value_ < dynamic_cast<String*>(other)->value());
    }
    return nullptr;
  }
};

}  // namespace vulpes::vm::object
