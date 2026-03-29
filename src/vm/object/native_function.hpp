#pragma once

#include "base.hpp"

#include <functional>
#include <string>
#include <utility>
#include <vector>

namespace vulpes::vm::object {

using NativeFn =
    std::function<BaseObject*(Machine&, const std::vector<BaseObject*>&)>;

class NativeFunction final : public BaseObject {
 private:
  std::string name_;
  size_t arity_;
  NativeFn function_;

 public:
  NativeFunction(std::string name, size_t arity, NativeFn function)
      : BaseObject(ObjectType::NativeFunction),
        name_(std::move(name)),
        arity_(arity),
        function_(std::move(function)) {}

  [[nodiscard]] const std::string& name() const { return name_; }
  [[nodiscard]] size_t getArity() const { return arity_; }

  BaseObject* call(Machine& machine, const std::vector<BaseObject*>& args) {
    return function_(machine, args);
  }

  void trace(const std::function<void(BaseObject*)>& /*visit*/) override {}

  [[nodiscard]] std::string toString() const override {
    return "NativeFunction(" + name_ + ")";
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
  BaseObject* pow([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shl([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shr([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_and([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_xor([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_or([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }

  BaseObject* eq([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  [[nodiscard]] bool isTruthy() const override { return true; }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }

  BaseObject* lt([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
};

}  // namespace vulpes::vm::object
