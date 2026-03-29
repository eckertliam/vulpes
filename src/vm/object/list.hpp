#pragma once

#include "base.hpp"
#include "boolean.hpp"
#include "../machine.hpp"

#include <string>

namespace vulpes::vm::object {

// A singly-linked list node. The list is formed by chaining nodes.
// An empty list is represented by null.
class ListNode final : public BaseObject {
 private:
  BaseObject* head_;
  BaseObject* tail_;  // either another ListNode or Null for end

 public:
  ListNode(BaseObject* head, BaseObject* tail)
      : BaseObject(ObjectType::List), head_(head), tail_(tail) {}

  [[nodiscard]] BaseObject* head() const { return head_; }
  [[nodiscard]] BaseObject* tail() const { return tail_; }
  void setTail(BaseObject* tail) { tail_ = tail; }

  [[nodiscard]] size_t length() const {
    size_t len = 1;
    auto* current = tail_;
    while (current && current->type() == ObjectType::List) {
      len++;
      current = dynamic_cast<const ListNode*>(current)->tail_;
    }
    return len;
  }

  void trace(const std::function<void(BaseObject*)>& visit) override {
    if (head_) visit(head_);
    if (tail_) visit(tail_);
  }

  [[nodiscard]] std::string toString() const override {
    std::string result = "list(";
    result += head_ ? head_->toString() : "null";
    auto* current = tail_;
    while (current && current->type() == ObjectType::List) {
      auto* node = dynamic_cast<const ListNode*>(current);
      result += ", ";
      result += node->head_ ? node->head_->toString() : "null";
      current = node->tail_;
    }
    result += ")";
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

  [[nodiscard]] bool isTruthy() const override { return true; }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }
  BaseObject* lt([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
};

}  // namespace vulpes::vm::object
