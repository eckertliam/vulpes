#pragma once

#include "base.hpp"
#include "vm/instruction.hpp"

#include <cstdint>
#include <string>

namespace vulpes::vm::object {
class Function : public BaseObject {
 private:
  std::string name_;
  size_t arity_;
  std::vector<Instruction> instructions_;
  std::vector<BaseObject*> constants_;
  std::vector<BaseObject*> locals_;

 public:
  Function(const std::string& name, size_t arity,
           const std::vector<Instruction>& instructions)
      : BaseObject(ObjectType::Function),
        name_(name),
        arity_(arity),
        instructions_(instructions) {}

  // BUILDER FUNCTIONS
  Function(const std::string& name, size_t arity);

  void addInstruction(const Instruction& instruction);

  uint32_t addConstant(BaseObject* constant);

  // END BUILDER FUNCTIONS

  ~Function() = default;

  size_t getArity() const { return arity_; }

  std::string name() const { return name_; }

  void trace(const std::function<void(BaseObject*)>& visit) override;

  BaseObject* getConstant(size_t index) const;

  BaseObject* getLocal(size_t index) const;

  uint32_t addLocal(BaseObject* value);

  void addArg(BaseObject* arg);

  // TODO: add methods for building functions from the frontend

  BaseObject* add(Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* sub(Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* mul(Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* div(Machine& machine, BaseObject* other) override {
    return nullptr;
  }

  BaseObject* mod(Machine& machine, BaseObject* other) override {
    return nullptr;
  }
};
}  // namespace vulpes::vm::object