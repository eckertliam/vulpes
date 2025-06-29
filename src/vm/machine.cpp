#include "machine.hpp"

#include <utility>

namespace vulpes::vm {
    Machine::Machine(std::vector<Function> functions, size_t entry_point)
        : functions(std::move(functions)), arena(1024 * 1024), sp(0), ip(0) {
        call_frames.push_back(CallFrame(&this->functions[entry_point], 0, 0));
        current_function = &this->functions[entry_point];
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

    String* Machine::make_string() {
        // pop the length from the stack
        Value length_value = pop_value();
        if (!length_value.is_int()) {
            throw std::runtime_error("Expected int for string length");
        }

        int64_t length = length_value.as_int();

        // pop the chars from the stack
        std::string data;
        for (int64_t i = 0; i < length; i++) {
            Value char_value = pop_value();
            if (!char_value.is_char()) {
                throw std::runtime_error("Expected char for string");
            }
            data += char_value.as_char();
        }

        // create the string
        String* str = arena.make<String>(data);

        // push the string to the stack
        push_value(Value(str));

        // return the string
        return str;
    }

    List* Machine::make_list() {
        // pop the bool for whether there are initial values
        Value has_initial_values = pop_value();
        if (!has_initial_values.is_bool()) {
            throw std::runtime_error("Expected bool for list");
        }

        // if there are initial values, pop the length and then pop that many values from the stack
        if (has_initial_values.as_bool()) {
            Value length_value = pop_value();
            if (!length_value.is_int()) {
                throw std::runtime_error("Expected int for list length");
            }
            int64_t length = length_value.as_int();

            // pop the values from the stack
            std::vector<Value> values;
            for (int64_t i = 0; i < length; i++) {
                values.push_back(pop_value());
            }

            // create the list
            List* list = arena.make<List>(values);

            // push the list to the stack
            push_value(Value(list));

            // return the list
            return list;
        } else {
            // create an empty list
            List* list = arena.make<List>();

            // push the list to the stack
            push_value(Value(list));

            // return the list
            return list;
        }
    }

    Tuple* Machine::make_tuple() {
        // pop the length from the stack
        Value length_value = pop_value();
        if (!length_value.is_int()) {
            throw std::runtime_error("Expected int for tuple length");
        }

        int64_t length = length_value.as_int();

        // pop the values from the stack
        std::vector<Value> values;
        for (int64_t i = 0; i < length; i++) {
            values.push_back(pop_value());
        }

        // create the tuple
        Tuple* tuple = arena.make<Tuple>(values);

        // push the tuple to the stack
        push_value(Value(tuple));

        // return the tuple
        return tuple;
    }

    Table* Machine::make_table() {
        // pop the bool for whether there are initial values
        Value has_initial_values = pop_value();
        if (!has_initial_values.is_bool()) {
            throw std::runtime_error("Expected bool for table");
        }

        // if there are initial values, pop the length and then pop twice that many values from the
        // stack
        if (has_initial_values.as_bool()) {
            Value length_value = pop_value();
            if (!length_value.is_int()) {
                throw std::runtime_error("Expected int for table length");
            }

            int64_t length = length_value.as_int();

            // pop the keys and values from the stack
            std::vector<std::pair<Value, Value>> pairs;
            for (int64_t i = 0; i < length; i++) {
                Value key = pop_value();
                Value value = pop_value();
                pairs.push_back(std::make_pair(key, value));
            }

            // create the table
            Table* table = arena.make<Table>(pairs);

            // push the table to the stack
            push_value(Value(table));

            // return the table
            return table;
        } else {
            // create an empty table
            Table* table = arena.make<Table>();

            // push the table to the stack
            push_value(Value(table));

            // return the table
            return table;
        }
    }
} // namespace vulpes::vm