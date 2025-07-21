#pragma once

#include <functional>

namespace vulpes::vm {
class Machine;
}

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
  explicit BaseObject(ObjectType type) : marked_(false), type_(type) {}

  [[nodiscard]] bool isMarked() const { return marked_; }
  void mark() { marked_ = true; }
  void unmark() { marked_ = false; }
  ObjectType type() const { return type_; }

  virtual ~BaseObject() = default;
  virtual void trace(const std::function<void(BaseObject*)>& visit) = 0;
  virtual std::string toString() const = 0;

  // arithmetic operations
  virtual BaseObject* add(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* sub(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* mul(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* div(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* mod(vulpes::vm::Machine& machine, BaseObject* other) = 0;

  // TODO: add comparison operations
  // TODO: add logical operations
};
}  // namespace vulpes::vm::object