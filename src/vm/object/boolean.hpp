#pragma once

#include "base.hpp"

#include <string>

namespace vulpes::vm::object {

class Boolean final : public BaseObject {
 private:
  bool value_;

 public:
  explicit Boolean(bool value)
      : BaseObject(ObjectType::Boolean), value_(value) {}

  [[nodiscard]] bool value() const { return value_; }

  void trace(const std::function<void(BaseObject*)>& /*visit*/) override {}

  [[nodiscard]] std::string toString() const override {
    return value_ ? "true" : "false";
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
};

}  // namespace vulpes::vm::object
