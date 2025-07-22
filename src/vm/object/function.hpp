#pragma once

#include "base.hpp"
#include "../instruction.hpp"

#include <string>
#include <utility>

namespace vulpes::vm::object {
class Function : public BaseObject {
 private:
  std::string name_;
  size_t arity_;
  std::vector<Instruction> instructions_;
  std::vector<BaseObject*> constants_;
  std::vector<BaseObject*> locals_;

 public:
  Function(std::string  name, const size_t arity,
           const std::vector<Instruction>& instructions)
      : BaseObject(ObjectType::Function),
        name_(std::move(name)),
        arity_(arity),
        instructions_(instructions) {}

  // BUILDER FUNCTIONS
  Function(std::string name, const size_t arity)
      : BaseObject(ObjectType::Function), name_(std::move(name)), arity_(arity) {}

  void addInstruction(const Instruction& instruction) { instructions_.push_back(instruction); };

  uint32_t addConstant(BaseObject* constant) {
    constants_.push_back(constant);
    return constants_.size() - 1;
  }

  // END BUILDER FUNCTIONS

  ~Function() override = default;

  [[nodiscard]] std::string toString() const override {
    return "Function(" + name_ + ")";
  }

  [[nodiscard]] size_t getArity() const { return arity_; }

  [[nodiscard]] std::string name() const { return name_; }

  void trace(const std::function<void(BaseObject*)>& visit) override;

  [[nodiscard]] BaseObject* getConstant(uint32_t index) const;

  [[nodiscard]] BaseObject* getLocal(uint32_t index) const;

  uint32_t addLocal(BaseObject* value) {
    locals_.push_back(value);
    return locals_.size() - 1;
  }


  uint32_t addArg(BaseObject* arg) {
    locals_.push_back(arg);
    return locals_.size() - 1;
  }

  Instruction& getInstruction(const size_t index) { return instructions_[index]; }

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