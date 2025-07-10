#pragma once

#include "base.hpp"
#include "vm/instruction.hpp"

#include <string>

namespace vulpes::vm::object {
    class Function : public BaseObject {
      private:
        std::string name_;
        size_t arity_;
        std::vector<BaseObject*> args_;
        std::vector<Instruction> instructions_;
        std::vector<BaseObject*> constants_;
        std::vector<BaseObject*> locals_;

      public:
        Function(const std::string& name, size_t arity,
                 const std::vector<Instruction>& instructions)
            : BaseObject(ObjectType::Function), name_(name), arity_(arity),
              instructions_(instructions) {
            args_.reserve(arity);
        }

        ~Function() = default;

        std::string name() const { return name_; }

        void trace(const std::function<void(BaseObject*)>& visit) override;

        // TODO: add methods for building functions during compilation
        // TODO: add methods for executing functions during runtime
    };
} // namespace vulpes::vm::object