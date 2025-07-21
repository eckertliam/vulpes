#pragma once

#include "base.hpp"

#include <string>
namespace vulpes::vm::object {
class Integer final : public BaseObject {
 private:
  int64_t value_;

 public:
  explicit Integer(int64_t value) : BaseObject(ObjectType::Integer), value_(value) {}

  ~Integer() = default;

  [[nodiscard]] int64_t value() const { return value_; }

  /* Nothing to trace */
  void trace(const std::function<void(BaseObject*)>& visit) override {}

  [[nodiscard]] std::string toString() const override { return std::to_string(value_); }

  BaseObject* add(vulpes::vm::Machine& machine, BaseObject* other) override;
  BaseObject* sub(vulpes::vm::Machine& machine, BaseObject* other) override;
  BaseObject* mul(vulpes::vm::Machine& machine, BaseObject* other) override;
  BaseObject* div(vulpes::vm::Machine& machine, BaseObject* other) override;
  BaseObject* mod(vulpes::vm::Machine& machine, BaseObject* other) override;
};
}  // namespace vulpes::vm::object