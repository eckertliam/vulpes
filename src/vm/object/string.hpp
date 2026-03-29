#pragma once

#include "base.hpp"

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
