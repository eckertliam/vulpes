#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "../machine.hpp"

#include <string>
#include <unordered_map>

namespace vulpes::vm::object {

class Instance final : public BaseObject {
 private:
  std::string class_name_;
  std::unordered_map<std::string, BaseObject*> fields_;

 public:
  explicit Instance(std::string class_name)
      : BaseObject(ObjectType::Object), class_name_(std::move(class_name)) {}

  [[nodiscard]] const std::string& className() const { return class_name_; }

  void setField(const std::string& name, BaseObject* value) {
    fields_[name] = value;
  }

  [[nodiscard]] BaseObject* getField(const std::string& name) const {
    auto it = fields_.find(name);
    if (it != fields_.end()) {
      return it->second;
    }
    return nullptr;
  }

  void trace(const std::function<void(BaseObject*)>& visit) override {
    for (auto& [_, value] : fields_) {
      visit(value);
    }
  }

  [[nodiscard]] std::string toString() const override {
    return class_name_ + " instance";
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

  BaseObject* eq(Machine& machine, BaseObject* other) override {
    return machine.allocate<Boolean>(this == other);
  }

  [[nodiscard]] bool isTruthy() const override { return true; }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }

  BaseObject* lt([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
};

}  // namespace vulpes::vm::object
