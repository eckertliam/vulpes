#include "machine.hpp"

#include "vm/opcode.hpp"

#include <algorithm>
#include <iostream>
#include <utility>

namespace vulpes::vm {
    Machine::Machine(std::vector<Function> functions, size_t entry_point)
        : functions(std::move(functions)), arena(1024 * 1024), sp(0), ip(0), running(true) {
        call_frames.push_back(CallFrame(&this->functions[entry_point], 0, 0));
        current_function = &this->functions[entry_point];
    }

    void Machine::run() {
        while (running) {
            if (ip >= current_function->instructions.size()) {
                throw std::runtime_error("Instruction pointer out of bounds");
            }
            execute_instruction(current_function->instructions[ip]);
            ip++;
        }
    }

    void Machine::execute_instruction(Instruction instruction) {
        switch (instruction.opcode) {
        case OpCode::Nop:
            break;
        case OpCode::Pop:
            pop_value();
            break;
        case OpCode::Dup:
            push_value(stack[sp - 1]);
            break;
        case OpCode::Swap:
            std::swap(stack[sp - 1], stack[sp - 2]);
            break;
        case OpCode::Add:
            // TODO: Implement
            break;
        case OpCode::Sub:
            // TODO: Implement
            break;
        case OpCode::Mul:
            // TODO: Implement
            break;
        case OpCode::Div:
            // TODO: Implement
            break;
        case OpCode::Mod:
            // TODO: Implement
            break;
        case OpCode::Eq:
            // TODO: Implement
            break;
        case OpCode::Neq:
            // TODO: Implement
            break;
        case OpCode::Lt:
            // TODO: Implement
            break;
        case OpCode::Gt:
            // TODO: Implement
            break;
        case OpCode::Lte:
            // TODO: Implement
            break;
        case OpCode::Gte:
            // TODO: Implement
            break;
        case OpCode::Jump:
            // TODO: Implement
            break;
        case OpCode::JumpIf:
            // TODO: Implement
            break;
        case OpCode::JumpIfNot:
            // TODO: Implement
            break;
        case OpCode::LoadConst:
            if (instruction.imm0 >= current_function->constants.size()) {
                throw std::runtime_error("Constant index out of bounds");
            }
            push_value(current_function->constants[instruction.imm0]);
            break;
        case OpCode::Call:
            call_function(instruction.imm0);
            break;
        case OpCode::Return:
            return_value();
            break;
        case OpCode::MakeString:
            make_string();
            break;
        case OpCode::MakeList:
            make_list();
            break;
        case OpCode::MakeTuple:
            make_tuple();
            break;
        case OpCode::MakeTable:
            make_table();
            break;
        case OpCode::Halt:
            running = false;
            break;
        default:
            throw std::runtime_error("Unknown opcode: " +
                                     std::to_string(static_cast<int>(instruction.opcode)));
        }
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

        // pop the chars from the stack and collect them
        std::string data;
        data.reserve(length); // optimize for known length
        for (int64_t i = 0; i < length; i++) {
            Value char_value = pop_value();
            if (!char_value.is_char()) {
                throw std::runtime_error("Expected char for string");
            }
            data += char_value.as_char();
        }

        // reverse the string since stack is LIFO
        std::reverse(data.begin(), data.end());

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

            if (length < 0) {
                throw std::runtime_error("List length must be non-negative");
            }

            if (sp < length) {
                throw std::runtime_error("Not enough values on stack to make list");
            }

            // pop the values from the stack
            std::vector<Value> values;
            for (int64_t i = 0; i < length; i++) {
                values.push_back(pop_value());
            }

            // create the list
            List* list = arena.make<List>(values);

            // push the list to the stack
            push_value(Value(static_cast<Object*>(list)));

            // return the list
            return list;
        } else {
            // create an empty list
            List* list = arena.make<List>();

            // push the list to the stack
            push_value(Value(static_cast<Object*>(list)));

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

    void Machine::print_stack() const {
        std::cout << "Stack (top to bottom):\n";
        for (ssize_t i = static_cast<ssize_t>(sp) - 1; i >= 0; --i) {
            std::cout << "  [" << i << "]: " << stack[i].to_string() << "\n";
        }
    }
} // namespace vulpes::vm