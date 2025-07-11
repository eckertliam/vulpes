#pragma once

#include <functional>

namespace vulpes::vm::object {

enum class ObjectType : uint8_t {
  Integer,
  Float,
  String,
  Boolean,
  Null,
  Object,
  Function,
};

static constexpr const char* ObjectTypeNames[] = {
    "Integer", "Float", "String", "Boolean", "Null", "Object", "Function",
};

class BaseObject {
 private:
  bool marked_;
  ObjectType type_;

 public:
  BaseObject(ObjectType type) : marked_(false), type_(type) {}

  bool isMarked() const { return marked_; }
  void mark() { marked_ = true; }
  void unmark() { marked_ = false; }
  ObjectType type() const { return type_; }

  virtual ~BaseObject() = default;
  virtual void trace(const std::function<void(BaseObject*)>& visit) = 0;
  virtual std::string toString() const = 0;

  // TODO: add primitives such as add, sub, mul, div, etc.
};
}  // namespace vulpes::vm::object