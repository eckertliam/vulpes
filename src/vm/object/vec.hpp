#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "integer.hpp"
#include "../machine.hpp"

#include <string>
#include <vector>

namespace vulpes::vm::object {

class Vec final : public BaseObject {
 private:
  std::vector<BaseObject*> elements_;

 public:
  Vec() : BaseObject(ObjectType::Vec) {}

  explicit Vec(std::vector<BaseObject*> elements)
      : BaseObject(ObjectType::Vec), elements_(std::move(elements)) {}

  [[nodiscard]] size_t length() const { return elements_.size(); }

  void push(BaseObject* value) { elements_.push_back(value); }

  BaseObject* pop() {
    if (elements_.empty()) {
      throw std::runtime_error("IndexOutOfBounds: pop on empty vec");
    }
    auto* val = elements_.back();
    elements_.pop_back();
    return val;
  }

  BaseObject* get(int64_t index) const {
    if (index < 0 || static_cast<size_t>(index) >= elements_.size()) {
      throw std::runtime_error("IndexOutOfBounds");
    }
    return elements_[static_cast<size_t>(index)];
  }

  void set(int64_t index, BaseObject* value) {
    if (index < 0 || static_cast<size_t>(index) >= elements_.size()) {
      throw std::runtime_error("IndexOutOfBounds");
    }
    elements_[static_cast<size_t>(index)] = value;
  }

  void trace(const std::function<void(BaseObject*)>& visit) override {
    for (auto* elem : elements_) {
      visit(elem);
    }
  }

  [[nodiscard]] std::string toString() const override {
    std::string result = "[";
    for (size_t i = 0; i < elements_.size(); i++) {
      if (i > 0) result += ", ";
      result += elements_[i]->toString();
    }
    result += "]";
    return result;
  }

  BaseObject* add(Machine& machine, BaseObject* other) override {
    if (other->type() == ObjectType::Vec) {
      auto* other_vec = dynamic_cast<Vec*>(other);
      std::vector<BaseObject*> combined = elements_;
      combined.insert(combined.end(), other_vec->elements_.begin(), other_vec->elements_.end());
      return machine.allocate<Vec>(std::move(combined));
    }
    return nullptr;
  }
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

  [[nodiscard]] bool isTruthy() const override { return !elements_.empty(); }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }

  BaseObject* lt([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
};

}  // namespace vulpes::vm::object
