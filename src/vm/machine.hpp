#pragma once

#include "call_frame.hpp"
#include "function.hpp"

namespace vulpes::vm {
    class Machine {
      public:
        Machine(std::vector<Function> functions, size_t entry_point);

        void execute_instruction(Instruction instruction);

        void call_function(size_t function_idx);

        void push_call_frame(Function* function, size_t callee_arity);

        void pop_call_frame();

        void push_value(Value value);

        Value pop_value();

        void return_value();

      private:
        std::vector<Function> functions;
        std::vector<CallFrame> call_frames;
        std::vector<Value> stack;
        std::vector<Value> heap;
        size_t sp;
        size_t ip;
        Function* current_function;
    };
} // namespace vulpes::vm