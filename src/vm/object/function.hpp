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
  std::vector<BaseObject*> upvalues_;  // captured upvalue cells

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


  Function(std::string_view name, const size_t arity) 
      : BaseObject(ObjectType::Function), name_(name), arity_(arity) {}
      
  void addInstruction(const Instruction& instruction) { instructions_.push_back(instruction); }

  [[nodiscard]] uint32_t instructionCount() const {
    return static_cast<uint32_t>(instructions_.size());
  }

  void patchInstruction(uint32_t index, uint32_t new_imm) {
    instructions_[index].imm = new_imm;
  }

  uint32_t addConstant(BaseObject* constant) {
    constants_.push_back(constant);
    return static_cast<uint32_t>(constants_.size() - 1);
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
    return static_cast<uint32_t>(locals_.size() - 1);
  }

  void setLocal(uint32_t index, BaseObject* value) {
    if (index >= locals_.size()) {
      locals_.resize(index + 1, nullptr);
    }
    locals_[index] = value;
  }

  uint32_t addArg(BaseObject* arg) {
    locals_.push_back(arg);
    return static_cast<uint32_t>(locals_.size() - 1);
  }

  Instruction& getInstruction(const size_t index) { return instructions_[index]; }

  // Upvalue support for closures
  uint32_t addUpvalue(BaseObject* upvalue) {
    upvalues_.push_back(upvalue);
    return static_cast<uint32_t>(upvalues_.size() - 1);
  }

  [[nodiscard]] BaseObject* getUpvalue(uint32_t index) const {
    if (index >= upvalues_.size()) return nullptr;
    return upvalues_[index];
  }

  void setUpvalue(uint32_t index, BaseObject* value) {
    if (index >= upvalues_.size()) {
      upvalues_.resize(index + 1, nullptr);
    }
    upvalues_[index] = value;
  }

  [[nodiscard]] size_t upvalueCount() const { return upvalues_.size(); }

  BaseObject* add([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  BaseObject* sub([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  BaseObject* mul([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  BaseObject* div([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  BaseObject* mod([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
  BaseObject* pow([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shl([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* shr([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_and([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_xor([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }
  BaseObject* bit_or([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override { return nullptr; }

  BaseObject* eq([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }

  [[nodiscard]] bool isTruthy() const override { return true; }
  BaseObject* negate([[maybe_unused]] Machine& machine) override { return nullptr; }

  BaseObject* lt([[maybe_unused]] Machine& machine, [[maybe_unused]] BaseObject* other) override {
    return nullptr;
  }
};
}  // namespace vulpes::vm::object
