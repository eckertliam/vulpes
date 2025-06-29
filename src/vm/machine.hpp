#pragma once

#include "arena.hpp"
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

        /// Pop a length from the stack and then pop that many chars from the stack
        /// and construct a string from them
        /// push the string pointer to the stack
        String* make_string();
        /// Pop a bool for whether there are initial values
        /// If true then pop a length and then pop that many values from the stack
        /// and construct a list from them
        /// push the list pointer to the stack
        List* make_list();
        /// Pop a length from the stack and then pop that many values from the stack
        /// and construct a tuple from them
        /// push the tuple pointer to the stack
        Tuple* make_tuple();
        /// Pop a bool for whether there are initial values
        /// If true then pop a length and then pop twice that many values from the stack
        /// Every two value are a key and a value
        /// and construct a table from them
        /// push the table pointer to the stack
        Table* make_table();

      private:
        std::vector<Function> functions;
        std::vector<CallFrame> call_frames;
        std::vector<Value> stack;
        Arena arena;
        size_t sp;
        size_t ip;
        Function* current_function;
    };
} // namespace vulpes::vm