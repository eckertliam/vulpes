#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "../machine.hpp"


namespace vulpes::vm::object {

// TODO: instantiate a single static null instance

class Null : public BaseObject {
 public:
  Null() : BaseObject(ObjectType::Null) {}

  std::string toString() const override { return "null"; }

  ~Null() override = default;

  void trace(const std::function<void(BaseObject*)>& visit) override { visit(this); }

  BaseObject* add([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override {
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
  BaseObject* pow([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shl([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shr([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_and([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_xor([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_or([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }

  BaseObject* eq(vulpes::vm::Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Null) {
      return machine.allocate<Boolean>(true);
    }
    return machine.allocate<Boolean>(false);
  }

  [[nodiscard]] bool isTruthy() const override { return false; }
  BaseObject* negate([[maybe_unused]] vulpes::vm::Machine& machine) override { return nullptr; }

  BaseObject* lt([[maybe_unused]] vulpes::vm::Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
};

}  // namespace vulpes::vm::object
