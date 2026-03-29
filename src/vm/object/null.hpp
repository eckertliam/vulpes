#pragma once

#include "base.hpp"


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
};

}  // namespace vulpes::vm::object
