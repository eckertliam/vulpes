#include "machine.hpp"

namespace vulpes::vm {
    Machine::Machine(std::vector<Function> functions, size_t entry_point) {
        functions = functions;
        call_frames.push_back(CallFrame(&functions[entry_point], 0, 0));
        current_function = &functions[entry_point];
        sp = 0;
        ip = 0;
    }

    void Machine::execute_instruction(Instruction instruction) {
        // TODO: Implement
    }

    void Machine::call_function(size_t function_idx) {
        // push the current call frame
        push_call_frame(current_function, functions[function_idx].arity);

        // set the current function to the function we are calling
        current_function = &functions[function_idx];

        // set the instruction pointer to the entry point of the function
        ip = 0;

        // increment the call count of the function
        current_function->call_count++;

        // execute the function
        while (ip < current_function->instructions.size()) {
            execute_instruction(current_function->instructions[ip]);
            ip++;
        }
    }

    void Machine::push_call_frame(Function* function, size_t callee_arity) {
        // subtract the callee arity from the stack pointer to account for the popped args
        call_frames.push_back(CallFrame(function, ip, sp - callee_arity));
    }

    void Machine::pop_call_frame() {
        CallFrame frame = call_frames.back();
        call_frames.pop_back();
        ip = frame.ip;
        sp = frame.sp;
        current_function = frame.function;
    }

    void Machine::push_value(Value value) {
        stack.push_back(value);
        sp++;
    }

    Value Machine::pop_value() {
        return stack[--sp];
    }

    void Machine::return_value() {
        // pop the return value
        Value return_value = pop_value();
        // restore the caller frame
        pop_call_frame();
        // push the return value to the stack
        push_value(return_value);
    }
} // namespace vulpes::vm