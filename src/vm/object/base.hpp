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
  Char,
  Boolean,
  Null,
  Object,
  Vec,
  Map,
  Upvalue,
  Function,
  NativeFunction,
};

static constexpr const char* ObjectTypeNames[] = {
    "Integer", "Float",    "String",         "Char",     "Boolean",
    "Null",    "Object",   "Vec",            "Map",      "Upvalue",
    "Function", "NativeFunction",
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
  virtual BaseObject* pow(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* shl(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* shr(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* bit_and(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* bit_xor(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* bit_or(vulpes::vm::Machine& machine, BaseObject* other) = 0;

  // truthiness — used by if/while/!/&&/||
  [[nodiscard]] virtual bool isTruthy() const = 0;
  // unary negate — returns nullptr if not supported
  virtual BaseObject* negate(vulpes::vm::Machine& machine) = 0;

  // comparison — returns a Boolean allocated on the machine
  virtual BaseObject* eq(vulpes::vm::Machine& machine, BaseObject* other) = 0;
  virtual BaseObject* lt(vulpes::vm::Machine& machine, BaseObject* other) = 0;
};
}  // namespace vulpes::vm::object
