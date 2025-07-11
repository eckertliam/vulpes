#pragma once

#include "base.hpp"

#include <string>

namespace vulpes::vm::object {
class Float : public BaseObject {
 private:
  double value_;

 public:
  Float(double value) : BaseObject(ObjectType::Float), value_(value) {}

  ~Float() = default;

  double value() const { return value_; }

  /* Nothing to trace */
  void trace(const std::function<void(BaseObject*)>& visit) override {}

  std::string toString() const override { return std::to_string(value_); }
};
}  // namespace vulpes::vm::object