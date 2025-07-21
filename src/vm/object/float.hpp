#pragma once

#include "base.hpp"

#include <string>

namespace vulpes::vm::object {
class Float final : public BaseObject {
 private:
  double value_;

 public:
  explicit Float(double value) : BaseObject(ObjectType::Float), value_(value) {}

  ~Float() = default;

  [[nodiscard]] double value() const { return value_; }

  /* Nothing to trace */
  void trace(const std::function<void(BaseObject*)>& visit) override {}

  [[nodiscard]] std::string toString() const override { return std::to_string(value_); }

  BaseObject* add(Machine& machine, BaseObject* other) override;
  BaseObject* sub(Machine& machine, BaseObject* other) override;
  BaseObject* mul(Machine& machine, BaseObject* other) override;
  BaseObject* div(Machine& machine, BaseObject* other) override;
  BaseObject* mod(Machine& machine, BaseObject* other) override;
};
}  // namespace vulpes::vm::object