#pragma once

#include "base.hpp"


namespace vulpes::vm::object {

// TODO: instantiate a single static null instance

class Null : public BaseObject {
 public:
  Null() : BaseObject(ObjectType::Null) {}

  std::string toString() const override { return "null"; }

  void trace(const std::function<void(BaseObject*)>& visit) override { visit(this); }

  BaseObject* add(vulpes::vm::Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* sub(vulpes::vm::Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* mul(vulpes::vm::Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* div(vulpes::vm::Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* mod(vulpes::vm::Machine& machine, BaseObject* other) override {
    return nullptr;
  }
};

}  // namespace vulpes::vm::object