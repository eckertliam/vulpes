#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "integer.hpp"
#include "string.hpp"
#include "../machine.hpp"

#include <string>
#include <vector>

namespace vulpes::vm::object {

class Map final : public BaseObject {
 private:
  // Using parallel vectors for key-value pairs since BaseObject* doesn't have std::hash
  std::vector<BaseObject*> keys_;
  std::vector<BaseObject*> values_;

  int findKey(BaseObject* key, Machine& machine) const {
    for (size_t i = 0; i < keys_.size(); i++) {
      auto* eq_result = keys_[i]->eq(machine, key);
      if (eq_result && dynamic_cast<Boolean*>(eq_result)->value()) {
        return static_cast<int>(i);
      }
    }
    return -1;
  }

 public:
  Map() : BaseObject(ObjectType::Map) {}

  [[nodiscard]] size_t length() const { return keys_.size(); }

  void set(Machine& machine, BaseObject* key, BaseObject* value) {
    int idx = findKey(key, machine);
    if (idx >= 0) {
      values_[static_cast<size_t>(idx)] = value;
    } else {
      keys_.push_back(key);
      values_.push_back(value);
    }
  }

  BaseObject* get(Machine& machine, BaseObject* key) const {
    int idx = findKey(key, machine);
    if (idx >= 0) {
      return values_[static_cast<size_t>(idx)];
    }
    return nullptr;
  }

  void trace(const std::function<void(BaseObject*)>& visit) override {
    for (auto* k : keys_) visit(k);
    for (auto* v : values_) visit(v);
  }

  [[nodiscard]] std::string toString() const override {
    std::string result = "{";
    for (size_t i = 0; i < keys_.size(); i++) {
      if (i > 0) result += ", ";
      result += keys_[i]->toString() + ": " + values_[i]->toString();
    }
    result += "}";
    return result;
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

  [[nodiscard]] bool isTruthy() const override { return !keys_.empty(); }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }
  BaseObject* lt([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
};

}  // namespace vulpes::vm::object
